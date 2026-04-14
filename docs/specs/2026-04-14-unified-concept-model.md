<!-- ABOUTME: 统一概念模型设计方案 — Identity/Goal/Chapter/Process Goal/LifeSign 五层结构 -->
<!-- ABOUTME: 定义概念关系、数据结构变更、S-PDCA 映射、Onboarding 与 Coach prompt 影响 -->

# 统一概念模型设计方案

## 一、问题陈述

当前系统中 Identity、Goal、Chapter、Metrics、LifeSign 是孤立的数据片段，缺少统一的关系模型。具体表现：

1. **Chapter 角色模糊**：同时承载身份声明和阶段目标，既是"我是谁"又是"我在做什么"。
2. **Goal 没有独立存在**：`user_goal` 是 `dashboardConfig` 中的自由文本字段，与 Chapter 和 Metrics 无结构化关联。
3. **指标悬空**：`north_star` 和 `support_metrics` 定义了追踪什么，但不追踪"为了什么"（没有目标值绑定）。
4. **缺少行动层**：Onboarding 产出身份和危险场景，但不产出"接下来具体做什么"。用户完成 onboarding 后缺乏行动锚点。
5. **S-PDCA Plan 阶段空转**：文档定义为"意图对齐"，但 Coach 缺乏结构化的上下文来生成每日意图。

## 二、设计原则

1. **内部丰富，表面极简**：五层概念模型是 Coach 的认知框架，不是用户的认知负担。用户通过对话和极简仪表盘感知，不需要学习任何术语。
2. **微调现有结构**：在 dashboardConfig / Chapter / LifeSign 等已有数据结构上增量修改，不另起炉灶。
3. **Coach 是唯一的编排者**：所有概念管理（Chapter 过渡、Process Goal 调整、指标更新）通过 Coach 在对话中完成，不需要独立的管理 UI。
4. **与用户共建一切**：时间跨度、指标选择、阶段划分均由 Coach 与用户协作确定。本方案给出参考区间，不写死数值。
5. **State Before Strategy**：每日意图由 Coach 与用户在晨间 Check-in 中共创，不是前一天预设的刚性计划。

## 三、五层概念模型

```
Identity（身份宣言）
  │  约束关系：Goal 必须与 Identity 价值一致
  ▼
Goal（结果目标）
  │  分解为时间锚点
  ▼
Chapter（阶段）
  │  展开为可追踪行为
  ▼
Process Goal（过程目标）
  │  具象为情境预案
  ▼
LifeSign（应对预案）
```

### 3.1 各层定义

#### Identity（身份宣言）

- **本质**：用户想成为什么样的人。无时限，定性，缓慢演化但不随 Goal 更换而重置。
- **理论依据**：Carver & Scheier 控制层级理论（1998）——身份是目标层级的最高设定点，约束下层目标的合法性。Oyserman IBM 理论（2015）——身份决定困难的解读方式，是挫折后复原力的来源。
- **与 Goal 的关系**：约束关系，不是包含关系。Goal 可更换（减脂目标达成后换为体能目标），Identity 持续演化。Coach 在 Goal 变更时做价值一致性检验。
- **用户感知**：仪表盘顶部的引导语；Coach 在 L5 反馈中自然强化。用户不需要知道这叫"Identity"。
- **演化机制**：Coach 在 Chapter 复盘时（L5 身份式反馈）提议更新。用户也可在对话中主动表达新的自我认知。
- **示例**：`"一个在复杂环境中仍能做出清晰选择的人"`

#### Goal（结果目标）

- **本质**：用户的量化终点 + 时间约束。对应 BCT 1.3（结果目标设定）。
- **时间跨度**：由用户与 Coach 共同确定。参考区间数周至数月，取决于用户的实际目标规模。
- **指标绑定**：Goal 锚定 North Star 指标的目标值（如：体重从 75kg 降至 70kg）。
- **用户感知**：仪表盘上的"我的目标"——一句话 + 进度。用户自己设定、自己理解。
- **示例**：`"12 周 75kg → 70kg"`

#### Chapter（阶段）

