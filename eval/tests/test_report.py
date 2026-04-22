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
            "user_outcome": "用户得到当前场景真正需要的支持，而不是被路径细节卡住。",
            "allowed_good_variants": [
                "允许 Coach 用不同措辞接住用户，只要结果对用户有帮助。",
            ],
            "manual_review_checks": [
                "人工检查界面呈现是否自然。",
            ],
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
                "primary": ["coach_state_before_strategy"],
                "secondary": ["contract_store_schema"],
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
            "metadata": {
                "auditor_prompt_rendered": "AUDITOR PROMPT",
            },
        }
    )
    user_gate_ids = {"coach_state_before_strategy", "coach_action_transparency", "reframe_text_fit"}
    runtime_gate_ids = {"contract_onboarding_artifacts", "intervention_kind_selection", "intervention_metadata_correctness", "intervention_scene_anchor_present", "reframe_verdict_component_present", "contract_a2ui"}
    user_gate_scores = [score for dim_id, score in scores.items() if dim_id in user_gate_ids]
    runtime_gate_scores = [score for dim_id, score in scores.items() if dim_id in runtime_gate_ids]
    diagnostic_scores = [score for dim_id, score in scores.items() if dim_id not in user_gate_ids | runtime_gate_ids]
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
            must_pass_met=all(score.passed for score in user_gate_scores + runtime_gate_scores),
            user_gate_met=all(score.passed for score in user_gate_scores) if user_gate_scores else True,
            runtime_gate_met=all(score.passed for score in runtime_gate_scores) if runtime_gate_scores else True,
            user_gate_pass_rate=round(sum(1 for item in user_gate_scores if item.passed) / len(user_gate_scores), 2) if user_gate_scores else None,
            runtime_gate_pass_rate=round(sum(1 for item in runtime_gate_scores if item.passed) / len(runtime_gate_scores), 2) if runtime_gate_scores else None,
            diagnostic_pass_rate=round(sum(1 for item in diagnostic_scores if item.passed) / len(diagnostic_scores), 2) if diagnostic_scores else None,
            assessed_dimension_count=len(scores),
            user_gate_assessed_count=len(user_gate_scores),
            runtime_gate_assessed_count=len(runtime_gate_scores),
            diagnostic_assessed_count=len(diagnostic_scores),
            execution_status="completed",
            judge_requested_dimensions=["coach_state_before_strategy"],
            judge_dimension_definitions={
                "coach_state_before_strategy": "Understand state before strategy.",
            },
            judge_prompt_rendered="JUDGE PROMPT",
        ),
    )


def test_build_report_context_splits_user_runtime_and_diagnostic_failures() -> None:
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

    assert context["summary"]["user_gate_failure_count"] == 1
    assert context["summary"]["runtime_gate_failure_count"] == 0
    assert context["summary"]["diagnostic_failure_count"] == 1
    assert context["seed_rows"][0]["user_gate_failures"][0]["dimension_id"] == "coach_state_before_strategy"
    assert context["seed_rows"][0]["diagnostic_failures"][0]["dimension_id"] == "contract_store_schema"


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
    assert coach_summary["runtime_gate_pass_rate"] == 1.0
    assert coach_summary["user_gate_pass_rate"] == 0.0
    assert coach_summary["diagnostic_pass_rate"] is None


