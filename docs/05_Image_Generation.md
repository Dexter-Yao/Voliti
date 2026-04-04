<!-- ABOUTME: Azure OpenAI gpt-image-1.5 技术实现指南，定义 API 参数、Subagent 架构、Prompt 模板与工程实践 -->
<!-- ABOUTME: 教练干预的理论基础与设计原则见 01_Product_Foundation.md 第二章、第六章与附录A -->

# gpt-image-1.5 技术实现指南

**前置阅读**：`/docs/01_Product_Foundation.md`第二节（理论基础）、第六节（Guardrail）、附录A（理论基础详细阐述）

本文档聚焦技术实现层：如何用 Azure OpenAI gpt-image-1.5 承载四类教练干预（未来自我对话、场景预演、隐喻协作、认知重构）。关于**为什么用这些干预方法**、**时机-内容-情感的设计原则**，请参考 01_Product_Foundation.md。

## 一、模型与 API 参数

| 参数 | 值 |
|------|-----|
| 部署名 | `gpt-image-1.5` |
| API 端点 | Azure AI Foundry（`AZURE_OPENAI_ENDPOINT`）|
| API 版本 | `2024-02-01` |
| 支持尺寸 | `1024x1024`、`1024x1536`、`1536x1024` |
| 质量等级 | `low` / `medium` / `high`（生产使用 `high`）|
| 输出格式 | `png`（支持 `jpeg`、`webp`）|
| 返回格式 | 始终返回 base64 数据（无 URL）|

### 尺寸映射

| 原 aspect_ratio | 映射到 size | 说明 |
|-----------------|------------|------|
| `3:4` | `1024x1536` | 竖版（默认）|
| `4:3` | `1536x1024` | 横版 |
| `1:1` | `1024x1024` | 正方形 |
| `16:9` | `1536x1024` | fallback 到横版 |
| `9:16` | `1024x1536` | fallback 到竖版 |


## 二、Subagent 架构设计

### 为什么用 Subagent 而非直接调用

图像生成需要 8-12 秒，直接在 Coach 对话流中调用会阻塞用户体验。设计为 Subagent：

1. Coach 决定需要视觉干预 → 用文字铺垫（"让我为你描绘一下这个画面"）→ 异步委派给 Image Subagent
2. Image Subagent 独立执行：选择 prompt 模板 → 注入用户上下文 → 调用 Azure OpenAI gpt-image-1.5 → 存储结果
3. 图像就绪后，通过 LangGraph state 更新推送到前端

### 与 Pattern Analysis Subagent 的协作

```
Coach Agent (Supervisor)
├── Image Generation Subagent
│   ├── Prompt Template Library (Jinja2)
│   ├── User Context Injection
│   └── Azure OpenAI gpt-image-1.5
└── Pattern Analysis Subagent
    ├── Behavior Ledger Reader (1M context)
    ├── Azure OpenAI GPT-5.4 (high level)
    └── Trend/Pattern Output → 可触发 Image Subagent
```

Pattern Analysis Subagent 的输出（如"用户连续三天在高压力下选择安慰食物"）可作为 Image Subagent 的输入（"生成一张认知重构图：同一场景从'失控'视角和'信息'视角对比"）。

### Image Subagent 系统指令要点

