# ABOUTME: A2UI 通用交互工具 + intervention 专用工具共享的核心 interrupt/响应处理
# ABOUTME: 通过组合 8 种 UI 原语构建动态界面，经 interrupt() 采集用户响应

from typing import Any, Literal

from langchain_core.tools import tool
from langgraph.types import interrupt

from pydantic import ValidationError

from voliti.a2ui import (
    A2UIPayload,
    A2UIResponse,
    current_interrupt_id,
    validate_a2ui_response,
)


def _fan_out_core(payload: A2UIPayload) -> str:
    """将 A2UI payload 呈送给用户并收集响应。

    该函数封装了 fan_out / fan_out_<intervention_kind> 共享的 interrupt + 响应验证 +
    结果摘要逻辑。工具层职责：构造 payload（含 metadata 与 layout），调用此函数即可。

    Args:
        payload: 已校验的 A2UI payload（构造层负责 ValidationError）。

    Returns:
        供 Coach 消费的响应摘要字符串。
    """
    raw_response = interrupt(payload.model_dump())

    try:
        response = A2UIResponse.model_validate(raw_response)
    except ValidationError:
        return "User response could not be parsed. Ask the user to repeat their answer verbally."
    try:
        validate_a2ui_response(
            payload,
            response,
            expected_interrupt_id=current_interrupt_id(),
        )
    except ValueError:
        return "User response no longer matches the active panel. Ask the user to try again."

    if response.action == "reject":
        if response.reason:
            return f"User rejected: {response.reason}"
        return "User closed the panel without responding."
    if response.action == "skip":
        return "User acknowledged but chose to skip."

    if not response.data:
        return "User responded: (acknowledged the observation)"
    data_summary = ", ".join(f"{k}={v}" for k, v in response.data.items())
    return f"User responded: {data_summary}"


@tool
def fan_out(
    components: list[dict[str, Any]],
    layout: Literal["half", "three-quarter", "full"] = "three-quarter",
) -> str:
    """Present an interactive UI to the user and collect their response.

    Compose dynamic interfaces from 8 UI primitives: text, image, protocol_prompt,
    slider, text_input, number_input, select, multi_select.

    Use this tool for general A2UI interactions (daily check-ins, reviews, ad-hoc
    structured dialogue). For the four experiential intervention skills, prefer the
    dedicated tools `fan_out_future_self_dialogue` / `fan_out_scenario_rehearsal` /
    `fan_out_metaphor_collaboration` / `fan_out_cognitive_reframing`; they are loaded
    automatically when a matching skill is active and carry the correct metadata.

    Args:
        components: List of component dicts, each with a "kind" field.
        layout: Display layout — "half", "three-quarter" (default, 75%), or "full".
    """
    try:
        payload = A2UIPayload(components=components, layout=layout)
    except ValidationError as exc:
        return f"Invalid UI components: {exc.error_count()} validation errors. Describe the information verbally instead."

    return _fan_out_core(payload)
