# ABOUTME: Plan 契约模型单元测试
# ABOUTME: 覆盖字段约束、ISO 日期守护、6 条跨字段校验、PlanPatch / ChapterPatch、domain error 消息

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from voliti.contracts.plan import (
    ChapterPatch,
    PlanDocument,
    PlanPatch,
)
from voliti.contracts.plan_errors import format_plan_write_error


# ── fixtures ──────────────────────────────────────────────────────────────


def _baseline_plan_dict() -> dict:
    """合法 PlanDocument dict：三章节、current_week 有 goals_status、带 linked_lifesigns + linked_markers。"""
    return {
        "plan_id": "plan_test_001",
        "status": "active",
        "version": 1,
        "predecessor_version": None,
        "supersedes_plan_id": None,
        "change_summary": None,
        "target_summary": "两个月减 10 斤",
        "overall_narrative": "两个月前体重回到一个我自己都不认识的数字，我想用两个月看看能不能把它掰回来。",
        "started_at": "2026-02-21T00:00:00+08:00",
        "planned_end_at": "2026-04-17T00:00:00+08:00",
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
                "why_this_chapter": "建立早餐蛋白锚点，前两周不追求体重变化。",
                "start_date": "2026-02-21",
                "end_date": "2026-03-06",
                "milestone": "早餐蛋白达标 5/7 持续两周",
                "process_goals": [
                    {
                        "name": "早餐蛋白 25 克以上",
                        "weekly_target_days": 5,
                        "weekly_total_days": 7,
                        "how_to_measure": "Coach 每日评估蛋白种类与份量",
                        "examples": ["一杯牛奶 + 一个鸡蛋"],
                    }
                ],
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "早中晚各 25g，分散比集中更稳血糖"},
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
                "why_this_chapter": "让每周三次训练从心情变成不用挣扎的惯性。",
                "start_date": "2026-03-07",
                "end_date": "2026-04-03",
                "milestone": "再减 3 公斤，训练变成日常",
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
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "沿用阶段一节奏"},
                    "training": {"value": "每周三次", "tooltip": "力量优先，每次 30-45 分钟"},
                    "sleep": {"value": "十一点半", "tooltip": "沿用阶段一节奏"},
                },
                "daily_calorie_range": [1400, 1700],
                "daily_protein_grams_range": [100, 120],
                "weekly_training_count": 3,
            },
            {
                "chapter_index": 3,
                "name": "焊进日常",
                "why_this_chapter": "测试节奏的抗压能力。",
                "start_date": "2026-04-04",
                "end_date": "2026-04-17",
                "milestone": "压力测试下节奏守住即毕业",
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
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "沿用阶段一节奏"},
                    "training": {"value": "每周两到三次", "tooltip": "压力下保底即可"},
                    "sleep": {"value": "十一点半", "tooltip": "沿用阶段一节奏"},
                },
                "daily_calorie_range": [1500, 1800],
                "daily_protein_grams_range": [90, 110],
                "weekly_training_count": 2,
            },
        ],
        "linked_lifesigns": [
            {"id": "ls_latenight_craving", "name": "深夜食欲", "relevant_chapters": [1, 2, 3]}
        ],
        "linked_markers": [
            {
                "id": "mk_2026_03_01_trip",
                "name": "出差",
                "date": "2026-03-01",
                "impacts_chapter": 2,
                "note": "三天出差",
            }
        ],
        "current_week": {
            "updated_at": "2026-03-15T07:00:00+08:00",
            "source": "coach_inferred",
            "goals_status": [
                {"goal_name": "每周三次训练", "days_met": 2, "days_expected": 3}
            ],
            "highlights": "周二训练状态回暖",
            "concerns": None,
        },
    }


# ── Happy path ────────────────────────────────────────────────────────────


def test_plan_document_accepts_baseline_fixture() -> None:
    doc = PlanDocument.model_validate(_baseline_plan_dict())
    assert doc.plan_id == "plan_test_001"
    assert doc.version == 1
    assert len(doc.chapters) == 3
    assert doc.chapters[0].daily_calorie_range == (1500, 1800)
    assert doc.current_week is not None


def test_plan_document_accepts_minimal_single_chapter() -> None:
    """chapters 最少 1 个（方案 F 放宽自 min_length=2 → 1）。"""
    data = _baseline_plan_dict()
    only = data["chapters"][0]
    only["end_date"] = "2026-04-17"   # 覆盖整个 plan
    data["chapters"] = [only]
    data["current_week"] = None        # 避免跨字段约束 4
    data["linked_lifesigns"] = [
        {"id": "ls_x", "name": "x", "relevant_chapters": [1]}
    ]
    data["linked_markers"][0]["impacts_chapter"] = 1
    doc = PlanDocument.model_validate(data)
    assert len(doc.chapters) == 1


def test_plan_document_accepts_null_current_week() -> None:
    data = _baseline_plan_dict()
    data["current_week"] = None
    doc = PlanDocument.model_validate(data)
    assert doc.current_week is None


# ── 字段级负例 ────────────────────────────────────────────────────────────


def test_rate_kg_per_week_above_safe_threshold_rejected() -> None:
    data = _baseline_plan_dict()
    data["target"]["rate_kg_per_week"] = 1.5   # 超过健康上限 1.0
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    assert any("rate_kg_per_week" in str(e["loc"]) for e in exc_info.value.errors())


def test_chapters_empty_rejected() -> None:
    data = _baseline_plan_dict()
    data["chapters"] = []
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


def test_chapters_too_many_rejected() -> None:
    data = _baseline_plan_dict()
    one = data["chapters"][0]
    data["chapters"] = [
        {**copy.deepcopy(one), "chapter_index": i}
        for i in range(1, 8)   # 7 个超过 max 6
    ]
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


