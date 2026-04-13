# ABOUTME: Briefing 计算模块 — 确定性脚本生成 Coach Briefing
# ABOUTME: 从 Store 和 Thread API 读取用户数据，计算结构化 briefing 写入 Store

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from voliti.store_contract import (
    BRIEFING_DERIVED_KEY,
    COPING_PLANS_INDEX_KEY,
    TIMELINE_MARKERS_KEY,
    make_file_value,
    unwrap_file_value,
)

logger = logging.getLogger(__name__)

# Store keys 使用 /user/ 前缀（client SDK 视角）
_MARKERS_STORE_KEY = f"/user{TIMELINE_MARKERS_KEY}"
_COPING_STORE_KEY = f"/user{COPING_PLANS_INDEX_KEY}"


def compute_days_since_last_session(
    threads: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> int | None:
    """计算距上次会话的天数。"""
    now = now or datetime.now(timezone.utc)
    latest = None
    for t in threads:
        date_str = t.get("metadata", {}).get("date")
        if date_str and (latest is None or date_str > latest):
            latest = date_str
    if latest is None:
        return None
    try:
        last_date = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return max(0, (now - last_date).days)
    except ValueError:
        return None


def compute_sessions_this_week(
    threads: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> int:
    """计算本周会话数（周一至周日）。"""
    now = now or datetime.now(timezone.utc)
    monday_date = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    return sum(
        1 for t in threads
        if t.get("metadata", {}).get("date", "") >= monday_date
    )


def extract_upcoming_markers(
    markers_content: str | None,
    *,
    now: datetime | None = None,
    days_ahead: int = 7,
) -> list[dict[str, str]]:
    """提取未来 N 天的 calendar 事件。"""
    if not markers_content:
        return []
    now = now or datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)
    try:
        data = json.loads(markers_content)
        markers = data.get("markers", [])
    except (json.JSONDecodeError, AttributeError):
        return []

    upcoming = []
    for m in markers:
        if m.get("status") != "upcoming":
            continue
        try:
            date = datetime.fromisoformat(m["date"])
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            if now <= date <= cutoff:
                upcoming.append({
                    "date": date.strftime("%m/%d"),
                    "desc": m.get("description", ""),
                    "risk": m.get("risk_level", ""),
                })
        except (KeyError, ValueError):
            continue
    return upcoming


def extract_lifesign_activity(
    coping_index_content: str | None,
) -> list[dict[str, Any]]:
    """从 coping_plans_index.md 提取 LifeSign 活跃度信息。"""
    if not coping_index_content:
        return []
    results = []
    for line in coping_index_content.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        # 格式: - ls_001: "trigger" → response [active, 2/5 success]
        parts = line[2:].split(":", 1)
        if len(parts) < 2:
            continue
        ls_id = parts[0].strip()
        rest = parts[1].strip()
        success_count = 0
        total_attempts = 0
        if "[" in rest and "success" in rest:
            bracket = rest[rest.rindex("[") + 1 : rest.rindex("]")]
            for segment in bracket.split(","):
                segment = segment.strip()
                if "success" in segment:
                    try:
                        ratio = segment.split("success")[0].strip().split("/")
                        if len(ratio) == 2:
                            success_count = int(ratio[0].strip())
                            total_attempts = int(ratio[1].strip())
                    except (ValueError, IndexError):
                        pass
        trigger = ""
        if '"' in rest:
            first_q = rest.index('"')
            second_q = rest.index('"', first_q + 1) if rest.count('"') >= 2 else -1
            if second_q > first_q:
                trigger = rest[first_q + 1 : second_q]

        results.append({
            "id": ls_id,
            "trigger": trigger,
            "success_count": success_count,
            "total_attempts": total_attempts,
        })
    return results


def format_briefing(
    *,
    days_since_last: int | None,
    sessions_this_week: int,
    upcoming_markers: list[dict[str, str]],
    lifesign_activity: list[dict[str, Any]],
    now: datetime | None = None,
) -> str:
    """将计算结果格式化为 briefing 文本。"""
    now = now or datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    lines = [f"## Coach Briefing (auto-generated, {date_str})", ""]

    if days_since_last is not None:
        lines.append(f"距上次会话：{days_since_last} 天")
    lines.append(f"本周会话：{sessions_this_week} 次")
    lines.append("")

    if upcoming_markers:
        lines.append("近期日程：")
        for m in upcoming_markers:
            risk_tag = f" [{m['risk'].upper()}]" if m.get("risk") else ""
            lines.append(f"- {m['date']} {m['desc']}{risk_tag}")
        lines.append("")

    if lifesign_activity:
        lines.append("LifeSign 状态：")
        for ls in lifesign_activity:
            trigger = ls["trigger"] or ls["id"]
            sc = ls["success_count"]
            ta = ls["total_attempts"]
            lines.append(f"- {trigger}：{sc}/{ta} 成功")
        lines.append("")

    lines.append(f"完整日历：read_file {_MARKERS_STORE_KEY}")
    return "\n".join(lines)


async def _read_store_file(client: Any, namespace: tuple[str, ...], key: str) -> str | None:
    """从 Store 读取文件内容，fail-open。"""
    try:
        item = await client.store.get_item(namespace, key)
        if item and item.get("value"):
            return unwrap_file_value(item["value"])
    except Exception:  # noqa: BLE001
        logger.debug("Briefing: failed to read %s", key)
    return None


async def compute_and_write_briefing(
    *,
    client: Any,
    user_id: str,
    namespace: tuple[str, ...],
    threads: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
    user_timezone: str | None = None,
) -> str | None:
    """计算并写入 briefing 文件。

    Args:
        client: LangGraph SDK client
        user_id: 用户标识
        namespace: Store namespace（如 ("voliti", user_id)）
        threads: 预查询的 threads 列表（避免重复 API 调用）
        now: 当前时间（可覆盖用于测试）
        user_timezone: 用户本地时区标识（如 "Asia/Shanghai"），用于日期对齐

    Returns:
        生成的 briefing 文本，或 None（计算失败时）
    """
    now = now or datetime.now(timezone.utc)

    # 1. 获取 threads（如果未预传入）
    if threads is None:
        try:
            threads = await client.threads.search(
                metadata={"user_id": user_id},
                limit=30,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Briefing: failed to search threads for user %s", user_id)
            threads = []

    # 2. 并行读取 Store 数据
    markers_task = _read_store_file(client, namespace, _MARKERS_STORE_KEY)
    coping_task = _read_store_file(client, namespace, _COPING_STORE_KEY)
    markers_content, coping_content = await asyncio.gather(markers_task, coping_task)

    # 3. 计算各项指标
    days_since_last = compute_days_since_last_session(threads, now=now)
    sessions_this_week = compute_sessions_this_week(threads, now=now)
    upcoming = extract_upcoming_markers(markers_content, now=now)
    lifesigns = extract_lifesign_activity(coping_content)

    # 4. 格式化并写入
    briefing = format_briefing(
        days_since_last=days_since_last,
        sessions_this_week=sessions_this_week,
        upcoming_markers=upcoming,
        lifesign_activity=lifesigns,
        now=now,
    )

    try:
        await client.store.put_item(
            namespace,
            BRIEFING_DERIVED_KEY,
            value=make_file_value(briefing, now=now),
        )
        logger.info("Briefing: written for user %s", user_id)
    except Exception:  # noqa: BLE001
        logger.warning("Briefing: failed to write briefing for user %s", user_id)
        return None

    return briefing
