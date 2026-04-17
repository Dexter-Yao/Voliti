# ABOUTME: Auditor LLM
# ABOUTME: 作为受约束的场景执行器驱动多轮对话，并优先按 seed 策略处理 A2UI

from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import AsyncAzureOpenAI

from voliti_eval.config import ModelConfig
from voliti_eval.models import A2UIPlanStep, Seed, Turn

logger = logging.getLogger(__name__)

_DATA_URL_PREFIX = "data:"
_LANGUAGE_NAMES = {"zh": "Chinese (中文)", "en": "English"}

AUDITOR_SYSTEM_PROMPT = """\
You are the simulated user in an evaluation of Voliti Coach.

Stay fully in character. You are NOT the coach and you are NOT judging the system.
Your job is to execute the seed faithfully, reveal information only when allowed,
and avoid helping the coach complete missing work.

Persona:
- Name: {persona_name}
- Background: {persona_background}
- Personality: {persona_personality}
- Language: {persona_language}

Scenario goal:
{goal}

Latent facts you know but do not proactively reveal unless the conversation rule allows it:
{latent_facts}

Reveal rules:
{reveal_rules}

Challenge rules:
{challenge_rules}

Conversation rules:
- Stay natural and concise.
- Do not volunteer missing data just because the coach skipped an important step.
- If the coach asks for something that should only be revealed when asked, answer it naturally.
- If a challenge rule is triggered, ask the specified challenge question once.
- Speak in {persona_language_name}.
- Ignore any ```json:coach_thinking``` and ```json:suggested_replies``` metadata blocks.

Stop rules:
- Do not end before {min_turns} user turns.
- End only when at least one of these completion conditions is satisfied: {complete_when}.
- Continue pressing until these conditions are met when relevant: {continue_until}.

Output valid JSON only.
For a normal reply:
{{"type": "text", "decision": "continue", "message": "your next message"}}

To end:
{{"type": "text", "decision": "end", "reason": "brief reason"}}
"""


