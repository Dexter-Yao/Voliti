# ABOUTME: LangGraph Runtime Session History provider 适配层测试
# ABOUTME: 验证供应商适配层只做透传，不污染产品级 conversation archive 模型

from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import patch

from voliti.runtime_session_history_langgraph import (
    LangGraphRuntimeSessionHistoryProvider,
    create_conversation_archive_access_layer,
)


def test_langgraph_runtime_session_history_provider_delegates_to_threads_api() -> None:
    thread_payload = {"thread_id": "thread-123"}
    history_payload = [{"checkpoint": {"checkpoint_id": "cp-123"}}]
    search_payload = [{"thread_id": "thread-123"}]

    threads = SimpleNamespace(
        get=AsyncMock(return_value=thread_payload),
        get_history=AsyncMock(return_value=history_payload),
        search=AsyncMock(return_value=search_payload),
    )
    client = SimpleNamespace(threads=threads)
    provider = LangGraphRuntimeSessionHistoryProvider(client=client)

    import asyncio

    thread = asyncio.run(provider.get_thread("thread-123"))
    history = asyncio.run(provider.get_history("thread-123", limit=15))
    threads_list = asyncio.run(provider.search_threads(user_id="user-123", limit=5))

    threads.get.assert_awaited_once_with("thread-123")
    threads.get_history.assert_awaited_once_with("thread-123", limit=15)
    threads.search.assert_awaited_once_with(metadata={"user_id": "user-123"}, limit=5)
    assert thread == thread_payload
    assert history == history_payload
    assert threads_list == search_payload


def test_create_conversation_archive_access_layer_builds_provider_from_server_url() -> None:
    threads = SimpleNamespace()
    client = SimpleNamespace(threads=threads)

    with patch("langgraph_sdk.get_client", return_value=client):
        layer = create_conversation_archive_access_layer(server_url="http://127.0.0.1:2026")

    assert isinstance(layer.provider, LangGraphRuntimeSessionHistoryProvider)
    assert layer.provider.client is client
