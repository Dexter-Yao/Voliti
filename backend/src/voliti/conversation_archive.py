# ABOUTME: Conversation archive access layer 的稳定读模型
# ABOUTME: 将运行时 session history 规范化为供应商中立的 conversation record

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


class ConversationArchiveAccessError(RuntimeError):
    """Conversation Archive Access Layer 的稳定失败类型。"""


@dataclass(frozen=True)
class ConversationMessageRecord:
    """稳定的对话消息视图。"""

    message_ref: str
    role: str
    content: str
    author_name: str | None = None


@dataclass(frozen=True)
class ConversationRecord:
    """稳定的对话归档视图。"""

    conversation_ref: str
    runtime_thread_ref: str
    runtime_checkpoint_ref: str | None
    user_id: str
    session_type: str
    correlation_id: str | None
    started_at: str | None
    updated_at: str | None
    source: str
    messages: list[ConversationMessageRecord]


class RuntimeSessionHistoryProvider(Protocol):
    """运行时原始会话读取接口。"""

    async def get_thread(self, thread_ref: str) -> dict[str, Any]: ...

    async def get_history(self, thread_ref: str, *, limit: int) -> list[dict[str, Any]]: ...

    async def search_threads(self, *, user_id: str, limit: int) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class ConversationArchiveAccessLayer:
    """对运行时原始会话提供稳定读取语义。"""

    provider: RuntimeSessionHistoryProvider
    default_history_limit: int = 20

    async def read_conversation_record(self, conversation_ref: str) -> ConversationRecord:
        try:
            thread = await self.provider.get_thread(conversation_ref)
            history = await self.provider.get_history(
                conversation_ref,
                limit=self.default_history_limit,
            )
        except ConversationArchiveAccessError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConversationArchiveAccessError(
                "runtime session history is unavailable"
            ) from exc
        return normalize_conversation_record(thread=thread, history=history)

    async def list_conversation_refs(self, *, user_id: str, limit: int = 10) -> list[str]:
        try:
            threads = await self.provider.search_threads(user_id=user_id, limit=limit)
        except ConversationArchiveAccessError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConversationArchiveAccessError(
                "runtime session history is unavailable"
            ) from exc
        refs: list[str] = []
        for thread in threads:
            thread_ref = _optional_str(thread, "thread_id")
            if thread_ref:
                refs.append(thread_ref)
        return refs


def normalize_conversation_record(
    *,
    thread: Mapping[str, Any],
    history: list[Mapping[str, Any]],
) -> ConversationRecord:
    """将运行时 session history 规范化为稳定的 conversation record。"""
    metadata = thread.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("runtime session history is missing required metadata")

    user_id = metadata.get("user_id")
    session_type = metadata.get("session_mode")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("runtime session history is missing required metadata")
    if not isinstance(session_type, str) or not session_type:
        raise ValueError("runtime session history is missing required metadata")

    thread_ref = _require_str(thread, "thread_id")
    latest_state = _select_latest_message_state(thread=thread, history=history)
    raw_messages = _extract_messages(latest_state)

    return ConversationRecord(
        conversation_ref=thread_ref,
        runtime_thread_ref=thread_ref,
        runtime_checkpoint_ref=_extract_checkpoint_ref(latest_state),
        user_id=user_id,
        session_type=session_type,
        correlation_id=_optional_str(metadata, "correlation_id"),
        started_at=_optional_str(thread, "created_at"),
        updated_at=_optional_str(thread, "updated_at") or _optional_str(latest_state, "created_at"),
        source="runtime_session_history",
        messages=_normalize_messages(raw_messages),
    )


def _select_latest_message_state(
    *,
    thread: Mapping[str, Any],
    history: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    states_with_messages: list[tuple[str, Mapping[str, Any]]] = []
    for state in history:
        messages = _extract_messages(state)
        if messages:
            created_at = _optional_str(state, "created_at") or ""
            states_with_messages.append((created_at, state))

    if states_with_messages:
        states_with_messages.sort(key=lambda item: item[0])
        return states_with_messages[-1][1]

    thread_values = thread.get("values")
    if isinstance(thread_values, Mapping):
        return {"values": thread_values}

    return {}


def _extract_messages(state: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    values = state.get("values")
    if not isinstance(values, Mapping):
        return []

    messages = values.get("messages")
    if not isinstance(messages, list):
        return []

    return [message for message in messages if isinstance(message, Mapping)]


def _normalize_messages(raw_messages: list[Mapping[str, Any]]) -> list[ConversationMessageRecord]:
    normalized: list[ConversationMessageRecord] = []
    seen_refs: set[str] = set()

    for message in raw_messages:
        message_ref = _optional_str(message, "id")
        role = _map_role(_optional_str(message, "type"))
        content = _coerce_content(message.get("content"))
        if message_ref is None or role is None or not content or message_ref in seen_refs:
            continue

        seen_refs.add(message_ref)
        normalized.append(
            ConversationMessageRecord(
                message_ref=message_ref,
                role=role,
                content=content,
                author_name=_optional_str(message, "name"),
            )
        )

    return normalized


def _map_role(raw_role: str | None) -> str | None:
    if raw_role == "human":
        return "user"
    if raw_role == "ai":
        return "assistant"
    return None


def _coerce_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        text_parts: list[str] = []
        for block in value:
            if isinstance(block, Mapping) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
        return "\n".join(text_parts)
    return ""


def _extract_checkpoint_ref(state: Mapping[str, Any]) -> str | None:
    checkpoint = state.get("checkpoint")
    if isinstance(checkpoint, Mapping):
        checkpoint_id = checkpoint.get("checkpoint_id")
        if isinstance(checkpoint_id, str) and checkpoint_id:
            return checkpoint_id
    return None


def _require_str(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required field: {key}")
    return value


def _optional_str(mapping: Mapping[str, Any], key: str) -> str | None:
    value = mapping.get(key)
    if isinstance(value, str) and value:
        return value
    return None
