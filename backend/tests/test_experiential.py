# ABOUTME: Witness Card 生成工具测试
# ABOUTME: 验证 compose_witness_card 的 A2UI payload、错误处理、元数据存储和用户响应

import hashlib
from unittest.mock import MagicMock, patch

import pytest

from voliti.tools.experiential import (
    _ASPECT_RATIO_TO_SIZE,
    CARD_STATUS_ACCEPTED,
    CARD_STATUS_PENDING,
    CARD_STATUS_REJECTED,
    _card_cache,
    compose_witness_card,
)

FAKE_B64 = "ZmFrZV9pbWFnZV9kYXRh"
FAKE_MIME = "image/jpeg"
TEST_PROMPT = "test prompt for witness card"
TEST_USER_ID = "device_0001"


def invoke_witness_card(payload: dict) -> str:
    return compose_witness_card.invoke(
        payload,
        config={"configurable": {"user_id": TEST_USER_ID}},
    )


@pytest.fixture(autouse=True)
def _prefill_cache() -> None:
    """预填充缓存，跳过 API 调用。"""
    cache_key = hashlib.sha256(TEST_PROMPT.encode()).hexdigest()
    _card_cache[cache_key] = (FAKE_B64, FAKE_MIME, FAKE_B64, FAKE_MIME)
    yield
    _card_cache.pop(cache_key, None)


