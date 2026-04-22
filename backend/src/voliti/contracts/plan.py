# ABOUTME: /plan/*.json 路径的 Pydantic 契约模型
# ABOUTME: PlanDocument 单文件嵌套快照 + PlanPatch / ChapterPatch 用于 revise_plan

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


# ────────────────────────────────────────────────────────────────────────
#  嵌套值对象
# ────────────────────────────────────────────────────────────────────────


class ProcessGoalRecord(BaseModel):
    """chapter 内可追踪的 process goal。days_met / days_expected 由 Coach 写在 CurrentWeekRecord。"""

    name: str = Field(min_length=2, max_length=60)
    why_this_goal: str | None = Field(default=None, max_length=200)
    weekly_target_days: int = Field(ge=1, le=7)
    weekly_total_days: int = Field(ge=1, le=7, default=7)
    how_to_measure: str = Field(min_length=4, max_length=240)
    examples: list[str] = Field(default_factory=list, max_length=6)


class RhythmItem(BaseModel):
    """daily_rhythm 的单维度（meals / training / sleep）。value 为显示文本，tooltip 为 info icon 详情。"""

    value: str = Field(min_length=1, max_length=40)
    tooltip: str = Field(min_length=4, max_length=200)


class DailyRhythm(BaseModel):
    meals: RhythmItem
    training: RhythmItem
    sleep: RhythmItem


class ChapterRecord(BaseModel):
    """Plan 内的一个阶段，2-4 周为典型长度。"""

    chapter_index: int = Field(ge=1, le=6)
    name: str = Field(min_length=2, max_length=20)
    why_this_chapter: str = Field(min_length=4, max_length=400)
    previous_chapter_id: str | None = None
    revision_of: str | None = None
    start_date: date
    end_date: date
    milestone: str = Field(min_length=4, max_length=200)
    process_goals: list[ProcessGoalRecord] = Field(min_length=1, max_length=4)
    daily_rhythm: DailyRhythm
    daily_calorie_range: tuple[int, int]
    daily_protein_grams_range: tuple[int, int]
    weekly_training_count: int = Field(ge=0, le=7)


class TargetRecord(BaseModel):
    """Plan 整体目标，例如 "两个月减 10 斤"。rate_kg_per_week 上限 1.0kg/周为健康安全阈值。"""

    metric: str
    baseline: float
    goal_value: float
    duration_weeks: int = Field(ge=2, le=26)
    rate_kg_per_week: float = Field(ge=0.1, le=1.0)


class LinkedLifeSign(BaseModel):
    id: str
    name: str
    relevant_chapters: list[int]


class LinkedMarker(BaseModel):
    id: str
    name: str
    date: date
    impacts_chapter: int
    note: str | None = None


class GoalStatus(BaseModel):
    goal_name: str
    days_met: int = Field(ge=0, le=7)
    days_expected: int = Field(ge=1, le=7)


class CurrentWeekRecord(BaseModel):
    """本周状态。极简 schema：仅 Coach 判断的状态字段。
    week_index / active_chapter_index 由 compute_plan_view 派生，不在此处持久化。"""

    updated_at: AwareDatetime
    source: Literal["coach_inferred", "user_reported"]
    goals_status: list[GoalStatus]
    highlights: str | None = None
    concerns: str | None = None


# ────────────────────────────────────────────────────────────────────────
#  聚合根
# ────────────────────────────────────────────────────────────────────────


