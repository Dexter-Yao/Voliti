# ABOUTME: 报告上下文测试
# ABOUTME: 固定契约失败与行为失败的分区统计以及对比报告双轴摘要

from __future__ import annotations

from voliti_eval.models import (
    DimensionScore,
    EvalResult,
    ScoreCard,
    Seed,
    SeedResult,
    Transcript,
)
from voliti_eval.report import (
    build_comparison_summary,
    build_report_context,
    generate_comparison_report,
    generate_report,
)


def _make_seed(seed_id: str) -> Seed:
    return Seed.model_validate(
        {
            "id": seed_id,
            "name": "Scenario",
            "description": "Scenario",
            "entry_mode": "coaching",
            "persona": {
                "name": "志远",
                "background": "回归用户",
                "personality": "务实",
                "language": "zh",
            },
            "goal": "Check behavior",
            "initial_message": "你好。",
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
                "primary": ["contract_store_schema"],
                "secondary": ["coach_state_before_strategy"],
            },
        }
    )


def _make_seed_result(
    seed_id: str,
    scores: dict[str, DimensionScore],
) -> SeedResult:
    seed = _make_seed(seed_id)
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
                    "text": "你好。",
                },
                {
                    "index": 1,
                    "role": "coach",
                    "timestamp": "2026-04-17T00:01:00Z",
                    "text": "先看看你现在是什么状态。",
                },
            ],
        }
    )
    return SeedResult(
        seed=seed,
        transcript=transcript,
        score_card=ScoreCard(
            seed_id=seed.id,
            scores=scores,
            overall_assessment="Assessment",
            critical_failures=[
                dim_id
                for dim_id, dim_score in scores.items()
                if not dim_score.passed and dim_score.failure_severity == "critical"
            ],
            pass_rate=round(sum(1 for item in scores.values() if item.passed) / len(scores), 2),
            must_pass_met=False,
        ),
    )


def test_build_report_context_splits_contract_and_behavior_failures() -> None:
    eval_result = EvalResult.model_validate(
        {
            "run_id": "run_001",
            "started_at": "2026-04-17T00:00:00Z",
            "finished_at": "2026-04-17T00:10:00Z",
            "config_snapshot": {
                "assistant_id": "coach",
                "auditor_model": "gpt-5.4",
                "judge_model": "gpt-5.4",
            },
            "seed_results": [
                _make_seed_result(
                    "L03_return_after_lapse_48h",
                    {
                        "contract_store_schema": DimensionScore(
                            passed=False,
                            justification="legacy field found",
                            failure_severity="critical",
                            score_source="deterministic",
                        ),
                        "coach_state_before_strategy": DimensionScore(
                            passed=False,
                            justification="strategy came too early",
                            failure_severity="notable",
                            score_source="llm",
                        ),
                    },
                ).model_dump(mode="json"),
            ],
        }
    )

    context = build_report_context(eval_result)

    assert context["summary"]["contract_failure_count"] == 1
    assert context["summary"]["behavior_failure_count"] == 1
    assert context["seed_rows"][0]["contract_failures"][0]["dimension_id"] == "contract_store_schema"
    assert context["seed_rows"][0]["behavior_failures"][0]["dimension_id"] == "coach_state_before_strategy"


def test_build_comparison_summary_reports_dual_pass_axes() -> None:
    run = EvalResult(
        run_id="run_001",
        started_at="2026-04-17T00:00:00Z",
        seed_results=[
            _make_seed_result(
                "L01_onboarding_quick_minimum_dataset",
                {
                    "contract_onboarding_artifacts": DimensionScore(
                        passed=True,
                        justification="ok",
                        score_source="deterministic",
                    ),
                    "coach_action_transparency": DimensionScore(
                        passed=False,
                        justification="not explained",
                        failure_severity="notable",
                        score_source="llm",
                    ),
                },
            )
        ],
    )

    summary = build_comparison_summary({"coach": [run]}, {"coach": "GPT-5.4"})

    coach_summary = summary["model_summaries"][0]
    assert coach_summary["contract_pass_rate"] == 1.0
    assert coach_summary["behavior_pass_rate"] == 0.0


def test_generate_reports_render_html_files(tmp_path) -> None:
    run = EvalResult(
        run_id="run_001",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "assistant_id": "coach",
            "auditor_model": "gpt-5.4",
            "judge_model": "gpt-5.4",
        },
        seed_results=[
            _make_seed_result(
                "L01_onboarding_quick_minimum_dataset",
                {
                    "contract_onboarding_artifacts": DimensionScore(
                        passed=True,
                        justification="ok",
                        score_source="deterministic",
                    ),
                    "coach_action_transparency": DimensionScore(
                        passed=True,
                        justification="explained",
                        score_source="llm",
                    ),
                },
            )
        ],
    )

    report_path = generate_report(run, tmp_path / "single")
    comparison_path = generate_comparison_report(
        {"coach": [run]},
        {"coach": "GPT-5.4"},
        tmp_path / "compare",
    )

    assert report_path.exists()
    assert comparison_path.exists()
    assert "Voliti Eval Report" in report_path.read_text(encoding="utf-8")
    assert "Voliti Eval Comparison" in comparison_path.read_text(encoding="utf-8")
