# ABOUTME: PromptRegistry 单元测试
# ABOUTME: 验证 Jinja2 模板加载、渲染、变量注入与错误处理

from pathlib import Path

import pytest

from voliti.config.prompts import PromptRegistry


class TestPromptRegistry:
    """PromptRegistry Jinja2 提示词管理中心测试。"""

    def setup_method(self) -> None:
        """每个测试前重置 registry 状态。"""
        PromptRegistry.reset()

    def test_load_creates_environment(self, tmp_path: Path) -> None:
        """load 应创建 Jinja2 Environment。"""
        (tmp_path / "coach_system.j2").write_text("你是教练。")
        PromptRegistry.load(tmp_path)
        assert PromptRegistry._env is not None

    def test_get_returns_template_content(self, tmp_path: Path) -> None:
        """get 应返回模板渲染结果。"""
        content = "你是 Voliti 的教练。\n\n核心原则：冷静、精准。"
        (tmp_path / "coach_system.j2").write_text(content)
        PromptRegistry.load(tmp_path)
        result = PromptRegistry.get("coach_system")
        assert result == content

    def test_get_strips_jinja2_comments(self, tmp_path: Path) -> None:
        """Jinja2 注释不应出现在渲染结果中。"""
        (tmp_path / "test.j2").write_text(
            "{# 这是注释，不应发送给 LLM #}\n你是教练。"
        )
        PromptRegistry.load(tmp_path)
        result = PromptRegistry.get("test")
        assert "注释" not in result
        assert "你是教练。" in result

    def test_get_renders_variables(self, tmp_path: Path) -> None:
        """get 应渲染 Jinja2 变量。"""
        (tmp_path / "test.j2").write_text("路径: {{ ledger_base }}")
        PromptRegistry.load(tmp_path)
        result = PromptRegistry.get("test", ledger_base="/user/ledger")
        assert result == "路径: /user/ledger"

    def test_get_undefined_variable_raises(self, tmp_path: Path) -> None:
        """模板中使用未提供的变量应抛出异常（StrictUndefined）。"""
        from jinja2 import UndefinedError

        (tmp_path / "test.j2").write_text("路径: {{ missing_var }}")
        PromptRegistry.load(tmp_path)
        with pytest.raises(UndefinedError):
            PromptRegistry.get("test")

    def test_get_unknown_template_raises(self, tmp_path: Path) -> None:
        """获取未加载的模板应抛出异常。"""
        from jinja2 import TemplateNotFound

        PromptRegistry.load(tmp_path)
        with pytest.raises(TemplateNotFound):
            PromptRegistry.get("nonexistent")

    def test_load_empty_directory(self, tmp_path: Path) -> None:
        """加载空目录应正常执行。"""
        PromptRegistry.load(tmp_path)
        assert PromptRegistry._env is not None

    def test_coach_system_includes_day_summary_recall_guidance(self) -> None:
        """coach_system 应包含日摘要回顾指引。"""
        prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
        PromptRegistry.load(prompts_dir)

        result = PromptRegistry.get("coach_system")

        assert "day_summary" in result
        assert "read_file" in result

    def test_onboarding_prompt_defines_fan_out_input_schema(self) -> None:
        """onboarding prompt 应明确 fan_out 输入组件的必填字段。"""
        prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
        PromptRegistry.load(prompts_dir)

        result = PromptRegistry.get("onboarding")

        assert '"kind": "select"' in result
        assert '"key": "depth_choice"' in result
        assert '"kind": "multi_select"' in result
        assert '"key": "danger_scenarios"' in result

    def test_onboarding_prompt_does_not_reference_removed_suggested_replies(self) -> None:
        """onboarding prompt 不应继续要求已删除的 suggested replies 功能。"""
        prompts_dir = Path(__file__).resolve().parents[1] / "prompts"
        PromptRegistry.load(prompts_dir)

        result = PromptRegistry.get("onboarding")

        assert "suggested replies" not in result.lower()
