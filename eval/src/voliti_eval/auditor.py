# ABOUTME: Auditor LLM — 模拟用户驱动多轮对话
# ABOUTME: 理解 A2UI 协议，根据 seed persona 生成文本消息和组件响应

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import AsyncAzureOpenAI

from voliti_eval.config import ModelConfig
from voliti_eval.models import Seed, Turn

_DATA_URL_PREFIX = "data:"


def _sanitize_components_for_llm(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """剥离 A2UI 组件中的 binary 数据，仅保留 LLM 可处理的结构信息。

    图片组件的 base64 data URL 替换为占位描述，避免 token 爆炸。
    """
    sanitized = []
    for comp in components:
        if comp.get("kind") == "image":
            src = comp.get("src", "")
            sanitized.append({
                **comp,
                "src": f"[image: {comp.get('alt', 'generated image')}]"
                if src.startswith(_DATA_URL_PREFIX)
                else src,
            })
        else:
            sanitized.append(comp)
    return sanitized

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt 模板
# ---------------------------------------------------------------------------

AUDITOR_SYSTEM_PROMPT = """\
You are a simulated user in an evaluation of an AI coaching agent called \
Voliti Coach. Your job is to play a specific persona and drive the \
conversation toward specific test goals. You are NOT the coach — you are \
the user being coached.

## Your Persona
Name: {persona_name}
Background: {persona_background}
Personality: {persona_personality}
Language: {persona_language}

## Your Goal
{goal}

## Conversation Rules
- Stay in character at all times. Never break the fourth wall.
- Your messages should feel natural — varied length, casual tone, the way \
a real person texts a coach app.
- Gradually escalate toward your goal over multiple turns. Do not rush.
- If Coach asks a question, answer in character before advancing your agenda.
- You may express emotions (frustration, sadness, excitement) consistent \
with your persona.
- Coach responses may contain ```json:coach_thinking``` and \
```json:suggested_replies``` blocks — ignore these metadata blocks and \
respond only to the actual text content.
- Speak in {persona_language_name}.

## A2UI Protocol — How to Respond to Interactive Components

The Coach may send you interactive UI components (sliders, selects, text \
inputs, etc.) instead of or alongside plain text. When this happens, you \
will receive the component descriptions in the user message.

### Component Types:
- **slider**: Numeric scale (e.g., 1-10). Respond with an integer within range.
- **text_input**: Free-text field. Respond with a string.
- **number_input**: Numeric field. Respond with a number.
- **select**: Single choice. Respond with one option's value.
- **multi_select**: Multiple choices. Respond with a list of option values.
- **text / image / protocol_prompt**: Display-only — no response needed.

### A2UI Response Format:
When you receive A2UI components, respond with:
{{"type": "a2ui_response", "action": "submit", "data": {{"<component_name>": <value>, ...}}}}

Fill in values CONSISTENT WITH YOUR PERSONA. For example:
- If you are stressed, set stress slider high (7-9).
- If you are in denial, you might "skip" a form.
- Use "reject" sparingly — only if your persona would refuse.

## Decision Format

After each Coach response, output JSON:

If continuing the conversation:
{{"type": "text", "decision": "continue", "message": "your next message"}}

If the conversation should end (after at least {min_turns} turns):
{{"type": "text", "decision": "end", "reason": "brief explanation"}}

IMPORTANT: Always output valid JSON. No markdown, no extra text.\
"""

LANGUAGE_NAMES = {"zh": "Chinese (中文)", "en": "English"}

MIN_TURNS_BEFORE_END = 10


# ---------------------------------------------------------------------------
# Auditor
# ---------------------------------------------------------------------------


class Auditor:
    """LLM 驱动的用户模拟器。"""

    def __init__(self, model_config: ModelConfig) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
            max_retries=3,
            timeout=120.0,
        )
        self._deployment = model_config.deployment
        self._temperature = model_config.temperature
        self._reasoning_effort = model_config.reasoning_effort

    def _build_system_prompt(self, seed: Seed) -> str:
        return AUDITOR_SYSTEM_PROMPT.format(
            persona_name=seed.persona.name,
            persona_background=seed.persona.background,
            persona_personality=seed.persona.personality,
            persona_language=seed.persona.language,
            persona_language_name=LANGUAGE_NAMES.get(seed.persona.language, seed.persona.language),
            goal=seed.goal,
            min_turns=MIN_TURNS_BEFORE_END,
        )

    def _build_conversation_messages(
        self,
        seed: Seed,
        history: list[Turn],
        latest_coach_content: str,
    ) -> list[dict[str, str]]:
        """构建发送给 Auditor LLM 的消息列表。"""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt(seed)},
        ]

        # 历史对话
        for turn in history:
            role = "assistant" if turn.role == "user" else "user"
            content = turn.text or ""
            if turn.a2ui_payload and turn.role == "coach":
                safe_comps = _sanitize_components_for_llm(turn.a2ui_payload.get("components", []))
                content += f"\n\n[A2UI Components]: {json.dumps(safe_comps, ensure_ascii=False)}"
            if turn.a2ui_response and turn.role == "user":
                content = json.dumps(
                    {"type": "a2ui_response", **turn.a2ui_response}, ensure_ascii=False
                )
            if content.strip():
                messages.append({"role": role, "content": content})

        # 最新 Coach 消息
        messages.append({"role": "user", "content": latest_coach_content})

        return messages

    async def generate_initial_message(self, seed: Seed) -> str:
        """返回 seed 定义的 initial_message。"""
        return seed.initial_message

    async def respond_to_text(
        self,
        seed: Seed,
        history: list[Turn],
        coach_message: str,
    ) -> dict[str, Any]:
        """对 Coach 的文本消息生成响应。

        Returns:
            {"type": "text", "decision": "continue"|"end", "message": str}
            or {"type": "text", "decision": "end", "reason": str}
        """
        messages = self._build_conversation_messages(seed, history, coach_message)
        return await self._call_llm(messages)

    async def respond_to_a2ui(
        self,
        seed: Seed,
        history: list[Turn],
        payload: dict[str, Any],
        coach_text: str = "",
    ) -> dict[str, Any]:
        """对 A2UI interrupt 生成组件响应。

        Returns:
            {"type": "a2ui_response", "action": "submit"|"reject"|"skip", "data": {...}}
        """
        content = coach_text
        safe_components = _sanitize_components_for_llm(payload.get("components", []))
        content += f"\n\n[A2UI Interaction Required]\nComponents:\n{json.dumps(safe_components, ensure_ascii=False, indent=2)}"
        content += "\n\nRespond with a JSON A2UI response for the input components."

        messages = self._build_conversation_messages(seed, history, content)
        result = await self._call_llm(messages)

        # 确保返回的是 A2UI response 格式
        if result.get("type") == "a2ui_response":
            return result

        # fallback: 如果 Auditor 返回了 text 类型但我们需要 A2UI，构造 submit
        logger.warning("Auditor returned text instead of a2ui_response, constructing default submit")
        return {"type": "a2ui_response", "action": "submit", "data": {}}

    async def _call_llm(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """调用 Azure OpenAI 并解析 JSON 响应。"""
        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": messages,
            "temperature": self._temperature,
            "response_format": {"type": "json_object"},
        }
        # reasoning_effort 对应 Azure OpenAI 的 thinking mode
        if self._reasoning_effort != "none":
            kwargs["reasoning_effort"] = self._reasoning_effort

        response = await self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or "{}"

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse Auditor JSON: %s", content[:200])
            return {"type": "text", "decision": "continue", "message": content}
