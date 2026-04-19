# ABOUTME: Store 强格式 JSON 路径的 Pydantic 契约模型
# ABOUTME: 对应 docs/05_Runtime_Contracts.md 中 authoritative_semantic 分类的 JSON 路径

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Final, Literal


# ── /chapter/current.json ──────────────────────────────────────────────────────

class ProcessGoalRecord(BaseModel):
    key: str
    description: str
    target: str
    metric_key: str


class ChapterRecord(BaseModel):
    id: str | None = None
    chapter_number: int = Field(ge=1, le=99)
    goal_id: str
    title: str = Field(min_length=2, max_length=60)
    milestone: str = Field(min_length=4, max_length=200)
    start_date: str        # ISO-8601，保持字符串避免时区处理复杂度
    planned_end_date: str
    status: str = "active"
    process_goals: list[ProcessGoalRecord] = Field(min_length=1, max_length=5)


# ── /goal/current.json ─────────────────────────────────────────────────────────

class NorthStarTarget(BaseModel):
    key: str
    baseline: float
    target: float
    unit: str


class GoalRecord(BaseModel):
    id: str
    description: str = Field(min_length=4, max_length=200)
    north_star_target: NorthStarTarget
    start_date: str
    target_date: str
    status: str = "active"


# ── /timeline/markers.json ─────────────────────────────────────────────────────

class MarkerItem(BaseModel):
    id: str
    date: str
    timezone: str = "Asia/Shanghai"
    description: str = Field(min_length=2, max_length=100)
    risk_level: Literal["low", "medium", "high"] = "medium"
    status: Literal["upcoming", "passed", "cancelled"] = "upcoming"
    created_at: str
    linked_lifesign: str | None = None


class MarkersRecord(BaseModel):
    markers: list[MarkerItem]


# ── /profile/dashboardConfig ───────────────────────────────────────────────────

class NorthStarConfig(BaseModel):
    key: str
    label: str
    type: str
    unit: str | None = None
    delta_direction: str | None = None


class SupportMetric(BaseModel):
    key: str
    label: str
    type: str
    unit: str | None = None
    order: int | None = None


class DashboardConfigRecord(BaseModel):
    north_star: NorthStarConfig
    support_metrics: list[SupportMetric]
    user_goal: str | None = None


# 提供给 Coach 的最小合法格式示例；与模型类直接绑定，避免字符串键在重命名时静默漂移
CANONICAL_EXAMPLES: Final[dict[type[BaseModel], str]] = {
    ChapterRecord: (
        '{"chapter_number":1,"goal_id":"goal_001","title":"建立饮食节奏",'
        '"milestone":"蛋白质达标率≥70%","start_date":"2026-04-19T00:00:00Z",'
        '"planned_end_date":"2026-05-19T00:00:00Z",'
        '"process_goals":[{"key":"pg_001","description":"每日记录三餐",'
        '"target":"5/7天","metric_key":"meal_log_days"}]}'
    ),
    GoalRecord: (
        '{"id":"goal_001","description":"12周从75kg减至70kg",'
        '"north_star_target":{"key":"weight_trend","baseline":75,"target":70,"unit":"kg"},'
        '"start_date":"2026-04-19T00:00:00Z","target_date":"2026-07-12T00:00:00Z","status":"active"}'
    ),
    MarkersRecord: (
        '{"markers":[{"id":"mk_001","date":"2026-04-20T00:00:00+08:00",'
        '"description":"出差上海","risk_level":"high","status":"upcoming",'
        '"created_at":"2026-04-19T10:00:00Z"}]}'
    ),
    DashboardConfigRecord: (
        '{"north_star":{"key":"weight_trend","label":"体重趋势","type":"numeric","unit":"kg"},'
        '"support_metrics":[{"key":"protein_days","label":"蛋白质达标天","type":"count"}]}'
    ),
}
