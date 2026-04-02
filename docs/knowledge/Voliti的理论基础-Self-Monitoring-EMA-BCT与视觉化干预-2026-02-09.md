# Voliti 的理论基础：Self-Monitoring、EMA、BCT 与体验式教练干预

元信息：
- 作者：Claude (基于学术文献综述)
- Topic：行为改变理论, 数字健康, AI教练, 减脂干预, 心理学
- 创建日期：2026-02-09
- 最后更新日期：2026-02-09

## 一句话简介

系统性阐述 Voliti 减脂教练产品的四层理论基础（Self-Monitoring、EMA、BCT、体验式教练干预），明确其在学术研究中的证据支持，并提供整合应用方案与实施优先级。核心聚焦教练干预的时机、内容与情感传递，而非表达形式。

---

## 核心分析

### 一、Self-Monitoring（自我监测）理论

**理论根源与核心机制**

Self-Monitoring 建立在三个经典理论基础之上：
- Kanfer & Karoly 的自我调节模型（1972）：自我监测 → 自我评估 → 自我强化的三阶段循环
- Carver & Scheier 的控制理论（1982）：负反馈回路（TOTE），强调双回路监控
- Bandura 的社会认知理论（1991）：Self-monitoring 是自我调节的第一核心组件

**核心机制：Reactivity（反应性）**——仅仅因为观察和记录行为，行为本身就会改变，无论记录准确性如何。实质是提高意识（awareness），打断自动化行为模式，激活有意识决策。

**关键研究发现**

1. **记录维度的重要性**：
   - 必需维度：行为本身 + 精确时间戳
   - 增强效果的关键维度：情境变量、情绪状态、生理状态
   - 研究表明："行为波动往往不是因为'缺乏意志力'，而是源于当下的情境与生理状态"

2. **频率、粒度、时机的影响**：
   - **一致性 > 频率**：每周 ≥3 天记录是效果阈值，宁可每天记录少量，不要间断多日
   - **即时记录 > 回忆记录**：即使同一天晚上回忆早餐，准确性已显著下降
   - 最佳时机：下午早些时候合规率最高（83%），清晨最低（56%）

3. **减重应用的证据强度**：
   - Self-monitoring 是行为减重干预的核心组件（cornerstone）
   - 数字化 self-monitoring 平均额外减重 2.87 kg（95% CI: -3.78 至 -1.96）
   - **最一致的预测因子**：自我调节技术包（self-monitoring + 目标设定 + 应对策略 + 问题解决）

**对 Voliti 的启示**

✅ 多维事件记录架构正确（时间戳 + 原始证据 + 情境标签 + 置信度）
✅ State-First 逻辑符合理论（状态不佳时降低记录负担）
⚠️ 需强化一致性支持机制（追踪连续记录天数，而非总次数）
⚠️ 需教育用户：self-monitoring 是识别模式，阻抗是信息

---

### 二、EMA（生态瞬时评估）理论

**核心定义与理论支柱**

EMA（Ecological Momentary Assessment）是在受试者自然环境中，实时重复采样其当前行为与体验的方法论。

三大理论支柱：
1. **最小化回忆偏差**：人们对一周前饮食摄入量估计误差可达 40-60%
2. **最大化生态效度**：在真实生活情境中采集数据，捕捉环境变量的实际影响
3. **捕捉微观过程**：行为受时间、情境、生理状态动态调节，EMA 捕捉个体内变异性（within-person variability）

**"生态"和"瞬时"的深层含义**：
- **生态**：不仅指"在现实环境中"，更强调捕捉**情境变量**对行为的即时影响
- **瞬时**：描述当下（"现在感觉如何"），而非总结过去（"今天感觉如何"）

**运行逻辑：三种采样方法**

1. **Signal-Contingent（信号触发）**：预设时间点推送问卷，能捕捉平时不被注意的状态
2. **Event-Contingent（事件触发）**：特定事件发生时用户主动记录，回忆偏差最小
3. **Interval-Contingent（间隔触发）**：按固定时间间隔采集，便于时间序列分析

**推荐混合策略**：主动记录（event）捕捉关键行为 + 随机信号（signal）采集背景状态

**多层次关联模型**

