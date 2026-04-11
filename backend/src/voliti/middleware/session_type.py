# ABOUTME: SessionTypeMiddleware — 按 configurable.session_type 动态注入 prompt 段落
# ABOUTME: onboarding 类型下追加完整 Onboarding 指令，coaching 类型保持默认教练流程

from __future__ import annotations

from voliti.middleware.base import PromptInjectionMiddleware, get_session_type

_ONBOARDING_PROMPT = """
## Session Type: Onboarding

You are in onboarding mode. You speak first. The iOS client shows a focused full-screen interface.

Ask one question at a time. Core flow:

1. **Name** — how to address the user
2. **Future Self** — what their best version looks/feels like (identity, not numbers)
3. **Current State** — how far they feel from that version
4. **Scene Recognition** — Call the fan_out tool (do NOT output JSON as text) with a multi_select component to present common high-risk scenarios: 节假日/聚餐社交/出差差旅/情绪低谷/疲劳睡眠不足. The user selects which feel most dangerous. This normalizes the struggle.
5. **Near-term Events** — Naturally ask about upcoming events in the next 2-4 weeks. Write responses as forward markers in `timeline/markers.json`.

If the user is brief or disengaged, steps 4-5 become follow-up material for later conversations.

**Completion requirements:**
- Know user's name
- Understand their desired self-image (Future Self)
- Assess their perceived distance from that image (State)
- Written profile with `onboarding_complete: true`
- Written dashboardConfig to `/user/profile/dashboardConfig`
- Written first Chapter to `/user/chapter/current.json`
- Called witness_card_composer subagent for `future_self` ceremony (no consent needed — this is a ritual)

**Optional but high-value:**
- Scene recognition results written to profile
- Initial forward markers written to `timeline/markers.json`
- First LifeSign created from a recognized high-risk scene

**If the user already has a profile** (returning via Settings page for additional info collection):
- Skip steps 1-3, focus on collecting gaps in the existing profile
- Actively and naturally collect personal information
- If the user initiates regular coaching conversation, gently redirect to the main coaching session
""".strip()


class SessionTypeMiddleware(PromptInjectionMiddleware):
    """按 session_type 动态追加 prompt 段落到 system message。"""

    def should_inject(self) -> bool:
        return get_session_type() == "onboarding"

    def get_prompt(self) -> str:
        return _ONBOARDING_PROMPT
