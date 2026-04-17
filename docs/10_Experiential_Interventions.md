# 体验式干预手段应用方案

本文件给出四种体验式干预手段（未来自我对话、场景预演、隐喻协作、认知重构）在 Voliti 中的落地规格。定位为实施规格；学术依据参见 `docs/experiential-interventions/`。目标读者是实施者（Coach、code-reviewer、前端开发）。

## 1. 架构一览

| 组件 | 位置 | 职能 |
|---|---|---|
| Skill 定义 | `backend/skills/coach/<skill-name>/SKILL.md` | 四份独立 skill，渐进式披露 |
| Skill 深度参考 | `backend/skills/coach/<skill-name>/references/theory.md` | 从 `docs/experiential-interventions/` 物理复制，按需加载 |
| Middleware | `deepagents.middleware.skills.SkillsMiddleware` | 自动注入 skill 元数据到 Coach 系统提示词（仅 coaching session；onboarding 薄条件包装跳过注入）|
| Backend 路由 | `CompositeBackend` 新增 `/skills/coach/` → 只读 `FilesystemBackend` | 挂载 skill 目录；Coach 对该路径只读，禁止写入 |
| Coach 入口节 | `coach_system.j2` 新增 `## Experiential Interventions` 小节（14 行） | 触发门槛 + 优先级 + 硬停 + 节奏 |
| A2UI 差异化 | `A2UIPayload.metadata["surface"]` 约定 `"intervention"` + `intervention_kind` | 前端渲染差异化 |

## 2. Coach 系统提示词入口节（成品）

插入位置：`backend/prompts/coach_system.j2` 现有 Section 3（Coaching Framework）之后、Section 4（Tools）之前。

```jinja
<!-- ═══════════════════════════════════════════════════════════════════ -->
<!-- SECTION 3.5: Experiential Interventions                           -->
<!-- ═══════════════════════════════════════════════════════════════════ -->

## Experiential Interventions

Four skills extend you beyond dialogue and information.
Their descriptions are auto-injected above; read a skill's SKILL.md
when a situation matches its trigger.

### Before invoking any intervention
- State Before Strategy applies — dysregulated users need co-regulation, not technique.
- Interventions amplify existing motivation; they do not manufacture it.

### Picking a skill
When multiple fit, pick the one closest to what the user needs next,
not the most theoretically fitting.

### Hard stops
No intervention during: mental-health crisis, explicit refusal, end-of-session fatigue.

### Rhythm
At most one intervention skill per session. Let it settle before stacking another.
```

**Rhythm 与 Hard stops 无运行时强制**：节奏与硬停仅作为 prompt 层约束存在，无 middleware 或 tool 级检测。Coach 自律为第一道防线；后续 eval 扩展需补一条"同一 thread 二次干预"作为 FAIL 维度，作为第二道防线。

## 3. A2UI 契约增量

`backend/src/voliti/a2ui.py` 中 `A2UIPayload.metadata: dict[str, str]` 类型保持不变，新增两条语义约定：

| key | 取值 | 语义 | 必需性 |
|---|---|---|---|
| `surface` | `"onboarding"` / `"coaching"` / `"intervention"` / `"witness-card"` | A2UI 交互形态 | 干预与 Witness Card 场景必需；缺失时前端降级为 `"coaching"` 视觉 |
| `intervention_kind` | `"future-self-dialogue"` / `"scenario-rehearsal"` / `"metaphor-collaboration"` / `"cognitive-reframing"` | 手法级细分 | 仅当 `surface="intervention"` 时必需 |

**运行时契约边界**：`metadata` 键由 `A2UIPayload.metadata: dict[str, str]` 透传，后端 `validate_a2ui_response` 仅校验 `data` 字段，**不做 metadata 键级验证**。`surface` 与 `intervention_kind` 的写入依赖 Coach 系统提示词约束与后续 eval 覆盖；为防止静默漏填，payload 构造侧应加最小断言：若 `surface="intervention"` 必带 `intervention_kind`。

**开场原语**：四手法的 fan_out 首条组件固定为 `ProtocolPromptComponent`（`observation` + `question` 字段）。

**Layout 建议**：`future-self-dialogue` 用 `layout: "full"`（仪式感）；其他三手法用 `layout: "three-quarter"`（工作对话）。

**字段扩展**：本轮不新增组件类型、不改现有字段定义、不新增 `layout` 档位。

## 4. 四份 SKILL.md 成品

以下四份 SKILL.md 为可直接写入 `backend/skills/coach/<skill-name>/SKILL.md` 的英文成品。

### 4.1 `backend/skills/coach/future-self-dialogue/SKILL.md`

```markdown
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
```

---

### 4.2 `backend/skills/coach/scenario-rehearsal/SKILL.md`