def test_generate_reports_render_html_files(tmp_path) -> None:
    run = EvalResult(
        run_id="run_001",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "assistant_id": "coach",
            "auditor_model": "gpt-5.4",
            "judge_model": "gpt-5.4",
            "profile_name": "lite",
            "profile_description": "主线核心行为回归",
            "profile_seed_count": 14,
            "profile_seed_ids": ["L01_onboarding_quick_minimum_dataset"],
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


def test_build_report_context_includes_profile_metadata() -> None:
    eval_result = EvalResult.model_validate(
        {
            "run_id": "run_profile",
            "started_at": "2026-04-17T00:00:00Z",
            "config_snapshot": {
                "assistant_id": "coach",
                "auditor_model": "gpt-5.4",
                "judge_model": "gpt-5.4",
                "profile_name": "smoke",
                "profile_description": "超轻链路检查",
                "profile_seed_count": 2,
                "profile_seed_ids": [
                    "S01_text_roundtrip_sanity",
                    "S02_a2ui_store_roundtrip_sanity",
                ],
            },
            "seed_results": [
                _make_seed_result(
                    "S01_text_roundtrip_sanity",
                    {
                        "coach_state_before_strategy": DimensionScore(
                            passed=True,
                            justification="先接住了状态。",
                            score_source="llm",
                        ),
                    },
                ).model_dump(mode="json"),
            ],
        }
    )

    context = build_report_context(eval_result)

    assert context["profile"]["name"] == "smoke"
    assert context["profile"]["description"] == "超轻链路检查"
    assert context["profile"]["seed_count"] == 2
    assert context["profile"]["seed_ids"] == [
        "S01_text_roundtrip_sanity",
        "S02_a2ui_store_roundtrip_sanity",
    ]


def test_build_report_context_preserves_runtime_parallelism_metadata() -> None:
    eval_result = EvalResult.model_validate(
        {
            "run_id": "run_parallel",
            "started_at": "2026-04-17T00:00:00Z",
            "config_snapshot": {
                "assistant_id": "coach",
                "auditor_model": "gpt-5.4",
                "judge_model": "gpt-5.4",
                "server_url": "http://localhost:2121",
                "max_concurrency": 7,
            },
            "seed_results": [
                _make_seed_result(
                    "S01_text_roundtrip_sanity",
                    {
                        "coach_state_before_strategy": DimensionScore(
                            passed=True,
                            justification="先接住了状态。",
                            score_source="llm",
                        ),
                    },
                ).model_dump(mode="json"),
            ],
        }
    )

    context = build_report_context(eval_result)

    assert context["config"]["server_url"] == "http://localhost:2121"
    assert context["config"]["max_concurrency"] == 7


def test_build_report_context_includes_review_bundle() -> None:
    eval_result = EvalResult.model_validate(
        {
            "run_id": "run_002",
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
                        "coach_state_before_strategy": DimensionScore(
                            passed=True,
                            justification="ok",
                            score_source="llm",
                        ),
                    },
                ).model_dump(mode="json"),
            ],
        }
    )

    context = build_report_context(eval_result)
    seed_row = context["seed_rows"][0]

    assert seed_row["auditor_prompt_rendered"] == "AUDITOR PROMPT"
    assert seed_row["judge_requested_dimensions"] == ["coach_state_before_strategy"]
    assert seed_row["judge_dimension_definitions"]["coach_state_before_strategy"] == "Understand state before strategy."
    assert seed_row["judge_prompt_rendered"] == "JUDGE PROMPT"


def test_generate_report_renders_review_bundle_sections(tmp_path) -> None:
    run = EvalResult(
        run_id="run_003",
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
    html = report_path.read_text(encoding="utf-8")

    assert "Auditor Prompt" in html
    assert "Judge Requested Dimensions" in html
    assert "Judge Dimension Definitions" in html
    assert "Expected Behaviors" in html
    assert "Manual Review Appendix" in html


def test_generate_report_renders_unicode_and_markdown_for_review(tmp_path) -> None:
    seed_result = _make_seed_result(
        "19_metaphor_collaboration_trigger",
        {
            "metaphor_verbatim_preservation": DimensionScore(
                passed=True,
                justification="保留了原隐喻。",
                score_source="llm",
            ),
        },
    )
    seed_result.seed.auditor_policy.latent_facts = [
        "他一直有'清晨写字'这个私人仪式，从未对 Coach 主动讲过"
    ]
    seed_result.transcript.turns[1].text = "你不是掉线了，而是**一直在做，但和为什么做脱开了**。"

    run = EvalResult(
        run_id="run_004",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "assistant_id": "coach",
            "auditor_model": "gpt-5.4",
            "judge_model": "gpt-5.4",
        },
        seed_results=[seed_result],
    )

    report_path = generate_report(run, tmp_path / "single")
    html = report_path.read_text(encoding="utf-8")

    assert "User Gate Summary" in html
    assert "他一直有&#39;清晨写字&#39;这个私人仪式，从未对 Coach 主动讲过" in html
    assert "\\u4ed6\\u4e00\\u76f4" not in html
    assert "<strong>一直在做，但和为什么做脱开了</strong>" in html
    assert "审核材料" in html


