# ABOUTME: Witness Card 生成工具
# ABOUTME: 生成里程碑见证卡片（缩略图进 A2UI payload，原图+元数据存 Store），interrupt() 暂停执行等待用户审阅

import base64
import hashlib
import io
import logging
import os
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from langgraph.types import interrupt
from PIL import Image

from voliti.a2ui import (
    A2UIPayload,
    A2UIResponse,
    ImageComponent,
    SelectComponent,
    SelectOption,
    TextComponent,
)

logger = logging.getLogger(__name__)

_CACHE_MAXSIZE = 32
_THUMB_MAX_WIDTH = 384
_THUMB_JPEG_QUALITY = 75

_card_cache: OrderedDict[str, tuple[str, str, str, str]] = OrderedDict()
"""模块级有界缓存，避免 resume 重执行时重复调用图片生成 API。

LangGraph 在 interrupt() 后 resume 时会从 node 起重新执行。
缓存确保同一 prompt 不会重复调用付费 API。
值为 (full_b64, full_mime, thumb_b64, thumb_mime) 元组。
超过 _CACHE_MAXSIZE 时 FIFO 淘汰。
"""

INTERVENTIONS_NAMESPACE = ("voliti", "user", "interventions")

CARD_STATUS_PENDING = "pending"
CARD_STATUS_ACCEPTED = "accepted"
CARD_STATUS_REJECTED = "rejected"

ACHIEVEMENT_EXPLICIT = "explicit"
ACHIEVEMENT_IMPLICIT = "implicit"
ACHIEVEMENT_JOURNEY = "journey"

# gpt-image-1.5 仅支持三种固定尺寸
_ASPECT_RATIO_TO_SIZE: dict[str, str] = {
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "1:1": "1024x1024",
    "16:9": "1536x1024",
    "9:16": "1024x1536",
}

_openai_client: "AzureOpenAI | None" = None


def _get_openai_client() -> "AzureOpenAI":
    """模块级 lazy init AzureOpenAI client，复用连接池。"""
    global _openai_client  # noqa: PLW0603
    if _openai_client is None:
        from openai import AzureOpenAI

        import httpx

        _openai_client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            api_version=os.environ.get(
                "AZURE_OPENAI_API_VERSION", "2025-03-01-preview"
            ),
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
            max_retries=2,
        )
    return _openai_client


def _make_thumbnail(png_b64: str) -> tuple[str, str]:
    """从高清 PNG base64 生成 JPEG 缩略图。

    缩放到最大宽度 _THUMB_MAX_WIDTH，保持宽高比。
    Returns: (thumb_b64, "image/jpeg")
    """
    raw = base64.b64decode(png_b64)
    img = Image.open(io.BytesIO(raw))

    ratio = _THUMB_MAX_WIDTH / img.width
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_THUMB_JPEG_QUALITY)
    thumb_b64 = base64.b64encode(buf.getvalue()).decode()
    return thumb_b64, "image/jpeg"


def _pre_store_card(
    *,
    store: BaseStore | None,
    card_id: str,
    image_data_url: str,
    narrative: str,
    achievement_type: str,
    achievement_title: str,
    chapter_id: str | None,
    linked_lifesign_id: str | None,
    user_quote: str | None,
) -> None:
    """在 interrupt 前将完整图片数据和元数据预写入 Store。

    status="pending"，等待用户审阅后 finalize 或删除。
    """
    if store is None:
        return
    store.put(
        INTERVENTIONS_NAMESPACE,
        card_id,
        {
            "imageData": image_data_url,
            "narrative": narrative,
            "achievement_type": achievement_type,
            "achievement_title": achievement_title,
            "chapter_id": chapter_id,
            "linked_lifesign_id": linked_lifesign_id,
            "user_quote": user_quote,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": CARD_STATUS_PENDING,
        },
    )


def _finalize_card(
    *,
    store: BaseStore | None,
    card_id: str,
    accepted: bool,
) -> None:
    """用户审阅后更新 Store 中 card 的状态。

    accepted=True → status="accepted"；False → status="rejected"。
    """
    if store is None:
        return
    item = store.get(INTERVENTIONS_NAMESPACE, card_id)
    if item is not None:
        status = CARD_STATUS_ACCEPTED if accepted else CARD_STATUS_REJECTED
        store.put(INTERVENTIONS_NAMESPACE, card_id, {**item.value, "status": status})


