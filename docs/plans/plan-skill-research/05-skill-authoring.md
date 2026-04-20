<!-- ABOUTME: Plan Skill 撰写最佳实践手册，覆盖架构、文件结构、渐进披露、工具与 references 边界 -->
<!-- ABOUTME: 综合 Anthropic 官方 skill-creator 方法论与 Voliti 现有 5 份 SKILL.md 共性模板，为 Plan Skill 推荐差异化骨架 -->

# Plan Skill 撰写最佳实践手册

本手册为 Plan Skill 的准备阶段提供撰写范式。内容分为五部分：Anthropic 官方方法论摘要、Voliti 现有五份 SKILL.md 共性模板、Plan Skill 的差异化特点、推荐骨架、共建 UX 在 SKILL.md 里的表达范式。

---

## 一、Anthropic 官方 skill-creator 方法论摘要

以下关键段落来源于本地缓存的官方 skill-creator SKILL.md（`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md`），引用原文以保持权威性。

### 1. Frontmatter 规范

官方明确 frontmatter 必填字段仅为 `name` 与 `description`，其他字段按需扩展：

> - **name**: Skill identifier
> - **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body.
> - **compatibility**: Required tools, dependencies (optional, rarely needed)

### 2. description 怎么写

description 是 skill 被正确触发的**唯一入口**，官方给出明确的反欠触发指引：

> Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"

关键要素：**做什么（what）+ 触发语境（when to use）+ 明确否定条件（when not to use）**，所有"何时使用"的信息都写在 description，不能放在正文，因为 description 是主调度机制，正文只在被触发后才进入上下文。

### 3. Progressive Disclosure（渐进披露）

官方定义三层加载系统：

> Skills use a three-level loading system:
> 1. **Metadata** (name + description) - Always in context (~100 words)
> 2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
> 3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

关键约束：

> - Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
> - Reference files clearly from SKILL.md with guidance on when to read them
> - For large reference files (>300 lines), include a table of contents

多变体领域按变体组织 references：

> **Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
> ```
> cloud-deploy/
> ├── SKILL.md (workflow + selection)
> └── references/
>     ├── aws.md
>     ├── gcp.md
>     └── azure.md
> ```

### 4. references / assets / scripts 边界

官方在 Anatomy of a Skill 明确三者定位：

> ```
> skill-name/
> ├── SKILL.md (required)
> │   ├── YAML frontmatter (name, description required)
> │   └── Markdown instructions
> └── Bundled Resources (optional)
>     ├── scripts/    - Executable code for deterministic/repetitive tasks
>     ├── references/ - Docs loaded into context as needed
>     └── assets/     - Files used in output (templates, icons, fonts)
> ```

三者的本质差异：

| 目录 | 用途 | 何时加载 | 是否进上下文 |
|------|------|----------|--------------|
| `scripts/` | 确定性/重复性任务的可执行代码 | Coach 通过工具调用执行 | 代码本身不进上下文，输出结果进 |
| `references/` | Coach 按需查阅的说明文档 | Coach 主动 `Read` 时加载 | 是，但仅在 Coach 判断需要时 |
| `assets/` | 输出产物直接使用的文件 | 作为渲染/复制素材 | 内容不进上下文，文件被引用或拷贝 |

重要原则："**scripts can execute without loading**"——脚本即便庞大也不会占用 context window，是长工程逻辑的理想载体。

### 5. 写作风格

官方反对僵硬的 MUST：

> Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples.

> If you find yourself writing ALWAYS or NEVER in all caps, or using super rigid structures, that's a yellow flag — if possible, reframe and explain the reasoning so that the model understands why the thing you're asking for is important. That's a more humane, powerful, and effective approach.

---

## 二、Voliti 现有 5 份 SKILL.md 共性模板

### 2.1 Frontmatter 对比

