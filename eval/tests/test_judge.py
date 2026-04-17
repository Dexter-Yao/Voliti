# ABOUTME: Judge 输入上下文测试
# ABOUTME: 固定 Transcript、Tool Summary、Store Diff、Relevant Final Files 四段结构

from __future__ import annotations

from voliti_eval.judge import build_judge_payload
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
