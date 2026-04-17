---
type: map
topics:
  - agentic AI
  - systems design
  - context engineering
  - AI agents
created: 2026-03-01
updated: 2026-04-12
status: canonical
canonical: true
review_after: 2026-07-04
---

# Agentic AI 系统构建

## 导读

本 Map 回答一个核心问题：**如何把 Agent 从实验室原型变成生产可用的系统？**

这不是一个技术选型清单，而是一套工程认识论的积累——从「评估驱动」这个首要原则出发，向下分解为上下文管理、工具设计、前端交互三个工程子问题，向上收敛至厂商格局与协议标准。读这组笔记的核心收益：**建立生产级 Agentic 系统的完整心智模型**，而不是掌握某个具体工具的用法。

**知识脉络**：评估驱动开发（架构选择的判断标准）→ 上下文管理（长程任务的核心瓶颈）→ 工具设计（Agent 能力边界的决定因素）→ 前端范式（人机协作界面的新形态）→ 厂商格局（外部约束与机会窗口）

## 阅读起点

[[2026-02-08 - Agentic系统设计与评估驱动开发]] 是整张 Map 的骨架，建议先读完再展开其他节点。

---

## 系统设计与评估驱动

这一节确立「以评估为主流程」的工程范式——不先定架构，先定如何判断架构好坏。

- [[2026-02-08 - Agentic系统设计与评估驱动开发]] — 来源：Anthropic、OpenAI、Google 综合。梳理了生产级 Agentic 的六种架构模式（单 Agent、多 Agent 编排、并行 Agent 等），核心主张是「先写 Eval，再写 Agent」——没有评估标准就没有资格讨论架构选型。是本组必读首篇。
- [[2026-03-02 - AI采用格局的真实分裂从泛用到深用]] — 来源：Dexter。把“AI 辅助工程”从概念归并为两套模式：vibe coding 代表快速试错边界，agentic engineering 代表可持续生产边界，核心分歧在于是否建立审计与可靠性的治理闭环。
- [[2026-02-08 - Agent评估方法论与抗AI评估设计]] — 来源：Anthropic（Mikaela Grace, Jeremy Hadfield, Tristan Hume）。在上篇的基础上深入一个关键问题：当模型越来越强，评估体系本身会被「刷分」——如何设计具有抗 AI 性质的评估，防止指标失真？提出 Swiss Cheese Model 与 Eval Saturation 两个概念。

## 上下文管理

Agent 在长时间运行时的首要工程挑战不是推理能力，而是上下文窗口的耗尽与状态丢失。这一节处理这个问题。

