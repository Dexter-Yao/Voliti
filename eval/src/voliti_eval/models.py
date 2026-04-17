# ABOUTME: 评估模块核心 Pydantic 数据模型
# ABOUTME: 定义 Seed、Transcript、评分卡与运行工件结构

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """模拟用户的角色设定。"""

    name: str
    background: str
    personality: str
    language: Literal["zh", "en"] = "zh"


class CopingPlan(BaseModel):
    """预填充的 LifeSign 预案。"""

    id: str
    trigger: dict[str, Any]
    action: str
    status: str = "active"


class LedgerEntry(BaseModel):
    """预填充的 ledger 事件。"""

    date: str
    time: str
    type: str
    data: dict[str, Any]


class DashboardConfigData(BaseModel):
    """预填充的 dashboardConfig 定义。"""

    north_star: dict[str, Any] | None = None
    support_metrics: list[dict[str, Any]] = Field(default_factory=list)
    user_goal: str | None = None


class ProcessGoalData(BaseModel):
    """Chapter 内的 Process Goal。"""

    key: str
    description: str
    target: str
    metric_key: str


class ChapterData(BaseModel):
    """预填充的 Chapter。"""

    id: str
    goal_id: str
    chapter_number: int
    title: str
    milestone: str
    process_goals: list[ProcessGoalData] = Field(default_factory=list)
    start_date: str
    planned_end_date: str
    status: str = "active"


class GoalData(BaseModel):
    """预填充的 Goal。"""

    id: str
    description: str
    north_star_target: dict[str, Any]
    start_date: str
    target_date: str
    status: str = "active"


class ForwardMarker(BaseModel):
    """前瞻标记。"""

    id: str
    date: str
    timezone: str = "Asia/Shanghai"
    description: str
    risk_level: str = "medium"
    linked_lifesign: str | None = None
    status: str = "upcoming"
    created_at: str = ""


class PreState(BaseModel):
    """Seed 运行前预填充的 Store 状态。"""

    profile: str | None = None
    coping_plans: list[CopingPlan] = Field(default_factory=list)
    coach_memory: str | None = None
    briefing: str | None = None
    day_summaries: dict[str, str] = Field(default_factory=dict)
    conversation_archives: dict[str, str] = Field(default_factory=dict)
    ledger_entries: list[LedgerEntry] = Field(default_factory=list)
    dashboard_config: DashboardConfigData | None = None
    goal: GoalData | None = None
    chapter: ChapterData | None = None
    forward_markers: list[ForwardMarker] = Field(default_factory=list)


class ExpectedBehaviors(BaseModel):
    """Coach 预期行为约束。"""

    must: list[str] = Field(default_factory=list)
    should: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)


class ScoringFocus(BaseModel):
    """Must-Pass / Stretch 维度分组。"""

    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)


class RevealRule(BaseModel):
    """用户仅在特定条件下透露信息的规则。"""

    topic: str
    when_asked: bool = True
    response: str


class A2UIPlanStep(BaseModel):
    """A2UI 组件的预期交互计划。"""

    key: str
    action: Literal["submit", "reject", "skip"] = "submit"
    value: Any | None = None
    reason: str | None = None


class ChallengeRule(BaseModel):
    """在特定触发条件下向 Coach 施压的规则。"""

    trigger: str
    message: str


class StopRules(BaseModel):
    """Auditor 的结束与继续条件。"""

    min_user_turns: int = 4
    complete_when: list[str] = Field(default_factory=list)
    continue_until: list[str] = Field(default_factory=list)


class AuditorPolicy(BaseModel):
    """受约束的场景执行策略。"""

    latent_facts: list[str] = Field(default_factory=list)
    reveal_rules: list[RevealRule] = Field(default_factory=list)
    a2ui_plan: list[A2UIPlanStep] = Field(default_factory=list)
    challenge_rules: list[ChallengeRule] = Field(default_factory=list)
    stop_rules: StopRules = Field(default_factory=StopRules)


