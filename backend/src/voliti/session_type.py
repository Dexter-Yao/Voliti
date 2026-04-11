# ABOUTME: SessionType 共享类型定义
# ABOUTME: 为 backend 运行时与契约测试提供唯一的会话类型事实来源

from __future__ import annotations

from typing import Literal, TypeGuard

SessionType = Literal["coaching", "onboarding"]
"""Voliti 当前支持的会话类型。"""

DEFAULT_SESSION_TYPE: SessionType = "coaching"
"""默认会话类型。"""


def is_session_type(value: object) -> TypeGuard[SessionType]:
    """判断给定值是否为受支持的会话类型。"""
    return value in ("coaching", "onboarding")


def coerce_session_type(value: object) -> SessionType | None:
    """将任意值收敛为 SessionType。"""
    if is_session_type(value):
        return value
    return None
