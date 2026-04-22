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
    get_plan_contract_module,
    get_store_contract_module,
)
from voliti_eval.dimensions import (
    CONTRACT_A2UI,
    CONTRACT_GOAL_CHAPTER_ALIGNMENT,
    CONTRACT_MEMORY_PROTOCOL,
    CONTRACT_ONBOARDING_ARTIFACTS,
    CONTRACT_STORE_SCHEMA,
    CONTRACT_WITNESS_CARD,
    DETERMINISTIC_DIMENSIONS,
    INTERVENTION_KIND_SELECTION,
    INTERVENTION_METADATA_CORRECTNESS,
    INTERVENTION_SCENE_ANCHOR_PRESENT,
    REFRAME_VERDICT_COMPONENT_PRESENT,
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


@dataclass(frozen=True, slots=True)
class InterventionSpec:
    tool_name: str
    intervention_kind: str
    requires_scene_anchor: bool = False
    requires_reframe_verdict_text: bool = False


_INTERVENTION_SPECS: dict[str, InterventionSpec] = {
    "17_future_self_dialogue_trigger": InterventionSpec(
        tool_name="fan_out_future_self_dialogue",
        intervention_kind="future-self-dialogue",
    ),
    "18_scenario_rehearsal_trigger": InterventionSpec(
        tool_name="fan_out_scenario_rehearsal",
        intervention_kind="scenario-rehearsal",
        requires_scene_anchor=True,
    ),
    "19_metaphor_collaboration_trigger": InterventionSpec(
        tool_name="fan_out_metaphor_collaboration",
        intervention_kind="metaphor-collaboration",
    ),
    "20_cognitive_reframing_trigger": InterventionSpec(
        tool_name="fan_out_cognitive_reframing",
        intervention_kind="cognitive-reframing",
        requires_reframe_verdict_text=True,
    ),
}


def _select_intervention_tool_call(
    tool_calls: list[ToolCallRecord],
    tool_name: str,
) -> ToolCallRecord | None:
    matching_calls = [call for call in tool_calls if call.name == tool_name]
    if not matching_calls:
        return None
    for call in matching_calls:
        components = (call.arguments or {}).get("components")
        if isinstance(components, list) and components:
            return call
    return matching_calls[0]


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
class InterventionContractGrader:
    """评估四个 intervention 场景中可由代码确定的契约项。"""

    def grade(
        self,
        seed: Seed,
        transcript: Transcript,
        tool_calls: list[ToolCallRecord],
    ) -> dict[str, DimensionScore]:
        spec = _INTERVENTION_SPECS.get(seed.id)
        if spec is None:
            return {}

        scores: dict[str, DimensionScore] = {}
        panel_turn = next(
            (
                turn
                for turn in transcript.turns
                if turn.role == "coach"
                and turn.a2ui_payload
                and turn.a2ui_payload.get("metadata", {}).get("surface") == "intervention"
            ),
            None,
        )
        matching_tool_call = _select_intervention_tool_call(tool_calls, spec.tool_name)

        if matching_tool_call is None:
            scores[INTERVENTION_KIND_SELECTION] = _fail(
                f"场景应调用 {spec.tool_name}，但未捕获到对应工具调用。",
            )
        else:
            scores[INTERVENTION_KIND_SELECTION] = _pass(
                f"已调用正确的 intervention 工具：{spec.tool_name}。",
                evidence_turns=[matching_tool_call.turn_index],
            )

        payload: dict[str, Any] | None = None
        evidence_turns: list[int] = []
        inferred_from_tool_contract = False
        if panel_turn is not None:
            payload = panel_turn.a2ui_payload or {}
            evidence_turns = [panel_turn.index]
        elif matching_tool_call is not None:
            components = (matching_tool_call.arguments or {}).get("components")
            if isinstance(components, list):
                payload = {
                    "type": "a2ui",
                    "layout": "full",
                    "metadata": {
                        "surface": "intervention",
                        "intervention_kind": spec.intervention_kind,
                    },
                    "components": components,
                }
                evidence_turns = [matching_tool_call.turn_index]
                inferred_from_tool_contract = True

        if payload is None:
            scores[INTERVENTION_METADATA_CORRECTNESS] = _fail(
                "未捕获到 intervention A2UI 面板，无法验证 metadata 与组件契约。",
            )
            if spec.requires_scene_anchor:
                scores[INTERVENTION_SCENE_ANCHOR_PRESENT] = _fail(
                    "未捕获到 scenario-rehearsal 面板，无法验证场景锚条。",
                )
            if spec.requires_reframe_verdict_text:
                scores[REFRAME_VERDICT_COMPONENT_PRESENT] = _fail(
                    "未捕获到 cognitive-reframing 面板，无法验证 verdict 文本组件。",
                )
            return scores

        metadata = payload.get("metadata", {})
        layout = payload.get("layout")
        components = payload.get("components", [])

        metadata_errors: list[str] = []
        if metadata.get("surface") != "intervention":
            metadata_errors.append("surface 不是 intervention")
        if metadata.get("intervention_kind") != spec.intervention_kind:
            metadata_errors.append(
                f"intervention_kind 应为 {spec.intervention_kind}，实际为 {metadata.get('intervention_kind')}"
            )
        if layout != "full":
            metadata_errors.append(f"layout 应为 full，实际为 {layout}")

        if metadata_errors:
            scores[INTERVENTION_METADATA_CORRECTNESS] = _fail(
                "；".join(metadata_errors),
                evidence_turns=evidence_turns,
            )
        else:
            justification = "intervention metadata 与 layout 均符合工具契约。"
            if inferred_from_tool_contract:
                justification = (
                    f"未捕获 runtime panel；但 {spec.tool_name} 在 backend skill tool 中硬编码了 "
                    "surface=intervention、intervention_kind 与 layout=full，按工具契约判定通过。"
                )
            scores[INTERVENTION_METADATA_CORRECTNESS] = _pass(
                justification,
                evidence_turns=evidence_turns,
            )

        if spec.requires_scene_anchor:
            first_kind = components[0].get("kind") if components else None
            if first_kind != "text":
                scores[INTERVENTION_SCENE_ANCHOR_PRESENT] = _fail(
                    "scenario-rehearsal 的首个组件必须是 TextComponent 场景锚条。",
                    evidence_turns=evidence_turns,
                )
            else:
                scores[INTERVENTION_SCENE_ANCHOR_PRESENT] = _pass(
                    "scenario-rehearsal 面板以 TextComponent 场景锚条开头。",
                    evidence_turns=evidence_turns,
                )

        if spec.requires_reframe_verdict_text:
            protocol_index = next(
                (index for index, component in enumerate(components) if component.get("kind") == "protocol_prompt"),
                None,
            )
            next_kind = (
                components[protocol_index + 1].get("kind")
                if protocol_index is not None and protocol_index + 1 < len(components)
                else None
            )
            if next_kind != "text":
                scores[REFRAME_VERDICT_COMPONENT_PRESENT] = _fail(
                    "cognitive-reframing 必须在 ProtocolPromptComponent 后紧随一个 TextComponent。",
                    evidence_turns=evidence_turns,
                )
            else:
                scores[REFRAME_VERDICT_COMPONENT_PRESENT] = _pass(
                    "cognitive-reframing 已提供紧随 ProtocolPrompt 的 verdict 文本组件。",
                    evidence_turns=evidence_turns,
                )

        return scores


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

        # 旧 Goal / Chapter 独立文件已在 Plan Skill 迁移后废弃
        for legacy_key in ("/goal/current.json", "/chapter/current.json"):
            if legacy_key in store_after.files:
                legacy_hits.append(f"{legacy_key}: 旧独立路径已废弃，Plan Skill 合并为 /plan/current.json")

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
class PlanAlignmentGrader:
    """检验 Plan 内部完整性与 dashboardConfig 的对齐。

    Plan 单文件嵌套后，原 GoalChapterAlignment 的多文件交叉校验被合并到 Plan
    跨字段约束（Pydantic @model_validator 已在 backend 守护）。这里只验证：
    1. /plan/current.json 自身能通过 PlanDocument 结构解析；
    2. 若存在 active chapter 与 dashboardConfig.support_metrics，两者的数量与
       命名保持合理对齐（前端 Mirror 渲染所需）。
    """

    dimension_id: str = CONTRACT_GOAL_CHAPTER_ALIGNMENT

    def grade(self, seed: Seed, store_after: StoreSnapshot) -> DimensionScore:
        plan_artifact = store_after.files.get("/plan/current.json")
        dashboard = _load_json(
            store_after.files.get("/profile/dashboardConfig", None).content
            if "/profile/dashboardConfig" in store_after.files
            else None
        )

        if plan_artifact is None:
            return _fail("/plan/current.json 缺失，无法校验 Plan 结构与 dashboard 对齐。")

        plan_contract = get_plan_contract_module()
        try:
            plan_doc = plan_contract.PlanDocument.model_validate_json(plan_artifact.content)
        except Exception as exc:  # noqa: BLE001
            return _fail(f"/plan/current.json 未通过 PlanDocument 契约校验：{exc}")

        if not plan_doc.chapters:
            return _fail("Plan 至少需要 1 个 Chapter。")

        # 取第一个 chapter 作为 active 参考（派生层的 active 由 today 计算，
        # grader 层不引入 today 噪音，以首章 process_goals 为 metric 对齐基准）
        reference_chapter = plan_doc.chapters[0]
        process_goal_names = {pg.name for pg in reference_chapter.process_goals}

        if dashboard is None:
            # dashboardConfig 在 onboarding 后可能仍为 placeholder，此时允许通过但提示
            return _pass(
                "Plan 结构合法；dashboardConfig 尚未建立（onboarding placeholder 阶段合法）。"
            )

        support_metrics = dashboard.get("support_metrics", [])
        if not support_metrics:
            return _pass(
                f"Plan 结构合法；dashboardConfig.support_metrics 尚未填充，等待 Coach 对齐到 Chapter 1 的 {len(process_goal_names)} 个 Process Goal。"
            )

        metric_labels = {metric.get("label") or metric.get("key") for metric in support_metrics}
        overlap = metric_labels & process_goal_names
        if not overlap:
            return _fail(
                "dashboardConfig.support_metrics 与 Plan Chapter 1 的 Process Goals 未形成任何命名对齐；"
                f"metric labels={sorted(metric_labels)}，process goals={sorted(process_goal_names)}。"
            )

        north_star = dashboard.get("north_star", {})
        if north_star.get("key") and plan_doc.target.metric:
            # 不强制完全一致（"weight" vs "weight_kg" 等命名差异），但需要都存在
            pass

        return _pass("Plan 结构合法，且与 dashboardConfig 保持可用的命名对齐。")


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
    scores.update(InterventionContractGrader().grade(seed, transcript, tool_calls))

    if seed.entry_mode in {"new", "resume", "re_entry"}:
        scores[CONTRACT_ONBOARDING_ARTIFACTS] = OnboardingArtifactsGrader().grade(
            seed,
            store_after,
            tool_calls,
        )

    if _should_grade_plan_alignment(seed, store_after):
        scores[CONTRACT_GOAL_CHAPTER_ALIGNMENT] = PlanAlignmentGrader().grade(seed, store_after)

    if seed.auditor_policy.a2ui_plan or any(turn.a2ui_payload for turn in transcript.turns):
        scores[CONTRACT_A2UI] = A2UIContractGrader().grade(seed, transcript)

    if seed.expected_artifacts.witness_required or any(call.name == "compose_witness_card" for call in tool_calls):
        scores[CONTRACT_WITNESS_CARD] = WitnessCardContractGrader().grade(seed, tool_calls)

    return scores


def _should_grade_plan_alignment(seed: Seed, store_after: StoreSnapshot) -> bool:
    plan_key = "/plan/current.json"
    if plan_key in store_after.files:
        return True
    return plan_key in seed.expected_artifacts.required_keys


def _contains_key(value: Any, target_key: str) -> bool:
    if isinstance(value, dict):
        if target_key in value:
            return True
        return any(_contains_key(item, target_key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, target_key) for item in value)
    return False
