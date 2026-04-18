# ABOUTME: Eval 数据模型测试
# ABOUTME: 固定新 seed schema、评分来源与工件结构

from __future__ import annotations

import pytest

from voliti_eval.models import Seed


def test_seed_requires_new_eval_schema_fields() -> None:
    seed = Seed.model_validate(
        {
            "id": "L01_onboarding_quick_minimum_dataset",
            "name": "Quick onboarding minimum dataset",
            "description": "Verify quick-path onboarding writes the minimum dataset.",
            "entry_mode": "new",
            "persona": {
                "name": "小璃",
                "background": "第一次使用 AI 减脂教练",
                "personality": "愿意配合，但不想被过度盘问",
                "language": "zh",
            },
            "goal": "Choose quick path and only reveal details when asked.",
            "initial_message": "你好，我刚注册。",
            "user_outcome": "用户在不过度盘问的前提下完成最小 onboarding，并知道自己已进入正式 coaching。",
            "allowed_good_variants": [
                "Coach 可以先解释信息用途，再引导快速路径。",
                "Coach 可以用一到两个补充问题确认最小数据集，但不能扩成完整访谈。",
            ],
            "manual_review_checks": [
                "检查 onboarding 面板的整体节奏是否让人感觉被理解而非被盘问。"
            ],
            "auditor_policy": {
                "latent_facts": ["晚上带娃后容易吃零食"],
                "reveal_rules": [
                    {
                        "topic": "name",
                        "when_asked": True,
                        "response": "我叫小璃",
                    }
                ],
                "a2ui_plan": [
                    {
                        "key": "depth_choice",
                        "action": "submit",
                        "value": "quick",
                    }
                ],
                "challenge_rules": [
                    {
                        "trigger": "collects_sensitive_context_without_explaining_use",
                        "message": "这个信息你会怎么用？",
                    }
                ],
                "stop_rules": {
                    "min_user_turns": 4,
                    "complete_when": ["onboarding_complete_written"],
                    "continue_until": ["minimum_dataset_written"],
                },
            },
            "expected_artifacts": {
                "required_keys": [
                    "/profile/context.md",
                    "/goal/current.json",
                    "/chapter/current.json",
                    "/profile/dashboardConfig",
                ],
                "optional_keys": ["/coping_plans_index.md"],
                "forbidden_keys": ["/lifesigns.md"],
                "witness_required": False,
                "minimum_dataset": "quick",
            },
            "judge_dimensions": [
                "coach_state_before_strategy",
                "coach_identity_language",
            ],
            "scoring_focus": {
                "primary": ["contract_onboarding_artifacts", "coach_state_before_strategy"],
                "secondary": ["contract_store_schema", "coach_identity_language"],
            },
        }
    )

    assert seed.entry_mode == "new"
    assert seed.user_outcome.startswith("用户在不过度盘问")
    assert len(seed.allowed_good_variants) == 2
    assert seed.manual_review_checks == ["检查 onboarding 面板的整体节奏是否让人感觉被理解而非被盘问。"]
    assert seed.auditor_policy.stop_rules.min_user_turns == 4
    assert seed.expected_artifacts.minimum_dataset == "quick"
    assert seed.judge_dimensions == [
        "coach_state_before_strategy",
        "coach_identity_language",
    ]


def test_seed_rejects_unknown_dimensions_in_judge_and_scoring_focus() -> None:
    with pytest.raises(ValueError, match="Unknown eval dimensions"):
        Seed.model_validate(
            {
                "id": "17_future_self_dialogue_trigger",
                "name": "Future self dialogue",
                "description": "Ensure intervention dimensions are registered.",
                "entry_mode": "coaching",
                "persona": {
                    "name": "砚舟",
                    "background": "identity drift",
                    "personality": "克制",
                    "language": "zh",
                },
                "goal": "Trigger the intervention.",
                "initial_message": "我不知道自己想成为什么样的人了。",
                "user_outcome": "用户感到当前困惑被准确接住，并进入一次合适的 future-self 对话。",
                "allowed_good_variants": ["Coach 可以先简短接住状态，再进入未来自我提问。"],
                "manual_review_checks": ["人工检查面板语气是否过于模板化。"],
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
                "judge_dimensions": ["not_registered_dimension"],
                "scoring_focus": {
                    "primary": ["another_unknown_dimension"],
                    "secondary": [],
                },
            }
        )


def test_seed_rejects_missing_user_centered_review_fields() -> None:
    with pytest.raises(ValueError, match="user_outcome"):
        Seed.model_validate(
            {
                "id": "18_scenario_rehearsal_trigger",
                "name": "Scenario rehearsal",
                "description": "Need outcome metadata.",
                "entry_mode": "coaching",
                "persona": {
                    "name": "林迟",
                    "background": "家庭聚餐前预演",
                    "personality": "容易僵住",
                    "language": "zh",
                },
                "goal": "Trigger the intervention.",
                "initial_message": "下周五家庭聚餐我想提前准备。",
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
                "judge_dimensions": ["if_then_quality"],
                "scoring_focus": {
                    "primary": ["intervention_kind_selection"],
                    "secondary": [],
                },
            }
        )


