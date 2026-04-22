# ABOUTME: 派生层 compute_plan_view 单元测试
# ABOUTME: 覆盖 plan_phase 三态、week_freshness 三态、event.urgency 公式、watch_list 过滤与引用缺失 try-skip

from __future__ import annotations

import logging
from datetime import date, timedelta

import pytest

from voliti.contracts.markers import MarkerItem
from voliti.contracts.plan import PlanDocument
from voliti.derivations.plan_view import (
    EventView,
    MapState,
    PlanViewRecord,
    WatchItem,
    WeekFreshness,
    _compute_plan_phase,
    _compute_week_freshness,
    _compute_week_index,
    _event_urgency,
    compute_plan_view,
)


# ── fixture ──────────────────────────────────────────────────────────────


def _baseline_plan_dict() -> dict:
    """合法 PlanDocument dict。start=2026-02-21, chapters=[2/21-3/6, 3/7-4/3, 4/4-4/17]。"""
    return {
        "plan_id": "plan_test_001",
        "status": "active",
        "version": 1,
        "target_summary": "两个月减 10 斤",
        "overall_narrative": "两个月前体重回到一个我自己都不认识的数字。",
        "started_at": "2026-02-21T00:00:00+08:00",
        "planned_end_at": "2026-04-17T23:59:59+08:00",
        "created_at": "2026-02-21T09:15:00+08:00",
        "revised_at": "2026-02-21T09:15:00+08:00",
        "target": {
            "metric": "weight_kg",
            "baseline": 70.0,
            "goal_value": 65.0,
            "duration_weeks": 8,
            "rate_kg_per_week": 0.625,
        },
        "chapters": [
            {
                "chapter_index": 1,
                "name": "立起早餐",
                "why_this_chapter": "建立早餐蛋白锚点。",
                "start_date": "2026-02-21",
                "end_date": "2026-03-06",
                "milestone": "早餐蛋白达标 5/7 持续两周",
                "process_goals": [
                    {
                        "name": "早餐蛋白 25 克以上",
                        "weekly_target_days": 5,
                        "weekly_total_days": 7,
                        "how_to_measure": "Coach 每日评估",
                        "examples": [],
                    }
                ],
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "早中晚各 25g"},
                    "training": {"value": "每周两次", "tooltip": "适应期量小"},
                    "sleep": {"value": "十一点半", "tooltip": "上床时间目标"},
                },
                "daily_calorie_range": [1500, 1800],
                "daily_protein_grams_range": [90, 110],
                "weekly_training_count": 2,
            },
            {
                "chapter_index": 2,
                "name": "训练成锚",
                "why_this_chapter": "让训练变成不用挣扎的惯性。",
                "start_date": "2026-03-07",
                "end_date": "2026-04-03",
                "milestone": "再减 3 公斤",
                "process_goals": [
                    {
                        "name": "每周三次训练",
                        "weekly_target_days": 3,
                        "weekly_total_days": 3,
                        "how_to_measure": "训练日可弹性",
                        "examples": [],
                    }
                ],
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "沿用阶段一"},
                    "training": {"value": "每周三次", "tooltip": "力量优先"},
                    "sleep": {"value": "十一点半", "tooltip": "沿用阶段一"},
                },
                "daily_calorie_range": [1400, 1700],
                "daily_protein_grams_range": [100, 120],
                "weekly_training_count": 3,
            },
            {
                "chapter_index": 3,
                "name": "焊进日常",
                "why_this_chapter": "测试节奏抗压能力。",
                "start_date": "2026-04-04",
                "end_date": "2026-04-17",
                "milestone": "压力测试下守住",
                "process_goals": [
                    {
                        "name": "每周两次训练（保底）",
                        "weekly_target_days": 2,
                        "weekly_total_days": 3,
                        "how_to_measure": "保底即可",
                        "examples": [],
                    }
                ],
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "沿用阶段一"},
                    "training": {"value": "每周两到三次", "tooltip": "压力下保底即可"},
                    "sleep": {"value": "十一点半", "tooltip": "沿用阶段一"},
                },
                "daily_calorie_range": [1500, 1800],
                "daily_protein_grams_range": [90, 110],
                "weekly_training_count": 2,
            },
        ],
        "linked_lifesigns": [
            {"id": "ls_latenight", "name": "深夜食欲", "relevant_chapters": [1, 2, 3]},
            {"id": "ls_weekend_drift", "name": "周末漂移", "relevant_chapters": [2, 3]},
        ],
        "linked_markers": [
            {"id": "mk_trip", "name": "出差", "date": "2026-03-01", "impacts_chapter": 1},
            {"id": "mk_birthday", "name": "生日", "date": "2026-03-15", "impacts_chapter": 2},
            {"id": "mk_holiday", "name": "节日", "date": "2026-04-02", "impacts_chapter": 3},
        ],
        "current_week": {
            "updated_at": "2026-03-15T07:00:00+08:00",
            "source": "coach_inferred",
            "goals_status": [
                {"goal_name": "每周三次训练", "days_met": 2, "days_expected": 3}
            ],
            "highlights": "状态回暖",
            "concerns": None,
        },
    }


