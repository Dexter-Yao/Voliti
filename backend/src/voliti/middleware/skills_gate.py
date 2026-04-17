# ABOUTME: SkillsGateMiddleware — 按 session_type 决定是否注入 skills 元数据到 system prompt
# ABOUTME: onboarding 会话不注入四份 intervention skill，保持引导节奏；coaching 会话正常注入

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from deepagents.middleware.skills import SkillsMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse

from voliti.session_type import InvalidSessionTypeError, get_current_session_type

logger = logging.getLogger(__name__)


class SkillsGateMiddleware(SkillsMiddleware):
    """仅在 coaching session 注入 skills 元数据的 SkillsMiddleware。

    继承 deepagents 原生 `SkillsMiddleware`，保留 `before_agent` / `abefore_agent`
    的 skills metadata 加载行为（无副作用，仅改 state），但在 `wrap_model_call` /
    `awrap_model_call` 层按 session_type 决定是否注入 system prompt：

    - coaching session → 调父类默认行为，注入四份 intervention skill 清单
    - onboarding session → 跳过注入，直接交给 handler 处理原始 request

    理由：onboarding 有自己的引导节奏，额外 skill 清单会稀释注意力且无触发机会。
    """

    def _should_inject(self) -> bool:
        try:
            return get_current_session_type() == "coaching"
        except InvalidSessionTypeError:
            # 配置缺失时保守不注入；上游 middleware 会抛错提示
            return False

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        if not self._should_inject():
            logger.debug("SkillsGate: skipping skill injection for non-coaching session")
            return handler(request)
        return super().wrap_model_call(request, handler)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        if not self._should_inject():
            logger.debug("SkillsGate: skipping skill injection for non-coaching session")
            return await handler(request)
        return await super().awrap_model_call(request, handler)
