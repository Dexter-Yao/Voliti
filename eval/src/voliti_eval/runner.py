# ABOUTME: 评估编排器
# ABOUTME: 执行对话、抓取工件、运行 deterministic graders，并与 Judge 评分合并

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

from voliti_eval.auditor import Auditor
from voliti_eval.client import A2UIInterruptEvent, CoachClient, TextEvent, ToolCallEvent
from voliti_eval.config import EvalConfig
from voliti_eval.dimensions import (
    is_diagnostic_dimension,
    is_runtime_gate_dimension,
    is_user_gate_dimension,
)
from voliti_eval.graders import build_store_diff, grade_deterministic
from voliti_eval.models import (
    DimensionScore,
    EvalResult,
    ImageRecord,
    ScoreCard,
    Seed,
    SeedResult,
    StoreDiff,
    StoreSnapshot,
    ToolCallRecord,
    Transcript,
    Turn,
)
from voliti_eval.store import clear_store, populate_store, snapshot_store

logger = logging.getLogger(__name__)

_THINKING_RE = re.compile(r"```json:coach_thinking\s*\n(.*?)\n```", re.DOTALL)
_REPLIES_RE = re.compile(r"```json:suggested_replies\s*\n(.*?)\n```", re.DOTALL)


def _strip_binary_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    components = payload.get("components")
    if not components:
        return payload
    cleaned = []
    for component in components:
        if component.get("kind") == "image" and isinstance(component.get("src"), str) and component["src"].startswith("data:"):
            cleaned.append({**component, "src": "[data_url]"})
        else:
            cleaned.append(component)
    return {**payload, "components": cleaned}


