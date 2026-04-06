# Phase C: Coach 治理机制方案

> 目标：让 Coach 在 Onboarding 和日常对话中自主管理北极星指标、支持性指标、Chapter 身份宣言，并在适当时刻触发 Moments 图像。

## 一、设计原则

### 1. Coach 自主性优先

Coach 是一个具备推理能力的 LLM Agent。我们只提供：
- **它能做什么**（可用工具和 Store 路径）
- **每件事的质量标准**（什么是好的 Chapter，什么是好的北极星选择）
- **边界约束**（不能做什么）

不提供：
- 具体的对话脚本或步骤编排
- 硬编码的触发条件（如"第 3 轮对话后创建 Chapter"）
- 强制性的操作顺序

### 2. 用户感知的 Coach 行动

Coach 的写入/更新行为对用户应是自然可感知的，但不是系统通知式的。实现方式：

- Coach 的 `coach_thinking` JSON（已有机制，前端渲染为 ThinkingCard）中自然地体现它的判断过程
- Coach 在对话中用教练语言提及它的观察和决策，例如："我注意到你连续一周在体重上有稳定的记录，我把它设为你的核心追踪指标了"
- 不显示系统消息、不弹 toast、不用技术语言

在 prompt 中加一条原则：

```
When you write or update user data (profile, chapter, dashboard, ledger), 
weave your reasoning into the conversation naturally. The user should 
understand what changed and why through your coaching voice, not through 
system notifications. Never mention file paths, Store operations, or 
technical details.
```

## 二、Onboarding 设计

### 调研结论

Apple HIG 核心原则："减少 Onboarding 的必要性本身"。行业实践分为两极：
- Headspace/Gentler Streak：3 个问题，1 分钟，即刻进入主体验
- Noom：80+ 问题，15-30 分钟，深度心理画像

Voliti 的定位（策略顾问，非健身教练）和 S-PDCA 框架（State 优先）指向 Headspace 模式：最小采集，快速进入教练体验，后续对话中渐进补充。

### Onboarding 流程方案

视觉规格详见 `DESIGN.md` "Onboarding — 全屏对话" 部分。

**入口**：首次启动时，全屏 `OnboardingView` 覆盖 TabView。

**三步对话（每次一个问题）**：
1. 称呼（文本输入 + 语音）
2. Future Self — "你最享受的自己是什么样的？"（Quick Reply pills + 可展开自由输入）
3. State — "离那个状态有多远？"（Quick Reply pills）

三步完成后，Coach 自主判断是否发送 fan_out 结构化表单深入采集，或直接完成。

**Coach Onboarding Completion Requirements（prompt 中定义）**：
1. 知道用户的称呼
2. 理解用户向往的状态（Future Self，为 Chapter 身份宣言提供素材）
3. 评估用户当前与目标的心理距离（State）

LifeSign 创建从 "必须" 改为 "提供"，Coach 自主判断是否在 Onboarding 中协助创建。

**仪式完成**：
1. Coach 写入 profile（`onboarding_complete: true`）+ dashboardConfig + chapter
2. 触发 `future_self` ceremony image
3. StoreSyncService.syncAll() 确认数据到位
4. Tab 栏从底部滑入，对话历史保留在 COACH Tab

### iOS 实现

**新建 `OnboardingView.swift`**：
- 全屏覆盖（fullScreenCover），`@AppStorage("onboardingComplete")` 控制显示
- 两个视觉阶段：居中模式（Step 1-2）→ 对话模式（Step 3+）
- 共享 thread_id 与 CoachView，对话历史跨界面保留
- 支持 Quick Reply pills、自由文本输入、语音输入
- Onboarding 完成信号：sync 检测到 `onboarding_complete: true` 后过渡

**改动 `ContentView.swift`**：
- 在 TabView 外层加 `.fullScreenCover(isPresented: !onboardingComplete)`

## 三、指标治理（北极星 + 支持性指标）

### DashboardConfig 数据结构扩展

当前结构：
```json
{"metrics": [{"key": "weight", "label": "体重", "unit": "KG", "order": 0}]}
```

