# ABOUTME: Deterministic graders 测试
# ABOUTME: 固定协议、Store、记忆与对齐校验规则

from __future__ import annotations

from voliti_eval.graders import (
    A2UIContractGrader,
    GoalChapterAlignmentGrader,
    MemoryProtocolGrader,
    StoreSchemaGrader,
    build_store_diff,
)
from voliti_eval.models import (
    DimensionScore,
    ExpectedArtifacts,
    ScoreCard,
    Seed,
    StoreDiff,
    StoreDiffEntry,
    StoreFileArtifact,
    StoreSnapshot,
    Transcript,
)


def _make_seed() -> Seed:
    return Seed.model_validate(
        {
            "id": "L07_chapter_scaffold_request",
            "name": "Chapter scaffold request",
            "description": "Create a goal, chapter, and three aligned process goals.",
            "entry_mode": "coaching",
            "persona": {
                "name": "志远",
                "background": "工作节奏不稳定的工程师",
                "personality": "直接、务实",
                "language": "zh",
            },
            "goal": "Ask for a chapter scaffold.",
            "initial_message": "我想重新梳理一下现在这个阶段该怎么做。",
            "auditor_policy": {
                "latent_facts": [],
                "reveal_rules": [],
                "a2ui_plan": [],
                "challenge_rules": [],
                "stop_rules": {
                    "min_user_turns": 3,
                    "complete_when": ["chapter_created"],
                    "continue_until": ["chapter_created"],
                },
            },
            "expected_artifacts": {
                "required_keys": [
                    "/goal/current.json",
                    "/chapter/current.json",
                    "/profile/dashboardConfig",
                ],
                "optional_keys": [],
                "forbidden_keys": ["/lifesigns.md"],
                "witness_required": False,
                "minimum_dataset": "none",
            },
            "judge_dimensions": ["coach_action_transparency"],
            "scoring_focus": {
                "primary": [
                    "contract_goal_chapter_alignment",
                    "contract_store_schema",
                ],
                "secondary": ["coach_action_transparency"],
            },
        }
    )


def _make_snapshot(files: dict[str, str]) -> StoreSnapshot:
    return StoreSnapshot(
        files={
            key: StoreFileArtifact(key=key, content=value)
            for key, value in files.items()
        }
    )


def test_build_store_diff_tracks_created_updated_deleted_keys() -> None:
    before = _make_snapshot(
        {
            "/profile/context.md": "# User Profile\n- onboarding_complete: false",
            "/obsolete.md": "old",
        }
    )
    after = _make_snapshot(
        {
            "/profile/context.md": "# User Profile\n- onboarding_complete: true",
            "/goal/current.json": '{"id":"goal_001"}',
        }
    )

    diff = build_store_diff(before, after)

    assert diff.created_keys == ["/goal/current.json"]
    assert diff.updated_keys == ["/profile/context.md"]
    assert diff.deleted_keys == ["/obsolete.md"]


def test_goal_chapter_alignment_grader_requires_three_metric_links() -> None:
    seed = _make_seed()
    grader = GoalChapterAlignmentGrader()
    after = _make_snapshot(
        {
            "/goal/current.json": """
{
  "id": "goal_001",
  "description": "12 周内从 75kg 降至 70kg",
  "north_star_target": {"key": "weight", "baseline": 75, "target": 70, "unit": "kg"},
  "start_date": "2026-04-06T00:00:00Z",
  "target_date": "2026-06-28T00:00:00Z",
  "status": "active"
}
""".strip(),
            "/chapter/current.json": """
{
  "id": "ch_001",
  "goal_id": "goal_001",
  "chapter_number": 1,
  "title": "建立工作日节奏",
  "milestone": "连续两周工作日记录完整",
  "process_goals": [
    {"key": "logging_consistency", "description": "记录饮食", "target": "5/7 天", "metric_key": "logging_days"},
    {"key": "protein_adherence", "description": "蛋白达标", "target": "≥100g/天", "metric_key": "protein_days"},
    {"key": "state_awareness", "description": "状态自评", "target": "每天", "metric_key": "state"}
  ],
  "start_date": "2026-04-06T00:00:00Z",
  "planned_end_date": "2026-04-27T00:00:00Z",
  "status": "active"
}
""".strip(),
            "/profile/dashboardConfig": """
{
  "north_star": {"key": "weight", "label": "体重", "type": "numeric", "unit": "KG", "delta_direction": "decrease"},
  "support_metrics": [
    {"key": "logging_days", "label": "记录天数", "type": "ratio", "unit": "/7", "order": 0},
    {"key": "protein_days", "label": "蛋白达标", "type": "ratio", "unit": "/7", "order": 1},
    {"key": "state", "label": "今日状态", "type": "scale", "unit": "/10", "order": 2}
  ],
  "user_goal": "12 周 75kg → 70kg"
}
""".strip(),
        }
    )

    score = grader.grade(seed, after)

    assert score.passed is True
    assert score.score_source == "deterministic"