class PlanDocument(BaseModel):
    """Plan 单文件嵌套快照。与 /plan/current.json 及 /plan/archive/{plan_id}_v{n}.json 一一对应。"""

    # 身份与版本
    plan_id: str
    status: Literal["active", "completed", "paused", "archived"]
    version: int = Field(ge=1)
    predecessor_version: int | None = None
    supersedes_plan_id: str | None = None
    change_summary: str | None = None

    # 叙事与时间
    target_summary: str
    overall_narrative: str = Field(min_length=10, max_length=800)
    started_at: AwareDatetime
    planned_end_at: AwareDatetime
    created_at: AwareDatetime
    revised_at: AwareDatetime

    # 结构
    target: TargetRecord
    chapters: list[ChapterRecord] = Field(min_length=1, max_length=6)
    linked_lifesigns: list[LinkedLifeSign] = Field(default_factory=list)
    linked_markers: list[LinkedMarker] = Field(default_factory=list)
    current_week: CurrentWeekRecord | None = None

    @model_validator(mode="after")
    def _check_cross_field_consistency(self) -> Self:
        """跨字段一致性守护。每条约束的 domain error 消息由 plan_errors.py 生成。"""
        self._check_chapter_timeline_continuous()
        self._check_chapter_index_monotonic()
        self._check_target_covers_chapters()
        self._check_goal_name_references()
        self._check_linked_chapter_references()
        return self

    def _check_chapter_timeline_continuous(self) -> None:
        """约束 1：下一章必须从前一章结束后的次日开始。"""
        for i in range(len(self.chapters) - 1):
            prev_end = self.chapters[i].end_date
            next_start = self.chapters[i + 1].start_date
            expected_next_start = prev_end + timedelta(days=1)
            if next_start != expected_next_start:
                raise ValueError(
                    f"chapters_timeline_discontinuous|i={i}|prev_end={prev_end}|next_start={next_start}|expected_next_start={expected_next_start}"
                )

    def _check_chapter_index_monotonic(self) -> None:
        """约束 2：chapter_index 从 1 开始严格递增。"""
        expected = list(range(1, len(self.chapters) + 1))
        actual = [c.chapter_index for c in self.chapters]
        if actual != expected:
            raise ValueError(
                f"chapters_index_not_monotonic|actual={actual}|expected={expected}"
            )

    def _check_target_covers_chapters(self) -> None:
        """约束 3：planned_end_at 必须覆盖最后一章结束日期。"""
        if not self.chapters:
            return
        last_end = self.chapters[-1].end_date
        plan_end = self.planned_end_at.date()
        if plan_end < last_end:
            raise ValueError(
                f"plan_end_before_last_chapter|plan_end={plan_end}|last_chapter_end={last_end}"
            )

    def _check_goal_name_references(self) -> None:
        """约束 4：current_week.goals_status[i].goal_name 必须在任一 chapter 的 process_goals 中出现。"""
        if self.current_week is None or not self.current_week.goals_status:
            return
        available_names = {
            pg.name for c in self.chapters for pg in c.process_goals
        }
        for status in self.current_week.goals_status:
            if status.goal_name not in available_names:
                raise ValueError(
                    f"goal_name_unknown|requested={status.goal_name}|available={sorted(available_names)}"
                )

    def _check_linked_chapter_references(self) -> None:
        """约束 5 & 6：linked_lifesigns.relevant_chapters 与 linked_markers.impacts_chapter 必须在 chapter_index 范围内。"""
        valid_indices = {c.chapter_index for c in self.chapters}
        max_idx = max(valid_indices) if valid_indices else 0

        for i, ls in enumerate(self.linked_lifesigns):
            out_of_range = [ci for ci in ls.relevant_chapters if ci not in valid_indices]
            if out_of_range:
                raise ValueError(
                    f"linked_lifesign_chapter_out_of_range|index={i}|invalid={out_of_range}|max_idx={max_idx}"
                )

        for i, mk in enumerate(self.linked_markers):
            if mk.impacts_chapter not in valid_indices:
                raise ValueError(
                    f"linked_marker_chapter_out_of_range|index={i}|invalid={mk.impacts_chapter}|max_idx={max_idx}"
                )


# ────────────────────────────────────────────────────────────────────────
#  Patch 模型（供 revise_plan 使用）
# ────────────────────────────────────────────────────────────────────────


class ChapterPatch(BaseModel):
    """chapter 级别 partial：chapter_index 必填作为定位键，其他字段可选。"""

    model_config = ConfigDict(extra="forbid")

    chapter_index: int = Field(ge=1, le=6)
    name: str | None = Field(default=None, min_length=2, max_length=20)
    why_this_chapter: str | None = Field(default=None, min_length=4, max_length=400)
    previous_chapter_id: str | None = None
    revision_of: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    milestone: str | None = Field(default=None, min_length=4, max_length=200)
    process_goals: list[ProcessGoalRecord] | None = None
    daily_rhythm: DailyRhythm | None = None
    daily_calorie_range: tuple[int, int] | None = None
    daily_protein_grams_range: tuple[int, int] | None = None
    weekly_training_count: int | None = Field(default=None, ge=0, le=7)


class PlanPatch(BaseModel):
    """部分修订。chapters 按 chapter_index 定位合并，不是整体替换。
    合并后由 revise_plan tool 再跑 PlanDocument.model_validate 做全量校验。"""

    model_config = ConfigDict(extra="forbid")

    status: Literal["active", "completed", "paused", "archived"] | None = None
    change_summary: str | None = None
    target_summary: str | None = None
    overall_narrative: str | None = None
    planned_end_at: AwareDatetime | None = None

    target: TargetRecord | None = None
    chapters: list[ChapterPatch] | None = None
    linked_lifesigns: list[LinkedLifeSign] | None = None
    linked_markers: list[LinkedMarker] | None = None

    # plan_id / version / 时间 metadata 不在 patch 中，由系统维护