@pytest.fixture
def baseline_plan() -> PlanDocument:
    return PlanDocument.model_validate(_baseline_plan_dict())


@pytest.fixture
def markers_dict(baseline_plan: PlanDocument) -> dict[str, MarkerItem]:
    """上游 batch 读取后展开为 id → MarkerItem。"""
    return {
        "mk_trip": MarkerItem(
            id="mk_trip",
            date="2026-03-01T00:00:00+08:00",
            description="三天出差",
            risk_level="high",
            status="upcoming",
            created_at="2026-02-21T10:00:00+08:00",
        ),
        "mk_birthday": MarkerItem(
            id="mk_birthday",
            date="2026-03-15T00:00:00+08:00",
            description="生日聚餐",
            risk_level="medium",
            status="upcoming",
            created_at="2026-02-21T10:00:00+08:00",
        ),
        "mk_holiday": MarkerItem(
            id="mk_holiday",
            date="2026-04-02T00:00:00+08:00",
            description="节日",
            risk_level="low",
            status="upcoming",
            created_at="2026-02-21T10:00:00+08:00",
        ),
    }


@pytest.fixture
def lifesigns_dict() -> dict[str, dict]:
    """上游从 coping_plans_index 解析后的 id → 轻量 dict。"""
    return {
        "ls_latenight": {"id": "ls_latenight", "trigger": "深夜独处"},
        "ls_weekend_drift": {"id": "ls_weekend_drift", "trigger": "周末无计划"},
    }


# ── plan_phase 三态 ──────────────────────────────────────────────────────


def test_plan_phase_before_start(baseline_plan: PlanDocument) -> None:
    phase, idx = _compute_plan_phase(baseline_plan, date(2026, 2, 20))
    assert phase == "before_start"
    assert idx is None


def test_plan_phase_in_chapter_1(baseline_plan: PlanDocument) -> None:
    phase, idx = _compute_plan_phase(baseline_plan, date(2026, 2, 21))
    assert phase == "in_chapter"
    assert idx == 1


def test_plan_phase_in_chapter_2(baseline_plan: PlanDocument) -> None:
    phase, idx = _compute_plan_phase(baseline_plan, date(2026, 3, 20))
    assert phase == "in_chapter"
    assert idx == 2


def test_plan_phase_boundary_day_enters_next_chapter(baseline_plan: PlanDocument) -> None:
    phase, idx = _compute_plan_phase(baseline_plan, date(2026, 3, 7))
    assert phase == "in_chapter"
    assert idx == 2


def test_plan_phase_in_chapter_3(baseline_plan: PlanDocument) -> None:
    phase, idx = _compute_plan_phase(baseline_plan, date(2026, 4, 10))
    assert phase == "in_chapter"
    assert idx == 3


def test_plan_phase_after_end(baseline_plan: PlanDocument) -> None:
    phase, idx = _compute_plan_phase(baseline_plan, date(2026, 4, 18))
    assert phase == "after_end"
    assert idx is None