```
外层：情境变量（物理环境、社交环境、时间因素）
  ↓
中层：生理状态（睡眠、疲劳、饥饿、生理周期）
  ↓
内层：情绪状态（压力、沮丧、快乐、无聊）
  ↓
行为输出（饮食选择、摄入量、运动决策）
```

**关键交互效应**：工作日下午（情境）+ 睡眠不足（生理）+ 工作压力（情绪）→ 高糖零食摄入风险极高

**EMA 数据转化为可操作洞察的四阶段**

1. **模式识别**：个体化触发模式、时间模式、情绪-行为链
2. **可操作洞察生成**：触发因素识别、保护因素识别、环境优化建议
3. **JITAI（Just-In-Time Adaptive Interventions）整合**：基于实时状态提供动态干预
4. **持续演化**：指标治理能力、个性化演进

**对 Voliti 的启示**

✅ S-PDCA 与 EMA 深度整合：State 使用 signal-contingent，Do 使用 event-contingent，Check 识别模式，Act 实施 JITAI
✅ 事件文件结构天然适合 EMA（建议字段：context + state + behavior + derived）
✅ Coach Agent 的 JITAI 能力：实时风险评估 → 干预决策
⚠️ 需明确依从性优化策略（第一周建立习惯 → 第 2-4 周深度观测 → 第 5 周+ 个性化运行）
⚠️ "阻抗即信息"的 EMA 视角：用户连续 3 天未记录 → 不是失败，而是信号

---

### 三、BCT（行为改变技术）理论

**BCT Taxonomy 的理论基础**

- BCT Taxonomy v1（2013）包含 **93 项明确定义的 BCT**，分为 **16 个功能组**
- 最新 BCT Ontology 扩展至 161 项技术
- 涉及 400+ 名研究者的国际共识，建立跨学科、跨行为领域的通用语言

**从理论到可操作技术的转化路径**

```
理论层（Theory，如 COM-B, TTM, SCT）
  ↓
机制层（Mechanisms of Action, MoA）
  ↓
技术层（BCTs）← 可观察、可编码、可复制
  ↓
干预实施（Interventions）
```

**BCT 与 COM-B 模型的关系**（最核心的整合框架）：
- **Capability（能力）** → BCT 如：指导、示范、训练
- **Opportunity（机会）** → BCT 如：重构物理环境、社会支持
- **Motivation（动机）** → BCT 如：目标设定、反馈、信息提供

研究显示：**大多数 BCT 通过动机和意图改变行为**

**核心 BCT 深度解析**

1. **目标设定（Goal Setting）**
   - 原则：行为目标 > 结果目标（更可控），SMART 原则，接近型 > 回避型

2. **反馈（Feedback）**
   - 证据：数字化自我监测显著促进减重（效果量 d = 0.35-0.68）
   - 个性化反馈 > 通用反馈（效果差异达 2.1 kg）

3. **问题识别（Problem Solving）**
   - 核心是**应对计划（Coping Planning）**：建立"风险情境 → 应对反应"的心理链接
   - 研究显示：应对计划对长期行为维持的效果 > 单纯行动计划

4. **复盘与纠偏（Action Planning & Review）**
   - 关键发现：**自我调节 BCT 组合**（self-monitoring + goal setting + problem solving + coping strategies）是减重效果最一致的预测因子

**减重和健康行为改变的应用证据**

最有效的 BCT 组合：
1. Self-monitoring of behaviour（自我监测行为）
2. Goal setting (behaviour)（行为目标设定）
3. Problem solving（问题解决）
4. Action planning（行动计划）
5. Feedback on behaviour（行为反馈）

增效组合：
- 添加 Social support（社会支持）→ 额外 -0.8 kg
- 添加 Coping strategies（应对策略）→ 维持率 +23%
- 添加 Relapse prevention（复发预防）→ 长期维持 +35%

**关键发现**：
- 单一 BCT **无一致效果**
- **自我调节技术包**是唯一一致预测因子
- 个性化反馈 > 通用反馈（减重差异 2.1 kg）
- 即时反馈 > 延迟反馈（用户黏性 +40%）
- 多模态输入（照片 + 语音）> 纯文字（记录持续性 +28%）

**Voliti 的 BCT 映射**（当前隐式实现）

