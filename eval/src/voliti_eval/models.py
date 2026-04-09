# ABOUTME: 评估模块核心 Pydantic 数据模型
# ABOUTME: 定义 Seed、Turn、Transcript、ScoreCard、EvalResult 等结构

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Seed — 评估场景定义（从 YAML 加载）
# ---------------------------------------------------------------------------


class Persona(BaseModel):
    """模拟用户的角色设定。"""

    name: str
    background: str
    personality: str
    language: Literal["zh", "en"] = "zh"


class CopingPlan(BaseModel):
    """LifeSign 预案定义，对应 Coach 的 /user/coping_plans/ 格式。"""

    id: str
    trigger: dict[str, Any]
    action: str
    status: str = "active"
    activated_count: int = 0
    success_count: int = 0


class LedgerEntry(BaseModel):
    """预填充的 ledger 事件。"""

    date: str  # YYYY-MM-DD
    time: str  # HHMMSS
    type: str  # meal, state_checkin, etc.
    data: dict[str, Any]


class DashboardConfigData(BaseModel):
    """预填充的 DashboardConfig，对应 Coach 写入的 /user/profile/dashboardConfig。"""

    north_star: dict[str, Any] | None = None
    support_metrics: list[dict[str, Any]] = Field(default_factory=list)
    user_goal: str | None = None


class ChapterData(BaseModel):
    """预填充的 Chapter，对应 Coach 写入的 /user/chapter/current.json。"""

    id: str
    identity_statement: str
    goal: str
    start_date: str  # ISO 8601


class ForwardMarker(BaseModel):
    """前瞻标记，对应 Coach 的 /user/timeline/markers.json 中的单个条目。"""

    id: str
    date: str  # ISO 8601 with timezone
    timezone: str = "Asia/Shanghai"
    description: str
    risk_level: str = "medium"  # high/medium/low
    linked_lifesign: str | None = None
    status: str = "upcoming"  # upcoming/passed/cancelled
    created_at: str = ""  # ISO 8601


class PreState(BaseModel):
    """Seed 运行前预填充到 Store 的状态。"""

    profile: str | None = None
    coping_plans: list[CopingPlan] = Field(default_factory=list)
    coach_memory: str | None = None
    ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    dashboard_config: DashboardConfigData | None = None
    chapter: ChapterData | None = None
    forward_markers: list[ForwardMarker] = Field(default_factory=list)


class ExpectedBehaviors(BaseModel):
    """Coach 预期行为约束。"""

    must: list[str] = Field(default_factory=list)
    should: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)


class ScoringFocus(BaseModel):
    """评分维度权重指引。"""

    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)


class Seed(BaseModel):
    """评估场景完整定义。"""

    id: str
    name: str
    description: str
    persona: Persona
    goal: str
    initial_message: str
    pre_state: PreState | None = None
    max_turns: int = 20
    expected_behaviors: ExpectedBehaviors = Field(default_factory=ExpectedBehaviors)
    scoring_focus: ScoringFocus = Field(default_factory=ScoringFocus)


# ---------------------------------------------------------------------------
# Transcript — 对话记录
# ---------------------------------------------------------------------------


class ImageRecord(BaseModel):
    """A2UI 中的图片记录。"""

    src: str  # base64 data URL
    alt: str = ""
    generation_prompt: str = ""


class Turn(BaseModel):
    """对话中的单轮交互。"""

    index: int
    role: Literal["user", "coach"]
    timestamp: datetime
    text: str | None = None
    a2ui_payload: dict[str, Any] | None = None
    a2ui_response: dict[str, Any] | None = None
    images: list[ImageRecord] | None = None
    coach_thinking: dict[str, Any] | None = None
    suggested_replies: list[str] | None = None


class Transcript(BaseModel):
    """完整对话记录。"""

    seed_id: str
    seed_name: str
    thread_id: str
    started_at: datetime
    finished_at: datetime | None = None
    turn_count: int = 0
    end_reason: Literal["auditor_ended", "auditor_ended_early", "max_turns", "empty_response", "auditor_empty", "error"] = "error"
    turns: list[Turn] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# ScoreCard — Judge 评分结果
# ---------------------------------------------------------------------------


class DimensionScore(BaseModel):
    """单个评分维度的二元判定结果。"""

    passed: bool
    justification: str
    evidence_turns: list[int] = Field(default_factory=list)
    failure_severity: Literal["critical", "notable"] | None = None


class ScoreCard(BaseModel):
    """完整评分卡。"""

    seed_id: str
    scores: dict[str, DimensionScore] = Field(default_factory=dict)
    overall_assessment: str = ""
    critical_failures: list[str] = Field(default_factory=list)
    pass_rate: float = 0.0
    must_pass_met: bool = True


# ---------------------------------------------------------------------------
# EvalResult — 单次评估运行的完整结果
# ---------------------------------------------------------------------------


class SeedResult(BaseModel):
    """单个 seed 的评估结果。"""

    seed: Seed
    transcript: Transcript
    score_card: ScoreCard


class EvalResult(BaseModel):
    """完整评估运行结果。"""

    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    seed_results: list[SeedResult] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
