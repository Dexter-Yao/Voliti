# ABOUTME: Voliti 运行时 Store 契约辅助函数
# ABOUTME: 定义用户标识校验、namespace、正式路径和文件封装值解包规则

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,63}$")
STORE_NAMESPACE_PREFIX = "voliti"

PROFILE_CONTEXT_KEY = "/profile/context.md"
PROFILE_DASHBOARD_CONFIG_KEY = "/profile/dashboardConfig"
CHAPTER_CURRENT_KEY = "/chapter/current.json"
COPING_PLANS_INDEX_KEY = "/coping_plans_index.md"
TIMELINE_MARKERS_KEY = "/timeline/markers.json"
COACH_MEMORY_KEY = "/coach/AGENTS.md"
LIFESIGNS_KEY = "/lifesigns.md"
TIMELINE_CALENDAR_KEY = "/timeline-calendar.md"
BRIEFING_DERIVED_KEY = "/user/derived/briefing.md"
DAY_SUMMARY_PREFIX = "/user/day_summary/"
CONVERSATION_ARCHIVE_PREFIX = "/user/conversation_archive/"
INTERVENTIONS_SEGMENT = "interventions"


class InvalidUserIDError(ValueError):
    """用户标识不满足运行时契约。"""


class InvalidStoreValueError(ValueError):
    """Store 文件封装值不满足运行时契约。"""


def validate_user_id(user_id: str) -> str:
    """校验并返回符合契约的 user_id。"""
    if user_id != user_id.strip() or not USER_ID_PATTERN.fullmatch(user_id):
        raise InvalidUserIDError(
            "user_id must be 8-64 chars of letters, digits, '_' or '-'"
        )
    return user_id


def make_user_namespace(user_id: str) -> tuple[str, str]:
    """构造用户级 Store namespace。"""
    return (STORE_NAMESPACE_PREFIX, validate_user_id(user_id))


def make_interventions_namespace(user_id: str) -> tuple[str, str, str]:
    """构造 Witness Card 所在的 Store namespace。"""
    user_namespace = make_user_namespace(user_id)
    return (*user_namespace, INTERVENTIONS_SEGMENT)


def resolve_user_namespace(config: dict[str, Any] | None) -> tuple[str, str]:
    """从 configurable config 中解析用户 namespace。"""
    user_id = (config or {}).get("configurable", {}).get("user_id")
    if not isinstance(user_id, str) or not user_id.strip():
        raise InvalidUserIDError("configurable.user_id is required")
    return make_user_namespace(user_id)


def make_file_value(content: str, *, now: datetime | None = None) -> dict[str, Any]:
    """构造统一文件封装值。"""
    timestamp = (now or datetime.now(UTC)).isoformat()
    return {
        "version": "1",
        "content": content.splitlines(),
        "created_at": timestamp,
        "modified_at": timestamp,
    }


def unwrap_file_value(value: dict[str, Any]) -> str:
    """解包统一文件封装值，恢复为原始文本。"""
    content = value.get("content")
    if not isinstance(content, list) or not all(isinstance(line, str) for line in content):
        raise InvalidStoreValueError("content must be list[str]")
    return "\n".join(content)


def parse_json_file_value(value: dict[str, Any]) -> Any:
    """解包文件封装值并解析其中的 JSON 正文。"""
    return json.loads(unwrap_file_value(value))
