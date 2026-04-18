# ABOUTME: Future Self Dialogue 干预手段专用 A2UI 工具
# ABOUTME: 硬编码 surface / intervention_kind / layout，Coach 仅传组件列表

from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from voliti.a2ui import A2UIPayload
from voliti.tools.fan_out import _fan_out_core

KIND = "future-self-dialogue"
"""intervention_kind 分派键；供测试与外部消费者按名称定位工具。"""

_LAYOUT = "full"
_METADATA: dict[str, str] = {
    "surface": "intervention",
    "intervention_kind": KIND,
}


@tool
def fan_out_future_self_dialogue(components: list[dict[str, Any]]) -> str:
    """Present the Future Self Dialogue intervention panel.

    Invoke this tool when the future-self-dialogue skill triggers — typically when
    motivation is foggy, at a Chapter transition, during long-horizon review, or when
    stated identity and observed behavior diverge. See
    `/skills/coach/future-self-dialogue/SKILL.md` for the full trigger criteria and
    guardrails.

    Metadata (`surface="intervention"`, `intervention_kind="future-self-dialogue"`) and
    `layout="full"` are injected automatically by this tool — do not pass them.

    Expected components (per SKILL.md § A2UI Composition):
    1. `TextComponent` — a memory quote the user has said, referenced from their
       Chapter identity or profile.
    2. `ProtocolPromptComponent` — `observation` mirrors the future self the user
       has already named; `question` is what the future self asks the present self.
    3. `TextInputComponent` — the user's narrative reply. No slider, no select —
       future-self work is narrative, not measured.

    Args:
        components: List of component dicts following the order above.

    Returns:
        Summary of the user's response for Coach to consume.
    """
    try:
        payload = A2UIPayload(
            components=components,
            layout=_LAYOUT,
            metadata=dict(_METADATA),
        )
    except ValidationError as exc:
        return (
            f"Invalid {KIND} components: {exc.error_count()} validation errors. "
            "Describe the future self verbally instead."
        )

    return _fan_out_core(payload)


TOOL = fan_out_future_self_dialogue
"""agent.py 动态加载入口。"""
