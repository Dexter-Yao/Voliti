# ABOUTME: SessionType 共享类型定义
# ABOUTME: 为 backend 运行时与契约测试提供唯一的会话类型与会话配置事实来源

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeGuard

SessionType = Literal["coaching", "onboarding"]
"""Voliti 当前支持的会话类型。"""

DEFAULT_SESSION_TYPE: SessionType = "coaching"
"""默认会话类型。"""


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


def get_session_profile(session_type: SessionType) -> SessionProfile:
    """返回指定会话类型的配置。"""
    return _SESSION_PROFILES[session_type]


def list_session_profiles() -> tuple[SessionProfile, ...]:
    """按稳定顺序返回当前支持的会话配置。"""
    return tuple(_SESSION_PROFILES[session_type] for session_type in ("coaching", "onboarding"))
