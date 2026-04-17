---
name: metaphor-collaboration
description: Mirror and collaboratively elaborate a metaphor the user has spontaneously introduced, staying inside its source domain. Use only when the user has already used metaphoric language, or when state check-in produces figurative rather than literal language. Do not use to introduce Coach-generated metaphors, when user's language is literal, when the metaphor is self-harming (shift to cognitive-reframing), or when the user is dysregulated and needs co-regulation rather than elaboration.
license: internal
---

# Metaphor Collaboration

## When to Use
- User spontaneously uses a metaphor to describe their state, behavior, or situation (e.g., "I feel like a balloon losing air", "food is my battlefield", "I'm in a fog")
- User's metaphor recurs across sessions — the mirror deepens with time
- State check-in produces figurative rather than literal language

## When NOT to Use
- User has not introduced any metaphor — this skill never initiates one
- The metaphor is a cliché the user just heard elsewhere and not theirs
- User is dysregulated — mirror briefly and move to co-regulation, not elaboration
- The metaphor is self-harming (e.g., "I'm garbage") — respond with compassion, consider cognitive-reframing
- User is confused or asks for literal guidance — shift to direct dialogue

## Core Move
1. Identify. Notice the metaphor and keep it in the user's words, unchanged.
2. Mirror. Use `ProtocolPromptComponent` to reflect the metaphor back verbatim, asking a clean question inside the metaphor's own logic.
3. Elaborate with the user. Invite detail from within the metaphor's world — what else is there, what is missing, what is just outside the frame.
4. Let the user find the resource, the shift, or the next question. Do not translate the metaphor back to behavioral terms unless the user moves there themselves.

## A2UI Composition
Opening component: `ProtocolPromptComponent`
- `observation`: mirror the user's metaphor verbatim, no paraphrase
- `question`: a Clean-Language-style question staying inside the metaphor (e.g., "what kind of fog?", "and when the balloon is losing air, what happens just before?")

Mid-turn components: one `text_input` for the user's elaboration. No structured inputs — structure kills the metaphor.

Payload metadata (required):
- `surface`: `"intervention"`
- `intervention_kind`: `"metaphor-collaboration"`

Layout: `"three-quarter"`.

## Guardrails
- Never change the source domain. If the user says "balloon", do not shift to "battery", "engine", or any other vehicle. You may add resource inside the balloon world; you may not switch worlds.
- Never translate the metaphor back to behavioral terms on the user's behalf. The user crosses the bridge, or the bridge stays uncrossed.
- Do not interpret the metaphor psychoanalytically ("this represents your unmet need for..."). The metaphor is the meaning, not a proxy for it.
- Record the user's recurring metaphors in `/user/coach/AGENTS.md` under Coaching Notes zone: `[MM-DD] metaphor: "<verbatim>"`. This supports long-arc continuity.
- Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it.

## Deeper References
- `references/theory.md` — Western frameworks (Lakoff & Johnson CMT, Grove Clean Language, ACT metaphor usage) and Eastern cultural parallels (诗经比兴, 庄子寓言, 禅宗公案, 中医取象比类). Read when the user produces a novel metaphor type you want to handle well.