| 字段 | future-self-dialogue | scenario-rehearsal | metaphor-collaboration | cognitive-reframing | witness-card |
|------|----------------------|--------------------|-----------------------|---------------------|--------------|
| `name` | future-self-dialogue | scenario-rehearsal | metaphor-collaboration | cognitive-reframing | witness-card |
| `description` 结构 | 一句动词句 + 触发四情境 + Do not use 三条 | 一句动词句 + 触发四情境 + Do not use 四条 | 一句动词句（含"only when"） + 触发三情境 + Do not use 四条 | 一句动词句 + 触发五情境 + Do not use 三条 | 一句动词句 + 触发四情境 + Do not use 三条 |
| `license` | internal | internal | internal | internal | 无 |

共性模式：description 遵循严格的"**动词短句 + When to Use 触发条件 + Do not use 否定条件**"三段结构；否定条件往往指向其他兄弟 skill（例："try cognitive-reframing first"），形成清晰的分诊图。

### 2.2 章节顺序共性

五份 SKILL.md 的章节顺序高度一致，提炼如下：

```
# <Skill 名称>

## When to Use
- 触发情境 1
- 触发情境 2
- ...

## When NOT to Use（或 When Not To Use）
- 否定条件 1
- 否定条件 2
- ...

## Core Move（或 Core Principles / Input Rules）
1. 步骤 1
2. 步骤 2
3. ...

## A2UI Composition（或 Decision Rules / Relationship To Other Skills）
工具调用 + 组件序列 + 前端渲染映射说明

## Guardrails
- 禁止项 1
- 禁止项 2
- ...

## Deeper References（或 Further Reading）
- references/xxx.md — 何时读取的指引
```

`witness-card` 因不是"对话 move"而是"卡片发放", 略有差异——它用 `Input Rules` 替代 `Core Move`, 用 `Decision Rules` 与 `Relationship To Other Skills` 替代 `A2UI Composition` 与部分 `Guardrails`。这证明"章节按 skill 语义差异可调整"，但**骨架三要素不变**：Why（When to Use / When NOT to Use）、How（Core Move）、约束（Guardrails）、延伸（Deeper References）。

### 2.3 A2UI Composition 写法范式

四份干预 skill 使用同一套范式：

1. **声明专用工具**：`fan_out_<kind>(components=[...])`
2. **声明自动注入字段**：`surface="intervention"` / `intervention_kind="<kind>"` / `layout="full"` 由代码硬编码，禁止 Coach 重复传递
3. **列举组件序列**：按前端渲染顺序（position 或 kind）逐项说明
4. **给出禁止项**：说明哪些组件不适用（如 future-self "no slider, no multi_select"；metaphor "do not attach slider, select, multi_select, or number_input — structure kills the metaphor"）

原文示例（future-self-dialogue）：

```
Invoke the dedicated tool `fan_out_future_self_dialogue(components=[...])`. The tool
injects `surface="intervention"`, `intervention_kind="future-self-dialogue"`, and
`layout="full"` automatically — do not pass metadata or layout.

Component sequence (the frontend maps these to the three-column layout by kind):
1. `TextComponent` — a memory quote the user has said ...
2. `ProtocolPromptComponent` — rendered as the copper-edged right column ...
3. `TextInputComponent` — the user's narrative reply ...

No slider, no multi_select, no select — future-self work is narrative, not measured.
```

### 2.4 references 目录范式

| Skill | references/ 内容 | 行数级别 |
|-------|-------------------|---------|
| future-self-dialogue | theory.md（单一理论文件） | 约 500 行 |
| scenario-rehearsal | theory.md + dialogue-examples.md | 约 900 行 + 50 行 |
| metaphor-collaboration | theory.md | 约 800 行 |
| cognitive-reframing | theory.md | 约 500 行 |
| witness-card | positioning.md + visual-system.md + evidence-rubric.md + narrative-examples.md | 各 20~30 行 |

**两种范式对比：**

- **干预类（四份）**：references 以"theory.md 单一长文件"为主，结构为"1. 理论基础（西方主流轴 / 东方传统视角）→ 2. 标准使用方法 → 边界与风险"。目的是让 Coach 在被用户追问"为什么这样做"或遇到陌生场景时，主动 Read 得到深度支撑。
- **Witness Card**：references 拆为多个微小文件（每个 < 30 行），每个文件回答一个独立问题（定位 / 视觉 / 证据门槛 / 叙事范例）。SKILL.md 正文对每个文件标注"何时读"。这是因为 witness-card 的输入是结构化字段而非对话 move，不需要大量理论支撑，反而需要精准的产出模板与反面示例。

