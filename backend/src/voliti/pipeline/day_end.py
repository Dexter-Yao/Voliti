# ABOUTME: 日终 Pipeline — 封存 thread、生成日摘要、回填缺失日、归档会话、更新 briefing
# ABOUTME: 使用 LangGraph SDK client 操作 threads/store，轻量模型生成摘要

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage

from voliti.briefing import compute_and_write_briefing
from voliti.config.models import ModelRegistry
from voliti.store_contract import (
    CONVERSATION_ARCHIVE_PREFIX,
    DAY_SUMMARY_PREFIX,
    make_file_value,
)

logger = logging.getLogger(__name__)

_MAX_MESSAGE_CHARS = 500

_SUMMARY_SYSTEM_PROMPT = """\
你是一个日志摘要助手。根据以下教练会话记录，用一句话概括当天的核心内容。

格式要求：
- 一句话，不超过 60 字
- 涵盖关键行为或状态（如有数据变动则包含）
- 使用中文
- 不要加任何前缀、标题或标点列表

只输出摘要内容。"""


def _thread_meta(t: Any) -> dict[str, Any]:
    """统一获取 thread metadata（兼容 dict 和 object 两种返回格式）。"""
    if isinstance(t, dict):
        return t.get("metadata", {})
    return getattr(t, "metadata", {})


def _thread_id(t: Any) -> str:
    """统一获取 thread ID。"""
    if isinstance(t, dict):
        return t.get("thread_id", "")
    return getattr(t, "thread_id", "")


async def seal_thread(
    client: Any,
    thread_id: str,
    *,
    sealed_at: datetime | None = None,
) -> bool:
    """封存 thread，标记为 sealed。"""
    sealed_at = sealed_at or datetime.now(timezone.utc)
    try:
        await client.threads.update(
            thread_id,
            metadata={
                "segment_status": "sealed",
                "sealed_at": sealed_at.isoformat(),
            },
        )
        logger.info("Pipeline: sealed thread %s", thread_id)
        return True
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to seal thread %s", thread_id)
        return False


def _extract_messages_text(state: dict[str, Any]) -> str:
    """从 thread state 中提取可读的对话文本。"""
    values = state.get("values", {})
    messages = values.get("messages", [])
    if not messages:
        return ""

    lines: list[str] = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("type", msg.get("role", "unknown"))
            content = msg.get("content", "")
        else:
            role = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")

        if not content or not isinstance(content, str):
            continue
        if role in ("system", "tool"):
            continue
        prefix = "用户" if role == "human" else "Coach"
        lines.append(f"{prefix}: {content[:_MAX_MESSAGE_CHARS]}")

    return "\n\n".join(lines)


async def generate_day_summary(
    client: Any,
    thread_id: str,
    *,
    date_str: str,
    namespace: tuple[str, ...],
    now: datetime | None = None,
) -> str | None:
    """从 thread 历史生成日摘要，写入 Store。"""
    now = now or datetime.now(timezone.utc)

    try:
        state = await client.threads.get_state(thread_id)
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to get state for thread %s", thread_id)
        return None

    conversation_text = _extract_messages_text(state)
    if not conversation_text:
        logger.info("Pipeline: thread %s has no messages, skipping summary", thread_id)
        return None

    try:
        model = ModelRegistry.get("summarizer")
        response = await model.ainvoke([
            SystemMessage(content=_SUMMARY_SYSTEM_PROMPT),
            HumanMessage(content=f"日期：{date_str}\n\n会话记录：\n{conversation_text}"),
        ])
        summary = response.content
        if not isinstance(summary, str) or not summary.strip():
            logger.warning("Pipeline: empty summary for thread %s", thread_id)
            return None
        summary = summary.strip()
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to generate summary for thread %s", thread_id)
        return None

    key = f"{DAY_SUMMARY_PREFIX}{date_str}.md"
    try:
        await client.store.put_item(
            namespace, key, value=make_file_value(summary, now=now),
        )
        logger.info("Pipeline: day summary written for %s", date_str)
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to write day summary for %s", date_str)
        return None

    return summary


async def archive_conversation(
    client: Any,
    *,
    thread_id: str,
    date_str: str,
    namespace: tuple[str, ...],
    now: datetime | None = None,
) -> bool:
    """将封存 thread 的完整会话文本写入按天独立的归档文件。

    存储路径：/user/conversation_archive/{YYYY-MM-DD}.md
    Coach 通过 grep 关键词定位日期，再 read_file 单日文件。
    """
    now = now or datetime.now(timezone.utc)

    try:
        state = await client.threads.get_state(thread_id)
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to get state for archiving thread %s", thread_id)
        return False

    conversation_text = _extract_messages_text(state)
    if not conversation_text:
        return False

    key = f"{CONVERSATION_ARCHIVE_PREFIX}{date_str}.md"
    try:
        await client.store.put_item(
            namespace, key, value=make_file_value(conversation_text, now=now),
        )
        logger.info("Pipeline: archived conversation for %s", date_str)
        return True
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to archive conversation for %s", date_str)
        return False


