# ABOUTME: SessionType 共享类型定义
# ABOUTME: 为 backend 运行时与契约测试提供唯一的会话类型与会话配置事实来源

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping, TypeGuard

from langgraph.config import get_config

SessionType = Literal["coaching", "onboarding"]
"""Voliti 当前支持的会话类型。"""

DEFAULT_SESSION_TYPE: SessionType = "coaching"
"""默认会话类型。"""


class InvalidSessionTypeError(ValueError):
    """session_type 不满足运行时契约。"""


@dataclass(frozen=True)
class SessionProfile:
    """会话类型对应的最小配置对象。"""

    session_type: SessionType
    system_prompt_name: str
    memory_paths: tuple[str, ...]
    enable_journey_analysis: bool


_DEFAULT_MEMORY_PATHS = (
    "/user/coach/AGENTS.md",
    "/user/profile/context.md",
    "/user/coping_plans_index.md",
    "/user/timeline/markers.json",
)

_SESSION_PROFILES: dict[SessionType, SessionProfile] = {
    "coaching": SessionProfile(
        session_type="coaching",
        system_prompt_name="coach_system",
        memory_paths=_DEFAULT_MEMORY_PATHS,
        enable_journey_analysis=True,
    ),
    "onboarding": SessionProfile(
        session_type="onboarding",
        system_prompt_name="coach_system",
        memory_paths=_DEFAULT_MEMORY_PATHS,
        enable_journey_analysis=False,
    ),
}


def is_session_type(value: object) -> TypeGuard[SessionType]:
    """判断给定值是否为受支持的会话类型。"""
    return value in ("coaching", "onboarding")


def coerce_session_type(value: object) -> SessionType | None:
    """将任意值收敛为 SessionType。"""
    if is_session_type(value):
        return value
    return None


def require_session_type(value: object) -> SessionType:
    """将任意值收敛为 SessionType，失败时直接报错。"""
    session_type = coerce_session_type(value)
    if session_type is None:
        raise InvalidSessionTypeError(
            "configurable.session_type is required and must be one of: coaching, onboarding"
        )
    return session_type


def resolve_session_type(config: Mapping[str, Any] | None) -> SessionType:
    """从运行时 config 中严格解析 session_type。"""
    configurable = (config or {}).get("configurable", {})
    if not isinstance(configurable, Mapping):
        raise InvalidSessionTypeError(
            "configurable.session_type is required and must be one of: coaching, onboarding"
        )
    return require_session_type(configurable.get("session_type"))


def get_current_session_type() -> SessionType:
    """从当前 LangGraph 运行时 config 严格读取 session_type。"""
    try:
        return resolve_session_type(get_config())
    except InvalidSessionTypeError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InvalidSessionTypeError(
            "configurable.session_type is required and must be one of: coaching, onboarding"
        ) from exc


def get_session_profile(session_type: SessionType) -> SessionProfile:
    """返回指定会话类型的配置。"""
    return _SESSION_PROFILES[session_type]


def list_session_profiles() -> tuple[SessionProfile, ...]:
    """按稳定顺序返回当前支持的会话配置。"""
    return tuple(_SESSION_PROFILES[session_type] for session_type in ("coaching", "onboarding"))
