# ABOUTME: fan_out 工具测试
# ABOUTME: 验证 fan_out 通过 interrupt() 采集用户响应并正确处理 submit/reject/skip 三种路径

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from voliti.tools.fan_out import fan_out


class TestFanOutSubmit:
    """fan_out submit 路径测试。"""

    @patch("voliti.tools.fan_out.interrupt")
    def test_returns_data_summary(self, mock_interrupt) -> None:  # noqa: ANN001
        """submit 应返回包含用户数据的摘要字符串。"""
        mock_interrupt.return_value = {
            "action": "submit",
            "data": {"energy": 7, "mood": 6},
        }
        result = fan_out.invoke({
            "components": [
                {"kind": "slider", "name": "energy", "label": "Energy"},
            ],
        })
        assert "energy=7" in result
        assert "mood=6" in result

    @patch("voliti.tools.fan_out.interrupt")
    def test_submit_with_empty_data(self, mock_interrupt) -> None:  # noqa: ANN001
        """submit 但无输入组件时应正常返回。"""
        mock_interrupt.return_value = {"action": "submit", "data": {}}
        result = fan_out.invoke({
            "components": [{"kind": "text", "content": "hello"}],
        })
        assert isinstance(result, str)


class TestFanOutReject:
    """fan_out reject 路径测试。"""

    @patch("voliti.tools.fan_out.interrupt")
    def test_returns_cancel_message(self, mock_interrupt) -> None:  # noqa: ANN001
        """reject 应返回取消信息。"""
        mock_interrupt.return_value = {"action": "reject"}
        result = fan_out.invoke({
            "components": [{"kind": "text", "content": "hello"}],
        })
        assert "cancel" in result.lower()


class TestFanOutSkip:
    """fan_out skip 路径测试。"""

    @patch("voliti.tools.fan_out.interrupt")
    def test_returns_skip_message(self, mock_interrupt) -> None:  # noqa: ANN001
        """skip 应返回跳过信息。"""
        mock_interrupt.return_value = {"action": "skip"}
        result = fan_out.invoke({
            "components": [{"kind": "text", "content": "hello"}],
        })
        assert "skip" in result.lower()


class TestFanOutPayload:
    """fan_out payload 构建测试。"""

    @patch("voliti.tools.fan_out.interrupt")
    def test_interrupt_receives_a2ui_payload(self, mock_interrupt) -> None:  # noqa: ANN001
        """interrupt 应收到完整的 A2UI payload dict。"""
        mock_interrupt.return_value = {"action": "submit", "data": {}}
        fan_out.invoke({
            "components": [{"kind": "text", "content": "hello"}],
        })
        payload = mock_interrupt.call_args[0][0]
        assert payload["type"] == "a2ui"
        assert len(payload["components"]) == 1
        assert payload["components"][0]["kind"] == "text"

    @patch("voliti.tools.fan_out.interrupt")
    def test_default_layout_is_three_quarter(self, mock_interrupt) -> None:  # noqa: ANN001
        """默认 layout 应为 three-quarter。"""
        mock_interrupt.return_value = {"action": "submit", "data": {}}
        fan_out.invoke({
            "components": [{"kind": "text", "content": "hi"}],
        })
        payload = mock_interrupt.call_args[0][0]
        assert payload["layout"] == "three-quarter"

    @patch("voliti.tools.fan_out.interrupt")
    def test_passes_full_layout(self, mock_interrupt) -> None:  # noqa: ANN001
        """layout=full 应透传到 payload。"""
        mock_interrupt.return_value = {"action": "submit", "data": {}}
        fan_out.invoke({
            "components": [{"kind": "text", "content": "hi"}],
            "layout": "full",
        })
        payload = mock_interrupt.call_args[0][0]
        assert payload["layout"] == "full"


class TestFanOutValidation:
    """fan_out 输入验证测试。"""

    def test_invalid_component_raises(self) -> None:
        """无效 kind 应触发 ValidationError。"""
        with pytest.raises(ValidationError):
            fan_out.invoke({"components": [{"kind": "invalid"}]})

    @patch("voliti.tools.fan_out.interrupt")
    def test_multiple_components(self, mock_interrupt) -> None:  # noqa: ANN001
        """多组件 payload 应正确组装。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"x": 5}}
        fan_out.invoke({
            "components": [
                {"kind": "text", "content": "Rate your energy:"},
                {"kind": "slider", "name": "x", "label": "Energy"},
            ],
        })
        payload = mock_interrupt.call_args[0][0]
        assert len(payload["components"]) == 2
        assert payload["components"][0]["kind"] == "text"
        assert payload["components"][1]["kind"] == "slider"