# ── week_index 公式 ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "today,expected",
    [
        (date(2026, 2, 21), 1),    # day 0
        (date(2026, 2, 27), 1),    # day 6
        (date(2026, 2, 28), 2),    # day 7
        (date(2026, 3, 6), 2),     # day 13 (13 // 7 + 1 = 2)
        (date(2026, 3, 7), 3),     # day 14
        (date(2026, 4, 17), 8),    # 最后一天，day 55 (55 // 7 + 1 = 8)
    ],
)
def test_week_index_formula(
    baseline_plan: PlanDocument, today: date, expected: int
) -> None:
    assert _compute_week_index(baseline_plan, today) == expected


# ── week_freshness 三态 ──────────────────────────────────────────────────


def test_week_freshness_fresh_same_day(baseline_plan: PlanDocument) -> None:
    fr = _compute_week_freshness(baseline_plan, date(2026, 3, 15))
    assert fr is not None
    assert fr.days_since_update == 0
    assert fr.level == "fresh"


def test_week_freshness_stale_two_days(baseline_plan: PlanDocument) -> None:
    fr = _compute_week_freshness(baseline_plan, date(2026, 3, 17))
    assert fr is not None
    assert fr.days_since_update == 2
    assert fr.level == "stale"


def test_week_freshness_very_stale_five_days(baseline_plan: PlanDocument) -> None:
    fr = _compute_week_freshness(baseline_plan, date(2026, 3, 20))
    assert fr is not None
    assert fr.days_since_update == 5
    assert fr.level == "very_stale"


def test_week_freshness_none_when_current_week_missing(
    baseline_plan: PlanDocument,
) -> None:
    data = _baseline_plan_dict()
    data["current_week"] = None
    plan = PlanDocument.model_validate(data)
    assert _compute_week_freshness(plan, date(2026, 3, 15)) is None


# ── event.urgency 公式 ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "event_offset_days,expected",
    [
        (0, 1.0),      # today → 1.0
        (15, 0.5),     # today+15 → 0.5
        (30, 0.25),    # today+30 → clamp 最小 0.25（公式: 1-30/30 = 0 → clamp 0.25）
        (45, 0.25),    # today+45 → 仍 clamp
        (-15, 0.5),    # today-15 → 0.5 (abs)
    ],
)
def test_event_urgency(event_offset_days: int, expected: float) -> None:
    today = date(2026, 3, 1)
    ev_date = today + timedelta(days=event_offset_days)
    assert _event_urgency(ev_date, today) == pytest.approx(expected)


# ── compute_plan_view 编排 ───────────────────────────────────────────────


def test_compute_plan_view_full_pipeline(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    today = date(2026, 3, 15)
    view = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)

    assert isinstance(view, PlanViewRecord)
    assert view.plan_phase == "in_chapter"
    assert view.active_chapter_index == 2
    assert view.week_index == 4     # day 22 / 7 + 1 = 4
    assert view.day_progress[0] == 22
    assert view.days_left_in_chapter == (date(2026, 4, 3) - today).days
    assert isinstance(view.map_state, MapState)
    assert len(view.map_state.events) == 3   # 三个 linked_markers 都生成 EventView
    assert view.week_freshness is not None
    assert view.week_freshness.level == "fresh"
    assert len(view.day_template) == 3       # meals / training / sleep
    # watch_list 应含 active chapter 有效的 lifesigns + 7 天内 markers
    kinds = {(w.kind, w.id) for w in view.watch_list}
    assert ("lifesign", "ls_latenight") in kinds
    assert ("lifesign", "ls_weekend_drift") in kinds


