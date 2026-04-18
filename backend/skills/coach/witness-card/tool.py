# ABOUTME: Witness Card 技能专用工具
# ABOUTME: 接收结构化见证上下文，组装图片 prompt，处理重试并返回结构化 envelope

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Literal

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from pydantic import BaseModel
from typing_extensions import Annotated

from voliti.tools.experiential import render_witness_card

_PROMPT_BUILDER_PATH = Path(__file__).resolve().parent / "scripts" / "prompt_builder.py"
_CARD_ID_PATTERN = re.compile(r"Card saved as (?P<card_id>card_[A-Za-z0-9]+)")


def _load_prompt_builder():
    spec = importlib.util.spec_from_file_location(
        "voliti_witness_card_prompt_builder",
        _PROMPT_BUILDER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Prompt builder unavailable: {_PROMPT_BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PROMPT_BUILDER = _load_prompt_builder()
build_witness_card_prompt = _PROMPT_BUILDER.build_witness_card_prompt


class WitnessCardInput(BaseModel):
    """Coach-facing structured arguments for issuing a Witness Card."""

    achievement_title: str
    achievement_type: Literal["explicit", "implicit", "journey"]
    emotional_tone: Literal["growth", "warmth", "strength", "breakthrough"]
    evidence_summary: str
    scene_anchors: list[str]
    narrative: str
    chapter_id: str = ""
    linked_lifesign_id: str = ""
    user_quote: str = ""
    aspect_ratio: Literal["3:4", "4:3", "1:1"] = "3:4"


WitnessCardInput.model_rebuild()


def _format_result(
    *,
    status: str,
    reason_code: str,
    coach_recommendation: str,
    user_message: str = "",
    card_id: str = "",
    missing_fields: list[str] | None = None,
) -> str:
    missing = ", ".join(missing_fields or []) or "-"
    return "\n".join(
        [
            "<WITNESS_CARD_RESULT>",
            f"status: {status}",
            f"reason_code: {reason_code}",
            f"coach_recommendation: {coach_recommendation}",
            f"user_message: {user_message or '-'}",
            f"card_id: {card_id or '-'}",
            f"missing_fields: {missing}",
            "</WITNESS_CARD_RESULT>",
        ]
    )


def _validate_inputs(
    *,
    achievement_title: str,
    evidence_summary: str,
    scene_anchors: list[str],
    narrative: str,
) -> list[str]:
    missing_fields: list[str] = []
    if not achievement_title.strip():
        missing_fields.append("achievement_title")
    if len(evidence_summary.strip()) < 16:
        missing_fields.append("evidence_summary")
    cleaned_anchors = [anchor.strip() for anchor in scene_anchors if anchor.strip()]
    if len(cleaned_anchors) < 2:
        missing_fields.append("scene_anchors")
    if len(narrative.strip()) < 12:
        missing_fields.append("narrative")
    return missing_fields


def _render_witness_card(
    *,
    prompt: str,
    narrative: str,
    achievement_title: str,
    achievement_type: str,
    aspect_ratio: str,
    chapter_id: str,
    linked_lifesign_id: str,
    user_quote: str,
    store: BaseStore | None,
) -> str:
    return render_witness_card(
        prompt=prompt,
        narrative=narrative,
        achievement_title=achievement_title,
        achievement_type=achievement_type,
        aspect_ratio=aspect_ratio,
        chapter_id=chapter_id,
        linked_lifesign_id=linked_lifesign_id,
        user_quote=user_quote,
        store=store,
    )


def _is_retryable_render_failure(result: str) -> bool:
    return result.startswith("Image generation failed")


def _is_terminal_render_failure(result: str) -> bool:
    return result.startswith("Card storage failed") or result.startswith(
        "User response no longer matches"
    )


def _extract_card_id(result: str) -> str:
    match = _CARD_ID_PATTERN.search(result)
    if match is None:
        return ""
    return match.group("card_id")


@tool(args_schema=WitnessCardInput)
def issue_witness_card(
    achievement_title: str,
    achievement_type: Literal["explicit", "implicit", "journey"],
    emotional_tone: Literal["growth", "warmth", "strength", "breakthrough"],
    evidence_summary: str,
    scene_anchors: list[str],
    narrative: str,
    chapter_id: str = "",
    linked_lifesign_id: str = "",
    user_quote: str = "",
    aspect_ratio: Literal["3:4", "4:3", "1:1"] = "3:4",
    store: Annotated[BaseStore | None, InjectedStore()] = None,
) -> str:
    """Issue a Witness Card from structured context instead of a free-form prompt."""
    missing_fields = _validate_inputs(
        achievement_title=achievement_title,
        evidence_summary=evidence_summary,
        scene_anchors=scene_anchors,
        narrative=narrative,
    )
    if missing_fields:
        return _format_result(
            status="needs_more_detail",
            reason_code="insufficient_context",
            coach_recommendation="ask_for_detail",
            missing_fields=missing_fields,
        )

    prompt = build_witness_card_prompt(
        achievement_title=achievement_title,
        emotional_tone=emotional_tone,
        evidence_summary=evidence_summary,
        scene_anchors=[anchor.strip() for anchor in scene_anchors if anchor.strip()],
        user_quote=user_quote.strip(),
    )

    first_result = _render_witness_card(
        prompt=prompt,
        narrative=narrative,
        achievement_title=achievement_title,
        achievement_type=achievement_type,
        aspect_ratio=aspect_ratio,
        chapter_id=chapter_id,
        linked_lifesign_id=linked_lifesign_id,
        user_quote=user_quote,
        store=store,
    )
    if _is_retryable_render_failure(first_result):
        second_result = _render_witness_card(
            prompt=prompt,
            narrative=narrative,
            achievement_title=achievement_title,
            achievement_type=achievement_type,
            aspect_ratio=aspect_ratio,
            chapter_id=chapter_id,
            linked_lifesign_id=linked_lifesign_id,
            user_quote=user_quote,
            store=store,
        )
        if _is_retryable_render_failure(second_result):
            return _format_result(
                status="retryable_failure",
                reason_code="image_generation_retry_exhausted",
                coach_recommendation="tell_user_retry_later",
                user_message="我想把这个时刻认真留住，但当前生成服务不稳定。稍后我再为你补上。",
            )
        first_result = second_result

    if _is_terminal_render_failure(first_result):
        return _format_result(
            status="terminal_failure",
            reason_code="render_pipeline_failed",
            coach_recommendation="continue_without_card",
        )

    return _format_result(
        status="success",
        reason_code="issued",
        coach_recommendation="continue_without_card",
        card_id=_extract_card_id(first_result),
    )


TOOL = issue_witness_card
