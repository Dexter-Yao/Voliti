# ABOUTME: A2UI resume 构造测试
# ABOUTME: 保证评估入口会将 interrupt_id 原样带回 backend

from voliti_eval.runner import build_a2ui_resume_response


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
