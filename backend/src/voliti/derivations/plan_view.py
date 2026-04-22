# ABOUTME: Plan Skill 计算层 · PlanDocument → PlanViewRecord 纯函数
# ABOUTME: 派生所有日期驱动字段；指标聚合由 Coach 写 current_week 承担；视觉细节由前端控制

from __future__ import annotations

import logging
from datetime import date
from typing import Literal

from pydantic import BaseModel

from voliti.contracts.markers import MarkerItem
from voliti.contracts.plan import (
    ChapterRecord,
    GoalStatus,
    LinkedLifeSign,
    LinkedMarker,
    PlanDocument,
)

logger = logging.getLogger(__name__)


# ── PlanViewRecord 结构 ───────────────────────────────────────────────


class EventView(BaseModel):
    id: str
    name: str
    event_date: date
    urgency: float         # 0.25 - 1.0 语义权重
    description: str | None = None
    is_past: bool = False
    risk_level: str | None = None


class MapState(BaseModel):
    flag_ratio: float      # 0.0 - 1.0
    events: list[EventView]


class WeekFreshness(BaseModel):
    days_since_update: int
    level: Literal["fresh", "stale", "very_stale"]


class DayTemplateItem(BaseModel):
    label: str             # "meals" / "training" / "sleep"
    value: str
    tooltip: str


class WatchItem(BaseModel):
    kind: Literal["lifesign", "marker"]
    id: str
    name: str
    # marker-only
    event_date: date | None = None
    risk_level: str | None = None
    note: str | None = None
    # lifesign-only
    relevant_chapters: list[int] | None = None
    trigger: str | None = None
    coping_response: str | None = None


class PlanViewRecord(BaseModel):
    plan_phase: Literal["before_start", "in_chapter", "after_end"]
    active_chapter_index: int | None
    week_index: int
    day_progress: tuple[int, int]        # (past_days, total_days)
    active_chapter_day_progress: tuple[int, int]
    days_left_in_chapter: int
    map_state: MapState
    week_view: list[GoalStatus]           # 透传 current_week.goals_status
    week_freshness: WeekFreshness | None
    day_template: list[DayTemplateItem]
    watch_list: list[WatchItem]


# ── 编排 ──────────────────────────────────────────────────────────────


def compute_plan_view(
    plan: PlanDocument,
    today: date,
    markers: dict[str, MarkerItem] | None = None,
    lifesigns: dict[str, dict] | None = None,
) -> PlanViewRecord:
    """由 PlanDocument + today + 展开后的 markers/lifesigns 派生整套视图字段。

    markers / lifesigns 必须由调用方（Briefing / API wrap）一次性 batch 读取后传入，
    避免派生层 N+1 读取。引用缺失时 try-skip + WARN，不抛 KeyError。
    """
    markers = markers or {}
    lifesigns = lifesigns or {}

    plan_phase, active_idx = _compute_plan_phase(plan, today)
    week_index = _compute_week_index(plan, today)
    day_progress = _compute_day_progress(plan, today)
    active_chapter_day_progress = _compute_active_chapter_day_progress(plan, today, active_idx)
    days_left = _compute_days_left_in_chapter(plan, today, active_idx)
    map_state = _compute_map_state(plan, today, markers)
    week_view = _compute_week_view(plan)
    freshness = _compute_week_freshness(plan, today)
    day_template = _compute_day_template(plan, active_idx)
    watch_list = _compute_watch_list(plan, today, markers, lifesigns, active_idx)

    return PlanViewRecord(
        plan_phase=plan_phase,
        active_chapter_index=active_idx,
        week_index=week_index,
        day_progress=day_progress,
        active_chapter_day_progress=active_chapter_day_progress,
        days_left_in_chapter=days_left,
        map_state=map_state,
        week_view=week_view,
        week_freshness=freshness,
        day_template=day_template,
        watch_list=watch_list,
    )


# ── 子函数 ────────────────────────────────────────────────────────────


def _compute_plan_phase(
    plan: PlanDocument, today: date
) -> tuple[Literal["before_start", "in_chapter", "after_end"], int | None]:
    """plan_phase 三态 + active_chapter_index（非 in_chapter 时为 None）。"""
    plan_start = plan.started_at.date()
    if today < plan_start:
        return "before_start", None
    if not plan.chapters:
        return "after_end", None
    last_end = plan.chapters[-1].end_date
    if today > last_end:
        return "after_end", None
    for chapter in plan.chapters:
        # chapters 连续且不重叠（model_validator 保证），start/end 都归属本章
        if chapter.start_date <= today <= chapter.end_date:
            return "in_chapter", chapter.chapter_index
    # 按约束应不可达；fallback
    return "after_end", None


def _compute_week_index(plan: PlanDocument, today: date) -> int:
    """week_index 从 plan.started_at 起按 7 天分段，最小 1。"""
    plan_start = plan.started_at.date()
    total_end = plan.chapters[-1].end_date if plan.chapters else plan.planned_end_at.date()
    clamped = min(today, total_end)
    delta_days = max(0, (clamped - plan_start).days)
    return delta_days // 7 + 1


def _compute_day_progress(plan: PlanDocument, today: date) -> tuple[int, int]:
    plan_start = plan.started_at.date()
    plan_end = plan.planned_end_at.date()
    total_days = max(1, (plan_end - plan_start).days)
    past_days = max(0, min((today - plan_start).days, total_days))
    return past_days, total_days


def _compute_days_left_in_chapter(
    plan: PlanDocument, today: date, active_idx: int | None
) -> int:
    if active_idx is None:
        return 0
    chapter = _find_chapter(plan, active_idx)
    if chapter is None:
        return 0
    return max(0, (chapter.end_date - today).days)


