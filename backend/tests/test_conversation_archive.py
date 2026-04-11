# ABOUTME: Conversation archive access layer 测试
# ABOUTME: 验证运行时 session history 到稳定 conversation record 的规范化

import asyncio

from voliti.conversation_archive import (
    ConversationArchiveAccessLayer,
    ConversationArchiveAccessError,
    ConversationMessageRecord,
    ConversationRecord,
    RuntimeSessionHistoryProvider,
    normalize_conversation_record,
)


def test_normalize_conversation_record_builds_stable_record() -> None:
    thread = {
        "thread_id": "thread-123",
        "created_at": "2026-04-10T02:32:07.903960+00:00",
        "updated_at": "2026-04-10T02:32:13.797897+00:00",
        "metadata": {
            "user_id": "user-123",
            "session_type": "coaching",
            "correlation_id": "corr-123",
        },
    }
    history = [
        {
            "values": {
                "messages": [
                    {
                        "id": "m-user-1",
                        "type": "human",
                        "content": "[2026-04-10T02:32:00Z] 你好，请简单回复一句。",
                    }
                ]
            },
            "checkpoint": {"checkpoint_id": "cp-1"},
            "created_at": "2026-04-10T02:32:08.000000+00:00",
        },
        {
            "values": {
                "messages": [
                    {
                        "id": "m-user-1",
                        "type": "human",
                        "content": "[2026-04-10T02:32:00Z] 你好，请简单回复一句。",
                    },
                    {
                        "id": "m-ai-1",
                        "type": "ai",
                        "name": "coach",
                        "content": "你好，我在这。",
                    },
                ]
            },
            "checkpoint": {"checkpoint_id": "cp-2"},
            "created_at": "2026-04-10T02:32:13.797897+00:00",
        },
    ]

    record = normalize_conversation_record(thread=thread, history=history)

    assert record == ConversationRecord(
        conversation_ref="thread-123",
        runtime_thread_ref="thread-123",
        runtime_checkpoint_ref="cp-2",
        user_id="user-123",
        session_type="coaching",
        correlation_id="corr-123",
        started_at="2026-04-10T02:32:07.903960+00:00",
        updated_at="2026-04-10T02:32:13.797897+00:00",
        source="runtime_session_history",
        messages=[
            ConversationMessageRecord(
                message_ref="m-user-1",
                role="user",
                content="[2026-04-10T02:32:00Z] 你好，请简单回复一句。",
                author_name=None,
            ),
            ConversationMessageRecord(
                message_ref="m-ai-1",
                role="assistant",
                content="你好，我在这。",
                author_name="coach",
            ),
        ],
    )


def test_normalize_conversation_record_filters_runtime_noise_and_deduplicates() -> None:
    thread = {
        "thread_id": "thread-456",
        "created_at": "2026-04-10T02:40:00.000000+00:00",
        "updated_at": "2026-04-10T02:40:05.000000+00:00",
        "metadata": {
            "user_id": "user-456",
            "session_type": "onboarding",
            "correlation_id": "corr-456",
        },
    }
    history = [
        {
            "values": {"messages": []},
            "tasks": [
                {
                    "result": {
                        "messages": [
                            {
                                "id": "m-ai-noise",
                                "type": "ai",
                                "content": "不应从 tasks.result 混入正式对话。",
                            }
                        ]
                    }
                }
            ],
            "checkpoint": {"checkpoint_id": "cp-noise"},
            "created_at": "2026-04-10T02:40:01.000000+00:00",
        },
        {
            "values": {
                "messages": [
                    {"id": "m-user-2", "type": "human", "content": "我是第一次来。"},
                    {"id": "m-ai-2", "type": "ai", "content": "欢迎你，我们从一个小问题开始。"},
                    {"id": "m-tool", "type": "tool", "content": "tool noise"},
                ]
            },
            "checkpoint": {"checkpoint_id": "cp-final"},
            "created_at": "2026-04-10T02:40:05.000000+00:00",
        },
    ]

    record = normalize_conversation_record(thread=thread, history=history)

    assert [message.message_ref for message in record.messages] == ["m-user-2", "m-ai-2"]
    assert [message.role for message in record.messages] == ["user", "assistant"]
    assert record.session_type == "onboarding"
    assert record.runtime_checkpoint_ref == "cp-final"


def test_normalize_conversation_record_requires_user_identity_and_session_type() -> None:
    thread = {
        "thread_id": "thread-789",
        "created_at": "2026-04-10T02:50:00.000000+00:00",
        "updated_at": "2026-04-10T02:50:05.000000+00:00",
        "metadata": {},
    }

    try:
        normalize_conversation_record(thread=thread, history=[])
    except ValueError as exc:
        assert str(exc) == "runtime session history is missing required metadata"
    else:
        raise AssertionError("normalize_conversation_record should reject missing metadata")


