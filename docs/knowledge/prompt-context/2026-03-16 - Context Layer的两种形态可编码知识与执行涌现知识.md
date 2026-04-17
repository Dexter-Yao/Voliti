---
type: insight
author: 综合（Evan Armstrong, David Autor, Michael Polanyi, Celonis, a16z 等）
published: N/A
topics:
  - context engineering
  - tacit knowledge
  - organizational knowledge
  - AI agents
  - competitive moat
source_basis:
  - "[[2026-04-10 - OpenAI长程Agent的Skills、Shell、Compaction协同]]"
  - "[[2026-04-09 - Harness把执行轨迹变成智能飞轮]]"
  - "[[2026-04-04 - MetaHarness把Harness优化变成代码搜索]]"
  - "[[2026-03-10 - 以 Skills 为核心的领域 AI 产品形态]]"
  - "[[2026-03-09 - Taylor到Autor数字生产工厂化的权力迁移理论]]"
  - "[[2026-01-14 - Google UCP 与 AI 时代商品化策略及广告实验]]"
  - "[[2026-03-16 - Christensen利润守恒定律的机制案例与局限]]"
  - "[[2026-03-07 - AI 时代设计系统的上下文基础设施角色]]"
  - "[[2025-10-06 - 代理式转向的核心是人的角色重构与暗知识激活]]"
  - "[[2026-03-16 - Agent时代利润先集中于模型与Harness耦合层]]"
  - "[[2026-03-18 - AI个性化价值来自能推动行动的上下文]]"
  - "[[2026-03-07 - AI Agent时代按成果收费的全景研究]]"
  - "[[2026-04-01 - 打造 AI Agent 员工的操作方法论]]"
created: 2026-03-16
updated: 2026-04-10
status: canonical
canonical: true
review_after: 2026-07-04
---

# Context Layer的两种形态可编码知识与执行涌现知识

## 一句话简介

组织 context 存在两种本质不同的形态——可编码的显性知识（流程规则、权限矩阵、术语定义）与从执行中涌现的隐性知识（经验判断、例外处理模式、非正式流程）；前者可以文档化但不构成护城河，后者才是真正的价值所在但天然抵抗文档化——只能通过 trace 提取、执行回放与 Eval 校准逐步捕获。

## Takeaway

1. **"文档永远落后于实践"不是执行力问题，而是知识的结构性属性**：Polanyi 的悖论（"we can know more than we can tell"）和 Autor 的任务经济学共同指出，需要判断力、灵活性和情境适配的知识天然抵抗编码化。这设定了 context layer 能捕获什么的理论上限。
2. **产品问题不是"context 能否文档化"，而是"能否从执行 trace 中被动提取"**：Process mining（如 Celonis）从系统事件日志中提取"组织实际如何运作"的实证记录；Agent memory 系统（如 Mem0/ACE 框架）从 agent 执行 trace 中自动学习并更新 context。两者代表了当前最有前景的技术路径——它们绕开了"让人类写文档"这个历史性失败模式。
3. **当 Agent 从 System of Record 进入 System of Action，trace 的价值会急剧上升**：谁能捕获 GUI、文档、语音、终端与审批过程中的执行轨迹，谁就更有机会把隐性知识沉淀成私有优势。
4. **Eval 机制是 trace 学习的质量控制层**：没有 Eval，从 trace 中学习会积累噪声而非信号。这对应 Skills 五层系统中第四层（Eval 与校准机制）的角色——它验证从执行中涌现的 context 是否准确，是整个闭环中最隐蔽但最关键的环节。

## 问题描述

这篇笔记试图回答的问题不是"企业有没有文档"，而是"当 Agent 真正开始替人做事时，哪些组织知识会自然沉淀成护城河，哪些不会"。OpenClaw、Computer Use Agent、Process Mining 和 Voice Agent 之所以值得放在同一张图里，不是因为它们技术路线相同，而是因为它们都在把原本散落在执行过程中的隐性知识转化为可积累的 trace。

---

## 两种 Context 的本质区别

Evan Armstrong 在分析 SaaS 市值蒸发（"SaaSacre"）时提出了 context layer 的概念：当代码和数据库被商品化后，价值迁移到编码了组织制度性知识的中间层（Armstrong, "Context is King", 2026）。但他在论述中混合了两种本质不同的东西：

**可编码的 context（Codifiable Context）** 包括：流程规则、权限矩阵、术语定义、SOP、报告模板、KPI 定义。这类知识可以写成文档或注入为 prompt，也正在被 Glean、Atlan、Stack Internal 等产品结构化。但它不构成持久护城河——正如 Skill 文本没有编译屏障，任何有访问权限的人都可以复制。

