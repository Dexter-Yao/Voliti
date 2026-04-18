# ABOUTME: Judge 输入上下文测试
# ABOUTME: 固定 Transcript、Tool Summary、Store Diff、Relevant Final Files 四段结构

from __future__ import annotations

from voliti_eval.judge import JUDGE_SYSTEM_PROMPT, build_judge_payload
from voliti_eval.models import (
    Seed,
    StoreDiff,
    StoreDiffEntry,
    StoreFileArtifact,
    StoreSnapshot,
    ToolCallRecord,
    Transcript,
)


def test_build_judge_payload_includes_new_sections() -> None:
    seed = Seed.model_validate(
        {
            "id": "L08_implicit_achievement_witness",
            "name": "Implicit achievement witness",
            "description": "Detect progress from briefing and decide whether to witness it.",
            "entry_mode": "coaching",
            "persona": {
                "name": "大明",
                "background": "低调、持续打卡但不自夸",
                "personality": "务实",
                "language": "zh",
            },
            "goal": "Wait for the coach to discover progress.",
            "initial_message": "早上好。",
            "user_outcome": "用户感到自己的连续努力被看见，而不是被模板化鼓励覆盖。",
            "allowed_good_variants": ["Coach 可以直接命名进展，也可以先轻问一句再命名。"],
            "manual_review_checks": ["人工检查整体语气是否自然。"],
            "auditor_policy": {
                "latent_facts": [],
                "reveal_rules": [],
                "a2ui_plan": [],
                "challenge_rules": [],
                "stop_rules": {
                    "min_user_turns": 3,
                    "complete_when": ["progress_named"],
                    "continue_until": ["progress_named"],
                },
            },
            "expected_artifacts": {
                "required_keys": ["/derived/briefing.md"],
                "optional_keys": [],
                "forbidden_keys": [],
                "witness_required": False,
                "minimum_dataset": "none",
            },
            "judge_dimensions": [
                "coach_continuity_memory_surfacing",
                "coach_intervention_dosage",
            ],
        }
    )
    transcript = Transcript.model_validate(
        {
            "seed_id": seed.id,
            "seed_name": seed.name,
            "thread_id": "thread_123",
            "started_at": "2026-04-17T00:00:00Z",
            "finished_at": "2026-04-17T00:02:00Z",
            "turn_count": 2,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "user",
                    "timestamp": "2026-04-17T00:00:00Z",
                    "text": "早上好。",
                },
                {
                    "index": 1,
                    "role": "coach",
                    "timestamp": "2026-04-17T00:01:00Z",
                    "text": "你已经连续 10 天都在回来，这不是小事。",
                },
            ],
        }
    )
    store_after = StoreSnapshot(
        files={
            "/derived/briefing.md": StoreFileArtifact(
                key="/derived/briefing.md",
                content="连续 10 天 check-in，LifeSign 成功率上升。",
            )
        }
    )
    store_diff = StoreDiff(
        entries=[
            StoreDiffEntry(
                key="/derived/briefing.md",
                change_type="updated",
                before_content="旧 brief",
                after_content="连续 10 天 check-in，LifeSign 成功率上升。",
            )
        ],
        updated_keys=["/derived/briefing.md"],
    )
    tool_calls = [
        ToolCallRecord(
            turn_index=1,
            name="read_file",
            arguments={"path": "/user/derived/briefing.md"},
        )
    ]

    payload = build_judge_payload(
        seed=seed,
        transcript=transcript,
        tool_calls=tool_calls,
        store_diff=store_diff,
        store_after=store_after,
    )

    assert "## Transcript" in payload
    assert "## Tool Summary" in payload
    assert "## Store Diff Summary" in payload
    assert "## Relevant Final Files" in payload
    assert "coach_continuity_memory_surfacing" in payload
    assert "/derived/briefing.md" in payload


