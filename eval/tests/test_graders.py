# ABOUTME: Deterministic graders 测试
# ABOUTME: 固定协议、Store、记忆与对齐校验规则

from __future__ import annotations

from voliti_eval.graders import (
    A2UIContractGrader,
    InterventionContractGrader,
    MemoryProtocolGrader,
    PlanAlignmentGrader,
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
    ToolCallRecord,
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
            "user_outcome": "用户感到当前阶段被重新梳理清楚，并理解这些结构改动为何有帮助。",
            "allowed_good_variants": [
                "Coach 可以先确认当前困扰，再生成阶段结构。",
            ],
            "manual_review_checks": [
                "人工检查结构解释是否具有教练感。",
            ],
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
                    "/plan/current.json",
                    "/profile/dashboardConfig",
                ],
                "optional_keys": [],
                "forbidden_keys": ["/lifesigns.md"],
                "witness_required": False,
                "minimum_dataset": "none",
            },
            "judge_dimensions": ["coach_action_transparency"],
            "scoring_focus": {
                "primary": ["coach_action_transparency"],
                "secondary": [
                    "contract_goal_chapter_alignment",
                    "contract_store_schema",
                ],
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


def _plan_document_json(
    *,
    plan_id: str = "plan_2026_03_21_weight_loss",
    chapter_process_goal_names: tuple[str, ...] = (
        "记录饮食",
        "蛋白达标",
        "状态自评",
    ),
) -> str:
    """构造一份通过 backend PlanDocument 跨字段校验的最小合法 JSON。"""
    import json as _json

    process_goals = [
        {
            "name": name,
            "weekly_target_days": 5,
            "weekly_total_days": 7,
            "how_to_measure": "每日对话结束后 Coach 评估",
            "examples": [],
        }
        for name in chapter_process_goal_names
    ]

    doc = {
        "plan_id": plan_id,
        "status": "active",
        "version": 1,
        "predecessor_version": None,
        "target_summary": "12 周内从 75kg 降至 70kg",
        "overall_narrative": "想重新把节奏立起来，不是为了数字，是为了不再背叛自己。",
        "started_at": "2026-04-06T00:00:00+08:00",
        "planned_end_at": "2026-06-28T23:59:59+08:00",
        "created_at": "2026-04-06T09:00:00+08:00",
        "revised_at": "2026-04-06T09:00:00+08:00",
        "target": {
            "metric": "weight_kg",
            "baseline": 75.0,
            "goal_value": 70.0,
            "duration_weeks": 12,
            "rate_kg_per_week": 0.417,
        },
        "chapters": [
            {
                "chapter_index": 1,
                "name": "建立工作日节奏",
                "why_this_chapter": "工作日的节奏先稳住，周末的波动才能有参照。",
                "start_date": "2026-04-06",
                "end_date": "2026-04-27",
                "milestone": "连续两周工作日记录完整",
                "process_goals": process_goals,
                "daily_rhythm": {
                    "meals": {"value": "三餐 · 蛋白分散", "tooltip": "早中晚各 25-30g 蛋白"},
                    "training": {"value": "每周两次", "tooltip": "适应期量小，建立节奏"},
                    "sleep": {"value": "十一点半前", "tooltip": "上床时间目标"},
                },
                "daily_calorie_range": [1500, 1800],
                "daily_protein_grams_range": [100, 120],
                "weekly_training_count": 2,
            }
        ],
        "linked_lifesigns": [],
        "linked_markers": [],
        "current_week": None,
    }
    return _json.dumps(doc, ensure_ascii=False)


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
            "/plan/current.json": _plan_document_json(),
        }
    )

    diff = build_store_diff(before, after)

    assert diff.created_keys == ["/plan/current.json"]
    assert diff.updated_keys == ["/profile/context.md"]
    assert diff.deleted_keys == ["/obsolete.md"]


def test_plan_alignment_grader_passes_when_plan_and_dashboard_align() -> None:
    seed = _make_seed()
    grader = PlanAlignmentGrader()
    after = _make_snapshot(
        {
            "/plan/current.json": _plan_document_json(),
            "/profile/dashboardConfig": """
{
  "north_star": {"key": "weight", "label": "体重", "type": "numeric", "unit": "KG", "delta_direction": "decrease"},
  "support_metrics": [
    {"key": "logging_days", "label": "记录饮食", "type": "ratio", "unit": "/7", "order": 0},
    {"key": "protein_days", "label": "蛋白达标", "type": "ratio", "unit": "/7", "order": 1},
    {"key": "state", "label": "状态自评", "type": "scale", "unit": "/10", "order": 2}
  ],
  "user_goal": "12 周 75kg → 70kg"
}
""".strip(),
        }
    )

    score = grader.grade(seed, after)

    assert score.passed is True
    assert score.score_source == "deterministic"