def test_normalize_conversation_record_rejects_legacy_session_mode_metadata() -> None:
    thread = {
        "thread_id": "thread-790",
        "created_at": "2026-04-10T02:50:00.000000+00:00",
        "updated_at": "2026-04-10T02:50:05.000000+00:00",
        "metadata": {
            "user_id": "user-790",
            "session_mode": "coaching",
        },
    }

    try:
        normalize_conversation_record(thread=thread, history=[])
    except ValueError as exc:
        assert str(exc) == "runtime session history is missing required metadata"
    else:
        raise AssertionError("normalize_conversation_record should reject legacy session_mode metadata")


class _FakeRuntimeSessionHistoryProvider(RuntimeSessionHistoryProvider):
    def __init__(self) -> None:
        self.thread = {
            "thread_id": "thread-999",
            "created_at": "2026-04-10T03:00:00.000000+00:00",
            "updated_at": "2026-04-10T03:00:06.000000+00:00",
            "metadata": {
                "user_id": "user-999",
                "session_type": "coaching",
                "correlation_id": "corr-999",
            },
        }
        self.history = [
            {
                "values": {
                    "messages": [
                        {"id": "m-user-9", "type": "human", "content": "请记下这次对话。"},
                        {"id": "m-ai-9", "type": "ai", "name": "coach", "content": "我会在需要时回看它。"},
                    ]
                },
                "checkpoint": {"checkpoint_id": "cp-999"},
                "created_at": "2026-04-10T03:00:06.000000+00:00",
            }
        ]
        self.last_thread_ref: str | None = None
        self.last_limit: int | None = None
        self.last_user_id: str | None = None

    async def get_thread(self, thread_ref: str) -> dict:
        self.last_thread_ref = thread_ref
        return self.thread

    async def get_history(self, thread_ref: str, *, limit: int) -> list[dict]:
        self.last_thread_ref = thread_ref
        self.last_limit = limit
        return self.history

    async def search_threads(self, *, user_id: str, limit: int) -> list[dict]:
        self.last_user_id = user_id
        self.last_limit = limit
        return [
            {
                "thread_id": "thread-002",
                "updated_at": "2026-04-10T03:10:00.000000+00:00",
            },
            {
                "thread_id": "thread-001",
                "updated_at": "2026-04-10T03:05:00.000000+00:00",
            },
        ]


def test_archive_access_layer_reads_conversation_record() -> None:
    provider = _FakeRuntimeSessionHistoryProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)

    record = asyncio.run(layer.read_conversation_record("thread-999"))

    assert provider.last_thread_ref == "thread-999"
    assert provider.last_limit == 20
    assert record == ConversationRecord(
        conversation_ref="thread-999",
        runtime_thread_ref="thread-999",
        runtime_checkpoint_ref="cp-999",
        user_id="user-999",
        session_type="coaching",
        correlation_id="corr-999",
        started_at="2026-04-10T03:00:00.000000+00:00",
        updated_at="2026-04-10T03:00:06.000000+00:00",
        source="runtime_session_history",
        messages=[
            ConversationMessageRecord(
                message_ref="m-user-9",
                role="user",
                content="请记下这次对话。",
                author_name=None,
            ),
            ConversationMessageRecord(
                message_ref="m-ai-9",
                role="assistant",
                content="我会在需要时回看它。",
                author_name="coach",
            ),
        ],
    )


def test_archive_access_layer_lists_conversation_refs_for_user() -> None:
    provider = _FakeRuntimeSessionHistoryProvider()
    layer = ConversationArchiveAccessLayer(provider=provider)

    import asyncio

    refs = asyncio.run(layer.list_conversation_refs(user_id="user-999", limit=5))

    assert refs == ["thread-002", "thread-001"]
    assert provider.last_user_id == "user-999"
    assert provider.last_limit == 5


def test_archive_access_layer_wraps_runtime_provider_failure() -> None:
    class _FailingProvider(RuntimeSessionHistoryProvider):
        async def get_thread(self, thread_ref: str) -> dict:
            raise OSError("connection refused")

        async def get_history(self, thread_ref: str, *, limit: int) -> list[dict]:
            raise AssertionError("should not request history after thread failure")

        async def search_threads(self, *, user_id: str, limit: int) -> list[dict]:
            raise AssertionError("unused")

    layer = ConversationArchiveAccessLayer(provider=_FailingProvider())

    try:
        asyncio.run(layer.read_conversation_record("thread-err"))
    except ConversationArchiveAccessError as exc:
        assert str(exc) == "runtime session history is unavailable"
    else:
        raise AssertionError("runtime provider failure should be normalized")
