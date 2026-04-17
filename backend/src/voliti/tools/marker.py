# ABOUTME: Forward Marker 工具 — Coach 写入前瞻事件标记
# ABOUTME: 自动生成 id/timezone/created_at/status，Coach 只需提供核心字段

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Annotated, Any

from langchain_core.tools import InjectedToolArg, tool
from langgraph.store.base import BaseStore

from voliti.store_contract import (
    TIMELINE_MARKERS_KEY,
    make_file_value,
    resolve_user_namespace,
    unwrap_file_value,
)

logger = logging.getLogger(__name__)

# MVP 阶段默认时区；待多时区支持时从用户配置读取
_DEFAULT_TIMEZONE = "Asia/Shanghai"
_DEFAULT_UTC_OFFSET = "+08:00"


@tool
def add_forward_marker(
    description: str,
    date: str,
    risk_level: str = "medium",
    linked_lifesign: str | None = None,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Add a forward-looking event marker to the user's timeline.

    Use when the user mentions an upcoming event that may affect their behavior
    (e.g., business trip, social dinner, holiday, exam period).
    Date must be a future date. No server-side date validation is applied;
    expired markers are cleaned up by the daily pipeline.

    Args:
        description: Brief event description (e.g., "出差上海一周").
        date: Event date in YYYY-MM-DD format (e.g., "2026-04-20").
        risk_level: Behavioral risk level — "low", "medium", or "high".
        linked_lifesign: LifeSign ID to link (e.g., "ls_001"), if a matching coping plan exists.
    """
    namespace = resolve_user_namespace(config)
    now = datetime.now(timezone.utc)

    # 基于内容哈希，同一 description+date 只产生一个 ID
    marker_id = f"mk_{hashlib.sha256(f'{description}{date}'.encode()).hexdigest()[:8]}"
    marker: dict[str, Any] = {
        "id": marker_id,
        "date": f"{date}T00:00:00{_DEFAULT_UTC_OFFSET}",
        "timezone": _DEFAULT_TIMEZONE,
        "description": description,
        "risk_level": risk_level,
        "status": "upcoming",
        "created_at": now.isoformat(),
    }
    if linked_lifesign:
        marker["linked_lifesign"] = linked_lifesign

    # 读取现有 markers 列表，追加后写回
    existing_markers: list[dict[str, Any]] = []
    try:
        item = store.get(namespace, TIMELINE_MARKERS_KEY)
        if item and item.value:
            content = unwrap_file_value(item.value)
            data = json.loads(content)
            existing_markers = data.get("markers", [])
    except Exception:  # noqa: BLE001
        logger.warning("marker: failed to read existing markers, starting fresh")

    existing_markers.append(marker)
    new_content = json.dumps({"markers": existing_markers}, ensure_ascii=False)
    store.put(namespace, TIMELINE_MARKERS_KEY, make_file_value(new_content, now=now))

    risk_label = f" [{risk_level.upper()}]" if risk_level != "medium" else ""
    lifesign_label = f", linked to {linked_lifesign}" if linked_lifesign else ""
    return f"Marker added: {date} {description}{risk_label}{lifesign_label}"