**选型原则**：单个主题、深度连贯 → 单 theory.md；多个独立小切片、Coach 按需单选 → 多个微小文件 + SKILL.md 明确路标。

### 2.5 文案风格共性

- **否定式约束的语言**：用"Do not"、"Never"的短句列表，但在 Guardrails 里同时解释"为什么"（例：`"Never anchor on appearance, weight, or body shape. Anchor on capability, rhythm, relationships, and small daily rituals."`）。这与官方"explain the why"原则一致。
- **引用用户原话**：干预 skill 反复强调"in the user's own words"、"verbatim"、"no paraphrase"，保护用户语言主权。
- **跨 skill 互引**：description 与正文主动指向其他 skill，形成分诊图（例：cognitive-reframing 的"try cognitive-reframing first"）。
- **方法论隐身**：共性 Guardrails 条款——"Do not reference method names (including abbreviations) or researcher surnames to the user. Use the method without naming it."

---

## 三、Plan Skill 的差异化特点

Plan Skill 与干预类 skill 存在本质差异，撰写时必须明确表达这些差异，否则触发器会与干预类 skill 冲突。

### 3.1 核心机制差异

| 维度 | 干预类 skill | Plan Skill |
|------|--------------|-----------|
| 触发场景 | 对话中的单次 move（识别 → 展开 → 关闭） | 结构化方案生成 + 持续编辑（跨会话） |
| 产出形态 | A2UI 面板，单轮内完成 | Store 中的长期方案文档 + 阶段性增量编辑 |
| 用户参与 | 单轮内即时响应 | 共建讨论 → 保存 → 多日后复查修订 |
| 状态生命周期 | 会话级（无持久化结构） | 持久化（Store 契约 + 版本增量） |
| Coach 角色 | 对话引导者 | 文档起草人 + 协商伙伴 + 编辑员 |

### 3.2 SKILL.md 需要新增表达的维度

- **Plan 的生命周期**：生成（generate） / 查阅（review） / 调整当周（update current phase） / 跨阶段修订（tweak phase） / 归档（complete and close）
- **与 Chapter 的关系**：Plan 是 Chapter 下的执行蓝图，不能脱离 Chapter 独立存在
- **编辑的最小颗粒度**：哪些字段可被编辑、哪些只能整体重生成
- **协商而非独断的姿态**：Coach 不能在用户未明确确认前覆盖已持久化的字段

### 3.3 与干预类 skill 的触发分界

Plan Skill 的 description 必须明确让 Coach 在以下场景**不要误用干预类 skill**：

- 用户说"帮我做一个 12 周减脂计划" → Plan Skill，不是 scenario-rehearsal
- 用户说"这周的安排我想调一下" → Plan Skill 的 update 分支，不是 cognitive-reframing
- 用户说"我想规划一下第 5 周之后的过渡" → Plan Skill 的 tweak phase 分支

反之，以下场景要让 Plan Skill **让位**：

- 用户正处于 lapse + 自责 → cognitive-reframing
- 用户对"未来完成后"没有画面 → future-self-dialogue（先锚定动机再做 plan）
- 用户要预演某次具体高风险场景 → scenario-rehearsal

---

## 四、推荐骨架

### 4.1 文件结构

```
plan-design/
├── SKILL.md                              # 主 skill 文档，精简 <300 行
├── tool.py                               # 专用工具集（generate/update/tweak 等）
├── references/
│   ├── plan-architecture.md             # Plan 的数据结构、字段语义、Store 契约映射
│   ├── phase-templates.md               # 典型阶段模板（适应期 / 减脂期 / 巩固期 / 自由期）
│   ├── numeric-guidelines.md            # 热量赤字、周减重、训练负荷等数值安全边界
│   ├── edit-protocol.md                 # 编辑协商规则（何时整体重生成 / 何时局部更新）
│   └── example-plans.md                 # 2-3 个真实风格的完整示例（而非空模板）
├── assets/
│   ├── default-phases.json              # 默认阶段骨架（代码初始化时使用）
│   └── phase-template-skeletons/        # 各阶段的字段骨架 JSON（生成时作为种子）
└── scripts/
    └── compute_phase_metrics.py         # 可选：确定性指标计算（总赤字、平均周减重等）
```