- **State 阶段**：15.4 Self-talk（自我对话），11.2 Reduce negative emotions（减少负面情绪）
- **Plan 阶段**：1.1 Goal setting (behavior)，1.4 Action planning，13.1 Identification of self as role model（身份认同）
- **Do 阶段**：2.3 Self-monitoring of behaviour，2.4 Self-monitoring of outcome(s)
- **Check 阶段**：2.2 Feedback on behaviour，12.5 Adding objects to the environment（环境提示），5.1 Information about health consequences
- **Act 阶段**：1.2 Problem solving（⚠️ 需强化），1.5 Review behavior goal(s)，8.7 Graded tasks（分级任务）

**当前最大缺口**

1. **应对计划（Coping Planning）机制**：缺乏"if-then 预案"生成机制
2. **反馈层级系统**：缺乏清晰的反馈层级和触发逻辑（建议 L1 确认式 → L2 评估式 → L3 趋势式 → L4 模式式 → L5 身份式）
3. **目标回顾（Review）机制**：缺乏明确的回顾触发条件和对话流程
4. **身份 BCT 强化**：话术从行为层 → 状态层 → 身份层

**对 Voliti 的启示**

✅ S-PDCA 框架与 BCT 自我调节组合高度契合（这是减重干预中证据最强的路径）
✅ "State Before Strategy"是理论支持的正确选择
✅ Coach Agent 的真正价值在于实现"不可能的 BCT 组合"（即时反馈 + 模式识别 + 预测性干预 + 长期追踪）
⚠️ 当前最大缺口是"应对计划"和"结构化回顾"（这两个 BCT 是从"知道"到"做到"的关键桥梁）

---

### 四、体验式教练干预方法

**核心定位**：Voliti 的核心是通过教练恰当的干预，帮助用户更好地管理行为以达到减脂目标。生成式UI（如动态图像）是表达形式、工具或手段，**重要的不是"视觉"本身，而是干预出现的时机、承载的内容、向用户传递的情感和意向**。

Coach 通过体验式干预方法，在关键时刻向用户传递特定的信息与情感，强化身份认同、激活应对策略、识别行为模式、重构认知框架。这些干预方法可以通过对话、生成式UI或其他形式表达，形式服务于目的。

#### 4.1 未来自我对话（Future Self Continuity）

**理论基础：Future Self-Continuity**

- **时间折扣问题**：人们将未来的自己视为"陌生人"，导致对未来结果的低估
- **Hershfield 的 fMRI 研究**：思考"10 年后的自己"时，大脑激活模式接近思考"陌生人"
- **MIT "Future You" 项目（2024）**：用户与 AI 模拟的 60 岁未来自我进行对话，短暂互动显著降低焦虑水平、提升未来自我连续性

**干预的核心要素**（基于 Identity-Based Motivation 理论）：

1. **时机**：什么时候介入
   - 目标设定阶段（S-PDCA 的 Plan）：帮助用户将抽象目标转化为具象身份
   - 动机低落时：提供"身份提醒"，重新连接长期意图
   - 长期复盘时（Act 阶段）：回顾"身份演化轨迹"

2. **内容**：传递什么信息
   - **身份一致性优先于外观变化**：不是"瘦了的自己"，而是"能管理选择的自己"
   - **价值锚定**：反映用户的核心价值观（自主性、活力、掌控感）
   - **连续性强化**：包含用户可识别的个人元素，强调"这不是不同的人，是你进一步沿着路径"

3. **情感与意向**：传递什么情绪
   - 希望感（而非焦虑）
   - 掌控感（而非压力）
   - 连续性（而非割裂）

**伦理边界**：
- ❌ 禁止：理想化身材图像、身体对比图、任何聚焦于体重/体型的内容
- ✅ 聚焦：行为能力、情境掌控、价值观具象化

**表达形式**：对话叙事为主，必要时辅以生成式UI（如动态图像）增强具象感

#### 4.2 场景预演（Scenario Rehearsal）

**理论基础**

1. **Mental Contrasting with Implementation Intentions (MCII / WOOP)**
   - 由 Gabriele Oettingen 开发（NYU & University of Hamburg）
   - 核心机制：对比理想与障碍，激活问题解决模式
   - 效果：目标达成效应量 Cohen's d ≈ 0.35

