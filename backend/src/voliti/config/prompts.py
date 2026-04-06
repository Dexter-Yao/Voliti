# ABOUTME: 全局提示词管理中心
# ABOUTME: 基于 Jinja2 模板引擎，支持注释、变量注入与严格校验

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Undefined


class PromptRegistry:
    """全局提示词管理中心，基于 Jinja2 模板引擎。

    模板文件使用 .j2 扩展名。Jinja2 注释（{# ... #}）不会出现在渲染结果中。
    使用 Undefined 允许模板中未传递的变量被 `is defined` 测试检查。
    """

    _env: Environment | None = None

    @classmethod
    def load(cls, prompts_dir: Path) -> None:
        """从指定目录加载 Jinja2 模板环境。"""
        cls._env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            undefined=Undefined,
            keep_trailing_newline=True,
        )

    @classmethod
    def get(cls, name: str, **kwargs: object) -> str:
        """获取并渲染指定名称的提示词模板。

        Args:
            name: 模板名称（不含 .j2 扩展名）。
            **kwargs: 传递给模板的变量。
        """
        if cls._env is None:
            msg = "PromptRegistry 未初始化，请先调用 load()"
            raise RuntimeError(msg)
        template = cls._env.get_template(f"{name}.j2")
        return template.render(**kwargs)

    @classmethod
    def reset(cls) -> None:
        """重置状态，供测试使用。"""
        cls._env = None
