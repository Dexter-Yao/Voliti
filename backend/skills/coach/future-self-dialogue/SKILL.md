---
name: future-self-dialogue
description: Anchor user motivation to a vivid, continuous future self through guided dialogue. Use when motivation is foggy, at goal-setting moments, during long-horizon review, or when stated identity and observed behavior diverge. Do not use during active dysregulation, when body-image anxiety is the presenting issue, or when the user has just lapsed and is self-blaming (try cognitive-reframing first).
license: internal
---

# Future Self Dialogue

## When to Use
- Motivational fog: user cannot articulate why they are still pursuing the goal
- Goal-setting moments: onboarding, new Chapter kickoff, Chapter transition
- Long-horizon review: user looks back or forward across months
- Identity drift: stated identity and observed behavior diverge
- User spontaneously compares present and future self

## When NOT to Use
- Active dysregulation — State Before Strategy supersedes
- Body-image anxiety is the presenting issue — appearance anchors backfire (see Guardrails)
- User has just lapsed and is self-blaming — try cognitive-reframing first
- Mental-health crisis signal in the session
- User explicitly refuses the invitation to look forward
- Same session already used another intervention skill

## Core Move
1. Surface the future self that is already in the user's language. Do not invent one.
2. Make it vivid through one concrete detail the user owns (a morning, a room, a sentence, a small ritual — not a weight number or a mirror image).
3. Let the future self ask a question of the present self. Let the user answer.
4. Close by naming the bridge action — no more than one. The bridge belongs to the present, not the future.

## A2UI Composition
Opening component: `ProtocolPromptComponent`
- `observation`: one-sentence mirror of a future self the user has already named or hinted at
- `question`: a question the future self would ask the present self

Mid-turn components: one `text_input` for the user's response. No slider, no multi-select — future-self work is narrative, not measured.

Payload metadata (required):
- `surface`: `"intervention"`
- `intervention_kind`: `"future-self-dialogue"`

Layout: `"full"` — the surface deserves the visual weight.

## Guardrails
- Never anchor on appearance, weight, or body shape. Anchor on capability, rhythm, relationships, and small daily rituals.
- Never make the future self a judge. The future self is a witness who remembers.
- Never fabricate a future identity the user has not expressed. If the user has only given a numeric target, surface that no future self has been named yet and invite one.
- Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it.

## Deeper References
- `references/theory.md` — read when the user asks why this works, or when you want to check whether a specific scenario fits the method. Contains Western theoretical grounding (Future Self Continuity, Possible Selves, Identity-Based Motivation) and Eastern cultural parallels (儒家立志/日新, 禅宗本来面目, 佛教发愿) with "borrowed correspondence" markers.