扩展为：
```json
{
  "north_star": {"key": "weight", "label": "体重", "unit": "KG", "delta_direction": "decrease"},
  "support_metrics": [
    {"key": "calories", "label": "今日摄入", "unit": "KCAL", "order": 0},
    {"key": "state", "label": "今日状态", "unit": "/10", "order": 1},
    {"key": "consistency", "label": "本周一致性", "unit": "/7", "order": 2}
  ],
  "user_goal": "12 周 75kg → 70kg"
}
```

新增字段：
- `north_star`：独立对象，不在 metrics 数组中
- `delta_direction`：`"decrease"` 或 `"increase"`，告诉前端哪个方向是正向（减脂场景体重下降为正）
- `support_metrics`：固定 3 个，由 Coach 选择

### Coach prompt 补充

```
## Metrics Governance

You manage the user's tracking metrics via `/user/profile/dashboardConfig`.

**North Star:** One metric that best represents the user's primary goal. 
Default: weight for fat loss. Include `delta_direction` ("decrease" or "increase") 
so the UI knows which direction is positive.

**Support Metrics:** Three metrics that support the North Star. 
Choose from: calories, state (energy/mood), consistency (days active this week), 
protein, sleep, water, exercise_minutes, body_fat.

**When to adjust:** Use your judgment. Typical triggers include:
- User explicitly asks to track something different
- You observe that a metric is consistently irrelevant
- A new dimension emerges as important from conversation patterns

When you adjust metrics, explain your reasoning in conversation.
```

### iOS 端改动

**DashboardConfig 模型**：增加 `northStar: NorthStarConfig?` 和 `supportMetrics: [DashboardMetric]`

**StoreSyncService**：解析新 JSON 结构

**MirrorViewModel**：从 DashboardConfig 读取北极星和支持指标配置，替换硬编码 fallback。无 config 时仍用硬编码默认值。

## 四、Chapter 治理

### Chapter 的定义

**Chapter 是什么**：Coach 根据用户旅程自主划分的身份阶段。没有固定周期，长度由 Coach 判断。它是用户行为日志的一部分，也是 MIRROR 页面的最高层级信息。

**与 LifeSign 的关系**：
- LifeSign 是具体的应对预案，粒度小（单个 if-then 行为）
- Chapter 是更长的身份阶段，包含多个 LifeSign 的积累
- LifeSign 的里程碑（如累计成功）可以成为 Chapter 过渡的信号之一，但不是唯一触发条件

**核心要素**：
- **身份宣言**（identityStatement）：一句话描述用户在这个阶段正在成为的人。例如"在压力下保持清晰选择的人"。不是目标陈述（"我要减到 70kg"），而是身份陈述（"我是...的人"）。
- **阶段性目标**（goal）：该 Chapter 的聚焦方向，例如"建立工作日饮食节奏"或"12 周 75kg → 70kg"
- **周期**：无固定长度。Coach 根据用户的熟悉程度、行为模式变化、LifeSign 里程碑等综合判断

**典型 Chapter 演进示例**：
```
Chapter 1: "正在认识自己饮食模式的人" — 初次使用，探索和记录阶段
Chapter 2: "在工作日能提前准备午餐的人" — LifeSign 积累，形成第一个稳定习惯
Chapter 3: "在压力下保持清晰选择的人" — 从行为层面上升到决策层面
```

每个 Chapter 之间有连续性：后一个 Chapter 建立在前一个的基础上。

**生命周期**：
1. **创建**：Onboarding 完成时 Coach 创建首个 Chapter
2. **运行**：MIRROR 页顶部持续展示 "CHAPTER · DAY N" + 身份宣言
3. **过渡**：Coach 自主判断时机（LifeSign 里程碑、用户行为模式变化、用户明确表达转变、阶段性目标达成）
4. **续接**：过渡时触发 `identity_evolution` Moment，归档当前 Chapter，创建新 Chapter

### Store 路径

```
/user/chapter/current.json
```

```json
{
  "id": "ch_001",
  "identity_statement": "在压力下保持清晰选择的人",
  "goal": "12 周 75kg → 70kg",
  "start_date": "2026-04-06T00:00:00Z"
}
```

Coach 创建新 Chapter 时，先读取 current，归档到 `/user/chapter/archive/{id}.json`，再写入新的 current。

### Coach prompt 补充

