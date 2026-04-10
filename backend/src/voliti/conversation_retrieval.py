# ABOUTME: Conversation retrieval engine
# ABOUTME: 基于 Conversation Archive Access Layer 提供摘要优先、显式 excerpt 的单一检索语义

from __future__ import annotations

from dataclasses import dataclass

from voliti.conversation_archive import ConversationArchiveAccessLayer, ConversationRecord


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
        del window, time_hint

        if detail_level == "excerpt":
            if not conversation_ref:
                raise ValueError("conversation_ref is required for excerpt retrieval")
            record = await self.archive.read_conversation_record(conversation_ref)
            return {
                "detail_level": "excerpt",
                "conversation_ref": conversation_ref,
                "excerpt": [
                    {
                        "message_ref": message.message_ref,
                        "role": message.role,
                        "content": message.content,
                    }
                    for message in record.messages
                ],
            }

        refs = await self.archive.list_conversation_refs(user_id=user_id, limit=limit)
        records = [await self.archive.read_conversation_record(ref) for ref in refs]
        summaries = [
            self._build_summary(record, query)
            for record in records
            if self._matches_query(record, query)
        ]

        return {
            "detail_level": "summary",
            "results": summaries[:limit],
        }

    def _matches_query(self, record: ConversationRecord, query: str) -> bool:
        if not query.strip():
            return True
        return query in " ".join(message.content for message in record.messages)

    def _build_summary(self, record: ConversationRecord, query: str) -> dict:
        user_text = next((message.content for message in record.messages if message.role == "user"), "")
        assistant_text = next((message.content for message in record.messages if message.role == "assistant"), "")
        summary = " / ".join(part for part in [user_text, assistant_text] if part)
        return {
            "conversation_ref": record.conversation_ref,
            "session_type": record.session_type,
            "updated_at": record.updated_at,
            "summary": summary if query.strip() else summary,
        }
