# ABOUTME: Plan Skill 工具桥接 · re-export plan_tools 的 4 个 tool 给 _load_skill_tools 动态注册
# ABOUTME: 实现位于 voliti.tools.plan_tools；SKILL.md 引导 Coach 何时选用哪一个

from __future__ import annotations

from voliti.tools.plan_tools import (
    create_plan,
    revise_plan,
    set_goal_status,
    update_week_narrative,
)

TOOLS = [create_plan, set_goal_status, update_week_narrative, revise_plan]
