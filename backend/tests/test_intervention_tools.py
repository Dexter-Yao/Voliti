# ABOUTME: 四种 intervention 专用 A2UI 工具测试
# ABOUTME: 校验 metadata / layout 由工具硬编码、动态加载能发现四工具、_fan_out_core 正常透传

import importlib.util
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from voliti.agent import COACH_TOOLS, _load_intervention_tools
from voliti.store_contract import COACH_SKILLS_ROOT


_EXPECTED_KINDS = {
    "future-self-dialogue",
    "scenario-rehearsal",
    "metaphor-collaboration",
    "cognitive-reframing",
}


def _load_tool_module(tool_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        f"voliti_intervention_tools_test.{tool_path.parent.name.replace('-', '_')}",
        tool_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _intervention_tools() -> dict[str, Any]:
    """按 KIND 常量建立 intervention_kind → tool 索引。"""
    index: dict[str, Any] = {}
    for tool in COACH_TOOLS:
        if not tool.name.startswith("fan_out_") or tool.name == "fan_out":
            continue
        # 从对应 tool.py 的 KIND 常量定位，避免对工具名做字符串 replace
        skill_dir = tool.name.removeprefix("fan_out_").replace("_", "-")
        module = _load_tool_module(COACH_SKILLS_ROOT / skill_dir / "tool.py")
        index[module.KIND] = tool
    return index


class TestDynamicLoading:
    """_load_intervention_tools 动态加载行为。"""

    def test_finds_four_tools(self) -> None:
        """应发现四个 intervention skill 的 tool.py。"""
        tools = _load_intervention_tools()
        assert len(tools) == 4

    def test_tool_names_match_kinds(self) -> None:
        """工具函数名应为 fan_out_<intervention_kind>。"""
        tools = _load_intervention_tools()
        names = {t.name for t in tools}
        assert names == {
            "fan_out_future_self_dialogue",
            "fan_out_scenario_rehearsal",
            "fan_out_metaphor_collaboration",
            "fan_out_cognitive_reframing",
        }

    def test_coach_tools_includes_generic_and_interventions(self) -> None:
        """COACH_TOOLS 包含通用 fan_out、add_forward_marker 和四个专用工具。"""
        names = {t.name for t in COACH_TOOLS}
        assert "fan_out" in names
        assert "add_forward_marker" in names
        for kind in _EXPECTED_KINDS:
            assert f"fan_out_{kind.replace('-', '_')}" in names


class TestMetadataHardcoding:
    """四种工具的 metadata 必须由代码硬编码写入，不由 Coach 传参。"""

    @pytest.mark.parametrize("kind", sorted(_EXPECTED_KINDS))
    @patch("voliti.tools.fan_out.interrupt")
    def test_payload_metadata_carries_surface_and_kind(
        self, mock_interrupt, kind: str  # noqa: ANN001
    ) -> None:
        """payload.metadata 必须包含 surface=intervention 和正确的 intervention_kind。"""
        mock_interrupt.return_value = {"action": "submit", "data": {}}
        tool = _intervention_tools()[kind]

        tool.invoke({"components": [{"kind": "text", "text": "hello"}]})

        payload = mock_interrupt.call_args[0][0]
        assert payload["metadata"]["surface"] == "intervention"
        assert payload["metadata"]["intervention_kind"] == kind

    @pytest.mark.parametrize("kind", sorted(_EXPECTED_KINDS))
    @patch("voliti.tools.fan_out.interrupt")
    def test_layout_hardcoded_full(
        self, mock_interrupt, kind: str  # noqa: ANN001
    ) -> None:
        """所有 intervention 的 layout 必须硬编码为 'full'。"""
        mock_interrupt.return_value = {"action": "submit", "data": {}}
        tool = _intervention_tools()[kind]

        tool.invoke({"components": [{"kind": "text", "text": "hello"}]})

        payload = mock_interrupt.call_args[0][0]
        assert payload["layout"] == "full"

    @pytest.mark.parametrize("kind", sorted(_EXPECTED_KINDS))
    def test_tool_signature_does_not_accept_metadata(self, kind: str) -> None:
        """intervention 工具签名不应暴露 metadata / layout 参数。

        Coach 仅负责决策调哪个工具并传组件；metadata / layout 由代码硬编码。
        """
        tool = _intervention_tools()[kind]
        # langchain @tool 装饰器在 args_schema 上暴露可选参数
        fields = set(tool.args_schema.model_fields.keys())
        assert fields == {"components"}, (
            f"Tool {tool.name} must only accept `components`; got {fields}"
        )


class TestCoreResponseHandling:
    """_fan_out_core 的响应分支通过 intervention 工具同样生效。"""

    @patch("voliti.tools.fan_out.interrupt")
    def test_submit_with_data_returns_summary(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {
            "action": "submit",
            "data": {"reply": "hello future"},
        }
        tool = _intervention_tools()["future-self-dialogue"]
        result = tool.invoke(
            {
                "components": [
                    {"kind": "text", "text": "You said before..."},
                    {
                        "kind": "protocol_prompt",
                        "observation": "A calmer you",
                        "question": "Why did you start?",
                    },
                    {
                        "kind": "text_input",
                        "key": "reply",
                        "label": "Reply",
                    },
                ]
            }
        )
        assert "reply=hello future" in result

    @patch("voliti.tools.fan_out.interrupt")
    def test_reject_returns_cancel_message(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "reject"}
        tool = _intervention_tools()["metaphor-collaboration"]
        result = tool.invoke(
            {
                "components": [
                    {
                        "kind": "protocol_prompt",
                        "observation": "a balloon losing air",
                        "question": "what kind of balloon?",
                    },
                    {"kind": "text_input", "key": "reply", "label": ""},
                ]
            }
        )
        assert result == "User closed the panel without responding."

    @patch("voliti.tools.fan_out.interrupt")
    def test_reject_with_reason_is_forwarded(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {
            "action": "reject",
            "reason": "not ready today",
        }
        tool = _intervention_tools()["cognitive-reframing"]
        result = tool.invoke(
            {
                "components": [
                    {
                        "kind": "protocol_prompt",
                        "observation": "tonight ruined the week",
                        "question": "did you sign that =?",
                    },
                ]
            }
        )
        assert "User rejected: not ready today" == result

    @patch("voliti.tools.fan_out.interrupt")
    def test_skip_returns_skip_message(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "skip"}
        tool = _intervention_tools()["scenario-rehearsal"]
        result = tool.invoke(
            {
                "components": [
                    {
                        "kind": "text",
                        "text": "Friday dinner with dad",
                    },
                    {
                        "kind": "protocol_prompt",
                        "observation": "the toast moment",
                        "question": "rehearse together?",
                    },
                ]
            }
        )
        assert result == "User acknowledged but chose to skip."


class TestInvalidComponents:
    """组件校验失败时应返回提示而不抛异常。"""

    @pytest.mark.parametrize("kind", sorted(_EXPECTED_KINDS))
    def test_invalid_components_return_error_message(self, kind: str) -> None:
        """组件 kind 无效时应返回友好的错误提示。"""
        tool = _intervention_tools()[kind]
        result = tool.invoke(
            {"components": [{"kind": "nonexistent_kind", "text": "x"}]}
        )
        assert "validation errors" in result.lower()