```
你是 Voliti 的教练干预图像专家。你的职责是根据 Coach 的指令，
生成帮助用户建立身份一致性的个性化图像。

核心定位：
- 图像是教练干预工具，用于传递洞察、触发情感、辅助场景代入
- 不是数据可视化工具——数据展示由前端组件负责
- 不是装饰——每张图像必须服务于明确的教练目的

视觉约束（Starpath Protocol）：
- 背景只用两种：羊皮纸色 (#F5F1EB) 或暖黑色 (#2A2520)
- 主色调：深黑曜石 (#1A1A1A)
- 点缀色：仅在风险标记时使用克制红
- 对齐状态：低饱和冷色 (#8AACB8)
- 必须有大面积留白（≥40%）
- 禁止：过度渐变、激励式色彩、医疗蓝、游戏化元素、阴影浮层
- 风格偏向抽象/符号化/水墨画，避免照片写实和真人面孔
- **伦理约束详见 `/docs/01_Product_Foundation.md` 第六节（Guardrail）**

你会收到以下信息：
- purpose: 干预类型（future_self / scene_rehearsal / metaphor_mirror / reframe_contrast / identity_evolution）
- context: Coach 提供的用户行为上下文与个性化细节
- user_language: 用户原话中的关键隐喻或表达
- aspect_ratio: 目标宽高比
- text_overlay: 需要嵌入图像的文本（可选）

你需要：
1. 从 Prompt Template Library 选择对应模板
2. 将用户上下文和语言填入变量槽
3. 组装完整 prompt（含负面 prompt）
4. 调用 Azure OpenAI gpt-image-1.5
5. 返回图像数据
```

## 三、Prompt 模块化架构

每个 prompt 由四个模块组装：

```
[SCENE] + [STYLE] + [TECHNICAL] + [NEGATIVE]
```

### [STYLE] 基础模块（所有 prompt 共用）

**羊皮纸主题（默认）**：
```
Style: minimalist composition inspired by Japanese ma (negative space)
and Scandinavian restraint. High contrast. Warm parchment background (#F5F1EB)
with subtle handmade paper texture. Deep obsidian black (#1A1A1A) as primary
contrast element. Large generous white space comprising 40-60% of composition.
Linear divisions, no containers or shadows. Quiet confidence, never decorative.
```

**暖黑主题（Map 页专用）**：
```
Style: hand-drawn celestial cartography on warm dark background (#2A2520)
with subtle aged paper texture. Stars in low-saturation cool blue (#8AACB8)
with soft halos. Connecting lines as organic Bézier curves, not rigid geometry.
Eastern ink painting meets star atlas aesthetic. Generous dark negative space (60%+).
```

### [TECHNICAL] 模块

```
Aspect ratio: {aspect_ratio}.
Medium format film aesthetic with subtle organic grain.
Natural side lighting, soft and diffused. Non-photorealistic rendering.
```

### [NEGATIVE] 模块

```
Avoid: colorful, vibrant, busy, excessive gradients, motivational graphics,
medical blue, bright green/yellow/orange, rounded containers, drop shadows,
glossy effects, gamification elements (badges, stars, explosions),
fitness influencer photography, stock photo people, cartoon or emoji style,
high saturation, 3D effects, watermarks, realistic human faces.
```

## 四、教练干预 Prompt 模板

### Template 1: future_self — 未来自我可视化

**用途**: 帮助用户将抽象的"理想自我"转化为具象、感官丰富的画面，拉近当下与未来身份的心理距离
**S-PDCA 阶段**: Plan
**触发条件**: 用户描述了理想状态但表达抽象或遥远；新 Chapter 启动时建立身份愿景
**变量**: `{scene_description}`, `{sensory_details}`, `{identity_text}`, `{time_of_day}`, `{emotional_tone}`

```
An intimate, personal scene of a quiet moment of self-leadership:
{scene_description}

The scene feels lived-in and specific — not aspirational stock photography,
but a real moment in a real life. {sensory_details}

{time_of_day} light fills the space — warm, natural, unhurried.
The atmosphere conveys {emotional_tone}: this is not a fantasy of perfection,
but a vision of someone at ease with their choices.

A single line of hand-lettered text floats subtly in the composition:
"{identity_text}"
The text is rendered in obsidian black (#1A1A1A), small and dignified,
as if written by hand on the scene itself.

Style: contemplative documentary photography meets watercolor illustration.
The scene hovers between photographic detail and painterly abstraction —
real enough to feel personal, soft enough to feel like a dream.
Warm parchment tones (#F5F1EB) dominate. Large areas of quiet space.

Mood: grounded, clear, "this is who I'm becoming."
```