**边界判断**：
- `phase-templates.md` 是文本化的**说明**（为什么这样设计阶段，边界是什么） → 属于 references
- `default-phases.json` 是**可复制的种子数据** → 属于 assets
- `compute_phase_metrics.py` 是**确定性计算** → 属于 scripts（对应官方"deterministic/repetitive tasks"）

### 4.2 推荐 frontmatter

```yaml
---
name: plan-design
description: Co-author and maintain the user's multi-phase fat-loss plan under an active Chapter. Use when the user asks to build a plan, review an existing plan, adjust the current phase, revise an upcoming phase, or reconcile the plan with a newly set Chapter/Goal. Also use when Coach detects plan-reality drift — observed behavior materially deviates from the current phase for 3+ days. Do not use when no active Chapter exists (run the Chapter skill first), when the user is lapsed and self-blaming (try cognitive-reframing first), when motivation itself is foggy (try future-self-dialogue first), or when the user only needs a single-event rehearsal (use scenario-rehearsal).
license: internal
---
```

要点说明：
- `co-author and maintain` 直接传达"共建 + 编辑"的双面性，避免 Coach 误以为 Plan 是一次性生成
- 触发语境涵盖五类：build / review / adjust current / revise upcoming / reconcile with Chapter；补一条"drift 检测"作为 Coach 主动触发点
- 否定条件明确导向其他 skill，形成分诊
- `under an active Chapter` 隐式表达"Plan 是 Chapter 的下位概念"的架构契约

### 4.3 章节结构

```
# Plan Design

## When to Use
（5-6 条触发情境，每条引用 Chapter/Goal 层概念，让触发与当前上下文绑定）

## When NOT to Use
（4-5 条否定条件，明确指向其他 skill）

## Core Move
（Plan 不是单次 move，而是状态机；此处改写为"五种动作"）
Plan Skill 有五种核心动作，Coach 根据用户意图与 Plan 当前状态选择其一：
1. generate — 全新生成：用户未有 Plan 或明确请求重做
2. review — 只读查阅：用户想看看当前 Plan 的内容
3. update_current_phase — 微调当前阶段的字段（非结构性）
4. tweak_phase — 修改某个尚未到达的未来阶段
5. close — 当 Chapter 关闭时，同步归档 Plan

任何动作之前，先显式读取 Store 的 `plan_current.value.json`。

## Negotiation Contract
（共建契约，详见第五节）

## A2UI / Tool Composition
（调用范式，详见 4.4）

## Store Contract
（Plan 的持久化契约，指向 references/plan-architecture.md）
- Store key: `plan_current.value.json`（单一当前版本）
- Field 级别的可编辑范围与只重生成范围见 references/edit-protocol.md

## Guardrails
- 永不在用户未确认前覆盖已持久化字段
- 永不绕过 Chapter 直接操作 Plan
- 永不在 plan-reality drift 未被用户确认前单方面"修正"Plan
- 永不使用打卡 / streak / 连续天数语言
- 永不引用研究方法名或学术术语给用户
- 热量 / 负荷数值必须引用 references/numeric-guidelines.md 中的安全区间

## Deeper References
- `references/plan-architecture.md` — 读取时机：任何 generate/tweak 动作前
- `references/phase-templates.md` — 读取时机：选择阶段组合时
- `references/numeric-guidelines.md` — 读取时机：写入任何数值前
- `references/edit-protocol.md` — 读取时机：任何 update/tweak 动作前
- `references/example-plans.md` — 读取时机：Coach 想校准生成风格时
```

### 4.4 工具层设计

参考 `fan_out_future_self_dialogue` 的"专用工具 + 代码硬编码元字段"范式，Plan Skill 应提供一组动词化工具，而非单一大工具：