- **本质**：Goal 之下的时间容器，每个 Chapter 有明确的主题、里程碑和时间范围。
- **时间跨度**：由 Coach 与用户协商，参考区间 2-6 周。研究显示与自然时间地标对齐效果更好（新鲜起点效应，Dai et al. 2014）。一个 Goal 下通常若干个 Chapter。
- **用户感知**：仪表盘上的 `Chapter N`，用户感受到"阶段感"。Coach 通过对话和 Witness Card 标记阶段转换。
- **与 Identity 的关系**：Chapter 不再承载 `identity_statement`（上移至 Identity 层）。Chapter 的重点是"这个阶段我在做什么"，不是"我是谁"。
- **示例**：Chapter 1 "认识饮食模式" → Chapter 2 "建立工作日节奏" → Chapter 3 "应对社交场景"

#### Process Goal（过程目标）

- **本质**：Chapter 内的行为目标，对应 BCT 1.1（行为目标设定）。由 Coach 与用户共创，以周为自然追踪单位，日常 Check-in 中灵活参考。
- **数量**：固定 3 个/Chapter，与仪表盘 3 个 support_metrics 一一对应。
- **指标绑定**：每个 Process Goal 直接对应一个 support_metric。support_metrics 随 Chapter 变化而变化。
- **每日实现**：Process Goal 不是刚性的每日计划。Coach 在 Check-in 中基于用户当前 State 与 Process Goal 共创"今日意图"，保持弹性。
- **用户感知**：仪表盘上显示为 support_metrics（如"达标天数 4/7"）。Coach 在对话中自然提及。用户不需要知道这叫"Process Goal"。
- **调整机制**：Coach 在复盘对话中如发现某个目标持续不达标，与用户共同调整（BCT 1.2 Problem Solving）。
- **示例**：`"每天蛋白质 ≥100g，目标 5/7 天"` / `"每周记录 ≥5 天"`

#### LifeSign（应对预案）

- **本质**：不变。结构化的 if-then 应对预案（BCT 1.4 行动计划）。
- **与 Process Goal 的关系**：LifeSign 保护 Process Goal 在高风险情境下不被打断。
- **用户感知**：Coach 在危险时刻自然提醒；仪表盘上简洁展示。

### 3.2 层级间关系总结

| 关系 | 说明 |
|------|------|
| Identity → Goal | 约束：Goal 必须与 Identity 价值一致 |
| Goal → Chapter | 分解：一个 Goal 分为若干个 Chapter |
| Chapter → Process Goal | 展开：每个 Chapter 固定 3 个 Process Goal |
| Process Goal → LifeSign | 保护：LifeSign 在高风险时刻保护 Process Goal 的执行 |
| Process Goal ↔ support_metrics | 绑定：每个 Process Goal 对应一个仪表盘指标 |
| Goal ↔ north_star | 绑定：Goal 锚定 North Star 的目标值 |

## 四、与 S-PDCA 的关系

概念模型的五层提供上下文，S-PDCA 是每天的运作引擎。两者的关系是：**概念模型定义"关于什么"，S-PDCA 定义"怎么运作"。**

| 概念层 | 在 S-PDCA 中的角色 |
|--------|-------------------|
| Identity | Act 阶段的身份强化素材（L5 反馈） |
| Goal | Check 阶段的方向校准参照 |
| Chapter | 当前阶段的主题和里程碑，约束 Coach 的关注重点 |
| Process Goal | Plan 阶段共创今日意图的锚点；Check 阶段反馈的核心素材 |
| LifeSign | 高风险情境下的即时应对预案 |

Coach 的上下文加载由现有 Middleware 机制（MemoryMiddleware 自动加载 profile + chapter + coping_plans_index，BriefingMiddleware 注入近期回顾）处理。概念模型不改变上下文加载方式，只丰富 Coach 可读取的数据内容。

## 五、数据结构变更

以下变更基于现有结构微调，不重建。

### 5.1 Identity — 从 Chapter 上移至 Profile

**变更**：`identity_statement` 从 `/chapter/current.json` 移至 `/profile/context.md`。

**原因**：Identity 的生命周期长于 Chapter。当 Chapter 过渡时，Identity 不应该被归档。

`/profile/context.md` 新增字段：
```markdown
identity_statement: 一个在复杂环境中仍能做出清晰选择的人
```

### 5.2 Goal — 新增独立存储

**变更**：新增 `/goal/current.json`。

**原因**：当前系统中 Goal 只是 `dashboardConfig.user_goal` 的自由文本，没有结构化的目标值和时间约束。