### Template 2: scene_rehearsal — 场景预演

**用途**: 为即将到来的挑战性场景（商务晚宴、出差、节日聚餐等）提供视觉锚定，让用户预先"看见"自己在该场景中做出对齐选择
**S-PDCA 阶段**: Do
**触发条件**: 用户提到即将面对的挑战性事件；Coach 检测到历史上该类场景常导致行为波动
**变量**: `{setting_description}`, `{challenge_context}`, `{aligned_choice_detail}`, `{anchor_text}`

```
A scene of quiet self-possession in a challenging social environment:
{setting_description}

The atmosphere is {challenge_context} — the kind of situation where
old patterns have the strongest pull. But in this rendering, there is
a visible thread of calm intentionality running through the scene.

{aligned_choice_detail}

The composition emphasizes the individual's centered presence
within a busy environment — they are part of the scene but not swept by it.
A subtle sense of agency radiates from the central figure (shown as
an abstract silhouette or shadow, never a realistic person).

Small hand-lettered text anchors the bottom of the composition:
"{anchor_text}"

Style: editorial illustration with selective watercolor accents.
Warm parchment background (#F5F1EB). The social environment is suggested
through minimal line work and muted tones, while the central presence
is rendered with more clarity and warmth.

Mood: composed, intentional, "I lead myself even here."
```

### Template 3: metaphor_mirror — 隐喻图像化

**用途**: 将用户自己的隐喻语言（如"被洪流冲走""站在十字路口""背着石头走"）转化为具象图像，利用 dual-coding 增强记忆与洞察
**S-PDCA 阶段**: Check
**触发条件**: 用户使用隐喻语言描述行为体验；Coach 在模式分析中构建了有力的隐喻解读
**变量**: `{metaphor_scene}`, `{transformation_element}`, `{emotional_undercurrent}`, `{insight_text}`

```
An abstract landscape that gives visual form to an inner experience:
{metaphor_scene}

The scene is rendered with dreamlike quality — not surreal or fantastical,
but the way a real landscape feels in memory. Every element carries meaning.

{transformation_element}

The emotional undercurrent of the image is {emotional_undercurrent} —
not dramatic, but honest. The image acknowledges what is, without judgment.

In the quiet space of the composition, a single observation appears
in small hand-lettered text: "{insight_text}"

Style: contemporary ink wash (sumi-e) with selective watercolor.
Warm parchment (#F5F1EB) or warm dark (#2A2520) background depending
on the metaphor's emotional register (light metaphors → parchment,
heavy/deep metaphors → dark).
The rendering is loose and organic, with visible brushwork.
Large areas of untouched background (50%+).

Mood: reflective, honest, "this is what it feels like — and that's information."
```

### Template 4: reframe_contrast — 认知重构

**用途**: 通过同一情境的两个视觉视角对比，帮助用户从"失败/失控"框架转向"信息/学习"框架
**S-PDCA 阶段**: Act
**触发条件**: 用户陷入固定视角看待行为偏离（自责、放弃心态）；Coach 检测到重复的自我批评模式
**变量**: `{situation_description}`, `{old_frame_visual}`, `{new_frame_visual}`, `{reframe_text}`

```
A diptych composition — two panels sharing the same scene,
seen through different eyes.

LEFT PANEL (smaller, slightly faded):
{old_frame_visual}
This rendering feels constricted, the lines tight, the space compressed.
It's the view from inside judgment — everything looks like failure.

RIGHT PANEL (larger, clearer):
{new_frame_visual}
The same scene opens up. The lines are looser, the space breathes.
Details that were invisible in the first view become visible —
context, complexity, humanity.

A thin vertical line separates the two panels.
Below the diptych, centered: "{reframe_text}"

The overall composition breathes. Generous parchment space (#F5F1EB)
surrounds both panels. The left panel uses slightly cooler, tighter marks.
The right panel uses warmer, more expansive strokes.

Style: architectural sketch meets editorial illustration.
Minimal line work, selective ink wash accents. No color except
for one subtle warm accent in the right panel.

Mood: perspective shift, "the same facts tell different stories."
```