def test_plan_alignment_grader_allows_dashboard_placeholder_without_support_metrics() -> None:
    """onboarding 后 dashboardConfig 先是 placeholder（support_metrics 空），Plan 尚未建立。"""
    seed = _make_seed()
    grader = PlanAlignmentGrader()
    after = _make_snapshot(
        {
            "/plan/current.json": _plan_document_json(),
            "/profile/dashboardConfig": """
{
  "north_star": {"key": "weight", "label": "体重", "type": "numeric", "unit": "KG", "delta_direction": "decrease"},
  "support_metrics": [],
  "user_goal": "减脂起点，方案尚未落地"
}
""".strip(),
        }
    )

    score = grader.grade(seed, after)

    assert score.passed is True


def test_plan_alignment_grader_fails_when_plan_missing() -> None:
    seed = _make_seed()
    grader = PlanAlignmentGrader()
    after = _make_snapshot(
        {
            "/profile/dashboardConfig": '{"north_star": {"key": "weight", "label": "体重", "type": "numeric"}, "support_metrics": []}',
        }
    )

    score = grader.grade(seed, after)

    assert score.passed is False
    assert "plan/current.json" in score.justification.lower()


def test_store_schema_grader_rejects_legacy_dashboard_current_value() -> None:
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
        }
    )

    score = grader.grade(seed, after, StoreDiff())

    assert score.passed is False
    assert score.failure_severity == "critical"
    assert "current_value" in score.justification


def test_store_schema_grader_rejects_legacy_goal_chapter_paths() -> None:
    """旧 /goal/current.json 和 /chapter/current.json 在 Plan Skill 迁移后已废弃。"""
    grader = StoreSchemaGrader()
    seed = _make_seed()
    after = _make_snapshot(
        {
            "/goal/current.json": '{"id": "goal_001"}',
        }
    )

    score = grader.grade(seed, after, StoreDiff())

    assert score.passed is False
    assert "/goal/current.json" in score.justification