- [[2026-02-08 - 长时间运行Agent的上下文管理与弹性设计]] — 来源：Anthropic。针对长程 Agent 任务（超出单个上下文窗口的工作流），提出 Agent Harness 模式：将上下文压缩、状态序列化、任务恢复机制作为系统基础设施而非临时 hack，是生产部署的必读参考。
- [[2026-02-08 - 提示工程范式演变与上下文工程实践]] — 来源：OpenAI、Anthropic、Google 综合。范式转变的历史叙述：从「寻找魔法词语」的提示工程，到「管理整个信息流」的上下文工程。核心洞察：在 Agent 系统中，提示只是上下文的一个子集，系统提示、历史记录、工具输出、外部知识都是上下文工程的管辖范围。
- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]] — 来源：Ryan Lopopolo（OpenAI）。OpenAI 以「0 行手写代码、100 万行 AI 生成代码」的内部实验，将 Harness Engineering 定义为 Agent 时代的核心工程范式：工程师不再写代码，而是设计「让 Agent 可靠生产的环境」——上下文管理从辅助能力变成了核心产出。
- [[2026-04-10 - OpenAI长程Agent的Skills、Shell、Compaction协同]] — 来源：Charlie Guo（OpenAI Developers）。把长程 Agent 的连续执行拆成三种基础原语：Skills 管流程，Shell 管执行，Compaction 管上下文续航；并补齐 `/mnt/data`、network allowlist 与 `domain_secrets` 等落地边界。
- [[2026-04-09 - AgentMiddleware把Harness定制抽象为生命周期拓展接口]] — 来源：Sydney Runkle（LangChain）。把 harness 定制从“重写执行循环”降为“通过生命周期拓展接口插入控制逻辑”，说明合规、摘要压缩、动态工具选择、重试与资源管理如何在框架层变成可组合控制平面，是 Anthropic 长程 harness 实践与 OpenAI harness engineering 之间的 LangChain 实现层补点。
- [[2026-04-04 - MetaHarness把Harness优化变成代码搜索]] — 来源：Yoonho Lee 等（arXiv）。将 Harness 从人工经验推进为可搜索的代码对象：通过让 coding agent 直接读取历史候选方案的源码、分数与 execution traces，自动迭代 context 管理程序，说明 harness engineering 开始从工程范式进入可自动化搜索阶段。
- [[2026-03-16 - Context Layer的两种形态可编码知识与执行涌现知识]] — 来源：综合（Armstrong, Autor, Polanyi 等）。从知识类型学角度重构上下文管理：可编码 context 是工程问题（文档注入），涌现型 context 是 trace 提取 + Eval 校准问题——后者对应 Process Mining 和 Agent Memory 两条技术路径。
- [[2026-03-18 - AI个性化价值来自能推动行动的上下文]] — 作者：Dexter。把上下文工程从技术视角翻译回产品决策：系统的关键任务不是接入更多数据，而是筛出能在有限上下文预算内改变行为结果的变量。
- [[2026-04-09 - Harness把执行轨迹变成智能飞轮]] — 来源：Celia（微信文章）。把 prompt、context 与 harness 三代工程范式串成一条演进线，并用“信息层—执行层—反馈层”重组 harness 的六个组件，适合作为中文语境下理解 harness engineering 的综述入口。
- [[2026-04-10 - 原始会话记录应附着运行时而非长期Store]] — 作者：Dexter。把 LangGraph 的 thread/checkpoint、Deep Agents 的 pluggable backend 与 Anthropic 的 session log 收敛为一条可执行判断：原始会话记录属于运行时可恢复层，长期 Store 只承载跨 thread 的语义记忆；适合作为 transcript archive、retrieval 与 memory layering 的架构锚点。
- [[2026-04-10 - OpenAI个性化记忆的状态分层与生命周期]] — 来源：Emre Okcular（OpenAI Cookbook）。把个性化记忆拆成状态建模、会话蒸馏、注入优先级、会后整理与分阶段评估五个环节，适合作为“如何让用户偏好在多轮系统中可控演化”的实现型参考。
- [[2026-04-12 - ClaudeCode泄露证明AI工程价值转向Harness]] — 来源：Ben Dickson（AlphaSignal）。以 Claude Code 源码泄露为切口，把自愈查询循环、KAIROS 记忆整理、结构化工具约束与 KV cache 稳定化放回同一判断：生产级 Agent 的真正壁垒不是模型本身，而是围绕上下文、状态与失败恢复构建的 harness。

## 工具设计与输出质量

工具是 Agent 能力的边界，工具设计的质量直接决定 Agent 在实际任务中的上限。

- [[2026-02-08 - AI Agent工具设计的上下文令牌经济学]] — 来源：Anthropic、OpenAI 综合。将工具设计视为核心竞争力而非辅助功能：工具的粒度、命名、返回值格式都直接影响 Agent 对上下文的消耗效率。提出「工具是 Agent 的感知器官」的设计哲学。
- [[2026-02-14 - LLM输出一致性与召回率最大化]] — 作者：Dexter，基于并行研究 Agent 成果整合。将「确定性」作为伪命题放弃，转而追求「稳定的高召回率」——即在多次调用中持续覆盖目标信息，而非寄望于单次完美输出。提出搜索接地、多路径并行、输出模板化三类策略。

## 实践方法

当系统判断已经基本清楚，真正的落地难点会从“理解 Agent”转向“如何把 Agent 放进持续工作的岗位与授权结构”。

- 2026-04-01 - 打造AI Agent员工的操作方法论 — 作者：Dexter。将 Long-Horizon Agent 从“会调用工具”推进为“可被逐步信任的数字员工”：围绕岗位定义、共享状态、角色手册、渐进授权与责任边界给出完整操作框架。

## 前端与交互范式

Agent 时代的前端不再是静态界面，而是动态生成、可与 Agent 双向通信的交互层。

