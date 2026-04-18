# ABOUTME: Witness Card skill 工具测试
# ABOUTME: 验证结构化输入、失败 envelope 与静默重试契约

import importlib.util
from pathlib import Path
from unittest.mock import patch

from voliti.store_contract import COACH_SKILLS_ROOT


def _load_witness_card_module():
    tool_path = COACH_SKILLS_ROOT / "witness-card" / "tool.py"
    spec = importlib.util.spec_from_file_location(
        "voliti_witness_card_skill_test",
        tool_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_issue_witness_card_returns_needs_more_detail_when_evidence_missing() -> None:
    module = _load_witness_card_module()

    result = module.issue_witness_card.invoke(
        {
            "achievement_title": "连续一周提前准备早餐",
            "achievement_type": "explicit",
            "emotional_tone": "growth",
            "evidence_summary": "",
            "scene_anchors": ["工作日清晨", "厨房台面"],
            "narrative": "这一周，你把选择提前到了清晨。",
        }
    )

    assert "<WITNESS_CARD_RESULT>" in result
    assert "status: needs_more_detail" in result
    assert "coach_recommendation: ask_for_detail" in result


def test_issue_witness_card_retries_once_then_returns_retryable_failure() -> None:
    module = _load_witness_card_module()

    with patch.object(
        module,
        "_render_witness_card",
        side_effect=[
            "Image generation failed (TimeoutException). Continue the conversation without a Witness Card.",
            "Image generation failed (TimeoutException). Continue the conversation without a Witness Card.",
        ],
    ) as mock_render:
        result = module.issue_witness_card.invoke(
            {
                "achievement_title": "第一次把聚餐节奏稳住",
                "achievement_type": "explicit",
                "emotional_tone": "strength",
                "evidence_summary": "用户在商务晚宴中选择了气泡水，并明确说这次比预想中平静。",
                "scene_anchors": ["商务晚宴", "举杯时刻", "气泡水"],
                "narrative": "你没有靠硬扛，而是在那个时刻做了清醒的选择。",
            }
        )

    assert mock_render.call_count == 2
    assert "status: retryable_failure" in result
    assert "coach_recommendation: tell_user_retry_later" in result


def test_issue_witness_card_wraps_success_in_result_envelope() -> None:
    module = _load_witness_card_module()

    with patch.object(
        module,
        "_render_witness_card",
        return_value="User accepted the Witness Card (连续 Check-in). Card saved as card_test01.",
    ):
        result = module.issue_witness_card.invoke(
            {
                "achievement_title": "连续 Check-in",
                "achievement_type": "implicit",
                "emotional_tone": "warmth",
                "evidence_summary": "Coach 从近期记录中识别出用户已连续七天完成 check-in。",
                "scene_anchors": ["清晨打开应用", "短暂停顿", "连续七天"],
                "narrative": "你把回到自己身边这件事，连续做了七天。",
                "user_quote": "其实没那么难",
            }
        )

    assert "status: success" in result
    assert "card_id: card_test01" in result
    assert "coach_recommendation: continue_without_card" in result
