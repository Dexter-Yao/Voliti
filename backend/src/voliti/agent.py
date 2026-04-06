# ABOUTME: Coach Agent 工厂函数
# ABOUTME: 组装 DeepAgent 配置，创建 Coach Agent 实例（含 A2UI fan_out 工具与 Intervention Composer Subagent）

from collections.abc import Callable
from typing import Any

from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.middleware.subagents import SubAgent

from voliti.config.models import ModelRegistry
from voliti.config.prompts import PromptRegistry
from voliti.middleware.session_mode import SessionModeMiddleware
from voliti.tools.experiential import compose_experiential_intervention
from voliti.tools.fan_out import fan_out

COACH_TOOLS = [fan_out]
"""Coach 直接调用的工具，通过 A2UI 组件组合实现动态交互。"""

_DEFAULT_USER_NAMESPACE = ("voliti", "user")


def _resolve_user_namespace(ctx: Any) -> tuple[str, ...]:
    """从运行时 config 解析用户 namespace。

    支持通过 configurable.user_id 传入自定义用户标识，
    实现多用户或评估场景下的 Store 隔离。
    默认回退到 ("voliti", "user")。

    解析优先级：
    1. ctx.runtime.config（DeepAgent 运行时注入）
    2. langgraph.config.get_config()（LangGraph 上下文）
    3. 默认 ("voliti", "user")
    """
    # 优先从 runtime config 读取（与 StoreBackend legacy 一致）
    runtime_cfg = getattr(getattr(ctx, "runtime", None), "config", None)
    if isinstance(runtime_cfg, dict):
        user_id = runtime_cfg.get("configurable", {}).get("user_id")
        if user_id:
            return ("voliti", str(user_id))

    # Fallback 到 LangGraph context
    try:
        from langgraph.config import get_config

        cfg = get_config()
        user_id = cfg.get("configurable", {}).get("user_id")
        if user_id:
            return ("voliti", str(user_id))
    except Exception:  # noqa: BLE001
        pass

    return _DEFAULT_USER_NAMESPACE


def _create_backend_factory() -> Callable[..., Any]:
    """创建 CompositeBackend 工厂函数。

    路由规则：
    - /user/ → StoreBackend（持久存储）
    - 其他 → StateBackend（临时存储）
    """

    def factory(rt: Any) -> CompositeBackend:
        return CompositeBackend(
            default=StateBackend(rt),
            routes={
                "/user/": StoreBackend(
                    rt,
                    namespace=_resolve_user_namespace,
                ),
            },
        )

    return factory


def _create_intervention_composer() -> SubAgent:
    """创建 Intervention Composer Subagent 配置。"""
    return SubAgent(
        name="intervention_composer",
        description=(
            "根据教练干预意图和用户行为上下文，构建并呈现体验式干预。"
            "基于行为科学理论（Future Self-Continuity、MCII/WOOP、概念隐喻、CBT），"
            "将教练洞察转化为可感知的体验，辅助用户理解行为模式、感受未来自我、预演应对场景。"
        ),
        system_prompt=PromptRegistry.get("intervention_composer_system"),
        tools=[compose_experiential_intervention],
        model=ModelRegistry.get("intervention_composer"),
    )


def create_coach_agent(
    *,
    store: BaseStore | None = None,
) -> CompiledStateGraph:
    """创建 Coach Agent。

    Args:
        store: 持久化存储后端。默认为 None，由 LangGraph API 自动注入。
    """
    kwargs = {
        "model": ModelRegistry.get("coach"),
        "system_prompt": PromptRegistry.get("coach_system"),
        "backend": _create_backend_factory(),
        "name": "coach",
        "memory": ["/user/coach/AGENTS.md", "/user/profile/context.md", "/user/coping_plans_index.md"],
        "tools": COACH_TOOLS,
        "subagents": [_create_intervention_composer()],
        "middleware": [SessionModeMiddleware()],
    }
    if store is not None:
        kwargs["store"] = store

    return create_deep_agent(**kwargs)

