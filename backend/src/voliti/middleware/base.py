# ABOUTME: Prompt 注入 Middleware 基类 — 消除 sync/async 重复代码
# ABOUTME: 子类只需实现 should_inject() 和 get_prompt()，基类处理 wrap_model_call 的双路径

from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from deepagents.middleware._utils import append_to_system_message
from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse

logger = logging.getLogger(__name__)


def get_session_mode() -> str:
    """从当前 LangGraph 运行时 config 读取 session_mode。"""
    try:
        from langgraph.config import get_config

        cfg = get_config()
        return cfg.get("configurable", {}).get("session_mode", "coaching")
    except Exception:  # noqa: BLE001
        return "coaching"


class PromptInjectionMiddleware(AgentMiddleware):
    """按条件向 system message 注入 prompt 段落的基类。

    子类实现两个方法：
    - should_inject() → 是否注入
    - get_prompt() → 注入的内容
    """

    tools: list = []

    @abstractmethod
    def should_inject(self) -> bool:
        """判断是否应注入 prompt。"""

    @abstractmethod
    def get_prompt(self) -> str:
        """返回要注入的 prompt 内容。"""

    def _inject(self, request: ModelRequest) -> ModelRequest:
        if not self.should_inject():
            return request

        prompt = self.get_prompt()
        if not prompt:
            return request

        new_system = append_to_system_message(request.system_message, prompt)
        request = request.override(system_message=new_system)
        logger.debug("%s: injected prompt", type(self).__name__)
        return request

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        return handler(self._inject(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Any],
    ) -> Any:
        return await handler(self._inject(request))
