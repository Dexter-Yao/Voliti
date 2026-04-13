# ABOUTME: Briefing 计算模块 — 确定性脚本生成 Coach Briefing
# ABOUTME: 从 Store 和 Thread API 读取用户数据，计算结构化 briefing 写入 /user/derived/briefing.md

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

_BRIEFING_KEY = "/user/derived/briefing.md"
_MARKERS_KEY = "/user/timeline/markers.json"
_COPING_PLANS_INDEX_KEY = "/user/coping_plans_index.md"


def compute_days_since_last_session(
    threads: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> int | None:
    """计算距上次会话的天数。"""
    now = now or datetime.now(timezone.utc)
    dates: list[str] = []
    for t in threads:
        meta = t.get("metadata", {})
        date_str = meta.get("date")
        if date_str:
            dates.append(date_str)
    if not dates:
        return None
    dates.sort(reverse=True)
    try:
        last_date = datetime.strptime(dates[0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        delta = now - last_date
        return max(0, delta.days)
    except (ValueError, IndexError):
        return None


def compute_sessions_this_week(
    threads: list[dict[str, Any]],
    *,
    now: datetime | None = None,
) -> int:
    """计算本周会话数（周一至周日）。"""
    now = now or datetime.now(timezone.utc)
    monday = now - timedelta(days=now.weekday())
    monday_date = monday.strftime("%Y-%m-%d")
    count = 0
    for t in threads:
        meta = t.get("metadata", {})
        date_str = meta.get("date", "")
        if date_str >= monday_date:
            count += 1
    return count


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
        # 提取 success 信息
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
        # 提取 trigger
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

    lines.append(f"完整日历：read_file /user/timeline/markers.json")
    return "\n".join(lines)


async def compute_and_write_briefing(
    *,
    client: Any,
    user_id: str,
    namespace: tuple[str, ...],
    now: datetime | None = None,
) -> str | None:
    """计算并写入 briefing 文件。

    Args:
        client: LangGraph SDK client
        user_id: 用户标识
        namespace: Store namespace（如 ("voliti", user_id)）
        now: 当前时间（可覆盖用于测试）

    Returns:
        生成的 briefing 文本，或 None（计算失败时）
    """
    now = now or datetime.now(timezone.utc)

    # 1. 获取用户的近期 threads
    try:
        threads = await client.threads.search(
            metadata={"user_id": user_id},
            limit=30,
        )
    except Exception:  # noqa: BLE001
        logger.warning("Briefing: failed to search threads for user %s", user_id)
        threads = []

    # 2. 从 Store 读取 markers
    markers_content = None
    try:
        item = await client.store.get_item(namespace, _MARKERS_KEY)
        if item and item.get("value"):
            from voliti.store_contract import unwrap_file_value
            markers_content = unwrap_file_value(item["value"])
    except Exception:  # noqa: BLE001
        logger.debug("Briefing: failed to read markers")

    # 3. 从 Store 读取 coping plans index
    coping_content = None
    try:
        item = await client.store.get_item(namespace, _COPING_PLANS_INDEX_KEY)
        if item and item.get("value"):
            from voliti.store_contract import unwrap_file_value
            coping_content = unwrap_file_value(item["value"])
    except Exception:  # noqa: BLE001
        logger.debug("Briefing: failed to read coping plans index")

    # 4. 计算各项指标
    days_since_last = compute_days_since_last_session(threads, now=now)
    sessions_this_week = compute_sessions_this_week(threads, now=now)
    upcoming = extract_upcoming_markers(markers_content, now=now)
    lifesigns = extract_lifesign_activity(coping_content)

    # 5. 格式化
    briefing = format_briefing(
        days_since_last=days_since_last,
        sessions_this_week=sessions_this_week,
        upcoming_markers=upcoming,
        lifesign_activity=lifesigns,
        now=now,
    )

    # 6. 写入 Store
    try:
        from voliti.store_contract import make_file_value
        await client.store.put_item(
            namespace,
            _BRIEFING_KEY,
            value=make_file_value(briefing, now=now),
        )
        logger.info("Briefing: written for user %s", user_id)
    except Exception:  # noqa: BLE001
        logger.warning("Briefing: failed to write briefing for user %s", user_id)
        return None

    return briefing