```json
{
  "id": "goal_001",
  "description": "12 周内从 75kg 降至 70kg",
  "north_star_target": {
    "key": "weight",
    "baseline": 75,
    "target": 70,
    "unit": "kg"
  },
  "start_date": "2026-04-06T00:00:00Z",
  "target_date": "2026-06-28T00:00:00Z",
  "status": "active"
}
```

### 5.3 Chapter — 增加阶段规划字段

**变更**：在现有 Chapter 结构上新增字段。

当前结构：
```json
{
  "id": "ch_001",
  "identity_statement": "...",  // 移除，上移至 Profile
  "goal": "建立工作日饮食节奏",
  "start_date": "2026-04-06T00:00:00Z"
}
```

调整后：
```json
{
  "id": "ch_001",
  "goal_id": "goal_001",
  "chapter_number": 1,
  "title": "认识自己的饮食模式",
  "milestone": "连续两周工作日三餐记录完整",
  "process_goals": [
    {
      "key": "logging_consistency",
      "description": "每天记录饮食",
      "target": "5/7 天",
      "metric_key": "logging_days"
    },
    {
      "key": "protein_adherence",
      "description": "蛋白质摄入达标",
      "target": "≥100g/天",
      "metric_key": "protein_days"
    }
  ],
  "start_date": "2026-04-06T00:00:00Z",
  "planned_end_date": "2026-04-27T00:00:00Z",
  "status": "active"
}
```

**保留字段**：`id`、`start_date`、`chapter_number`、`status`
**移除字段**：`identity_statement`（→ Profile）
**重命名字段**：`goal` → `title`（避免与顶层 Goal 混淆）
**新增字段**：`goal_id`、`milestone`、`process_goals[]`、`planned_end_date`

### 5.4 dashboardConfig — 增加语义分层

**变更**：在现有结构上新增 `goal_summary` 和 `process_metrics` 语义标记。

当前结构：
```json
{
  "north_star": {"key": "weight", "label": "体重", "type": "numeric", "unit": "KG", "delta_direction": "decrease"},
  "support_metrics": [...],
  "user_goal": "12 周 75kg → 70kg"
}
```

调整后：
```json
{
  "north_star": {
    "key": "weight",
    "label": "体重趋势",
    "type": "numeric",
    "unit": "KG",
    "delta_direction": "decrease"
  },
  "support_metrics": [
    {"key": "logging_days", "label": "记录天数", "type": "ratio", "unit": "/7", "order": 0},
    {"key": "protein_days", "label": "蛋白达标", "type": "ratio", "unit": "/7", "order": 1},
    {"key": "state", "label": "今日状态", "type": "scale", "unit": "/10", "order": 2}
  ],
  "user_goal": "12 周 75kg → 70kg"
}
```

**不变**：整体结构、字段名、类型定义。
**语义变化**：`support_metrics` 现在由 Chapter 的 `process_goals` 驱动。当 Chapter 过渡时，Coach 更新 `support_metrics` 以匹配新 Chapter 的 Process Goal。`user_goal` 保留作为仪表盘显示用的简短描述。

### 5.5 指标分层（Coach 认知，非数据结构变更）

Coach prompt 中增加指标语义指引，帮助 Coach 理解三类指标的不同用途：

| 类型 | 绑定层 | 用途 |
|------|--------|------|
| North Star（滞后） | Goal | 方向感，长周期看趋势 |
| Process（领先） | Process Goal → support_metrics | Coach 日常反馈的核心素材 |
| State（调节） | S-PDCA State | 校准当日期望 |

具体的反馈频率和回顾节奏由 Coach 根据用户情况自然把握，不硬编码周期。State 指标（能量、情绪、压力）不存入 dashboardConfig，它们是 Check-in 的采集维度，在 ledger 事件中记录。

### 5.6 Store Key 变更汇总

| 路径 | 变更类型 | 说明 |
|------|---------|------|
| `/profile/context.md` | 新增字段 | 增加 `identity_statement` |
| `/goal/current.json` | **新增** | 独立的结果目标存储 |
| `/goal/archive/{id}.json` | **新增** | Goal 归档（Goal 完成或更换时） |
| `/chapter/current.json` | 字段调整 | 移除 `identity_statement`，新增 `goal_id` / `milestone` / `process_goals[]` / `planned_end_date`，`goal` → `title` |
| `/profile/dashboardConfig` | 语义调整 | support_metrics 由 Chapter process_goals 驱动 |
| 其余路径 | 不变 | — |

