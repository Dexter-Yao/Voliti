<!-- ABOUTME: Onboarding 对话流程重设计规格文档 -->
<!-- ABOUTME: 定义混合叙事式交互模型、自适应深度、prompt 设计哲学与数据产出要求 -->

# Onboarding 对话流程重设计

## 一、设计背景

当前 onboarding 采用 5 步线性流程（Name → Future Self → Current State → Scene Recognition → Near-term Events），由 SessionTypeMiddleware 注入一段高度具体的 prompt 驱动。主要问题：

1. **过于脚本化**：prompt 写死了 5 个步骤的顺序和具体做法，模型缺乏根据用户投入度灵活调整的空间。
2. **交互单一**：仅在场景识别环节使用一次 A2UI（multi_select），其余全靠自由对话，缺乏选项驱动的定制化回复。
3. **Coach 开场薄弱**：硬编码问候语仅一句自我介绍，未建立产品认知和信任。
4. **深度不可控**：所有用户走同一条路径，无法适应不同画像的耐受差异。

## 二、设计目标

1. 全屏沉浸、流畅的首次体验。
2. 混合叙事式交互：Coach 主导叙事节奏，每段结束给出选项，选项决定下一段方向和内容。
3. 用户选择 onboarding 深度（快速 / 完整），尊重自主性。
4. 无论哪条路径，都产出完整的最小数据集。
5. Prompt 提供框架和"为什么"，不写死"怎么做"。
6. Onboarding 对话过程本身作为产品数据资产，支撑后续分析与验证。

## 三、交互模型

### 3.1 混合叙事式（Approach C）

Coach 主导叙事节奏。每一段叙事结束后给出 2-3 个选项（建议回复按钮或 A2UI），用户的选择决定下一段叙事的方向和内容。Coach 根据用户选择给出定制化回复。

**选项呈现规则：**

| 场景 | 呈现方式 |
|------|----------|
| 深度选择（快速/完整） | A2UI select 组件（结构化，模型通过 tool result 接收） |
| 方向性选择（话题分��） | 建议回复按钮（2-3 个） |
| 结构化采集（场景识别、指标偏好） | A2UI 组件（multi_select / select） |
| 纯输入（名字、自由描述） | 不给建议回复，直接等待用户输入 |
| 场景补充描述 | A2UI 预设选项 + text_input 组合 |

### 3.2 自适应深度

在 Phase 1 由用户显式选择路径，而非模型猜测。两条路径的差异不在于"做几步"，而在于"问几轮"——快速路径下模型根据已有信息合理推断，输出同样完整的数据集。

## 四、流程结构

### Phase 0: Coach 自我介绍（硬编码）

**触发**：用户首次进入 onboarding，消息队列为空。

**内容**：

```
你好。

我是 Voliti Coach——你的减脂教练。

无论是每天该怎么吃、怎么动，还是突然想放弃时该怎么办，
我都会陪着你。不过我最擅长的，是帮你在压力、疲劳、
冲动来袭的那些时刻，守住你自己已经做出的选择。

我会记住你的习惯、你容易失控的场景、你在意的那个身份。
然后在关键时候提醒你——你想成为的那个人会怎么做。

怎么称呼你？
```

**英文版本**：

```
Hi.

I'm Voliti Coach, your weight loss coach.

Whether it's what to eat today, how to move, or what to do
when you suddenly want to give up, I'll be right here with you.
What I'm best at, though, is helping you hold on to the choices
you've already made when stress, fatigue, or impulse hits.

I'll remember your habits, the scenarios where you lose control,
and the identity that matters to you. Then at the key moments,
I'll remind you: what would the person you want to become do?

What should I call you?
```

**交互**：不给建议回复，等待用户输入名字。

**设计意图**：
- "无论是...还是...我都会陪着你"确立 All-in-One 减脂载体定位。
- "不过我最擅长的"自然过渡到行为对齐的独特价值。
- "记住你的习惯...在意的身份"预告个性化能力，建立信任。
- 语气温暖、直接，不讨好也不居高临下。

### Phase 1: 深度选择

**触发**：用户输入名字后，Coach 的第一轮 LLM 回复。

**内容**：Coach 用名字称呼用户，简述两种路径：

- **完整对话**（约 15 分钟）：深入了解你的目标、驱动力、容易失控的场景，一起建立你的个人体系。
- **快速开始**（约 5 分钟）：了解最关键的信息，尽快开始日常教练。之后随时可以补充。

**交互**：A2UI select 组件，两个选项。使用结构化组件而非建议回复按钮，确保模型通过 tool result 接收用户选择，不会漂移到另一条路径。选择结果同时写入 onboarding_progress 记录。

