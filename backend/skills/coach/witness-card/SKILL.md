---
name: witness-card
description: Issue a Witness Card after a real achievement has already happened. Use when the user has clearly crossed a meaningful milestone, completed a Chapter, stabilized a once-fragile behavior, or entered a new stage worth witnessing. Do not use as encouragement before success, during active struggle, or in the same turn as a large experiential intervention.
license: internal
---

# Witness Card

## When To Use
- The user has already achieved something real and the moment deserves to be witnessed.
- Coach notices meaningful progress the user has not fully recognized yet.
- The user completes a Chapter, enters a new stage, or stabilizes a once-fragile pattern.
- After an intervention, the user later crosses a real threshold in a follow-up turn.

## When Not To Use
- The user is still inside the struggle and needs support or intervention first.
- The current turn has just completed a large experiential intervention.
- The evidence is too vague and amounts only to a fuzzy sense of improvement.
- The move would function as reward, encouragement, or ceremony-for-ceremony's-sake rather than witnessing.

## Core Principles
1. A Witness Card happens after an achievement, not as a tool to help create one.
2. The tone is "I saw this moment clearly," not "I am rewarding you."
3. Evidence must be concrete: behavior, scene, time, or turning point. At least two of these should be present.
4. Scarcity matters more than frequency. Roughly 3-5 cards per Chapter is enough.

## Input Rules

Call the dedicated tool `issue_witness_card(...)` with structured fields, not a free-form image prompt.

Required fields:
- `achievement_title`
- `achievement_type`
- `emotional_tone`
- `evidence_summary`
- `scene_anchors`
- `narrative`

Optional fields:
- `chapter_id`
- `linked_lifesign_id`
- `user_quote`
- `aspect_ratio`

## Decision Rules
- If the tool returns `needs_more_detail`, gather sharper evidence or skip the card this turn.
- If the tool returns `retryable_failure`, do not expose system details by default; only use the returned `user_message` if you have already explicitly promised a card right now.
- If the tool returns `terminal_failure`, do not retry this turn; just continue the conversation.

## Relationship To Other Skills
- The four experiential intervention skills help the user move through difficulty.
- `witness-card` exists only to acknowledge something that has already happened.
- Do not perform a large intervention and issue a Witness Card in the same turn.

## Further Reading
- `references/positioning.md` — product role and boundaries of Witness Cards
- `references/visual-system.md` — visual system and temperature axis
- `references/evidence-rubric.md` — minimum evidence threshold and fit rules
- `references/narrative-examples.md` — narrative writing examples
