# ABOUTME: 日终 Pipeline — 封存 thread、生成日摘要、更新 briefing
# ABOUTME: 使用 LangGraph SDK client 操作 threads/store，GPT-5.4 Nano 生成摘要

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from voliti.config.models import ModelRegistry
from voliti.store_contract import make_file_value

logger = logging.getLogger(__name__)

_DAY_SUMMARY_PREFIX = "/user/day_summary/"
_BRIEFING_KEY = "/user/derived/briefing.md"

_SUMMARY_SYSTEM_PROMPT = """\
你是一个日志摘要助手。根据以下教练会话记录，生成一份简洁的日摘要。

格式要求：
- 3-5 个要点，每点一行
- 包含关键数据变动（体重、饮食、运动等，如有）
- 一句话情绪基调描述
- 使用中文
- 不超过 300 字

只输出摘要内容，不要加任何前缀或标题。"""


async def seal_thread(
    client: Any,
    thread_id: str,
    *,
    sealed_at: datetime | None = None,
) -> bool:
    """封存 thread，标记为 sealed。

    Returns:
        True if sealed successfully, False on failure.
    """
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
        # 跳过 system 消息和工具调用/结果
        if role in ("system", "tool"):
            continue
        prefix = "用户" if role == "human" else "Coach"
        lines.append(f"{prefix}: {content[:500]}")

    return "\n\n".join(lines)


async def generate_day_summary(
    client: Any,
    thread_id: str,
    *,
    date_str: str,
    namespace: tuple[str, ...],
    now: datetime | None = None,
) -> str | None:
    """从 thread 历史生成日摘要，写入 Store。

    Args:
        client: LangGraph SDK client
        thread_id: 要摘要的 thread ID
        date_str: 日期字符串 (YYYY-MM-DD)
        namespace: Store namespace
        now: 当前时间

    Returns:
        生成的摘要文本，或 None（失败时）
    """
    now = now or datetime.now(timezone.utc)

    # 1. 读取 thread 状态获取消息历史
    try:
        state = await client.threads.get_state(thread_id)
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to get state for thread %s", thread_id)
        return None

    conversation_text = _extract_messages_text(state)
    if not conversation_text:
        logger.info("Pipeline: thread %s has no messages, skipping summary", thread_id)
        return None

    # 2. 使用 summarizer 模型生成摘要
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

    # 3. 写入 Store
    key = f"{_DAY_SUMMARY_PREFIX}{date_str}.md"
    try:
        await client.store.put_item(
            namespace,
            key,
            value=make_file_value(summary, now=now),
        )
        logger.info("Pipeline: day summary written for %s", date_str)
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to write day summary for %s", date_str)
        return None

    return summary


async def find_unsealed_threads(
    client: Any,
    *,
    user_id: str,
    before_date: str,
) -> list[dict[str, Any]]:
    """查找需要封存的 threads（日期早于 before_date 且未封存）。"""
    try:
        threads = await client.threads.search(
            metadata={"user_id": user_id},
            limit=30,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Pipeline: failed to search threads for user %s", user_id)
        return []

    unsealed = []
    for t in threads:
        meta = t.get("metadata", {}) if isinstance(t, dict) else getattr(t, "metadata", {})
        date = meta.get("date", "")
        status = meta.get("segment_status", "")
        thread_id = t.get("thread_id", "") if isinstance(t, dict) else getattr(t, "thread_id", "")

        if date and date < before_date and status != "sealed" and thread_id:
            unsealed.append(t)

    return unsealed


async def run_day_end_pipeline(
    client: Any,
    *,
    user_id: str,
    namespace: tuple[str, ...],
    today: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """为一个用户执行日终 Pipeline。

    步骤（每步独立 fail-open）：
    1. 查找并封存过期 threads
    2. 为每个封存的 thread 生成日摘要
    3. 更新 briefing

    Args:
        client: LangGraph SDK client
        user_id: 用户标识
        namespace: Store namespace (e.g., ("voliti", user_id))
        today: 今天的日期字符串 (YYYY-MM-DD)
        now: 当前时间

    Returns:
        执行结果摘要 dict
    """
    now = now or datetime.now(timezone.utc)
    today = today or now.strftime("%Y-%m-%d")

    result: dict[str, Any] = {
        "user_id": user_id,
        "today": today,
        "sealed": [],
        "summaries": [],
        "briefing_updated": False,
        "errors": [],
    }

    # Step 1: 查找并封存
    unsealed = await find_unsealed_threads(client, user_id=user_id, before_date=today)
    for thread in unsealed:
        meta = thread.get("metadata", {}) if isinstance(thread, dict) else getattr(thread, "metadata", {})
        tid = thread.get("thread_id", "") if isinstance(thread, dict) else getattr(thread, "thread_id", "")
        date = meta.get("date", "unknown")

        sealed = await seal_thread(client, tid, sealed_at=now)
        if sealed:
            result["sealed"].append(tid)

            # Step 2: 生成日摘要
            summary = await generate_day_summary(
                client, tid, date_str=date, namespace=namespace, now=now,
            )
            if summary:
                result["summaries"].append(date)
        else:
            result["errors"].append(f"seal failed: {tid}")

    # Step 3: 更新 briefing
    try:
        from voliti.briefing import compute_and_write_briefing

        briefing = await compute_and_write_briefing(
            client=client,
            user_id=user_id,
            namespace=namespace,
            now=now,
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
