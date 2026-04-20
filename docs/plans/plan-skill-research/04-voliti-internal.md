# Plan Skill 设计——Voliti 内部资产系统梳理

> **文档类型**：设计研究（READ-ONLY）  
> **梳理范围**：Voliti docs/ 及 backend/prompts/ 既有资产  
> **产出日期**：2026-04-19  
> **梳理深度**：与 Plan Skill 四层分解结构的直接关联

---

## 一、既定产品结论：不可违反的硬约束

### 1.1 核心定位与反打卡原则

**硬约束**：
- **Voliti 不是减脂工具，是行为一致性教练** 
  - 核心解决"知道该怎么做却做不到"，而非"知识不足"
  - `docs/01_Product_Foundation.md § 一` 第 6-10 行
  
- **Coach 是用户的唯一接口，后台分析对用户透明**
  - 用户只面对一个"教练"，无多套 agent 或厚重对话路由
  - `docs/01_Product_Foundation.md § 七` 第 310-316 行
  - `docs/03_Architecture.md § 3.3` 第 143-161 行
  
- **设计哲学：反打卡、反激励化、反游戏化**
  - "Map Over Metrics"：用户走在路径上，而非被仪表盘监控
  - `docs/02_Design_Philosophy.md § 一、二` 第 9-41 行
  - 禁止 streak 语言、打卡框架、成就徽章
  - `docs/01_Product_Foundation.md § 6.1` 第 231-247 行

### 1.2 私密感与反群体验证

**硬约束**：
- **用户偏好私密、低评判、低摩擦的支持**
  - 79% 偏好私密方式，仅 3% 未用过 AI
  - `docs/07_User_Research.md § 二` 第 47 行
  - `docs/08_Customer_Journey_Map.md § 五` 第 134 行
  
- **不应投入社区、排名、公开展示**
  - 禁止内容：公开社区、排名式打卡、通用食谱展示、GLP-1 陪聊化定位
  - `docs/08_Customer_Journey_Map.md § 七` 第 179-186 行

### 1.3 State Before Strategy 原则

**硬约束**：
- **高压力/疲劳状态下计划无效，优先恢复认知资源**
  - 这是所有 Plan 相关设计的底层前提
  - `docs/01_Product_Foundation.md § 二.2` 第 55 行
  - `docs/01_Product_Foundation.md § 一` 第 13-16 行
  
- **失控之后，复原 > 计划**
  - 留存决定时刻不是第 1 天，而是"第一次明显破功之后"
  - `docs/08_Customer_Journey_Map.md § 六` 第 145-151 行
  - 复原设计应围绕"复原路径"而非"连续路径"展开

### 1.4 伦理与身体形象边界

**硬约束**：
- **绝对禁止**：理想化身材、身体对比、任何聚焦体重/体型的干预
- **聚焦内容**：行为能力与情境掌控、身份演化、应对策略
- `docs/01_Product_Foundation.md § 6.1.1` 第 241-245 行

---

## 二、用户研究对 Plan Skill 的直接含义

### 2.1 四类核心用户画像与对 Plan 的不同需求

**用户共性**：
- 年龄 25-40 岁，中基数（5-15 斤），曾有效但反弹
- 66% 反弹，不是初始失败；43% 有效但反弹，26% 效果有限
- `docs/07_User_Research.md § 一` 第 18-24 行

**失败归因**（关键对 Plan 设计的含义）：
- 51% 节奏被打乱（非计划有误，而是执行环境变化）
- 26% 方案难执行（方案刚性 → 需要弹性 B 计划，而非精细单一计划）
- 详见 `docs/07_User_Research.md § 二` 第 40-45 行

**核心 Persona：周衡**
- 30 岁，城市知识工作者，中基数
- **决策风格偏理性**：更吃数据、逻辑、结构，**不吃空泛安慰**
- **MBTI 特征**：94% N 型（直觉），69% T 型（思维）——偏理性分析
- **对 Plan 的期待**：不要泛化计划，要基于我真实的行为历史与约束
- `docs/07_User_Research.md § 一` 第 31-33 行，`docs/08_Customer_Journey_Map.md § 三` 第 34-37 行

**对 Plan 形态的直接含义**：
- **方案必须内置弹性（B 计划）**
  - 详细计划者归因"方案难执行"的比例是全样本的 1.6 倍
  - `docs/07_User_Research.md § 二` 第 55 行
  