def _generate_image(prompt: str, size: str) -> tuple[str, str]:
    """调用 Azure OpenAI gpt-image-1.5 生成图片。

    Returns: (base64_data, mime_type) 元组。
    Raises: 各类 API 异常由调用方捕获处理。
    """
    client = _get_openai_client()

    response = client.images.generate(
        model="gpt-image-1.5",
        prompt=prompt,
        n=1,
        size=size,
        quality="high",
        output_format="png",
    )

    b64_data = response.data[0].b64_json
    if not b64_data:
        msg = "gpt-image-1.5 未返回图片数据"
        raise ValueError(msg)

    return b64_data, "image/png"


@tool
def compose_witness_card(
    prompt: str,
    narrative: str = "",
    achievement_title: str = "",
    achievement_type: str = "explicit",
    aspect_ratio: str = "3:4",
    chapter_id: str = "",
    linked_lifesign_id: str = "",
    user_quote: str = "",
    store: Annotated[BaseStore | None, InjectedStore()] = None,
) -> str:
    """Generate a Witness Card and present it for user review.

    Witness Cards commemorate user milestones with a brand-consistent visual
    and personalized narrative text. The image contains no text overlay;
    narrative text is displayed in the card frame's independent area.

    Args:
        prompt: Full image generation prompt, assembled by Witness Card Composer.
        narrative: Coach-voice narrative text for the card's text area.
        achievement_title: Short milestone description (e.g., "第一个 Chapter 完成").
        achievement_type: "explicit" (user reported), "implicit" (Coach discovered), "journey" (journey node).
        aspect_ratio: Aspect ratio, e.g. "3:4", "1:1", "4:3".
        chapter_id: Current Chapter ID if applicable.
        linked_lifesign_id: Related LifeSign ID if applicable.
        user_quote: User's own words related to this achievement.
    """
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()

    if cache_key not in _card_cache:
        size = _ASPECT_RATIO_TO_SIZE.get(aspect_ratio, "1024x1536")
        try:
            full_b64, full_mime = _generate_image(prompt, size)
        except Exception as exc:
            logger.warning("Witness Card image generation failed: %s", exc)
            return (
                f"Image generation failed ({type(exc).__name__}). "
                "Continue the conversation without a Witness Card. "
                "You may acknowledge the milestone verbally instead."
            )
        thumb_b64, thumb_mime = _make_thumbnail(full_b64)
        _card_cache[cache_key] = (full_b64, full_mime, thumb_b64, thumb_mime)
        if len(_card_cache) > _CACHE_MAXSIZE:
            _card_cache.popitem(last=False)

    cached_full_b64, cached_full_mime, cached_thumb_b64, cached_thumb_mime = (
        _card_cache[cache_key]
    )

    card_id = f"card_{cache_key[:8]}"

    try:
        _pre_store_card(
            store=store,
            card_id=card_id,
            image_data_url=f"data:{cached_full_mime};base64,{cached_full_b64}",
            narrative=narrative,
            achievement_type=achievement_type,
            achievement_title=achievement_title,
            chapter_id=chapter_id or None,
            linked_lifesign_id=linked_lifesign_id or None,
            user_quote=user_quote or None,
        )
    except Exception as exc:
        logger.warning("Witness Card Store write failed: %s", exc)
        return (
            f"Card storage failed ({type(exc).__name__}). "
            "Continue the conversation without a Witness Card."
        )

    card_metadata: dict[str, str] = {
        "card_id": card_id,
        "achievement_type": achievement_type,
    }
    if linked_lifesign_id:
        card_metadata["linked_lifesign_id"] = linked_lifesign_id
    if chapter_id:
        card_metadata["chapter_id"] = chapter_id
    if user_quote:
        card_metadata["user_quote"] = user_quote

    payload = A2UIPayload(
        components=[
            ImageComponent(
                src=f"data:{cached_thumb_mime};base64,{cached_thumb_b64}",
                alt=achievement_title,
            ),
            TextComponent(text=narrative),
            SelectComponent(
                key="decision",
                label="",
                options=[
                    SelectOption(label="收下", value="accept"),
                    SelectOption(label="跳过", value="dismiss"),
                ],
            ),
        ],
        layout="full",
        metadata=card_metadata,
    )
    raw_response = interrupt(payload.model_dump())
    ui_response = A2UIResponse.model_validate(raw_response)

    if ui_response.action == "reject":
        _finalize_card(store=store, card_id=card_id, accepted=False)
        _card_cache.pop(cache_key, None)
        return f"User closed the Witness Card panel without reviewing ({achievement_title})."

    accepted = ui_response.data.get("decision") == "accept"
    _finalize_card(store=store, card_id=card_id, accepted=accepted)
    _card_cache.pop(cache_key, None)

    if accepted:
        return f"User accepted the Witness Card ({achievement_title}). Card saved as {card_id}."
    return f"User reviewed and dismissed the Witness Card ({achievement_title})."
