# ABOUTME: Deterministic graders
# ABOUTME: 用代码校验协议、Store 结构与关键持久化产物

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any

from voliti_eval.backend_contracts import (
    get_a2ui_module,
    get_experiential_module,
    get_store_contract_module,
)
from voliti_eval.models import (
    DimensionScore,
    Seed,
    StoreDiff,
    StoreDiffEntry,
    StoreSnapshot,
    ToolCallRecord,
    Transcript,
)

CONTRACT_A2UI = "contract_a2ui"
CONTRACT_WITNESS_CARD = "contract_witness_card"
CONTRACT_STORE_SCHEMA = "contract_store_schema"
CONTRACT_ONBOARDING_ARTIFACTS = "contract_onboarding_artifacts"
CONTRACT_GOAL_CHAPTER_ALIGNMENT = "contract_goal_chapter_alignment"
CONTRACT_MEMORY_PROTOCOL = "contract_memory_protocol"

DETERMINISTIC_DIMENSIONS = [
    CONTRACT_A2UI,
    CONTRACT_WITNESS_CARD,
    CONTRACT_STORE_SCHEMA,
    CONTRACT_ONBOARDING_ARTIFACTS,
    CONTRACT_GOAL_CHAPTER_ALIGNMENT,
    CONTRACT_MEMORY_PROTOCOL,
]


def _pass(justification: str, evidence_turns: list[int] | None = None) -> DimensionScore:
    return DimensionScore(
        passed=True,
        justification=justification,
        evidence_turns=evidence_turns or [],
        score_source="deterministic",
    )


def _fail(
    justification: str,
    *,
    severity: str = "critical",
    evidence_turns: list[int] | None = None,
) -> DimensionScore:
    return DimensionScore(
        passed=False,
        justification=justification,
        evidence_turns=evidence_turns or [],
        failure_severity=severity,
        score_source="deterministic",
    )


def _load_json(content: str | None) -> dict[str, Any] | None:
    if not content:
        return None
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def build_store_diff(before: StoreSnapshot, after: StoreSnapshot) -> StoreDiff:
    before_keys = set(before.files)
    after_keys = set(after.files)
    created = sorted(after_keys - before_keys)
    deleted = sorted(before_keys - after_keys)
    updated = sorted(
        key
        for key in before_keys & after_keys
        if before.files[key].content != after.files[key].content
    )

    entries = [
        StoreDiffEntry(
            key=key,
            change_type="created",
            after_content=after.files[key].content,
        )
        for key in created
    ]
    entries.extend(
        StoreDiffEntry(
            key=key,
            change_type="updated",
            before_content=before.files[key].content,
            after_content=after.files[key].content,
        )
        for key in updated
    )
    entries.extend(
        StoreDiffEntry(
            key=key,
            change_type="deleted",
            before_content=before.files[key].content,
        )
        for key in deleted
    )

    return StoreDiff(
        entries=entries,
        created_keys=created,
        updated_keys=updated,
        deleted_keys=deleted,
    )


@dataclass(slots=True)
class A2UIContractGrader:
    dimension_id: str = CONTRACT_A2UI

    def grade(self, seed: Seed, transcript: Transcript) -> DimensionScore:
        a2ui = get_a2ui_module()
        turns_with_panels = [turn for turn in transcript.turns if turn.a2ui_payload]
        if not turns_with_panels and not seed.auditor_policy.a2ui_plan:
            return _pass("该场景未使用 A2UI，也未声明必须发生结构化交互。")
        if not turns_with_panels and seed.auditor_policy.a2ui_plan:
            return _fail("Seed 声明了 A2UI 计划，但对话中没有出现任何结构化面板。")

        for turn in turns_with_panels:
            payload = a2ui.A2UIPayload.model_validate(turn.a2ui_payload)
            response_turn = next(
                (
                    candidate
                    for candidate in transcript.turns
                    if candidate.index > turn.index and candidate.a2ui_response is not None
                ),
                None,
            )
            if response_turn is None:
                return _fail(
                    f"Turn {turn.index} 出现了 A2UI 面板，但没有匹配到用户响应。",
                    evidence_turns=[turn.index],
                )
            response = a2ui.A2UIResponse.model_validate(response_turn.a2ui_response)
            expected_interrupt_id = None
            if turn.a2ui_payload:
                expected_interrupt_id = turn.a2ui_payload.get("metadata", {}).get("interrupt_id")
            try:
                a2ui.validate_a2ui_response(
                    payload,
                    response,
                    expected_interrupt_id=expected_interrupt_id,
                )
            except ValueError as exc:
                return _fail(str(exc), evidence_turns=[turn.index, response_turn.index])

        return _pass(
            f"A2UI 面板与用户响应均通过 backend 契约校验，共 {len(turns_with_panels)} 次。",
            evidence_turns=[turn.index for turn in turns_with_panels],
        )


