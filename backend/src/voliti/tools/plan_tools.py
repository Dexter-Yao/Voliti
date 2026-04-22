# ABOUTME: Plan Skill 工具层 · 3 个专用 tool + _execute_plan_tool helper
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
from voliti.store_contract import (
    InvalidStoreValueError,
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
    {"target", "chapters", "linked_lifesigns", "linked_markers", "status", "supersedes_plan_id"}
)

# 成功写入后返回 Coach 的摘要前缀
_OK_PREFIX = "Plan 写入成功。"


# ────────────────────────────────────────────────────────────────────────
#  自愈读取
# ────────────────────────────────────────────────────────────────────────


def read_current_plan_with_self_heal(
    store: BaseStore,
    user_namespace: tuple[str, ...],
    archive_namespace: tuple[str, ...],
) -> PlanDocument | None:
    """读 /plan/current.json；若损坏或落后于 archive 最大版本则自愈并重写 current。

    返回：最新权威 PlanDocument；无 plan 时返回 None；全部 archive 损坏时仍返回 current（可能也损坏）或 None。
    """
    current_doc = _try_read_current(store, user_namespace)
    archive_latest = _load_latest_archive(store, archive_namespace)

    if archive_latest is None:
        # 无 archive：可能是新用户或者首次 revise_plan 尚未触发
        return current_doc

    if current_doc is None or archive_latest.version > current_doc.version:
        logger.warning(
            "plan_tools: self-heal triggered, rewriting current from archive",
            extra={
                "current_version": current_doc.version if current_doc else None,
                "archive_max_version": archive_latest.version,
                "plan_id": archive_latest.plan_id,
            },
        )
        _write_current(store, user_namespace, archive_latest)
        return archive_latest

    return current_doc


def _try_read_current(
    store: BaseStore, user_namespace: tuple[str, ...]
) -> PlanDocument | None:
    """尝试读 /plan/current.json；损坏返回 None（不抛），交由自愈逻辑补救。"""
    try:
        item = store.get(user_namespace, PLAN_CURRENT_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "plan_tools: failed to read /plan/current.json",
            extra={"exception_type": type(exc).__name__},
        )
        return None
    if item is None or item.value is None:
        return None
    try:
        text = unwrap_file_value(item.value)
        return PlanDocument.model_validate_json(text)
    except (InvalidStoreValueError, ValidationError, ValueError) as exc:
        logger.warning(
            "plan_tools: /plan/current.json corrupted, will self-heal from archive",
            extra={"exception_type": type(exc).__name__},
        )
        return None


def _load_latest_archive(
    store: BaseStore, archive_namespace: tuple[str, ...]
) -> PlanDocument | None:
    """列 archive namespace 下全部 items，返回 version 最大且合法的 PlanDocument。"""
    try:
        items = store.search(archive_namespace, limit=1000)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "plan_tools: failed to list archive namespace",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    latest: PlanDocument | None = None
    for item in items:
        if item.value is None:
            continue
        try:
            doc = PlanDocument.model_validate_json(unwrap_file_value(item.value))
        except (InvalidStoreValueError, ValidationError, ValueError) as exc:
            logger.error(
                "plan_tools: archive item corrupted, skipping",
                extra={
                    "archive_key": getattr(item, "key", None),
                    "exception_type": type(exc).__name__,
                },
            )
            continue
        if latest is None or doc.version > latest.version:
            latest = doc
    return latest


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
        return exc.message

    # 全量校验（merge_fn 已通过 PlanDocument.model_validate 构造，这里多跑一次以统一错误消息路径）
    try:
        new_plan = PlanDocument.model_validate(new_plan_candidate.model_dump())
    except ValidationError as exc:
        logger.info(
            "plan_tools: plan validation failed",
            extra={"error_count": len(exc.errors())},
        )
        return format_plan_write_error(exc)

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
        return (
            f"{_OK_PREFIX}已归档至 /plan/archive/{archive_key}（version {new_plan.version}）"
            f"；/plan/current.json 已更新。"
        )

    _write_current(store, user_namespace, new_plan, now=now)
    logger.info(
        "plan_tools: narrative update committed",
        extra={"plan_id": new_plan.plan_id, "version": new_plan.version},
    )
    return f"{_OK_PREFIX}已更新 current_week（plan version 保持 {new_plan.version}）。"


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
        merged.append(chapter.model_copy(update=update))
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
            "如需用新 Plan 替换（例如阶段性目标完成后开启新方案），"
            "请在 revise_plan 的 patch 中提供 supersedes_plan_id 与新的 target / chapters。"
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