class TestWitnessCardPayload:
    """interrupt payload 应为 A2UI 格式。"""

    @patch("voliti.tools.experiential.interrupt")
    def test_interrupt_payload_is_a2ui(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({
            "prompt": TEST_PROMPT,
            "narrative": "你做到了。",
            "achievement_title": "首张卡片",
            "achievement_type": "journey",
        })

        payload = mock_interrupt.call_args[0][0]
        assert payload["type"] == "a2ui"

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_contains_image_component(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({
            "prompt": TEST_PROMPT,
            "narrative": "Narrative text.",
            "achievement_title": "Test",
        })

        payload = mock_interrupt.call_args[0][0]
        components = payload["components"]
        image_components = [c for c in components if c["kind"] == "image"]
        assert len(image_components) == 1
        assert image_components[0]["src"].startswith("data:")

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_contains_narrative_text(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({
            "prompt": TEST_PROMPT,
            "narrative": "连续 7 天，你每天都选择了先喝水。",
        })

        payload = mock_interrupt.call_args[0][0]
        components = payload["components"]
        text_components = [c for c in components if c["kind"] == "text"]
        assert any("连续 7 天" in c["text"] for c in text_components)

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_layout_is_full(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({"prompt": TEST_PROMPT})

        payload = mock_interrupt.call_args[0][0]
        assert payload["layout"] == "full"

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_metadata_includes_achievement_fields(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({
            "prompt": TEST_PROMPT,
            "achievement_type": "implicit",
            "linked_lifesign_id": "ls_010",
            "chapter_id": "ch_001",
            "user_quote": "其实没那么难",
        })

        payload = mock_interrupt.call_args[0][0]
        metadata = payload["metadata"]
        assert metadata["achievement_type"] == "implicit"
        assert metadata["linked_lifesign_id"] == "ls_010"
        assert metadata["chapter_id"] == "ch_001"
        assert metadata["user_quote"] == "其实没那么难"

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_metadata_omits_none_fields(self, mock_interrupt) -> None:  # noqa: ANN001
        """nullable 字段为空时不应出现在 metadata 中。"""
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({
            "prompt": TEST_PROMPT,
            "achievement_type": "implicit",
        })

        payload = mock_interrupt.call_args[0][0]
        metadata = payload["metadata"]
        assert "linked_lifesign_id" not in metadata
        assert "chapter_id" not in metadata
        assert "user_quote" not in metadata

    @patch("voliti.tools.experiential.interrupt")
    def test_payload_contains_accept_skip_select(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        invoke_witness_card({"prompt": TEST_PROMPT})

        payload = mock_interrupt.call_args[0][0]
        components = payload["components"]
        select_components = [c for c in components if c["kind"] == "select"]
        assert len(select_components) == 1
        option_values = [o["value"] for o in select_components[0]["options"]]
        assert "accept" in option_values
        assert "dismiss" in option_values


class TestWitnessCardResponse:
    """用户响应处理测试。"""

    @patch("voliti.tools.experiential.interrupt")
    def test_accept_returns_success_message(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "accept"}}

        result = invoke_witness_card({
            "prompt": TEST_PROMPT,
            "achievement_title": "连续 Check-in",
        })

        assert "accepted" in result.lower()
        assert "Card saved" in result

    @patch("voliti.tools.experiential.interrupt")
    def test_dismiss_returns_dismiss_message(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "submit", "data": {"decision": "dismiss"}}

        result = invoke_witness_card({
            "prompt": TEST_PROMPT,
            "achievement_title": "Test",
        })

        assert "reviewed and dismissed" in result.lower()

    @patch("voliti.tools.experiential.interrupt")
    def test_reject_returns_cancel_message(self, mock_interrupt) -> None:  # noqa: ANN001
        mock_interrupt.return_value = {"action": "reject"}

        result = invoke_witness_card({
            "prompt": TEST_PROMPT,
            "achievement_title": "Test",
        })

        assert "closed" in result.lower()


class TestWitnessCardErrorHandling:
    """API 错误处理测试。"""

    def test_api_timeout_returns_graceful_error(self) -> None:
        """API 超时应返回结构化错误文本，不抛异常。"""
        import httpx

        cache_key = hashlib.sha256(b"unique_timeout_prompt").hexdigest()
        _card_cache.pop(cache_key, None)

        with patch(
            "voliti.tools.experiential._generate_image",
            side_effect=httpx.TimeoutException("Connection timed out"),
        ):
            result = invoke_witness_card({
                "prompt": "unique_timeout_prompt",
                "achievement_title": "Test",
            })

        assert "Image generation failed" in result
        assert "TimeoutException" in result
        assert "Continue the conversation" in result

    def test_api_rate_limit_returns_graceful_error(self) -> None:
        """API 429 应返回结构化错误文本。"""
        cache_key = hashlib.sha256(b"unique_ratelimit_prompt").hexdigest()
        _card_cache.pop(cache_key, None)

        mock_response = MagicMock()
        mock_response.status_code = 429

        from openai import RateLimitError

        with patch(
            "voliti.tools.experiential._generate_image",
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=mock_response,
                body=None,
            ),
        ):
            result = invoke_witness_card({
                "prompt": "unique_ratelimit_prompt",
                "achievement_title": "Test",
            })

        assert "Image generation failed" in result
        assert "Continue the conversation" in result

    def test_empty_image_returns_graceful_error(self) -> None:
        """空图片响应应返回结构化错误文本。"""
        cache_key = hashlib.sha256(b"unique_empty_prompt").hexdigest()
        _card_cache.pop(cache_key, None)

        with patch(
            "voliti.tools.experiential._generate_image",
            side_effect=ValueError("gpt-image-1.5 未返回图片数据"),
        ):
            result = invoke_witness_card({
                "prompt": "unique_empty_prompt",
                "achievement_title": "Test",
            })

        assert "Image generation failed" in result
        assert "ValueError" in result


class TestWitnessCardPersistence:
    """元数据存储测试。"""

    def test_resolve_interventions_namespace_uses_configured_user_id(self) -> None:
        from voliti.tools.experiential import resolve_interventions_namespace

        assert resolve_interventions_namespace({
            "configurable": {"user_id": TEST_USER_ID}
        }) == ("voliti", TEST_USER_ID, "interventions")

    def test_pre_store_card_writes_metadata(self) -> None:
        """_pre_store_card 应写入完整元数据。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.store_contract import make_interventions_namespace
        from voliti.tools.experiential import _pre_store_card

        store = InMemoryStore()
        namespace = make_interventions_namespace(TEST_USER_ID)
        _pre_store_card(
            store=store,
            namespace=namespace,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            narrative="你做到了连续 7 天。",
            achievement_type="implicit",
            achievement_title="连续 Check-in",
            chapter_id="ch_001",
            linked_lifesign_id="ls_010",
            user_quote="其实没那么难",
        )

        items = store.search(namespace)
        assert len(items) == 1
        item = items[0]
        assert item.key == "card_test01"
        assert item.value["narrative"] == "你做到了连续 7 天。"
        assert item.value["achievement_type"] == "implicit"
        assert item.value["achievement_title"] == "连续 Check-in"
        assert item.value["chapter_id"] == "ch_001"
        assert item.value["linked_lifesign_id"] == "ls_010"
        assert item.value["user_quote"] == "其实没那么难"
        assert item.value["status"] == CARD_STATUS_PENDING
        assert "timestamp" in item.value

    def test_pre_store_card_nullable_fields(self) -> None:
        """隐性成就场景下 nullable 字段可以为 None。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.store_contract import make_interventions_namespace
        from voliti.tools.experiential import _pre_store_card

        store = InMemoryStore()
        namespace = make_interventions_namespace(TEST_USER_ID)
        _pre_store_card(
            store=store,
            namespace=namespace,
            card_id="card_test02",
            image_data_url="data:image/jpeg;base64,abc123",
            narrative="连续 10 天 check-in。",
            achievement_type="implicit",
            achievement_title="连续 Check-in",
            chapter_id=None,
            linked_lifesign_id=None,
            user_quote=None,
        )

        items = store.search(namespace)
        assert len(items) == 1
        assert items[0].value["chapter_id"] is None
        assert items[0].value["user_quote"] is None

    def test_finalize_card_accepted_updates_status(self) -> None:
        """accepted=True 应将 status 更新为 accepted。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.tools.experiential import (
            _finalize_card,
            _pre_store_card,
        )
        from voliti.store_contract import make_interventions_namespace

        store = InMemoryStore()
        namespace = make_interventions_namespace(TEST_USER_ID)
        _pre_store_card(
            store=store,
            namespace=namespace,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            narrative="Test",
            achievement_type="explicit",
            achievement_title="Test",
            chapter_id=None,
            linked_lifesign_id=None,
            user_quote=None,
        )
        _finalize_card(
            store=store,
            namespace=namespace,
            card_id="card_test01",
            accepted=True,
        )

        item = store.get(namespace, "card_test01")
        assert item is not None
        assert item.value["status"] == CARD_STATUS_ACCEPTED

    def test_finalize_card_rejected_updates_status(self) -> None:
        """accepted=False 应将 status 更新为 rejected。"""
        from langgraph.store.memory import InMemoryStore

        from voliti.tools.experiential import (
            _finalize_card,
            _pre_store_card,
        )
        from voliti.store_contract import make_interventions_namespace

        store = InMemoryStore()
        namespace = make_interventions_namespace(TEST_USER_ID)
        _pre_store_card(
            store=store,
            namespace=namespace,
            card_id="card_test01",
            image_data_url="data:image/jpeg;base64,abc123",
            narrative="Test",
            achievement_type="explicit",
            achievement_title="Test",
            chapter_id=None,
            linked_lifesign_id=None,
            user_quote=None,
        )
        _finalize_card(
            store=store,
            namespace=namespace,
            card_id="card_test01",
            accepted=False,
        )

        item = store.get(namespace, "card_test01")
        assert item is not None
        assert item.value["status"] == CARD_STATUS_REJECTED


class TestAspectRatioMapping:
    """aspect_ratio 到 gpt-image-1.5 size 的映射测试。"""

    def test_portrait_mapping(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["3:4"] == "1024x1536"

    def test_landscape_mapping(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["4:3"] == "1536x1024"

    def test_square_mapping(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["1:1"] == "1024x1024"

    def test_wide_fallback(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["16:9"] == "1536x1024"

    def test_tall_fallback(self) -> None:
        assert _ASPECT_RATIO_TO_SIZE["9:16"] == "1024x1536"