def _compute_active_chapter_day_progress(
    plan: PlanDocument,
    today: date,
    active_idx: int | None,
) -> tuple[int, int]:
    if active_idx is None:
        return 0, 0
    chapter = _find_chapter(plan, active_idx)
    if chapter is None:
        return 0, 0
    total_days = max(1, (chapter.end_date - chapter.start_date).days + 1)
    elapsed_days = max(0, min((today - chapter.start_date).days, total_days - 1)) + 1
    return elapsed_days, total_days


def _compute_map_state(
    plan: PlanDocument,
    today: date,
    markers: dict[str, MarkerItem],
) -> MapState:
    plan_start = plan.started_at.date()
    plan_end = plan.planned_end_at.date()
    total_days = max(1, (plan_end - plan_start).days)
    past_days = (today - plan_start).days
    flag_ratio = max(0.0, min(past_days / total_days, 1.0))

    events: list[EventView] = []
    for mk in plan.linked_markers:
        urgency = _event_urgency(mk.date, today)
        events.append(
            EventView(
                id=mk.id,
                name=mk.name,
                event_date=mk.date,
                urgency=urgency,
                description=markers.get(mk.id).description if mk.id in markers else mk.name,
                is_past=mk.date < today,
                risk_level=markers.get(mk.id).risk_level if mk.id in markers else None,
            )
        )
    return MapState(flag_ratio=flag_ratio, events=events)


def _compute_week_view(plan: PlanDocument) -> list[GoalStatus]:
    """透传 current_week.goals_status；无 current_week 返回空列表。"""
    if plan.current_week is None:
        return []
    return list(plan.current_week.goals_status)


def _compute_week_freshness(plan: PlanDocument, today: date) -> WeekFreshness | None:
    if plan.current_week is None:
        return None
    updated = plan.current_week.updated_at.date()
    days_since = max(0, (today - updated).days)
    if days_since < 1:
        level: Literal["fresh", "stale", "very_stale"] = "fresh"
    elif days_since < 3:
        level = "stale"
    else:
        level = "very_stale"
    return WeekFreshness(days_since_update=days_since, level=level)


def _compute_day_template(
    plan: PlanDocument, active_idx: int | None
) -> list[DayTemplateItem]:
    if active_idx is None:
        return []
    chapter = _find_chapter(plan, active_idx)
    if chapter is None:
        return []
    rhythm = chapter.daily_rhythm
    return [
        DayTemplateItem(label="meals", value=rhythm.meals.value, tooltip=rhythm.meals.tooltip),
        DayTemplateItem(label="training", value=rhythm.training.value, tooltip=rhythm.training.tooltip),
        DayTemplateItem(label="sleep", value=rhythm.sleep.value, tooltip=rhythm.sleep.tooltip),
    ]


def _compute_watch_list(
    plan: PlanDocument,
    today: date,
    markers: dict[str, MarkerItem],
    lifesigns: dict[str, dict],
    active_idx: int | None,
) -> list[WatchItem]:
    """合并 active chapter 相关的 lifesigns + 未来 7 天内的 markers。
    引用完整性 try-skip（GAP 12）：上游 dict 缺失时跳过 + WARN。"""
    watch: list[WatchItem] = []

    # lifesigns 对 active chapter 有效的
    for ls in plan.linked_lifesigns:
        if active_idx is not None and active_idx not in ls.relevant_chapters:
            continue
        item = _resolve_lifesign(ls, lifesigns)
        if item is None:
            continue
        watch.append(item)

    # markers 未来 7 天窗口
    cutoff = _add_days(today, 7)
    for mk in plan.linked_markers:
        if mk.date < today or mk.date > cutoff:
            continue
        item = _resolve_marker(mk, markers)
        if item is None:
            continue
        watch.append(item)

    return watch


def _resolve_lifesign(
    ls: LinkedLifeSign, lifesigns: dict[str, dict]
) -> WatchItem | None:
    data = lifesigns.get(ls.id)
    if data is None:
        logger.warning(
            "plan_view: lifesign id not found in lifesigns dict, skipping",
            extra={"missing_id": ls.id, "ref_type": "lifesign"},
        )
        return None
    return WatchItem(
        kind="lifesign",
        id=ls.id,
        name=ls.name,
        relevant_chapters=list(ls.relevant_chapters),
        trigger=data.get("trigger"),
        coping_response=data.get("coping_response"),
    )


def _resolve_marker(
    mk: LinkedMarker, markers: dict[str, MarkerItem]
) -> WatchItem | None:
    item = markers.get(mk.id)
    if item is None:
        logger.warning(
            "plan_view: marker id not found in markers dict, skipping",
            extra={"missing_id": mk.id, "ref_type": "marker"},
        )
        return None
    return WatchItem(
        kind="marker",
        id=mk.id,
        name=mk.name,
        event_date=mk.date,
        risk_level=item.risk_level,
        note=mk.note,
    )


# ── helpers ───────────────────────────────────────────────────────────


def _find_chapter(plan: PlanDocument, chapter_index: int) -> ChapterRecord | None:
    for c in plan.chapters:
        if c.chapter_index == chapter_index:
            return c
    return None


def _event_urgency(event_date: date, today: date) -> float:
    """语义 urgency：距离今天 0-30 天内线性衰减，最小 0.25。"""
    delta = abs((event_date - today).days)
    return max(0.25, min(1.0 - delta / 30.0, 1.0))


def _add_days(day: date, n: int) -> date:
    from datetime import timedelta

    return day + timedelta(days=n)
