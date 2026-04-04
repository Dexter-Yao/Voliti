# ABOUTME: 评估编排器
# ABOUTME: 串行执行 seed 场景，管理对话循环、Store 隔离、transcript 收集

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from voliti_eval.auditor import Auditor
from voliti_eval.client import A2UIInterruptEvent, CoachClient, TextEvent
from voliti_eval.config import EvalConfig
from voliti_eval.models import (
    EvalResult,
    ImageRecord,
    ScoreCard,
    Seed,
    SeedResult,
    Transcript,
    Turn,
)
from voliti_eval.store import clear_store, populate_store

logger = logging.getLogger(__name__)


async def run_conversation(
    seed: Seed,
    thread_id: str,
    auditor: Auditor,
    client: CoachClient,
    max_turns: int,
) -> Transcript:
    """执行单个 seed 的完整对话循环。

    对话流程：
    1. Auditor 发送 initial_message
    2. CoachClient 流式收集 Coach 响应
    3. 如果遇到 A2UI interrupt → Auditor 生成组件响应 → resume
    4. 如果是纯文本 → Auditor 决定 continue/end
    5. 重复直到 end 或 max_turns
    """
    transcript = Transcript(
        seed_id=seed.id,
        seed_name=seed.name,
        thread_id=thread_id,
        started_at=datetime.now(UTC),
    )

    turns: list[Turn] = []
    turn_index = 0

    # 发送初始消息
    initial_msg = await auditor.generate_initial_message(seed)
    turns.append(Turn(
        index=turn_index,
        role="user",
        timestamp=datetime.now(UTC),
        text=initial_msg,
    ))
    turn_index += 1

    logger.info("[%s] User (initial): %s", seed.id, initial_msg[:80])
    events = await client.send_message(thread_id, initial_msg)

    while turn_index < max_turns * 2:  # *2 因为一个"轮"包含 user+coach
        # 处理 Coach 响应事件
        coach_text_parts: list[str] = []
        pending_interrupt: A2UIInterruptEvent | None = None
        all_images: list[ImageRecord] = []

        for event in events:
            if isinstance(event, TextEvent):
                coach_text_parts.append(event.text)
            elif isinstance(event, A2UIInterruptEvent):
                pending_interrupt = event
                for img in event.images:
                    all_images.append(ImageRecord(
                        src=img.get("src", ""),
                        alt=img.get("alt", ""),
                    ))

        coach_text = "\n".join(coach_text_parts) if coach_text_parts else ""

        # 记录 Coach turn
        coach_turn = Turn(
            index=turn_index,
            role="coach",
            timestamp=datetime.now(UTC),
            text=coach_text or None,
            a2ui_payload=pending_interrupt.payload if pending_interrupt else None,
            images=all_images or None,
        )
        turns.append(coach_turn)
        turn_index += 1

        if coach_text:
            logger.info("[%s] Coach: %s", seed.id, coach_text[:80])
        if pending_interrupt:
            logger.info("[%s] Coach: A2UI interrupt (%d components)",
                        seed.id, len(pending_interrupt.payload.get("components", [])))

        # 处理 A2UI interrupt
        if pending_interrupt:
            a2ui_result = await auditor.respond_to_a2ui(
                seed, turns, pending_interrupt.payload, coach_text
            )

            a2ui_response = {
                "action": a2ui_result.get("action", "submit"),
                "data": a2ui_result.get("data", {}),
            }

            # 记录 User A2UI 响应
            turns.append(Turn(
                index=turn_index,
                role="user",
                timestamp=datetime.now(UTC),
                a2ui_response=a2ui_response,
            ))
            turn_index += 1

            logger.info("[%s] User (A2UI): %s", seed.id, a2ui_response)

            # Resume interrupt，可能产生更多事件
            events = await client.resume_interrupt(thread_id, a2ui_response)

            # resume 后可能有后续文本或新 interrupt，继续循环处理
            continue

        # 纯文本响应 — 让 Auditor 决定下一步
        if not coach_text:
            logger.warning("[%s] Empty coach response", seed.id)
            break

        user_turn_count = sum(1 for t in turns if t.role == "user")
        auditor_response = await auditor.respond_to_text(seed, turns, coach_text)

        decision = auditor_response.get("decision", "continue")
        if decision == "end" and user_turn_count >= 6:
            logger.info("[%s] Auditor ended: %s", seed.id, auditor_response.get("reason", ""))
            transcript.end_reason = "auditor_ended"
            break

        user_message = auditor_response.get("message", "")
        if not user_message:
            logger.warning("[%s] Auditor returned empty message", seed.id)
            break

        # 记录 User turn
        turns.append(Turn(
            index=turn_index,
            role="user",
            timestamp=datetime.now(UTC),
            text=user_message,
        ))
        turn_index += 1

        logger.info("[%s] User: %s", seed.id, user_message[:80])
        events = await client.send_message(thread_id, user_message)

    else:
        transcript.end_reason = "max_turns"
        logger.info("[%s] Max turns reached", seed.id)

    transcript.turns = turns
    transcript.turn_count = len(turns)
    transcript.finished_at = datetime.now(UTC)

    return transcript


async def run_evaluation(
    seeds: list[Seed],
    config: EvalConfig,
    judge_fn: Any = None,
) -> EvalResult:
    """串行执行所有 seed 场景，收集评估结果。

    Args:
        seeds: 要运行的 seed 列表。
        config: 评估配置。
        judge_fn: 可选的 Judge 评分函数，签名 (Seed, Transcript) -> ScoreCard。
    """
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

    client = CoachClient(config.server_url, config.assistant_id)
    auditor = Auditor(config.auditor_model)

    for i, seed in enumerate(seeds, 1):
        logger.info("=" * 60)
        logger.info("Running seed %d/%d: %s (%s)", i, len(seeds), seed.id, seed.name)
        logger.info("=" * 60)

        try:
            # 清空 Store
            await clear_store(client.store)

            # 预填充状态
            if seed.pre_state:
                await populate_store(client.store, seed.pre_state)

            # 创建线程
            thread_id = await client.create_thread()

            # 运行对话
            max_turns = seed.max_turns or config.max_turns_default
            transcript = await run_conversation(seed, thread_id, auditor, client, max_turns)

            # Judge 评分
            score_card: ScoreCard
            if judge_fn:
                score_card = await judge_fn(seed, transcript)
            else:
                score_card = ScoreCard(seed_id=seed.id)

            result.seed_results.append(SeedResult(
                seed=seed,
                transcript=transcript,
                score_card=score_card,
            ))

            logger.info("[%s] Completed: %d turns, end_reason=%s",
                        seed.id, transcript.turn_count, transcript.end_reason)

        except Exception:
            logger.exception("[%s] Failed", seed.id)
            # 记录失败但继续下一个 seed
            error_transcript = Transcript(
                seed_id=seed.id,
                seed_name=seed.name,
                thread_id="error",
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
                end_reason="error",
            )
            result.seed_results.append(SeedResult(
                seed=seed,
                transcript=error_transcript,
                score_card=ScoreCard(seed_id=seed.id),
            ))

    result.finished_at = datetime.now(UTC)
    return result