def _sanitize_components_for_llm(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    for component in components:
        if component.get("kind") == "image":
            src = component.get("src", "")
            sanitized.append(
                {
                    **component,
                    "src": f"[image: {component.get('alt', 'generated image')}]"
                    if isinstance(src, str) and src.startswith(_DATA_URL_PREFIX)
                    else src,
                }
            )
        else:
            sanitized.append(component)
    return sanitized


class Auditor:
    """LLM 驱动的用户模拟器。"""

    def __init__(
        self,
        model_config: ModelConfig,
        *,
        timeout: float,
        min_turns_before_end: int = 4,
    ) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-03-01-preview"),
            max_retries=3,
            timeout=timeout,
        )
        self._deployment = model_config.deployment
        self._temperature = model_config.temperature
        self._reasoning_effort = model_config.reasoning_effort
        self._min_turns_before_end = min_turns_before_end

    async def generate_initial_message(self, seed: Seed) -> str:
        return seed.initial_message

    async def respond_to_text(
        self,
        seed: Seed,
        history: list[Turn],
        coach_message: str,
    ) -> dict[str, Any]:
        messages = self._build_conversation_messages(seed, history, coach_message)
        return await self._call_llm(messages)

    async def respond_to_a2ui(
        self,
        seed: Seed,
        history: list[Turn],
        payload: dict[str, Any],
        coach_text: str = "",
    ) -> dict[str, Any]:
        planned = self._build_planned_a2ui_response(seed, payload)
        if planned is not None:
            return planned

        messages = self._build_conversation_messages(
            seed,
            history,
            coach_text + "\n\n[A2UI Components]\n" + json.dumps(
                _sanitize_components_for_llm(payload.get("components", [])),
                ensure_ascii=False,
                indent=2,
            ),
        )
        messages.append(
            {
                "role": "system",
                "content": (
                    "Respond ONLY with an A2UI JSON response.\n"
                    "Valid shape: "
                    '{"type":"a2ui_response","action":"submit|reject|skip","data":{...},"reason":"...optional"}'
                ),
            }
        )

        result = await self._call_llm(messages)
        if result.get("type") == "a2ui_response" and result.get("action") in {"submit", "reject", "skip"}:
            return result

        retry_messages = messages + [
            {
                "role": "system",
                "content": "Your previous answer was invalid. Output ONLY a valid a2ui_response JSON object now.",
            }
        ]
        retry_result = await self._call_llm(retry_messages)
        if retry_result.get("type") == "a2ui_response" and retry_result.get("action") in {"submit", "reject", "skip"}:
            return retry_result
        raise ValueError("Auditor failed to return a valid a2ui_response after retry")

    def _build_system_prompt(self, seed: Seed) -> str:
        policy = seed.auditor_policy
        stop_rules = policy.stop_rules
        return AUDITOR_SYSTEM_PROMPT.format(
            persona_name=seed.persona.name,
            persona_background=seed.persona.background,
            persona_personality=seed.persona.personality,
            persona_language=seed.persona.language,
            persona_language_name=_LANGUAGE_NAMES.get(seed.persona.language, seed.persona.language),
            goal=seed.goal,
            latent_facts="\n".join(f"- {fact}" for fact in policy.latent_facts) or "- None",
            reveal_rules="\n".join(
                f"- {rule.topic}: when_asked={rule.when_asked}; respond=\"{rule.response}\""
                for rule in policy.reveal_rules
            )
            or "- None",
            challenge_rules="\n".join(
                f"- trigger={rule.trigger}; ask=\"{rule.message}\""
                for rule in policy.challenge_rules
            )
            or "- None",
            min_turns=max(self._min_turns_before_end, stop_rules.min_user_turns),
            complete_when=", ".join(stop_rules.complete_when) or "scenario feels complete",
            continue_until=", ".join(stop_rules.continue_until) or "none",
        )

    def _build_conversation_messages(
        self,
        seed: Seed,
        history: list[Turn],
        latest_coach_content: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt(seed)},
        ]
        for turn in history:
            role = "assistant" if turn.role == "user" else "user"
            content = turn.text or ""
            if turn.a2ui_payload and turn.role == "coach":
                content += "\n\n[A2UI Components]: " + json.dumps(
                    _sanitize_components_for_llm(turn.a2ui_payload.get("components", [])),
                    ensure_ascii=False,
                )
            if turn.a2ui_response and turn.role == "user":
                content = json.dumps({"type": "a2ui_response", **turn.a2ui_response}, ensure_ascii=False)
            if content.strip():
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": latest_coach_content})
        return messages

    def _build_planned_a2ui_response(
        self,
        seed: Seed,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        keyed_plan = {step.key: step for step in seed.auditor_policy.a2ui_plan}
        components = payload.get("components", [])
        input_components = [component for component in components if component.get("kind") in {"slider", "text_input", "number_input", "select", "multi_select"}]
        if not input_components:
            return None

        action = "submit"
        reason: str | None = None
        data: dict[str, Any] = {}
        matched_any = False

        for component in input_components:
            key = component.get("key")
            if not isinstance(key, str):
                continue
            plan = keyed_plan.get(key)
            if plan is None:
                continue
            matched_any = True
            action = plan.action
            if plan.reason:
                reason = plan.reason
            if plan.action == "submit":
                data[key] = self._normalize_planned_value(plan, component)

        if not matched_any:
            return None
        response: dict[str, Any] = {"type": "a2ui_response", "action": action}
        if action == "submit":
            response["data"] = data
        if reason:
            response["reason"] = reason
        return response

    def _normalize_planned_value(self, step: A2UIPlanStep, component: dict[str, Any]) -> Any:
        if step.value is not None:
            return step.value
        kind = component.get("kind")
        if kind == "multi_select":
            return []
        if kind == "select":
            options = component.get("options", [])
            if options:
                return options[0].get("value", "")
            return ""
        if kind == "text_input":
            return ""
        if kind == "number_input":
            return 0
        if kind == "slider":
            return component.get("min", 1)
        return ""

    async def _call_llm(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._deployment,
            "messages": messages,
            "temperature": self._temperature,
            "response_format": {"type": "json_object"},
        }
        if self._reasoning_effort != "none":
            kwargs["reasoning_effort"] = self._reasoning_effort
        response = await self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse Auditor JSON: %s", content[:500])
            return {"type": "text", "decision": "continue", "message": content}
