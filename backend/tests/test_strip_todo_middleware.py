# ABOUTME: StripTodoMiddleware 单元测试
# ABOUTME: 验证 write_todos prompt 段落和工具在 system_message / tools 中被正确剥离

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import SystemMessage

from voliti.middleware.strip_todo import (
    StripTodoMiddleware,
    _strip_todo_blocks,
    _strip_todo_tools,
)


def _make_system_message(*texts: str) -> SystemMessage:
    """构造包含多个 text block 的 SystemMessage。"""
    blocks = [{"type": "text", "text": t} for t in texts]
    return SystemMessage(content_blocks=blocks)


def _make_tool(name: str) -> MagicMock:
    """构造 BaseTool mock。"""
    tool = MagicMock()
    tool.name = name
    return tool


class TestStripTodoBlocks:
    """_strip_todo_blocks 行为测试。"""

    def test_removes_block_containing_write_todos(self) -> None:
        msg = _make_system_message(
            "You are a coach.",
            "\n\n## `write_todos`\n\nUse this to manage tasks...",
            "\n\n## Filesystem Tools...",
        )
        result = _strip_todo_blocks(msg)
        assert result is not None
        assert len(result.content_blocks) == 2
        for block in result.content_blocks:
            assert "`write_todos`" not in block["text"]

    def test_preserves_all_blocks_when_no_todo(self) -> None:
        msg = _make_system_message("Block 1", "Block 2")
        result = _strip_todo_blocks(msg)
        assert result is msg  # 原对象返回，无复制

    def test_returns_none_for_none_input(self) -> None:
        assert _strip_todo_blocks(None) is None

    def test_returns_none_when_all_blocks_removed(self) -> None:
        msg = _make_system_message("`write_todos` only block")
        result = _strip_todo_blocks(msg)
        assert result is None


class TestStripTodoTools:
    """_strip_todo_tools 行为测试。"""

    def test_removes_write_todos_tool(self) -> None:
        tools = [_make_tool("read_file"), _make_tool("write_todos"), _make_tool("edit_file")]
        result = _strip_todo_tools(tools)
        assert len(result) == 2
        assert all(t.name != "write_todos" for t in result)

    def test_preserves_all_when_no_write_todos(self) -> None:
        tools = [_make_tool("read_file"), _make_tool("edit_file")]
        result = _strip_todo_tools(tools)
        assert len(result) == 2

    def test_handles_empty_list(self) -> None:
        assert _strip_todo_tools([]) == []

    def test_handles_dict_tools(self) -> None:
        tools: list = [{"type": "function", "function": {"name": "custom"}}]
        result = _strip_todo_tools(tools)
        assert len(result) == 1


class TestStripTodoMiddleware:
    """StripTodoMiddleware 集成行为测试。"""

    def test_strips_both_prompt_and_tool(self) -> None:
        mw = StripTodoMiddleware()
        msg = _make_system_message(
            "Coach prompt",
            "\n\n## `write_todos`\n\nTodo instructions...",
        )
        tools = [_make_tool("fan_out"), _make_tool("write_todos")]

        request = MagicMock()
        request.system_message = msg
        request.tools = tools

        captured = {}

        def fake_handler(req: MagicMock) -> MagicMock:
            captured["system_blocks"] = len(req.system_message.content_blocks)
            captured["tools"] = [t.name for t in req.tools]
            return MagicMock()

        request.override.return_value = MagicMock()
        # 让 override 返回的 mock 带上过滤后的值
        def side_effect(**kwargs: object) -> MagicMock:
            result = MagicMock()
            result.system_message = kwargs.get("system_message", msg)
            result.tools = kwargs.get("tools", tools)
            return result

        request.override.side_effect = side_effect

        mw.wrap_model_call(request, fake_handler)

        assert captured["system_blocks"] == 1
        assert "write_todos" not in captured["tools"]
        assert "fan_out" in captured["tools"]