- **Coach 默认人格应面向 NT 型**
  - 简洁、数据驱动、不过度共情
  - `docs/07_User_Research.md § 三` 教练设计第 56 行

### 2.2 第 6-8 周干预窗口与 phases 设计

**研究发现**：
- 留存的决定性时刻 = 第一次明显破功之后，而非第 1 周
- 用户最厌恶的不是失败本身，而是失败后系统只告诉他"你落后了"
- `docs/08_Customer_Journey_Map.md § 六` 第 145-151 行

**对 phases 设计的含义**：
- Plan 的 phases 不应只关注"完成进度"，要关注"失控恢复周期"
- 第 6-8 周是"新鲜感衰减"阶段，**需要持续相关而不是重复提醒**
- `docs/08_Customer_Journey_Map.md § 五` Retention 触点 第 87 行
- 最有决策价值的四个指标中，**第 3 项 = "首次失控后 72 小时回访率"**
- `docs/08_Customer_Journey_Map.md § 八` 第 195 行

### 2.3 失控后的首句话与 Plan 接入

**既定约束**：
- 失控之后，系统**没有要求继续记账或自责**
- 系统帮助"完成复盘、调整、复原"
- `docs/08_Customer_Journey_Map.md § 五` Retention 行 第 87 行

**对 Plan 的含义**：
- 失控后第一次 Coach 接入时，**不能说"按原计划继续"**
- 应该说"让我们一起看发生了什么，然后决定接下来怎么调整"
- Plan 要能**动态迭代**（不是固定快照），支持失控后的"计划修正"而非"计划执行追踪"
- 这是与"Coach 记忆"（LifeSign 迭代、模式识别）的接口点

---

## 三、旅程地图中 Plan 的触发点与呈现时机

### 3.1 Plan 首次出现的关键时刻

**Onboarding 阶段**（`docs/08_Customer_Journey_Map.md § 五` 第 85 行）：
- **用户此刻最关心**："它是真的懂我，还是只是换一种方式套模板？"
- **对 Plan 的含义**：Onboarding 中的 Plan 不应是"一份完整减脂餐计划"，而是
  - 基于用户**真实消费习惯、失败历史、现实约束**的首个**高风险场景预案**
  - `docs/01_Product_Foundation.md § 4.1` Onboarding 第 103-127 行
  - Plan 在此处的作用 = "被理解"的信号，而非"给方案"
- **代码端体现**：`docs/01_Product_Foundation.md § 四.1` 第 114-116 行定义了 Plan Scaffold（Goal 拆解首个 Chapter）

### 3.2 Plan 持续出现的时刻

**Engagement 阶段**（`docs/08_Customer_Journey_Map.md § 五` 第 86 行）：
- **晨间 check-in**：状态评估，**参考前瞻标记调整当天策略**
  - Plan 在此不是"提醒目标"，而是"响应当日状态的微调指南"
  
- **风险窗口触发**：
  - 前瞻标记（Forward Marker）接近时，Plan 变成"场景预演"支撑
  - 既有 LifeSign 匹配时，Plan 变成"预案引用"
  - `docs/01_Product_Foundation.md § 4.1` LifeSign 系统 第 141-153 行

- **日内微干预**：
  - 在高风险时刻主动触达，引用 LifeSign 预案
  - Plan 与 LifeSign 的关系 = 粗颗粒（阶段计划）vs 细颗粒（具体场景预案）

**Retention 阶段**（`docs/08_Customer_Journey_Map.md § 五` 第 87 行）：
- **第一次破功后 48-72 小时**：
  - 系统不是"重新下达计划"，而是"协作复盘、调整、重建信心"
  - Plan **必须支持版本化与迭代**，记录"原计划 → 失控 → 调整后计划"的演化链
  
- **连续数周使用、跨周总结**：
  - Plan 与 Chapter 的转场是主要节奏触发点
  - `docs/01_Product_Foundation.md § 4.1` Chapter transition 第 98 行

---

## 四、架构边界：Plan 与其他核心概念的数据关系

### 4.1 Plan 在层级结构中的位置