### Template 5: identity_evolution — 身份演化

**用途**: 在月度或 Chapter 里程碑节点，回顾用户身份的连续性演化——不是"成就展示"而是"成为过程"的视觉记录
**S-PDCA 阶段**: Act
**触发条件**: Chapter 完成或月度回顾；Coach 检测到显著的行为模式正向转变
**变量**: `{form_count}`, `{evolution_description}`, `{continuity_note}`

```
Abstract visualization of personal identity evolution,
rendered in minimalist ink wash technique on warm parchment (#F5F1EB).

{form_count} overlapping silhouette forms flow from left to right, each slightly
more defined than the last. They share a continuous brushstroke at the core,
showing the same person evolving — not different people.

{evolution_description}

Between forms, delicate connecting lines suggest continuity.
{continuity_note}

Large areas of untouched warm parchment (50%+ white space).
Deep obsidian black ink with soft gray gradations.

Mood: contemplative, dignified, "becoming" rather than "achieving".
No text, no metrics, no comparison.
Style: Japanese sumi-e meets contemporary illustration.
```

## 五、AI Studio 即测 Prompt（完整版，直接复制）

以下 prompt 已填入具体变量，可直接在 Azure AI Foundry 中使用 `gpt-image-1.5` 测试。

### Test 1: 未来自我可视化（3:4）

```
An intimate, personal scene of a quiet moment of self-leadership:
A person's silhouette at a standing desk near a window, morning light streaming in.
A simple ceramic mug of black coffee, a clean workspace, a calm posture
suggesting someone who has already made their first good choice of the day.

The scene feels lived-in and specific — not aspirational stock photography,
but a real moment in a real life. The desk has subtle traces of actual work.
A small plant on the windowsill. The morning light catches dust motes.

Early morning light fills the space — warm, natural, unhurried.
The atmosphere conveys quiet clarity: this is not a fantasy of perfection,
but a vision of someone at ease with their choices.

A single line of hand-lettered text floats subtly in the upper portion:
"A person who starts the day with intention"
The text is rendered in obsidian black (#1A1A1A), small and dignified,
as if written by hand on the scene itself.

Style: contemplative documentary photography meets watercolor illustration.
The scene hovers between photographic detail and painterly abstraction —
real enough to feel personal, soft enough to feel like a dream.
Warm parchment tones (#F5F1EB) dominate. Large areas of quiet space.

Mood: grounded, clear, "this is who I'm becoming."

Avoid: colorful, vibrant, busy, motivational, realistic face, stock photo,
fitness imagery, perfect styling, text labels, watermarks.
```

### Test 2: 场景预演（4:3）

```
A scene of quiet self-possession in a challenging social environment:
A restaurant table set for a business dinner — warm lighting, multiple
place settings, wine glasses catching light. The scene is rendered from
the perspective of one seat, looking outward.

The atmosphere is social and energetic — colleagues, food being ordered,
conversations flowing — the kind of situation where dietary intentions
often dissolve into "I'll start again Monday."

But in this rendering, there is a clear, calm space around the viewer's
place setting. A glass of sparkling water with lemon sits prominently.
The food choices are simple and intentional, contrasting with the
abundance around them.

The composition emphasizes centered presence within a busy environment.
The surrounding activity is rendered in loose, impressionistic strokes,
while the personal space has more clarity and warmth.

Small hand-lettered text anchors the bottom: "I lead myself even here"

Style: editorial illustration with selective watercolor accents.
Warm parchment background (#F5F1EB). Minimal line work.

Mood: composed, intentional, self-led.

Avoid: colorful, vibrant, realistic faces, stock photo, medical, clinical,
gamification, bright colors, motivational imagery, text labels.
```