```markdown
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
Opening component: `ProtocolPromptComponent`
- `observation`: name the upcoming scenario as the user described it
- `question`: invite rehearsal with the user's consent

Mid-turn components, one or two of:
- `text_input` for obstacle surfacing
- `text_input` for the if-then response (user edits what Coach proposes)
- `select` for picking among 2-3 candidate responses when the user hesitates

Payload metadata (required):
- `surface`: `"intervention"`
- `intervention_kind`: `"scenario-rehearsal"`

Layout: `"three-quarter"` — rehearsal is working dialogue, not ceremonial.

## Guardrails
- The if-then must be small enough that the user can picture doing it without effort. If the user says "I'll resist dessert entirely" you have gone too abstract — bring it back to one specific bodily action.
- Do not rehearse willpower. Rehearse the environmental move, the first 90 seconds, or the exit ritual.
- Never rehearse a scenario the user has not named. Coach cannot generate the scenario — only refine it.
- After the session, if the event passed and the user lapsed, do not re-rehearse the same plan. Explore why and revise the LifeSign.
- Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it.

## Deeper References
- `references/theory.md` — Western protocols (MCII, WOOP, Implementation Intentions, Coping Planning, Episodic Future Thinking) and Eastern cultural parallels (庙算, 慎独, 豫则立, 禅宗日课, 中医取象比类). Read when calibrating depth or explaining rationale.
- `references/dialogue-examples.md` — one academically documented teaching dialogue (WOOP / MCII source). Read when you encounter a novel scenario and want to see a documented form.
```

---

### 4.3 `backend/skills/coach/metaphor-collaboration/SKILL.md`

```markdown
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
```

---

### 4.4 `backend/skills/coach/cognitive-reframing/SKILL.md`

```markdown
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
Opening component: `ProtocolPromptComponent`
- `observation`: quote the user's catastrophizing sentence directly, verbatim
- `question`: surface the "=" in their sentence and ask whether they consciously signed it

Mid-turn components, one or two of:
- `text_input` for the user's new frame (they write it, not you)
- `select` for picking between 2-3 candidate frames when the user hesitates
- No slider — reframing is not measured

Payload metadata (required):
- `surface`: `"intervention"`
- `intervention_kind`: `"cognitive-reframing"`

Layout: `"three-quarter"`.

## Guardrails
- Never dispute the user's feelings. Dispute the inferential leap, not the pain.
- Never impose a positive reframe. "You did great" replaces one distortion with another. Offer a neutral, information-carrying frame instead.
- Never reframe toward "you should have known better". Information, not blame.
- If the user resists the reframe three times, stop. Their current frame contains something the new one is missing — ask what.
- Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it.

## Deeper References
- `references/theory.md` — Western grounding (Beck CBT, Ellis REBT ABC model, Paivio Dual-Coding, MBCT variant) and Eastern cultural parallels (佛教观心, 王阳明格物致知, 金刚经应无所住, 森田疗法). Also contains the distinction between reframing and toxic positivity. Read when the user asks rationale or an edge case challenges the method.
```

## 5. 代码落地清单

### 5.1 后端

| 文件 | 动作 |
|---|---|
| `backend/src/voliti/agent.py` | `_create_backend_factory` 新增 `/skills/coach/` 路由（只读 `FilesystemBackend`）；`_build_coach_middleware` 插入 `SkillsMiddleware`（位置：`SessionTypeMiddleware` **之后**，仅在 coaching session 注入 —— 薄条件包装，onboarding 跳过）|
| `backend/src/voliti/store_contract.py` 或新建 `backend/src/voliti/fs_paths.py` | 集中定义 `COACH_SKILLS_ROOT` 常量（与现有 `BRIEFING_FILE_PATH` 等非 Store-key 路径并置），避免跨目录相对路径硬编码 |
| `backend/prompts/coach_system.j2` | Section 3 之后新增 §2 所示入口节；Section 4（Tools）补一句 "`/skills/` 前缀是内置能力库，只读，不可写入"；Section 6（Memory Write Protocol）Coaching Notes 区授权 `[MM-DD] metaphor: "<verbatim>"` 作为 metaphor-collaboration skill 的合法扩展格式 |
| `backend/src/voliti/tools/experiential.py` | Witness Card payload 的 `metadata` 补 `surface="witness-card"`，与本次 `surface` 四取值对齐，防止前端降级误判 |
| `backend/skills/coach/future-self-dialogue/SKILL.md` | §4.1 内容 |
| `backend/skills/coach/scenario-rehearsal/SKILL.md` | §4.2 内容 |
| `backend/skills/coach/metaphor-collaboration/SKILL.md` | §4.3 内容 |
| `backend/skills/coach/cognitive-reframing/SKILL.md` | §4.4 内容 |
| `backend/skills/coach/<4 个>/references/theory.md` | 从 `docs/experiential-interventions/0X_*.md` 物理复制。`docs/knowledge/` 为真相源 |
| `backend/skills/coach/scenario-rehearsal/references/dialogue-examples.md` | 仅该手法提取 WOOP 教学对话片段，标注来源（其他三手法无学术对话样本，不建此文件）|
| `backend/tests/test_skills_sync.py`（新建）| CI 校验脚本：对 `backend/skills/coach/<name>/references/theory.md` 与 `docs/experiential-interventions/0X_*.md` 做字节级 diff（或 hash 比对）；不一致则失败。防止真相源与 backend 复制品静默 drift |
| `backend/tests/test_agent.py` | 新增单测：`SkillsMiddleware` 装配；四份 skill 加载；**onboarding session 的 system prompt 不含 `## Skills System` 字样**；`surface="intervention"` 时 `intervention_kind` 必填的构造侧断言 |

