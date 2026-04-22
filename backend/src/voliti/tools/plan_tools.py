# ABOUTME: Plan Skill 工具层 · Plan 写入工具与共用执行辅助
# ABOUTME: archive-first 写入 + current 自愈读取 + 结构性/状态性 diff 归档判定

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Annotated, Any, Callable

from langchain_core.tools import InjectedToolArg, tool
from langgraph.store.base import BaseStore
from pydantic import ValidationError

from voliti.a2ui import Component, SliderComponent, TextComponent, TextInputComponent
from voliti.contracts.dashboard import DashboardConfigRecord
from voliti.contracts.plan import (
    ChapterPatch,
    ChapterRecord,
    CurrentWeekRecord,
    GoalStatus,
    PlanDocument,
    PlanPatch,
)
from voliti.contracts.plan_errors import format_plan_write_error
from voliti.plan_runtime import load_current_plan_with_self_heal
from voliti.store_contract import (
    PLAN_CURRENT_KEY,
    PROFILE_DASHBOARD_CONFIG_KEY,
    make_file_value,
    resolve_plan_archive_namespace,
    resolve_user_namespace,
    unwrap_file_value,
)

# target.metric → dashboardConfig.north_star 默认呈现的映射（新用户 / 无 onboarding
# placeholder 时走这套兜底）
_METRIC_NORTH_STAR_DEFAULTS: dict[str, dict[str, Any]] = {
    "weight_kg": {
        "key": "weight_kg",
        "label": "体重",
        "type": "numeric",
        "unit": "kg",
        "delta_direction": "decrease",
    },
}

logger = logging.getLogger(__name__)


# 结构性字段：任一出现在 patch 中即视为结构性修改 → 归档 + version++
_STRUCTURAL_PATCH_FIELDS: frozenset[str] = frozenset(
    {"target", "chapters", "linked_lifesigns", "linked_markers", "status"}
)

# 成功写入后返回 Coach 的摘要前缀
_OK_PREFIX = "Plan 写入成功。"


def _format_tool_result(
    *,
    action: str,
    status: str,
    write_kind: str,
    summary: str,
    plan: PlanDocument | None = None,
    archive_keys: list[str] | None = None,
    warnings: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """把 Planner tool 结果收口为稳定 JSON 字符串。

    `summary` 保留给 Coach / 测试的人类可读文本；其余字段供 agent / harness 稳定分支。
    """
    payload: dict[str, Any] = {
        "action": action,
        "status": status,
        "write_kind": write_kind,
        "summary": summary,
        "plan_id": plan.plan_id if plan is not None else None,
        "version": plan.version if plan is not None else None,
        "archive_keys": archive_keys or [],
        "warnings": warnings or [],
    }
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


# ────────────────────────────────────────────────────────────────────────
#  自愈读取
# ────────────────────────────────────────────────────────────────────────


def read_current_plan_with_self_heal(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
) -> PlanDocument | None:
    """读取当前权威 Plan，并在需要时用 archive 自愈 current 指针。"""
    return load_current_plan_with_self_heal(
        store,
        user_namespace,
        archive_namespace,
        context="plan_tools",
    ).plan


# ────────────────────────────────────────────────────────────────────────
#  写入
# ────────────────────────────────────────────────────────────────────────


def _write_current(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    plan: PlanDocument,
    *,
    now: datetime | None = None,
) -> None:
    content = plan.model_dump_json()
    store.put(user_namespace, PLAN_CURRENT_KEY, make_file_value(content, now=now))


def _write_archive(
    store: BaseStore,
    archive_namespace: tuple[str, ...],
    plan: PlanDocument,
    *,
    now: datetime | None = None,
) -> str:
    """archive-first 权威写入。返回 archive key。"""
    key = f"{plan.plan_id}_v{plan.version}.json"
    content = plan.model_dump_json()
    store.put(archive_namespace, key, make_file_value(content, now=now))
    return key


# ────────────────────────────────────────────────────────────────────────
#  dashboardConfig 同步（D.1）
# ────────────────────────────────────────────────────────────────────────


def _derive_support_metrics_from_plan(plan: PlanDocument) -> list[dict[str, Any]]:
    """从 Plan 第一章的 process_goals 派生 dashboardConfig.support_metrics。

    对齐规则（D.1）：
      · 第一章作为 Mirror 面板的关注源（Plan 入口章节）；后续切章通过 revise_plan 触发重新同步
      · label 直接承接 process_goal.name（用户文本）；key 走 metric_{i} 稳定序号
      · type="ratio"，unit="/{weekly_total_days}"（匹配 goals_status.days_met/days_expected 的语义）
      · order=i 保证 UI 顺序一致
    """
    if not plan.chapters:
        return []
    first = plan.chapters[0]
    return [
        {
            "key": f"metric_{i}",
            "label": pg.name,
            "type": "ratio",
            "unit": f"/{pg.weekly_total_days}",
            "order": i,
        }
        for i, pg in enumerate(first.process_goals)
    ]


def _try_read_dashboard_config(
    store: BaseStore, user_namespace: tuple[str, ...]
) -> dict[str, Any] | None:
    """读 /profile/dashboardConfig；损坏 / 缺失 → None（fail-open，让同步路径重建）。"""
    try:
        item = store.get(user_namespace, PROFILE_DASHBOARD_CONFIG_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "plan_tools: failed to read dashboardConfig",
            extra={"exception_type": type(exc).__name__},
        )
        return None
    if item is None or item.value is None:
        return None
    try:
        text = unwrap_file_value(item.value)
        data = json.loads(text)
        # 结构性校验（挡住明显损坏）；字段扩展由 Pydantic 允许
        DashboardConfigRecord.model_validate(data)
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "plan_tools: dashboardConfig corrupted, will rebuild on next sync",
            extra={"exception_type": type(exc).__name__},
        )
        return None


