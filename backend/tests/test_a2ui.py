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
    validate_a2ui_response,
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


class TestA2UIResponseValidation:
    """A2UIResponse 契约验证测试。"""

    def make_payload(self) -> A2UIPayload:
        return A2UIPayload(components=[
            SliderComponent(key="energy", label="Energy", min=1, max=10, step=1),
            SelectComponent(
                key="decision",
                label="Decision",
                options=[
                    SelectOption(label="Accept", value="accept"),
                    SelectOption(label="Skip", value="skip"),
                ],
            ),
            MultiSelectComponent(
                key="tags",
                label="Tags",
                options=[
                    SelectOption(label="A", value="a"),
                    SelectOption(label="B", value="b"),
                ],
            ),
            TextInputComponent(key="note", label="Note"),
            NumberInputComponent(key="weight", label="Weight"),
        ])

    def test_accepts_matching_interrupt_id_and_valid_data(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_123",
            data={
                "energy": 7,
                "decision": "accept",
                "tags": ["a", "b"],
                "note": "ready",
                "weight": 72.5,
            },
        )

        validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_missing_interrupt_id(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(action="submit", data={"energy": 7})

        with pytest.raises(ValueError, match="interrupt_id"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_mismatched_interrupt_id(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_old",
            data={"energy": 7},
        )

        with pytest.raises(ValueError, match="interrupt_id"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_unknown_input_key(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_123",
            data={"unexpected": "value"},
        )

        with pytest.raises(ValueError, match="unexpected"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_slider_value_out_of_range(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_123",
            data={"energy": 11},
        )

        with pytest.raises(ValueError, match="energy"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_invalid_select_option(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_123",
            data={"decision": "dismiss"},
        )

        with pytest.raises(ValueError, match="decision"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_invalid_multi_select_option(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_123",
            data={"tags": ["a", "c"]},
        )

        with pytest.raises(ValueError, match="tags"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_reject_with_data(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="reject",
            interrupt_id="int_123",
            data={"energy": 7},
        )

        with pytest.raises(ValueError, match="data"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_rejects_skip_with_data(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="skip",
            interrupt_id="int_123",
            data={"energy": 7},
        )

        with pytest.raises(ValueError, match="data"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_reject_with_reason_passes(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="reject",
            interrupt_id="int_123",
            reason="现在不方便回答",
        )

        validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_reject_without_reason_passes(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="reject",
            interrupt_id="int_123",
        )

        validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_skip_with_reason_raises(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="skip",
            interrupt_id="int_123",
            reason="不想回答",
        )

        with pytest.raises(ValueError, match="reason"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")

    def test_submit_with_reason_raises(self) -> None:
        payload = self.make_payload()
        response = A2UIResponse(
            action="submit",
            interrupt_id="int_123",
            data={"energy": 5},
            reason="should not be here",
        )

        with pytest.raises(ValueError, match="reason"):
            validate_a2ui_response(payload, response, expected_interrupt_id="int_123")
