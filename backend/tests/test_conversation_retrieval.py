# ABOUTME: Conversation retrieval engine 测试
# ABOUTME: 验证单一 retrieval contract 的语义参数、摘要优先与二次钻取 excerpt

from voliti.conversation_archive import (
    ConversationArchiveAccessLayer,
    ConversationMessageRecord,
    ConversationRecord,
    RuntimeSessionHistoryProvider,
)
from voliti.conversation_retrieval import ConversationRetrievalEngine


class _FakeArchiveProvider(RuntimeSessionHistoryProvider):
    def __init__(self) -> None:
        self.last_user_id: str | None = None
        self.last_limit: int | None = None
        self.records = {
            "conv-2": ConversationRecord(
                conversation_ref="conv-2",
                runtime_thread_ref="conv-2",
                runtime_checkpoint_ref="cp-2",
                user_id="user-1",
                session_type="coaching",
                correlation_id="corr-2",
                started_at="2026-04-10T03:20:00.000000+00:00",
                updated_at="2026-04-10T03:25:00.000000+00:00",
                source="runtime_session_history",
                messages=[
                    ConversationMessageRecord("u2", "user", "这周我压力很大。"),
                    ConversationMessageRecord("a2", "assistant", "我们先看压力和饮食之间的关系。", "coach"),
                    ConversationMessageRecord("u3", "user", "我昨晚聚餐吃多了。"),
                    ConversationMessageRecord("a3", "assistant", "你想回看那次聚餐后的应对吗？", "coach"),
                    ConversationMessageRecord("u4", "user", "今天早上我又有点内疚。"),
                    ConversationMessageRecord("a4", "assistant", "先不要自责，我们拆开看。", "coach"),
                ],
            ),
            "conv-1": ConversationRecord(
                conversation_ref="conv-1",
                runtime_thread_ref="conv-1",
                runtime_checkpoint_ref="cp-1",
                user_id="user-1",
                session_type="onboarding",
                correlation_id="corr-1",
                started_at="2026-04-09T09:00:00.000000+00:00",
                updated_at="2026-04-09T09:05:00.000000+00:00",
                source="runtime_session_history",
                messages=[
                    ConversationMessageRecord("u1", "user", "我是第一次来，希望减脂。"),
                    ConversationMessageRecord("a1", "assistant", "我们先从你的作息开始。", "coach"),
                ],
            ),
        }

    async def get_thread(self, thread_ref: str) -> dict:
        record = self.records[thread_ref]
        return {
            "thread_id": record.runtime_thread_ref,
            "created_at": record.started_at,
            "updated_at": record.updated_at,
            "metadata": {
                "user_id": record.user_id,
                "session_type": record.session_type,
                "correlation_id": record.correlation_id,
            },
        }

    async def get_history(self, thread_ref: str, *, limit: int) -> list[dict]:
        record = self.records[thread_ref]
        return [
            {
                "values": {
                    "messages": [
                        {
                            "id": message.message_ref,
                            "type": "human" if message.role == "user" else "ai",
                            "name": message.author_name,
                            "content": message.content,
                        }
                        for message in record.messages
                    ]
                },
                "checkpoint": {"checkpoint_id": record.runtime_checkpoint_ref},
                "created_at": record.updated_at,
            }
        ]

    async def search_threads(self, *, user_id: str, limit: int) -> list[dict]:
        self.last_user_id = user_id
        self.last_limit = limit
        return [
            {"thread_id": "conv-2", "updated_at": "2026-04-10T03:25:00.000000+00:00"},
            {"thread_id": "conv-1", "updated_at": "2026-04-09T09:05:00.000000+00:00"},
        ]


def test_retrieve_returns_summary_results_by_default() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="聚餐",
            window="recent",
            limit=2,
            detail_level="summary",
        )
    )

    assert result["detail_level"] == "summary"
    assert result["results"][0]["conversation_ref"] == "conv-2"
    assert "聚餐" in result["results"][0]["summary"]
    assert provider.last_user_id == "user-1"
    assert provider.last_limit == 2


def test_retrieve_excerpt_requires_conversation_ref_and_returns_message_slice() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="聚餐",
            window="recent",
            limit=2,
            detail_level="excerpt",
            conversation_ref="conv-2",
        )
    )

    assert result["detail_level"] == "excerpt"
    assert result["conversation_ref"] == "conv-2"
    assert [item["message_ref"] for item in result["excerpt"]] == ["u2", "a2", "u3", "a3"]
    assert result["excerpt"][2]["role"] == "user"
    assert "聚餐" in result["excerpt"][2]["content"]


