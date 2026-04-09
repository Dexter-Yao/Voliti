# ABOUTME: A2UI 通用交互工具
# ABOUTME: 通过组合 8 种 UI 原语构建动态界面，经 interrupt() 采集用户响应

from typing import Any, Literal

from langchain_core.tools import tool
from langgraph.types import interrupt

from pydantic import ValidationError

from voliti.a2ui import A2UIPayload, A2UIResponse


@tool
def fan_out(
    components: list[dict[str, Any]],
    layout: Literal["half", "three-quarter", "full"] = "three-quarter",
) -> str:
    """Present an interactive UI to the user and collect their response.

    Compose dynamic interfaces from 8 UI primitives: text, image, protocol_prompt,
    slider, text_input, number_input, select, multi_select.

    Args:
        components: List of component dicts, each with a "kind" field.
        layout: Display layout — "half", "three-quarter" (default, 75%), or "full".
    """
    try:
        payload = A2UIPayload(components=components, layout=layout)
    except ValidationError as exc:
        return f"Invalid UI components: {exc.error_count()} validation errors. Describe the information verbally instead."

    raw_response = interrupt(payload.model_dump())

    try:
        response = A2UIResponse.model_validate(raw_response)
    except ValidationError:
        return "User response could not be parsed. Ask the user to repeat their answer verbally."

    if response.action == "reject":
        return "User closed the panel without responding."
    if response.action == "skip":
        return "User acknowledged but chose to skip."

    if not response.data:
        return "User responded: (acknowledged the observation)"
    data_summary = ", ".join(f"{k}={v}" for k, v in response.data.items())
    return f"User responded: {data_summary}"
