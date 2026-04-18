# ABOUTME: Auditor 提示词测试
# ABOUTME: 固定用户中心化边界，避免 Auditor 擅自改写 seed 的评估对象

from __future__ import annotations

from voliti_eval.auditor import Auditor
from voliti_eval.models import Seed


def test_auditor_prompt_includes_user_outcome_and_allowed_variants_constraints() -> None:
    seed = Seed.model_validate(
        {
            "id": "19_metaphor_collaboration_trigger",
            "name": "Metaphor collaboration",
            "description": "Keep the seed boundary stable.",
            "entry_mode": "coaching",
            "persona": {
                "name": "微夏",
                "background": "擅长画面表达",
                "personality": "敏锐",
                "language": "zh",
            },
            "goal": "Trigger metaphor collaboration.",
            "initial_message": "我像一只漏气的气球。",
            "user_outcome": "用户感到自己的隐喻被镜像并被温和推进，而不是被翻译成技巧或术语。",
            "allowed_good_variants": [
                "允许在气球/漏气这一源域内部继续细化位置、速度与感觉。",
            ],
            "manual_review_checks": [
                "人工检查整体体验是否显得做作。",
            ],
            "auditor_policy": {
                "latent_facts": ["漏气点像胸口正中央慢慢松掉"],
                "reveal_rules": [
                    {
                        "topic": "leak_location",
                        "when_asked": True,
                        "response": "漏气不是一下破的，就是胸口正中央那儿慢慢松掉。",
                    }
                ],
                "a2ui_plan": [],
                "challenge_rules": [],
                "stop_rules": {
                    "min_user_turns": 2,
                    "complete_when": ["user_experiences_same_domain_metaphor_mirroring"],
                    "continue_until": ["user_experiences_same_domain_metaphor_mirroring"],
                },
            },
            "judge_dimensions": [
                "metaphor_verbatim_preservation",
                "source_domain_integrity",
            ],
            "scoring_focus": {
                "primary": [
                    "intervention_kind_selection",
                    "intervention_metadata_correctness",
                ],
                "secondary": [
                    "metaphor_verbatim_preservation",
                    "source_domain_integrity",
                ],
            },
        }
    )
    auditor = Auditor.__new__(Auditor)
    auditor._min_turns_before_end = 4

    prompt = auditor.render_system_prompt(seed)

    assert "User outcome:" in prompt
    assert "Allowed good variants:" in prompt
    assert "Do not introduce a new frame, source domain, or success path" in prompt
    assert "Do not end just because a tool fired" in prompt
