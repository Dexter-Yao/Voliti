# ABOUTME: Voliti 运行时 Store 契约辅助函数
# ABOUTME: 定义用户标识校验、Store key、Agent 文件路径和文件封装值解包规则

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, ValidationError

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{7,63}$")
STORE_NAMESPACE_PREFIX = "voliti"

_BACKEND_DIR: Final[Path] = Path(__file__).resolve().parent.parent.parent
COACH_SKILLS_ROOT: Final[Path] = _BACKEND_DIR / "skills" / "coach"
"""Coach 的 Agent Skills 根目录；由 SkillsMiddleware 通过只读 FilesystemBackend 挂载。"""

COACH_SKILLS_BACKEND_PREFIX: Final[str] = "/skills/coach/"
"""Skills 在 CompositeBackend 中暴露给 Coach 的虚拟路径前缀（只读）。"""

PROFILE_CONTEXT_KEY = "/profile/context.md"
PROFILE_DASHBOARD_CONFIG_KEY = "/profile/dashboardConfig"
GOAL_CURRENT_KEY = "/goal/current.json"
GOAL_ARCHIVE_PREFIX = "/goal/archive/"
CHAPTER_CURRENT_KEY = "/chapter/current.json"
COPING_PLANS_INDEX_KEY = "/coping_plans_index.md"
TIMELINE_MARKERS_KEY = "/timeline/markers.json"
COACH_MEMORY_KEY = "/coach/AGENTS.md"
LIFESIGNS_KEY = "/lifesigns.md"
BRIEFING_STORE_KEY = "/derived/briefing.md"
DAY_SUMMARY_PREFIX = "/day_summary/"
CONVERSATION_ARCHIVE_PREFIX = "/conversation_archive/"
BRIEFING_FILE_PATH = "/user/derived/briefing.md"
INTERVENTIONS_SEGMENT = "interventions"
PLAN_CURRENT_KEY = "/plan/current.json"
PLAN_ARCHIVE_SEGMENT = "plan_archive"


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


def make_plan_archive_namespace(user_id: str) -> tuple[str, str, str]:
    """构造 Plan archive 所在的 Store 子 namespace。
    archive 文件 key 格式：{plan_id}_v{version}.json；
    用子 namespace 避免与 user namespace 下的其他 key（day_summary / briefing 等）混杂。"""
    user_namespace = make_user_namespace(user_id)
    return (*user_namespace, PLAN_ARCHIVE_SEGMENT)


def resolve_plan_archive_namespace(config: dict[str, Any] | None) -> tuple[str, str, str]:
    """从 configurable config 中解析 Plan archive namespace。"""
    user_namespace = resolve_user_namespace(config)
    return (*user_namespace, PLAN_ARCHIVE_SEGMENT)


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


# ── 强格式 Store 路径契约校验 ─────────────────────────────────────────────────


def _format_write_error(exc: ValidationError, model_class: type[BaseModel]) -> str:
    """将 Pydantic ValidationError 转为可操作的中文错误说明。"""
    from voliti.contracts import CANONICAL_EXAMPLES

    lines = [f"Store 写入校验失败（{model_class.__name__}）："]
    for error in exc.errors():
        field_path = " → ".join(str(loc) for loc in error["loc"]) or "(根级别)"
        current_val = error.get("input", "<未提供>")
        lines.append(f"  • 字段 `{field_path}`：{error['msg']}（当前值：{current_val!r}）")
    example = CANONICAL_EXAMPLES.get(model_class)
    if example:
        lines.append(f"\n最小合法格式参考：{example}")
    return "\n".join(lines)


def store_write_validated(
    store: Any,
    namespace: tuple[str, ...],
    key: str,
    data: dict[str, Any],
    model_class: type[BaseModel],
    *,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """校验 data 并写入 Store。

    写入端 fail-closed：校验失败时不写 Store，返回 (False, 中文错误消息)。
    错误消息由调用方（工具函数）转发给 Coach，Coach 据此决策是否修正后重试。
    """
    try:
        record = model_class.model_validate(data)
    except ValidationError as exc:
        return False, _format_write_error(exc, model_class)

    content = record.model_dump_json()
    store.put(namespace, key, make_file_value(content, now=now))
    return True, ""


def store_read_validated(
    raw_value: dict[str, Any] | None,
    model_class: type[BaseModel],
    store_key: str,
) -> BaseModel | None:
    """从 Store 原始值读取并校验结构完整性。

    读取端 fail-closed：
    - raw_value 为 None（键不存在）→ 返回 None（正常情况，不报错）
    - raw_value 存在但解析/校验失败 → 抛出 InvalidStoreValueError
    """
    if raw_value is None:
        return None

    try:
        text = unwrap_file_value(raw_value)
        data = json.loads(text)
        return model_class.model_validate(data)
    except (InvalidStoreValueError, json.JSONDecodeError) as exc:
        raise InvalidStoreValueError(
            f"[{store_key}] JSON 解析失败：{exc}"
        ) from exc
    except ValidationError as exc:
        field_errors = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        )
        raise InvalidStoreValueError(
            f"[{store_key}] 契约校验失败（{model_class.__name__}）：{field_errors}"
        ) from exc