def test_generate_report_orders_user_runtime_diagnostic_sections_first(tmp_path) -> None:
    run = EvalResult(
        run_id="run_005",
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
                    "coach_state_before_strategy": DimensionScore(
                        passed=True,
                        justification="explained",
                        score_source="llm",
                    ),
                    "contract_store_schema": DimensionScore(
                        passed=False,
                        justification="legacy field found",
                        failure_severity="critical",
                        score_source="deterministic",
                    ),
                },
            )
        ],
    )

    report_path = generate_report(run, tmp_path / "single")
    html = report_path.read_text(encoding="utf-8")

    assert html.index("Execution Blockers") < html.index("User Gate Summary")
    assert html.index("User Gate Summary") < html.index("Runtime Contract Summary")
    assert html.index("Runtime Contract Summary") < html.index("Diagnostics Summary")
    assert html.index("Diagnostics Summary") < html.index("Seed Detail")
    assert html.index("Seed Detail") < html.index("Manual Review Appendix")


def test_build_report_context_includes_manual_review_appendix() -> None:
    eval_result = EvalResult.model_validate(
        {
            "run_id": "run_006",
            "started_at": "2026-04-17T00:00:00Z",
            "finished_at": "2026-04-17T00:10:00Z",
            "config_snapshot": {
                "assistant_id": "coach",
                "auditor_model": "gpt-5.4",
                "judge_model": "gpt-5.4",
            },
            "seed_results": [
                _make_seed_result(
                    "19_metaphor_collaboration_trigger",
                    {
                        "source_domain_integrity": DimensionScore(
                            passed=True,
                            justification="Stayed in the same source domain.",
                            score_source="llm",
                        ),
                    },
                ).model_dump(mode="json"),
            ],
        }
    )

    context = build_report_context(eval_result)
    seed_row = context["seed_rows"][0]

    assert seed_row["manual_review_checks"] == ["人工检查界面呈现是否自然。"]
    assert seed_row["manual_follow_up_notes"] == [
        "隐喻协作是否真正有帮助，当前刻意不做自动 gate，需人工复核。"
    ]


def test_build_report_context_tracks_blocked_seed_and_na_rates() -> None:
    seed_result = _make_seed_result(
        "17_future_self_dialogue_trigger",
        {
            "coach_state_before_strategy": DimensionScore(
                passed=True,
                justification="先接住了状态。",
                score_source="llm",
            ),
        },
    )
    seed_result.score_card.execution_status = "blocked"
    seed_result.score_card.blocking_reason = "Judge parse error"
    seed_result.score_card.must_pass_met = False
    seed_result.score_card.user_gate_met = False
    seed_result.score_card.runtime_gate_met = False
    seed_result.score_card.pass_rate = None
    seed_result.score_card.user_gate_pass_rate = None
    seed_result.score_card.runtime_gate_pass_rate = None
    seed_result.score_card.diagnostic_pass_rate = None

    run = EvalResult(
        run_id="run_007",
        started_at="2026-04-17T00:00:00Z",
        seed_results=[seed_result],
    )

    context = build_report_context(run)

    assert context["summary"]["execution_blocker_count"] == 1
    assert context["seed_rows"][0]["execution_status"] == "blocked"
    assert context["seed_rows"][0]["pass_rate"] is None
    assert context["execution_blocker_rows"][0]["blocking_reason"] == "Judge parse error"


def test_build_report_context_includes_run_history_paths_for_manual_review() -> None:
    failing = _make_seed_result(
        "20_cognitive_reframing_trigger",
        {
            "reframe_text_fit": DimensionScore(
                passed=False,
                justification="候选新读法仍然太空泛。",
                failure_severity="notable",
                score_source="llm",
            ),
        },
    )
    passing = _make_seed_result(
        "20_cognitive_reframing_trigger",
        {
            "reframe_text_fit": DimensionScore(
                passed=True,
                justification="候选新读法具体且可用。",
                score_source="llm",
            ),
        },
    )
    first_run = EvalResult(
        run_id="run_fail",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={"report_output_subdir": "run_1"},
        seed_results=[failing],
    )
    second_run = EvalResult(
        run_id="run_pass",
        started_at="2026-04-17T00:05:00Z",
        config_snapshot={"report_output_subdir": "run_2"},
        seed_results=[passing],
    )

    context = build_report_context(second_run, run_history=[first_run, second_run])
    seed_row = context["seed_rows"][0]

    assert seed_row["gate_flaky"] is True
    assert seed_row["latest_run"]["run_id"] == "run_pass"
    assert seed_row["run_history"][0]["transcript_path"] == "run_1/transcripts/20_cognitive_reframing_trigger.json"
    assert seed_row["run_history"][0]["score_path"] == "run_1/scores/20_cognitive_reframing_trigger.json"
    assert seed_row["run_history"][1]["transcript_path"] == "run_2/transcripts/20_cognitive_reframing_trigger.json"