```
## Chapter Management

A Chapter is an identity stage in the user's journey. No fixed duration. 
Write to `/user/chapter/current.json`.

**Identity Statement:** One sentence describing who the user is becoming 
in this phase. Frame as identity ("a person who..."), not goal ("I want to..."). 
Each Chapter builds on the previous one.

**Creating:** Create the first Chapter at onboarding completion. Early Chapters 
may focus on exploration and familiarity ("getting to know my patterns"). 
Later Chapters reflect deeper identity shifts.

**Transitioning:** Use your judgment. Signals that a Chapter may be complete:
- LifeSign milestones (accumulated successes showing a behavioral shift)
- User's behavioral patterns have visibly changed
- User expresses a new self-understanding
- The current identity statement no longer captures who they are becoming

When transitioning: archive current to `/user/chapter/archive/{id}.json`, 
create new current, trigger `identity_evolution` image. 
Explain the transition through conversation — this is a meaningful moment.

**Quality standard:** A good identity statement is specific enough to guide 
daily decisions but broad enough to not expire in a week. It should feel 
true and aspirational at the same time.
```

### iOS 端改动

**StoreSyncService**：新增 `syncChapter()` 方法，从 `/user/chapter/current.json` 同步到 SwiftData

## 五、Moments 触发（已有能力，仅 prompt 对齐）

当前 `intervention_composer` 已支持 5 种图像类型。需要确认 prompt 中的触发框架与 Phase C 对齐：

| 触发场景 | 图像类型 | Coach 行为 |
|---------|---------|-----------|
| Onboarding 完成 | `future_self` | 自动触发，不需用户同意（仪式） |
| LifeSign 累计 3 次成功 | `identity_evolution` | 自动触发（已在 prompt 中） |
| Chapter 过渡 | `identity_evolution` | 新增：Coach 自主判断，LifeSign 里程碑可作为信号之一 |
| 用户面临高压场景 | `scene_rehearsal` | 已有：需先征求用户意愿 |
| 用户表达认知困境 | `reframe_contrast` | 已有：需先征求用户意愿 |
| 用户使用隐喻表达 | `metaphor_mirror` | 已有：需先征求用户意愿 |

**新增触发**：Chapter 过渡时的 `identity_evolution`。在 Chapter management prompt 中已包含。

## 六、CEO Review 新增范围

以下为 /plan-ceo-review 审查后新增的设计决策（SELECTIVE EXPANSION 模式）：

### 6.1 指标类型系统

4 种类型覆盖所有可量化指标：

| 类型 | 标识符 | 示例 | 显示格式 |
|------|--------|------|---------|
| 数值 | `numeric` | 体重 68.5 kg | 数值 + 单位 |
| 刻度 | `scale` | 精力 7/10 | 整数 |
| 序数 | `ordinal` | 情绪 高/中/低 | 文字标签（内部存为索引） |
| 比率 | `ratio` | 打卡 5/7 天 | 分数（归一化为 0-1 用于图表） |

北极星指标限制为 `numeric` 或 `scale`（需支持 delta 计算）。

### 6.2 DashboardConfig JSON Schema（最终版）

```json
{
  "north_star": {
    "key": "weight",
    "label": "体重",
    "type": "numeric",
    "unit": "KG",
    "delta_direction": "decrease",
    "current_value": {"value": 72.3, "unit": "kg"}
  },
  "support_metrics": [
    {
      "key": "calories",
      "label": "今日摄入",
      "type": "numeric",
      "unit": "KCAL",
      "order": 0,
      "current_value": {"value": 1420, "unit": "kcal"}
    },
    {
      "key": "state",
      "label": "今日状态",
      "type": "scale",
      "unit": "/10",
      "order": 1,
      "current_value": {"value": 7, "min": 1, "max": 10}
    },
    {
      "key": "consistency",
      "label": "本周一致性",
      "type": "ratio",
      "unit": "",
      "order": 2,
      "current_value": {"numerator": 5, "denominator": 7}
    }
  ],
  "user_goal": "12 周 75kg → 70kg"
}
```

**混合方案**：Coach 在每次会话后写入 `current_value`，前端只负责显示。这让 Coach 能定义任意指标而不需前端改代码。

### 6.3 Chapter 过渡事件

