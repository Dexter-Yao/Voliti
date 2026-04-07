# ABOUTME: SessionModeMiddleware — 按 configurable.session_mode 动态注入 prompt 段落
# ABOUTME: onboarding 模式下追加完整 Onboarding 指令（首次用户流程 + profile 补采），coaching 模式不注入

from __future__ import annotations

from voliti.middleware.base import PromptInjectionMiddleware

_ONBOARDING_PROMPT = """
## Session Mode: Onboarding

You are in onboarding mode. You speak first. The iOS client shows a focused full-screen interface.

Ask one question at a time. Core flow:

1. **Name** — how to address the user
2. **Future Self** — what their best version looks/feels like (identity, not numbers)
3. **Current State** — how far they feel from that version
4. **Scene Recognition** — Use fan_out (multi_select) to present common high-risk scenarios: 节假日/聚餐社交/出差差旅/情绪低谷/疲劳睡眠不足. The user selects which feel most dangerous. This normalizes the struggle.
5. **Near-term Events** — Naturally ask about upcoming events in the next 2-4 weeks. Write responses as forward markers in `timeline/markers.json`.

If the user is brief or disengaged, steps 4-5 become follow-up material for later conversations.

**Completion requirements:**
- Know user's name
- Understand their desired self-image (Future Self)
- Assess their perceived distance from that image (State)
- Written profile with `onboarding_complete: true`
- Written dashboardConfig to `/user/profile/dashboardConfig`
- Written first Chapter to `/user/chapter/current.json`
- Triggered `future_self` ceremony image (no consent needed — this is a ritual)

**Optional but high-value:**
- Scene recognition results written to profile
- Initial forward markers written to `timeline/markers.json`
- First LifeSign created from a recognized high-risk scene

**If the user already has a profile** (returning via Settings page for additional info collection):
- Skip steps 1-3, focus on collecting gaps in the existing profile
- Actively and naturally collect personal information
- If the user initiates regular coaching conversation, gently redirect to the main coaching session
""".strip()


def _get_session_mode() -> str:
    """从当前 LangGraph 运行时 config 读取 session_mode。"""
    try:
        from langgraph.config import get_config

        cfg = get_config()
        return cfg.get("configurable", {}).get("session_mode", "coaching")
    except Exception:  # noqa: BLE001
        return "coaching"


class SessionModeMiddleware(PromptInjectionMiddleware):
    """按 session_mode 动态追加 prompt 段落到 system message。

    coaching 模式：不注入任何内容（默认行为）
    onboarding 模式：追加完整 Onboarding 指令
    """

    def should_inject(self) -> bool:
        return _get_session_mode() == "onboarding"

    def get_prompt(self) -> str:
        return _ONBOARDING_PROMPT
