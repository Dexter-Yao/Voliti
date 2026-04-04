# ABOUTME: LangGraph SDK 交互封装
# ABOUTME: 管理线程生命周期、流式消息处理、A2UI interrupt 检测与 resume

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langgraph_sdk import get_client
from langgraph_sdk.client import LangGraphClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Coach 事件类型（tagged union）
# ---------------------------------------------------------------------------


@dataclass
class TextEvent:
    """Coach 的文本消息。"""

    text: str


@dataclass
class A2UIInterruptEvent:
    """A2UI interrupt — Coach 请求用户通过 UI 组件交互。"""

    payload: dict[str, Any]  # A2UIPayload dict: {type, components, layout}
    images: list[dict[str, Any]] = field(default_factory=list)  # 提取的 ImageComponent


CoachEvent = TextEvent | A2UIInterruptEvent


# ---------------------------------------------------------------------------
# CoachClient
# ---------------------------------------------------------------------------


class CoachClient:
    """与 Coach Agent 通信的 LangGraph SDK 客户端。"""

    def __init__(self, server_url: str, assistant_id: str = "coach") -> None:
        self._client: LangGraphClient = get_client(url=server_url)
        self._assistant_id = assistant_id

    async def create_thread(self) -> str:
        """创建新对话线程，返回 thread_id。"""
        thread = await self._client.threads.create()
        thread_id = thread["thread_id"]
        logger.info("Created thread: %s", thread_id)
        return thread_id

    async def send_message(self, thread_id: str, message: str) -> list[CoachEvent]:
        """发送用户消息并流式收集 Coach 响应。

        返回本轮所有 CoachEvent（文本消息和/或 A2UI interrupt）。
        """
        input_data = {"messages": [{"role": "human", "content": message}]}
        return await self._stream_and_collect(thread_id, input_data=input_data)

    async def resume_interrupt(
        self, thread_id: str, response: dict[str, Any]
    ) -> list[CoachEvent]:
        """以 A2UIResponse 恢复 interrupt，继续流式收集。"""
        from langgraph_sdk.schema import Command

        command = Command(resume=response)
        return await self._stream_and_collect(thread_id, command=command)

    @property
    def store(self):
        """暴露底层 store 客户端供 store.py 使用。"""
        return self._client.store

    async def _stream_and_collect(
        self,
        thread_id: str,
        input_data: dict[str, Any] | None = None,
        command: Any | None = None,
    ) -> list[CoachEvent]:
        """流式处理 Coach 响应，提取文本和 interrupt 事件。"""
        events: list[CoachEvent] = []
        collected_text_parts: list[str] = []

        kwargs: dict[str, Any] = {
            "thread_id": thread_id,
            "assistant_id": self._assistant_id,
            "stream_mode": ["updates", "values"],
            "stream_subgraphs": True,
        }
        if input_data is not None:
            kwargs["input"] = input_data
        if command is not None:
            kwargs["command"] = command

        async for chunk in self._client.runs.stream(**kwargs):
            logger.debug("Stream chunk: event=%s", chunk.event)

            # 检测 interrupt（A2UI）
            if chunk.event == "values" and isinstance(chunk.data, dict):
                interrupts = chunk.data.get("__interrupt__")
                if interrupts:
                    # 先 flush 累积的文本
                    if collected_text_parts:
                        events.append(TextEvent(text="\n".join(collected_text_parts)))
                        collected_text_parts.clear()

                    for interrupt in interrupts:
                        value = interrupt.get("value", interrupt)
                        if isinstance(value, dict) and value.get("type") == "a2ui":
                            images = _extract_images(value)
                            events.append(A2UIInterruptEvent(payload=value, images=images))
                            logger.info("A2UI interrupt detected: %d components", len(value.get("components", [])))
                        else:
                            logger.warning("Non-A2UI interrupt: %s", type(value))
                    continue

            # 提取 AI 文本消息
            if chunk.event == "updates" and isinstance(chunk.data, dict):
                for node_data in chunk.data.values():
                    if not isinstance(node_data, dict):
                        continue
                    messages = node_data.get("messages", [])
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get("type") == "ai":
                            content = msg.get("content", "")
                            if isinstance(content, str) and content.strip():
                                collected_text_parts.append(content.strip())

        # flush 剩余文本
        if collected_text_parts:
            events.append(TextEvent(text="\n".join(collected_text_parts)))

        return events


def _extract_images(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """从 A2UIPayload 中提取 ImageComponent。"""
    images = []
    for comp in payload.get("components", []):
        if comp.get("kind") == "image":
            images.append({
                "src": comp.get("src", ""),
                "alt": comp.get("alt", ""),
            })
    return images
