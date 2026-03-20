# ABOUTME: 体验式干预工具
# ABOUTME: 调用 Gemini 3 Pro Image API 生成干预内容，通过 A2UI interrupt() 供用户审阅，接受后持久化到 Store

import base64
import os
import uuid
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

_intervention_cache: dict[int, tuple[str, str]] = {}
"""模块级缓存，避免 resume 重执行时重复调用 Gemini API。

LangGraph 在 interrupt() 后 resume 时会从 node 起重新执行。
缓存确保同一 prompt 不会重复调用付费 API。
值为 (base64_data, mime_type) 元组。
"""

INTERVENTIONS_NAMESPACE = ("constellate", "user", "interventions")


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
        aspect_ratio: Aspect ratio, e.g. "3:4", "1:1", "16:9".
        purpose: Intervention type identifier, e.g. "future_self", "scene_rehearsal".
        caption: Coach-voice narrative conveying the intervention intent.
    """
    cache_key = hash(prompt)

    if cache_key not in _intervention_cache:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )
        image_part = response.candidates[0].content.parts[0]
        _intervention_cache[cache_key] = (
            base64.b64encode(image_part.inline_data.data).decode(),
            image_part.inline_data.mime_type or "image/jpeg",
        )

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
    response = A2UIResponse.model_validate(raw_response)

    if response.action == "reject":
        _intervention_cache.pop(cache_key, None)
        return f"User dismissed the experiential intervention ({purpose})."
    if response.data.get("decision") == "accept":
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
