# ABOUTME: Plan Skill 工具层 · 3 个专用 tool + _execute_plan_tool helper
# ABOUTME: archive-first 写入 + current 自愈读取 + 结构性/状态性 diff 归档判定

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, Any, Callable

from langchain_core.tools import InjectedToolArg, tool
from langgraph.store.base import BaseStore
from pydantic import ValidationError

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
    make_file_value,
    resolve_plan_archive_namespace,
    resolve_user_namespace,
    unwrap_file_value,
)

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