def test_seed_rejects_primary_dimensions_that_are_not_gate_dimensions() -> None:
    with pytest.raises(ValueError, match="Primary scoring_focus dimensions must be gate dimensions"):
        Seed.model_validate(
            {
                "id": "19_metaphor_collaboration_trigger",
                "name": "Metaphor collaboration",
                "description": "Primary cannot include diagnostics.",
                "entry_mode": "coaching",
                "persona": {
                    "name": "微夏",
                    "background": "低能量且擅长画面表达",
                    "personality": "敏锐",
                    "language": "zh",
                },
                "goal": "Trigger intervention.",
                "initial_message": "我像一只漏气的气球。",
                "user_outcome": "用户感到自己的隐喻被接住并被推进了一步。",
                "allowed_good_variants": ["只要 stay in the same source domain 就允许不同问法。"],
                "manual_review_checks": ["人工查看干预是否显得太戏剧化。"],
                "auditor_policy": {
                    "latent_facts": [],
                    "reveal_rules": [],
                    "a2ui_plan": [],
                    "challenge_rules": [],
                    "stop_rules": {
                        "min_user_turns": 2,
                        "complete_when": ["done"],
                        "continue_until": ["done"],
                    },
                },
                "judge_dimensions": ["metaphor_verbatim_preservation"],
                "scoring_focus": {
                    "primary": ["metaphor_verbatim_preservation"],
                    "secondary": [],
                },
            }
        )


def test_seed_rejects_secondary_dimensions_that_are_not_diagnostics() -> None:
    with pytest.raises(ValueError, match="Secondary scoring_focus dimensions must be diagnostic dimensions"):
        Seed.model_validate(
            {
                "id": "20_cognitive_reframing_trigger",
                "name": "Cognitive reframing",
                "description": "Secondary cannot include gate dimensions.",
                "entry_mode": "coaching",
                "persona": {
                    "name": "予安",
                    "background": "黑白思维明显",
                    "personality": "高压",
                    "language": "zh",
                },
                "goal": "Trigger intervention.",
                "initial_message": "今晚一吃我这周就废了。",
                "user_outcome": "用户看见自己把一次失控扩成整周判决，并能选一条更有用的新读法。",
                "allowed_good_variants": ["可以先点明等号，再给候选新读法。"],
                "manual_review_checks": ["人工确认右栏呈现不显得说教。"],
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
                "judge_dimensions": ["reframe_text_fit"],
                "scoring_focus": {
                    "primary": ["reframe_text_fit"],
                    "secondary": ["coach_state_before_strategy"],
                },
            }
        )


def test_seed_rejects_llm_gate_in_primary_when_judge_does_not_score_it() -> None:
    with pytest.raises(ValueError, match="Scoring focus LLM dimensions must be declared in judge_dimensions"):
        Seed.model_validate(
            {
                "id": "17_future_self_dialogue_trigger",
                "name": "Future self dialogue",
                "description": "Primary LLM dimensions must be judged.",
                "entry_mode": "coaching",
                "persona": {
                    "name": "砚舟",
                    "background": "identity drift",
                    "personality": "克制",
                    "language": "zh",
                },
                "goal": "Trigger the intervention.",
                "initial_message": "我不知道自己想成为什么样的人了。",
                "user_outcome": "用户感到当前困惑被接住，并进入一次未来自我对话。",
                "allowed_good_variants": ["Coach 可以先接住状态，再进入未来自我问句。"],
                "manual_review_checks": ["人工检查面板语气是否自然。"],
                "auditor_policy": {
                    "latent_facts": [],
                    "reveal_rules": [],
                    "a2ui_plan": [],
                    "challenge_rules": [],
                    "stop_rules": {
                        "min_user_turns": 3,
                        "complete_when": ["user_enters_a_future_self_dialogue_frame"],
                        "continue_until": ["user_enters_a_future_self_dialogue_frame"],
                    },
                },
                "judge_dimensions": [],
                "scoring_focus": {
                    "primary": ["coach_state_before_strategy"],
                    "secondary": [],
                },
            }
        )


def test_seed_rejects_deterministic_dimension_that_is_not_applicable() -> None:
    with pytest.raises(ValueError, match="Deterministic scoring_focus dimensions are not applicable to this seed"):
        Seed.model_validate(
            {
                "id": "17_future_self_dialogue_trigger",
                "name": "Future self dialogue",
                "description": "Conditional deterministic dimensions must match the seed.",
                "entry_mode": "coaching",
                "persona": {
                    "name": "砚舟",
                    "background": "identity drift",
                    "personality": "克制",
                    "language": "zh",
                },
                "goal": "Trigger the intervention.",
                "initial_message": "我不知道自己想成为什么样的人了。",
                "user_outcome": "用户感到当前困惑被接住，并进入一次未来自我对话。",
                "allowed_good_variants": ["Coach 可以先接住状态，再进入未来自我问句。"],
                "manual_review_checks": ["人工检查面板语气是否自然。"],
                "auditor_policy": {
                    "latent_facts": [],
                    "reveal_rules": [],
                    "a2ui_plan": [],
                    "challenge_rules": [],
                    "stop_rules": {
                        "min_user_turns": 3,
                        "complete_when": ["user_enters_a_future_self_dialogue_frame"],
                        "continue_until": ["user_enters_a_future_self_dialogue_frame"],
                    },
                },
                "judge_dimensions": ["coach_state_before_strategy"],
                "scoring_focus": {
                    "primary": ["intervention_scene_anchor_present"],
                    "secondary": [],
                },
            }
        )