2. **Episodic Future Thinking (EFT)**
   - Meta-analysis 结果（2024）：减少时间折扣（d ≈ 0.50），改善食物选择（d ≈ 0.30）
   - 关键设计因素：时间视野匹配

3. **Functional Imagery Training (FIT)**
   - 减重效果是单纯动机性访谈（MI）的 **5 倍**
   - 关键：教会用户自主激发心理预演，而非依赖治疗师

**干预的核心要素**：

1. **时机**：什么时候介入
   - 识别到高风险模式后（Check 阶段）：系统发现用户在特定情境下反复偏离
   - 用户主动请求时："明天有聚餐，我担心控制不住"
   - 预防性干预：在高风险事件前（如周末、假期）主动提供

2. **内容**：传递什么信息
   - **情境线索**：环境细节（餐桌、办公室、夜晚），激活情境记忆
   - **应对行为**：具体的选择动作（如选择蔬菜、倒水、深呼吸）
   - **挑战呈现**：不仅展示成功结果，也呈现挑战本身（"甜点菜单经过"）
   - **if-then 链接**：建立触发条件与应对反应的心理链接

3. **情感与意向**：传递什么情绪
   - 平静（而非焦虑）
   - 掌控感（而非挣扎）
   - 准备就绪（而非恐惧）

**表达形式**：对话引导为主（"想象一下...""如果...你会...？"），必要时辅以生成式UI提供视觉锚定

#### 4.3 隐喻协作（Metaphor Collaboration）

**理论基础：概念隐喻理论（Lakoff & Johnson）**

- 隐喻不仅存在于语言中，而是**思维的基本结构**
- 隐喻不仅塑造我们如何**谈论**某事，更塑造我们如何**思考和行动**
- 用户自创隐喻是其**内在身份模型的外显**

**常见减脂隐喻及其认知框架**：

| 用户隐喻 | 源域 | 隐含认知框架 | 行为影响 |
|---------|-----|------------|---------|
| "减脂是马拉松" | 长跑 | 耐力、配速、长期主义 | 降低急躁、接受波动 |
| "走钢丝" | 平衡术 | 危险、精确、随时失败 | 增加焦虑、二元思维 |
| "对抗食欲" | 战争 | 敌我对立、意志力消耗 | 反弹、自我批评 |
| "在路上" | 旅程 | 方向、过程、连续性 | 强化行动、接受偏离 |
| "调频" | 收音机 | 可调节、非全或无 | 降低羞耻、增强掌控感 |

**干预的核心要素**：

1. **时机**：什么时候介入
   - 用户使用隐喻语言时（"我现在像被困在雾中"）
   - 状态调频时（State 阶段）：用户表达困境或情绪
   - 模式识别后（Check 阶段）：帮助用户理解模式

2. **内容**：传递什么信息
   - **识别用户隐喻**（Coach 倾听）：用户说"我感觉自己在逆流而上"
   - **镜射并扩展**（Coach 精化）："逆流很真实。你有没有发现某些时刻水流缓一些？"
   - **协作精化隐喻**：将限制性隐喻转化为赋能性隐喻（增加资源，而非改变源域）

3. **情感与意向**：传递什么情绪
   - 被理解（而非被纠正）
   - 赋能感（而非无力感）
   - 可能性（而非困境）

**关键原则**：
- 永远**保留用户的源域**（river, not replace with "journey"）
- **增加而非替换**（add stones, not calm the water）
- **征求反馈**："这像你描述的那样吗？" → 迭代编辑

**表达形式**：对话协作为主，必要时辅以生成式UI将精化后的隐喻具象化，增强记忆与共鸣

#### 4.4 认知重构（Cognitive Reframing）

**理论基础：认知行为疗法（CBT）核心机制**

- 改变对事件的**解释**，而非事件本身
- 经典公式：Event → Interpretation → Emotion → Behavior
- 认知重构介入点在 Interpretation，通过**换框**（reframing）改变后续情绪与行为

**多模态表达增强认知重构的神经机制**

1. **Dual-Coding Theory（Paivio, 1971）**
   - 人脑通过两个独立通道处理信息：语言系统 + 非语言系统
   - 双重编码提供两条检索路径，增强记忆
   - 多模态表达（语言 + 意象）比纯语言更有效

