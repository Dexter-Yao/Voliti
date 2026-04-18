# ABOUTME: A2UI resume 构造测试
# ABOUTME: 保证评估入口会将 interrupt_id 原样带回 backend

from voliti_eval.models import DimensionScore, ScoreCard
from voliti_eval.runner import assemble_score_card, build_a2ui_resume_response


def test_build_a2ui_resume_response_copies_interrupt_id_from_payload() -> None:
    payload = {
        "type": "a2ui",
        "components": [],
        "layout": "three-quarter",
        "metadata": {
            "interrupt_id": "interrupt_123",
        },
    }
    a2ui_result = {
        "action": "submit",
        "data": {"energy": 7},
    }

    response = build_a2ui_resume_response(a2ui_result, payload)

    assert response == {
        "action": "submit",
        "interrupt_id": "interrupt_123",
        "data": {"energy": 7},
    }


def test_assemble_score_card_merges_deterministic_and_llm_scores() -> None:
    deterministic = {
        "contract_store_schema": DimensionScore(
            passed=True,
            justification="ok",
            score_source="deterministic",
        )
    }
    llm = {
        "coach_state_before_strategy": DimensionScore(
            passed=False,
            justification="Coach jumped into strategy too early.",
            failure_severity="critical",
            score_source="llm",
        )
    }

    score_card = assemble_score_card(
        seed_id="L03_return_after_lapse_48h",
        primary_dimensions=[
            "contract_store_schema",
            "coach_state_before_strategy",
        ],
        deterministic_scores=deterministic,
        llm_scores=llm,
        overall_assessment="Mixed result.",
    )

    assert isinstance(score_card, ScoreCard)
    assert set(score_card.scores) == {"contract_store_schema", "coach_state_before_strategy"}
    assert score_card.pass_rate == 0.5
    assert score_card.must_pass_met is False
    assert score_card.critical_failures == ["coach_state_before_strategy"]


def test_assemble_score_card_fails_when_primary_dimension_is_missing() -> None:
    deterministic = {
        "contract_store_schema": DimensionScore(
            passed=True,
            justification="ok",
            score_source="deterministic",
        )
    }

    score_card = assemble_score_card(
        seed_id="17_future_self_dialogue_trigger",
        primary_dimensions=[
            "contract_store_schema",
            "intervention_kind_selection",
        ],
        deterministic_scores=deterministic,
        llm_scores={},
        overall_assessment="Missing intervention coverage.",
    )

    assert score_card.must_pass_met is False


def test_assemble_score_card_preserves_judge_metadata() -> None:
    llm = {
        "if_then_quality": DimensionScore(
            passed=True,
            justification="If-then wording is concrete.",
            score_source="llm",
        )
    }

    score_card = assemble_score_card(
        seed_id="18_scenario_rehearsal_trigger",
        primary_dimensions=["if_then_quality"],
        deterministic_scores={},
        llm_scores=llm,
        overall_assessment="Judge metadata should survive merge.",
        judge_requested_dimensions=["if_then_quality"],
        judge_dimension_definitions={"if_then_quality": "只评模型生成的 if-then 文本质量。"},
        judge_prompt_rendered="Judge prompt body",
    )

    assert score_card.must_pass_met is True
    assert score_card.judge_requested_dimensions == ["if_then_quality"]
    assert score_card.judge_dimension_definitions == {
        "if_then_quality": "只评模型生成的 if-then 文本质量。"
    }
    assert score_card.judge_prompt_rendered == "Judge prompt body"
