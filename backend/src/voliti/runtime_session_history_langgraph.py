# ABOUTME: LangGraph Runtime Session History 适配层
# ABOUTME: 将 LangGraph threads API 适配为供应商中立的 RuntimeSessionHistoryProvider 接口

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from voliti.conversation_archive import ConversationArchiveAccessLayer


@dataclass(frozen=True)
class LangGraphRuntimeSessionHistoryProvider:
    """基于 LangGraph threads API 的运行时会话读取适配层。"""

    client: Any

    async def get_thread(self, thread_ref: str) -> dict[str, Any]:
        return await self.client.threads.get(thread_ref)

    async def get_history(self, thread_ref: str, *, limit: int) -> list[dict[str, Any]]:
        return await self.client.threads.get_history(thread_ref, limit=limit)

    async def search_threads(self, *, user_id: str, limit: int) -> list[dict[str, Any]]:
        return await self.client.threads.search(metadata={"user_id": user_id}, limit=limit)


def create_conversation_archive_access_layer(*, server_url: str) -> ConversationArchiveAccessLayer:
    """创建基于 LangGraph SDK 的 Conversation Archive Access Layer。"""
    from langgraph_sdk import get_client

    client = get_client(url=server_url)
    provider = LangGraphRuntimeSessionHistoryProvider(client=client)
    return ConversationArchiveAccessLayer(provider=provider)
