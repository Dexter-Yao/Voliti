# ABOUTME: 评估编排器
# ABOUTME: 并发执行 seed 场景，每个 seed 使用独立 Store namespace 实现隔离

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

_THINKING_RE = re.compile(r"```json:coach_thinking\s*\n(.*?)\n```", re.DOTALL)
_REPLIES_RE = re.compile(r"```json:suggested_replies\s*\n(.*?)\n```", re.DOTALL)


def _strip_binary_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """剥离 A2UI payload 中的 base64 图片数据，保留结构信息。

    用于 transcript 序列化——避免 JSON 文件膨胀到几 MB。
    """
    components = payload.get("components")
    if not components:
        return payload
    clean_components = []
    for comp in components:
        if comp.get("kind") == "image" and isinstance(comp.get("src"), str) and comp["src"].startswith("data:"):
            clean_components.append({**comp, "src": "[data_url]"})
        else:
            clean_components.append(comp)
    return {**payload, "components": clean_components}


def build_a2ui_resume_response(
    a2ui_result: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """构造 resume 所需的 A2UIResponse。"""
    response = {
        "action": a2ui_result.get("action", "submit"),
        "data": a2ui_result.get("data", {}),
    }
    metadata = payload.get("metadata", {})
    interrupt_id = metadata.get("interrupt_id") if isinstance(metadata, dict) else None
    if isinstance(interrupt_id, str) and interrupt_id:
        response["interrupt_id"] = interrupt_id
    return response


def _inject_timestamp(message: str) -> str:
    """在用户消息前注入 ISO 8601 时间戳，与 iOS 客户端行为一致。"""
    ts = datetime.now(UTC).isoformat()
    return f"[{ts}] {message}"


def _extract_structured_blocks(text: str) -> tuple[str, dict | None, list[str] | None]:
    """从 Coach 文本中提取 coach_thinking 和 suggested_replies 块。

    Returns: (clean_text, thinking_dict, replies_list)
    """
    thinking: dict | None = None
    replies: list[str] | None = None

    m = _THINKING_RE.search(text)
    if m:
        try:
            thinking = json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
        text = text[:m.start()] + text[m.end():]

    m = _REPLIES_RE.search(text)
    if m:
        try:
            replies = json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
        text = text[:m.start()] + text[m.end():]

    return text.strip(), thinking, replies


def _save_image_to_file(data_url: str, output_dir: str, filename: str) -> str | None:
    """将 base64 data URL 解码并保存为图片文件，返回相对路径。

    文件保存到 {output_dir}/images/{filename}.{ext}，
    返回相对路径 images/{filename}.{ext}（供 report.html 引用）。
    """
    if not data_url.startswith("data:"):
        return None
    try:
        header, b64_data = data_url.split(",", 1)
        raw = base64.b64decode(b64_data)
        ext = "jpg" if "jpeg" in header else "png"
        rel_path = f"images/{filename}.{ext}"
        abs_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(raw)
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

    # 发送初始消息（注入时间戳）
    initial_msg = await auditor.generate_initial_message(seed)
    timestamped_msg = _inject_timestamp(initial_msg)
    turns.append(Turn(
        index=turn_index,
        role="user",
        timestamp=datetime.now(UTC),
        text=initial_msg,
    ))
    turn_index += 1

    logger.info("[%s] User (initial): %s", seed.id, initial_msg[:80])
    events = await client.send_message(thread_id, timestamped_msg)

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
                for img_idx, img in enumerate(event.images):
                    src = img.get("src", "")
                    # 将缩略图保存为文件（~50KB），transcript 引用相对路径
                    if output_dir and src.startswith("data:"):
                        filename = f"{seed.id}_turn{turn_index}_img{img_idx}"
                        saved = _save_image_to_file(src, output_dir, filename)
                        if saved:
                            src = saved
                    all_images.append(ImageRecord(
                        src=src,
                        alt=img.get("alt", ""),
                    ))

        raw_coach_text = "\n".join(coach_text_parts) if coach_text_parts else ""

        # 提取 coach_thinking 和 suggested_replies 结构化块
        coach_text, thinking, replies = _extract_structured_blocks(raw_coach_text)

        # 记录 Coach turn
        coach_turn = Turn(
            index=turn_index,
            role="coach",
            timestamp=datetime.now(UTC),
            text=coach_text or None,
            a2ui_payload=_strip_binary_from_payload(pending_interrupt.payload) if pending_interrupt else None,
            images=all_images or None,
            coach_thinking=thinking,
            suggested_replies=replies,
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

            a2ui_response = build_a2ui_resume_response(
                a2ui_result,
                pending_interrupt.payload,
            )

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
            logger.warning("[%s] Empty coach response (raw=%d chars, thinking=%s, replies=%s)",
                           seed.id, len(raw_coach_text), thinking is not None, replies is not None)
            transcript.end_reason = "empty_response"
            break

        user_turn_count = sum(1 for t in turns if t.role == "user")
        auditor_response = await auditor.respond_to_text(seed, turns, coach_text)

        decision = auditor_response.get("decision", "continue")
        if decision == "end":
            reason = auditor_response.get("reason", "")
            if user_turn_count >= 6:
                logger.info("[%s] Auditor ended: %s", seed.id, reason)
                transcript.end_reason = "auditor_ended"
            else:
                logger.info("[%s] Auditor ended early (turn %d): %s", seed.id, user_turn_count, reason)
                transcript.end_reason = "auditor_ended_early"
            break

        user_message = auditor_response.get("message", "")
        if not user_message:
            logger.warning("[%s] Auditor returned empty message (decision=%s)", seed.id, decision)
            transcript.end_reason = "auditor_empty"
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
        events = await client.send_message(thread_id, _inject_timestamp(user_message))

    else:
        transcript.end_reason = "max_turns"
        logger.info("[%s] Max turns reached", seed.id)

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
    """执行单个 seed 的完整流程（Store 隔离 → 对话 → 评分）。"""
    user_id = f"eval_{seed.id}"
    client = CoachClient(
        config.server_url,
        config.assistant_id,
        config.turn_timeout_seconds,
    )
    client.with_user_id(user_id)

    # Onboarding seed（无 pre_state）使用 onboarding session_mode
    if seed.pre_state is None:
        client.with_session_mode("onboarding")

    transcript: Transcript | None = None
    score_card = ScoreCard(seed_id=seed.id)

    try:
        logger.info("[%s] Starting (user_id=%s)", seed.id, user_id)

        # 清空 + 预填充隔离的 Store namespace
        await clear_store(client.store, user_id=user_id)
        if seed.pre_state:
            await populate_store(client.store, seed.pre_state, user_id=user_id)

        # 创建线程 + 运行对话
        thread_id = await client.create_thread()
        max_turns = seed.max_turns or config.max_turns_default
        transcript = await run_conversation(seed, thread_id, auditor, client, max_turns, output_dir=output_dir)

        # Judge 评分
        if judge_fn:
            score_card = await judge_fn(seed, transcript)

        logger.info("[%s] Completed: %d turns, end_reason=%s",
                    seed.id, transcript.turn_count, transcript.end_reason)

    except Exception:
        logger.exception("[%s] Failed", seed.id)
        if transcript is not None:
            # 保留已收集的对话数据，仅标记异常
            transcript.end_reason = "error"
            transcript.finished_at = datetime.now(UTC)
        else:
            transcript = Transcript(
                seed_id=seed.id,
                seed_name=seed.name,
                thread_id="error",
                started_at=datetime.now(UTC),
                finished_at=datetime.now(UTC),
                end_reason="error",
            )

    finally:
        # 清理 Store
        try:
            await clear_store(client.store, user_id=user_id)
        except Exception:
            logger.warning("[%s] Store cleanup failed", seed.id)

    return SeedResult(seed=seed, transcript=transcript, score_card=score_card)


async def run_evaluation(
    seeds: list[Seed],
    config: EvalConfig,
    judge_fn: Any = None,
    output_dir: str = "",
) -> EvalResult:
    """并发执行所有 seed 场景，每个 seed 使用独立的 Store namespace。

    Args:
        seeds: 要运行的 seed 列表。
        config: 评估配置。
        judge_fn: 可选的 Judge 评分函数，签名 (Seed, Transcript) -> ScoreCard。
        output_dir: 评估输出目录，图片保存到其 images/ 子目录。
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

    auditor = Auditor(config.auditor_model, timeout=config.turn_timeout_seconds)

    # 限制并发数，避免 Azure OpenAI API 连接超时
    max_concurrency = 5
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_with_semaphore(seed: Seed) -> SeedResult:
        async with semaphore:
            return await _run_single_seed(seed, config, auditor, judge_fn, output_dir=output_dir)

    logger.info("Running %d seeds (max %d concurrent)", len(seeds), max_concurrency)
    tasks = [_run_with_semaphore(seed) for seed in seeds]
    seed_results = await asyncio.gather(*tasks)

    # 按 seed ID 排序保持输出一致性
    result.seed_results = sorted(seed_results, key=lambda sr: sr.seed.id)
    result.finished_at = datetime.now(UTC)
    return result
