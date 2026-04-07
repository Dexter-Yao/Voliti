# ABOUTME: SessionModeMiddleware — 按 configurable.session_mode 动态注入 prompt 段落
# ABOUTME: onboarding 模式下追加 profile 采集指令，coaching 模式不注入任何内容

from __future__ import annotations

from voliti.middleware.base import PromptInjectionMiddleware

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


class SessionModeMiddleware(PromptInjectionMiddleware):
    """按 session_mode 动态追加 prompt 段落到 system message。

    coaching 模式：不注入任何内容（默认行为）
    onboarding 模式：追加 profile 采集指令
    """

    def should_inject(self) -> bool:
        return _get_session_mode() == "onboarding"

    def get_prompt(self) -> str:
        return _ONBOARDING_PROMPT
