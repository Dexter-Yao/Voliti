# ABOUTME: 体验式干预工具测试
# ABOUTME: 验证 compose_experiential_intervention 使用 A2UI payload 格式并正确处理用户响应

import hashlib
from unittest.mock import patch

import pytest

from voliti.tools.experiential import (
    _ASPECT_RATIO_TO_SIZE,
    _intervention_cache,
    compose_experiential_intervention,
)

FAKE_B64 = "ZmFrZV9pbWFnZV9kYXRh"
FAKE_MIME = "image/jpeg"
TEST_PROMPT = "test prompt for intervention"


@pytest.fixture(autouse=True)
def _prefill_cache() -> None:
    """预填充缓存，跳过 Gemini API 调用。"""
    cache_key = hashlib.sha256(TEST_PROMPT.encode()).hexdigest()
    _intervention_cache[cache_key] = (FAKE_B64, FAKE_MIME, FAKE_B64, FAKE_MIME)
    yield
    _intervention_cache.pop(cache_key, None)


class TestExperientialInterventionPayload:
    """interrupt payload 应为 A2UI 格式。"""

    @patch("voliti.tools.experiential.interrupt")
    def test_interrupt_payload_is_a2ui(self, mock_interrupt) -> None:  # noqa: ANN001
        """interrupt 应收到 type=a2ui 的 payload。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
            "caption": "A glimpse of your future.",
        })

        payload = mock_interrupt.call_args[0][0]
        assert payload["type"] == "a2ui"

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_contains_image_component(self, mock_interrupt) -> None:  # noqa: ANN001
        """payload 应包含 image 组件。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
            "caption": "Caption text.",
        })

        payload = mock_interrupt.call_args[0][0]
        components = payload["components"]
        image_components = [c for c in components if c["kind"] == "image"]
        assert len(image_components) == 1
        assert image_components[0]["src"].startswith("data:")

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_contains_caption_text(self, mock_interrupt) -> None:  # noqa: ANN001
        """payload 应包含 caption 文本组件。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "caption": "This is the caption.",
        })

        payload = mock_interrupt.call_args[0][0]
        components = payload["components"]
        text_components = [c for c in components if c["kind"] == "text"]
        assert any("This is the caption." in c["content"] for c in text_components)

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_layout_is_full(self, mock_interrupt) -> None:  # noqa: ANN001
        """体验式干预应使用 full layout。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
        })

        payload = mock_interrupt.call_args[0][0]
        assert payload["layout"] == "full"

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_contains_decision_select(self, mock_interrupt) -> None:  # noqa: ANN001
        """payload 应包含 accept/dismiss 选择组件。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
        })

        payload = mock_interrupt.call_args[0][0]
        components = payload["components"]
        select_components = [c for c in components if c["kind"] == "select"]
        assert len(select_components) == 1
        option_values = [o["value"] for o in select_components[0]["options"]]
        assert "accept" in option_values
        assert "dismiss" in option_values


class TestExperientialInterventionResponse:
    """用户响应处理测试。"""

    @patch("voliti.tools.experiential.interrupt")
    def test_accept_returns_success_message(self, mock_interrupt) -> None:  # noqa: ANN001
        """用户接受应返回成功信息。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        result = compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
            "caption": "A glimpse.",
        })

        assert "accepted" in result.lower()
        assert "Card saved" in result

    @patch("voliti.tools.experiential.interrupt")
    def test_dismiss_returns_dismiss_message(self, mock_interrupt) -> None:  # noqa: ANN001
        """用户取消应返回取消信息。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "dismiss"}}

        result = compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
        })

        assert "reviewed and dismissed" in result.lower()

    @patch("voliti.tools.experiential.interrupt")
    def test_reject_returns_cancel_message(self, mock_interrupt) -> None:  # noqa: ANN001
        """用户 reject 整个交互应返回关闭信息。"""
        mock_interrupt.return_value = {"action": "reject"}

        result = compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
        })

        assert "closed" in result.lower()
        assert "without reviewing" in result.lower()


class TestExperientialCardPersistence:
    """两阶段持久化：_pre_store_card 预写 pending，_finalize_card 确认或删除。"""

    def test_pre_store_card_writes_pending(self) -> None:
        """_pre_store_card 应写入 status=pending 的卡片数据。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.tools.experiential import INTERVENTIONS_NAMESPACE, _pre_store_card

        store = InMemoryStore()
        _pre_store_card(
            store=store,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            caption="Test caption",
            purpose="future_self",
        )

        items = store.search(INTERVENTIONS_NAMESPACE)
        assert len(items) == 1
        item = items[0]
        assert item.key == "card_test01"
        assert item.value["imageData"] == "data:image/jpeg;base64,abc123"
        assert item.value["caption"] == "Test caption"
        assert item.value["purpose"] == "future_self"
        assert item.value["status"] == "pending"
        assert "timestamp" in item.value

    def test_pre_store_card_noop_when_store_is_none(self) -> None:
        """store 为 None 时 _pre_store_card 应静默跳过。"""
        from voliti.tools.experiential import _pre_store_card

        _pre_store_card(
            store=None,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            caption="Test",
            purpose="future_self",
        )

    def test_finalize_card_accepted(self) -> None:
        """accepted=True 应将 status 更新为 accepted。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.tools.experiential import (
            INTERVENTIONS_NAMESPACE,
            _finalize_card,
            _pre_store_card,
        )

        store = InMemoryStore()
        _pre_store_card(
            store=store,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            caption="Test",
            purpose="future_self",
        )
        _finalize_card(store=store, card_id="card_test01", accepted=True)

        item = store.get(INTERVENTIONS_NAMESPACE, "card_test01")
        assert item is not None
        assert item.value["status"] == "accepted"

    def test_finalize_card_rejected(self) -> None:
        """accepted=False 应删除预写入的 card。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.tools.experiential import (
            INTERVENTIONS_NAMESPACE,
            _finalize_card,
            _pre_store_card,
        )

        store = InMemoryStore()
        _pre_store_card(
            store=store,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            caption="Test",
            purpose="future_self",
        )
        _finalize_card(store=store, card_id="card_test01", accepted=False)

        item = store.get(INTERVENTIONS_NAMESPACE, "card_test01")
        assert item is None

    @patch("voliti.tools.experiential.interrupt")
    @patch("voliti.tools.experiential._finalize_card")
    @patch("voliti.tools.experiential._pre_store_card")
    def test_accept_triggers_finalize_accepted(self, mock_pre_store, mock_finalize, mock_interrupt) -> None:  # noqa: ANN001
        """用户接受时应调用 _finalize_card(accepted=True)。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
            "caption": "A glimpse.",
        })

        mock_pre_store.assert_called_once()
        mock_finalize.assert_called_once()
        assert mock_finalize.call_args[1]["accepted"] is True

    @patch("voliti.tools.experiential.interrupt")
    @patch("voliti.tools.experiential._finalize_card")
    @patch("voliti.tools.experiential._pre_store_card")
    def test_reject_triggers_finalize_not_accepted(self, mock_pre_store, mock_finalize, mock_interrupt) -> None:  # noqa: ANN001
        """用户拒绝时应调用 _finalize_card(accepted=False)。"""
        mock_interrupt.return_value = {"action": "reject"}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
        })

        mock_pre_store.assert_called_once()
        mock_finalize.assert_called_once()
        assert mock_finalize.call_args[1]["accepted"] is False

    @patch("voliti.tools.experiential.interrupt")
    @patch("voliti.tools.experiential._finalize_card")
    @patch("voliti.tools.experiential._pre_store_card")
    def test_dismiss_triggers_finalize_not_accepted(self, mock_pre_store, mock_finalize, mock_interrupt) -> None:  # noqa: ANN001
        """用户选择 dismiss 时应调用 _finalize_card(accepted=False)。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "dismiss"}}

        compose_experiential_intervention.invoke({
            "prompt": TEST_PROMPT,
            "purpose": "future_self",
        })

        mock_pre_store.assert_called_once()
        mock_finalize.assert_called_once()
        assert mock_finalize.call_args[1]["accepted"] is False


class TestAspectRatioMapping:
    """aspect_ratio 到 gpt-image-1.5 size 的映射测试。"""

    def test_portrait_mapping(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["3:4"] == "1024x1536"

    def test_landscape_mapping(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["4:3"] == "1536x1024"

    def test_square_mapping(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["1:1"] == "1024x1024"

    def test_wide_fallback(self) -> None:
        """16:9 应 fallback 到横版。"""
        assert _ASPECT_RATIO_TO_SIZE["16:9"] == "1536x1024"

    def test_tall_fallback(self) -> None:
        """9:16 应 fallback 到竖版。"""
        assert _ASPECT_RATIO_TO_SIZE["9:16"] == "1024x1536"
