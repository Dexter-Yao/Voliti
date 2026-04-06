# ABOUTME: SessionModeMiddleware — 按 configurable.session_mode 动态注入 prompt 段落
# ABOUTME: onboarding 模式下追加 profile 采集指令，coaching 模式不注入任何内容

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from deepagents.middleware._utils import append_to_system_message

logger = logging.getLogger(__name__)

_ONBOARDING_PROMPT = """
## Session Mode: Profile Collection

This is a profile collection session, not a regular coaching session. Your focus:
- Actively and naturally collect personal information to build the user's profile
- Ask about goals, lifestyle patterns, constraints, preferences, and context
- Write collected information to the user's profile via Store operations
- If the user initiates regular coaching conversation (reporting meals, asking for advice, discussing struggles), gently redirect: suggest they return to the main coaching session for that topic
""".strip()


def _get_session_mode() -> str:
    """从当前 LangGraph 运行时 config 读取 session_mode。"""
    try:
        from langgraph.config import get_config

        cfg = get_config()
        return cfg.get("configurable", {}).get("session_mode", "coaching")
    except Exception:  # noqa: BLE001
        return "coaching"


class SessionModeMiddleware(AgentMiddleware):
    """按 session_mode 动态追加 prompt 段落到 system message。

    coaching 模式：不注入任何内容（默认行为）
    onboarding 模式：追加 profile 采集指令
    """

    tools: list = []

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        session_mode = _get_session_mode()

        if session_mode == "onboarding":
            new_system = append_to_system_message(
                request.system_message, _ONBOARDING_PROMPT
            )
            request = request.override(system_message=new_system)
            logger.debug("SessionModeMiddleware: injected onboarding prompt")

        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Any],
    ) -> Any:
        session_mode = _get_session_mode()

        if session_mode == "onboarding":
            new_system = append_to_system_message(
                request.system_message, _ONBOARDING_PROMPT
            )
            request = request.override(system_message=new_system)
            logger.debug("SessionModeMiddleware: injected onboarding prompt (async)")

        return await handler(request)
