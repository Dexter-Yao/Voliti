# ABOUTME: 全局初始化函数
# ABOUTME: 加载 ModelRegistry 与 PromptRegistry，作为所有入口的单一初始化来源

from pathlib import Path

from voliti.config.models import ModelRegistry
from voliti.config.prompts import PromptRegistry


def init(project_root: Path) -> None:
    """初始化全局配置。

    Args:
        project_root: 项目根目录，包含 config/ 和 prompts/ 子目录。
    """
    ModelRegistry.load_from_toml(project_root / "config" / "models.toml")
    PromptRegistry.load(project_root / "prompts")
