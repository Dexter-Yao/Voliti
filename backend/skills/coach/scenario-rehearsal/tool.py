# ABOUTME: Scenario Rehearsal 干预手段专用 A2UI 工具
# ABOUTME: 硬编码 surface / intervention_kind / layout，Coach 仅传组件列表

from typing import Any

from langchain_core.tools import tool
from pydantic import ValidationError

from voliti.a2ui import A2UIPayload
from voliti.tools.fan_out import _fan_out_core

KIND = "scenario-rehearsal"
"""intervention_kind 分派键；供测试与外部消费者按名称定位工具。"""

_LAYOUT = "full"
_METADATA: dict[str, str] = {
    "surface": "intervention",
    "intervention_kind": KIND,
}


@tool
def fan_out_scenario_rehearsal(components: list[dict[str, Any]]) -> str:
    """Present the Scenario Rehearsal intervention panel.

    Invoke this tool when the scenario-rehearsal skill triggers — typically when the
    user names a concrete upcoming event (business trip, dinner, holiday, medical
    visit, family gathering) within 2–14 days, when a Forward Marker matches a known
    trigger pattern, or when the user is forming / revising a LifeSign. See
    `/skills/coach/scenario-rehearsal/SKILL.md` for the full trigger criteria and
    guardrails.

    Metadata (`surface="intervention"`, `intervention_kind="scenario-rehearsal"`) and
    `layout="full"` are injected automatically — do not pass them.

    Expected components (per SKILL.md § A2UI Composition):
    1. `TextComponent` — a scene anchor naming the scenario with one concrete cue
       (time, place, or social context). Must be the first component so the frontend
       pins it to the top.
    2. `ProtocolPromptComponent` — `observation` references the trigger the user has
       already flagged; `question` invites rehearsal with the user's consent.
    3. Zero or more of: `TextInputComponent` (obstacle / if-then response),
       `SelectComponent` (candidate responses when the user hesitates).

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
            "Describe the scenario verbally instead."
        )

    return _fan_out_core(payload)


TOOL = fan_out_scenario_rehearsal
"""agent.py 动态加载入口。"""