async def find_unsealed_threads(
    client: Any,
    *,
    user_id: str,
    before_date: str,
    threads: list[Any] | None = None,
) -> list[Any]:
    """查找需要封存的 threads（日期早于 before_date 且未封存）。"""
    if threads is None:
        try:
            threads = await client.threads.search(
                metadata={"user_id": user_id},
                limit=30,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Pipeline: failed to search threads for user %s", user_id)
            return []

    return [
        t for t in threads
        if _thread_meta(t).get("date", "") < before_date
        and _thread_meta(t).get("segment_status") != "sealed"
        and _thread_id(t)
    ]


_NO_SESSION_TEXT = "当天没有对话记录。"


async def backfill_missing_summaries(
    client: Any,
    *,
    namespace: tuple[str, ...],
    today: str,
    days_back: int = 7,
    now: datetime | None = None,
) -> list[str]:
    """回填过去 N 天中缺失日期的摘要。

    连续缺失的日期合并为一条（如 "04/10-04/12 期间没有对话记录。"）。
    返回已回填的日期列表。
    """
    now = now or datetime.now(timezone.utc)
    today_date = datetime.strptime(today, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    # 收集需要检查的日期（不含今天）
    dates_to_check: list[str] = []
    for i in range(1, days_back + 1):
        d = (today_date - timedelta(days=i)).strftime("%Y-%m-%d")
        dates_to_check.append(d)

    # 检查哪些日期已有摘要
    missing: list[str] = []
    for date_str in dates_to_check:
        key = f"{DAY_SUMMARY_PREFIX}{date_str}.md"
        try:
            item = await client.store.get_item(namespace, key)
            if item and item.get("value"):
                continue
        except Exception:  # noqa: BLE001
            pass
        missing.append(date_str)

    if not missing:
        return []

    # 按日期排序（升序），合并连续缺失日期
    missing.sort()
    backfilled: list[str] = []

    groups: list[list[str]] = []
    current_group: list[str] = [missing[0]]
    for i in range(1, len(missing)):
        prev = datetime.strptime(missing[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(missing[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            current_group.append(missing[i])
        else:
            groups.append(current_group)
            current_group = [missing[i]]
    groups.append(current_group)

    for group in groups:
        if len(group) == 1:
            text = _NO_SESSION_TEXT
        else:
            start = datetime.strptime(group[0], "%Y-%m-%d").strftime("%m/%d")
            end = datetime.strptime(group[-1], "%Y-%m-%d").strftime("%m/%d")
            text = f"{start}-{end} 期间没有对话记录。"

        # 为组内每个日期写入摘要（单日写标准文本，多日每个日期写合并文本）
        for date_str in group:
            key = f"{DAY_SUMMARY_PREFIX}{date_str}.md"
            try:
                await client.store.put_item(
                    namespace, key, value=make_file_value(text, now=now),
                )
                backfilled.append(date_str)
            except Exception:  # noqa: BLE001
                logger.warning("Pipeline: failed to backfill summary for %s", date_str)

    if backfilled:
        logger.info("Pipeline: backfilled %d missing day summaries", len(backfilled))
    return backfilled


async def run_day_end_pipeline(
    client: Any,
    *,
    user_id: str,
    namespace: tuple[str, ...],
    today: str | None = None,
    now: datetime | None = None,
    user_timezone: str | None = None,
) -> dict[str, Any]:
    """为一个用户执行日终 Pipeline。

    步骤（每步独立 fail-open）：
    1. 查找并封存过期 threads
    2. 为每个封存的 thread 生成日摘要 + 追加完整会话到归档
    3. 回填缺失日期的摘要
    4. 更新 briefing
    """
    now = now or datetime.now(timezone.utc)
    if today is None:
        if user_timezone:
            try:
                today = now.astimezone(ZoneInfo(user_timezone)).strftime("%Y-%m-%d")
            except Exception:  # noqa: BLE001
                logger.warning("Pipeline: invalid timezone %r, falling back to UTC", user_timezone)
                today = now.strftime("%Y-%m-%d")
        else:
            today = now.strftime("%Y-%m-%d")

    result: dict[str, Any] = {
        "user_id": user_id,
        "today": today,
        "sealed": [],
        "summaries": [],
        "briefing_updated": False,
        "errors": [],
    }

    # 查询一次 threads，共享给 find_unsealed 和 briefing
    try:
        all_threads = await client.threads.search(
            metadata={"user_id": user_id},
            limit=30,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to search threads for user %s", user_id)
        all_threads = []

    # Step 1+2: 封存 + 摘要 + 归档
    unsealed = await find_unsealed_threads(
        client, user_id=user_id, before_date=today, threads=all_threads,
    )
    archived_dates: list[str] = []
    for thread in unsealed:
        tid = _thread_id(thread)
        date = _thread_meta(thread).get("date", "unknown")

        sealed = await seal_thread(client, tid, sealed_at=now)
        if sealed:
            result["sealed"].append(tid)
            summary = await generate_day_summary(
                client, tid, date_str=date, namespace=namespace, now=now,
            )
            if summary:
                result["summaries"].append(date)
            if await archive_conversation(
                client, thread_id=tid, date_str=date, namespace=namespace, now=now,
            ):
                archived_dates.append(date)
        else:
            result["errors"].append(f"seal failed: {tid}")
    result["archived"] = archived_dates

    # Step 2.5: 回填缺失日期的摘要
    try:
        backfilled = await backfill_missing_summaries(
            client, namespace=namespace, today=today, now=now,
        )
        result["backfilled"] = backfilled
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to backfill missing summaries for user %s", user_id)
        result["errors"].append("backfill failed")

    # Step 3: 更新 briefing（共享 threads 避免重复查询）
    try:
        briefing = await compute_and_write_briefing(
            client=client,
            user_id=user_id,
            namespace=namespace,
            threads=all_threads,
            now=now,
            user_timezone=user_timezone,
        )
        result["briefing_updated"] = briefing is not None
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to update briefing for user %s", user_id)
        result["errors"].append("briefing update failed")

    logger.info(
        "Pipeline: completed for user %s — sealed=%d, summaries=%d, errors=%d",
        user_id, len(result["sealed"]), len(result["summaries"]), len(result["errors"]),
    )
    return result