### 5.7 前端 ChapterData 接口调整

```typescript
export interface ChapterData {
  chapter_number: number;
  title: string;                    // 原 goal → title
  milestone: string;                // 新增
  start_date: string;
  planned_end_date: string;         // 新增
  north_star: {                     // 不变
    metric: string;
    unit: string;
    current_value: number | null;
    target_value: number | null;
    delta: number | null;
    history: number[];
  };
  support_metrics: Array<{          // 不变
    metric: string;
    unit: string;
    current_value: number | null;
  }>;
}

// 新增
export interface GoalData {
  id: string;
  description: string;
  north_star_target: {
    key: string;
    baseline: number;
    target: number;
    unit: string;
  };
  start_date: string;
  target_date: string;
  status: string;
}

// MirrorData 扩展
export interface MirrorData {
  identity_statement: string | null;  // 新增：从 profile 读取
  goal: GoalData | null;              // 新增
  chapter: ChapterData | null;
  copingPlans: CopingPlan[];
}
```

## 六、MIRROR 仪表盘调整

在现有 MirrorPanel 布局上微调，不重建。

### 当前布局

```
Chapter N · start_date
"identity_statement"         ← 楷体引用
goal                         ← 小字

★ 北极星
  数值 + 趋势柱状图

支持指标 ×3

LifeSign 预案

见证卡库
```

### 调整后布局

```
"identity_statement"         ← 保留楷体引用，数据源从 chapter 改为 profile
我的目标：12 周 75→70kg      ← 新增：从 goal/current.json 读取（纯文本，不带进度条）

Chapter N · 认识饮食模式      ← title 替代原 goal
里程碑：连续两周三餐记录完整   ← 新增 milestone 展示

★ 北极星
  体重趋势 + 7 日柱状图       ← 不变

本周节奏                      ← 标签微调，内容不变
  记录天数  4/7               ← support_metrics[0]
  蛋白达标  5/7               ← support_metrics[1]
  今日状态  7/10              ← support_metrics[2]

LifeSign 预案                ← 不变

见证卡库                      ← 不变
```

**变更量极小**：
1. Identity 数据源从 `chapter.identity_statement` 改为 `profile.identity_statement`
2. 新增一行 Goal 描述（纯文本，不带进度条，避免与北极星柱状图冲突）
3. Chapter 区域显示 `title` + `milestone`（替代原 `identity_statement` + `goal`）
4. 其余完全不变

## 七、Onboarding 影响

### 7.1 核心变化：新增 Plan Scaffold 阶段

在现有 Phase 4 之后、Phase N 之前，新增 **Phase 5: Plan Scaffold**。

**设计意图**：让用户带着行动方向离开 onboarding，而不仅仅带着"我是谁"和"我怕什么"。

**快速路径**：Coach 基于已采集信息全量推断，用一段话概述行动框架，用户确认即可。
**完整路径**：Coach 逐项与用户讨论，协作确定。

Phase 5 具体内容：Coach 基于前几轮对话中已采集的信息，提出行动框架草案——结果目标（含时间约束）、第一个 Chapter 的主题和里程碑、2-3 个 Process Goal。用户确认或微调。

**快速路径**：Coach 全量推断并概述，用户确认即可。**完整路径**：Coach 逐项与用户讨论。

### 7.2 数据产出调整

**最小数据集（更新）**：

| # | 路径 | 内容 | 变更 |
|---|------|------|------|
| 1 | `/profile/context.md` | 名字、depth_choice、场景数据、`identity_statement`、`onboarding_complete: true` | 新增 identity_statement |
| 2 | `/goal/current.json` | 结果目标 + 时间约束 + north_star_target | **新增** |
| 3 | `/chapter/current.json` | 第一个 Chapter：title、milestone、process_goals[]、planned_end_date | 字段调整 |
| 4 | `/profile/dashboardConfig` | north_star + support_metrics（由 process_goals 驱动） | 语义调整 |
| 5 | `/ledger/{date}/{time}_system.json` | 种子事件 | 不变 |
| 6 | `/coping_plans/{id}.json` + index | 首批 LifeSign（可选） | 不变 |
| 7 | `/timeline/markers.json` | 前瞻标记（可选） | 不变 |

### 7.3 Onboarding Phases 总览（调整后）

