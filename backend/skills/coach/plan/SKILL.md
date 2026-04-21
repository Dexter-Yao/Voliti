---
name: plan
description: Draft or revise the user's structured fat-loss Plan (target, chapters with process goals, weekly progress). Use when the user needs a coherent multi-week plan (calorie range, training cadence, meal structure, process goals), after six-dimension profile is sufficiently filled and emotional state is stable, or when the user explicitly requests to adjust the Plan. Offers four tools — create_plan (first Plan only), set_goal_status, update_week_narrative, revise_plan. Detailed triggers, workflows, and single-direction data boundary are in Phase B.5.
license: internal
---

# Plan Skill (placeholder — full content lands in Phase B.5)

This SKILL.md is a placeholder for the Plan Skill introduced by Phase B of the plan-skill-research rollout.

The full skill spec (triggers / workflows / single-direction data boundary / three-scenario scripts / references) will replace this file in Phase B.5. Until then:

- Coach sees four Plan tools in the coaching session: `create_plan`, `set_goal_status`, `update_week_narrative`, `revise_plan`.
- Use them only when the six-dimension profile is sufficiently filled and the user is not in an acute dysregulated state.
- On any validation error returned by a tool, surface the Coach-readable message from the tool result directly to reason about the next action.
