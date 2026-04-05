# ABOUTME: 体验式干预工具
# ABOUTME: 生成干预图片（缩略图进 A2UI payload，原图存 Store），interrupt() 暂停执行等待用户审阅

import base64
import hashlib
import io
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

_CACHE_MAXSIZE = 32
_THUMB_MAX_WIDTH = 384
_THUMB_JPEG_QUALITY = 75

_intervention_cache: OrderedDict[str, tuple[str, str, str, str]] = OrderedDict()
"""模块级有界缓存，避免 resume 重执行时重复调用图片生成 API。

LangGraph 在 interrupt() 后 resume 时会从 node 起重新执行。
缓存确保同一 prompt 不会重复调用付费 API。
值为 (full_b64, full_mime, thumb_b64, thumb_mime) 元组。
超过 _CACHE_MAXSIZE 时 FIFO 淘汰。
"""

INTERVENTIONS_NAMESPACE = ("voliti", "user", "interventions")

# gpt-image-1.5 仅支持三种固定尺寸
_ASPECT_RATIO_TO_SIZE: dict[str, str] = {
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "1:1": "1024x1024",
    "16:9": "1536x1024",  # fallback 到最近横版
    "9:16": "1024x1536",  # fallback 到最近竖版
}


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
    caption: str,
    purpose: str,
) -> None:
    """在 interrupt 前将完整图片数据预写入 Store。

    status="pending"，等待用户审阅后 finalize 或删除。
    """
    if store is None:
        return
    store.put(
        INTERVENTIONS_NAMESPACE,
        card_id,
        {
            "imageData": image_data_url,
            "caption": caption,
            "purpose": purpose,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        },
    )


def _finalize_card(
    *,
    store: BaseStore | None,
    card_id: str,
    accepted: bool,
) -> None:
    """用户审阅后更新 Store 中 card 的状态。

    accepted=True → status="accepted"；False → 删除预写入的 card。
    """
    if store is None:
        return
    if accepted:
        item = store.get(INTERVENTIONS_NAMESPACE, card_id)
        if item is not None:
            value = {**item.value, "status": "accepted"}
            store.put(INTERVENTIONS_NAMESPACE, card_id, value)
    else:
        store.delete(INTERVENTIONS_NAMESPACE, card_id)


def _generate_image(prompt: str, size: str) -> tuple[str, str]:
    """调用 Azure OpenAI gpt-image-1.5 生成图片。

    Returns: (base64_data, mime_type) 元组。
    """
    from openai import AzureOpenAI

    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        api_version="2024-02-01",
    )

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
        raise ValueError("gpt-image-1.5 未返回图片数据")

    return b64_data, "image/png"


@tool
def compose_experiential_intervention(
    prompt: str,
    aspect_ratio: str = "3:4",
    purpose: str = "",
    caption: str = "",
    store: Annotated[BaseStore | None, InjectedStore()] = None,
) -> str:
    """Generate experiential intervention content and present it for user review.

    Based on research theories (Future Self-Continuity, MCII/WOOP, Conceptual Metaphor, CBT),
    translates coaching insights into felt experiences.

    Args:
        prompt: Full generation prompt, assembled by Intervention Composer.
        aspect_ratio: Aspect ratio, e.g. "3:4", "1:1", "4:3".
        purpose: Intervention type identifier, e.g. "future_self", "scene_rehearsal".
        caption: Coach-voice narrative conveying the intervention intent.
    """
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()

    if cache_key not in _intervention_cache:
        size = _ASPECT_RATIO_TO_SIZE.get(aspect_ratio, "1024x1536")
        full_b64, full_mime = _generate_image(prompt, size)
        thumb_b64, thumb_mime = _make_thumbnail(full_b64)
        _intervention_cache[cache_key] = (full_b64, full_mime, thumb_b64, thumb_mime)
        if len(_intervention_cache) > _CACHE_MAXSIZE:
            _intervention_cache.popitem(last=False)

    cached_full_b64, cached_full_mime, cached_thumb_b64, cached_thumb_mime = _intervention_cache[cache_key]

    # 预生成 card_id，写入 Store（status=pending）
    card_id = f"card_{uuid.uuid4().hex[:8]}"
    _pre_store_card(
        store=store,
        card_id=card_id,
        image_data_url=f"data:{cached_full_mime};base64,{cached_full_b64}",
        caption=caption,
        purpose=purpose,
    )

    # A2UI payload：缩略图 + 交互组件 + card_id 引用
    payload = A2UIPayload(
        components=[
            ImageComponent(src=f"data:{cached_thumb_mime};base64,{cached_thumb_b64}", alt=purpose),
            TextComponent(content=caption),
            SelectComponent(
                name="decision",
                label="",
                options=[
                    SelectOption(label="Accept", value="accept"),
                    SelectOption(label="Dismiss", value="dismiss"),
                ],
            ),
        ],
        layout="full",
        metadata={"card_id": card_id},
    )
    raw_response = interrupt(payload.model_dump())
    ui_response = A2UIResponse.model_validate(raw_response)

    if ui_response.action == "reject":
        _finalize_card(store=store, card_id=card_id, accepted=False)
        _intervention_cache.pop(cache_key, None)
        return f"User closed the intervention panel without reviewing ({purpose})."

    accepted = ui_response.data.get("decision") == "accept"
    _finalize_card(store=store, card_id=card_id, accepted=accepted)
    _intervention_cache.pop(cache_key, None)

    if accepted:
        return f"User accepted the intervention ({purpose}). Card saved as {card_id}."
    return f"User reviewed and dismissed the intervention ({purpose})."