**从执行中涌现的 context（Emergent Context）** 包括：Armstrong 举的例子——"$500K 以上的交易在法务审核后会停滞"、"最好的 AE 对老客户跳过 discovery call"。这类知识不存在于任何文档中，它从数千次工作流执行中涌现，体现为模式识别、例外处理直觉和非正式流程。

> A markdown file can describe your sales process. It can't encode that deals over $500K stall when legal reviews before procurement, or that your best AE skips the discovery call for inbound leads from existing customers. That kind of process knowledge doesn't live in a document. It emerges from thousands of workflows executed over time. (Armstrong, 2026)

这一区分的产品含义是深远的：如果你在构建 context layer 产品，可编码的部分是入场筹码（table stakes），而从执行中涌现的部分才是可积累的竞争优势。

## 文档为什么永远落后于实践

"文档落后"不是一个可以通过更好的工具或更严格的流程来解决的执行力问题。它反映了知识本身的结构性属性。

**Polanyi 的悖论（Polanyi's Paradox）。** Michael Polanyi 在 1966 年提出："we can know more than we can tell"——所有显性知识都建立在一个无法完全表达的隐性基底（tacit substrate）之上。这不是关于个人技能的观察，而是关于知识结构本身的论断。David Autor 在 2014 年 NBER 论文中将此形式化为经济框架：可编码的例行任务恰好是可自动化的，而需要判断力、灵活性和常识的非例行任务天然抵抗编码化（Autor, NBER 2014）。

**知识管理的历史性失败。** 企业知识管理有大量失败记录：McKinsey 数据显示知识工作者 20% 的工作时间用于搜索信息；Asana 数据显示 60% 的工作时间是"work about work"——协调开销而非价值生产。Stack Overflow 在 2019 年的分析中得出结论：wiki、文档和聊天工具都无法解决知识管理问题，因为它们把知识当成**占有问题**（possession problem）而非**实践问题**（practice problem）（Stack Overflow, 2019）。

*Organization Science* 的研究更为根本：组织知识存在于实践中，而非文档中。当前的知识管理建立在"占有认识论"（epistemology of possession）之上，将知识视为人们"拥有"的东西。但在实际组织运作中，关键知识通过做事（knowing in practice）而非记录来传递和维持（Orlikowski, *Organization Science*, 2001）。

**Nonaka & Takeuchi 的 SECI 模型及其局限。** Nonaka 和 Takeuchi 的 SECI 模型（Socialization → Externalization → Combination → Internalization）是企业知识管理的主要理论框架。其中 Externalization——将隐性知识转化为显性知识——正是 context layer 产品试图自动化的环节。但学术文献一致认为 Externalization 是四种转化中最困难的，它需要对话、隐喻和共享经验来"结晶化"知识，无法被简单自动化。

## 中间地带：从"记录"转向"观察"

上述分析并不意味着涌现型 context 永远无法被软件捕获。当前最有前景的技术路径是**停止让人类写文档，转而从执行 trace 中被动提取**。

这里有一个经常被忽略的前提变化：上一代企业软件的中心是 `System of Record`，主要任务是记录现实；而 Long-Horizon Agent 的中心是 `System of Action`，主要任务是执行现实。当前者转向后者，context 的主要来源也随之改变。真正重要的知识，不再只存在于 CRM 字段、SOP 文档或知识库条目里，而开始存在于：

- Agent 如何拆解一个模糊目标；
- 遇到异常时先查哪份文档、后点哪个按钮；
- 哪种审批路径在特定组织结构下更顺；
- 哪些语气、延迟与转人工时机会提升完成率；
- 哪些 GUI 操作序列能穿透没有 API 的遗留系统。

也因此，context layer 的竞争不再只是"谁接了更多文档库"，而是"谁更靠近行动现场"。

### Process Mining：观察而非询问

Celonis 的方法代表了这一方向：不问专家"你的流程是什么"（他们会回答得不完整、不准确且滞后），而是从 ERP/CRM 系统的事件日志中直接提取流程知识——每笔交易、审批、异常和变通方案都留下 trace。结果是组织**实际如何运作**的实证记录，而非设计文档。

Celonis 2024 年推出 AgentC，将运行时流程智能直接连接到 Salesforce、SAP、ServiceNow 中的 AI agent。SAP Signavio 的"Digital Twin of an Organization"（组织数字孪生）概念以类似思路桥接设计流程与实际行为之间的执行差距。