- [[2026-02-08 - 生成式UI与Agent原生前端设计]] — 来源：Google Research、Google Developers、Jakob Nielsen。介绍 LLM 动态生成界面（Generative UI）的可用性研究，以及 A2UI 协议（Agent 到 UI 的声明式安全通信）的设计原则。核心问题：当界面本身由 AI 生成时，如何保证用户的理解与控制权。
- [[2026-02-08 - AI对话交互的信任框架与Agentic UX范式]] — 来源：IBM Design, Botpress, UX Magazine, Microsoft Design, Wharton 综合（2022–2026）。从对话设计基础出发，覆盖 Agentic UX 的全新范式：如何设计「模型路由」逻辑、如何在多轮 Agent 任务中维护用户信任、如何处理 Agent 失败时的交互降级。
- [[2026-04-10 - ChatGPT App 协同设计中的 The Third Body]] — 来源：Nikolay Rodionov（OpenAI Developers）。将 [[ChatGPT Apps]] 的构建难题归结为 “The Third Body”：产品不再只处理用户与界面，而要处理用户、widget、模型三方之间的上下文分配、可见性与边界管理。该文同时补齐了多显示模式、语言优先交互、`CSP` 约束与专门开发底座等生产经验。
- [[2026-02-08 - 语音与图像评估的Gate-Grade框架与分阶段建设]] — 来源：OpenAI Cookbook。处理多模态 Agent 的评估工程：语音和图像输出的评估标准如何设计（不能直接套用文本评估框架），以及 Gate-Grade 框架和 Crawl-Walk-Run 框架在多模态场景中的应用。

## 生态格局与产品形态

这一节从宏观视角看 Agentic 生态：厂商战略、协议标准、以及 Agent 时代新的产品形态如何塑造开发者的选择空间。

- [[2026-02-08 - Agentic AI厂商战略分化与标准收敛]] — 来源：OpenAI、Anthropic、Google 综合分析。三大厂商在 Agent 协议层呈现明显分化：OpenAI 主推 Agents SDK 与封闭生态，Anthropic 以 MCP（Model Context Protocol）押注开放标准，Google 以 A2A 协议主导跨平台互操作。分化之下正在出现的收敛信号。
- [[2025-09-11 - 需求侧智能体颠覆平台互联网的三层重构]] — 来源：侯宏（北大管理学助理教授）。从平台经济学视角分析 Agent 网络的三维战略意义：新的价值创造模式（Agent 作为经济参与者）、新的商业模式（按任务完成计费）、新的竞争格局（平台层 vs. 应用层的价值分配）。
- [[2026-03-10 - 以 Skills 为核心的领域 AI 产品形态]] — 作者：Dexter。当通用 Agent 泛化能力趋同，领域 AI 产品的竞争力来自「通用 Agent + 领域 Skill」的组合。Skill 作为可组合的能力单元，同时承担效率工具与职业转型载体的双重角色——是 Agentic 系统从技术架构到产品形态的桥接层。
- [[2026-03-16 - Agent时代利润先集中于模型与Harness耦合层]] — 作者：Dexter。把工程层的 Harness 讨论推进到产业层：为什么 Harness 不只是执行系统设计问题，而是 2026 年 AI 价值链中暂时吸引利润的性能瓶颈层。
- [[2026-03-16 - Agent压倒泡沫叙事的资本开支逻辑]] — 来源：Ben Thompson（Stratechery）。从产业结构视角补上 Agentic 系统构建的外部经济约束：一旦 Agent 真正可执行，算力需求、企业付费意愿与模型厂商利润归属都会被重估。适合作为本 Map 从工程走向产业判断的收束材料。

## 相关 Map

这两张相关 Map 分别向下展开评估方法，向外展开组织采用问题，因此适合作为本主题从“系统能不能做”过渡到“组织愿不愿意用”的下一跳。

- [[Topic - LLM 评估体系]] — 本 Map「系统设计与评估驱动」一节的深度展开，包含完整的评估方法论、RAG/Agent 诊断流程与数据集构建方法
- [[Topic - AI 落地与组织转型]] — 系统构建完成之后，如何在组织内推动采用、管理认知张力、重构人的角色

## Canonical Nodes

- [[2026-02-08 - Agentic系统设计与评估驱动开发]]
- [[2026-02-08 - 长时间运行Agent的上下文管理与弹性设计]]
- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]
- 2026-04-01 - 打造AI Agent员工的操作方法论

## 覆盖缺口

- 真实生产环境中的 durable execution、checkpoint 与恢复策略仍主要停留在分散材料，尚未形成单独权威节点
- 多 Agent 权限边界、审批门与失败责任分配的产品化设计仍缺一篇专门 Insight