| Phase | 目的 | 产出 |
|-------|------|------|
| 1 Depth Choice | 尊重自主性 | depth_choice |
| 2 Goals & Identity | 身份愿景 + 距离感知 | identity_statement（写入 profile） |
| 3 Context & Danger | 高风险场景 | LifeSign 种子、Forward Marker |
| 4 Personal System | LifeSign 创建、指标确认 | LifeSign、dashboardConfig |
| **5 Plan Scaffold** | **行动框架** | **Goal、Chapter（含 process_goals）** |
| N Wrap-up | 数据写入、启程仪式 | Witness Card、onboarding_complete |

## 八、Coach System Prompt 影响

### 8.1 Section 3 Coaching Instruments 变更

需要更新或新增三个 Instrument 定义：

变更已直接应用至 `backend/prompts/coach_system.j2`，具体 diff 见 git。核心内容：

- Section 3 Coaching Instruments：新增 Identity、Goal、Process Goal 三个 Instrument 定义；重写 Chapter 定义（从身份阶段变为时间阶段，固定 3 个 Process Goal）；Chapter transition 操作扩展（含 dashboardConfig 同步和 Identity 演化评估）
- Section 3 Metrics Governance：新增指标语义（North Star 滞后 / support_metrics 领先 / State 调节）；Chapter 过渡时同步更新 support_metrics
- Section 4 Tools：新增 `/user/goal/` 路径

## 九、实施顺序

1. **数据 + Prompt**：新增 goal store path → 调整 chapter 字段 → identity 上移至 profile → 更新 coach_system.j2 和 onboarding.j2 → 更新 store_contract.py
2. **前端适配**：store-sync.ts 接口更新 → MirrorPanel 布局微调
3. **验证**：eval fixture 更新 → 契约验证

## 十、不在本方案范围内

- 每日计划数据实体（由 S-PDCA Check-in 对话动态生成，不需要持久化结构）
- Goal 完成后的自动新建流程（Coach 在对话中引导即可）
- 多 Goal 并行（当前场景为单一减脂目标，不需要）
- Process Goal 的独立存储（内嵌于 Chapter，足够简单）
- 仪表盘的交互增强（趋势图点击等，独立于本方案）

---

## 附录 A：学术依据摘要

| 理论 | 核心观点 | 在本方案中的应用 |
|------|---------|----------------|
| Carver & Scheier 控制层级（1998） | 身份是目标层级最高设定点 | Identity 在 Goal 之上，约束关系 |
| Oyserman IBM（2015） | 身份决定困难的解读方式 | Identity 是挫折复原力来源 |
| Locke & Latham（2006） | 近端目标提升自我效能 | Process Goal 作为近端行为目标 |
| Dai, Milkman & Riis（2014） | 新鲜起点效应 | Chapter 与自然时间地标对齐 |
| Gollwitzer（1999） | if-then 计划效应量 d=0.65 | LifeSign 保持不变 |
| BCT Taxonomy v1（Michie 2013） | 1.1 行为目标 / 1.3 结果目标 / 1.4 行动计划 | Process Goal / Goal / LifeSign 分别对应 |
| SDT（Deci & Ryan 2000） | 自主性需求 | Process Goal 共创而非指定；每日意图弹性 |
| 领先 vs 滞后指标 | 追踪领先指标维持率高 3.2 倍 | Coach 日常反馈聚焦 Process 指标 |

## 附录 B：术语对照（内部概念 → 用户感知）

| 内部概念 | 用户在仪表盘上看到的 | 用户在对话中感受到的 |
|---------|-------------------|-------------------|
| Identity | 楷体引用语 | "你这几周越来越像一个掌控节奏的人" |
| Goal | "我的目标：12 周 75→70kg" | "你当初说想在 12 周内到 70" |
| Chapter | "Chapter 1 · 认识饮食模式" | "这几周我们先关注记录习惯" |
| Process Goal | 支持指标（记录天数 4/7） | "这周我们说好关注蛋白质，今天状态怎样？" |
| LifeSign | 触发 → 应对 | "上次你说聚餐前先喝水，今天试试？" |
| S-PDCA | 不可见 | 自然的对话节奏 |
| North Star | 体重趋势 + 数值 | "体重这两周稳步下降" |
| State 指标 | 不在仪表盘上 | 晨间 Check-in 的滑块 |