_PROCESS_GOAL_DAYS_KEY = re.compile(r"^process_goals\.(\d+)\.weekly_target_days$")


def _resolve_numeric_field_value(
    key: str, chapter: ChapterRecord
) -> int | None:
    """Plan Builder 数值字段 key → 当前 chapter 对应值。未知 key 返 None。

    支持 key 集合（C.3.b.1）：
      - weekly_training_count
      - daily_calorie_range.lower / .upper
      - daily_protein_grams_range.lower / .upper
      - process_goals.{N}.weekly_target_days
    """
    if key == "weekly_training_count":
        return chapter.weekly_training_count
    if key == "daily_calorie_range.lower":
        return chapter.daily_calorie_range[0]
    if key == "daily_calorie_range.upper":
        return chapter.daily_calorie_range[1]
    if key == "daily_protein_grams_range.lower":
        return chapter.daily_protein_grams_range[0]
    if key == "daily_protein_grams_range.upper":
        return chapter.daily_protein_grams_range[1]
    match = _PROCESS_GOAL_DAYS_KEY.fullmatch(key)
    if match:
        idx = int(match.group(1))
        if 0 <= idx < len(chapter.process_goals):
            return chapter.process_goals[idx].weekly_target_days
    return None


def _editable_field_to_slider(
    spec: dict[str, Any], chapter: ChapterRecord
) -> dict[str, Any] | None:
    """把 Coach 传入的 editable_field spec 转换为 A2UI slider component。

    spec 非法（kind 不是 slider / min>max / key 未识别 / 当前值取不到）→ 返 None，
    调用方跳过该字段。非致命，便于 Coach 迭代 editable_fields 时不整体失败。
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
    return {
        "kind": "slider",
        "key": key,
        "label": label,
        "min": min_val,
        "max": max_val,
        "step": step,
        "value": initial,
    }


def _readonly_numeric_summary(
    chapter: ChapterRecord, edited_keys: set[str]
) -> str | None:
    """把当前 chapter 中 *未开放编辑* 的数值合并为一行只读展示。三项都被编辑 → None。"""
    segments: list[str] = []
    calorie_edited = (
        "daily_calorie_range.lower" in edited_keys
        and "daily_calorie_range.upper" in edited_keys
    )
    protein_edited = (
        "daily_protein_grams_range.lower" in edited_keys
        and "daily_protein_grams_range.upper" in edited_keys
    )
    wtc_edited = "weekly_training_count" in edited_keys
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
) -> list[dict[str, Any]] | None:
    """按约定顺序生成 Plan Builder overlay 的 A2UI components。

    约定的 key 命名映射（前后端对齐）：
      - "milestone"        → patch.chapters[i].milestone
      - "rhythm.meals"     → patch.chapters[i].daily_rhythm.meals.value
      - "rhythm.training"  → patch.chapters[i].daily_rhythm.training.value
      - "rhythm.sleep"     → patch.chapters[i].daily_rhythm.sleep.value
      - 数值字段通过 editable_fields 参数按 spec 开放（见 _resolve_numeric_field_value）

    editable_fields：Coach 供给的数值字段约束列表，每条 spec:
      { "key": str, "kind": "slider", "min": int, "max": int, "step": int?,
        "label": str, "hint": str? }
    Coach 负责根据用户画像/当前 chapter/numeric-guidelines.md 计算合理的
    min/max，代码只执行。无效 spec 跳过，不阻断整体渲染。

    chapter_index 不匹配任何 chapter → 返回 None，由调用方透传错误给 Coach。
    """
    chapter = next(
        (c for c in plan.chapters if c.chapter_index == chapter_index),
        None,
    )
    if chapter is None:
        return None

    components: list[dict[str, Any]] = [
        {"kind": "text", "text": f"“{plan.overall_narrative}”"},
        {"kind": "text", "text": f"{plan.target_summary}"},
        {
            "kind": "text",
            "text": (
                f"Chapter {chapter.chapter_index} · {chapter.name}\n"
                f"{chapter.why_this_chapter}"
            ),
        },
        {
            "kind": "text_input",
            "key": "milestone",
            "label": "本章目标（可调整文案）",
            "value": chapter.milestone,
        },
        {"kind": "text", "text": "每日节奏"},
        {
            "kind": "text_input",
            "key": "rhythm.meals",
            "label": "三餐",
            "value": chapter.daily_rhythm.meals.value,
        },
        {
            "kind": "text_input",
            "key": "rhythm.training",
            "label": "训练",
            "value": chapter.daily_rhythm.training.value,
        },
        {
            "kind": "text_input",
            "key": "rhythm.sleep",
            "label": "作息",
            "value": chapter.daily_rhythm.sleep.value,
        },
    ]

    edited_keys: set[str] = set()
    numeric_components: list[dict[str, Any]] = []
    for spec in editable_fields or []:
        slider = _editable_field_to_slider(spec, chapter)
        if slider is None:
            continue
        hint = spec.get("hint")
        if isinstance(hint, str) and hint.strip():
            numeric_components.append({"kind": "text", "text": hint.strip()})
        numeric_components.append(slider)
        edited_keys.add(slider["key"])

    if numeric_components:
        components.append({"kind": "text", "text": "数值调整"})
        components.extend(numeric_components)

    readonly_line = _readonly_numeric_summary(chapter, edited_keys)
    if readonly_line is not None:
        components.append({"kind": "text", "text": readonly_line})

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

    new_milestone = data.get("milestone")
    if isinstance(new_milestone, str):
        stripped = new_milestone.strip()
        if stripped and stripped != chapter.milestone:
            chapter_patch["milestone"] = stripped
            changes.append(f"本章目标 → {stripped}")

    rhythm_patch: dict[str, Any] = {}
    rhythm_labels = {"meals": "三餐", "training": "训练", "sleep": "作息"}
    for slot in ("meals", "training", "sleep"):
        raw = data.get(f"rhythm.{slot}")
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
        changes.append(f"{rhythm_labels[slot]} → {stripped}")

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

    new_wtc = _coerce_int(data.get("weekly_training_count"))
    if new_wtc is not None and new_wtc != chapter.weekly_training_count:
        chapter_patch["weekly_training_count"] = new_wtc
        changes.append(f"每周训练次数 → {new_wtc}")

    # 区间字段：lower / upper 单独提交时需合成完整 tuple，另一端保留原值
    for range_key, label_zh, unit in (
        ("daily_calorie_range", "热量区间", "kcal"),
        ("daily_protein_grams_range", "蛋白区间", "g"),
    ):
        current_lower, current_upper = getattr(chapter, range_key)
        new_lower = _coerce_int(data.get(f"{range_key}.lower"))
        new_upper = _coerce_int(data.get(f"{range_key}.upper"))
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
        match = _PROCESS_GOAL_DAYS_KEY.fullmatch(key)
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

    Invalid specs (wrong kind, bad min/max, unknown key, current value unresolvable)
    are silently skipped so a bad field does not block the whole panel.

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
        return (
            "Plan 尚未创建，Plan Builder 无法打开。请先调用 create_plan 建立首份 Plan。"
        )

    resolved_index = chapter_index if chapter_index is not None else plan.chapters[0].chapter_index
    components = _build_plan_builder_components(plan, resolved_index, editable_fields)
    if components is None:
        available = sorted(c.chapter_index for c in plan.chapters)
        return (
            f"chapter_index={resolved_index} 不对应任何已有 chapter；"
            f"可用 chapter_index：{available}。"
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
        return (
            f"Plan Builder 组件构造失败（{exc.error_count()} 处校验错误），"
            "请改走对话方式与用户确认方案。"
        )

    # 直接 interrupt 拿原始 A2UIResponse（绕过 _fan_out_core 的字符串摘要，
    # 让 slider 数值保持整数类型、text 字段里的逗号不被误分隔）
    raw_response = interrupt(payload.model_dump())
    try:
        response = A2UIResponse.model_validate(raw_response)
    except ValidationError:
        return "User response could not be parsed. Ask the user to repeat their answer verbally."
    try:
        validate_a2ui_response(
            payload, response, expected_interrupt_id=current_interrupt_id()
        )
    except ValueError:
        return "User response no longer matches the active panel. Ask the user to try again."

    if response.action == "reject":
        if response.reason:
            return f"User rejected: {response.reason}"
        return "User closed the panel without responding."
    if response.action == "skip":
        return "User acknowledged but chose to skip."

    if not response.data:
        return "User acknowledged the plan as is."

    # 重新读取最新 Plan（panel 期间状态可能已变）作为 submission → patch 的基线
    latest_plan = read_current_plan_with_self_heal(store, user_namespace, archive_namespace)
    if latest_plan is None:
        return "Plan Builder 响应期间 Plan 被清空，未写入。"

    patch_dict, changes = _apply_plan_builder_submission(
        latest_plan, resolved_index, response.data
    )
    if not patch_dict or not changes:
        return "User submitted the plan panel without changes."

    try:
        patch_model = PlanPatch.model_validate(patch_dict)
    except ValidationError as exc:
        logger.info(
            "plan_tools: plan builder patch validation failed",
            extra={"error_count": exc.error_count()},
        )
        return format_plan_write_error(exc)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_revise_plan(current, patch=patch_model, now=now)

    write_result = _execute_plan_tool(
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=_patch_touches_structural(patch_model),
        now=now,
    )
    changes_text = "；".join(changes)
    return f"User edited plan via builder → {changes_text}\n{write_result}"


@tool
def create_plan(
    document: dict[str, Any],
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Create the user's first Plan from a complete PlanDocument.

    Structural write: archives /plan/archive/{plan_id}_v1.json and points /plan/current.json at it.
    Rejected when a Plan already exists — use revise_plan for subsequent changes, or revise_plan with
    supersedes_plan_id when replacing one Plan with a new one.

    System overrides four fields regardless of input: version=1, predecessor_version=null,
    status="active", created_at=revised_at=now (UTC). Other fields must be provided by the caller
    and are validated against PlanDocument's cross-field constraints (chapter timeline continuity,
    chapter_index monotonicity, planned_end_at coverage, process_goal name references, linked
    chapter references).

    Args:
        document: Full PlanDocument as a dict. Must include plan_id, target_summary,
            overall_narrative, started_at, planned_end_at, target, chapters (≥1). Optional:
            linked_lifesigns, linked_markers, current_week, change_summary, supersedes_plan_id.
    """
    now = datetime.now(timezone.utc)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_create_plan(current, document=document, now=now)

    return _execute_plan_tool(
        store=store, config=config, merge_fn=merge, is_structural=True, now=now
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
        store=store, config=config, merge_fn=merge, is_structural=False, now=now
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
        store=store, config=config, merge_fn=merge, is_structural=False, now=now
    )


@tool
def revise_plan(
    patch: dict[str, Any],
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Revise an existing Plan with a partial patch.

    Structural write: if patch touches target / chapters / linked_lifesigns / linked_markers / status / supersedes_plan_id,
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
        return format_plan_write_error(exc)

    is_structural = _patch_touches_structural(patch_model)

    def merge(current: PlanDocument | None) -> PlanDocument:
        return _merge_revise_plan(current, patch=patch_model, now=now)

    return _execute_plan_tool(
        store=store,
        config=config,
        merge_fn=merge,
        is_structural=is_structural,
        now=now,
    )