局限在于：Process mining 只对系统中介的结构化工作有效。发生在对话、判断和非正式关系中的知识工作不产生结构化事件日志。它能捕获组织行为的骨骼，但不能捕获软组织。

### Agent Memory：从执行 trace 中学习

2025 年 12 月的 arxiv 论文"Memory in the Age of AI Agents"综述了一个快速增长的研究领域：agent 从自身执行 trace 中学习，而非从静态文档中。ACE（Agentic Context Engineering）框架使用 Generator、Reflector、Curator 三个 agent 的循环，自动从执行 trace 中提取学习并更新 context playbook——据报告在 agent 基准测试中提升 +10.6%（arxiv, 2512.13564）。

Mem0 以图结构的持久化记忆为基础，实现跨会话的 context 积累。这条路径的有效性取决于一个关键前提：执行可观察的行为是否与真正重要的隐性知识相关联。对例行的、定义良好的任务：是的；对需要判断力的新颖情境：尚不确定。

[[2026-04-04 - MetaHarness把Harness优化变成代码搜索]] 则展示了另一条相邻但不同的路径：trace 的价值不一定体现为“写回持久记忆”，也可以体现为“反过来优化产生 context 的 harness 代码本身”。这说明 execution trace 不只是 memory 系统的燃料，也是 harness engineering 的搜索信号；谁能把 trace 组织成可检索、可比较、可验证的外部经验库，谁就更接近把 context layer 变成真正的工程资产。

[[2026-04-09 - Harness把执行轨迹变成智能飞轮]] 从工程范式演进的角度补上了同一判断的另一面：当 harness 被拆成信息层、执行层、反馈层之后，trace 的地位不再只是“事后可观察”，而是贯穿三层闭环的共享原料。它既决定模型当下看见什么，也决定系统之后学到什么，因此可以同时视为 context layer 的输入、eval 回路的证据和后训练数据飞轮的来源。

### Computer Use：把原本不可结构化的操作变成可学习的 trace

OpenClaw 与 Simular 这类 Computer Use 路线的重要性，在于它们把过去最难沉淀的一类执行过程暴露出来了。传统企业里大量关键工作发生在"看屏幕、切标签、找按钮、复制字段、上传 PDF、等待审批结果"的 GUI 世界里。这里往往没有 API，也没有结构化事件日志，因此很难进入旧式软件的数据模型。

一旦 Agent 开始直接操作浏览器、桌面应用、终端和聊天工具，这些原本处于黑箱中的执行行为就变成了可观察、可重放、可评估的轨迹。对 context layer 而言，这意味着新的原材料来源：

- 鼠标与键盘序列；
- 视觉定位与界面变更后的补救策略；
- 跨系统切换顺序；
- 人类接管前后的差异；
- 同一任务在不同环境下的失败模式。

这类 trace 与传统流程文档的区别在于，它记录的不是"理论上该怎么做"，而是"在脏环境里实际上怎么做成"。这正是组织隐性知识最有价值、也最难复制的部分。

### Voice Trace：情绪与合规也是 context

在语音场景里，context 不再只是知识与流程，还包括节奏、情绪和合规边界。理赔电话、医疗随访、催收沟通、物流确认这类场景的执行质量，不只取决于内容理解，也取决于何时停顿、何时确认、何时转人工、何时放缓语速。

这意味着 Voice Agent 生成的 trace 也属于 context layer 的一部分。只要产品能够把这些语音交互中的模式提取出来，并与结果质量关联，它积累的就不只是"对话记录"，而是"什么样的表达方式在特定人群和特定风险级别下更有效"的执行知识。

## 与 Skills 五层系统的对应关系

这一区分与 Skills 护城河的五层系统（详见 [[2026-03-10 - 以 Skills 为核心的领域 AI 产品形态]]）有精确的映射关系：

| 五层系统 | Context 类型 | 可复制性 |
|---------|-------------|---------|
| 第一层：领域知识定义 | 可编码 | 高——prompt 没有编译屏障 |
| 第二层：工作流嵌入 | 可编码 + 部分涌现 | 中——嵌入深度决定替换成本 |
| 第三层：专有上下文积累 | **涌现** | 低——需时间沉淀，新竞争者无法复制 |
| 第四层：Eval 与校准机制 | **涌现** | 低——"什么叫准确"本身是领域专业性 |
| 第五层：反馈闭环 | **涌现** | 低——工程化的错误-修正-预防机制 |

