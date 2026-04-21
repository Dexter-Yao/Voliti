# ABOUTME: Plan 上游 batch 读取共享 parser · raw Store value → 展开 dict
# ABOUTME: http_app.py 与 briefing.py 均通过此模块把 /timeline/markers.json、/coping_plans_index.md 转为 compute_plan_view 所需输入

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from voliti.contracts.markers import MarkerItem, MarkersRecord
from voliti.store_contract import (
    InvalidStoreValueError,
    parse_json_file_value,
    unwrap_file_value,
)

logger = logging.getLogger(__name__)


def parse_markers(raw_value: dict[str, Any] | None) -> dict[str, MarkerItem]:
    """从 /timeline/markers.json 解析出 {id: MarkerItem}；损坏降级为空 dict + WARN。"""
    if raw_value is None:
        return {}
    try:
        data = parse_json_file_value(raw_value)
        record = MarkersRecord.model_validate(data)
        return {mk.id: mk for mk in record.markers}
    except (InvalidStoreValueError, ValidationError, ValueError) as exc:
        logger.warning(
            "plan_store_parsers: markers parse failed, returning empty dict",
            extra={"exception_type": type(exc).__name__},
        )
        return {}


def parse_lifesigns_index(raw_value: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    """从 /coping_plans_index.md 解析出 {id: {trigger}}。

    格式约定：`- ls_001: "trigger text" → response [status]`；损坏降级为空 dict。
    """
    if raw_value is None:
        return {}
    try:
        text = unwrap_file_value(raw_value)
    except InvalidStoreValueError:
        logger.warning("plan_store_parsers: lifesigns envelope malformed, returning empty dict")
        return {}

    result: dict[str, dict[str, str]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        parts = line[2:].split(":", 1)
        if len(parts) < 2:
            continue
        ls_id = parts[0].strip()
        rest = parts[1].strip()
        trigger = ""
        if '"' in rest:
            first_q = rest.index('"')
            if rest.count('"') >= 2:
                second_q = rest.index('"', first_q + 1)
                trigger = rest[first_q + 1 : second_q]
        if ls_id:
            result[ls_id] = {"trigger": trigger}
    return result
