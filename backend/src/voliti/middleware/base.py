# ABOUTME: Voliti middleware 基础组件
# ABOUTME: 提供 prompt 注入基类与记忆生命周期 policy middleware，作为现有 DeepAgent hooks 的最小落点

from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from deepagents.middleware._utils import append_to_system_message
from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse

from voliti.semantic_memory import is_authoritative_semantic_memory_path
from voliti.session_type import DEFAULT_SESSION_TYPE, SessionType, coerce_session_type

logger = logging.getLogger(__name__)


def get_session_type() -> SessionType:
    """从当前 LangGraph 运行时 config 读取 session_type。"""
    try:
        from langgraph.config import get_config

        cfg = get_config()
        value = cfg.get("configurable", {}).get("session_type")
        return coerce_session_type(value) or DEFAULT_SESSION_TYPE
    except Exception:  # noqa: BLE001
        return DEFAULT_SESSION_TYPE


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


class MemoryLifecycleMiddleware(AgentMiddleware):
    """记忆生命周期 policy middleware。

    当前阶段只承担两类职责：
    1. 占住 `wrap_tool_call` / `after_model` / `after_agent` 的正式落点；
    2. 统一表达 promotion 禁止规则，避免 archive、runtime、observability
       或单次 journey analysis 摘要被直接写入权威长期语义。
    """

    tools: list = []

    def can_promote(
        self,
        *,
        source_kind: str,
        target_path: str,
        source_name: str | None,
        confirmed: bool,
    ) -> bool:
        """判断给定输入是否允许晋升为权威长期语义。"""
        if not confirmed:
            return False
        if not is_authoritative_semantic_memory_path(target_path):
            return False
        if source_kind != "candidate_signal":
            return False
        if source_name == "journey_analysis":
            return False
        return True

    def wrap_tool_call(self, request: Any, handler: Callable[[Any], Any]) -> Any:
        """当前阶段只保留 tool capture 的正式 hook 落点。"""
        return handler(request)

    async def awrap_tool_call(self, request: Any, handler: Callable[[Any], Any]) -> Any:
        """当前阶段只保留异步 tool capture 的正式 hook 落点。"""
        return await handler(request)

    def after_model(self, state: Any, runtime: Any) -> None:
        """当前阶段不在 after_model 执行 promotion。"""
        return None

    async def aafter_model(self, state: Any, runtime: Any) -> None:
        """当前阶段不在 after_model 执行 promotion。"""
        return None

    def after_agent(self, state: Any, runtime: Any) -> None:
        """当前阶段占住 consolidation 落点，但不引入后台整理逻辑。"""
        return None

    async def aafter_agent(self, state: Any, runtime: Any) -> None:
        """当前阶段占住 consolidation 落点，但不引入后台整理逻辑。"""
        return None
