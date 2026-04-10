# ABOUTME: Conversation archive retrieval tool 测试
# ABOUTME: 验证统一 envelope、语义参数与 Coach 可见输出边界

import asyncio
from unittest.mock import AsyncMock, patch

from voliti.tools.conversation_archive import (
    resolve_runtime_api_url,
    retrieve_conversation_archive,
)


def test_resolve_runtime_api_url_prefers_vendor_neutral_env(monkeypatch) -> None:
    monkeypatch.setenv("VOLITI_RUNTIME_API_URL", "http://127.0.0.1:3030")
    monkeypatch.setenv("LANGGRAPH_API_URL", "http://127.0.0.1:2025")

    assert resolve_runtime_api_url() == "http://127.0.0.1:3030"


def test_resolve_runtime_api_url_falls_back_to_langgraph_env(monkeypatch) -> None:
    monkeypatch.delenv("VOLITI_RUNTIME_API_URL", raising=False)
    monkeypatch.setenv("LANGGRAPH_API_URL", "http://127.0.0.1:2025")

    assert resolve_runtime_api_url() == "http://127.0.0.1:2025"


def test_retrieve_conversation_archive_returns_summary_envelope(monkeypatch) -> None:
    monkeypatch.setenv("VOLITI_RUNTIME_API_URL", "http://127.0.0.1:3030")

    fake_engine = AsyncMock()
    fake_engine.retrieve.return_value = {
        "detail_level": "summary",
        "results": [
            {
                "conversation_ref": "conv-2",
                "session_type": "coaching",
                "updated_at": "2026-04-10T03:25:00.000000+00:00",
                "summary": "我昨晚聚餐吃多了。 / 你想回看那次聚餐后的应对吗？",
            }
        ],
    }

    with patch(
        "voliti.tools.conversation_archive.get_config",
        return_value={"configurable": {"user_id": "user-1"}},
    ), patch(
        "voliti.tools.conversation_archive.create_conversation_archive_access_layer"
    ) as mock_create_layer, patch(
        "voliti.tools.conversation_archive.ConversationRetrievalEngine",
        return_value=fake_engine,
    ):
        result = asyncio.run(
            retrieve_conversation_archive.ainvoke(
                {
                    "query": "聚餐",
                    "window": "recent",
                    "limit": 3,
                    "detail_level": "summary",
                }
            )
        )

    mock_create_layer.assert_called_once_with(server_url="http://127.0.0.1:3030")
    fake_engine.retrieve.assert_awaited_once_with(
        user_id="user-1",
        query="聚餐",
        window="recent",
        limit=3,
        detail_level="summary",
        conversation_ref=None,
        time_hint=None,
    )
    assert result["status"] == "ok"
    assert result["error_code"] is None
    assert result["payload"]["detail_level"] == "summary"
    assert "找到" in result["coach_message"]


def test_retrieve_conversation_archive_returns_error_envelope(monkeypatch) -> None:
    monkeypatch.setenv("VOLITI_RUNTIME_API_URL", "http://127.0.0.1:3030")

    fake_engine = AsyncMock()
    fake_engine.retrieve.side_effect = ValueError(
        "conversation_ref is required for excerpt retrieval"
    )

    with patch(
        "voliti.tools.conversation_archive.get_config",
        return_value={"configurable": {"user_id": "user-1"}},
    ), patch(
        "voliti.tools.conversation_archive.create_conversation_archive_access_layer"
    ), patch(
        "voliti.tools.conversation_archive.ConversationRetrievalEngine",
        return_value=fake_engine,
    ):
        result = asyncio.run(
            retrieve_conversation_archive.ainvoke(
                {
                    "query": "聚餐",
                    "window": "recent",
                    "limit": 3,
                    "detail_level": "excerpt",
                }
            )
        )

    assert result == {
        "status": "error",
        "payload": None,
        "error_code": "conversation_archive_request_invalid",
        "coach_message": "Conversation archive retrieval request is invalid.",
    }


def test_retrieve_conversation_archive_returns_error_when_user_id_missing(monkeypatch) -> None:
    monkeypatch.setenv("VOLITI_RUNTIME_API_URL", "http://127.0.0.1:3030")

    with patch(
        "voliti.tools.conversation_archive.get_config",
        return_value={"configurable": {}},
    ):
        result = asyncio.run(
            retrieve_conversation_archive.ainvoke(
                {
                    "query": "聚餐",
                    "window": "recent",
                    "limit": 3,
                    "detail_level": "summary",
                }
            )
        )

    assert result == {
        "status": "error",
        "payload": None,
        "error_code": "conversation_archive_identity_unavailable",
        "coach_message": "Conversation archive retrieval requires a valid user identity.",
    }


def test_retrieve_conversation_archive_hides_runtime_transport_details(monkeypatch) -> None:
    monkeypatch.setenv("VOLITI_RUNTIME_API_URL", "http://127.0.0.1:3030")

    with patch(
        "voliti.tools.conversation_archive.get_config",
        return_value={"configurable": {"user_id": "user-1"}},
    ), patch(
        "voliti.tools.conversation_archive.create_conversation_archive_access_layer",
        side_effect=OSError("connection refused"),
    ):
        result = asyncio.run(
            retrieve_conversation_archive.ainvoke(
                {
                    "query": "聚餐",
                    "window": "recent",
                    "limit": 3,
                    "detail_level": "summary",
                }
            )
        )

    assert result == {
        "status": "error",
        "payload": None,
        "error_code": "conversation_archive_unavailable",
        "coach_message": "Conversation archive retrieval is temporarily unavailable.",
    }


def test_retrieve_conversation_archive_hides_incomplete_metadata_details(monkeypatch) -> None:
    monkeypatch.setenv("VOLITI_RUNTIME_API_URL", "http://127.0.0.1:3030")

    fake_engine = AsyncMock()
    fake_engine.retrieve.side_effect = ValueError(
        "runtime session history is missing required metadata"
    )

    with patch(
        "voliti.tools.conversation_archive.get_config",
        return_value={"configurable": {"user_id": "user-1"}},
    ), patch(
        "voliti.tools.conversation_archive.create_conversation_archive_access_layer"
    ), patch(
        "voliti.tools.conversation_archive.ConversationRetrievalEngine",
        return_value=fake_engine,
    ):
        result = asyncio.run(
            retrieve_conversation_archive.ainvoke(
                {
                    "query": "聚餐",
                    "window": "recent",
                    "limit": 3,
                    "detail_level": "summary",
                }
            )
        )

    assert result == {
        "status": "error",
        "payload": None,
        "error_code": "conversation_archive_record_incomplete",
        "coach_message": "Conversation archive data is incomplete for this request.",
    }