**设计意图**：
- 尊重用户自主性（SDT 自主性原则）。
- 适应不同画像耐受差异：执行困难者偏好低摩擦，连环节食者热情期可能选完整。
- 给出预计时间，降低不确定性。
- 结构化选择为后续分析提供干净的数据点。

### Phase 2: 目标与驱动力

**目的**：了解用户的减脂目标、内在驱动力和身份认同。

**Coach 需要理解的"为什么"**：
- 用户研究显示动机来自外观焦虑时脆弱，需要翻译为内在身份。
- "我想成为什么样的人"比"我要减多少斤"更持久。
- 身份可以是多重的、演化的，不需要锁死为一个。

**核心采集（两条路径都覆盖）**：
1. 期望成为什么样的人（身份愿景，非数字目标）
2. 当前与愿景的距离感知

**完整路径额外探索**：
- 驱动力来源：什么事件或感受让你决定开始？
- 多重身份探索：除了减脂，还有哪些身份对你重要？
- 内在动机挖掘：如果没有人看到你的变化，你还会坚持吗？

**交互**：对话为主，关键节点给建议回复引导方向。

### Phase 3: 现状与背景

**目的**：掌握用户的当前状态、危险场景和减脂经历。

**Coach 需要理解的"为什么"**：
- 知行分离是根本问题——用户不缺方法论，缺的是关键时刻的执行力。
- 场景识别是第一个 Aha Moment："这个 App 记住了我的弱点"。
- 基于真实经历的场景比抽象选项更有行动指导价值。

**核心采集（两条路径都覆盖）**：
1. 最危险的场景识别（预设选项 + 自由补充）

**场景识别的交互设计**：
- A2UI 呈现 multi_select 预设场景（节假日 / 聚餐社交 / 出差差旅 / 情绪低谷 / 疲劳睡眠不足 / 其他）
- 用户选择后，Coach 针对所选场景追问具体经历
- 即便选了预设选项，用户仍可补充描述以丰富场景信息
- text_input 组件允许自由添加预设外的场景

**完整路径额外探索**：
- 过往减脂经历：试过哪些方法？什么时候最接近成功？什么导致了放弃？
- 近期生活安排（前瞻标记采集）：未来 2-4 周有什么已知事件？
- 当前生活节奏：工作强度、作息、社交频率

**交互**：A2UI（场景识别）+ 对话（追问具体经历）+ 建议回复（引导话题转换）。

### Phase 4: 建立个人体系（完整路径，或快速路径的推断版）

**目的**：引导用户建立 LifeSign 预案、北极星指标和身份认知。

**Coach 需要理解的"为什么"**：
- LifeSign 预案是用户在清醒时为脆弱时刻预设的 if-then 应对方案。
- 北极星指标 + 3 个支持性指标构成用户的个人仪表板。
- 身份认知不是一次性声明，而是持续演化的自我理解。

**完整路径**：
1. 从 Phase 3 识别的场景中，引导建立首个 LifeSign 预案。
2. 讨论并确认北极星指标和支持性指标。
3. 基于 Phase 2 的身份愿景，精化为具体的身份陈述。

**快速路径**：
- Coach 不逐一讨论，而是基于 Phase 2-3 收集的信息，合理推断并生成：
  - 北极星指标（减脂场景默认体重 + 合理单位）
  - 3 个支持性指标（基于用户提到的关注点推断）
  - 身份陈述（基于用户描述的愿景提炼）
  - 如果有足够的场景信息，尝试生成首个 LifeSign
- 推断结果在收尾阶段由 Coach 简要告知用户，不要求确认。

### Phase N: 收尾

**所有路径共同执行**：

1. **数据写入**：确保最小数据集完整写入 Store：
   - `/user/profile/context.md`（含 `onboarding_complete: true`）
   - `/user/profile/dashboardConfig`（北极星 + 3 支持指标）
   - `/user/chapter/current.json`（首个身份 Chapter）
   - 可选：`/user/coping_plans/`（LifeSign 预案）
   - 可选：`/user/timeline/markers.json`（前瞻标记）

2. **Witness Card 启程仪式**：自动调用 witness_card_composer subagent，生成 future_self 仪式卡片，无需用户同意。**Witness Card 生成失败（API 超时、图片生成异常等）不得阻塞 onboarding 完成**——Coach 应优雅跳过并在后续 coaching 会话中补偿。

3. **引导后续补充**：Coach 自然提到"以后你随时可以从设置页面回来继续告诉我更多关于你的事"。

4. **平滑过渡**：结束 onboarding 会话，前端检测到 `onboarding_complete: true` 后切换到主界面。

### Onboarding 进度追踪与中断恢复

#### 进度记录

新增 Store 路径 `/user/onboarding_progress`，由 Coach 在每个 Phase 完成后更新：