def _sync_dashboard_config_from_plan(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    plan: PlanDocument,
    *,
    now: datetime | None = None,
) -> None:
    """把 Plan 第一章 process_goals 同步到 dashboardConfig.support_metrics。

    调用时机：任何结构性 Plan 写入（create_plan / revise_plan touching target /
    chapters / linked_*）完成后。状态性写入（current_week 变化）不触发。

    fail-open：sync 异常仅 WARN 日志，不阻塞 Plan 主写入——Plan 是 source of truth，
    dashboardConfig 是派生 surface；下次结构性修改会再次尝试同步。

    保留策略：
      · 已有 dashboardConfig.north_star → 保留（onboarding 期间写的语义优先）
      · 已有 dashboardConfig.user_goal → 保留（同上）
      · support_metrics 整体替换为派生结果（Plan 为 source of truth）
    无 dashboardConfig → 基于 target.metric 查 _METRIC_NORTH_STAR_DEFAULTS 兜底构造。
    """
    existing = _try_read_dashboard_config(store, user_namespace)
    new_metrics = _derive_support_metrics_from_plan(plan)

    if existing is None:
        north_star = _METRIC_NORTH_STAR_DEFAULTS.get(plan.target.metric, {
            "key": plan.target.metric,
            "label": plan.target.metric,
            "type": "numeric",
        })
        new_config: dict[str, Any] = {
            "north_star": north_star,
            "support_metrics": new_metrics,
            "user_goal": plan.target_summary,
        }
    else:
        new_config = dict(existing)
        new_config["support_metrics"] = new_metrics
        if not new_config.get("user_goal"):
            new_config["user_goal"] = plan.target_summary

    try:
        store.put(
            user_namespace,
            PROFILE_DASHBOARD_CONFIG_KEY,
            make_file_value(
                json.dumps(new_config, ensure_ascii=False),
                now=now,
            ),
        )
        logger.info(
            "plan_tools: dashboardConfig.support_metrics synced from plan",
            extra={"plan_id": plan.plan_id, "metric_count": len(new_metrics)},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "plan_tools: dashboard sync write failed (non-blocking)",
            extra={
                "plan_id": plan.plan_id,
                "exception_type": type(exc).__name__,
            },
        )


# ────────────────────────────────────────────────────────────────────────
#  执行流程 helper
# ────────────────────────────────────────────────────────────────────────


