# ABOUTME: A2UI 组件模型测试
# ABOUTME: 验证 8 种 UI 原语、Component 联合类型、Payload 与 Response 的序列化和验证

from typing import get_args

import pytest
from pydantic import ValidationError

from voliti.a2ui import (
    A2UIPayload,
    A2UIResponse,
    Component,
    ImageComponent,
    MultiSelectComponent,
    NumberInputComponent,
    ProtocolPromptComponent,
    SelectComponent,
    SelectOption,
    SliderComponent,
    TextComponent,
    TextInputComponent,
)


# --- Display Components ---


class TestTextComponent:
    """TextComponent 测试。"""

    def test_kind_is_text(self) -> None:
        c = TextComponent(text="hello")
        assert c.kind == "text"

    def test_text_required(self) -> None:
        with pytest.raises(ValidationError):
            TextComponent()  # type: ignore[call-arg]


class TestImageComponent:
    """ImageComponent 测试。"""

    def test_kind_is_image(self) -> None:
        c = ImageComponent(src="data:image/jpeg;base64,abc")
        assert c.kind == "image"

    def test_alt_defaults_empty(self) -> None:
        c = ImageComponent(src="data:image/jpeg;base64,abc")
        assert c.alt == ""

    def test_src_required(self) -> None:
        with pytest.raises(ValidationError):
            ImageComponent()  # type: ignore[call-arg]


# --- Input Components ---


class TestSliderComponent:
    """SliderComponent 测试。"""

    def test_kind_is_slider(self) -> None:
        c = SliderComponent(key="energy", label="Energy")
        assert c.kind == "slider"

    def test_defaults(self) -> None:
        c = SliderComponent(key="energy", label="Energy")
        assert c.min == 1
        assert c.max == 10
        assert c.step == 1
        assert c.value is None

    def test_name_and_label_required(self) -> None:
        with pytest.raises(ValidationError):
            SliderComponent()  # type: ignore[call-arg]


class TestTextInputComponent:
    """TextInputComponent 测试。"""

    def test_kind_is_text_input(self) -> None:
        c = TextInputComponent(key="note", label="Note")
        assert c.kind == "text_input"

    def test_defaults(self) -> None:
        c = TextInputComponent(key="note", label="Note")
        assert c.placeholder == ""
        assert c.value == ""


class TestNumberInputComponent:
    """NumberInputComponent 测试。"""

    def test_kind_is_number_input(self) -> None:
        c = NumberInputComponent(key="kcal", label="Calories")
        assert c.kind == "number_input"

    def test_defaults(self) -> None:
        c = NumberInputComponent(key="kcal", label="Calories")
        assert c.unit == ""
        assert c.value is None


class TestSelectComponent:
    """SelectComponent 测试。"""

    def test_kind_is_select(self) -> None:
        opts = [SelectOption(label="High", value="high")]
        c = SelectComponent(key="confidence", label="Confidence", options=opts)
        assert c.kind == "select"

    def test_value_defaults_empty(self) -> None:
        opts = [SelectOption(label="A", value="a")]
        c = SelectComponent(key="x", label="X", options=opts)
        assert c.value == ""

    def test_options_required(self) -> None:
        with pytest.raises(ValidationError):
            SelectComponent(key="x", label="X")  # type: ignore[call-arg]


class TestMultiSelectComponent:
    """MultiSelectComponent 测试。"""

    def test_kind_is_multi_select(self) -> None:
        opts = [SelectOption(label="Tag", value="tag")]
        c = MultiSelectComponent(key="tags", label="Tags", options=opts)
        assert c.kind == "multi_select"

    def test_value_defaults_empty_list(self) -> None:
        opts = [SelectOption(label="A", value="a")]
        c = MultiSelectComponent(key="tags", label="Tags", options=opts)
        assert c.value == []


# --- Component Union ---


class TestComponent:
    """Component discriminated union 测试。"""

    def test_resolves_text(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({"kind": "text", "text": "hello"})
        assert isinstance(c, TextComponent)

    def test_resolves_slider(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({"kind": "slider", "key": "x", "label": "X"})
        assert isinstance(c, SliderComponent)

    def test_resolves_image(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({"kind": "image", "src": "data:img"})
        assert isinstance(c, ImageComponent)

    def test_resolves_text_input(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({"kind": "text_input", "key": "n", "label": "N"})
        assert isinstance(c, TextInputComponent)

    def test_resolves_number_input(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({"kind": "number_input", "key": "n", "label": "N"})
        assert isinstance(c, NumberInputComponent)

    def test_resolves_select(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({
            "kind": "select",
            "key": "x",
            "label": "X",
            "options": [{"label": "A", "value": "a"}],
        })
        assert isinstance(c, SelectComponent)

    def test_resolves_multi_select(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        c = adapter.validate_python({
            "kind": "multi_select",
            "key": "x",
            "label": "X",
            "options": [{"label": "A", "value": "a"}],
        })
        assert isinstance(c, MultiSelectComponent)

    def test_invalid_kind_raises(self) -> None:
        from pydantic import TypeAdapter

        adapter = TypeAdapter(Component)
        with pytest.raises(ValidationError):
            adapter.validate_python({"kind": "invalid", "content": "x"})

    def test_covers_all_component_types(self) -> None:
        """Component 联合类型应包含所有 8 种组件。"""
        expected = {
            TextComponent,
            ImageComponent,
            ProtocolPromptComponent,
            SliderComponent,
            TextInputComponent,
            NumberInputComponent,
            SelectComponent,
            MultiSelectComponent,
        }
        # Annotated[Union[...], Field(...)] → get_args returns (Union, FieldInfo)
        # get_args on the Union gives the actual types
        union_type = get_args(Component)[0]
        actual = set(get_args(union_type))
        assert actual == expected


# --- Payload & Response ---


class TestA2UIPayload:
    """A2UIPayload 测试。"""

    def test_type_is_a2ui(self) -> None:
        p = A2UIPayload(components=[TextComponent(text="hi")])
        assert p.type == "a2ui"

    def test_layout_defaults_three_quarter(self) -> None:
        p = A2UIPayload(components=[])
        assert p.layout == "three-quarter"

    def test_full_layout(self) -> None:
        p = A2UIPayload(components=[], layout="full")
        assert p.layout == "full"

    def test_components_validated(self) -> None:
        """组件通过 dict 传入时应自动解析为正确类型。"""
        p = A2UIPayload(components=[{"kind": "text", "text": "hello"}])
        assert isinstance(p.components[0], TextComponent)

    def test_invalid_component_raises(self) -> None:
        with pytest.raises(ValidationError):
            A2UIPayload(components=[{"kind": "bad"}])

    def test_serialization_roundtrip(self) -> None:
        original = A2UIPayload(
            components=[
                TextComponent(text="hi"),
                SliderComponent(key="x", label="X", value=5),
            ],
            layout="half",
        )
        data = original.model_dump()
        restored = A2UIPayload.model_validate(data)
        assert restored == original


class TestA2UIResponse:
    """A2UIResponse 测试。"""

    def test_submit_with_data(self) -> None:
        r = A2UIResponse(action="submit", data={"energy": 7, "mood": 6})
        assert r.action == "submit"
        assert r.data == {"energy": 7, "mood": 6}

    def test_reject_defaults_empty_data(self) -> None:
        r = A2UIResponse(action="reject")
        assert r.data == {}

    def test_skip(self) -> None:
        r = A2UIResponse(action="skip")
        assert r.action == "skip"

    def test_invalid_action_raises(self) -> None:
        with pytest.raises(ValidationError):
            A2UIResponse(action="invalid")  # type: ignore[arg-type]