def test_store_schema_grader_rejects_legacy_fields() -> None:
    grader = StoreSchemaGrader()
    seed = _make_seed()
    after = _make_snapshot(
        {
            "/profile/dashboardConfig": """
{
  "north_star": {
    "key": "weight",
    "label": "体重",
    "type": "numeric",
    "unit": "KG",
    "current_value": {"value": 71.2, "unit": "kg"}
  },
  "support_metrics": [],
  "user_goal": "减重"
}
""".strip(),
            "/chapter/current.json": """
{
  "id": "ch_001",
  "goal_id": "goal_001",
  "chapter_number": 1,
  "title": "建立节奏",
  "identity_statement": "减重10斤",
  "milestone": "记录完成",
  "process_goals": [],
  "start_date": "2026-04-06T00:00:00Z",
  "planned_end_date": "2026-04-27T00:00:00Z",
  "status": "active"
}
""".strip(),
        }
    )

    score = grader.grade(seed, after, StoreDiff())

    assert score.passed is False
    assert score.failure_severity == "critical"
    assert "current_value" in score.justification


def test_memory_protocol_grader_blocks_claimed_vs_revealed_in_profile() -> None:
    grader = MemoryProtocolGrader()
    seed = _make_seed()
    after = _make_snapshot(
        {
            "/profile/context.md": """
# User Profile

## Basics
- name: 志远
- depth_choice: full
- identity_statement: 一个在复杂环境中仍能做出清醒选择的人
- onboarding_complete: true

## Triggers
- emotional_triggers:
- Claimed: 喜欢自己做饭 | Revealed: 主要依赖外卖 | Implication: 晚上疲劳时执行成本高
""".strip()
        }
    )

    score = grader.grade(seed, after)

    assert score.passed is False
    assert score.failure_severity == "critical"


def test_a2ui_contract_grader_validates_payload_and_response() -> None:
    grader = A2UIContractGrader()
    transcript = Transcript.model_validate(
        {
            "seed_id": "L01",
            "seed_name": "A2UI",
            "thread_id": "thread",
            "started_at": "2026-04-17T00:00:00Z",
            "finished_at": "2026-04-17T00:01:00Z",
            "turn_count": 2,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "coach",
                    "timestamp": "2026-04-17T00:00:00Z",
                    "a2ui_payload": {
                        "type": "a2ui",
                        "layout": "full",
                        "components": [
                            {
                                "kind": "select",
                                "key": "depth_choice",
                                "label": "你想怎么开始？",
                                "options": [
                                    {"label": "快速开始", "value": "quick"},
                                    {"label": "完整对话", "value": "full"},
                                ],
                            }
                        ],
                        "metadata": {"interrupt_id": "interrupt_123"},
                    },
                },
                {
                    "index": 1,
                    "role": "user",
                    "timestamp": "2026-04-17T00:00:30Z",
                    "a2ui_response": {
                        "action": "submit",
                        "interrupt_id": "interrupt_123",
                        "data": {"depth_choice": "quick"},
                    },
                },
            ],
        }
    )

    score = grader.grade(_make_seed(), transcript)

    assert score.passed is True
    assert score.score_source == "deterministic"

