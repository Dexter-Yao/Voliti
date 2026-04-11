# ABOUTME: LangGraph SDK 交互封装
# ABOUTME: 管理线程生命周期、流式消息处理、A2UI interrupt 检测与 resume

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
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


def decorate_interrupt_payload(payload: dict[str, Any], interrupt: dict[str, Any]) -> dict[str, Any]:
    """将 LangGraph interrupt 元信息合并进 A2UI payload。"""
    decorated = dict(payload)
    metadata = dict(payload.get("metadata", {}))
    interrupt_id = interrupt.get("id")
    if isinstance(interrupt_id, str) and interrupt_id:
        metadata["interrupt_id"] = interrupt_id
    if metadata:
        decorated["metadata"] = metadata
    return decorated


def build_client_timeout(turn_timeout_seconds: int) -> httpx.Timeout:
    """构造 LangGraph 客户端超时配置。

    连接与连接池等待保持短超时，流式读取与写入使用评估配置。
    """
    return httpx.Timeout(
        connect=5,
        read=turn_timeout_seconds,
        write=turn_timeout_seconds,
        pool=5,
    )


def _text_from_content(content: Any) -> str:
    """从 AI 消息的 content 字段提取纯文本。

    LangChain AIMessage 的 content 取决于模型供应商：
    - str: OpenAI chat completions 标准格式
    - list[dict]: Anthropic 或 OpenAI reasoning 模型的 content blocks
      例 [{"type": "text", "text": "..."}, {"type": "tool_use", ...}]
    - None: 纯 tool call 中间态
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
            elif isinstance(block, str) and block.strip():
                parts.append(block.strip())
        return "\n".join(parts)
    return ""


# ---------------------------------------------------------------------------
# CoachClient
# ---------------------------------------------------------------------------


class CoachClient:
    """与 Coach Agent 通信的 LangGraph SDK 客户端。"""

    def __init__(
        self,
        server_url: str,
        assistant_id: str,
        turn_timeout_seconds: int,
    ) -> None:
        self._client: LangGraphClient = get_client(
            url=server_url,
            timeout=build_client_timeout(turn_timeout_seconds),
        )
        self._assistant_id = assistant_id
        self._user_id: str | None = None
        self._session_type: str = "coaching"

    def with_user_id(self, user_id: str) -> "CoachClient":
        """设置当前会话的 user_id，用于 Store namespace 隔离。"""
        self._user_id = user_id
        return self

    def with_session_type(self, session_type: str) -> "CoachClient":
        """设置 session_type（coaching / onboarding）。"""
        self._session_type = session_type
        return self

    async def create_thread(self) -> str:
        """创建新对话线程，返回 thread_id。"""
        metadata: dict[str, Any] = {"session_type": self._session_type}
        if self._user_id:
            metadata["user_id"] = self._user_id
        thread = await self._client.threads.create(metadata=metadata)
        thread_id = thread["thread_id"]
        logger.info("Created thread: %s", thread_id)
        return thread_id

    async def send_message(self, thread_id: str, message: str) -> list[CoachEvent]:
        """发送用户消息并流式收集 Coach 响应。"""
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

    def _build_config(self) -> dict[str, Any] | None:
        """构造 run config，注入 user_id 和 session_type。"""
        configurable: dict[str, Any] = {"session_type": self._session_type}
        if self._user_id:
            configurable["user_id"] = self._user_id
        return {"configurable": configurable} if configurable else None

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

        config = self._build_config()
        if config is not None:
            kwargs["config"] = config

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
                            payload = decorate_interrupt_payload(value, interrupt)
                            images = _extract_images(payload)
                            events.append(A2UIInterruptEvent(payload=payload, images=images))
                            logger.info("A2UI interrupt detected: %d components", len(payload.get("components", [])))
                        else:
                            logger.warning("Non-A2UI interrupt: %s", type(value))
                    continue

            # 提取 AI 文本消息
            if chunk.event == "updates" and isinstance(chunk.data, dict):
                for node_name, node_data in chunk.data.items():
                    if not isinstance(node_data, dict):
                        continue
                    messages = node_data.get("messages", [])
                    for msg in messages:
                        if not isinstance(msg, dict) or msg.get("type") != "ai":
                            continue
                        content = msg.get("content")
                        tool_calls = msg.get("tool_calls", [])
                        text = _text_from_content(content)
                        if text:
                            collected_text_parts.append(text)
                        if tool_calls:
                            names = [tc.get("name", "?") for tc in tool_calls if isinstance(tc, dict)]
                            logger.debug("AI tool_calls from %s: %s", node_name, names)
                        if not text and not tool_calls:
                            logger.debug("AI message from %s: empty content (type=%s)", node_name, type(content).__name__)

        # flush 剩余文本
        if collected_text_parts:
            events.append(TextEvent(text="\n".join(collected_text_parts)))

        return events


def _extract_images(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """从 A2UIPayload 中提取 ImageComponent 信息。

    保留缩略图 base64 data URL（~50KB，用于 eval 报告渲染）。
    同时提取 payload.metadata 中的 card_id（如果存在）。
    """
    card_id = payload.get("metadata", {}).get("card_id", "")
    images = []
    for comp in payload.get("components", []):
        if comp.get("kind") == "image":
            images.append({
                "src": comp.get("src", ""),
                "alt": comp.get("alt", ""),
                "card_id": card_id,
            })
    return images