class PlanToolRejected(Exception):
    """tool 前置校验拒绝，携带返回给 Coach 的中文错误消息。"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _execute_plan_tool(
    *,
    action: str,
    store: BaseStore,
    config: dict[str, Any],
    merge_fn: Callable[[PlanDocument | None], PlanDocument],
    is_structural: bool,
    now: datetime | None = None,
) -> str:
    """统一执行流程（GAP 22）。

    1. 读 current（含自愈）
    2. merge_fn(current) → new_plan；merge_fn 负责前置校验（plan 不存在 / goal_name 未知 / 空 patch 等）
    3. PlanDocument.model_validate（含 @model_validator 全量跨字段）
    4. 归档判定 + 写入（结构性：archive-first；状态性：就地改）
    5. 返回 Coach 可读摘要
    """
    now = now or datetime.now(timezone.utc)
    user_namespace = resolve_user_namespace(config)
    archive_namespace = resolve_plan_archive_namespace(config)

    current = read_current_plan_with_self_heal(store, user_namespace, archive_namespace)

    try:
        new_plan_candidate = merge_fn(current)
    except PlanToolRejected as exc:
        logger.info(
            "plan_tools: rejected by tool pre-check",
            extra={"reason": exc.message[:120]},
        )
        return _format_tool_result(
            action=action,
            status="rejected",
            write_kind="none",
            summary=exc.message,
            plan=current,
        )

    # 全量校验（merge_fn 已通过 PlanDocument.model_validate 构造，这里多跑一次以统一错误消息路径）
    try:
        new_plan = PlanDocument.model_validate(new_plan_candidate.model_dump())
    except ValidationError as exc:
        logger.info(
            "plan_tools: plan validation failed",
            extra={"error_count": len(exc.errors())},
        )
        return _format_tool_result(
            action=action,
            status="validation_error",
            write_kind="none",
            summary=format_plan_write_error(exc),
            plan=current,
        )

    if is_structural:
        archive_key = _write_archive(store, archive_namespace, new_plan, now=now)
        _write_current(store, user_namespace, new_plan, now=now)
        # dashboardConfig.support_metrics 同步（D.1 · fail-open）——结构性修改后
        # 让 Mirror 面板的指标与 Plan 第一章 process_goals 自动对齐
        _sync_dashboard_config_from_plan(store, user_namespace, new_plan, now=now)
        logger.info(
            "plan_tools: structural revise_plan committed",
            extra={
                "plan_id": new_plan.plan_id,
                "new_version": new_plan.version,
                "archive_key": archive_key,
            },
        )
        return _format_tool_result(
            action=action,
            status="success",
            write_kind="structural",
            summary=(
                f"{_OK_PREFIX}已归档至 /plan/archive/{archive_key}（version {new_plan.version}）"
                f"；/plan/current.json 已更新。"
            ),
            plan=new_plan,
            archive_keys=[archive_key],
        )

    _write_current(store, user_namespace, new_plan, now=now)
    logger.info(
        "plan_tools: narrative update committed",
        extra={"plan_id": new_plan.plan_id, "version": new_plan.version},
    )
    return _format_tool_result(
        action=action,
        status="success",
        write_kind="state",
        summary=f"{_OK_PREFIX}已更新 current_week（plan version 保持 {new_plan.version}）。",
        plan=new_plan,
    )


# ────────────────────────────────────────────────────────────────────────
#  merge helpers
# ────────────────────────────────────────────────────────────────────────


def _iso_now(now: datetime | None = None) -> datetime:
    return now or datetime.now(timezone.utc)


def _init_current_week(now: datetime) -> CurrentWeekRecord:
    """Plan 已存在但 current_week=None 时的自动初始化（GAP 5）。"""
    return CurrentWeekRecord(
        updated_at=now,
        source="coach_inferred",
        goals_status=[],
        highlights=None,
        concerns=None,
    )


def _merge_set_goal_status(
    current: PlanDocument | None,
    *,
    goal_name: str,
    days_met: int,
    days_expected: int | None,
    now: datetime,
) -> PlanDocument:
    if current is None:
        raise PlanToolRejected(
            "Plan 尚未创建，状态性更新无从附加。请先调用 revise_plan 初始化一份完整 Plan。"
        )

    # upsert：若同 goal_name 存在则覆盖，否则新增（GAP 16）
    week = current.current_week or _init_current_week(now)
    new_statuses: list[GoalStatus] = []
    replaced = False
    for st in week.goals_status:
        if st.goal_name == goal_name:
            new_statuses.append(
                GoalStatus(
                    goal_name=goal_name,
                    days_met=days_met,
                    days_expected=days_expected if days_expected is not None else st.days_expected,
                )
            )
            replaced = True
        else:
            new_statuses.append(st)
    if not replaced:
        if days_expected is None:
            days_expected = _infer_days_expected(current, goal_name)
        new_statuses.append(
            GoalStatus(
                goal_name=goal_name,
                days_met=days_met,
                days_expected=days_expected,
            )
        )

    new_week = week.model_copy(update={"updated_at": now, "goals_status": new_statuses})
    return current.model_copy(update={"current_week": new_week, "revised_at": now})


def _infer_days_expected(plan: PlanDocument, goal_name: str) -> int:
    """在 chapters 中找同名 process_goal，取其 weekly_target_days 作为默认。找不到时保底 7。"""
    for chapter in plan.chapters:
        for pg in chapter.process_goals:
            if pg.name == goal_name:
                return pg.weekly_target_days
    return 7   # 若 goal_name 未知，model_validator #4 会拒；此兜底避免构造阶段崩


def _merge_update_week_narrative(
    current: PlanDocument | None,
    *,
    highlights: str | None,
    concerns: str | None,
    now: datetime,
) -> PlanDocument:
    if current is None:
        raise PlanToolRejected(
            "Plan 尚未创建，状态性更新无从附加。请先调用 revise_plan 初始化一份完整 Plan。"
        )
    if highlights is None and concerns is None:
        raise PlanToolRejected(
            "update_week_narrative 至少需要提供 highlights 或 concerns 之一。"
        )

    week = current.current_week or _init_current_week(now)
    update: dict[str, Any] = {"updated_at": now}
    if highlights is not None:
        update["highlights"] = highlights
    if concerns is not None:
        update["concerns"] = concerns
    new_week = week.model_copy(update=update)
    return current.model_copy(update={"current_week": new_week, "revised_at": now})


def _patch_touches_structural(patch: PlanPatch) -> bool:
    dumped = patch.model_dump(exclude_none=True)
    return bool(set(dumped.keys()) & _STRUCTURAL_PATCH_FIELDS)


def _merge_chapters(
    existing: list[ChapterRecord], patches: list[ChapterPatch]
) -> list[ChapterRecord]:
    """按 chapter_index 定位合并（GAP 17）。patches 中未涵盖的 chapter 原样保留。"""
    by_index: dict[int, ChapterPatch] = {p.chapter_index: p for p in patches}
    merged: list[ChapterRecord] = []
    for chapter in existing:
        patch = by_index.pop(chapter.chapter_index, None)
        if patch is None:
            merged.append(chapter)
            continue
        update = patch.model_dump(exclude_none=True, exclude={"chapter_index"})
        merged.append(
            ChapterRecord.model_validate(
                chapter.model_dump(mode="python") | update
            )
        )
    # patches 中指向不存在的 chapter_index → 视为新增，Pydantic 阶段不强制（全量校验会校验 chapter_index 单调性）
    for leftover_index, patch in by_index.items():
        raise PlanToolRejected(
            f"revise_plan 的 chapters 中 chapter_index={leftover_index} 不对应任何已有 chapter；"
            f"若要新增 chapter，请在 patch 里提供完整 chapters 数组（含已有 chapter 的全字段）。"
        )
    return merged


def _merge_create_plan(
    current: PlanDocument | None,
    *,
    document: dict[str, Any],
    now: datetime,
) -> PlanDocument:
    """首次创建 Plan 的合并函数。current 已存在时拒绝；系统强制版本与时间字段。"""
    if current is not None:
        raise PlanToolRejected(
            f"Plan 已存在（plan_id={current.plan_id}，version={current.version}）。"
            "如需修订当前 Plan，请调用 revise_plan；"
            "如需开启下一段新方案，请调用 create_successor_plan。"
        )

    try:
        candidate = PlanDocument.model_validate(document)
    except ValidationError as exc:
        raise PlanToolRejected(format_plan_write_error(exc)) from exc

    return candidate.model_copy(
        update={
            "version": 1,
            "predecessor_version": None,
            "status": "active",
            "created_at": now,
            "revised_at": now,
        }
    )


def _build_successor_plans(
    current: PlanDocument | None,
    *,
    document: dict[str, Any],
    previous_plan_id: str,
    user_confirmed: bool,
    confirmation_text: str,
    now: datetime,
) -> tuple[PlanDocument, PlanDocument]:
    if current is None:
        raise PlanToolRejected(
            "当前没有可切换的 Active Plan。首次建立方案请调用 create_plan。"
        )
    if current.status != "active":
        raise PlanToolRejected(
            f"当前 Plan 状态为 {current.status}，不能作为 successor 起点。"
        )
    if current.plan_id != previous_plan_id:
        raise PlanToolRejected(
            f"previous_plan_id={previous_plan_id} 与当前 Active Plan（{current.plan_id}）不一致。"
        )
    if not user_confirmed or not confirmation_text.strip():
        raise PlanToolRejected(
            "create_successor_plan 需要用户明确确认这是新的方案，并提供确认原话。"
        )

    try:
        candidate = PlanDocument.model_validate(document)
    except ValidationError as exc:
        raise PlanToolRejected(format_plan_write_error(exc)) from exc

    if candidate.plan_id == current.plan_id:
        raise PlanToolRejected(
            "successor plan 必须使用新的 plan_id，不能与当前 Active Plan 相同。"
        )
    if candidate.supersedes_plan_id not in (None, current.plan_id):
        raise PlanToolRejected(
            "document.supersedes_plan_id 若提供，必须为空或等于 previous_plan_id。"
        )

    completed_previous = current.model_copy(
        update={
            "status": "completed",
            "version": current.version + 1,
            "predecessor_version": current.version,
            "revised_at": now,
            "change_summary": (
                f"Coach 与用户确认开启下一段新方案。确认原话：{confirmation_text.strip()}"
            ),
        }
    )
    successor = candidate.model_copy(
        update={
            "version": 1,
            "predecessor_version": None,
            "supersedes_plan_id": current.plan_id,
            "status": "active",
            "created_at": now,
            "revised_at": now,
        }
    )
    return completed_previous, successor


def _merge_revise_plan(
    current: PlanDocument | None,
    *,
    patch: PlanPatch,
    now: datetime,
) -> PlanDocument:
    if current is None:
        raise PlanToolRejected(
            "Plan 尚未创建。首次创建请调用 create_plan，并传入包含完整 target / chapters / "
            "target_summary / overall_narrative / started_at / planned_end_at 等字段的 PlanDocument。"
        )

    dumped = patch.model_dump(exclude_none=True)
    if not dumped:
        raise PlanToolRejected(
            "revise_plan 的 patch 不能为空，请至少指定一个字段。"
        )

    # 仅 change_summary 无其他实质字段 → GAP 18 拒绝
    if set(dumped.keys()) == {"change_summary"}:
        raise PlanToolRejected(
            "revise_plan 仅含 change_summary 无实质字段变化；change_summary 必须伴随实质字段变化。"
        )

    is_structural = _patch_touches_structural(patch)

    update: dict[str, Any] = {"revised_at": now}
    if patch.status is not None:
        update["status"] = patch.status
    if patch.change_summary is not None:
        update["change_summary"] = patch.change_summary
    if patch.target_summary is not None:
        update["target_summary"] = patch.target_summary
    if patch.overall_narrative is not None:
        update["overall_narrative"] = patch.overall_narrative
    if patch.planned_end_at is not None:
        update["planned_end_at"] = patch.planned_end_at
    if patch.target is not None:
        update["target"] = patch.target
    if patch.linked_lifesigns is not None:
        update["linked_lifesigns"] = patch.linked_lifesigns
    if patch.linked_markers is not None:
        update["linked_markers"] = patch.linked_markers
    if patch.chapters is not None:
        update["chapters"] = _merge_chapters(current.chapters, patch.chapters)

    if is_structural:
        update["version"] = current.version + 1
        update["predecessor_version"] = current.version

    return current.model_copy(update=update)


# ────────────────────────────────────────────────────────────────────────
#  Tool 定义
# ────────────────────────────────────────────────────────────────────────


# Plan Builder A2UI component key 单一事实源——_build_plan_builder_components
# 生成 components 时注入、_apply_plan_builder_submission 解析 submit data 时
# 消费、_resolve_numeric_field_value 计算当前值时匹配，三处引用同一套常量
class PlanBuilderKey:
    MILESTONE = "milestone"
    RHYTHM_MEALS = "rhythm.meals"
    RHYTHM_TRAINING = "rhythm.training"
    RHYTHM_SLEEP = "rhythm.sleep"
    WEEKLY_TRAINING_COUNT = "weekly_training_count"
    CALORIE_LOWER = "daily_calorie_range.lower"
    CALORIE_UPPER = "daily_calorie_range.upper"
    PROTEIN_LOWER = "daily_protein_grams_range.lower"
    PROTEIN_UPPER = "daily_protein_grams_range.upper"
    _PROCESS_GOAL_DAYS_RE = re.compile(
        r"^process_goals\.(\d+)\.weekly_target_days$"
    )

    @staticmethod
    def process_goal_days(idx: int) -> str:
        return f"process_goals.{idx}.weekly_target_days"


def _resolve_numeric_field_value(
    key: str, chapter: ChapterRecord
) -> int | None:
    """Plan Builder 数值字段 key → 当前 chapter 对应值。未知 key 返 None。"""
    if key == PlanBuilderKey.WEEKLY_TRAINING_COUNT:
        return chapter.weekly_training_count
    if key == PlanBuilderKey.CALORIE_LOWER:
        return chapter.daily_calorie_range[0]
    if key == PlanBuilderKey.CALORIE_UPPER:
        return chapter.daily_calorie_range[1]
    if key == PlanBuilderKey.PROTEIN_LOWER:
        return chapter.daily_protein_grams_range[0]
    if key == PlanBuilderKey.PROTEIN_UPPER:
        return chapter.daily_protein_grams_range[1]
    match = PlanBuilderKey._PROCESS_GOAL_DAYS_RE.fullmatch(key)
    if match:
        idx = int(match.group(1))
        if 0 <= idx < len(chapter.process_goals):
            return chapter.process_goals[idx].weekly_target_days
    return None


def _validate_editable_field_spec(
    spec: dict[str, Any], chapter: ChapterRecord
) -> str | None:
    """校验单个 editable_field spec；非法时返回给 Coach 的可操作错误。"""
    if spec.get("kind") != "slider":
        return "kind 必须为 'slider'。"

    key = spec.get("key")
    if not isinstance(key, str) or not key:
        return "key 必须是非空字符串。"

    label = spec.get("label")
    if not isinstance(label, str) or not label:
        return f"key={key} 的 label 必须是非空字符串。"

    min_val = spec.get("min")
    max_val = spec.get("max")
    if not isinstance(min_val, int) or not isinstance(max_val, int):
        return f"key={key} 的 min/max 必须是整数。"
    if min_val > max_val:
        return f"key={key} 的 min 不能大于 max。"

    step = spec.get("step", 1)
    if not isinstance(step, int) or step < 1:
        return f"key={key} 的 step 必须是大于等于 1 的整数。"

    hint = spec.get("hint")
    if hint is not None and not isinstance(hint, str):
        return f"key={key} 的 hint 若提供，必须是字符串。"

    current = _resolve_numeric_field_value(key, chapter)
    if current is None:
        return f"key={key} 不属于当前 chapter 可编辑的数值字段。"

    return None


def _collect_invalid_editable_field_specs(
    editable_fields: list[dict[str, Any]] | None,
    chapter: ChapterRecord,
) -> list[str]:
    """收集 editable_fields 的全部非静默错误，避免错误配置进入用户面板。"""
    errors: list[str] = []
    for idx, spec in enumerate(editable_fields or []):
        error = _validate_editable_field_spec(spec, chapter)
        if error is None:
            continue
        errors.append(f"editable_fields[{idx}] {error}")
    return errors


def _editable_field_to_slider(
    spec: dict[str, Any], chapter: ChapterRecord
) -> SliderComponent | None:
    """把 Coach 传入的 editable_field spec 转换为 A2UI SliderComponent。

    本函数假定调用前已完成 spec 校验。保留 None 返回仅作防御式保护，
    避免未来调用方绕过验证时直接抛异常。
    """
    if spec.get("kind") != "slider":
        return None
    key = spec.get("key")
    label = spec.get("label")
    min_val = spec.get("min")
    max_val = spec.get("max")
    step = spec.get("step", 1)
    if not isinstance(key, str) or not key:
        return None
    if not isinstance(label, str) or not label:
        return None
    if not isinstance(min_val, int) or not isinstance(max_val, int):
        return None
    if min_val > max_val:
        return None
    if not isinstance(step, int) or step < 1:
        step = 1

    current = _resolve_numeric_field_value(key, chapter)
    if current is None:
        return None

    # 当前值若在 Coach 给出的区间之外，clamp 到区间内作为 slider 初始值——
    # 这是 slider 的 UI 约束，并非写入数据；最终写入仍由 Pydantic + Coach
    # 给的 min/max 共同守护
    initial = max(min_val, min(int(current), max_val))
    return SliderComponent(
        key=key, label=label, min=min_val, max=max_val, step=step, value=initial
    )


def _readonly_numeric_summary(
    chapter: ChapterRecord, edited_keys: set[str]
) -> str | None:
    """把当前 chapter 中 *未开放编辑* 的数值合并为一行只读展示。三项都被编辑 → None。"""
    segments: list[str] = []
    calorie_edited = (
        PlanBuilderKey.CALORIE_LOWER in edited_keys
        and PlanBuilderKey.CALORIE_UPPER in edited_keys
    )
    protein_edited = (
        PlanBuilderKey.PROTEIN_LOWER in edited_keys
        and PlanBuilderKey.PROTEIN_UPPER in edited_keys
    )
    wtc_edited = PlanBuilderKey.WEEKLY_TRAINING_COUNT in edited_keys
    if not calorie_edited:
        segments.append(
            f"热量 {chapter.daily_calorie_range[0]}-{chapter.daily_calorie_range[1]} kcal"
        )
    if not protein_edited:
        segments.append(
            f"蛋白 {chapter.daily_protein_grams_range[0]}-{chapter.daily_protein_grams_range[1]} g"
        )
    if not wtc_edited:
        segments.append(f"每周训练 {chapter.weekly_training_count} 次")
    if not segments:
        return None
    return " · ".join(segments)


def _build_plan_builder_components(
    plan: PlanDocument,
    chapter_index: int,
    editable_fields: list[dict[str, Any]] | None = None,
) -> list[Component] | None:
    """按约定顺序生成 Plan Builder overlay 的 A2UI components。

    key 映射（前后端对齐）集中在 `PlanBuilderKey` 常量类里。数值字段通过
    editable_fields 参数按 spec 开放（见 `_resolve_numeric_field_value`）。
    Coach 负责根据用户画像/当前 chapter/numeric-guidelines.md 计算合理的
    min/max；调用方需先完成 spec 校验，避免错误配置进入用户面板。

    chapter_index 不匹配任何 chapter → 返回 None，由调用方透传错误给 Coach。
    """
    chapter = next(
        (c for c in plan.chapters if c.chapter_index == chapter_index),
        None,
    )
    if chapter is None:
        return None

    components: list[Component] = [
        TextComponent(text=f"“{plan.overall_narrative}”"),
        TextComponent(text=plan.target_summary),
        TextComponent(
            text=f"Chapter {chapter.chapter_index} · {chapter.name}\n{chapter.why_this_chapter}"
        ),
        TextInputComponent(
            key=PlanBuilderKey.MILESTONE,
            label="本章目标（可调整文案）",
            value=chapter.milestone,
        ),
        TextComponent(text="每日节奏"),
        TextInputComponent(
            key=PlanBuilderKey.RHYTHM_MEALS,
            label="三餐",
            value=chapter.daily_rhythm.meals.value,
        ),
        TextInputComponent(
            key=PlanBuilderKey.RHYTHM_TRAINING,
            label="训练",
            value=chapter.daily_rhythm.training.value,
        ),
        TextInputComponent(
            key=PlanBuilderKey.RHYTHM_SLEEP,
            label="作息",
            value=chapter.daily_rhythm.sleep.value,
        ),
    ]

    edited_keys: set[str] = set()
    numeric_components: list[Component] = []
    for spec in editable_fields or []:
        slider = _editable_field_to_slider(spec, chapter)
        if slider is None:
            continue
        hint = spec.get("hint")
        if isinstance(hint, str) and hint.strip():
            numeric_components.append(TextComponent(text=hint.strip()))
        numeric_components.append(slider)
        edited_keys.add(slider.key)

    if numeric_components:
        components.append(TextComponent(text="数值调整"))
        components.extend(numeric_components)

    readonly_line = _readonly_numeric_summary(chapter, edited_keys)
    if readonly_line is not None:
        components.append(TextComponent(text=readonly_line))

    return components


def _coerce_int(value: Any) -> int | None:
    """把 submission data 里的数值（int / 纯数字 str / float）安全转 int，其他返 None。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not value.is_integer():
            return None
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            try:
                f = float(s)
                return int(f) if f.is_integer() else None
            except ValueError:
                return None
    return None