@dataclass(slots=True)
class WitnessCardContractGrader:
    dimension_id: str = CONTRACT_WITNESS_CARD

    def grade(self, seed: Seed, tool_calls: list[ToolCallRecord]) -> DimensionScore:
        experiential = get_experiential_module()
        card_calls = [call for call in tool_calls if call.name == "compose_witness_card"]
        if not card_calls and not seed.expected_artifacts.witness_required:
            return _pass("该场景未要求 Witness Card，也未发生卡片调用。")
        if not card_calls and seed.expected_artifacts.witness_required:
            return _fail("场景要求 Witness Card，但未捕获到 compose_witness_card 调用。")

        signature = inspect.signature(experiential.compose_witness_card.func)
        allowed_params = set(signature.parameters)
        allowed_types = {
            experiential.ACHIEVEMENT_EXPLICIT,
            experiential.ACHIEVEMENT_IMPLICIT,
            experiential.ACHIEVEMENT_JOURNEY,
        }

        for call in card_calls:
            args = call.arguments or {}
            unknown = sorted(set(args) - allowed_params)
            if unknown:
                return _fail(
                    f"Witness Card 调用了未定义参数：{', '.join(unknown)}。",
                    evidence_turns=[call.turn_index],
                )
            achievement_type = args.get("achievement_type", experiential.ACHIEVEMENT_EXPLICIT)
            if achievement_type not in allowed_types:
                return _fail(
                    f"achievement_type 非法：{achievement_type}",
                    evidence_turns=[call.turn_index],
                )

        return _pass(
            f"Witness Card 调用参数通过契约校验，共 {len(card_calls)} 次。",
            evidence_turns=[call.turn_index for call in card_calls],
        )


@dataclass(slots=True)
class StoreSchemaGrader:
    dimension_id: str = CONTRACT_STORE_SCHEMA

    def grade(self, seed: Seed, store_after: StoreSnapshot, store_diff: StoreDiff) -> DimensionScore:
        store_contract = get_store_contract_module()
        for key in seed.expected_artifacts.forbidden_keys:
            if key in store_after.files:
                return _fail(f"Store 中出现了被禁止的旧路径：{key}")

        legacy_hits: list[str] = []
        for artifact in store_after.files.values():
            parsed = _load_json(artifact.content)
            if artifact.key == store_contract.PROFILE_DASHBOARD_CONFIG_KEY and parsed:
                if _contains_key(parsed, "current_value"):
                    legacy_hits.append(f"{artifact.key}: current_value")
            if artifact.key == store_contract.CHAPTER_CURRENT_KEY and parsed:
                if "identity_statement" in parsed:
                    legacy_hits.append(f"{artifact.key}: identity_statement")

        if legacy_hits:
            return _fail(
                "检测到旧语义字段，当前 eval 不再允许继续依赖它们：" + "; ".join(legacy_hits),
            )

        touched_keys = sorted(set(store_diff.created_keys + store_diff.updated_keys))
        justification = "Store 路径与关键 JSON 结构未发现旧语义字段。"
        if touched_keys:
            justification += f" 本次写入涉及 {', '.join(touched_keys)}。"
        return _pass(justification)


@dataclass(slots=True)
class OnboardingArtifactsGrader:
    dimension_id: str = CONTRACT_ONBOARDING_ARTIFACTS

    def grade(
        self,
        seed: Seed,
        store_after: StoreSnapshot,
        tool_calls: list[ToolCallRecord],
    ) -> DimensionScore:
        if seed.entry_mode not in {"new", "resume", "re_entry"}:
            return _pass("该场景不是 onboarding 入口，不要求 onboarding 最小产物。")

        missing = [key for key in seed.expected_artifacts.required_keys if key not in store_after.files]
        if missing:
            return _fail("缺少 onboarding 必需产物：" + ", ".join(missing))

        profile = store_after.files.get("/profile/context.md")
        if profile is None or "onboarding_complete: true" not in profile.content:
            return _fail("profile/context.md 未将 onboarding_complete 收口为 true。")

        if seed.expected_artifacts.minimum_dataset == "full":
            required_markers = [
                "## Environment",
                "## Identity & Motivation",
                "## Habits",
                "## Rhythm",
                "## Triggers",
            ]
            missing_markers = [marker for marker in required_markers if marker not in profile.content]
            if missing_markers:
                return _fail("完整 onboarding 缺少六维画像章节：" + ", ".join(missing_markers))

        if seed.expected_artifacts.witness_required and not any(
            call.name == "compose_witness_card" for call in tool_calls
        ):
            return _fail("场景要求 onboarding 触发 Witness Card，但未检测到调用。")

        return _pass("Onboarding 最小产物符合当前场景要求。")


