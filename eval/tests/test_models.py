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
                "primary": ["contract_onboarding_artifacts", "contract_store_schema"],
                "secondary": ["coach_state_before_strategy"],
            },
        }
    )

    assert seed.entry_mode == "new"
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
