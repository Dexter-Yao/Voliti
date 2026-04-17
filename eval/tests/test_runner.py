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
