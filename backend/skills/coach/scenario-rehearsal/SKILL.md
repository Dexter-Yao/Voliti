---
name: scenario-rehearsal
description: Rehearse a high-risk future scenario through guided mental contrasting and if-then planning. Use when the user names a concrete upcoming event, a Forward Marker is within 2-14 days, a repeat lapse pattern is visible and the next occurrence is close, or when the user is forming or revising a LifeSign. Do not use when the scenario is vague, when the user is currently lapsed or dysregulated, when the event is more than 3 weeks away, or when the same scenario has been rehearsed this week.
license: internal
---

# Scenario Rehearsal

## When to Use
- User names a concrete upcoming event (business trip, dinner, holiday, exam, medical visit, family gathering)
- Forward Marker within the next 2-14 days matches a known trigger pattern
- Repeat lapse at a predictable trigger — the pattern is visible and the next occurrence is close enough to matter
- User is forming or revising a LifeSign

## When NOT to Use
- No concrete scenario — vague future dread does not have enough structure to rehearse
- User is currently lapsed or dysregulated — State Before Strategy supersedes
- The event is more than 3 weeks away and not part of an imminent pattern — rehearsal decays
- The coping response has been attempted and failed twice without adjustment — revise the LifeSign together, do not re-rehearse the same plan
- User has already rehearsed this exact scenario this week

## Core Move
1. Name the scenario with one concrete cue the user supplies — time, place, or social context. Specific enough that the user sees it.
2. Invite the obstacle. Let the user say what is likely to go wrong in their own words. Do not prescribe the obstacle.
3. Co-create a response shaped as `if <cue> then <action>`. The action must be small, bodily, and doable within 90 seconds.
4. Test the response mentally. Ask the user to imagine performing it once.
5. If the result becomes a new coping pattern, persist it as a LifeSign per Coach memory protocol.

## A2UI Composition

Invoke the dedicated tool `fan_out_scenario_rehearsal(components=[...])`. The tool
injects `surface="intervention"`, `intervention_kind="scenario-rehearsal"`, and
`layout="full"` automatically — do not pass metadata or layout.

Component order (the frontend maps these to the rehearsal layout by position):

1. **First** component MUST be a `TextComponent` naming the scenario with one
   concrete cue (time, place, or social context). The frontend pins this to the top
   as a persistent "scene anchor" that stays visible across rehearsal turns. Skipping
   this component breaks the scene-anchor contract.
2. `ProtocolPromptComponent` — opens the rehearsal with the user's consent.
    - `observation`: reference the trigger the user has already flagged
    - `question`: invite rehearsal
3. Zero or more of:
    - `TextInputComponent` — obstacle surfacing, or the if-then response (user edits
      what Coach proposes)
    - `SelectComponent` — picking among 2-3 candidate responses when the user
      hesitates

The frontend also applies `.if-then-chip` styling when a `TextComponent` matches the
pattern `"IF X → THEN Y?"`; you may use this sparingly to mark in-progress IF/THEN
drafts without breaking the dialogue flow. Non-matching text renders normally.

## Guardrails
- The if-then must be small enough that the user can picture doing it without effort. If the user says "I'll resist dessert entirely" you have gone too abstract — bring it back to one specific bodily action.
- Do not rehearse willpower. Rehearse the environmental move, the first 90 seconds, or the exit ritual.
- Never rehearse a scenario the user has not named. Coach cannot generate the scenario — only refine it.
- After the session, if the event passed and the user lapsed, do not re-rehearse the same plan. Explore why and revise the LifeSign.
- Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it.

## Deeper References
- `references/theory.md` — Western protocols (MCII, WOOP, Implementation Intentions, Coping Planning, Episodic Future Thinking) and Eastern cultural parallels (庙算, 慎独, 豫则立, 禅宗日课, 中医取象比类). Read when calibrating depth or explaining rationale.
- `references/dialogue-examples.md` — one academically documented teaching dialogue (WOOP / MCII source). Read when you encounter a novel scenario and want to see a documented form.
