# ABOUTME: Voliti middleware 基础组件
# ABOUTME: 提供 prompt 注入基类与记忆生命周期 policy middleware，作为现有 DeepAgent hooks 的最小落点

from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from deepagents.middleware._utils import append_to_system_message
from langchain.tools.tool_node import ToolCallRequest
from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import ToolMessage

from voliti.semantic_memory import (
    classify_semantic_memory_path,
    is_authoritative_semantic_memory_path,
)
from voliti.session_type import SessionType, get_current_session_type

logger = logging.getLogger(__name__)

_WRITE_TOOLS = frozenset({"edit_file", "write_file"})
_SEMANTIC_WRITE_CONFIRMED_KEY = "semantic_write_confirmed"
_SEMANTIC_WRITE_SOURCE_KIND_KEY = "semantic_write_source_kind"
_SEMANTIC_WRITE_SOURCE_NAME_KEY = "semantic_write_source_name"


def get_session_type() -> SessionType:
    """从当前 LangGraph 运行时 config 读取 session_type。"""
    return get_current_session_type()


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

    def _extract_target_path(self, request: ToolCallRequest) -> str | None:
        tool_call = request.tool_call
        if not isinstance(tool_call, dict):
            return None
        args = tool_call.get("args", {})
        if not isinstance(args, dict):
            return None
        path = args.get("file_path")
        if isinstance(path, str) and path:
            return path
        return None

    def _build_blocked_write_message(
        self,
        *,
        tool_name: str,
        tool_call_id: str,
        target_path: str,
    ) -> ToolMessage:
        return ToolMessage(
            content=(
                "Semantic memory promotion is not allowed for this write target. "
                f"Target path: {target_path}. "
                "Direct authoritative writes require explicit confirmed semantic write context."
            ),
            name=tool_name,
            tool_call_id=tool_call_id,
            status="error",
        )

    def _allows_authoritative_write(self, request: ToolCallRequest, target_path: str) -> bool:
        configurable = request.runtime.config.get("configurable", {})
        if not isinstance(configurable, dict):
            return False
        return self.can_promote(
            source_kind=str(configurable.get(_SEMANTIC_WRITE_SOURCE_KIND_KEY, "")),
            target_path=target_path,
            source_name=(
                str(configurable.get(_SEMANTIC_WRITE_SOURCE_NAME_KEY))
                if configurable.get(_SEMANTIC_WRITE_SOURCE_NAME_KEY) is not None
                else None
            ),
            confirmed=configurable.get(_SEMANTIC_WRITE_CONFIRMED_KEY) is True,
        )

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> Any:
        """在真实写入面阻止未确认的权威语义写入。"""
        if not isinstance(request, ToolCallRequest):
            return handler(request)
        tool_name = request.tool_call.get("name", "")
        if tool_name not in _WRITE_TOOLS:
            return handler(request)

        target_path = self._extract_target_path(request)
        if target_path is None:
            return handler(request)

        if classify_semantic_memory_path(target_path) != "authoritative_semantic":
            return handler(request)

        if self._allows_authoritative_write(request, target_path):
            return handler(request)

        return self._build_blocked_write_message(
            tool_name=tool_name or "tool",
            tool_call_id=request.tool_call.get("id", ""),
            target_path=target_path,
        )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Any],
    ) -> Any:
        """在真实写入面阻止未确认的权威语义写入。"""
        if not isinstance(request, ToolCallRequest):
            return await handler(request)
        tool_name = request.tool_call.get("name", "")
        if tool_name not in _WRITE_TOOLS:
            return await handler(request)

        target_path = self._extract_target_path(request)
        if target_path is None:
            return await handler(request)

        if classify_semantic_memory_path(target_path) != "authoritative_semantic":
            return await handler(request)

        if self._allows_authoritative_write(request, target_path):
            return await handler(request)

        return self._build_blocked_write_message(
            tool_name=tool_name or "tool",
            tool_call_id=request.tool_call.get("id", ""),
            target_path=target_path,
        )

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