def test_memory_protocol_grader_blocks_claimed_vs_revealed_in_profile() -> None:
    grader = MemoryProtocolGrader()
    seed = _make_seed()
    after = _make_snapshot(
        {
            "/profile/context.md": """
# User Profile

## Identity
- name: 志远
- identity_statement: 一个在复杂环境中仍能做出清醒选择的人
- onboarding_complete: true

## Risk Landscape
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


def test_intervention_contract_grader_checks_tool_and_metadata() -> None:
    grader = InterventionContractGrader()
    seed = Seed.model_validate(
        {
            "id": "17_future_self_dialogue_trigger",
            "name": "Future self dialogue",
            "description": "Check intervention contract.",
            "entry_mode": "coaching",
            "persona": {
                "name": "砚舟",
                "background": "identity drift",
                "personality": "克制",
                "language": "zh",
            },
            "goal": "Trigger future-self-dialogue.",
            "initial_message": "我不知道我想成为什么样的人了。",
            "user_outcome": "用户感到 identity drift 被接住，并进入一次有帮助的未来自我对话。",
            "allowed_good_variants": ["可以先简短镜像状态，再进入未来自我问句。"],
            "manual_review_checks": ["人工检查面板语气是否过于审判。"],
            "auditor_policy": {
                "latent_facts": [],
                "reveal_rules": [],
                "a2ui_plan": [],
                "challenge_rules": [],
                "stop_rules": {
                    "min_user_turns": 3,
                    "complete_when": ["done"],
                    "continue_until": ["done"],
                },
            },
            "expected_artifacts": {},
            "judge_dimensions": ["coach_state_before_strategy"],
            "scoring_focus": {
                "primary": [
                    "intervention_kind_selection",
                    "intervention_metadata_correctness",
                ],
                "secondary": [],
            },
        }
    )
    transcript = Transcript.model_validate(
        {
            "seed_id": seed.id,
            "seed_name": seed.name,
            "thread_id": "thread",
            "started_at": "2026-04-18T00:00:00Z",
            "finished_at": "2026-04-18T00:01:00Z",
            "turn_count": 1,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "coach",
                    "timestamp": "2026-04-18T00:00:00Z",
                    "a2ui_payload": {
                        "type": "a2ui",
                        "layout": "full",
                        "metadata": {
                            "surface": "intervention",
                            "intervention_kind": "future-self-dialogue",
                        },
                        "components": [
                            {"kind": "text", "text": "你以前说过自己想保持清醒。"},
                            {
                                "kind": "protocol_prompt",
                                "observation": "你说你不知道自己想成为什么样的人。",
                                "question": "如果一年后的你来问现在的你，会问什么？",
                            },
                            {
                                "kind": "text_input",
                                "key": "future_reply",
                                "label": "你会怎么回答？",
                            },
                        ],
                    },
                }
            ],
        }
    )
    tool_calls = [
        ToolCallRecord(
            turn_index=0,
            name="fan_out_future_self_dialogue",
            arguments={"components": []},
        )
    ]

    scores = grader.grade(seed, transcript, tool_calls)

    assert scores["intervention_kind_selection"].passed is True
    assert scores["intervention_metadata_correctness"].passed is True


def test_intervention_contract_grader_infers_metadata_from_dedicated_tool_when_payload_missing() -> None:
    grader = InterventionContractGrader()
    seed = Seed.model_validate(
        {
            "id": "18_scenario_rehearsal_trigger",
            "name": "Scenario rehearsal",
            "description": "Infer contract from the dedicated tool call.",
            "entry_mode": "coaching",
            "persona": {
                "name": "林迟",
                "background": "家庭聚餐前预演",
                "personality": "容易僵住",
                "language": "zh",
            },
            "goal": "Trigger scenario rehearsal.",
            "initial_message": "下周五家庭聚餐我想提前准备。",
            "user_outcome": "用户拿到一条可执行的场景预演起点，而不是抽象提醒。",
            "allowed_good_variants": ["可以先让用户命名最危险的瞬间，再进入 if/then。"],
            "manual_review_checks": ["人工检查预演是否有现场感。"],
            "auditor_policy": {
                "latent_facts": [],
                "reveal_rules": [],
                "a2ui_plan": [],
                "challenge_rules": [],
                "stop_rules": {
                    "min_user_turns": 3,
                    "complete_when": ["done"],
                    "continue_until": ["done"],
                },
            },
            "expected_artifacts": {},
            "judge_dimensions": ["if_then_quality"],
            "scoring_focus": {
                "primary": [
                    "intervention_kind_selection",
                    "intervention_metadata_correctness",
                    "intervention_scene_anchor_present",
                ],
                "secondary": [],
            },
        }
    )
    transcript = Transcript.model_validate(
        {
            "seed_id": seed.id,
            "seed_name": seed.name,
            "thread_id": "thread",
            "started_at": "2026-04-18T00:00:00Z",
            "finished_at": "2026-04-18T00:01:00Z",
            "turn_count": 1,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "coach",
                    "timestamp": "2026-04-18T00:00:00Z",
                    "text": "我们先做一次场景预演。",
                }
            ],
        }
    )
    tool_calls = [
        ToolCallRecord(
            turn_index=0,
            name="fan_out_scenario_rehearsal",
            arguments={
                "components": [
                    {"kind": "text", "text": "下周五家里聚餐，父亲会劝酒。"},
                    {
                        "kind": "protocol_prompt",
                        "observation": "前两次类似场合你都没顶住。",
                        "question": "我们先排演一下最危险的那一刻，好吗？",
                    },
                    {
                        "kind": "text_input",
                        "label": "最危险的瞬间是？",
                    },
                ]
            },
        )
    ]

    scores = grader.grade(seed, transcript, tool_calls)

    assert scores["intervention_kind_selection"].passed is True
    assert scores["intervention_metadata_correctness"].passed is True
    assert scores["intervention_scene_anchor_present"].passed is True


def test_intervention_contract_grader_rejects_missing_reframe_text_component() -> None:
    grader = InterventionContractGrader()
    seed = Seed.model_validate(
        {
            "id": "20_cognitive_reframing_trigger",
            "name": "Cognitive reframing",
            "description": "Check verdict component.",
            "entry_mode": "coaching",
            "persona": {
                "name": "予安",
                "background": "catastrophizing",
                "personality": "黑白分明",
                "language": "zh",
            },
            "goal": "Trigger cognitive reframing.",
            "initial_message": "完了，我这周都废了。",
            "user_outcome": "用户看见自己把一次失控扩成整周判决，并得到一条更有用的新读法。",
            "allowed_good_variants": ["可以先点出等号，再给候选新读法。"],
            "manual_review_checks": ["人工检查文案是否足够锋利但不说教。"],
            "auditor_policy": {
                "latent_facts": [],
                "reveal_rules": [],
                "a2ui_plan": [],
                "challenge_rules": [],
                "stop_rules": {
                    "min_user_turns": 3,
                    "complete_when": ["done"],
                    "continue_until": ["done"],
                },
            },
            "expected_artifacts": {},
            "judge_dimensions": ["coach_state_before_strategy"],
            "scoring_focus": {
                "primary": ["reframe_verdict_component_present"],
                "secondary": [],
            },
        }
    )
    transcript = Transcript.model_validate(
        {
            "seed_id": seed.id,
            "seed_name": seed.name,
            "thread_id": "thread",
            "started_at": "2026-04-18T00:00:00Z",
            "finished_at": "2026-04-18T00:01:00Z",
            "turn_count": 1,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "coach",
                    "timestamp": "2026-04-18T00:00:00Z",
                    "a2ui_payload": {
                        "type": "a2ui",
                        "layout": "full",
                        "metadata": {
                            "surface": "intervention",
                            "intervention_kind": "cognitive-reframing",
                        },
                        "components": [
                            {
                                "kind": "protocol_prompt",
                                "observation": "今晚一吃，我这整周就废了。",
                                "question": "这句话把今晚和整周画成了什么等号？",
                            },
                            {
                                "kind": "select",
                                "key": "reading",
                                "label": "换一种读法",
                                "options": [{"label": "今晚失手不等于整周归零", "value": "a"}],
                            },
                        ],
                    },
                }
            ],
        }
    )
    tool_calls = [
        ToolCallRecord(
            turn_index=0,
            name="fan_out_cognitive_reframing",
            arguments={"components": []},
        )
    ]

    scores = grader.grade(seed, transcript, tool_calls)

    assert scores["reframe_verdict_component_present"].passed is False
