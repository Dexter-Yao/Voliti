# ABOUTME: StripTodoMiddleware — 从 DeepAgent 内置栈中移除 TodoListMiddleware 的注入
# ABOUTME: 过滤 system_message 中的 write_todos prompt 段落，并从 tools 列表中移除 write_todos 工具

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

_TODO_MARKER = "`write_todos`"
"""TodoListMiddleware 注入的 system prompt 中的特征字符串。"""


def _strip_todo_blocks(system_message: SystemMessage | None) -> SystemMessage | None:
    """从 system_message 的 content_blocks 中移除包含 write_todos 指令的段落。"""
    if system_message is None:
        return None
    filtered = [
        block
        for block in system_message.content_blocks
        if not (isinstance(block, dict) and _TODO_MARKER in block.get("text", ""))
    ]
    if len(filtered) == len(system_message.content_blocks):
        return system_message
    logger.debug("StripTodoMW: removed %d todo block(s)", len(system_message.content_blocks) - len(filtered))
    return SystemMessage(content_blocks=filtered) if filtered else None


def _strip_todo_tools(tools: list[Any]) -> list[Any]:
    """从 tools 列表中移除 write_todos 工具。"""
    filtered = [
        t for t in tools
        if not (hasattr(t, "name") and t.name == "write_todos")
    ]
    if len(filtered) < len(tools):
        logger.debug("StripTodoMW: removed write_todos tool")
    return filtered


class StripTodoMiddleware(AgentMiddleware):
    """移除 DeepAgent 内置 TodoListMiddleware 注入的 prompt 和工具。

    DeepAgent 的 create_deep_agent() 无条件添加 TodoListMiddleware，
    但 Voliti Coach 场景不需要 todo 管理功能。此 middleware 在每次
    LLM 调用前清除 TodoList 相关的 system prompt 段落和 write_todos 工具，
    节省 ~4,700 chars 的无效 token 消耗。
    """

    tools: list = []

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        cleaned_system = _strip_todo_blocks(request.system_message)
        cleaned_tools = _strip_todo_tools(list(request.tools))
        request = request.override(system_message=cleaned_system, tools=cleaned_tools)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[Any]],
    ) -> Any:
        cleaned_system = _strip_todo_blocks(request.system_message)
        cleaned_tools = _strip_todo_tools(list(request.tools))
        request = request.override(system_message=cleaned_system, tools=cleaned_tools)
        return await handler(request)