def _apply_plan_builder_submission(
    plan: PlanDocument,
    chapter_index: int,
    data: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """把 Plan Builder submit data 翻译为 PlanPatch dict + 人类可读的变更清单。

    支持的编辑字段（C.3.a + C.3.b.1）：
      文本 — milestone / rhythm.{meals,training,sleep}
      数值 — weekly_training_count / daily_calorie_range.{lower,upper} /
             daily_protein_grams_range.{lower,upper} /
             process_goals.{N}.weekly_target_days

    其他 key 忽略（防御性，防止协议演进后旧字段残留触发校验错误）。
    返回 ({}，[]) 表示无有效改动。
    """
    chapter = next(
        (c for c in plan.chapters if c.chapter_index == chapter_index),
        None,
    )
    if chapter is None:
        return {}, []

    chapter_patch: dict[str, Any] = {"chapter_index": chapter_index}
    changes: list[str] = []

    new_milestone = data.get(PlanBuilderKey.MILESTONE)
    if isinstance(new_milestone, str):
        stripped = new_milestone.strip()
        if stripped and stripped != chapter.milestone:
            chapter_patch["milestone"] = stripped
            changes.append(f"本章目标 → {stripped}")

    rhythm_patch: dict[str, Any] = {}
    rhythm_slots = {
        "meals": (PlanBuilderKey.RHYTHM_MEALS, "三餐"),
        "training": (PlanBuilderKey.RHYTHM_TRAINING, "训练"),
        "sleep": (PlanBuilderKey.RHYTHM_SLEEP, "作息"),
    }
    for slot, (rhythm_key, label_zh) in rhythm_slots.items():
        raw = data.get(rhythm_key)
        if not isinstance(raw, str):
            continue
        stripped = raw.strip()
        if not stripped:
            continue
        current_value = getattr(chapter.daily_rhythm, slot).value
        if stripped == current_value:
            continue
        rhythm_patch[slot] = {
            "value": stripped,
            "tooltip": getattr(chapter.daily_rhythm, slot).tooltip,
        }
        changes.append(f"{label_zh} → {stripped}")

    if rhythm_patch:
        full_rhythm = {
            "meals": {
                "value": chapter.daily_rhythm.meals.value,
                "tooltip": chapter.daily_rhythm.meals.tooltip,
            },
            "training": {
                "value": chapter.daily_rhythm.training.value,
                "tooltip": chapter.daily_rhythm.training.tooltip,
            },
            "sleep": {
                "value": chapter.daily_rhythm.sleep.value,
                "tooltip": chapter.daily_rhythm.sleep.tooltip,
            },
        }
        full_rhythm.update(rhythm_patch)
        chapter_patch["daily_rhythm"] = full_rhythm

    # 数值字段（C.3.b.1）──────────────────────────────────────────────

    new_wtc = _coerce_int(data.get(PlanBuilderKey.WEEKLY_TRAINING_COUNT))
    if new_wtc is not None and new_wtc != chapter.weekly_training_count:
        chapter_patch["weekly_training_count"] = new_wtc
        changes.append(f"每周训练次数 → {new_wtc}")

    # 区间字段：lower / upper 单独提交时需合成完整 tuple，另一端保留原值
    for range_key, label_zh, unit, lower_key, upper_key in (
        ("daily_calorie_range", "热量区间", "kcal",
         PlanBuilderKey.CALORIE_LOWER, PlanBuilderKey.CALORIE_UPPER),
        ("daily_protein_grams_range", "蛋白区间", "g",
         PlanBuilderKey.PROTEIN_LOWER, PlanBuilderKey.PROTEIN_UPPER),
    ):
        current_lower, current_upper = getattr(chapter, range_key)
        new_lower = _coerce_int(data.get(lower_key))
        new_upper = _coerce_int(data.get(upper_key))
        if new_lower is None and new_upper is None:
            continue
        final_lower = current_lower if new_lower is None else new_lower
        final_upper = current_upper if new_upper is None else new_upper
        if final_lower > final_upper:
            # 用户把 lower 拉过了 upper——维持原值而非出错，Coach 可据日志察觉
            logger.info(
                "plan_tools: plan builder range lower>upper, ignoring",
                extra={"range_key": range_key, "lower": final_lower, "upper": final_upper},
            )
            continue
        if (final_lower, final_upper) == (current_lower, current_upper):
            continue
        chapter_patch[range_key] = [final_lower, final_upper]
        changes.append(f"{label_zh} → {final_lower}-{final_upper} {unit}")

    # process_goals.{N}.weekly_target_days 整体替换 process_goals 列表
    pg_updates: dict[int, int] = {}
    for key, value in data.items():
        match = PlanBuilderKey._PROCESS_GOAL_DAYS_RE.fullmatch(key)
        if not match:
            continue
        idx = int(match.group(1))
        if not (0 <= idx < len(chapter.process_goals)):
            continue
        new_days = _coerce_int(value)
        if new_days is None:
            continue
        if new_days == chapter.process_goals[idx].weekly_target_days:
            continue
        pg_updates[idx] = new_days

    if pg_updates:
        new_goals: list[dict[str, Any]] = []
        for i, pg in enumerate(chapter.process_goals):
            dumped = pg.model_dump()
            if i in pg_updates:
                dumped["weekly_target_days"] = pg_updates[i]
                changes.append(f"{pg.name} 目标 → {pg_updates[i]}/周")
            new_goals.append(dumped)
        chapter_patch["process_goals"] = new_goals

    if len(chapter_patch) <= 1:
        return {}, []

    return {"chapters": [chapter_patch]}, changes


@tool
def fan_out_plan_builder(
    chapter_index: int | None = None,
    editable_fields: list[dict[str, Any]] | None = None,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Open the Plan Builder full-screen overlay so the user can review and lightly
    revise the current Plan's target chapter.

    Editable field families:
      - **Text fields (always open)** — `milestone`, `rhythm.meals` /
        `rhythm.training` / `rhythm.sleep`.
      - **Numeric fields (opt-in via `editable_fields`)** — `weekly_training_count`,
        `daily_calorie_range.{lower,upper}`, `daily_protein_grams_range.{lower,upper}`,
        `process_goals.{N}.weekly_target_days`. You decide the per-field min/max
        based on the user's six-dimension profile, the current chapter's position,
        and `/skills/coach/plan/references/numeric-guidelines.md` — the tool does
        not hard-code ranges. Keep ranges tight enough that any point inside is a
        responsible choice for this user.

    Each editable_field spec is a dict:
      {"key": str, "kind": "slider", "min": int, "max": int,
       "step": int (default 1), "label": str, "hint": str (optional)}
    The `hint` renders as a short line of context above the slider — use it to
    tell the user *why* this range, in the user's own frame ("你自己说过周末时间
    自由度最大"), not as an instruction.

    Invalid specs are rejected before the panel opens. This keeps configuration
    mistakes out of the user-facing surface instead of silently omitting fields.

    Behavior:
      - Reads the current Plan with self-heal; rejects if no Plan exists.
      - Resolves target chapter via `chapter_index` (defaults to the first chapter).
      - Presents a full-screen overlay (`surface="plan-builder"`, `layout="full"`).
      - On submit with real changes → calls revise_plan internally with a minimal
        patch and returns a Chinese summary naming what changed.
      - On empty submit → treats as user acknowledgement, no write.
      - On reject / skip → returns the plain-text reason for Coach to pick up.

    Args:
        chapter_index: 1-based chapter index to open. When None, opens the first
            chapter (most common: the currently active chapter).
        editable_fields: Optional list of numeric field specs. Default None means
            text-only editing.
    """
    from voliti.a2ui import (
        A2UIPayload,
        A2UIResponse,
        current_interrupt_id,
        validate_a2ui_response,
    )
    from langgraph.types import interrupt

    now = datetime.now(timezone.utc)
    user_namespace = resolve_user_namespace(config)
    archive_namespace = resolve_plan_archive_namespace(config)

    plan = read_current_plan_with_self_heal(store, user_namespace, archive_namespace)
    if plan is None:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="rejected",
            write_kind="none",
            summary=(
                "Plan 尚未创建，Plan Builder 无法打开。请先调用 create_plan 建立首份 Plan。"
            ),
        )

    resolved_index = chapter_index if chapter_index is not None else plan.chapters[0].chapter_index
    chapter = next(
        (c for c in plan.chapters if c.chapter_index == resolved_index),
        None,
    )
    if chapter is None:
        available = sorted(c.chapter_index for c in plan.chapters)
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="rejected",
            write_kind="none",
            summary=(
                f"chapter_index={resolved_index} 不对应任何已有 chapter；"
                f"可用 chapter_index：{available}。"
            ),
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )

    invalid_specs = _collect_invalid_editable_field_specs(editable_fields, chapter)
    if invalid_specs:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="validation_error",
            write_kind="none",
            summary="；".join(invalid_specs),
            plan=plan,
            warnings=invalid_specs,
            extra={"requested_chapter_index": resolved_index},
        )

    components = _build_plan_builder_components(plan, resolved_index, editable_fields)
    if components is None:
        available = sorted(c.chapter_index for c in plan.chapters)
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="rejected",
            write_kind="none",
            summary=(
                f"chapter_index={resolved_index} 不对应任何已有 chapter；"
                f"可用 chapter_index：{available}。"
            ),
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )

    try:
        payload = A2UIPayload(
            components=components,
            layout="full",
            metadata={"surface": "plan-builder"},
        )
    except ValidationError as exc:
        logger.info(
            "plan_tools: plan builder payload validation failed",
            extra={"error_count": exc.error_count()},
        )
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="validation_error",
            write_kind="none",
            summary=(
                f"Plan Builder 组件构造失败（{exc.error_count()} 处校验错误），"
                "请改走对话方式与用户确认方案。"
            ),
            plan=plan,
        )

    # 直接 interrupt 拿原始 A2UIResponse（绕过 _fan_out_core 的字符串摘要，
    # 让 slider 数值保持整数类型、text 字段里的逗号不被误分隔）
    raw_response = interrupt(payload.model_dump())
    try:
        response = A2UIResponse.model_validate(raw_response)
    except ValidationError:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="validation_error",
            write_kind="none",
            summary="User response could not be parsed. Ask the user to repeat their answer verbally.",
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )
    try:
        validate_a2ui_response(
            payload, response, expected_interrupt_id=current_interrupt_id()
        )
    except ValueError:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="validation_error",
            write_kind="none",
            summary="User response no longer matches the active panel. Ask the user to try again.",
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )

    if response.action == "reject":
        if response.reason:
            return _format_tool_result(
                action="fan_out_plan_builder",
                status="user_rejected",
                write_kind="none",
                summary=f"User rejected: {response.reason}",
                plan=plan,
                extra={"requested_chapter_index": resolved_index},
            )
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="user_rejected",
            write_kind="none",
            summary="User closed the panel without responding.",
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )
    if response.action == "skip":
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="user_skipped",
            write_kind="none",
            summary="User acknowledged but chose to skip.",
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )

    if not response.data:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="user_acknowledged",
            write_kind="none",
            summary="User acknowledged the plan as is.",
            plan=plan,
            extra={"requested_chapter_index": resolved_index},
        )

    # 重新读取最新 Plan（panel 期间状态可能已变）作为 submission → patch 的基线
    latest_plan = read_current_plan_with_self_heal(store, user_namespace, archive_namespace)
    if latest_plan is None:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="rejected",
            write_kind="none",
            summary="Plan Builder 响应期间 Plan 被清空，未写入。",
            extra={"requested_chapter_index": resolved_index},
        )

    patch_dict, changes = _apply_plan_builder_submission(
        latest_plan, resolved_index, response.data
    )
    if not patch_dict or not changes:
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="no_changes",
            write_kind="none",
            summary="User submitted the plan panel without changes.",
            plan=latest_plan,
            extra={"requested_chapter_index": resolved_index},
        )

    try:
        patch_model = PlanPatch.model_validate(patch_dict)
    except ValidationError as exc:
        logger.info(
            "plan_tools: plan builder patch validation failed",
            extra={"error_count": exc.error_count()},
        )
        return _format_tool_result(
            action="fan_out_plan_builder",
            status="validation_error",
            write_kind="none",
            summary=format_plan_write_error(exc),
            plan=latest_plan,
            extra={"requested_chapter_index": resolved_index},
        )

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_revise_plan(current, patch=patch_model, now=now)

    write_result = _execute_plan_tool(
        action="revise_plan",
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=_patch_touches_structural(patch_model),
        now=now,
    )
    write_payload = json.loads(write_result)
    changes_text = "；".join(changes)
    return _format_tool_result(
        action="fan_out_plan_builder",
        status=write_payload["status"],
        write_kind=write_payload["write_kind"],
        summary=f"User edited plan via builder → {changes_text}；{write_payload['summary']}",
        plan=latest_plan if write_payload["plan_id"] is None else None,
        archive_keys=list(write_payload.get("archive_keys", [])),
        extra={
            "requested_chapter_index": resolved_index,
            "changes": changes,
            "downstream_action": write_payload["action"],
            "downstream_result": write_payload,
            "plan_id": write_payload.get("plan_id"),
            "version": write_payload.get("version"),
        },
    )


@tool
def create_plan(
    document: dict[str, Any],
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Create the user's first Plan from a complete PlanDocument.

    Structural write: archives /plan/archive/{plan_id}_v1.json and points /plan/current.json at it.
    Rejected when a Plan already exists — use revise_plan for subsequent changes, or
    create_successor_plan when starting a confirmed next-stage plan.

    System overrides four fields regardless of input: version=1, predecessor_version=null,
    status="active", created_at=revised_at=now (UTC). Other fields must be provided by the caller
    and are validated against PlanDocument's cross-field constraints (chapter timeline continuity,
    chapter_index monotonicity, planned_end_at coverage, process_goal name references, linked
    chapter references).

    Args:
        document: Full PlanDocument as a dict. Must include plan_id, target_summary,
            overall_narrative, started_at, planned_end_at, target, chapters (≥1). Optional:
            linked_lifesigns, linked_markers, current_week, change_summary.
    """
    now = datetime.now(timezone.utc)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_create_plan(current, document=document, now=now)

    return _execute_plan_tool(
        action="create_plan",
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=True,
        now=now,
    )


@tool
def create_successor_plan(
    document: dict[str, Any],
    previous_plan_id: str,
    user_confirmed: bool,
    confirmation_text: str,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Create a confirmed next-stage Plan and switch /plan/current.json to it.

    This tool is only for explicit "new plan" transitions. It requires both a
    stable previous_plan_id and an explicit user confirmation that this is not a
    revise of the current plan.

    Behavior:
      - Reads the authoritative current plan with self-heal.
      - Archives the previous plan again as a completed snapshot.
      - Archives the successor plan as version 1 with supersedes_plan_id set to
        previous_plan_id.
      - Updates /plan/current.json to point at the successor plan.

    Args:
        document: Full successor PlanDocument as a dict. plan_id must be new.
        previous_plan_id: The current active plan_id being superseded.
        user_confirmed: Must be true only after the user explicitly confirms this
            is a new plan.
        confirmation_text: The user's confirmation wording, stored in the old
            plan's completion summary for traceability.
    """
    now = datetime.now(timezone.utc)
    user_namespace = resolve_user_namespace(config)
    archive_namespace = resolve_plan_archive_namespace(config)
    current = read_current_plan_with_self_heal(store, user_namespace, archive_namespace)

    try:
        completed_previous, successor = _build_successor_plans(
            current,
            document=document,
            previous_plan_id=previous_plan_id,
            user_confirmed=user_confirmed,
            confirmation_text=confirmation_text,
            now=now,
        )
    except PlanToolRejected as exc:
        logger.info(
            "plan_tools: successor rejected by tool pre-check",
            extra={"reason": exc.message[:120]},
        )
        return _format_tool_result(
            action="create_successor_plan",
            status="rejected",
            write_kind="none",
            summary=exc.message,
            plan=current,
            extra={"previous_plan_id": previous_plan_id},
        )

    try:
        completed_previous = PlanDocument.model_validate(
            completed_previous.model_dump()
        )
        successor = PlanDocument.model_validate(successor.model_dump())
    except ValidationError as exc:
        logger.info(
            "plan_tools: successor validation failed",
            extra={"error_count": len(exc.errors())},
        )
        return _format_tool_result(
            action="create_successor_plan",
            status="validation_error",
            write_kind="none",
            summary=format_plan_write_error(exc),
            plan=current,
            extra={"previous_plan_id": previous_plan_id},
        )

    previous_archive_key = _write_archive(
        store, archive_namespace, completed_previous, now=now
    )
    successor_archive_key = _write_archive(
        store, archive_namespace, successor, now=now
    )
    _write_current(store, user_namespace, successor, now=now)
    _sync_dashboard_config_from_plan(store, user_namespace, successor, now=now)
    logger.info(
        "plan_tools: successor plan committed",
        extra={
            "previous_plan_id": completed_previous.plan_id,
            "previous_version": completed_previous.version,
            "successor_plan_id": successor.plan_id,
            "successor_version": successor.version,
        },
    )
    return _format_tool_result(
        action="create_successor_plan",
        status="success",
        write_kind="structural",
        summary=(
            f"{_OK_PREFIX}已切换为新的 Active Plan；旧 Plan 已归档至 "
            f"/plan/archive/{previous_archive_key}；新 Plan 已归档至 "
            f"/plan/archive/{successor_archive_key}，并已写入 /plan/current.json。"
        ),
        plan=successor,
        archive_keys=[previous_archive_key, successor_archive_key],
        extra={
            "previous_plan_id": completed_previous.plan_id,
            "previous_version": completed_previous.version,
            "supersedes_plan_id": successor.supersedes_plan_id,
        },
    )


@tool
def set_goal_status(
    goal_name: str,
    days_met: int,
    days_expected: int | None = None,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Update this week's progress on a single process goal.

    State-only write: updates current_week.goals_status in-place, does not create a new plan version.
    Upserts by goal_name (same name overwrites previous entry, different name appends).

    Args:
        goal_name: The process goal name as defined in some chapter's process_goals (e.g., "每周三次训练").
        days_met: How many days this week the user met the goal (0-7). Coach's holistic judgment, not a raw count.
        days_expected: Optional override for weekly target days this week (defaults to the chapter's weekly_target_days; use only when the user's week is atypical, e.g., traveling).
    """
    now = datetime.now(timezone.utc)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_set_goal_status(
            current,
            goal_name=goal_name,
            days_met=days_met,
            days_expected=days_expected,
            now=now,
        )

    return _execute_plan_tool(
        action="set_goal_status",
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=False,
        now=now,
    )


@tool
def update_week_narrative(
    highlights: str | None = None,
    concerns: str | None = None,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Update the narrative fields of the current week (highlights / concerns).

    State-only write: updates current_week.highlights and/or current_week.concerns.
    At least one of highlights or concerns must be provided; both are free-form Chinese text.

    Args:
        highlights: One-line positive summary of the week (e.g., "周二训练比计划多做了 15 分钟").
        concerns: One-line concern to flag (e.g., "周六深夜又吃了一顿，第二次触发 ls_latenight_craving").
    """
    now = datetime.now(timezone.utc)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_update_week_narrative(
            current, highlights=highlights, concerns=concerns, now=now
        )

    return _execute_plan_tool(
        action="update_week_narrative",
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=False,
        now=now,
    )


@tool
def revise_plan(
    patch: dict[str, Any],
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Revise an existing Plan with a partial patch.

    Structural write: if patch touches target / chapters / linked_lifesigns / linked_markers / status,
    a new archive version is created and /plan/current.json is updated. Otherwise the change is applied in-place.

    patch.chapters accepts a list of ChapterPatch (not full ChapterRecord); each ChapterPatch must include chapter_index as locator key and may include partial fields. Chapters not present in patch.chapters are preserved unchanged.

    Empty patch or patch containing only change_summary is rejected.

    Args:
        patch: Dict conforming to PlanPatch schema. Fields may be any subset of: status / change_summary / target_summary / overall_narrative / planned_end_at / target / chapters (list[ChapterPatch]) / linked_lifesigns / linked_markers.
    """
    now = datetime.now(timezone.utc)

    try:
        patch_model = PlanPatch.model_validate(patch)
    except ValidationError as exc:
        logger.info(
            "plan_tools: revise_plan patch validation failed",
            extra={"error_count": len(exc.errors())},
        )
        return _format_tool_result(
            action="revise_plan",
            status="validation_error",
            write_kind="none",
            summary=format_plan_write_error(exc),
        )

    is_structural = _patch_touches_structural(patch_model)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_revise_plan(current, patch=patch_model, now=now)

    return _execute_plan_tool(
        action="revise_plan",
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=is_structural,
        now=now,
    )
