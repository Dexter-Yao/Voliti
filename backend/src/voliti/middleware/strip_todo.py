# ABOUTME: StripDeepAgentDefaultsMiddleware — 剥离 DeepAgent 内置的无关 prompt 和工具
# ABOUTME: 移除 BASE_AGENT_PROMPT (~1,650 chars) 和 TodoList prompt+工具 (~4,728 chars)

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

_TODO_MARKER = "`write_todos`"
"""TodoListMiddleware 注入的 system prompt 中的特征字符串。"""

_BASE_PROMPT_MARKER = "You are a Deep Agent,"
"""BASE_AGENT_PROMPT 的开头标记，用于子串匹配移除。"""


def _strip_base_agent_prompt(text: str) -> str:
    """从字符串中移除 BASE_AGENT_PROMPT 子串。

    BASE_AGENT_PROMPT 在 create_deep_agent() 中通过字符串拼接
    追加到用户 system_prompt 后面，格式为 "\\n\\n" + BASE_AGENT_PROMPT。
    """
    idx = text.find(_BASE_PROMPT_MARKER)
    if idx < 0:
        return text
    # 移除标记之前的 \n\n 分隔符
    start = idx
    while start > 0 and text[start - 1] in "\n":
        start -= 1
    removed_len = len(text) - start
    logger.debug("StripDefaultsMW: removed BASE_AGENT_PROMPT (%d chars)", removed_len)
    return text[:start]


def _strip_blocks(system_message: SystemMessage | None) -> SystemMessage | None:
    """从 system_message 中移除 TodoList 段落和 BASE_AGENT_PROMPT。"""
    if system_message is None:
        return None

    changed = False
    new_blocks: list[dict[str, str]] = []

    for block in system_message.content_blocks:
        if not isinstance(block, dict):
            new_blocks.append(block)
            continue

        text = block.get("text", "")

        # 跳过 TodoList 段落（独立 content_block）
        if _TODO_MARKER in text:
            changed = True
            continue

        # 从拼接块中移除 BASE_AGENT_PROMPT（子串）
        cleaned = _strip_base_agent_prompt(text)
        if cleaned != text:
            changed = True
            if cleaned.strip():
                new_blocks.append({"type": "text", "text": cleaned})
        else:
            new_blocks.append(block)

    if not changed:
        return system_message

    logger.debug("StripDefaultsMW: cleaned system_message blocks")
    return SystemMessage(content_blocks=new_blocks) if new_blocks else None


def _strip_todo_tools(tools: list[Any]) -> list[Any]:
    """从 tools 列表中移除 write_todos 工具。"""
    filtered = [
        t for t in tools
        if not (hasattr(t, "name") and t.name == "write_todos")
    ]
    if len(filtered) < len(tools):
        logger.debug("StripDefaultsMW: removed write_todos tool")
    return filtered


class StripDeepAgentDefaultsMiddleware(AgentMiddleware):
    """剥离 DeepAgent 内置的无关 prompt 和工具。

    移除内容：
    1. BASE_AGENT_PROMPT (~1,650 chars) — 通用 AI 助手行为指导，
       与 Coach 自有的身份定义和语调冲突
    2. TodoListMiddleware 的 system prompt (~1,074 chars) 和
       write_todos 工具 (~3,654 chars tool schema) — Coach 不需要 todo 管理

    总计节省 ~6,378 chars per LLM call。
    """

    tools: list = []

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        cleaned_system = _strip_blocks(request.system_message)
        cleaned_tools = _strip_todo_tools(list(request.tools))
        request = request.override(system_message=cleaned_system, tools=cleaned_tools)
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[Any]],
    ) -> Any:
        cleaned_system = _strip_blocks(request.system_message)
        cleaned_tools = _strip_todo_tools(list(request.tools))
        request = request.override(system_message=cleaned_system, tools=cleaned_tools)
        return await handler(request)


# 向后兼容别名
StripTodoMiddleware = StripDeepAgentDefaultsMiddleware