def test_compute_plan_view_pure_function(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    today = date(2026, 3, 15)
    view_1 = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    view_2 = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    assert view_1.model_dump() == view_2.model_dump()


def test_compute_plan_view_today_required(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    """today 必须参数注入（GAP 25 · 禁止内部 datetime.now() 漏入）。"""
    import inspect

    sig = inspect.signature(compute_plan_view)
    today_param = sig.parameters["today"]
    assert today_param.default is inspect.Parameter.empty, (
        "today 必须是 required 参数，禁止默认使用 datetime.now()"
    )


# ── watch_list 过滤 + 引用完整性 ──────────────────────────────────────────


def test_watch_list_filters_inactive_chapter_lifesigns(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    """active_chapter=1 时，ls_weekend_drift (relevant_chapters=[2,3]) 应被过滤。"""
    today = date(2026, 2, 25)   # chapter 1 内
    view = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    lifesign_ids = {w.id for w in view.watch_list if w.kind == "lifesign"}
    assert "ls_latenight" in lifesign_ids
    assert "ls_weekend_drift" not in lifesign_ids


def test_watch_list_filters_markers_outside_7_day_window(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    """today=2026-03-20 时，mk_birthday (3-15) 已过期，mk_holiday (4-2) 在 13 天外，mk_trip (3-1) 早过期。"""
    today = date(2026, 3, 20)
    view = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    marker_ids = {w.id for w in view.watch_list if w.kind == "marker"}
    assert marker_ids == set()   # 没有 7 天内的 marker


def test_watch_list_skips_missing_lifesign_id(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """GAP 12 · lifesign id 不在上游 dict 中 → 跳过 + WARN 日志。"""
    today = date(2026, 2, 25)   # chapter 1，lifesigns 都 relevant
    with caplog.at_level(logging.WARNING, logger="voliti.derivations.plan_view"):
        view = compute_plan_view(baseline_plan, today, markers_dict, {})
    lifesign_ids = {w.id for w in view.watch_list if w.kind == "lifesign"}
    assert lifesign_ids == set()   # 全都 skip
    warnings = [r for r in caplog.records if "lifesign id not found" in r.message]
    assert len(warnings) >= 1
    assert warnings[0].missing_id == "ls_latenight"


def test_watch_list_skips_missing_marker_id(
    baseline_plan: PlanDocument,
    lifesigns_dict: dict[str, dict],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """GAP 12 · marker id 不在上游 dict 中 → 跳过 + WARN 日志。"""
    today = date(2026, 3, 10)   # 离 mk_birthday (3-15) 5 天，在 7 天窗内
    with caplog.at_level(logging.WARNING, logger="voliti.derivations.plan_view"):
        view = compute_plan_view(baseline_plan, today, {}, lifesigns_dict)
    marker_ids = {w.id for w in view.watch_list if w.kind == "marker"}
    assert marker_ids == set()
    warnings = [r for r in caplog.records if "marker id not found" in r.message]
    assert len(warnings) >= 1


# ── day_template + week_view ─────────────────────────────────────────────


def test_day_template_from_active_chapter_rhythm(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    today = date(2026, 2, 25)   # chapter 1
    view = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    labels = [d.label for d in view.day_template]
    assert labels == ["meals", "training", "sleep"]
    training_item = next(d for d in view.day_template if d.label == "training")
    assert training_item.value == "每周两次"


def test_day_template_empty_when_not_in_chapter(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    today = date(2026, 4, 18)   # after_end
    view = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    assert view.day_template == []


def test_week_view_transparent_pass_through(
    baseline_plan: PlanDocument,
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    today = date(2026, 3, 15)
    view = compute_plan_view(baseline_plan, today, markers_dict, lifesigns_dict)
    assert len(view.week_view) == 1
    assert view.week_view[0].goal_name == "每周三次训练"
    assert view.week_view[0].days_met == 2


def test_week_view_empty_when_no_current_week(
    markers_dict: dict[str, MarkerItem],
    lifesigns_dict: dict[str, dict],
) -> None:
    data = _baseline_plan_dict()
    data["current_week"] = None
    plan = PlanDocument.model_validate(data)
    today = date(2026, 3, 15)
    view = compute_plan_view(plan, today, markers_dict, lifesigns_dict)
    assert view.week_view == []
    assert view.week_freshness is None