```json
{
  "depth_choice": "quick|full",
  "phases_completed": ["phase_0", "phase_1", "phase_2"],
  "turns_per_phase": {"phase_0": 1, "phase_1": 3, "phase_2": 5},
  "scene_selections": ["social", "mood_low"],
  "started_at": "2026-04-12T10:00:00Z",
  "total_duration_minutes": 8,
  "witness_card_result": "accepted|rejected|skipped|failed",
  "completed_at": null
}
```

该记录同时服务于两个目的：
1. **中断恢复**：用户下次进入 onboarding 时，Coach 读取此记录判断断点。
2. **数据分析**：结构化记录替代从对话日志中手动提取的分析方式。

#### 恢复逻辑（写入 prompt 框架层）

每次 onboarding 会话开始时，Coach 检查已有数据判断断点：

1. 有 `onboarding_progress` 且 `completed_at` 非空 → 这是 re-entry（补采模式）
2. 有 `onboarding_progress` 但 `completed_at` 为空 → 用户中断了，从最后完成的 Phase 之后继续
3. 有 `profile/context.md` 但无 `onboarding_progress` → 旧版用户，按 re-entry 处理
4. 什么都没有 → 新用户，从头开始

#### 完成判定的韧性

为防止 Store 不可达或 Witness Card 仪式失败导致用户永久困在 onboarding：

1. 主路径：Store 中检测到 `onboarding_complete: true`（现有机制）。
2. 备用路径：`onboarding_progress.completed_at` 非空（新增的进度记录）。
3. 兜底路径：保留现有本地 fallback 机制（`shouldMarkOnboardingComplete`），直到进度追踪经过充分验证后再移除。

三条路径任一满足即标记完成，防止单点故障。

## 五、Prompt 设计哲学

### 5.1 三层结构

```
┌─────────────────────────────────────┐
│  框架层                              │
│  流程阶段 + 每阶段的目的              │
│  （为什么要问这个，不是怎么问）        │
├─────────────────────────────────────┤
│  约束层                              │
│  边界 + 禁区 + 节奏规则 + 推断授权    │
│  （什么不能做，什么时候收束）          │
├─────────────────────────────────────┤
│  上下文层                            │
│  用户研究洞察摘要                     │
│  （知行分离、重启疲劳、身份优于数字）  │
└─────────────────────────────────────┘
```

### 5.2 核心原则

1. **告诉 Coach 每一步的"为什么"和"边界"**，让它自己决定"怎么问"和"怎么回应"。
2. **不写死对话脚本**，而是提供决策框架。
3. **嵌入用户研究洞察**作为 Coach 的认知基础，而非执行指令。
4. **推断授权**：快速路径下，Coach 被显式授权基于已有信息合理推断未采集的字段。
5. **收束信号**：Coach 应能识别用户投入度下降的信号（回复变短、选择跳过），并优雅收束。

### 5.3 禁区（写入 prompt 约束层）

1. 不以体重数字作为对话的开场或核心。
2. 不在 onboarding 中使用"你应该知道"框架。
3. 不给出过于具体的饮食/运动方案（onboarding 阶段信息不足）。
4. 不创造"AI 是你的朋友"的虚假期待——定位是教练。
5. 不催促用户完成所有步骤——尊重用户选择的深度。
6. 不在 Phase 0 之外硬编码任何对话内容。

### 5.4 上下文层洞察摘要（嵌入 prompt）

Coach 在 onboarding 中应以这些洞察为认知基础：

1. **知行分离是根本问题**：用户不缺方法论，缺的是在关键时刻的执行力和陪伴。
2. **外观焦虑驱动的动机脆弱**：需要帮助用户将外在动机翻译为内在身份认同。
3. **身份可以是多重的**：一个人可能同时是"想变健康的父亲"和"想找回掌控感的职场人"。
4. **场景识别是第一个 Aha Moment**：用户感受到"这个 App 真的记住了我的弱点"。
5. **失控后的第一句话决定能否重启**：好奇而非评判。
6. **初始承诺规模必须限制**：防止热情期过激承诺导致 6-8 周崩溃。
7. **私密性是隐性承诺**：1v1 教练架构减少社交压力。

## 六、数据产出

### 6.1 最小数据集（两条路径都必须产出）

| 数据 | Store 路径 | 来源 |
|------|-----------|------|
| 用户档案（含 name, goal, onboarding_complete: true） | `/user/profile/context.md` | 对话采集 + 推断 |
| 仪表板配置（北极星 + 3 支持指标） | `/user/profile/dashboardConfig` | 对话采集 / 快速路径推断 |
| 首个身份 Chapter | `/user/chapter/current.json` | 对话采集 / 快速路径推断 |

### 6.2 可选数据（完整路径或信息充分时）