**既定层级**（`docs/01_Product_Foundation.md § 四` 与 Coach 系统提示词 `§4 Instruments`）：
```
Identity（用户身份）
  ↓
Goal（结果目标 + 时间约束）
  ├─ `north_star`（北极星指标）
  ├─ `current.json` 存储
  └─ `/goal/archive/{id}.json`（历史目标）
  
  ↓
Chapter（时间阶段，Goal 之下）
  ├─ `title` + `milestone` + 3 个 Process Goal
  ├─ `/chapter/current.json` 存储
  └─ `/chapter/archive/{id}.json`（历史章节）
  
  ↓
Process Goals（行为目标，与 support_metrics 一一映射）
  └─ `/profile/dashboardConfig` 中的 `support_metrics`
  
  ↓
LifeSigns（高风险场景预案）
  └─ `/coping_plans_index.md` + `/coping_plans/*.md`
```

**Plan Skill 的插入点**：
- Plan 在**"Goal → Chapter"之间的细化环节**
- 或在**"Chapter 内的 Process Goals → daily_rhythm 执行"之间**
- 当 Coach 说"当用户需要一份结构化计划"时，调用 Plan Skill
- `docs/01_Product_Foundation.md § 一` 第 40 行，Coach 系统提示词 `§5` 第 133-135 行

### 4.2 Plan 与 Chapter 的分工与边界

**Chapter 定义**（`docs/01_Product_Foundation.md § 四` 第 93 行，Coach 系统提示词 `§4` 第 93 行）：
- `title` + `milestone` + exactly 3 Process Goals
- **定义的是"阶段目标与行为维度"，不是"每日执行细节"**
- Duration 由 Coach 与用户共同确定（自然地标：月初、旅行后等）

**Plan Skill 定义应补充**：
- 当 Chapter 已有时，Plan 的职责是**"将 3 个 Process Goals 细化为具体执行框架"**
  - 包括：热量目标 + 宏量分配、进食节奏、训练安排、食物选择约束等
  - 这些是 Chapter 里 Process Goals 的**具体化**，而非新增层
  
- 当 Chapter 还未有时（Onboarding），Plan Scaffold 就是 Chapter 创建的**副产品**
  - `docs/01_Product_Foundation.md § 4.1` 第 114-115 行

### 4.3 Plan 与 LifeSign（预案系统）的协作

**既定**：
- LifeSign 是 if-then 预案，针对高风险时刻
- 最多 6 条，每条 ≤100 字
- `docs/01_Product_Foundation.md § 4.1` LifeSign 第 141-153 行

**Plan 与 LifeSign 的关系**：
- Plan = 日常基准（"一般情况下每天这样吃/动"）
- LifeSign = 偏差响应（"如果出现 X 就执行 Y 应对"）
- 前瞻标记（Forward Marker）关联 LifeSign 时，Plan 变成"背景支撑"
  - 例：聚餐明天，LifeSign 预案 + Plan 当日调整 → 场景预演干预
- `docs/01_Product_Foundation.md § 4.1` 前瞻标记触发 第 149-150 行

### 4.4 Plan 与 Briefing（每日上下文）的关系

**Briefing 定义**（`docs/05_Runtime_Contracts.md § 10.3` 第 456 行）：
- `/derived/briefing.md`：Goal / Chapter / Process Goals 的预计算摘要
- 作为 Coach 每日上下文只读来源
- 由 Day-End Pipeline 自动生成

**Plan 与 Briefing 的关系**：
- Briefing 中的 Process Goals 来自 Chapter，而 Chapter 由 Plan Skill 细化
- Briefing 是"Plan 执行状态的快照投影"，而非 Plan 本身
- 当用户复盘失控时，Coach 可能需要**读取原 Plan + 当前 Briefing，然后协作修正计划**
- 这是 Plan Skill 与 Briefing 层的**只读关联**（Plan Skill 读 Briefing，不写）

### 4.5 Store 契约的扩展点：新增 `/plan/current.json`

**既定 Store 路径**（`docs/05_Runtime_Contracts.md § 6.2`）：
```
/profile/context.md
/profile/dashboardConfig
/goal/current.json
/goal/archive/{id}.json
/chapter/current.json
/chapter/archive/{id}.json
/coach/AGENTS.md
/coping_plans_index.md
/lifesigns.md
/timeline/markers.json
/derived/briefing.md
/day_summary/{yyyy-mm-dd}.md
/conversation_archive/{yyyy-mm-dd}.md
```

**建议新增路径**：
- `/plan/current.json`（当前有效的详细计划）
  - 结构：缘何建立（JTBD）+ 热量目标 + 宏量 + 进食节奏 + 训练框架 + 食物约束 + 版本号
  - 写入方：Plan Skill 在用户确认后
  - 读取方：Coach 在晨间 check-in 时参考，失控复盘时对比修正
  
- `/plan/archive/{id}.json`（历史计划版本）
  - 记录修正历史，供分析"计划调整的模式"
  - 示例：初始计划 → 失控后修正 → 再失控后修正，形成"计划演化链"

- 或 `/plan/versions.md`（轻量索引）
  - 当前版本号、修改时间、修改原因、涉及失控事件的相关数据
  - 类似 LifeSign 的 `/coping_plans_index.md` 模式

**强格式路径**（需要 Pydantic 校验）：
- `/plan/current.json` 应添加到 `backend/src/voliti/contracts/__init__.py`
- 对应 `PlanRecord` Pydantic 模型
- 参考 `docs/05_Runtime_Contracts.md § 6.5` 第 188-204 行

---

## 五、现有 Skill 架构范式——对 Plan Skill 的借鉴

### 5.1 五份现有 Skill 的通用模板（从 SKILL.md 提炼）

**文件结构与命名**（`docs/10_Experiential_Interventions.md § 2`）：
```
backend/skills/coach/{kind}/
├── SKILL.md                     # LLM 直接消费的事实源
├── references/theory.md         # 学术与文化背景
├── references/dialogue-examples.md（可选，演示案例）
└── tool.py                      # 专用 A2UI 工具
```

**SKILL.md 统一结构**（从 future-self-dialogue 与 scenario-rehearsal 提炼）：
```markdown
---
name: <kind>
description: <Coach 需要理解的触发条件 + 禁止条件>
license: internal
---

# <中文方法名>

## When to Use
- 触发条件 1（最常见）
- 触发条件 2
- ...

## When NOT to Use
- 禁止场景 1
- 禁止场景 2
- State Before Strategy 覆盖场景

## Core Move
1. 具体操作步骤 1
2. 具体操作步骤 2
3. ...

## A2UI Composition
- Invoke 哪个专用工具
- Component 序列与槽位约束
- 特殊样式提示（如 scenario 的 IF-THEN chip）

## Guardrails
- 伦理红线 1
- 伦理红线 2
- 禁止内容（如理想化身材、理论术语等）

## Deeper References
- theory.md 在何时阅读
- dialogue-examples.md 在何时参考
```

### 5.2 四个 Intervention Skill 的 A2UI 工具模式

**通用模式**（`docs/10_Experiential_Interventions.md § 1`）：
```python
# tool.py 伪代码结构
def fan_out_<kind>(components: list[A2UIComponent]) -> A2UIPayload:
    # metadata 由代码硬编码（Coach 不写）
    return A2UIPayload(
        components=components,
        metadata={
            "surface": "intervention",           # 固定
            "intervention_kind": "<kind>",       # 固定
            # + 其他观测键（当前无工具写入路径）
        }
    )
```

**关键原则**：
- Coach 只决策"用哪个干预"，不传 metadata 或 layout
- `surface` / `intervention_kind` / `layout="full"` 由工具代码硬编码
- `test_intervention_tools.py` 字节级验证 metadata 正确性
- `docs/10_Experiential_Interventions.md § 2、4` 第 20-21、49-50 行

### 5.3 Coach 系统提示词中对 Skill 的约束

**既定约束**（Coach 系统提示词 `§5 Tactics`）：
- **State Before Strategy 优先**：dysregulated 用户优先 co-regulation，不技术
- **Interventions 不制造动机**，只放大既有动机
- **多个 fit 时选择用户需要的下一步**，不只看理论匹配
- **Hard stops**：心理危机、显式拒绝、session 末尾疲劳
- **Rhythm**：**最多一个 intervention 每 session**
- `Coach 系统提示词` 第 110-117 行

**对 Plan Skill 的含义**：
- Plan Skill 与四个 Intervention Skills（future-self-dialogue 等）并列
- Plan Skill **也应遵守 Rhythm 约束**：一次 session 最多一次 Plan 生成/修正对话
- Plan Skill 的触发应当明确，避免"每次都问要不要调计划"

### 5.4 现有 Skill 的测试范式

**既定范式**（`docs/10_Experiential_Interventions.md § 5.1`）：
- `backend/tests/test_intervention_tools.py`：23 项单测
  - metadata 硬编码校验
  - 动态加载验证
  - 响应处理
  - 组件校验
- `backend/tests/test_skills_sync.py`：theory.md 字节级同步校验
- `eval/seeds/17-20_*.yaml`：四种 intervention 各一个触发场景

**对 Plan Skill 测试的含义**：
- 需要类似的三层测试：工具层、同步层、eval 场景层
- Plan Skill 的工具测试应覆盖：
  - `/plan/current.json` 的 Pydantic 校验（写入 fail-closed，读取 fail-closed）
  - 版本化与迭代逻辑（原计划 → 修正，archive 更新）
  - Briefing 与 Plan 的一致性检查（Plan 的 Process Goals 应与 Briefing 对齐）

---

## 六、Coach 系统提示词中已规定的 Plan 行为

### 6.1 既有约束不可变

**既定说法**（Coach 系统提示词 `§5 Fat-loss Plan` 第 131-135 行）：
```
## Fat-loss Plan

When the user needs a structured plan (calorie target, macros, training schedule, meal structure), 
invoke the plan skill — do not improvise inline.

*The plan skill is under development. If unavailable, announce gracefully and continue with Goal + Chapter + Process Goals.*
```

**不可变含义**：
- Plan Skill **存在且可用**时，Coach 不自己编制计划
- Plan Skill **不可用**时，Coach 可以继续通过 Goal + Chapter + Process Goals 框架工作
- 这是 Coach 在处理"用户需要结构化计划"时的默认行为

### 6.2 与 Chapter transition 的关系

**既定**（Coach 系统提示词 `§4 Instruments`）：
```
**Chapter transition.** Signals: milestone met; LifeSign milestones showing behavioral shift; 
patterns visibly changed; user expresses readiness. On transition: archive current → create new → 
update `dashboardConfig.support_metrics` → evaluate Identity evolution → issue a `journey` Witness Card.
```

**对 Plan Skill 的含义**：
- Chapter 转场时（Chapter milestone 达成），是否应**自动触发 Plan 重生成**？
  - 当前 Coach 提示词未明确说，这是 Plan Skill 设计中的**待定义处**
  - 建议：Chapter 转场时，Coach 应提示"要不要调整本阶段的计划？"而不是强制重生成

### 6.3 State Before Strategy 对 Plan 的约束

**既定**（Coach 系统提示词 `§3 Principles`）：
```
- **State Before Strategy.** Assess state before offering any plan. 
  Two common states: just-lapsed + self-attacking (guilt escalating to compensation); 
  cycled-through-failure + flat (not upset, hollow).
```

**对 Plan Skill 的含义**：
- 用户刚失控并自责时，**不能说"按新计划继续"**
- 应该先用 cognitive-reframing 干预，再考虑是否调整 Plan
- Plan Skill 的调用前置条件 = "用户认知资源已恢复"

---

## 七、未解议题：docs 里未明说但影响 Plan 设计的问题

### 7.1 Plan 的版本化与修正流程

**问题**：当用户失控后，Plan 如何修正？

**既有线索**：
- LifeSign 是"动态更新"的：如果用户反馈某个预案持续无效，Coach 协作修改；如果用户发现更有效的应对，更新预案
- `docs/01_Product_Foundation.md § 4.1` LifeSign 第 153 行
- 但 Plan 是否也应支持类似的"版本化迭代"？还是保持单一快照？

**待设计**：
- 失控后 Coach 说"我们一起调整计划"时，是：
  - A. 创建新版本 Plan（保留历史），还是
  - B. 在原 Plan 上编辑修改（无历史），还是
  - C. 在原 Plan 上标记"临时调整"（灵活性最高但记录复杂）？
- `/plan/archive/` 目录是否应存在？如果存在，什么时机触发存档？

### 7.2 Plan 与 Process Goals 的同步边界

**问题**：Plan 里的"每日热量目标"与 Chapter 里的"摄入量 Process Goal"如何同步？

**既有线索**：
- Chapter 有 3 个 Process Goals，每个映射到 `/profile/dashboardConfig` 的一个 `support_metric`
- `docs/01_Product_Foundation.md § 4.1` 第 94 行，Coach 系统提示词 `§4` 第 100 行
- 但 Plan Skill 生成时，是否应该**创建或更新这些 Process Goals**？还是假设 Coach 已经创建好？

**待设计**：
- Onboarding 场景：Plan Scaffold 是 Chapter 创建的**副产品**，还是 Plan 创建 Chapter？
- 日常场景：Coach 说"我们调整一下计划"时，是否需要同步修改 Process Goals？

### 7.3 Plan Skill 与日常 check-in 的交互

**问题**：晨间 check-in 时，Plan 如何被呈现？

**既有线索**：
- 晨间 check-in 是轻量的：1-2 sliders + optional text_input
- `docs/01_Product_Foundation.md § 4.1` 第 139 行，Coach 系统提示词 `§7` 第 176 行
- 但当用户昨日失控或今日有前瞻标记时，是否应该**扇出 Plan 当日调整**？

**待设计**：
- Plan 的 A2UI 呈现形式是什么？
  - 仅文字卡片（"今日目标：热量 1600-1800"）？
  - 可交互的调整界面（"要不要为今天这个聚餐调整目标"）？
  - 完整的 Plan Skill `fan_out_plan(...)` 干预？

### 7.4 Plan 与前瞻标记（Forward Markers）的协作

**问题**：当前瞻标记触发（如"明天聚餐"）时，Plan 如何响应？

**既有线索**：
- Forward Markers 可以关联 LifeSign
- `docs/01_Product_Foundation.md § 4.1` 前瞻标记 第 149-150 行
- Coach 会"进行预防性准备"
- `docs/01_Product_Foundation.md § 四` Check 阶段 第 91 行

**待设计**：
- Forward Marker + LifeSign 匹配时，是否还需要生成临时性的 Plan 调整（如"聚餐当日的热量预留"）？
- 还是只调用 scenario-rehearsal 干预，Plan 保持不动？

### 7.5 Plan Skill 的"不可用"降级路径

**问题**：当 Plan Skill 不可用时，Coach 应该如何回退？

**既有线索**：
- Coach 系统提示词明确说了降级方案：
  ```
  The plan skill is under development. If unavailable, announce gracefully and 
  continue with Goal + Chapter + Process Goals.
  ```
  
**待设计**：
- "gracefully announce" 的具体措辞是什么？
- Coach 是否应该在缺少 Plan 的情况下仍能运作（MVP 模式）？
- 或者 Plan Skill 必须与整个 Coach 共发布（阻断性依赖）？

### 7.6 Plan Skill 对 Coach 内存的影响

**问题**：Plan Skill 生成的 Plan 是否应进入 Coach 记忆（`/coach/AGENTS.md`）？

**既有线索**：
- Coach 记忆有四个区：Verified Patterns / Hypotheses / Coaching Notes / Claimed-vs-Revealed
- 推测或计划痕迹应该记在哪里？

**待设计**：
- 当 Coach 与用户协作修正 Plan 时，修正原因（如"聚餐太频繁导致第一版失效"）应写入 Coach 记忆的哪个区？
- Plan 修正本身是否构成"Verified Pattern"（如"这个用户周末摄入普遍偏高，周一-周五要补偿"）？

---

## 八、关键发现摘要

### 发现 1：Plan Skill 不是"计划制定工具"，是"失控后的复原支撑"

**既有约束与用户研究的交汇点**：
- 用户失败归因：51% 节奏被打乱，而非计划有误 → Plan 应支持**动态调整，而非静态执行追踪**
- 留存决定时刻：第一次明显破功之后 → Plan Skill **最关键的应用场景是"失控 48-72 小时后的协作修正"**
- Coach 核心价值：失控前预防、失控后防螺旋 → Plan 版本化历史 = "计划演化链"，供识别模式
- **相关文档**：`docs/07_User_Research.md § 二` 第 40-45 行；`docs/08_Customer_Journey_Map.md § 五` 第 87 行；`docs/01_Product_Foundation.md § 一` 第 13-16 行

### 发现 2：Plan Skill 的设计人格应面向 NT 型（理性、数据驱动、反过度共情）

**既有约束与用户研究的交汇点**：
- 核心用户 MBTI：94% N 型，69% T 型
- 用户对 Plan 的期待：基于真实行为的结构化建议，而非泛化食谱
- Coach 默认人格：简洁、数据驱动、不过度共情
- **相关文档**：`docs/07_User_Research.md § 一` 第 31-33 行，`docs/07_User_Research.md § 三` 第 56 行；`docs/08_Customer_Journey_Map.md § 三` 第 34-37 行

### 发现 3：Plan 在架构中是"Chapter 细化层"，不是"独立决策层"

**既有约束与架构设计的交汇点**：
- Chapter 定义：`title` + `milestone` + 3 Process Goals（行为维度）
- Plan Skill 职责：将 Process Goals 细化为具体执行框架（热量、宏量、进食节奏、训练等）
- Store 契约：应新增 `/plan/current.json` + `/plan/archive/{id}.json`，支持版本化迭代
- **相关文档**：`docs/01_Product_Foundation.md § 四` 第 93-94 行，Coach 系统提示词 `§4 Instruments` 第 93-94 行，`docs/05_Runtime_Contracts.md § 6.2` 第 133-149 行

### 发现 4：现有四个 Intervention Skill 的架构范式完全适用于 Plan Skill

**关键复用模式**：
- SKILL.md = LLM 直接消费的事实源（Coach 通过 SkillsGate 加载）
- tool.py = A2UI 工具，metadata 由代码硬编码（Coach 不写）
- references/theory.md = 学术背景（Coach 在触发场景时按需阅读）
- 三层测试范式：工具层 + 同步层 + eval 场景层
- **相关文档**：`docs/10_Experiential_Interventions.md` 全文，特别是 § 2-5

### 发现 5：Plan Skill 的最关键未解议题是"版本化迭代流程与 Process Goals 同步"

**待设计的关键决策**：
1. 失控后修正 Plan 时：新建版本 vs 就地编辑 vs 临时标记？
2. Plan 修正时是否需要同步更新 Process Goals 与 dashboardConfig？
3. Forward Marker + LifeSign 匹配时是否生成临时 Plan 调整？
4. Chapter 转场时是否自动触发 Plan 重生成？
5. 晨间 check-in 中 Plan 的 A2UI 呈现形式？

**相关文档**：
- Coach 系统提示词关于 Chapter transition（`§4 Instruments` 第 98 行）
- Coach 系统提示词关于 State Before Strategy（`§3 Principles` 第 77 行）
- LifeSign 动态迭代说明（`docs/01_Product_Foundation.md § 4.1` 第 153 行）

---

## 附录A：文档交叉引用索引

| 既定约束/发现 | 来源文档 | 行号/章节 |
|---|---|---|
| 核心定位：行为一致性教练 | `docs/01_Product_Foundation.md` | § 一，6-10 行 |
| State Before Strategy | `docs/01_Product_Foundation.md` | § 二.2，55 行 |
| 四层理论闭环 | `docs/01_Product_Foundation.md` | § 二，23-54 行 |
| Onboarding 必答层 + 扩展层 | `docs/01_Product_Foundation.md` | § 4.1，103-127 行 |
| LifeSign 动态迭代 | `docs/01_Product_Foundation.md` | § 4.1，153 行 |
| Chapter 定义 | `docs/01_Product_Foundation.md` | § 四，93-94 行 |
| 反打卡设计哲学 | `docs/02_Design_Philosophy.md` | § 一、二，9-41 行 |
| Chapter 与 Process Goals | Coach 系统提示词 | `§4 Instruments`，93-94 行 |
| 用户失败归因 | `docs/07_User_Research.md` | § 二，40-45 行 |
| 核心 Persona 周衡 | `docs/08_Customer_Journey_Map.md` | § 三，29-50 行 |
| 留存关键时刻 | `docs/08_Customer_Journey_Map.md` | § 五 Retention，87 行 |
| Aha Moment 与 Onboarding | `docs/08_Customer_Journey_Map.md` | § 四、五，54-58、85 行 |
| 四个 Intervention Skills 范式 | `docs/10_Experiential_Interventions.md` | § 1-4 |
| Store 契约 | `docs/05_Runtime_Contracts.md` | § 6，121-204 行 |
| 语义边界分类 | `docs/05_Runtime_Contracts.md` | § 10.4，476-495 行 |
| Forward Marker 与 LifeSign 关联 | `docs/01_Product_Foundation.md` | § 四 Check，91 行 |
| 晨间 check-in 轻量交互 | `docs/01_Product_Foundation.md` | § 4.1，139 行；Coach 系统提示词 `§7`，176 行 |
| 前瞻标记预防性准备 | `docs/01_Product_Foundation.md` | § 四 Check，91 行 |
| Witness Card 频率 | `docs/01_Product_Foundation.md` | § 4.1，215 行 |

---

**文档完成日期**：2026-04-19  
**梳理范围**：Voliti docs/ + backend/prompts/ + backend/skills/  
**后续接口**：Plan Skill SKILL.md 编写时逐一确认这些待定义处的设计决策