def test_goal_status_days_met_out_of_range_rejected() -> None:
    data = _baseline_plan_dict()
    data["current_week"]["goals_status"][0]["days_met"] = 10
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


# ── ISO 日期格式（GAP 11 · Pydantic 层 fail-closed）──────────────────────


def test_chapter_start_date_rejects_non_iso_string() -> None:
    data = _baseline_plan_dict()
    data["chapters"][0]["start_date"] = "2026/02/21"   # 非 ISO 格式
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


def test_plan_started_at_rejects_non_iso_datetime() -> None:
    data = _baseline_plan_dict()
    data["started_at"] = "not-a-datetime"
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


def test_plan_started_at_rejects_naive_datetime() -> None:
    data = _baseline_plan_dict()
    data["started_at"] = "2026-02-21T00:00:00"   # 无时区，AwareDatetime 应拒
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


def test_linked_marker_date_rejects_non_iso() -> None:
    data = _baseline_plan_dict()
    data["linked_markers"][0]["date"] = "Mar 1 2026"
    with pytest.raises(ValidationError):
        PlanDocument.model_validate(data)


# ── 跨字段约束 6 条（@model_validator）───────────────────────────────────


def test_cross_field_chapter_timeline_not_continuous() -> None:
    data = _baseline_plan_dict()
    data["chapters"][0]["end_date"] = "2026-03-05"   # chapters[1].start_date = 2026-03-07，出现 gap
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "不连续" in msg
    assert "chapters[0].end_date" in msg


def test_cross_field_chapter_timeline_rejects_same_day_overlap() -> None:
    data = _baseline_plan_dict()
    data["chapters"][1]["start_date"] = "2026-03-06"
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "不连续" in msg


def test_cross_field_chapter_index_not_monotonic() -> None:
    data = _baseline_plan_dict()
    data["chapters"][1]["chapter_index"] = 4   # 1, 4, 3 不单调
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "chapter_index 序列" in msg


def test_cross_field_plan_end_before_last_chapter() -> None:
    data = _baseline_plan_dict()
    data["planned_end_at"] = "2026-04-10T00:00:00+08:00"   # 早于 chapters[-1].end_date = 2026-04-17
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "planned_end_at" in msg
    assert "早于最后一章" in msg


def test_cross_field_goal_name_unknown() -> None:
    data = _baseline_plan_dict()
    data["current_week"]["goals_status"][0]["goal_name"] = "不存在的目标"
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "goal_name" in msg
    assert "不存在的目标" in msg
    assert "可用 goal_name" in msg


def test_cross_field_linked_lifesign_chapter_out_of_range() -> None:
    data = _baseline_plan_dict()
    data["linked_lifesigns"][0]["relevant_chapters"] = [1, 5]   # 5 超过 chapters 数量
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "linked_lifesigns" in msg
    assert "有效范围" in msg


def test_cross_field_linked_marker_chapter_out_of_range() -> None:
    data = _baseline_plan_dict()
    data["linked_markers"][0]["impacts_chapter"] = 10
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert "impacts_chapter" in msg


def test_cross_field_goal_name_references_chapter_from_any_chapter() -> None:
    """goal_name 可引用任一 chapter 的 process_goal（非仅 active chapter）。"""
    data = _baseline_plan_dict()
    # chapter 1 有 "早餐蛋白 25 克以上"；current_week goals_status 引用它应该 OK
    data["current_week"]["goals_status"] = [
        {"goal_name": "早餐蛋白 25 克以上", "days_met": 3, "days_expected": 5}
    ]
    PlanDocument.model_validate(data)   # 不应 raise


# ── PlanPatch / ChapterPatch ─────────────────────────────────────────────


def test_plan_patch_accepts_single_field() -> None:
    patch = PlanPatch.model_validate({"change_summary": "微调说明"})
    assert patch.change_summary == "微调说明"
    assert patch.target is None
    assert patch.chapters is None


def test_plan_patch_accepts_chapter_patch_list() -> None:
    patch = PlanPatch.model_validate(
        {
            "chapters": [
                {"chapter_index": 2, "milestone": "新里程碑"}
            ]
        }
    )
    assert patch.chapters is not None
    assert len(patch.chapters) == 1
    assert patch.chapters[0].chapter_index == 2
    assert patch.chapters[0].milestone == "新里程碑"
    assert patch.chapters[0].name is None


def test_plan_patch_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        PlanPatch.model_validate({"supersedes_plan_id": "plan_old"})
    assert "supersedes_plan_id" in str(exc_info.value)


def test_chapter_patch_requires_chapter_index() -> None:
    with pytest.raises(ValidationError):
        ChapterPatch.model_validate({"milestone": "foo"})


def test_chapter_patch_rejects_invalid_chapter_index() -> None:
    with pytest.raises(ValidationError):
        ChapterPatch.model_validate({"chapter_index": 10, "milestone": "x"})


# ── 错误消息 formatter ───────────────────────────────────────────────────


def test_format_plan_write_error_renders_actionable_prefix() -> None:
    data = _baseline_plan_dict()
    data["chapters"][0]["end_date"] = "2026-03-05"   # 造一个跨字段错误
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    assert msg.startswith("Plan 校验未通过，未写入。")
    assert "字段：" in msg
    assert "问题：" in msg
    assert "修复：" in msg


def test_format_plan_write_error_fallback_for_field_errors() -> None:
    data = _baseline_plan_dict()
    data["target"]["rate_kg_per_week"] = 2.0   # 字段级错误
    with pytest.raises(ValidationError) as exc_info:
        PlanDocument.model_validate(data)
    msg = format_plan_write_error(exc_info.value)
    # fallback 渲染字段路径
    assert "target" in msg
    assert "rate_kg_per_week" in msg
