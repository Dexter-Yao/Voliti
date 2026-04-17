# ABOUTME: Coach Agent 工厂函数测试
# ABOUTME: 验证 agent 创建配置的正确性

from unittest.mock import MagicMock, patch

from langgraph.store.memory import InMemoryStore

from voliti.agent import create_coach_agent
from voliti.backends.readonly_filesystem import ReadOnlyFilesystemBackend
from voliti.middleware.briefing import BriefingMiddleware
from voliti.middleware.session_type import SessionTypeMiddleware
from voliti.middleware.skills_gate import SkillsGateMiddleware
from voliti.session_type import get_session_profile
from voliti.store_contract import COACH_SKILLS_BACKEND_PREFIX


class TestCreateCoachAgent:
    """Coach Agent 工厂函数测试。"""

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_passes_model_from_registry(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应使用 ModelRegistry 获取 coach 模型。"""
        mock_model = MagicMock()
        mock_model_reg.get.return_value = mock_model
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        mock_model_reg.get.assert_any_call("coach")
        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["model"] == mock_model

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_passes_prompt_from_registry(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应使用 PromptRegistry 获取 coach 系统提示词。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        mock_prompt_reg.get.assert_any_call("coach_system")
        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["system_prompt"] == "You are a coach."

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_passes_store(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应传入 store 实例。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        store = InMemoryStore()
        create_coach_agent(store=store)

        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["store"] is store

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_backend_is_callable_factory(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """backend 应为可调用的工厂函数（接受 ToolRuntime）。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        backend_factory = call_kwargs.kwargs["backend"]
        assert callable(backend_factory)

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_backend_factory_creates_composite(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """backend 工厂函数应创建 CompositeBackend。"""
        from deepagents.backends import CompositeBackend

        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        backend_factory = call_kwargs.kwargs["backend"]

        mock_runtime = MagicMock()
        backend = backend_factory(mock_runtime)
        assert isinstance(backend, CompositeBackend)

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_tools_include_fan_out(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """tools 应包含 fan_out。"""
        from voliti.tools.fan_out import fan_out

        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        tools = call_kwargs.kwargs["tools"]
        assert fan_out in tools

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_no_interrupt_on(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """不应使用 interrupt_on（fan_out 内部调用 interrupt）。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        assert "interrupt_on" not in call_kwargs.kwargs

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_sets_agent_name(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应设置 agent 名称为 coach。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["name"] == "coach"

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_enables_memory_middleware(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应启用 MemoryMiddleware，加载 Coach 持久记忆和用户档案。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs["memory"] == list(
            get_session_profile("coaching").memory_paths
        )

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_registers_session_type_middleware(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应注册 SessionTypeMiddleware。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        assert any(isinstance(item, SessionTypeMiddleware) for item in call_kwargs.kwargs["middleware"])

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_registers_briefing_middleware(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应注册 BriefingMiddleware。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        assert any(isinstance(item, BriefingMiddleware) for item in call_kwargs.kwargs["middleware"])

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_registers_skills_gate_middleware(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应注册 SkillsGateMiddleware（仅 coaching session 注入 skill 元数据）。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        call_kwargs = mock_create.call_args
        assert any(
            isinstance(item, SkillsGateMiddleware)
            for item in call_kwargs.kwargs["middleware"]
        )

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_skills_gate_is_after_session_type_and_before_briefing(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """SkillsGateMiddleware 位于 SessionTypeMiddleware 之后、BriefingMiddleware 之前。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        middleware = mock_create.call_args.kwargs["middleware"]
        types_in_order = [type(m).__name__ for m in middleware]
        session_idx = types_in_order.index("SessionTypeMiddleware")
        skills_idx = types_in_order.index("SkillsGateMiddleware")
        briefing_idx = types_in_order.index("BriefingMiddleware")
        assert session_idx < skills_idx < briefing_idx

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_skills_coach_route_uses_readonly_filesystem(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """CompositeBackend 的 /skills/coach/ 路由应是 ReadOnlyFilesystemBackend。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        backend_factory = mock_create.call_args.kwargs["backend"]
        composite = backend_factory(MagicMock())
        assert COACH_SKILLS_BACKEND_PREFIX in composite.routes
        assert isinstance(
            composite.routes[COACH_SKILLS_BACKEND_PREFIX], ReadOnlyFilesystemBackend
        )

    @patch("voliti.agent.create_deep_agent")
    @patch("voliti.agent.PromptRegistry")
    @patch("voliti.agent.ModelRegistry")
    def test_uses_prompt_name_from_coaching_profile(
        self,
        mock_model_reg: MagicMock,
        mock_prompt_reg: MagicMock,
        mock_create: MagicMock,
    ) -> None:
        """应从 coaching profile 读取系统提示词名称。"""
        mock_model_reg.get.return_value = MagicMock()
        mock_prompt_reg.get.return_value = "You are a coach."
        mock_create.return_value = MagicMock()

        create_coach_agent()

        coaching_profile = get_session_profile("coaching")
        mock_prompt_reg.get.assert_any_call(coaching_profile.system_prompt_name)


class TestSessionProfile:
    """SessionProfile 配置测试。"""

    def test_coaching_and_onboarding_profiles_exist(self) -> None:
        """coaching 和 onboarding profile 均可正常获取。"""
        assert get_session_profile("coaching").session_type == "coaching"
        assert get_session_profile("onboarding").session_type == "onboarding"