@dataclass(slots=True)
class GoalChapterAlignmentGrader:
    dimension_id: str = CONTRACT_GOAL_CHAPTER_ALIGNMENT

    def grade(self, seed: Seed, store_after: StoreSnapshot) -> DimensionScore:
        goal = _load_json(store_after.files.get("/goal/current.json", None).content if "/goal/current.json" in store_after.files else None)
        chapter = _load_json(store_after.files.get("/chapter/current.json", None).content if "/chapter/current.json" in store_after.files else None)
        dashboard = _load_json(store_after.files.get("/profile/dashboardConfig", None).content if "/profile/dashboardConfig" in store_after.files else None)

        if not goal or not chapter or not dashboard:
            return _fail("Goal / Chapter / dashboardConfig 缺一，无法构成当前产品的计划骨架。")

        process_goals = chapter.get("process_goals", [])
        support_metrics = dashboard.get("support_metrics", [])
        if len(process_goals) != 3:
            return _fail("Chapter 必须包含 3 个 Process Goal。")
        if len(support_metrics) != 3:
            return _fail("dashboardConfig.support_metrics 必须与 Process Goals 形成 3:3 对齐。")
        metric_keys = {metric.get("key") for metric in support_metrics}
        process_metric_keys = {goal_item.get("metric_key") for goal_item in process_goals}
        if metric_keys != process_metric_keys:
            return _fail("support_metrics 与 Process Goals 的 metric_key 未形成 1:1 对齐。")
        if chapter.get("goal_id") != goal.get("id"):
            return _fail("Chapter.goal_id 未指向当前 Goal。")
        north_star = dashboard.get("north_star", {})
        north_star_target = goal.get("north_star_target", {})
        if north_star.get("key") != north_star_target.get("key"):
            return _fail("Goal.north_star_target.key 与 dashboardConfig.north_star.key 未对齐。")

        return _pass("Goal、Chapter 与 dashboardConfig 已形成当前产品要求的对齐关系。")


@dataclass(slots=True)
class MemoryProtocolGrader:
    dimension_id: str = CONTRACT_MEMORY_PROTOCOL

    def grade(self, seed: Seed, store_after: StoreSnapshot) -> DimensionScore:
        profile = store_after.files.get("/profile/context.md")
        if profile:
            forbidden_profile_patterns = [
                "Claimed:",
                "Revealed:",
                "## Verified Patterns",
                "## Hypotheses",
                "## Coaching Notes",
                "## Claimed vs Revealed",
            ]
            hits = [pattern for pattern in forbidden_profile_patterns if pattern in profile.content]
            if hits:
                return _fail("profile/context.md 出现了不属于画像层的记忆协议内容：" + ", ".join(hits))

        coach_memory = store_after.files.get("/coach/AGENTS.md")
        if coach_memory:
            required_headers = [
                "## Verified Patterns",
                "## Hypotheses",
                "## Coaching Notes",
                "## Claimed vs Revealed",
            ]
            missing = [header for header in required_headers if header not in coach_memory.content]
            if missing:
                return _fail("coach/AGENTS.md 缺少四分区记忆协议头部：" + ", ".join(missing))

        return _pass("画像层与教练记忆层未发生职责污染。")


def grade_deterministic(
    seed: Seed,
    transcript: Transcript,
    tool_calls: list[ToolCallRecord],
    store_before: StoreSnapshot,
    store_after: StoreSnapshot,
    store_diff: StoreDiff,
) -> dict[str, DimensionScore]:
    scores: dict[str, DimensionScore] = {}

    scores[CONTRACT_STORE_SCHEMA] = StoreSchemaGrader().grade(seed, store_after, store_diff)
    scores[CONTRACT_MEMORY_PROTOCOL] = MemoryProtocolGrader().grade(seed, store_after)

    if seed.entry_mode in {"new", "resume", "re_entry"}:
        scores[CONTRACT_ONBOARDING_ARTIFACTS] = OnboardingArtifactsGrader().grade(
            seed,
            store_after,
            tool_calls,
        )

    if (
        "/goal/current.json" in store_after.files
        or "/chapter/current.json" in store_after.files
        or "/profile/dashboardConfig" in store_after.files
    ):
        scores[CONTRACT_GOAL_CHAPTER_ALIGNMENT] = GoalChapterAlignmentGrader().grade(seed, store_after)

    if seed.auditor_policy.a2ui_plan or any(turn.a2ui_payload for turn in transcript.turns):
        scores[CONTRACT_A2UI] = A2UIContractGrader().grade(seed, transcript)

    if seed.expected_artifacts.witness_required or any(call.name == "compose_witness_card" for call in tool_calls):
        scores[CONTRACT_WITNESS_CARD] = WitnessCardContractGrader().grade(seed, tool_calls)

    return scores


def _contains_key(value: Any, target_key: str) -> bool:
    if isinstance(value, dict):
        if target_key in value:
            return True
        return any(_contains_key(item, target_key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, target_key) for item in value)
    return False