def build_a2ui_resume_response(
    a2ui_result: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    response = {
        "action": a2ui_result.get("action", "submit"),
        "data": a2ui_result.get("data", {}),
    }
    metadata = payload.get("metadata", {})
    interrupt_id = metadata.get("interrupt_id") if isinstance(metadata, dict) else None
    if isinstance(interrupt_id, str) and interrupt_id:
        response["interrupt_id"] = interrupt_id
    reason = a2ui_result.get("reason")
    if isinstance(reason, str) and reason:
        response["reason"] = reason
    return response


def assemble_score_card(
    *,
    seed_id: str,
    primary_dimensions: list[str],
    deterministic_scores: dict[str, DimensionScore],
    llm_scores: dict[str, DimensionScore],
    overall_assessment: str = "",
    judge_requested_dimensions: list[str] | None = None,
    judge_dimension_definitions: dict[str, str] | None = None,
    judge_prompt_rendered: str = "",
) -> ScoreCard:
    def _lane_pass_rate(predicate: Any) -> float:
        lane_scores = [score for dimension_id, score in scores.items() if predicate(dimension_id)]
        if not lane_scores:
            return 0.0
        return round(sum(1 for score in lane_scores if score.passed) / len(lane_scores), 2)

    def _lane_met(predicate: Any) -> bool:
        lane_primary = [dimension_id for dimension_id in primary_dimensions if predicate(dimension_id)]
        if not lane_primary:
            return True
        missing = [dimension_id for dimension_id in lane_primary if dimension_id not in scores]
        if missing:
            return False
        return all(scores[dimension_id].passed for dimension_id in lane_primary)

    scores = {**deterministic_scores, **llm_scores}
    user_gate_met = _lane_met(is_user_gate_dimension)
    runtime_gate_met = _lane_met(is_runtime_gate_dimension)
    if not scores:
        return ScoreCard(
            seed_id=seed_id,
            overall_assessment=overall_assessment,
            must_pass_met=user_gate_met and runtime_gate_met,
            user_gate_met=user_gate_met,
            runtime_gate_met=runtime_gate_met,
            judge_requested_dimensions=judge_requested_dimensions or [],
            judge_dimension_definitions=judge_dimension_definitions or {},
            judge_prompt_rendered=judge_prompt_rendered,
        )

    pass_rate = round(sum(1 for score in scores.values() if score.passed) / len(scores), 2)
    must_pass_met = user_gate_met and runtime_gate_met
    critical_failures = [
        dimension_id
        for dimension_id, score in scores.items()
        if not score.passed and score.failure_severity == "critical"
    ]
    return ScoreCard(
        seed_id=seed_id,
        scores=scores,
        overall_assessment=overall_assessment,
        critical_failures=critical_failures,
        pass_rate=pass_rate,
        must_pass_met=must_pass_met,
        user_gate_pass_rate=_lane_pass_rate(is_user_gate_dimension),
        runtime_gate_pass_rate=_lane_pass_rate(is_runtime_gate_dimension),
        diagnostic_pass_rate=_lane_pass_rate(is_diagnostic_dimension),
        user_gate_met=user_gate_met,
        runtime_gate_met=runtime_gate_met,
        judge_requested_dimensions=judge_requested_dimensions or [],
        judge_dimension_definitions=judge_dimension_definitions or {},
        judge_prompt_rendered=judge_prompt_rendered,
    )


def _inject_timestamp(message: str) -> str:
    ts = datetime.now(UTC).isoformat()
    return f"[{ts}] {message}"


def _extract_structured_blocks(text: str) -> tuple[str, dict | None, list[str] | None]:
    thinking: dict | None = None
    replies: list[str] | None = None

    match = _THINKING_RE.search(text)
    if match:
        try:
            thinking = json.loads(match.group(1))
        except json.JSONDecodeError:
            thinking = None
        text = text[:match.start()] + text[match.end():]

    match = _REPLIES_RE.search(text)
    if match:
        try:
            replies = json.loads(match.group(1))
        except json.JSONDecodeError:
            replies = None
        text = text[:match.start()] + text[match.end():]

    return text.strip(), thinking, replies


def _save_image_to_file(data_url: str, output_dir: str, filename: str) -> str | None:
    if not data_url.startswith("data:"):
        return None
    try:
        header, encoded = data_url.split(",", 1)
        raw = base64.b64decode(encoded)
        ext = "jpg" if "jpeg" in header else "png"
        rel_path = f"images/{filename}.{ext}"
        abs_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as handle:
            handle.write(raw)
        return rel_path
    except Exception:
        logger.warning("Failed to save image: %s", filename)
        return None


async def run_conversation(
    seed: Seed,
    thread_id: str,
    auditor: Auditor,
    client: CoachClient,
    max_turns: int,
    output_dir: str = "",
) -> Transcript:
    transcript = Transcript(
        seed_id=seed.id,
        seed_name=seed.name,
        thread_id=thread_id,
        started_at=datetime.now(UTC),
        metadata={
            "entry_mode": seed.entry_mode,
            "auditor_prompt_rendered": auditor.render_system_prompt(seed),
        },
    )

    turns: list[Turn] = []
    turn_index = 0

    initial_message = await auditor.generate_initial_message(seed)
    turns.append(
        Turn(
            index=turn_index,
            role="user",
            timestamp=datetime.now(UTC),
            text=initial_message,
        )
    )
    turn_index += 1
    events = await client.send_message(thread_id, _inject_timestamp(initial_message))

    while turn_index < max_turns * 2:
        coach_text_parts: list[str] = []
        pending_interrupt: A2UIInterruptEvent | None = None
        pending_tool_calls: list[ToolCallRecord] = []
        images: list[ImageRecord] = []

        for event in events:
            if isinstance(event, TextEvent):
                coach_text_parts.append(event.text)
            elif isinstance(event, ToolCallEvent):
                pending_tool_calls.extend(event.tool_calls)
            elif isinstance(event, A2UIInterruptEvent):
                pending_interrupt = event
                for image_index, image in enumerate(event.images):
                    src = image.get("src", "")
                    if output_dir and src.startswith("data:"):
                        saved_path = _save_image_to_file(
                            src,
                            output_dir,
                            f"{seed.id}_turn{turn_index}_img{image_index}",
                        )
                        if saved_path:
                            src = saved_path
                    images.append(ImageRecord(src=src, alt=image.get("alt", "")))

        raw_text = "\n".join(coach_text_parts) if coach_text_parts else ""
        coach_text, thinking, replies = _extract_structured_blocks(raw_text)

        normalized_tool_calls = [
            ToolCallRecord(
                turn_index=turn_index,
                name=call.name,
                arguments=call.arguments,
                raw=call.raw,
            )
            for call in pending_tool_calls
        ]
        coach_turn = Turn(
            index=turn_index,
            role="coach",
            timestamp=datetime.now(UTC),
            text=coach_text or None,
            a2ui_payload=_strip_binary_from_payload(pending_interrupt.payload) if pending_interrupt else None,
            images=images or None,
            coach_thinking=thinking,
            suggested_replies=replies,
            tool_calls=normalized_tool_calls or None,
        )
        turns.append(coach_turn)
        turn_index += 1

        if pending_interrupt:
            a2ui_result = await auditor.respond_to_a2ui(seed, turns, pending_interrupt.payload, coach_text)
            a2ui_response = build_a2ui_resume_response(a2ui_result, pending_interrupt.payload)
            turns.append(
                Turn(
                    index=turn_index,
                    role="user",
                    timestamp=datetime.now(UTC),
                    a2ui_response=a2ui_response,
                )
            )
            turn_index += 1
            events = await client.resume_interrupt(thread_id, a2ui_response)
            continue

        if not coach_text:
            transcript.end_reason = "empty_response"
            break

        user_turn_count = sum(1 for turn in turns if turn.role == "user")
        auditor_response = await auditor.respond_to_text(seed, turns, coach_text)
        decision = auditor_response.get("decision", "continue")
        if decision == "end":
            transcript.end_reason = "auditor_ended" if user_turn_count >= 6 else "auditor_ended_early"
            break

        user_message = auditor_response.get("message", "")
        if not user_message:
            transcript.end_reason = "auditor_empty"
            break

        turns.append(
            Turn(
                index=turn_index,
                role="user",
                timestamp=datetime.now(UTC),
                text=user_message,
            )
        )
        turn_index += 1
        events = await client.send_message(thread_id, _inject_timestamp(user_message))
    else:
        transcript.end_reason = "max_turns"

    transcript.turns = turns
    transcript.turn_count = len(turns)
    transcript.finished_at = datetime.now(UTC)
    return transcript


async def _run_single_seed(
    seed: Seed,
    config: EvalConfig,
    auditor: Auditor,
    judge_fn: Any | None,
    output_dir: str = "",
) -> SeedResult:
    user_id = f"eval_{seed.id}"
    client = CoachClient(
        config.server_url,
        config.assistant_id,
        config.turn_timeout_seconds,
    )
    client.with_user_id(user_id)
    if seed.entry_mode in {"new", "resume", "re_entry"}:
        client.with_session_type("onboarding")

    transcript: Transcript | None = None
    store_before = StoreSnapshot()
    store_after = StoreSnapshot()
    store_diff = StoreDiff()
    tool_calls: list[ToolCallRecord] = []
    score_card = ScoreCard(seed_id=seed.id)

    try:
        await clear_store(client.store, user_id=user_id)
        if seed.pre_state:
            await populate_store(client.store, seed.pre_state, user_id=user_id)
        store_before = await snapshot_store(client.store, user_id=user_id)

        thread_id = await client.create_thread()
        transcript = await run_conversation(
            seed,
            thread_id,
            auditor,
            client,
            seed.max_turns or config.max_turns_default,
            output_dir=output_dir,
        )

        tool_calls = _flatten_tool_calls(transcript)
        store_after = await snapshot_store(client.store, user_id=user_id)
        store_diff = build_store_diff(store_before, store_after)
        deterministic_scores = grade_deterministic(
            seed,
            transcript,
            tool_calls,
            store_before,
            store_after,
            store_diff,
        )

        llm_scores: dict[str, DimensionScore] = {}
        overall_assessment = ""
        if judge_fn is not None:
            llm_score_card = await judge_fn(
                seed,
                transcript,
                tool_calls=tool_calls,
                store_diff=store_diff,
                store_after=store_after,
            )
            llm_scores = llm_score_card.scores
            overall_assessment = llm_score_card.overall_assessment

        score_card = assemble_score_card(
            seed_id=seed.id,
            primary_dimensions=seed.scoring_focus.primary,
            deterministic_scores=deterministic_scores,
            llm_scores=llm_scores,
            overall_assessment=overall_assessment,
            judge_requested_dimensions=llm_score_card.judge_requested_dimensions if judge_fn is not None else [],
            judge_dimension_definitions=llm_score_card.judge_dimension_definitions if judge_fn is not None else {},
            judge_prompt_rendered=llm_score_card.judge_prompt_rendered if judge_fn is not None else "",
        )
    except Exception:
        logger.exception("[%s] Failed", seed.id)
        if transcript is None:
            transcript = Transcript(
                seed_id=seed.id,
                seed_name=seed.name,
                thread_id="error",
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
                end_reason="error",
            )
        else:
            transcript.end_reason = "error"
            transcript.finished_at = datetime.now(UTC)
    finally:
        try:
            await clear_store(client.store, user_id=user_id)
        except Exception:
            logger.warning("[%s] Store cleanup failed", seed.id)

    return SeedResult(
        seed=seed,
        transcript=transcript,
        score_card=score_card,
        tool_calls=tool_calls,
        store_before=store_before,
        store_after=store_after,
        store_diff=store_diff,
    )


async def run_evaluation(
    seeds: list[Seed],
    config: EvalConfig,
    judge_fn: Any = None,
    output_dir: str = "",
    min_turns_before_end: int | None = None,
) -> EvalResult:
    result = EvalResult(
        run_id=datetime.now(UTC).strftime("%Y%m%d_%H%M%S"),
        started_at=datetime.now(UTC),
        config_snapshot={
            "server_url": config.server_url,
            "assistant_id": config.assistant_id,
            "max_turns_default": config.max_turns_default,
            "auditor_model": config.auditor_model.deployment,
            "judge_model": config.judge_model.deployment,
        },
    )

    auditor_kwargs: dict[str, Any] = {"timeout": config.turn_timeout_seconds}
    if min_turns_before_end is not None:
        auditor_kwargs["min_turns_before_end"] = min_turns_before_end
    auditor = Auditor(config.auditor_model, **auditor_kwargs)

    semaphore = asyncio.Semaphore(config.max_concurrency)

    async def _run_with_limit(seed: Seed) -> SeedResult:
        async with semaphore:
            return await _run_single_seed(seed, config, auditor, judge_fn, output_dir=output_dir)

    seed_results = await asyncio.gather(*[_run_with_limit(seed) for seed in seeds])
    result.seed_results = sorted(seed_results, key=lambda item: item.seed.id)
    result.finished_at = datetime.now(UTC)
    return result


def _flatten_tool_calls(transcript: Transcript) -> list[ToolCallRecord]:
    flattened: list[ToolCallRecord] = []
    for turn in transcript.turns:
        if turn.tool_calls:
            flattened.extend(turn.tool_calls)
    return flattened
