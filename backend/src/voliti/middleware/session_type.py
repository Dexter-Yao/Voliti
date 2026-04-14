# ABOUTME: SessionTypeMiddleware — 按 configurable.session_type 动态注入 prompt 段落
# ABOUTME: onboarding 类型下通过 PromptRegistry 加载 onboarding.j2 指令，coaching 类型保持默认教练流程

from __future__ import annotations

from voliti.config.prompts import PromptRegistry
from voliti.middleware.base import PromptInjectionMiddleware, get_session_type


class SessionTypeMiddleware(PromptInjectionMiddleware):
    """按 session_type 动态追加 prompt 段落到 system message。"""

    def should_inject(self) -> bool:
        return get_session_type() == "onboarding"

    def get_prompt(self) -> str:
        return PromptRegistry.get("onboarding")
