# ABOUTME: SkillsGateMiddleware 条件注入逻辑测试
# ABOUTME: 验证按 session_type 决定 skills 元数据是否注入 system prompt

from unittest.mock import patch

from voliti.middleware.skills_gate import SkillsGateMiddleware
from voliti.session_type import InvalidSessionTypeError


def _make_gate() -> SkillsGateMiddleware:
    """构造最小可用的 SkillsGateMiddleware 实例（测试无需真实 backend）。"""
    return SkillsGateMiddleware(
        backend=lambda rt: None,  # 测试只用到 should_inject，不触发真实加载
        sources=["/skills/coach/"],
    )


class TestSkillsGateShouldInject:
    """should_inject 按 session_type 路由判定。"""

    def test_coaching_session_injects(self) -> None:
        gate = _make_gate()
        with patch(
            "voliti.middleware.skills_gate.get_current_session_type",
            return_value="coaching",
        ):
            assert gate.should_inject() is True

    def test_onboarding_session_does_not_inject(self) -> None:
        gate = _make_gate()
        with patch(
            "voliti.middleware.skills_gate.get_current_session_type",
            return_value="onboarding",
        ):
            assert gate.should_inject() is False

    def test_invalid_session_type_falls_back_to_no_inject(self) -> None:
        """运行时 config 缺失或非法时保守不注入。"""
        gate = _make_gate()
        with patch(
            "voliti.middleware.skills_gate.get_current_session_type",
            side_effect=InvalidSessionTypeError("config missing"),
        ):
            assert gate.should_inject() is False