**第三到第五层构成了涌现型 context 的完整捕获链**：第三层积累原始 context，第四层验证其准确性（Eval 是 trace 学习的质量控制层——没有它，积累的将是噪声而非信号），第五层将每次失误转化为系统改进。

这也回应了 Armstrong 文中的一个重要观察：context layer 是**复合累积资产（compounding asset）**——每次 agent 执行工作流，产生的 trace 反馈回 context layer，使下一次执行更准确。但这个复利效应只在第四层（Eval）和第五层（反馈闭环）正常运作时才成立。没有这两层，context 积累会在时间中退化，复利变成复亏。

## Context Layer 的实际产品形态

当前市场中 context layer 产品按 context 来源可分为两大类：

**文档驱动型**（主要处理可编码 context）：
- **Glean**：Enterprise Graph 建模人、内容、工作流、应用之间的关系。第三代架构（2025 年 9 月发布）结合公司级知识图谱与个人图谱，被 Gartner 列入生成式 AI 知识管理新兴领导者。
- **Atlan**：数据治理 control plane，从 dbt、Looker、Power BI 的语义定义中自动构建 context，区分 semantic layer（标准化 BI 指标）与 context layer（编码组织决策智能）。
- **Stack Internal**：通过 MCP Server 将人类审核过的组织知识连接到 AI 开发工具（GitHub Copilot、ChatGPT、Cursor），混合自动化提取与人工审核。

**执行驱动型**（尝试捕获涌现型 context）：
- **Celonis**：Process mining 从系统事件日志提取"组织数字孪生"，AgentC 将运行时流程智能连接到 AI agent。
- **Mem0**：图结构持久化 agent 记忆，跨会话积累执行 context。
- **ACE 框架**：三 agent 循环（Generator/Reflector/Curator）从执行 trace 自动提取学习并更新 context playbook。
- **Computer Use / GUI Agent**：通过浏览器、桌面和终端操作暴露原本不存在于 API 日志中的执行轨迹，使 context layer 首次覆盖遗留系统与灰色流程。
- **Voice Agent runtime**：通过实时语音交互捕获情绪管理、打断、澄清与合规 fallback 的执行模式，使"如何说"也成为可积累的组织上下文。

Armstrong 的论点在宏观层面成立：context layer 确实可以从协调开销（而非 IT 预算）中获取价值。但在微观产品层面，决定性的问题是：你的产品在五层系统的哪一层建立积累？停留在第一、二层的产品（文档驱动型），面临的竞争压力与传统知识管理软件无异。只有触及第三到第五层（执行驱动型）的产品，才能建立 Armstrong 所说的复合累积效应。

## 结构性约束：涌现型 Context 的天花板

即便是最先进的 trace 提取方法，也存在理论上限。Polanyi 悖论与 Autor 框架共同暗示：**可编码化的组织知识存在天花板**。隐性的、依赖判断力的、以人际关系为中介的知识，恰好是高风险决策中最重要的知识——也是最抵抗编码化的知识。

MIT 2025 年"GenAI Divide"报告的数据提供了实证参照：95% 的企业 AI 部署没有产生可衡量的商业价值（MIT, 2025）。失败模式恰好是 context layer 试图解决的问题——技术与业务工作流之间的错位。但这个失败率说明，即使有某种形式的 context 方案，大多数企业仍然失败了。

California Management Review 的分析进一步指出：AI agent 不是简单地替代层级协调，而是创造新的协调需求——数字遗产（员工离开时带不走的 agent 配置）、碎片化（部门间重复的 agent 系统）、平台依赖、组织熵（各自局部优化的 agent 产生全局混乱）（CMR, 2025）。

这意味着 context layer 的真正价值定位可能不是"替代人类协调"，而是"增强人类协调中最机械化的部分，同时将人的注意力释放到判断密集型的协调任务上"。

---

## 参考链接