### Test 3: 隐喻图像化（9:16）

```
An abstract landscape that gives visual form to an inner experience:
A river flowing through a narrow gorge. The water is rendered in deep
ink washes — powerful, fast-moving, carrying everything along.
But midstream, a series of stepping stones emerge from the current —
solid, weathered, each one close enough to reach from the last.

The scene is rendered with dreamlike quality — not surreal,
but the way a real landscape feels in memory.

The stepping stones are lit with warm white (#F5F1EB), standing out
against the dark flowing water. Each stone has subtle texture —
these are not perfect geometric shapes, but natural, reliable holds.

The emotional undercurrent is recognition without alarm —
the current is strong, but the path exists.

In the quiet space above the scene, small hand-lettered text:
"The current is strong. The stones are real."

Style: contemporary ink wash (sumi-e) with selective watercolor.
Warm dark background (#2A2520). Loose, organic brushwork.
Large areas of untouched dark space above (50%+).

Mood: reflective, honest, grounded.

Avoid: colorful, bright, busy, cartoon, fantasy, motivational,
people, faces, text labels, symmetry, digital precision.
```

### Test 4: 认知重构（16:9）

```
A diptych composition — two panels sharing the same scene,
seen through different eyes.

LEFT PANEL (smaller, slightly faded):
A kitchen counter late at night. Harsh overhead light. Crumbs, an open
bag of chips, a half-empty glass. The rendering feels constricted —
tight cross-hatching, compressed space, every detail magnified
as if under a microscope of self-judgment.

RIGHT PANEL (larger, clearer):
The same kitchen counter, same moment. But the rendering opens up —
softer light, wider framing. Now visible: the laptop showing a late
work deadline, the cold dinner plate pushed aside, the long day
written in the scene's context. The chips are still there,
but they're a detail in a larger story, not the whole story.

A thin vertical obsidian line separates the two panels.
Below the diptych, centered: "Same facts. Different story."

Generous parchment space (#F5F1EB) surrounds both panels.
Left panel uses cooler, tighter ink marks.
Right panel uses warmer, more expansive watercolor strokes.
One subtle warm accent in the right panel.

Style: architectural sketch meets editorial illustration.
Minimal line work, selective ink wash accents.

Mood: perspective shift, compassionate honesty.

Avoid: colorful, motivational, realistic faces, clinical, bright,
cartoon, gamification, text labels, watermarks.
```

### Test 5: 身份演化（3:4）

```
Abstract visualization of personal identity evolution over one month,
rendered in minimalist ink wash technique on warm parchment (#F5F1EB).

Three overlapping silhouette forms flow from left to right, each slightly
more defined and upright than the last. They share a continuous brushstroke
at the core, showing the same person evolving — not three different people.

The leftmost form is rendered in lighter, more diffuse ink washes —
uncertain but present. The middle form gains subtle structure — clearer edges,
more grounded posture. The rightmost form has the most clarity but remains
soft, never rigid — defined by ease rather than effort.

Between the forms, delicate connecting lines suggest continuity.
The overall trajectory is not "up" but "inward" — becoming more oneself.

Large areas of untouched warm parchment above and below (50%+ white space).
Deep obsidian black (#1A1A1A) ink with soft gray gradations.

Mood: contemplative, dignified, showing "becoming" rather than "achieving".
No text, no metrics, no comparison.
Style: Japanese sumi-e meets contemporary illustration.

Avoid: colorful, bright, busy, facial features, realistic people, cartoon,
text, motivational imagery, achievement symbols, finish lines.
```

## 六、Coach 图像生成决策逻辑

图像生成是 Coach 的教练工具之一，不是自动触发的 UI 功能。

### 何时生成