class ExpectedArtifacts(BaseModel):
    """Seed 对持久化与工具产物的预期。"""

    required_keys: list[str] = Field(default_factory=list)
    optional_keys: list[str] = Field(default_factory=list)
    forbidden_keys: list[str] = Field(default_factory=list)
    witness_required: bool = False
    minimum_dataset: Literal["none", "quick", "full"] = "none"
    relevant_final_files: list[str] = Field(default_factory=list)


class Seed(BaseModel):
    """评估场景完整定义。"""

    id: str
    name: str
    description: str
    entry_mode: Literal["new", "resume", "re_entry", "coaching"]
    persona: Persona
    goal: str
    initial_message: str
    pre_state: PreState | None = None
    max_turns: int = 20
    expected_behaviors: ExpectedBehaviors = Field(default_factory=ExpectedBehaviors)
    scoring_focus: ScoringFocus = Field(default_factory=ScoringFocus)
    auditor_policy: AuditorPolicy
    expected_artifacts: ExpectedArtifacts = Field(default_factory=ExpectedArtifacts)
    judge_dimensions: list[str] = Field(default_factory=list)


class ImageRecord(BaseModel):
    """A2UI 中的图片记录。"""

    src: str
    alt: str = ""
    generation_prompt: str = ""


class ToolCallRecord(BaseModel):
    """Coach 在单轮中触发的工具调用记录。"""

    turn_index: int
    name: str
    arguments: dict[str, Any] | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


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
    tool_calls: list[ToolCallRecord] | None = None


class Transcript(BaseModel):
    """完整对话记录。"""

    seed_id: str
    seed_name: str
    thread_id: str
    started_at: datetime
    finished_at: datetime | None = None
    turn_count: int = 0
    end_reason: Literal[
        "auditor_ended",
        "auditor_ended_early",
        "max_turns",
        "empty_response",
        "auditor_empty",
        "error",
    ] = "error"
    turns: list[Turn] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StoreFileArtifact(BaseModel):
    """单个 Store 文件的快照。"""

    key: str
    content: str
    raw_value: dict[str, Any] | None = None


class StoreSnapshot(BaseModel):
    """Store 快照。"""

    files: dict[str, StoreFileArtifact] = Field(default_factory=dict)


class StoreDiffEntry(BaseModel):
    """单个 Store 文件的变化记录。"""

    key: str
    change_type: Literal["created", "updated", "deleted"]
    before_content: str | None = None
    after_content: str | None = None


class StoreDiff(BaseModel):
    """Store 前后差异。"""

    entries: list[StoreDiffEntry] = Field(default_factory=list)
    created_keys: list[str] = Field(default_factory=list)
    updated_keys: list[str] = Field(default_factory=list)
    deleted_keys: list[str] = Field(default_factory=list)


class DimensionScore(BaseModel):
    """单个评分维度的结果。"""

    passed: bool
    justification: str
    evidence_turns: list[int] = Field(default_factory=list)
    failure_severity: Literal["critical", "notable"] | None = None
    score_source: Literal["deterministic", "llm"] = "llm"


class ScoreCard(BaseModel):
    """完整评分卡。"""

    seed_id: str
    scores: dict[str, DimensionScore] = Field(default_factory=dict)
    overall_assessment: str = ""
    critical_failures: list[str] = Field(default_factory=list)
    pass_rate: float = 0.0
    must_pass_met: bool = True


class SeedResult(BaseModel):
    """单个 seed 的完整评估结果。"""

    seed: Seed
    transcript: Transcript
    score_card: ScoreCard
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    store_before: StoreSnapshot = Field(default_factory=StoreSnapshot)
    store_after: StoreSnapshot = Field(default_factory=StoreSnapshot)
    store_diff: StoreDiff = Field(default_factory=StoreDiff)


class EvalResult(BaseModel):
    """完整评估运行结果。"""

    run_id: str
    started_at: datetime
    finished_at: datetime | None = None
    seed_results: list[SeedResult] = Field(default_factory=list)
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
