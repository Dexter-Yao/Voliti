# ABOUTME: A2UI 组件类型目录与交互 Payload 定义
# ABOUTME: 定义 Coach 可组合的 8 种 UI 原语及前后端共享的交互协议

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class SelectOption(BaseModel):
    """选项定义，用于 select 和 multi_select 组件。"""

    label: str
    value: str


# --- Display Components (no output) ---


class TextComponent(BaseModel):
    """文本展示。"""

    kind: Literal["text"] = "text"
    content: str


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
    name: str
    label: str
    min: int = 1
    max: int = 10
    step: int = 1
    value: int | None = None
    """预填充值。None 表示待用户填写。"""


class TextInputComponent(BaseModel):
    """自由文本输入。"""

    kind: Literal["text_input"] = "text_input"
    name: str
    label: str
    placeholder: str = ""
    value: str = ""


class NumberInputComponent(BaseModel):
    """数值输入。"""

    kind: Literal["number_input"] = "number_input"
    name: str
    label: str
    unit: str = ""
    value: float | None = None


class SelectComponent(BaseModel):
    """单选。"""

    kind: Literal["select"] = "select"
    name: str
    label: str
    options: list[SelectOption]
    value: str = ""


class MultiSelectComponent(BaseModel):
    """多选。"""

    kind: Literal["multi_select"] = "multi_select"
    name: str
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


class A2UIResponse(BaseModel):
    """前端 resume 回传的用户响应。"""

    action: Literal["submit", "reject", "skip"]
    data: dict[str, object] = {}
    """Input component 的 name → value 映射。"""
