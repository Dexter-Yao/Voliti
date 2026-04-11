# ABOUTME: Conversation archive retrieval tool
# ABOUTME: 以统一 envelope 形式向 Coach 暴露原始会话检索能力

from __future__ import annotations

import os

from langchain_core.tools import tool
from langgraph.config import get_config

from voliti.conversation_archive import ConversationArchiveAccessError
from voliti.conversation_retrieval import (
    ARCHIVE_EVIDENCE_KIND,
    ARCHIVE_USAGE,
    ConversationRetrievalEngine,
)
from voliti.runtime_session_history_langgraph import (
    create_conversation_archive_access_layer,
)


def resolve_runtime_api_url() -> str:
    """解析运行时 API URL。

    优先使用供应商中立的 VOLITI_RUNTIME_API_URL。
    兼容已有本地测试入口 LANGGRAPH_API_URL。
    """
    if url := os.environ.get("VOLITI_RUNTIME_API_URL"):
        return url
    if url := os.environ.get("LANGGRAPH_API_URL"):
        return url
    return "http://127.0.0.1:2025"


def _resolve_user_id() -> str:
    configurable = get_config().get("configurable", {})
    user_id = configurable.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("configurable.user_id is required")
    return user_id


def _build_error_envelope(exc: Exception) -> dict:
    message = str(exc)
    if message == "configurable.user_id is required":
        return {
            "status": "error",
            "payload": None,
            "error_code": "conversation_archive_identity_unavailable",
            "coach_message": "Conversation archive retrieval requires a valid user identity.",
        }
    if message.startswith("unsupported ") or message == "conversation_ref is required for excerpt retrieval":
        return {
            "status": "error",
            "payload": None,
            "error_code": "conversation_archive_request_invalid",
            "coach_message": "Conversation archive retrieval request is invalid.",
        }
    if isinstance(exc, (ConversationArchiveAccessError, OSError)):
        return {
            "status": "error",
            "payload": None,
            "error_code": "conversation_archive_unavailable",
            "coach_message": "Conversation archive retrieval is temporarily unavailable.",
        }
    if message == "runtime session history is missing required metadata":
        return {
            "status": "error",
            "payload": None,
            "error_code": "conversation_archive_record_incomplete",
            "coach_message": "Conversation archive data is incomplete for this request.",
        }
    return {
        "status": "error",
        "payload": None,
        "error_code": "conversation_archive_retrieval_failed",
        "coach_message": "Conversation archive retrieval failed.",
    }


def _normalize_payload(payload: dict) -> dict:
    """补齐 retrieval payload 的稳定 evidence 语义。"""
    normalized = dict(payload)
    normalized.setdefault("evidence_kind", ARCHIVE_EVIDENCE_KIND)
    normalized.setdefault("usage", ARCHIVE_USAGE)
    return normalized


@tool
async def retrieve_conversation_archive(
    query: str,
    window: str = "recent",
    limit: int = 3,
    detail_level: str = "summary",
    conversation_ref: str | None = None,
    time_hint: str | None = None,
) -> dict:
    """Retrieve conversation archive records with summary-first semantics.

    Use this tool to look up past conversation details only when the current
    context is insufficient. Default to summary retrieval. Use excerpt mode only
    when a specific conversation_ref is already known.
    """
    try:
        archive = create_conversation_archive_access_layer(
            server_url=resolve_runtime_api_url()
        )
        engine = ConversationRetrievalEngine(archive=archive)
        payload = await engine.retrieve(
            user_id=_resolve_user_id(),
            query=query,
            window=window,
            limit=limit,
            detail_level=detail_level,
            conversation_ref=conversation_ref,
            time_hint=time_hint,
        )
        payload = _normalize_payload(payload)
        if detail_level == "summary":
            coach_message = f"找到 {len(payload.get('results', []))} 条相关会话摘要。"
        else:
            coach_message = "已读取指定会话片段。"
        return {
            "status": "ok",
            "payload": payload,
            "error_code": None,
            "coach_message": coach_message,
        }
    except Exception as exc:  # noqa: BLE001
        return _build_error_envelope(exc)
