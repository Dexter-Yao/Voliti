# ABOUTME: 全局 LLM 配置中心
# ABOUTME: 统一管理所有模型 profile，支持 TOML 配置文件加载与环境变量插值

from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


class ModelRegistry:
    """全局 LLM 配置中心，单一事实来源。"""

    _profiles: dict[str, dict[str, Any]] = {}
    _instances: dict[str, BaseChatModel] = {}

    @classmethod
    def configure(cls, profiles: dict[str, dict[str, Any]]) -> None:
        """加载模型 profile 配置，清除已缓存实例。"""
        cls._profiles = profiles
        cls._instances.clear()

    @classmethod
    def load_from_toml(cls, path: Path) -> None:
        """从 TOML 文件加载配置，支持环境变量插值。

        TOML 文件格式：
            [models.coach]
            model = "azure_openai:gpt-5.2"
            azure_endpoint = "${AZURE_OPENAI_GPT52_ENDPOINT}"

        Args:
            path: TOML 配置文件路径
        """
        with open(path, "rb") as f:
            raw = tomllib.load(f)

        profiles: dict[str, dict[str, Any]] = {}
        for name, config in raw.get("models", {}).items():
            profiles[name] = cls._resolve_env_vars(config)

        cls.configure(profiles)

    @classmethod
    def _resolve_env_vars(cls, config: dict[str, Any]) -> dict[str, Any]:
        """递归解析配置中的环境变量占位符 ${VAR_NAME}。"""
        pattern = re.compile(r"\$\{([^}]+)\}")
        resolved: dict[str, Any] = {}

        for key, value in config.items():
            if isinstance(value, str):
                def replacer(match: re.Match[str]) -> str:
                    var_name = match.group(1)
                    env_value = os.environ.get(var_name)
                    if env_value is None:
                        raise ValueError(
                            f"环境变量 {var_name} 未设置，配置项 '{key}' 需要此变量"
                        )
                    return env_value

                resolved[key] = pattern.sub(replacer, value)
            elif isinstance(value, dict):
                resolved[key] = cls._resolve_env_vars(value)
            else:
                resolved[key] = value

        return resolved

    @classmethod
    def reset(cls) -> None:
        """重置状态，供测试使用。"""
        cls._profiles.clear()
        cls._instances.clear()

    @classmethod
    def get(cls, profile: str) -> BaseChatModel:
        """获取指定 profile 的模型实例，自动缓存。"""
        if profile not in cls._instances:
            config = cls._profiles[profile].copy()
            cls._instances[profile] = init_chat_model(**config)

        return cls._instances[profile]