def test_retrieve_excerpt_without_query_returns_leading_message_slice() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="",
            window="recent",
            limit=2,
            detail_level="excerpt",
            conversation_ref="conv-2",
        )
    )

    assert [item["message_ref"] for item in result["excerpt"]] == ["u2", "a2", "u3", "a3"]


def test_retrieve_excerpt_expands_backward_when_match_is_near_end() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="内疚",
            window="recent",
            limit=2,
            detail_level="excerpt",
            conversation_ref="conv-2",
        )
    )

    assert [item["message_ref"] for item in result["excerpt"]] == ["u3", "a3", "u4", "a4"]


def test_retrieve_excerpt_returns_all_messages_when_conversation_is_short() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="减脂",
            window="recent",
            limit=2,
            detail_level="excerpt",
            conversation_ref="conv-1",
        )
    )

    assert [item["message_ref"] for item in result["excerpt"]] == ["u1", "a1"]


def test_retrieve_excerpt_without_conversation_ref_is_rejected() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    try:
        asyncio.run(
            engine.retrieve(
                user_id="user-1",
                query="聚餐",
                window="recent",
                limit=2,
                detail_level="excerpt",
            )
        )
    except ValueError as exc:
        assert str(exc) == "conversation_ref is required for excerpt retrieval"
    else:
        raise AssertionError("excerpt retrieval should require conversation_ref")


def test_retrieve_rejects_unknown_detail_level() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    try:
        asyncio.run(
            engine.retrieve(
                user_id="user-1",
                query="聚餐",
                window="recent",
                limit=2,
                detail_level="full",
            )
        )
    except ValueError as exc:
        assert str(exc) == "unsupported detail_level: full"
    else:
        raise AssertionError("unsupported detail_level should be rejected")


def test_retrieve_rejects_unknown_window() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    try:
        asyncio.run(
            engine.retrieve(
                user_id="user-1",
                query="聚餐",
                window="all_time",
                limit=2,
                detail_level="summary",
            )
        )
    except ValueError as exc:
        assert str(exc) == "unsupported window: all_time"
    else:
        raise AssertionError("unsupported window should be rejected")


def test_retrieve_returns_empty_summary_results_when_no_match() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="不存在的关键词",
            window="recent",
            limit=2,
            detail_level="summary",
        )
    )

    assert result == {
        "detail_level": "summary",
        "results": [],
    }


def test_retrieve_supports_all_window_with_wider_scan_limit() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="",
            window="all",
            limit=2,
            detail_level="summary",
        )
    )

    assert result["detail_level"] == "summary"
    assert len(result["results"]) == 2
    assert provider.last_limit == 50


def test_retrieve_filters_summary_results_by_time_hint() -> None:
    import asyncio

    provider = _FakeArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="",
            window="all",
            limit=2,
            detail_level="summary",
            time_hint="2026-04-09",
        )
    )

    assert result == {
        "detail_level": "summary",
        "results": [
            {
                "conversation_ref": "conv-1",
                "session_type": "onboarding",
                "updated_at": "2026-04-09T09:05:00.000000+00:00",
                "summary": "我是第一次来，希望减脂。 / 我们先从你的作息开始。",
            }
        ],
    }


def test_retrieve_sorts_summary_results_by_updated_at_desc() -> None:
    import asyncio

    class _UnsortedArchiveProvider(_FakeArchiveProvider):
        async def search_threads(self, *, user_id: str, limit: int) -> list[dict]:
            self.last_user_id = user_id
            self.last_limit = limit
            return [
                {"thread_id": "conv-1", "updated_at": "2026-04-09T09:05:00.000000+00:00"},
                {"thread_id": "conv-2", "updated_at": "2026-04-10T03:25:00.000000+00:00"},
            ]

    provider = _UnsortedArchiveProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)
    engine = ConversationRetrievalEngine(archive=layer)

    result = asyncio.run(
        engine.retrieve(
            user_id="user-1",
            query="",
            window="all",
            limit=2,
            detail_level="summary",
        )
    )

    assert [item["conversation_ref"] for item in result["results"]] == ["conv-2", "conv-1"]