新增 `EventType.chapterTransition`（rawValue "chapter_transition"），作为 FilterBar 的 "篇章" 标签。复用现有统一事件流，不新建视图。

### 6.4 coach_thinking actions 字段

```json
{
  "strategy": "...",
  "observation": "...",
  "actions": ["更新了你的核心追踪指标为体重", "创建了你的第一个篇章"]
}
```

ThinkingCard 展开时显示 actions 列表。纯 prompt + 前端渲染调整。

### 6.5 Onboarding 设计补充

- Coach 是对话发起人（不同于正常 COACH Tab）
- 需要独特的视觉设计（需 /design-consultation）
- 与 COACH Tab 共享同一 thread_id，会话历史跨界面保留
- LifeSign 创建从"必须"改为"提供"（Coach 判断是否在 Onboarding 中创建）
- Onboarding 完成信号：Coach 写入 `onboarding_complete: true` → iOS sync 检测 → 过渡到 2-Tab

### 6.6 错误处理原则

解析错误不静默丢弃。iOS 端保留前一次有效数据。后端层面错误信息返回给 Coach，由 Coach 智能决定后续操作。

## 七、实现计划

### 改动清单

| 步骤 | 文件 | 改动 |
|------|------|------|
| 1 | `coach_system.j2` | 新增 Metrics Governance（含 type system） + Chapter Management + 行动透明度 + coach_thinking actions + Onboarding requirements 调整 |
| 2 | `DashboardConfig.swift` | 模型扩展：northStar + supportMetrics + type + deltaDirection + currentValue |
| 3 | `StoreSyncService.swift` | 适配新 JSON 结构（4 种 metric type 解析）+ 新增 syncChapter() |
| 4 | `MirrorViewModel.swift` | 从 DashboardConfig 读取北极星/支持指标配置，替换硬编码 |
| 5 | `NorthStarMetric.swift` | 接收 deltaDirection 参数 + 从 config 读取值 |
| 6 | `SupportMetricSection.swift` | 从 config 读取指标定义 + 4 种类型显示格式 |
| 7 | `BehaviorEvent.swift` | 新增 `chapterTransition` EventType |
| 8 | `FilterBar.swift` | "篇章" 标签支持 |
| 9 | `ThinkingCard.swift` | 展示 coach_thinking actions 列表 |
| 10 | `OnboardingView.swift` | 新建全屏 Onboarding 界面（需先完成设计） |
| 11 | `ContentView.swift` | fullScreenCover 控制 Onboarding 显示 |

### 执行顺序

```
C1: coach_system.j2 prompt 更新
C2: DashboardConfig + StoreSyncService + syncChapter（数据管道）
C3: MirrorViewModel + NorthStar + SupportMetric 动态化
C4: BehaviorEvent + FilterBar + ThinkingCard（小改动）
C5: OnboardingView 设计（/design-consultation）+ 实现 + ContentView 集成
```

C1-C4 可按顺序快速推进。C5 需要先做设计再实现。

### 不在本轮范围内

- Middleware/Harness 调整（后续专门任务）
- 趋势图历史数据聚合（当前只显示 Coach 写入的 current_value）
- 多语言 Localization（当前中文为主）

---

## 变更记录

| 日期 | 内容 |
|------|------|
| 2026-04-06 | 初始创建：基于调研和 Dexter 反馈整理 Phase C 完整方案 |
| 2026-04-06 | CEO Review 更新：5 项扩展纳入范围（指标类型系统、Chapter 事件、actions 字段、Onboarding 过渡、错误处理原则）；DashboardConfig schema 定稿；Onboarding 设计补充 |
| 2026-04-06 | Eng Review 更新：删除 MirrorViewModel 硬编码计算（纯依赖 Coach current_value）；确认 1 个 critical gap（Onboarding sync timeout）；测试计划已生成 |

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 2 | CLEAR | 5 proposals, 5 accepted, 0 deferred |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 2 | CLEAR | 1 issue, 1 critical gap (sync timeout) |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | STALE | Prior review from 2026-04-05, needs refresh for Onboarding |

**VERDICT:** CEO + ENG CLEARED. Onboarding 需要 /design-consultation 做视觉设计后再做 design review。