| 数据 | Store 路径 | 来源 |
|------|-----------|------|
| 首个 LifeSign 预案 | `/user/coping_plans/{id}.json` | 场景识别 + 对话共创 |
| LifeSign 索引 | `/user/coping_plans_index.md` | 自动同步 |
| 前瞻标记 | `/user/timeline/markers.json` | 近期事件采集 |

### 6.3 快速路径的推断规则

当用户选择快速路径时，Coach 被授权基于以下逻辑推断未显式采集的字段：

| 字段 | 推断逻辑 |
|------|----------|
| 北极星指标 | 减脂场景默认 `weight` / `体重` / `numeric` / `KG` / `delta_direction: decrease` |
| 支持指标 1 | 默认 `calories` / `今日摄入` / `numeric` / `KCAL` |
| 支持指标 2 | 默认 `state` / `今日状态` / `scale` / `/10` |
| 支持指标 3 | 默认 `consistency` / `本周一致性` / `ratio` |
| 身份陈述 | 基于用户描述的愿景提炼，格式："正在[动词短语]的人" |
| Chapter 目标 | 基于用户提到的最具体的近期目标 |
| user_goal | 基于对话中提及的数字目标或身份目标生成摘要 |

## 七、Onboarding 数据分析

Onboarding 对话过程是产品数据资产，需支撑后续分析与 MVP 验证。

### 7.1 关键数据采集点

| 采集点 | 数据 | 用途 |
|--------|------|------|
| 路径选择 | 快速 / 完整 | 用户画像与深度偏好相关性 |
| 每阶段对话轮次 | 每个 Phase 的 user/assistant 消息数 | 用户投入度分布 |
| 选项选择分布 | 建议回复 / A2UI 选项的选择统计 | 热门选项识别、流程优化 |
| 自由输入长度 | 用户自由输入的字符数 | 投入度信号 |
| 场景识别结果 | 选中的预设场景 + 自由补充内容 | 场景覆盖度验证 |
| 收束触发点 | Coach 在哪个 Phase 判断需要收束 | 自适应逻辑效果验证 |
| 总时长 | onboarding 开始到完成的时间 | 与留存相关性分析 |
| Witness Card 审阅结果 | accepted / rejected / skipped | 启程仪式的情感价值验证 |

### 7.2 记录机制

主要通过 `/user/onboarding_progress` Store 路径记录（见 Phase N "进度追踪"章节）。该记录由 Coach 在每个 Phase 完成后更新，同时服务中断恢复和数据分析两个目的。补充性事件可通过现有 ledger 通道记录。

## 八、前端变更

### 8.1 硬编码问候语更新

`OnboardingGreeting.swift` 中的 `textZH` / `textEN` 需要替换为新版 Coach 自我介绍。

### 8.2 Re-entry 引导

Settings 页面的"继续了解我"入口保持不变。收尾阶段 Coach 的引导语确保用户知晓此入口。

### 8.3 其他前端逻辑

OnboardingView 的两阶段视觉（Welcome → Conversation）、fullScreenCover 模式、thread 隔离、完成检测机制均保持不变。

## 九、后端变更

### 9.1 SessionTypeMiddleware 的 Onboarding Prompt

完全重写 `_ONBOARDING_PROMPT`，从脚本式改为框架式。遵循第五节的三层结构设计。

### 9.2 Completion Requirements 调整

当前 prompt 中的 completion requirements 保持核心不变（profile + dashboardConfig + chapter + witness_card），但措辞从"必须完成以下步骤"改为"确保以下数据完整写入"，赋予模型更多灵活性。

### 9.3 推断授权

新增推断规则到 prompt 的约束层，明确授权 Coach 在快速路径下基于合理推断补全未采集字段。

### 9.4 Onboarding 进度追踪

新增 Store 路径 `/user/onboarding_progress`。Coach 在 prompt 框架层被指示在每个 Phase 完成后更新此记录。该路径属于 `runtime_only` 语义分类（非权威长期语义），不受 MemoryLifecycleMiddleware 的 promotion 规则约束。

### 9.5 恢复检查

在 prompt 框架层新增恢复逻辑段落，指示 Coach 在每次 onboarding 会话开始时检查已有数据判断断点（见 Phase N "恢复逻辑"章节）。

## 十、验证

1. 重写 prompt 后，运行 `cd backend && uv run python -m pytest` 确认测试通过。
2. 运行 `cd eval && uv run python -m voliti_eval` 验证 onboarding seed 场景的行为合规性。
3. 手动测试两条路径（快速 / 完整），验证数据产出完整性。
4. 检查 Witness Card 仪式在两条路径下都能正常触发。

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-12 | 初始创建：混合叙事式交互模型、自适应深度、prompt 三层设计、数据产出规格 |
| 2026-04-12 | CEO Review：新增 onboarding 进度追踪与中断恢复机制；深度选择改为 A2UI select；Witness Card 失败不阻塞完成；补充英文问候语；新增完成判定三层韧性 |