2. **fMRI 证据**
   - 心理意象激活的脑区与真实感知**高度重叠**
   - 通过意象诱导的情绪反应**强于语言诱导**
   - 认知重构时：前额叶皮层（PFC）**自上而下控制**增强，杏仁核反应降低

**干预的核心要素**：

1. **时机**：什么时候介入
   - 用户表达认知扭曲（如全或无思维："我又破戒了"）
   - Check 阶段复盘时：帮助用户重新框架行为偏离
   - 用户陷入自责情绪：提供替代性解释

2. **内容**：传递什么信息
   - **框架对比**：失败框架 vs. 信息框架
     - "我又失控了" → "疲劳状态下的安慰性选择"
     - "努力白费了" → "水分/生理周期的正常变化"
     - "破戒了" → "社交场景的挑战性决策点"
   - **比例感呈现**：一周中的一天，不是全部
   - **过程强调**："一周是由多个日子组成的，一个选择是信息，不是抹除"

3. **情感与意向**：传递什么情绪
   - 同理（而非评判）
   - 信息感（而非失败感）
   - 可通过性（"门槛"而非"分离"，暗示可以跨过去）

**表达形式**：对话重构为主（Coach 提供替代性解释），必要时辅以生成式UI（如对比图）增强记忆

#### 4.5 干预时机与伦理边界

**干预时机设计（基于 S-PDCA）**

| PDCA 阶段 | 干预方法 | 触发条件 | 频率 |
|----------|---------|---------|------|
| **State** | 隐喻协作（状态反映） | 压力/疲劳检测、用户使用隐喻语言 | 响应式 |
| **Plan** | 未来自我对话、场景预演 | 每周计划会话、挑战情境预期 | 每周 1-2 次 |
| **Do** | （最小化） | 用户主动寻求 | 罕见 |
| **Check** | 模式识别、隐喻协作 | 每周复盘 | 每周 1 次 |
| **Act** | 场景预演、认知重构 | 策略调整、用户表达认知扭曲 | 每 2-4 周 |

**频率与习惯化平衡**

- 每 Chapter（21 天）3-5 次体验式干预 ✅ 符合学术建议（避免脱敏）
- 同一类型干预（如未来自我对话）在一个 Chapter 内最多 1 次
- 两次干预至少间隔 3-5 天
- **关键**：变化性、个性化、基于最新上下文生成，而非模板化

**伦理边界（关键）**

1. **内容禁区**：理想化身材、身体对比、任何聚焦于体重/体型的内容
2. **内容聚焦**：行为能力、情境掌控、价值观具象化
3. **透明度与用户控制**：
   - 明确告知：生成式内容是"可能性探索"而非预测
   - 用户确认：干预前询问意愿
   - 退出机制：用户可随时关闭体验式干预功能
   - 反馈机制：每次干预后收集反馈（有帮助 / 不舒服 / 跳过）

#### 4.6 与 BCT 的整合

体验式教练干预对应的 BCT 编号：
- **15.1 Mental rehearsal of successful performance**（场景预演）
- **15.2 Focus on past success**（未来自我连续性）
- **16.3 Vicarious consequences**（体验未来结果）
- **1.4 Action planning + 体验式干预**（场景预演 + 实施意图）
- **13.5 Identity associated with changed behaviour + 体验式干预**（身份演化）

**学术证据支持的核心发现**：
1. **未来自我连续性是行为改变的关键机制**：MIT Future You 项目验证了 AI 模拟未来自我对话的有效性（显著降低焦虑、提升未来自我连续性）
2. **心理预演训练比表达形式本身更重要**：FIT 研究显示效果是 MI 的 5 倍，关键是教会用户自主激发心理预演
3. **Process simulation > Outcome simulation**：场景预演应包含挑战呈现，而非仅展示成功结果
4. **用户自创隐喻 + 协作精化最有效**：保留用户源域，增加而非替换
5. **多模态表达增强认知重构**：Dual-coding + fMRI 证据支持，语言 + 意象比纯语言更有效
6. **伦理优先**：避免身体形象内容，聚焦行为、情境、身份

---

### 五、理论整合：四层行为改变系统

四层理论形成完整行为改变闭环：

