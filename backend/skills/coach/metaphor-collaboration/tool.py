# ABOUTME: Metaphor Collaboration 干预手段专用 A2UI 工具
# ABOUTME: 硬编码 surface / intervention_kind / layout，Coach 仅传组件列表

from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from voliti.a2ui import A2UIPayload
from voliti.tools.fan_out import _fan_out_core

KIND = "metaphor-collaboration"
"""intervention_kind 分派键；供测试与外部消费者按名称定位工具。"""

_LAYOUT = "full"
_METADATA: dict[str, str] = {
    "surface": "intervention",
    "intervention_kind": KIND,
}


@tool
def fan_out_metaphor_collaboration(components: list[dict[str, Any]]) -> str:
    """Present the Metaphor Collaboration intervention panel.

    Invoke this tool only when the user has already introduced a metaphor
    spontaneously, or when state check-in produces figurative rather than literal
    language. Never use this tool to introduce a Coach-generated metaphor. See
    `/skills/coach/metaphor-collaboration/SKILL.md` for the full trigger criteria and
    guardrails.

    Metadata (`surface="intervention"`, `intervention_kind="metaphor-collaboration"`)
    and `layout="full"` are injected automatically — do not pass them.

    Expected components (per SKILL.md § A2UI Composition):
    1. `ProtocolPromptComponent` — `observation` must mirror the user's metaphor
       verbatim (no paraphrase); `question` is a Clean-Language-style question
       staying inside the metaphor's own logic.
    2. `TextInputComponent` — the user's elaboration. Do not attach structured
       inputs (slider, select) — structure kills the metaphor.

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
            "Mirror the metaphor verbally instead."
        )

    return _fan_out_core(payload)


TOOL = fan_out_metaphor_collaboration
"""agent.py 动态加载入口。"""
