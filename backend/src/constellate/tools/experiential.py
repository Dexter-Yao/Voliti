# ABOUTME: 体验式干预工具
# ABOUTME: 调用 Azure OpenAI gpt-image-1.5 生成图片，interrupt() 暂停执行等待用户审阅

import base64
import hashlib
import os
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from langgraph.types import interrupt

from constellate.a2ui import (
    A2UIPayload,
    A2UIResponse,
    ImageComponent,
    SelectComponent,
    SelectOption,
    TextComponent,
)

_CACHE_MAXSIZE = 32

_intervention_cache: OrderedDict[str, tuple[str, str]] = OrderedDict()
"""模块级有界缓存，避免 resume 重执行时重复调用图片生成 API。

LangGraph 在 interrupt() 后 resume 时会从 node 起重新执行。
缓存确保同一 prompt 不会重复调用付费 API。
值为 (base64_data, mime_type) 元组。超过 _CACHE_MAXSIZE 时 FIFO 淘汰。
"""

INTERVENTIONS_NAMESPACE = ("constellate", "user", "interventions")

# gpt-image-1.5 仅支持三种固定尺寸
_ASPECT_RATIO_TO_SIZE: dict[str, str] = {
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "1:1": "1024x1024",
    "16:9": "1536x1024",  # fallback 到最近横版
    "9:16": "1024x1536",  # fallback 到最近竖版
}


def _persist_card(
    *,
    store: BaseStore | None,
    image_data_url: str,
    caption: str,
    purpose: str,
) -> str | None:
    """将干预卡片持久化到 Store。

    Args:
        store: LangGraph Store 实例。为 None 时跳过持久化。
        image_data_url: Base64 data URL 格式的图片数据。
        caption: Coach 文案。
        purpose: 干预类型标识。

    Returns:
        卡片 ID，或 None（store 不可用时）。
    """
    if store is None:
        return None

    card_id = f"card_{uuid.uuid4().hex[:8]}"
    store.put(
        INTERVENTIONS_NAMESPACE,
        card_id,
        {
            "imageUrl": image_data_url,
            "caption": caption,
            "purpose": purpose,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    return card_id


def _generate_image(prompt: str, size: str) -> tuple[str, str]:
    """调用 Azure OpenAI gpt-image-1.5 生成图片。

    Args:
        prompt: 完整的图片生成 prompt。
        size: 图片尺寸，如 "1024x1536"。

    Returns:
        (base64_data, mime_type) 元组。
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
        b64_data, mime_type = _generate_image(prompt, size)
        _intervention_cache[cache_key] = (b64_data, mime_type)
        if len(_intervention_cache) > _CACHE_MAXSIZE:
            _intervention_cache.popitem(last=False)

    cached_b64, cached_mime = _intervention_cache[cache_key]

    payload = A2UIPayload(
        components=[
            ImageComponent(src=f"data:{cached_mime};base64,{cached_b64}", alt=purpose),
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
    )
    raw_response = interrupt(payload.model_dump())
    ui_response = A2UIResponse.model_validate(raw_response)

    if ui_response.action == "reject":
        _intervention_cache.pop(cache_key, None)
        return f"User dismissed the experiential intervention ({purpose})."
    if ui_response.data.get("decision") == "accept":
        _persist_card(
            store=store,
            image_data_url=f"data:{cached_mime};base64,{cached_b64}",
            caption=caption,
            purpose=purpose,
        )
        _intervention_cache.pop(cache_key, None)
        return f"User accepted the experiential intervention ({purpose}). {caption}"
    _intervention_cache.pop(cache_key, None)
    return f"User dismissed the experiential intervention ({purpose})."