Coach 在以下条件满足时考虑触发图像生成：

1. **文字不足以传达洞察**：Coach 判断图像比文字更能帮助用户"看见"某个模式或可能性
2. **用户处于接受状态**：用户当前不处于高压/紧急状态（详见 `/docs/01_Product_Foundation.md` 第六节Guardrail）
3. **上下文充足**：Coach 已积累足够的用户信息来生成有意义的个性化图像（不在首次对话中使用）
4. **时机恰当**：图像生成 8-12 秒的延迟不会打断当前对话节奏
5. **干预类型与 S-PDCA 阶段匹配**：选择的干预类型符合当前教练情境（详见 `/docs/01_Product_Foundation.md` 附录A.4节）

### 频率约束

- 每 Chapter（约 21 天）估计 3-5 次图像生成
- 不在每次对话中生成——大多数交互以文字为主
- 同一类型的干预不在短期内重复

### 交互流程

```
1. Coach 判断需要视觉干预
2. Coach 用文字铺垫："让我为你描绘一下这个画面" / "我想帮你看见一些东西"
3. Image Subagent 异步生成（Coach 可继续对话）
4. 图像就绪 → 推送到前端
5. Coach 征求反馈："这让你有什么感觉？" / "这像你描述的那样吗？"
6. 如用户要求调整 → Coach 通过对话式编辑精化
```

### 个性化原则

- 使用用户自己的语言和隐喻——不套用通用意象
- 参考用户 profile 中的偏好和身份愿景
- 在 `/user/coach/AGENTS.md` 中记录用户对图像干预的反应偏好（如"偏好抽象风格"/"对暗色背景反应更积极"）

## 七、Prompt 工程注意事项

1. **叙事式描述**优于关键词列表——gpt-image-1.5 在段落式描述下效果最好，按 场景→主体→细节→约束 组织
2. **颜色双重锚定**——hex 代码 + 描述性语言：`"warm parchment (#F5F1EB, like aged cream paper)"`
3. **显式要求留白**——"generous negative space"、"60%+ white space"
4. **正面描述优先**——关键约束写成正面描述融入 Style（"desaturated muted palette"），负面约束（"This image must not contain..."）作兜底
5. **非写实强化**——gpt-image-1.5 偏向写实，需要在 prompt 中反复强调 "illustration"、"painting"、"non-photorealistic rendering"
6. **文字渲染是强项**——用引号包裹要渲染的文字：`Render the text: "I lead myself even here"`。中文文字逐字标注
7. **用户语言优先**——将用户原话中的隐喻、表达直接嵌入 prompt，比 Coach 的转述更有效
8. **避免真人面孔**——在 Scene 描述中明确写 "silhouette figure" 或 "abstract form"
9. **文本嵌入要克制**——嵌入图像的文本应为一句话（肯定句、洞察、隐喻），不写段落
10. **情绪色温匹配**——温暖/安全场景用羊皮纸底，深沉/内省场景用暖黑底

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-09 | 初始创建：模型参数、Subagent 架构、模块化 prompt 体系、6 个数据可视化测试 prompt |
| 2026-02-09 | 架构重定位：图像生成从数据可视化转向教练干预工具；替换全部 6 个模板为 5 个教练干预模板（future_self, scene_rehearsal, metaphor_mirror, reframe_contrast, identity_evolution）；新增 Coach 图像生成决策逻辑；更新 Subagent 系统指令 |
| 2026-02-09 | 文档重新定位为技术实现指南；删除理论基础章节（移至 01_Product_Foundation.md 附录A.4节）；调整章节编号；更新交叉引用指向 01_Product_Foundation.md；遵循单一事实来源原则 |
| 2026-04-01 | 图片生成模型从 Gemini 3 Pro Image 迁移至 Azure OpenAI gpt-image-1.5；更新 API 参数表、尺寸映射、prompt 工程注意事项；移除 Gemini 特定内容 |