- [Context is King: Notes on the SaaSacre — The Leverage](https://every.to)
  - 作者：Evan Armstrong
  - 发布日期：2026-02-12
- [Polanyi's Paradox and the Shape of Employment Growth — NBER](https://www.nber.org/papers/w20485)
  - 作者：David Autor
  - 发布日期：2014
- [Why Docs, Wikis, and Chat Clients Are Not Knowledge Management Solutions — Stack Overflow](https://stackoverflow.blog/2019/09/30/why-docs-wikis-and-chat-clients-are-not-knowledge-management-solutions/)
  - 作者：Stack Overflow
  - 发布日期：2019
- [Your Data Agents Need Context — a16z](https://a16z.com/your-data-agents-need-context/)
  - 作者：a16z
  - 发布日期：N/A
- [Glean Enterprise Graph](https://www.glean.com/product/enterprise-graph)
  - 作者：Glean
  - 发布日期：2025-09
- [Atlan Context Layer 101](https://atlan.com/know/ai-readiness/context-layer-101/)
  - 作者：Atlan
  - 发布日期：N/A
- [From Coase to AI Agents — California Management Review](https://cmr.berkeley.edu/2025/04/from-coase-to-ai-agents/)
  - 作者：California Management Review
  - 发布日期：2025
- [Memory in the Age of AI Agents — arxiv](https://arxiv.org/abs/2512.13564)
  - 作者：N/A
  - 发布日期：2025-12
- [OpenClaw 是一个信号｜2026 Long-Horizon Agent 投资地图](https://www.google.com/search?q=OpenClaw+%E6%98%AF%E4%B8%80%E4%B8%AA%E4%BF%A1%E5%8F%B7%EF%BD%9C2026+Long-Horizon+Agent+%E6%8A%95%E8%B5%84%E5%9C%B0%E5%9B%BE)
  - 作者：Haina
  - 发布日期：N/A
- [OpenClaw](https://openclaw.ai/)
  - 作者：OpenClaw
  - 发布日期：N/A
- [OpenClaw GitHub](https://github.com/clawdbot/clawdbot)
  - 作者：OpenClaw
  - 发布日期：N/A
- [Harness is the New Dataset：模型智能提升的下一个关键方向](https://mp.weixin.qq.com/s/9qI83Ne-Ac_R9y-yJ6SVnQ)
  - 作者：Celia
  - 发布日期：N/A

## 相关笔记

- [[2026-03-10 - 以 Skills 为核心的领域 AI 产品形态]]（五层系统是本笔记"可编码 vs 涌现"区分的产品层映射；两篇笔记构成"宏观理论 + 产品架构"的完整认知对）
- [[2026-03-09 - Taylor到Autor数字生产工厂化的权力迁移理论]]（Autor 的任务经济学为本笔记"涌现型 context 的天花板"提供了劳动经济学层面的理论基础）
- [[2026-01-14 - Google UCP 与 AI 时代商品化策略及广告实验]]（Armstrong 的 context layer 论点与 Spolsky 的"commoditize your complement"框架有直接对应——当应用层被商品化，context layer 是 Christensen 利润守恒预测的价值迁移目标）
- [[2026-03-16 - Christensen利润守恒定律的机制案例与局限]]（本笔记的理论基础——利润守恒定律解释了 context layer 价值为何在此刻涌现）
- [[2026-03-07 - AI 时代设计系统的上下文基础设施角色]]（设计系统作为 context layer 在特定领域的具体实现——验证了"可编码 context"作为入场筹码的论点）
- [[2025-10-06 - 代理式转向的核心是人的角色重构与暗知识激活]]（"暗知识激活"与本笔记的"涌现型 context"在概念上高度对应——前者从组织变革角度，后者从产品架构角度）
- [[2026-03-16 - Agent时代利润先集中于模型与Harness耦合层]]（解释为何 context layer 不是 2026 年利润的首个集中点，而更可能是模型与 Harness 层趋于标准化之后的下一跳）
- [[2026-03-18 - AI个性化价值来自能推动行动的上下文]]（将 context 的理论分类推进为经营层标准：什么样的 context 足以改变行为结果）
- [[2026-04-01 - 打造 AI Agent 员工的操作方法论]]（从岗位定义、共享存储与渐进授权角度说明执行 trace 如何真正进入生产工作流）
- [[2026-03-07 - AI Agent时代按成果收费的全景研究]]（解释为什么 trace 一旦能稳定提升结果交付质量，就会转化为可计费的商业优势）
- [[2026-04-04 - MetaHarness把Harness优化变成代码搜索]]（补充 trace 如何直接用于优化 Harness 与 context 暴露逻辑，而不只用于训练 memory）
- [[2026-04-09 - Harness把执行轨迹变成智能飞轮]]（把 execution trace 从研究语境推进到工程与产业语境，强调 Harness 本身就是持续生成数据集的系统）
- [[2026-04-10 - OpenAI长程Agent的Skills、Shell、Compaction协同]]（用具体 API 与运行时边界说明可编码流程、执行环境与上下文续航如何分层落地，是 context layer 进入执行系统的直接案例）
- [[2026-04-10 - 原始会话记录应附着运行时而非长期Store]]（把“trace 值得积累”进一步落到运行时边界：原始会话首先应附着于 session / thread history，而不是直接复制进长期 Store）
