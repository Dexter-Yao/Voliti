# ABOUTME: StripDeepAgentDefaultsMiddleware 单元测试
# ABOUTME: 验证 BASE_AGENT_PROMPT / write_todos prompt / write_todos 工具的剥离行为

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import SystemMessage

from voliti.middleware.strip_todo import (
    StripDeepAgentDefaultsMiddleware,
    StripTodoMiddleware,
    _strip_base_agent_prompt,
    _strip_blocks,
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


# ── BASE_AGENT_PROMPT 子串剥离 ──────────────────────────────────────


class TestStripBaseAgentPrompt:
    """_strip_base_agent_prompt 行为测试。"""

    def test_removes_base_prompt_from_concatenated_string(self) -> None:
        text = "Coach system prompt content.\n\nYou are a Deep Agent, an AI assistant..."
        result = _strip_base_agent_prompt(text)
        assert result == "Coach system prompt content."
        assert "Deep Agent" not in result

    def test_preserves_text_without_marker(self) -> None:
        text = "Coach system prompt only."
        assert _strip_base_agent_prompt(text) == text

    def test_strips_preceding_newlines(self) -> None:
        text = "Content\n\nYou are a Deep Agent, blah"
        result = _strip_base_agent_prompt(text)
        assert result == "Content"

    def test_handles_marker_at_start(self) -> None:
        text = "You are a Deep Agent, an AI..."
        result = _strip_base_agent_prompt(text)
        assert result == ""


class TestStripBlocks:
    """_strip_blocks 综合行为测试。"""

    def test_removes_todo_block(self) -> None:
        msg = _make_system_message(
            "Coach prompt",
            "\n\n## `write_todos`\n\nUse this to manage tasks...",
            "\n\n## Filesystem Tools...",
        )
        result = _strip_blocks(msg)
        assert result is not None
        assert len(result.content_blocks) == 2
        for block in result.content_blocks:
            assert "`write_todos`" not in block["text"]

    def test_removes_base_prompt_from_concatenated_block(self) -> None:
        msg = _make_system_message(
            "Coach prompt content\n\nYou are a Deep Agent, an AI assistant that helps users..."
        )
        result = _strip_blocks(msg)
        assert result is not None
        assert len(result.content_blocks) == 1
        assert "Deep Agent" not in result.content_blocks[0]["text"]
        assert "Coach prompt content" in result.content_blocks[0]["text"]

    def test_removes_both_todo_and_base_prompt(self) -> None:
        msg = _make_system_message(
            "Coach prompt\n\nYou are a Deep Agent, an AI...",
            "\n\n## `write_todos`\n\nTodo stuff",
            "\n\nFilesystem prompt",
        )
        result = _strip_blocks(msg)
        assert result is not None
        assert len(result.content_blocks) == 2
        all_text = " ".join(b["text"] for b in result.content_blocks)
        assert "Deep Agent" not in all_text
        assert "`write_todos`" not in all_text
        assert "Coach prompt" in all_text
        assert "Filesystem prompt" in all_text

    def test_preserves_unchanged_message(self) -> None:
        msg = _make_system_message("Block 1", "Block 2")
        result = _strip_blocks(msg)
        assert result is msg

    def test_returns_none_for_none_input(self) -> None:
        assert _strip_blocks(None) is None

    def test_returns_none_when_all_blocks_removed(self) -> None:
        msg = _make_system_message("`write_todos` only block")
        result = _strip_blocks(msg)
        assert result is None


# ── 工具剥离 ────────────────────────────────────────────────────────


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


# ── Middleware 集成 ──────────────────────────────────────────────────


class TestStripDeepAgentDefaultsMiddleware:
    """StripDeepAgentDefaultsMiddleware 集成行为测试。"""

    def test_strips_all_defaults(self) -> None:
        mw = StripDeepAgentDefaultsMiddleware()
        msg = _make_system_message(
            "Coach prompt\n\nYou are a Deep Agent, an AI...",
            "\n\n## `write_todos`\n\nTodo instructions...",
        )
        tools = [_make_tool("fan_out"), _make_tool("write_todos")]

        request = MagicMock()
        request.system_message = msg
        request.tools = tools

        captured: dict = {}

        def fake_handler(req: MagicMock) -> MagicMock:
            captured["system_blocks"] = len(req.system_message.content_blocks)
            captured["system_text"] = req.system_message.content_blocks[0]["text"]
            captured["tools"] = [t.name for t in req.tools]
            return MagicMock()

        def side_effect(**kwargs: object) -> MagicMock:
            result = MagicMock()
            result.system_message = kwargs.get("system_message", msg)
            result.tools = kwargs.get("tools", tools)
            return result

        request.override.side_effect = side_effect

        mw.wrap_model_call(request, fake_handler)

        assert captured["system_blocks"] == 1
        assert "Deep Agent" not in captured["system_text"]
        assert "write_todos" not in captured["tools"]
        assert "fan_out" in captured["tools"]


class TestBackwardCompatAlias:
    """向后兼容别名测试。"""

    def test_alias_is_same_class(self) -> None:
        assert StripTodoMiddleware is StripDeepAgentDefaultsMiddleware