| 工具 | 职责 | 元字段注入 |
|------|------|-----------|
| `draft_plan(chapter_id, phase_proposals)` | 生成草稿（不直接写 Store，返回给 Coach 给用户审核） | `surface="plan-draft"` / `intervention_kind="plan-design"` |
| `commit_plan(plan_draft)` | 用户确认后写入 Store，通过契约校验层 | Store 写入调用 `store_write_validated()` |
| `update_current_phase(field_patches)` | 局部字段级更新；拒绝结构性改动 | 返回更新后全貌给 Coach |
| `tweak_phase(phase_index, patches)` | 未来阶段微调；拒绝改动已开始的阶段 | 同上 |
| `compute_plan_preview(phase_proposals)` | 调用 `scripts/compute_phase_metrics.py`，返回总赤字、预期周减重等 | 纯计算，不写入 |

**工具层的差异化约束**（相对干预类 skill）：
- Plan 工具不使用 `fan_out_*` 命名约定，因为它们的职责是数据层操作而非 A2UI 面板渲染
- draft/commit 分离确保"协商"语义：用户未确认前不落盘
- 计算工具独立，避免 Coach 凭空捏造数值

### 4.5 references / assets / scripts 填充建议

**references/（Coach 按需加载的文档）：**

- `plan-architecture.md`：Plan 的数据模型、字段语义、与 Chapter/Goal/LifeSign 的关系、Store 契约映射。长度 200~400 行，开头放目录。
- `phase-templates.md`：4~6 种典型阶段组合模板，每种说明适用画像、阶段长度、过渡条件。
- `numeric-guidelines.md`：热量赤字范围、周减重安全值、训练负荷增量上限。硬数据表。
- `edit-protocol.md`：可编辑字段矩阵（哪些 update 可改 / 哪些只能 tweak / 哪些必须 regenerate）+ 协商语言范例。
- `example-plans.md`：2~3 个完整 Plan 示例，对应不同画像（新手 / 有基础 / 复发期回归）。

**assets/（输出产物直接使用的文件）：**

- `default-phases.json`：空壳 JSON，`draft_plan` 从此起始
- `phase-template-skeletons/*.json`：各阶段字段骨架，供 draft 填充

**scripts/（确定性计算）：**

- `compute_phase_metrics.py`：总赤字、平均周减重、总训练量、阶段过渡可行性校验

是否需要 scripts？判断依据：该逻辑是否"每次调用都应得到相同输出"。数值计算 / 契约校验符合此标准 → 放 scripts；阶段模板描述、风格示例不符合 → 放 references 或 assets。

---

## 五、共建 UX 在 SKILL.md 里的表达范式

Plan Skill 的核心场景是"Coach + 用户共建"，而不是 Coach 单方面生成后交付。SKILL.md 必须用规则+范例+禁止项三层把这一约束"写进"skill 的执行逻辑。参考 future-self-dialogue 的"let the user find the resource"原则，但 Plan 层的协商涉及数据持久化，更加结构化。

### 5.1 在 Core Move 里嵌入协商节奏

建议在 `Core Move` 之后紧跟一节 `Negotiation Contract`：

```markdown
## Negotiation Contract

Plan 不是 Coach 独自生成的蓝图，是 Coach 与用户共同写下的东西。每一个 generate / tweak 动作都遵循"提议 → 审议 → 确认 → 落盘"四拍：

1. **提议（draft）** — Coach 生成一份草稿，明确说"这是一个草稿，不是最终版本"。使用 draft_plan 工具返回内容，不触发 Store 写入。
2. **审议（discuss）** — 用户阅读草稿。Coach 逐阶段请用户确认或修订。一次只就一个阶段或一个字段讨论；避免要求用户一次性审核全部字段。
3. **确认（confirm）** — 用户显式说"就这样" / "可以" / "保存"之后，Coach 调 commit_plan 写入。模糊语言（"看着差不多"）不算确认；Coach 重述一次确认点，等待用户再次明确。
4. **落盘（persist）** — commit_plan 通过契约校验层写入 Store。写入后 Coach 用一句"已保存。你可以在下次对话里调整任何阶段"收尾。

在 update_current_phase 与 tweak_phase 中，"提议 → 确认 → 落盘"仍然完整，只是"审议"可以压缩为一轮。
```

### 5.2 在 Guardrails 里明文禁止独断

