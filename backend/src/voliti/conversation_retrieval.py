# ABOUTME: Conversation retrieval engine
# ABOUTME: 基于 Conversation Archive Access Layer 提供摘要优先、显式 excerpt 的单一检索语义

from __future__ import annotations

from dataclasses import dataclass

from voliti.conversation_archive import (
    ConversationArchiveAccessLayer,
    ConversationMessageRecord,
    ConversationRecord,
)

EXCERPT_MESSAGE_LIMIT = 4
ARCHIVE_EVIDENCE_KIND = "archive_source"
ARCHIVE_USAGE = "runtime_evidence"


@dataclass(frozen=True)
class ConversationRetrievalEngine:
    """基于归档读取层的检索引擎。"""

    archive: ConversationArchiveAccessLayer

    async def retrieve(
        self,
        *,
        user_id: str,
        query: str,
        window: str,
        limit: int,
        detail_level: str,
        conversation_ref: str | None = None,
        time_hint: str | None = None,
    ) -> dict:
        if detail_level not in {"summary", "excerpt"}:
            raise ValueError(f"unsupported detail_level: {detail_level}")
        if window not in {"recent", "all"}:
            raise ValueError(f"unsupported window: {window}")

        if detail_level == "excerpt":
            if not conversation_ref:
                raise ValueError("conversation_ref is required for excerpt retrieval")
            record = await self.archive.read_conversation_record(conversation_ref)
            return {
                "detail_level": "excerpt",
                "evidence_kind": ARCHIVE_EVIDENCE_KIND,
                "usage": ARCHIVE_USAGE,
                "conversation_ref": conversation_ref,
                "source": record.source,
                "excerpt": [
                    {
                        "message_ref": message.message_ref,
                        "role": message.role,
                        "content": message.content,
                    }
                    for message in self._slice_excerpt(record.messages, query)
                ],
            }

        scan_limit = limit if window == "recent" else max(limit, 50)
        refs = await self.archive.list_conversation_refs(user_id=user_id, limit=scan_limit)
        records = [await self.archive.read_conversation_record(ref) for ref in refs]
        summaries = [
            self._build_summary(record, query)
            for record in records
            if self._matches_query(record, query) and self._matches_time_hint(record, time_hint)
        ]
        summaries.sort(key=lambda item: item.get("updated_at") or "", reverse=True)

        return {
            "detail_level": "summary",
            "evidence_kind": ARCHIVE_EVIDENCE_KIND,
            "usage": ARCHIVE_USAGE,
            "results": summaries[:limit],
        }

    def _matches_query(self, record: ConversationRecord, query: str) -> bool:
        if not query.strip():
            return True
        return query in " ".join(message.content for message in record.messages)

    def _matches_time_hint(self, record: ConversationRecord, time_hint: str | None) -> bool:
        if not time_hint:
            return True
        for value in (record.started_at, record.updated_at):
            if value and time_hint in value:
                return True
        return False

    def _build_summary(self, record: ConversationRecord, query: str) -> dict:
        summary_messages = self._slice_excerpt(record.messages, query) if query.strip() else record.messages
        user_text, assistant_text = self._select_summary_pair(summary_messages, query)
        summary = " / ".join(part for part in [user_text, assistant_text] if part)
        return {
            "conversation_ref": record.conversation_ref,
            "session_type": record.session_type,
            "updated_at": record.updated_at,
            "source": record.source,
            "summary": summary if query.strip() else summary,
        }

    def _select_summary_pair(
        self,
        messages: list[ConversationMessageRecord],
        query: str,
    ) -> tuple[str, str]:
        if not messages:
            return "", ""

        if query.strip():
            for index, message in enumerate(messages):
                if query in message.content:
                    if message.role == "user":
                        return message.content, self._find_adjacent_content(messages, index, "assistant")
                    if message.role == "assistant":
                        return self._find_adjacent_content(messages, index, "user"), message.content

        user_text = next((message.content for message in messages if message.role == "user"), "")
        assistant_text = next((message.content for message in messages if message.role == "assistant"), "")
        return user_text, assistant_text

    def _find_adjacent_content(
        self,
        messages: list[ConversationMessageRecord],
        index: int,
        role: str,
    ) -> str:
        for offset in range(1, len(messages)):
            before = index - offset
            if before >= 0 and messages[before].role == role:
                return messages[before].content
            after = index + offset
            if after < len(messages) and messages[after].role == role:
                return messages[after].content
        return ""

    def _slice_excerpt(
        self,
        messages: list[ConversationMessageRecord],
        query: str,
    ) -> list[ConversationMessageRecord]:
        if not messages:
            return []

        if not query.strip():
            return messages[:EXCERPT_MESSAGE_LIMIT]

        for index, message in enumerate(messages):
            if query in message.content:
                start = max(index - 1, 0)
                end = min(index + 2, len(messages))
                while end - start < min(EXCERPT_MESSAGE_LIMIT, len(messages)):
                    if start > 0:
                        start -= 1
                    elif end < len(messages):
                        end += 1
                    else:
                        break
                return messages[start:end]

        return messages[:EXCERPT_MESSAGE_LIMIT]
