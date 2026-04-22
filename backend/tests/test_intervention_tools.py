# ABOUTME: Coach skills 专用工具测试
# ABOUTME: 校验动态加载能发现各 skill tool，并验证 intervention / witness-card 的核心契约

import importlib.util
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from voliti.agent import COACH_TOOLS, _load_skill_tools
from voliti.store_contract import COACH_SKILLS_ROOT


_EXPECTED_KINDS = {
    "future-self-dialogue",
    "scenario-rehearsal",
    "metaphor-collaboration",
    "cognitive-reframing",
}
_EXPECTED_SKILL_TOOL_NAMES = {
    "fan_out_future_self_dialogue",
    "fan_out_scenario_rehearsal",
    "fan_out_metaphor_collaboration",
    "fan_out_cognitive_reframing",
    "issue_witness_card",
    "create_plan",
    "create_successor_plan",
    "set_goal_status",
    "update_week_narrative",
    "revise_plan",
    "fan_out_plan_builder",
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
    """按 KIND 常量建立 intervention_kind → tool 索引。

    仅覆盖四个干预 skill 目录（其 tool.py 导出 KIND 常量）。Plan Builder 这类
    非 intervention 的 fan_out_* 工具（skill 目录名与工具名不同构）自动跳过。
    """
    index: dict[str, Any] = {}
    for tool in COACH_TOOLS:
        if not tool.name.startswith("fan_out_") or tool.name == "fan_out":
            continue
        skill_dir = tool.name.removeprefix("fan_out_").replace("_", "-")
        tool_path = COACH_SKILLS_ROOT / skill_dir / "tool.py"
        if not tool_path.is_file():
            continue   # 非 intervention 工具（如 Plan Builder）走 plan/ 目录
        module = _load_tool_module(tool_path)
        kind = getattr(module, "KIND", None)
        if kind is None:
            continue
        index[kind] = tool
    return index


class TestDynamicLoading:
    """_load_skill_tools 动态加载行为。"""

    def test_finds_all_registered_skill_tools(self) -> None:
        """应发现 4 个 intervention + witness-card + Plan 的 6 个 tool，共 11 个。"""
        tools = _load_skill_tools()
        assert len(tools) == len(_EXPECTED_SKILL_TOOL_NAMES)

    def test_skill_tool_names_match_contract(self) -> None:
        """技能工具名应满足统一装载契约。"""
        tools = _load_skill_tools()
        names = {t.name for t in tools}
        assert names == _EXPECTED_SKILL_TOOL_NAMES

    def test_coach_tools_includes_generic_and_interventions(self) -> None:
        """COACH_TOOLS 包含通用工具、四个干预工具和 witness-card 工具。"""
        names = {t.name for t in COACH_TOOLS}
        assert "fan_out" in names
        assert "add_forward_marker" in names
        for kind in _EXPECTED_KINDS:
            assert f"fan_out_{kind.replace('-', '_')}" in names
        assert "issue_witness_card" in names


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


def _witness_card_tool() -> Any:
    for tool in COACH_TOOLS:
        if tool.name == "issue_witness_card":
            return tool
    raise AssertionError("issue_witness_card tool not found")


class TestWitnessCardTool:
    """Witness Card skill tool 契约。"""

    def test_signature_accepts_only_structured_fields(self) -> None:
        tool = _witness_card_tool()
        fields = set(tool.args_schema.model_fields.keys())
        assert fields == {
            "achievement_title",
            "achievement_type",
            "emotional_tone",
            "evidence_summary",
            "scene_anchors",
            "narrative",
            "chapter_id",
            "linked_lifesign_id",
            "user_quote",
            "aspect_ratio",
        }