### 5.2 前端

| 文件 | 动作 |
|---|---|
| A2UI 类型定义 | `metadata` 增加类型注释，约定 `surface` 与 `intervention_kind` 可选 key（具体路径由实施阶段探查）|
| A2UI 渲染层 | 新增 `surface=="intervention"` 分支：独立视觉外壳、更多留白、延迟揭示、仪式化动效。缺失或未识别时降级为 `"coaching"` 视觉 |

### 5.3 文档

| 文件 | 动作 |
|---|---|
| `docs/01_Product_Foundation.md` | 附录 A.4 末尾新增指向本文件的一行引用 |
| `docs/05_Runtime_Contracts.md` §8.5（新建）| "Surface 与 Intervention 分类"小节：列清 `surface` 四取值（`onboarding` / `coaching` / `intervention` / `witness-card`）、对应前端渲染分支、降级规则、`intervention_kind` 枚举（四手法）；与 §8.3 reject reason 并列 |
| `docs/03_Architecture.md` §5.4 | 在 DeepAgent 复用边界列表下新增子项 "Skills 机制（SkillsMiddleware + 只读 FilesystemBackend + `/skills/coach/` 路由；onboarding 不注入）" |
| `CLAUDE.md` / `AGENTS.md` | 变更记录各新增一行 |

## 6. 风险与回滚

| 风险 | 缓解 |
|---|---|
| SkillsMiddleware 注入使 token 预算上涨 | 监测生产 token 用量；必要时收紧 description 长度 |
| Coach 过度调用干预（"教育化"失陪伴感）| 入口节 Rhythm + Hard stops 硬约束；后续 eval 扩展时纳入观察 |
| 前端未及时支持 `metadata.surface` | 契约要求降级到 `"coaching"` 视觉，不阻断体验 |
| Skill 加载失败 | `SkillsMiddleware` 有容错（解析失败 warning 跳过）；单测覆盖装配与 YAML 解析 |
| 东方传统引用被用户理解为"学术对等" | Guardrails 禁止向用户提及任何理论名；分册 `theory.md` 内部已标注"借鉴性对应" |
| Witness Card 与 intervention 的 `metadata` 同 dict 共存造成渲染错乱 | `surface` 四取值集定死；Witness Card composer 必写 `surface="witness-card"`；前端分支按 surface 值分派，不依赖"有 card_id 即 Witness Card"的隐式约定 |
| 真相源 `docs/experiential-interventions/` 与 backend 复制品 drift | CI 校验脚本 `test_skills_sync.py` 在每次 CI 跑 diff；任何修改必须两边同步落盘 |

**回滚层级**：

- **仅前端**：前端忽略 `metadata.surface`，所有 payload 退化为默认视觉
- **SkillsMiddleware**：从 middleware 栈移除；入口节可保留自然失效
- **完整回滚**：`backend/skills/coach/` 目录保留但不挂载；入口节从 `coach_system.j2` 删除

所有改动不涉及 Store 迁移与数据契约破坏，回滚成本低。

## 7. 实施路线

| 里程碑 | 内容 | 预估工时 |
|---|---|---|
| M4 | `code-reviewer` + `architect-reviewer` 独立审校 | 0.5h |
| M5 | 合入审校意见，Dexter 终审本文件与分册 | 视反馈 |
| M6 | 后端落地（§5.1）+ 单测通过 | 2-3h |
| M7 | 前端 intervention 视觉外壳落地（§5.2）| 由视觉规格单独决定 |
| M8 | 端到端 QA：四手法在真实 Coach 对话中的触发、A2UI 渲染、LifeSign 写入回路 | 1h |

每个里程碑之后暂停，交 Dexter 审后再进入下一步。