```
Self-Monitoring（数据采集层）
  ↓ 提供原始数据
EMA（情境解析层）
  ↓ 识别触发模式
BCT（干预技术层）
  ↓ 选择干预技术
体验式教练干预（深化干预层）
  ↓ 深化干预效果（时机、内容、情感）
  ↓ 反馈到
Self-Monitoring（持续优化）
```

**整合原则**：
1. **Self-Monitoring 提供数据基础**：多维度记录（行为 + 时间 + 情境 + 情绪 + 生理状态）
2. **EMA 提供分析框架**：识别个体内变异性、时间动态性、情境依赖性
3. **BCT 提供干预工具包**：基于模式识别结果，选择和组合具体技术
4. **体验式教练干预深化干预效果**：在恰当的时机、传递特定的内容、传递目标情感（未来自我对话、场景预演、隐喻协作、认知重构）

**Voliti 的理论优势**

1. ✅ **S-PDCA 方法论与理论高度契合**：State（EMA 状态采集）→ Plan（BCT 目标设定）→ Do（Self-Monitoring）→ Check（EMA 模式识别）→ Act（BCT 干预）
2. ✅ **State-First 逻辑有理论支持**：高压力/疲劳状态下的目标设定和计划无效，优先恢复认知资源
3. ✅ **多维事件记录架构正确**：时间戳 + 原始证据 + 情境标签 + 情绪状态 + 置信度
4. ✅ **区间估算减少负担**：符合"一致性 > 频率"原则
5. ✅ **Coach 单点接触 + 后台分析**：正确的人机协作模式
6. ✅ **非评判式语言 + 身份强化**：对应 BCT Group 13（Identity），长期维持的关键机制

**核心实施优先级**

**立即实施（Phase 1）**：
1. 完善反馈层级（L1-L5）
2. 添加应对计划生成（if-then 预案）
3. 结构化目标回顾（周度触发）
4. 一致性支持机制（连续天数追踪）
5. 场景预演干预机制 + 伦理保障框架

**3 个月内（Phase 2）**：
6. Self-Monitoring 目的教育
7. Coping strategies 库
8. 模式识别呈现
9. JITAI 预测性干预
10. 未来自我对话（身份锚定）

**6-12 个月（Phase 3）**：
11. 身份演化追踪
12. 复发预防机制
13. 依从性优化策略
14. 隐喻协作机制

---

## 核心Takeaway

1. **Self-Monitoring 告诉我们**：记录本身即干预（Reactivity），一致性 > 频率，多维度 > 单维度，教育用户理解目的：识别模式，不是监督

2. **EMA 告诉我们**：行为波动源于当下情境与生理状态（不是意志力），即时记录 > 回忆记录，个体内变异性 > 群体平均，数据 → 洞察 → JITAI 的闭环

3. **BCT 告诉我们**：单一技术无效，自我调节技术包是唯一一致预测因子，State Before Strategy 有理论支持，应对计划和结构化回顾是从"知道"到"做到"的关键桥梁，身份演化是长期维持的核心机制

4. **体验式教练干预告诉我们**：未来自我连续性是行为改变的关键机制，心理预演训练比表达形式本身更重要，Process simulation > Outcome simulation，用户自创隐喻 + 协作精化最有效，**核心在于干预的时机、内容与情感传递**，伦理优先：避免身体形象内容，聚焦行为、情境、身份

5. **Voliti 的独特价值**：S-PDCA 框架与四层理论高度契合，Coach Agent 实现了传统干预"不可能的 BCT 组合"（即时反馈 + 模式识别 + 预测性干预 + 长期追踪 + 体验式教练干预），通过在恰当的时机传递特定内容与情感，深化行为改变效果，"阻抗即信息"的哲学与 EMA/Self-Monitoring 研究一致，身份演化定位是学术上最前沿的长期维持机制

6. **当前最高优先级**：完善反馈层级（L1-L5）、添加应对计划生成（if-then 预案）、结构化目标回顾（周度触发）、一致性支持机制（连续天数追踪）、体验式教练干预机制 + 伦理保障框架——这五项是理论到实践的关键缺口

---

## 参考资料

### Self-Monitoring 理论

