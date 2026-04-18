# ABOUTME: Cognitive Reframing 干预手段专用 A2UI 工具
# ABOUTME: 硬编码 surface / intervention_kind / layout，Coach 仅传组件列表

from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from voliti.a2ui import A2UIPayload
from voliti.tools.fan_out import _fan_out_core

KIND = "cognitive-reframing"
"""intervention_kind 分派键；供测试与外部消费者按名称定位工具。"""

_LAYOUT = "full"
_METADATA: dict[str, str] = {
    "surface": "intervention",
    "intervention_kind": KIND,
}


@tool
def fan_out_cognitive_reframing(components: list[dict[str, Any]]) -> str:
    """Present the Cognitive Reframing intervention panel.

    Invoke this tool when the user is catastrophizing, using black-and-white thinking
    after a lapse, or when a single failure dominates a Chapter review. Do not use
    during active dysregulation — State Before Strategy supersedes. See
    `/skills/coach/cognitive-reframing/SKILL.md` for the full trigger criteria and
    guardrails.

    Metadata (`surface="intervention"`, `intervention_kind="cognitive-reframing"`)
    and `layout="full"` are injected automatically — do not pass them.

    Expected components (per SKILL.md § A2UI Composition):
    1. `ProtocolPromptComponent` — `observation` quotes the user's catastrophizing
       sentence verbatim; `question` surfaces the inferential leap ("this = that?").
    2. `TextComponent` — a brief reading of the implicit verdict inside the original
       sentence ("what this sentence is really saying"). The frontend renders it in
       the right-hand pane of the upper row; if omitted it falls back to a greyed
       placeholder.
    3. Zero or more of: `SelectComponent` (2–3 alternative readings as options),
       `TextInputComponent` (the user writes their own new frame).

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
            "Offer an alternative reading verbally instead."
        )

    return _fan_out_core(payload)


TOOL = fan_out_cognitive_reframing
"""agent.py 动态加载入口。"""