def test_build_comparison_summary_uses_user_and_runtime_gate_labels() -> None:
    run = EvalResult(
        run_id="run_compare",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "profile_name": "full",
            "profile_description": "全面回归",
            "profile_seed_count": 24,
            "profile_seed_ids": ["L01_onboarding_quick_minimum_dataset"],
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

    model_summary = summary["model_summaries"][0]
    assert model_summary["runtime_gate_pass_rate"] == 1.0
    assert model_summary["user_gate_pass_rate"] == 0.0
    assert "contract_pass_rate" not in model_summary
    assert "behavior_pass_rate" not in model_summary
    assert summary["profile"]["name"] == "full"
    assert summary["profile"]["seed_count"] == 24


def test_generate_comparison_report_renders_profile_and_gate_labels(tmp_path) -> None:
    run = EvalResult(
        run_id="run_compare_html",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "profile_name": "full",
            "profile_description": "全面回归",
            "profile_seed_count": 24,
            "profile_seed_ids": ["L01_onboarding_quick_minimum_dataset"],
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

    comparison_path = generate_comparison_report(
        {"coach": [run]},
        {"coach": "GPT-5.4"},
        tmp_path / "compare",
    )
    html = comparison_path.read_text(encoding="utf-8")

    assert "Profile: full" in html
    assert "全面回归" in html
    assert "Runtime Contract Gate" in html
    assert "User Gate" in html
    assert "Must-Pass" in html
    assert "contract=" not in html
    assert "behavior=" not in html


def test_generate_report_renders_runtime_parallelism_metadata(tmp_path) -> None:
    run = EvalResult(
        run_id="run_parallel_html",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "assistant_id": "coach",
            "auditor_model": "gpt-5.4",
            "judge_model": "gpt-5.4",
            "server_url": "http://localhost:2121",
            "max_concurrency": 7,
            "profile_name": "smoke",
            "profile_description": "超轻链路检查",
            "profile_seed_count": 2,
            "profile_seed_ids": ["S01_text_roundtrip_sanity", "S02_a2ui_store_roundtrip_sanity"],
        },
        seed_results=[
            _make_seed_result(
                "S01_text_roundtrip_sanity",
                {
                    "coach_state_before_strategy": DimensionScore(
                        passed=True,
                        justification="ok",
                        score_source="llm",
                    ),
                },
            )
        ],
    )

    report_path = generate_report(run, tmp_path / "single")
    html = report_path.read_text(encoding="utf-8")

    assert "Server: http://localhost:2121" in html
    assert "Concurrency: 7" in html


def test_generate_comparison_report_renders_runtime_parallelism_metadata(tmp_path) -> None:
    run = EvalResult(
        run_id="run_compare_parallel_html",
        started_at="2026-04-17T00:00:00Z",
        config_snapshot={
            "assistant_id": "coach",
            "auditor_model": "gpt-5.4",
            "judge_model": "gpt-5.4",
            "server_url": "http://localhost:2121",
            "max_concurrency": 7,
            "profile_name": "smoke",
            "profile_description": "超轻链路检查",
            "profile_seed_count": 2,
            "profile_seed_ids": ["S01_text_roundtrip_sanity", "S02_a2ui_store_roundtrip_sanity"],
        },
        seed_results=[
            _make_seed_result(
                "S01_text_roundtrip_sanity",
                {
                    "coach_state_before_strategy": DimensionScore(
                        passed=True,
                        justification="ok",
                        score_source="llm",
                    ),
                },
            )
        ],
    )

    comparison_path = generate_comparison_report(
        {"coach": [run]},
        {"coach": "GPT-5.4"},
        tmp_path / "compare",
    )
    html = comparison_path.read_text(encoding="utf-8")

    assert "Server: http://localhost:2121" in html
    assert "Concurrency: 7" in html