1. Kanfer, F. H., & Karoly, P. (1972). Self-control: A behavioristic excursion into the lion's den. *Behavior Therapy*, 3(3), 398-416.
2. Carver, C. S., & Scheier, M. F. (1982). Control theory: A useful conceptual framework for personality–social, clinical, and health psychology. *Psychological Bulletin*, 92(1), 111-135.
3. Bandura, A. (1991). Social cognitive theory of self-regulation. *Organizational Behavior and Human Decision Processes*, 50(2), 248-287.
4. Burke, L. E., Wang, J., & Sevick, M. A. (2011). Self-monitoring in weight loss: A systematic review of the literature. *Journal of the American Dietetic Association*, 111(1), 92-102.

### EMA 理论

5. Shiffman, S., Stone, A. A., & Hufford, M. R. (2008). Ecological momentary assessment. *Annual Review of Clinical Psychology*, 4, 1-32.
6. Stone, A. A., & Shiffman, S. (1994). Ecological momentary assessment (EMA) in behavioral medicine. *Annals of Behavioral Medicine*, 16(3), 199-202.
7. Dunton, G. F. (2017). Ecological momentary assessment in physical activity research. *Exercise and Sport Sciences Reviews*, 45(1), 48-54.
8. Nahum-Shani, I., et al. (2018). Just-in-Time Adaptive Interventions (JITAIs) in Mobile Health: Key Components and Design Principles for Ongoing Health Behavior Support. *Annals of Behavioral Medicine*, 52(6), 446-462.

### BCT 理论

9. Michie, S., et al. (2013). The Behavior Change Technique Taxonomy (v1) of 93 Hierarchically Clustered Techniques: Building an International Consensus for the Reporting of Behavior Change Interventions. *Annals of Behavioral Medicine*, 46(1), 81-95.
   - 链接：https://academic.oup.com/abm/article/46/1/81/4563254

10. Michie, S., Atkins, L., & West, R. (2014). *The Behaviour Change Wheel: A Guide to Designing Interventions*. Silverback Publishing.

11. Connell, L. E., et al. (2023). The Behavior Change Technique Ontology: Transforming the Behavior Change Technique Taxonomy v1. *Wellcome Open Research*, 4:173.
    - 链接：https://pmc.ncbi.nlm.nih.gov/articles/PMC10427801/

12. Teixeira, P. J., et al. (2020). A Classification of Motivation and Behavior Change Techniques Used in Self-Determination Theory-Based Interventions in Health Contexts. *Motivation Science*, 6(4), 438-455.

### 体验式教练干预理论

13. Hershfield, H. E., et al. (2011). Increasing Saving Behavior Through Age-Progressed Renderings of the Future Self. *Journal of Marketing Research*, 48(SPL), S23-S37.

14. Pataranutaporn, P., et al. (2024). Future You: A Conversation with an AI-Generated Future Self Reduces Anxiety, Negative Emotions, and Increases Future Self-Continuity. MIT Media Lab.

15. Oettingen, G. (2012). Future thought and behaviour change. *European Review of Social Psychology*, 23(1), 1-63.

16. Stein, J. S., et al. (2024). A meta-analysis of episodic future thinking effects in delay discounting and health behaviors. *Psychonomic Bulletin & Review*, 31, 2019-2037.

17. Solbrig, L., et al. (2019). Functional imagery training versus motivational interviewing for weight loss: A randomised controlled trial of brief individual interventions for overweight and obesity. *International Journal of Obesity*, 43, 883-894.

18. Lakoff, G., & Johnson, M. (1980). *Metaphors We Live By*. University of Chicago Press.

19. Paivio, A. (1971). *Imagery and Verbal Processes*. Holt, Rinehart and Winston.

20. Beck, A. T. (1979). *Cognitive Therapy and the Emotional Disorders*. Penguin Books.

### 综合与应用

21. Webb, T. L., Joseph, J., Yardley, L., & Michie, S. (2010). Using the Internet to Promote Health Behavior Change: A Systematic Review and Meta-analysis of the Impact of Theoretical Basis, Use of Behavior Change Techniques, and Mode of Delivery on Efficacy. *Journal of Medical Internet Research*, 12(1), e4.

22. Schoeppe, S., et al. (2016). Efficacy of interventions that use apps to improve diet, physical activity and sedentary behaviour: A systematic review. *International Journal of Behavioral Nutrition and Physical Activity*, 13, 127.
