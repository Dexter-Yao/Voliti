---
name: cognitive-reframing
description: Re-pattern the meaning of a lapse, a distortion, or a catastrophic self-narrative by surfacing the inferential leap and offering a new frame alongside the original. Use after a lapse when the user is self-attacking in language, when catastrophizing or black-white thinking is present, during post-failure review, during end-of-chapter review dominated by a single failure, or when the user asks "what does this mean" about their own behavior. Do not use during active dysregulation (State Before Strategy supersedes), when the user has not been invited to reflect, or when the user has already accepted the lapse and moved on.
license: internal
---

# Cognitive Reframing

## When to Use
- User has just lapsed and is attacking themselves in language
- Catastrophizing: one event becomes an entire identity verdict ("I always fail", "this ruined everything")
- Black-and-white thinking: the middle has been erased from the frame
- End-of-Chapter review where one failure dominates the narrative
- User asks "what does this mean" about their own behavior

## When NOT to Use
- State is not stable — State Before Strategy supersedes. Co-regulate first.
- User is using a self-harming frame but is also dysregulated — stay with empathy; reframe only after stabilization
- User has not been invited to reflect — an unsolicited reframe feels like correction
- Mental-health crisis signal in the session
- User has already accepted the lapse and moved on — do not create friction by reopening it

## Core Move
1. Name the current frame in the user's own words. Repeat the sentence they said — no paraphrase, no softening.
2. Show the inferential leap. Make visible the "=" the user signed: one event = verdict, one lapse = identity, one failure = progress erased.
3. Invite a second frame. Do not replace the first. Place a new reading next to it and let the user choose.
4. Let the user decide whether the new frame fits. If they reject it, do not insist — ask what frame does feel accurate, and work with that.
5. Close by naming one concrete observation the lapse actually contains — information, not verdict.

## A2UI Composition

Invoke the dedicated tool `fan_out_cognitive_reframing(components=[...])`. The tool
injects `surface="intervention"`, `intervention_kind="cognitive-reframing"`, and
`layout="full"` automatically — do not pass metadata or layout.

Component sequence (the frontend maps these to the side-by-side frame layout by
position):

1. `ProtocolPromptComponent`
    - `observation`: quote the user's catastrophizing sentence directly, verbatim.
      Rendered as the upper-left frame ("what you just said").
    - `question`: surface the "=" and ask whether they consciously signed it.
      Rendered as the center inquiry under the frames.
2. `TextComponent` — a brief reading of the implicit verdict inside the original
   sentence ("what this sentence is really saying"). Rendered as the upper-right
   frame. **Strongly recommended**: omitting this component leaves the right frame
   as a greyed placeholder and weakens the "=" visibility.
3. Zero or more of:
    - `SelectComponent` — 2-3 alternative readings as options (lower row, "other
      readings to place beside yours")
    - `TextInputComponent` — the user writes their own new frame (lower row)
    - No slider — reframing is not measured

## Guardrails
- Never dispute the user's feelings. Dispute the inferential leap, not the pain.
- Never impose a positive reframe. "You did great" replaces one distortion with another. Offer a neutral, information-carrying frame instead.
- Never reframe toward "you should have known better". Information, not blame.
- If the user resists the reframe three times, stop. Their current frame contains something the new one is missing — ask what.
- Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it.

## Deeper References
- `references/theory.md` — Western grounding (Beck CBT, Ellis REBT ABC model, Paivio Dual-Coding, MBCT variant) and Eastern cultural parallels (佛教观心, 王阳明格物致知, 金刚经应无所住, 森田疗法). Also contains the distinction between reframing and toxic positivity. Read when the user asks rationale or an edge case challenges the method.