```markdown
## Guardrails
- 永不在用户未显式确认前调用 commit_plan。"我觉得可以了""差不多"不构成确认。
- 永不一次性让用户审议完整 Plan。按阶段拆分：先适应期 → 等用户确认 → 再减脂期……
- 永不在用户提出修改后立即覆盖原字段。先镜像用户的修改意图回去：「你是说把第 4 周的周目标从 0.5kg 改成 0.3kg？」等用户确认后再调 update_current_phase。
- 永不在 drift 发生时单方面修订 Plan。先与用户对齐："这两周你的训练频率比 Plan 里写的少了一半。我们是调整 Plan，还是找回原节奏？"
- 永不使用"我已经帮你调整好了"的措辞；使用"我起草了一版，你看看"。
```

### 5.3 在 references/edit-protocol.md 里提供协商语言范例

从 future-self-dialogue 的 references/theory.md 学到："给 Coach 示例比给约束更有效"。建议 edit-protocol.md 中给出至少 5~8 组**协商话术对照**：

```
❌ "我把第 3 周的热量赤字提到 500 千卡了。"
✅ "看你的反馈，第 3 周似乎还有余地。如果把赤字从 400 提到 500 千卡，你觉得合适吗？"

❌ "这周你没完成训练，我帮你把频率调低了。"
✅ "这周训练频率低于 Plan。是这周有特殊情况，还是 Plan 里 4 次 / 周一开始就偏高了？我们可以一起看看。"

❌ "Plan 已更新。"
✅ "已保存。第 3 周的赤字改成了 500 千卡，其他保持不变。"
```

### 5.4 与官方"解释 why"原则对齐

在 `Negotiation Contract` 节结尾补一段说明，避免 Coach 把协商规则当成僵硬流程：

> Plan 涉及用户数月的行为，它的每一次修改都会回到用户的生活。协商姿态不是礼貌形式，而是防止 Plan 变成另一个"别人替我写好的计划"——正是用户在前 N 段减脂经历里已经失败的那种东西。用户对 Plan 的所有权是 Plan 能持续服务用户的前提。

这一段是整个 SKILL.md 里对 Coach 解释"为什么这样做"的灵魂，取代任何 ALWAYS / NEVER。

---

## 六、撰写检查清单

撰写 Plan Skill SKILL.md 完成后，按以下清单自检：

- [ ] Frontmatter 的 description 是否明确包含 "co-author and maintain" 或等价表述？
- [ ] When to Use / When NOT to Use 是否覆盖与四种干预 skill 的分界？
- [ ] Core Move 是否按五种动作（generate/review/update/tweak/close）而非单次流程展开？
- [ ] 是否有独立的 Negotiation Contract 章节说明四拍节奏？
- [ ] Guardrails 是否明文禁止"未确认前写入"与"独断式措辞"？
- [ ] A2UI / Tool Composition 是否区分 draft_plan（无副作用）与 commit_plan（写入）？
- [ ] Store Contract 是否指向契约校验层的 `store_write_validated()`？
- [ ] references 是否按"为什么 / 模板 / 数值安全 / 编辑规则 / 范例"五档分文件？
- [ ] 主 SKILL.md 是否控制在 300 行以内，并在每个 reference 标注"何时读"？
- [ ] 全文是否避免了 ALWAYS / NEVER 大写祈使句，改以"why"解释？
- [ ] 是否避免了打卡 / streak / 连续天数语言？

---

## 附录：关键路径索引

- 官方 skill-creator SKILL.md：`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/SKILL.md`
- 官方 references/schemas.md：`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/references/schemas.md`
- Voliti 干预类 skill 根目录：`backend/skills/coach/{future-self-dialogue,scenario-rehearsal,metaphor-collaboration,cognitive-reframing,witness-card}/`
- Voliti 工具层范式：`backend/skills/coach/future-self-dialogue/tool.py`
- Voliti SkillsGate（按 session_type 注入）：`backend/src/voliti/middleware/skills_gate.py`
- Voliti Store 契约校验层：`backend/src/voliti/contracts/`（Plan Skill 需新增 `PlanRecord` 模型）
