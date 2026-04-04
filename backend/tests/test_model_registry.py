# ABOUTME: ModelRegistry 单元测试
# ABOUTME: 验证 LLM 配置中心的加载、获取与缓存行为

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from voliti.config.models import ModelRegistry


class TestModelRegistry:
    """ModelRegistry 全局 LLM 配置中心测试。"""

    def setup_method(self) -> None:
        """每个测试前重置 registry 状态。"""
        ModelRegistry.reset()

    def test_configure_loads_profiles(self) -> None:
        """configure 应加载 profile 配置。"""
        profiles = {
            "coach": {"model": "openai:gpt-4o"},
        }
        ModelRegistry.configure(profiles)
        assert ModelRegistry._profiles == profiles

    def test_configure_clears_cached_instances(self) -> None:
        """重新 configure 应清除已缓存的模型实例。"""
        ModelRegistry._instances["old"] = MagicMock()
        ModelRegistry.configure({"coach": {"model": "openai:gpt-4o"}})
        assert ModelRegistry._instances == {}

    @patch("voliti.config.models.init_chat_model")
    def test_get_creates_model_instance(self, mock_init: MagicMock) -> None:
        """get 应使用 profile 配置创建模型实例。"""
        mock_model = MagicMock()
        mock_init.return_value = mock_model

        ModelRegistry.configure({"coach": {"model": "openai:gpt-4o"}})
        result = ModelRegistry.get("coach")

        mock_init.assert_called_once_with(model="openai:gpt-4o")
        assert result is mock_model

    @patch("voliti.config.models.init_chat_model")
    def test_get_caches_instance(self, mock_init: MagicMock) -> None:
        """多次 get 同一 profile 应返回缓存实例，不重复创建。"""
        mock_init.return_value = MagicMock()

        ModelRegistry.configure({"coach": {"model": "openai:gpt-4o"}})
        first = ModelRegistry.get("coach")
        second = ModelRegistry.get("coach")

        assert first is second
        mock_init.assert_called_once()

    def test_get_unknown_profile_raises(self) -> None:
        """获取未配置的 profile 应抛出 KeyError。"""
        ModelRegistry.configure({})
        with pytest.raises(KeyError):
            ModelRegistry.get("nonexistent")

    @patch("voliti.config.models.init_chat_model")
    def test_get_passes_extra_kwargs(self, mock_init: MagicMock) -> None:
        """profile 中的额外参数应传递给 init_chat_model。"""
        mock_init.return_value = MagicMock()

        ModelRegistry.configure({
            "coach": {
                "model": "azure_openai:gpt-5.4",
                "api_key": "test-key",
            },
        })
        ModelRegistry.get("coach")

        mock_init.assert_called_once_with(
            model="azure_openai:gpt-5.4",
            api_key="test-key",
        )

    def test_load_from_toml_resolves_env_vars(self, tmp_path: Path) -> None:
        """load_from_toml 应解析配置中的环境变量占位符。"""
        toml_content = """
[models.test]
model = "azure_openai:gpt-5.4"
api_key = "${TEST_API_KEY}"
"""
        toml_file = tmp_path / "models.toml"
        toml_file.write_text(toml_content)

        with patch.dict("os.environ", {"TEST_API_KEY": "secret-key-123"}):
            ModelRegistry.load_from_toml(toml_file)

        assert ModelRegistry._profiles["test"]["api_key"] == "secret-key-123"
        assert ModelRegistry._profiles["test"]["model"] == "azure_openai:gpt-5.4"

    def test_load_from_toml_raises_on_missing_env_var(self, tmp_path: Path) -> None:
        """load_from_toml 遇到未设置的环境变量应抛出 ValueError。"""
        toml_content = """
[models.test]
model = "azure_openai:gpt-5.4"
api_key = "${UNDEFINED_VAR}"
"""
        toml_file = tmp_path / "models.toml"
        toml_file.write_text(toml_content)

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="UNDEFINED_VAR"):
                ModelRegistry.load_from_toml(toml_file)


