# ABOUTME: A2UI 组件类型目录与交互 Payload 定义
# ABOUTME: 定义 Coach 可组合的 8 种 UI 原语及前后端共享的交互协议

from typing import Annotated, Any, Literal, Union

from langgraph.config import get_config
from langgraph.types import Interrupt
from pydantic import BaseModel, Field


class SelectOption(BaseModel):
    """选项定义，用于 select 和 multi_select 组件。"""

    label: str
    value: str


# --- Display Components (no output) ---


class TextComponent(BaseModel):
    """文本展示。"""

    kind: Literal["text"] = "text"
    text: str


class ImageComponent(BaseModel):
    """图片展示。"""

    kind: Literal["image"] = "image"
    src: str
    """Base64 data URL 或图片路径。"""
    alt: str = ""


class ProtocolPromptComponent(BaseModel):
    """微干预卡片。Coach 检测到高压力或疲劳信号时触发。"""

    kind: Literal["protocol_prompt"] = "protocol_prompt"
    observation: str
    """Coach 的观察链，说明触发原因（如"压力分数连续两天 > 7"）。"""
    question: str
    """引导用户自我审视的核心问题，将被引号包裹呈现。"""


# --- Input Components (produce output keyed by name) ---


class SliderComponent(BaseModel):
    """有界整数滑块，适用于 1-10 量表。"""

    kind: Literal["slider"] = "slider"
    key: str
    label: str
    min: int = 1
    max: int = 10
    step: int = 1
    value: int | None = None
    """预填充值。None 表示待用户填写。"""


class TextInputComponent(BaseModel):
    """自由文本输入。"""

    kind: Literal["text_input"] = "text_input"
    key: str
    label: str
    placeholder: str = ""
    value: str = ""


class NumberInputComponent(BaseModel):
    """数值输入。"""

    kind: Literal["number_input"] = "number_input"
    key: str
    label: str
    unit: str = ""
    value: float | None = None


class SelectComponent(BaseModel):
    """单选。"""

    kind: Literal["select"] = "select"
    key: str
    label: str
    options: list[SelectOption]
    value: str = ""


class MultiSelectComponent(BaseModel):
    """多选。"""

    kind: Literal["multi_select"] = "multi_select"
    key: str
    label: str
    options: list[SelectOption]
    value: list[str] = []


# --- Union & Payload ---

Component = Annotated[
    Union[
        TextComponent,
        ImageComponent,
        ProtocolPromptComponent,
        SliderComponent,
        TextInputComponent,
        NumberInputComponent,
        SelectComponent,
        MultiSelectComponent,
    ],
    Field(discriminator="kind"),
]
"""所有 A2UI 组件的联合类型，通过 kind 字段自动解析。"""


class A2UIPayload(BaseModel):
    """interrupt() 发送给前端的 Payload。"""

    type: Literal["a2ui"] = "a2ui"
    components: list[Component]
    layout: Literal["half", "three-quarter", "full"] = "three-quarter"
    metadata: dict[str, str] = {}
    """透传给前端的引用信息（如 card_id），不参与组件渲染。"""


class A2UIResponse(BaseModel):
    """前端 resume 回传的用户响应。"""

    action: Literal["submit", "reject", "skip"]
    interrupt_id: str | None = None
    data: dict[str, object] = {}
    """Input component 的 key → value 映射。"""


def current_interrupt_id() -> str | None:
    """返回当前 graph interrupt 的权威标识。"""
    try:
        configurable = get_config().get("configurable", {})
    except Exception:
        return None

    checkpoint_ns = configurable.get("checkpoint_ns")
    if not isinstance(checkpoint_ns, str) or not checkpoint_ns:
        return None
    return Interrupt.from_ns(value=None, ns=checkpoint_ns).id


def validate_a2ui_response(
    payload: A2UIPayload,
    response: A2UIResponse,
    *,
    expected_interrupt_id: str | None,
) -> None:
    """验证 A2UI resume 是否仍匹配当前 interrupt 与 payload。"""
    if expected_interrupt_id is not None:
        if not response.interrupt_id:
            raise ValueError("A2UI response missing interrupt_id")
        if response.interrupt_id != expected_interrupt_id:
            raise ValueError("A2UI response interrupt_id does not match active interrupt")

    if response.action != "submit":
        if response.data:
            raise ValueError("A2UI non-submit actions must not include data")
        return

    allowed_inputs: dict[str, Component] = {}
    for component in payload.components:
        key = getattr(component, "key", None)
        if isinstance(key, str):
            allowed_inputs[key] = component

    unknown_keys = sorted(set(response.data) - set(allowed_inputs))
    if unknown_keys:
        raise ValueError(f"A2UI response contains unexpected keys: {', '.join(unknown_keys)}")

    for key, value in response.data.items():
        _validate_component_value(key, allowed_inputs[key], value)


def _validate_component_value(key: str, component: Component, value: object) -> None:
    if isinstance(component, SliderComponent):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"A2UI response key '{key}' must be an integer")
        if value < component.min or value > component.max:
            raise ValueError(f"A2UI response key '{key}' is out of range")
        if (value - component.min) % component.step != 0:
            raise ValueError(f"A2UI response key '{key}' does not match slider step")
        return

    if isinstance(component, TextInputComponent):
        if not isinstance(value, str):
            raise ValueError(f"A2UI response key '{key}' must be a string")
        return

    if isinstance(component, NumberInputComponent):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"A2UI response key '{key}' must be numeric")
        return

    if isinstance(component, SelectComponent):
        if not isinstance(value, str):
            raise ValueError(f"A2UI response key '{key}' must be a string option")
        allowed = {option.value for option in component.options}
        if value not in allowed:
            raise ValueError(f"A2UI response key '{key}' contains an invalid option")
        return

    if isinstance(component, MultiSelectComponent):
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"A2UI response key '{key}' must be a list of string options")
        allowed = {option.value for option in component.options}
        if any(item not in allowed for item in value):
            raise ValueError(f"A2UI response key '{key}' contains an invalid option")
        if len(set(value)) != len(value):
            raise ValueError(f"A2UI response key '{key}' contains duplicate options")
        return

    raise ValueError(f"A2UI response key '{key}' does not map to a supported input component")