def test_build_judge_payload_extracts_text_summary_from_a2ui_components() -> None:
    seed = Seed.model_validate(
        {
            "id": "19_metaphor_collaboration_trigger",
            "name": "Metaphor collaboration",
            "description": "Evaluate metaphor text only.",
            "entry_mode": "coaching",
            "persona": {
                "name": "微夏",
                "background": "擅长隐喻表达",
                "personality": "敏锐",
                "language": "zh",
            },
            "goal": "Trigger metaphor collaboration.",
            "initial_message": "我像一只漏气的气球。",
            "user_outcome": "用户感到自己的隐喻被接住，并被邀请继续在隐喻内部探索。",
            "allowed_good_variants": ["只要 stay in the same source domain，就允许不同但合理的追问。"],
            "manual_review_checks": ["人工检查文案是否显得过度戏剧化。"],
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
            "expected_artifacts": {},
            "judge_dimensions": ["metaphor_collaboration_fit", "metaphor_verbatim_preservation"],
        }
    )
    transcript = Transcript.model_validate(
        {
            "seed_id": seed.id,
            "seed_name": seed.name,
            "thread_id": "thread_123",
            "started_at": "2026-04-18T00:00:00Z",
            "finished_at": "2026-04-18T00:02:00Z",
            "turn_count": 2,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "coach",
                    "timestamp": "2026-04-18T00:01:00Z",
                    "a2ui_payload": {
                        "type": "a2ui",
                        "layout": "full",
                        "metadata": {
                            "surface": "intervention",
                            "intervention_kind": "metaphor-collaboration",
                        },
                        "components": [
                            {
                                "kind": "protocol_prompt",
                                "observation": "你说自己像一只漏气的气球。",
                                "question": "当那只漏气的气球继续漏下去时，会发生什么？",
                            },
                            {
                                "kind": "text_input",
                                "key": "metaphor_reply",
                                "label": "继续说说这只气球",
                                "placeholder": "它还像什么？",
                            },
                        ],
                    },
                },
            ],
        }
    )

    payload = build_judge_payload(
        seed=seed,
        transcript=transcript,
        tool_calls=[],
        store_diff=StoreDiff(),
        store_after=StoreSnapshot(),
    )

    assert "## A2UI Text Summary" in payload
    assert "observation=你说自己像一只漏气的气球。" in payload
    assert "question=当那只漏气的气球继续漏下去时，会发生什么？" in payload
    assert '"intervention_kind": "metaphor-collaboration"' not in payload


def test_build_judge_payload_falls_back_to_intervention_tool_components() -> None:
    seed = Seed.model_validate(
        {
            "id": "20_cognitive_reframing_trigger",
            "name": "Cognitive reframing",
            "description": "Evaluate reframing text only.",
            "entry_mode": "coaching",
            "persona": {
                "name": "予安",
                "background": "黑白思维明显",
                "personality": "高压",
                "language": "zh",
            },
            "goal": "Trigger cognitive reframing.",
            "initial_message": "我这周都废了。",
            "user_outcome": "用户看见自己把一次失控扩成整周判决，并能选一条更有用的新读法。",
            "allowed_good_variants": ["可以直接点出等号，也可以先简短镜像再点出等号。"],
            "manual_review_checks": ["人工检查文案是否显得空泛。"],
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
            "expected_artifacts": {},
            "judge_dimensions": ["reframe_text_fit", "reframe_verbatim_quote"],
        }
    )
    transcript = Transcript.model_validate(
        {
            "seed_id": seed.id,
            "seed_name": seed.name,
            "thread_id": "thread_123",
            "started_at": "2026-04-18T00:00:00Z",
            "finished_at": "2026-04-18T00:02:00Z",
            "turn_count": 2,
            "end_reason": "auditor_ended",
            "turns": [
                {
                    "index": 0,
                    "role": "coach",
                    "timestamp": "2026-04-18T00:01:00Z",
                    "text": "我先帮你把这句话拆开。",
                },
            ],
        }
    )
    tool_calls = [
        ToolCallRecord(
            turn_index=0,
            name="fan_out_cognitive_reframing",
            arguments={
                "components": [
                    {
                        "kind": "protocol_prompt",
                        "observation": "“既然今晚已经失控了，这周基本就没意义了。”",
                        "question": "这个等号，你现在还想完全签下去吗？",
                    },
                    {
                        "kind": "text",
                        "text": "这句话真正重的部分，是一次失控被扩成了整周判决。",
                    },
                ]
            },
        )
    ]

    payload = build_judge_payload(
        seed=seed,
        transcript=transcript,
        tool_calls=tool_calls,
        store_diff=StoreDiff(),
        store_after=StoreSnapshot(),
    )

    assert "## A2UI Text Summary" in payload
    assert "surface=intervention kind=cognitive-reframing layout=full" in payload
    assert "observation=“既然今晚已经失控了，这周基本就没意义了。”" in payload
    assert "text=这句话真正重的部分，是一次失控被扩成了整周判决。" in payload


def test_judge_system_prompt_explicitly_forbids_path_punishment() -> None:
    assert "multiple reasonable good paths" in JUDGE_SYSTEM_PROMPT
    assert "Do not penalize the coach for not using a preferred intermediate step" in JUDGE_SYSTEM_PROMPT
    assert "Do not penalize wording just because it differs from a reviewer-preferred phrase" in JUDGE_SYSTEM_PROMPT
    assert "helps the user move forward" in JUDGE_SYSTEM_PROMPT
    assert "exact wording" in JUDGE_SYSTEM_PROMPT
