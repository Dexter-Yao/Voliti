---
type: insight
author: Dexter
published: N/A
topics:
  - agentic AI
  - value chain
  - competitive moat
  - harness engineering
  - context engineering
source_basis:
  - "[[2026-04-12 - ClaudeCode泄露证明AI工程价值转向Harness]]"
  - "[[2026-04-09 - Harness把执行轨迹变成智能飞轮]]"
  - "[[2026-04-04 - MetaHarness把Harness优化变成代码搜索]]"
  - "[[2026-04-04 - LLM智能市场的供给定价与需求结构]]"
  - "[[2026-03-16 - Context Layer的两种形态可编码知识与执行涌现知识]]"
  - "[[2025-09-15 - AI时代护城河的双层结构从智能内核到商业外壳]]"
  - "[[2026-03-16 - Christensen利润守恒定律的机制案例与局限]]"
  - "[[2026-03-16 - Agent压倒泡沫叙事的资本开支逻辑]]"
  - "[[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]"
  - "[[2026-03-07 - AI Agent时代按成果收费的全景研究]]"
  - "[[2026-03-02 - AI采用格局的真实分裂从泛用到深用]]"
  - "[[2026-04-04 - AI代理决策偏差与机器消费者心理]]"
  - "[[2026-04-01 - 打造 AI Agent 员工的操作方法论]]"
created: 2026-03-16
updated: 2026-04-12
status: canonical
canonical: true
review_after: 2026-07-04
---

# Agent时代利润先集中于模型与Harness耦合层

## 一句话简介

在 Agent 产品范式下，模型能力不再以 API 形式独立兑现，而是通过 Harness、工具调用、Eval、状态管理与执行环境共同转化为可交付结果；因此 2026 年最具吸引力的利润暂时集中于模型与 Harness 的耦合层，但随着 Long-Horizon Agent 从 Coding 走向企业流程与现实世界，利润还会继续沿着价值链迁移。

## Takeaway

1. **模型与 Harness 在 Agent 时代形成了阶段性的再耦合层**：用户购买的不是模型回答，而是任务完成率；只要可靠执行仍然稀缺，利润就会集中在这一层。
2. **这不是对利润守恒定律的否定，而是它在 AI 时代的动态体现**：模块化不会线性推进；当标准接口无法交付足够性能时，价值链会重新走向局部专有整合。
3. **一旦通用 Agent 能力趋于充足，利润大概率继续迁移**：先从模型回答迁移到可靠执行，再从可靠执行迁移到工作流嵌入、专有上下文、Eval 体系、关系型分发与 outcome 定价控制权。

## 问题描述

这篇笔记试图回答的问题不是"2026 年哪家公司最值钱"，而是"当 Agent 从聊天框变成劳动力之后，利润究竟先停在哪里、又会往哪里走"。OpenClaw 这类产品的重要性，不在于它们是否会成为最后的赢家，而在于它们把一个过去主要属于研究和工程圈的事实做成了大众可见的产品形态：Agent 开始获得真实权限，进入真实工作流，并承担跨系统、跨时间尺度的执行任务。

## 为什么 2026 年利润仍停留在这层

Christensen 的利润守恒定律并不要求价值链永久稳定，而要求先识别"系统中哪一层仍然 not yet good enough"。在今天的 Agent 产业里，真正尚未被充分解决的问题不是模型参数量本身，而是如何让模型稳定地完成复杂任务。

这使得模型层、Harness 层、工具层、Eval 层、状态恢复层在经济上共同构成一个单一瓶颈。OpenAI 的 Codex、Anthropic 的 Claude Code 之所以显得重要，不是因为它们单独拥有最强模型，而是因为它们把模型、任务编排、验证回路和失败恢复封装成了结果交付系统。

用户愿意付费的对象因此发生了变化：不是购买 intelligence token，而是购买 reliable execution。只要可靠执行仍稀缺，利润就不会离开这一层。

OpenClaw 的信号意义恰好在这里。它向普通用户展示的不是一个更会聊天的模型，而是一个能翻邮箱、读日历、跑终端、接入 Slack/Discord、跨系统处理任务的执行体。只要这类能力仍然需要复杂的权限连接、失败恢复、上下文管理和技能编排，利润就不会单独沉淀在模型 API，而会沉淀在模型与 Harness 的耦合层。

2026-03-30 的 Claude Code 源码泄露则提供了一份罕见的公开反证材料：外界原本容易把编程 Agent 理解为“命令行界面 + 强模型”的轻壳产品，但泄露代码展示的却是自愈查询循环、Dream Mode 记忆整理、结构化工具约束、串并行调度与缓存稳定化等大规模工程脚手架。这类证据使“利润为何先停在模型与 Harness 的耦合层”不再只是产业推断，也获得了具体系统形态层面的公开佐证。

[[2026-04-04 - MetaHarness把Harness优化变成代码搜索]] 为这一判断补上了更细的机制层证据：Harness 不只是人工经验打磨出来的执行外壳，也可以被当作可搜索的代码对象。只要 execution trace、评测分数与候选方案源码能够持续归档并被 coding agent 重新检索，Harness 本身就会演化为一种可积累、可迭代、可复利的系统资产，而不再只是 prompt 层的小技巧。

[[2026-04-09 - Harness把执行轨迹变成智能飞轮]] 则把这一机制翻译成更适合产品与投资语境的判断：当 prompt engineering 与 context engineering 逐步收敛为工程常识之后，真正决定结果交付质量的已经是 harness 如何组织信息、执行与反馈闭环。也因此，execution trace 不只是技术副产物，而正在成为价值捕获与后训练数据飞轮的共同源头。

[[2026-04-04 - LLM智能市场的供给定价与需求结构]] 提供了一个与此判断相互印证的市场截面。该论文发表于 2025-12-12，使用的 OpenRouter usage 主体窗口始于 2025-01，provider-level 价格与流量数据始于 2025-04，Microsoft Azure 企业面板截至 2025-06。其关键发现是：开源模型在相同 intelligence 水平下比闭源模型便宜约 87% 到 90%，但平均份额仍低于 30%，且多数企业即便实验多模型，生产流量仍集中在单一默认模型上。这说明即便 intelligence token 已经明显商品化，企业采购与实际使用仍在为默认入口、品牌信任、工作流兼容与执行可靠性付费，而这些都更接近 Harness 层与分发层的能力，而不是裸模型本身。

## Long-Horizon Agent 如何把利润问题重新定义

Long-Horizon Agent 与早期 Copilot 式产品的差别，不是"多做几步"，而是交付单位的变化。

- Copilot 卖的是局部能力增强，例如建议、草稿、补全。
- Long-Horizon Agent 卖的是跨步骤结果，例如工单解决、审批完成、资料收集、理赔预审。

这一区别决定了利润判断必须改写。只要产品的核心价值仍然是"帮人更快地做"，利润大多仍落在工具预算里；一旦产品的核心价值变成"直接替代一段劳动闭环"，预算就开始从 software budget 向 services budget 迁移。

因此，2026 年最关键的不是"模型是否更聪明"，而是三层能力是否同时成立：

1. **是否能长时间保持状态**：任务跨小时、跨天执行而不丢上下文。
2. **是否能进入真实环境执行**：不仅调用 API，还能穿透 GUI、文档、遗留系统与语音交互。
3. **是否能被业务验收为结果**：客户愿意按 FTE、resolution、case completion 或其他 outcome 单位付费。

## 为什么这层不会是最终归宿

利润守恒定律更深的含义不是"找到今天最赚钱的层"，而是理解"今天最赚钱的层，未来为什么会失去吸引利润的能力"。

如果模型与 Harness 的组合继续成熟，会发生两件事。

第一，更多能力会被抽象成标准化接口。任务分解、工具调用、状态恢复、Eval 配置会逐渐产品化，新的进入者不必从零构造完整系统。

第二，用户的选择标准会改变。当多个通用 Agent 都能完成任务，市场不再主要比较"能否完成"，而开始比较：

- 谁更懂我的历史上下文
- 谁更嵌入我的组织工作流
- 谁拥有更可信的验收标准
- 谁能以更低成本、更高可控性持续交付

也就是说，当执行能力从稀缺变成 table stakes，利润会再次迁移。

## 利润可能迁移到哪里

### 路径一：向下游迁移到 Context / Workflow 层

这是与 [[2026-03-16 - Context Layer的两种形态可编码知识与执行涌现知识]] 及 [[2025-09-15 - AI时代护城河的双层结构从智能内核到商业外壳]] 最一致的路径。当通用 Agent 执行能力趋同，真正的稀缺资产将变成专有上下文、历史记忆、工作流嵌入、领域 Eval 与反馈闭环。此时的护城河不再是"我有更强的模型"或"我有更聪明的 harness"，而是"我更理解这家组织如何运作，以及什么才算完成得好"。

### 路径二：向上游迁移到 Compute / Infra 供给层

如果 Agent 经济持续推高推理消耗，而产品层难以维持显著差异化，那么利润也可能向真正稀缺的供给侧约束迁移，例如数据中心建设、能源、推理编排、算力调度与成本控制能力。

### 路径三：中间层被两端挤压

最危险的情况是中间的模型与 Harness 层既失去技术独占，又没有拿到足够深的下游上下文。那样利润会被上游稀缺供给和下游深嵌入应用共同分走，中间层沦为高成本但低议价的通道。

## 从价值链视角看 2026 的四个利润停靠点

如果把 Long-Horizon Agent 产业拆开看，利润不会平均分布，而会优先停靠在四类最稀缺的位置。

### 1. Reasoning Orchestrator / Durable Execution

这类层解决的是"能不能跑完"。当任务跨越数小时甚至数天，失败恢复、幂等、状态管理和异步调度会成为真实瓶颈。像 Temporal、Inngest 这类基础设施并不拥有终端需求，却掌握了长时程任务能否进入生产环境的门槛。

### 2. Process Intelligence / Execution Trace

这类层解决的是"做过之后有没有积累"。当 Agent 每次执行都能沉淀 corner cases、人类修正记录、API 调用路径、GUI 操作轨迹时，产品开始拥有通用模型拿不到的经验资产。这里的利润来自可复利的 execution trace，而不是一次性的调用差价。

### 3. Selling Labor / Vertical Specialist

这类层解决的是"预算从哪里出"。一旦客户的购买理由从"工具好用"变成"少雇一个人"，产品就不再只争夺软件预算，而开始争夺服务预算、外包预算甚至岗位预算。这里的代表性优势不是更强的 demo，而是更强的结果归因、审计能力和行业准确率。

### 4. Voice / Human Interface

这类层解决的是"谁来面对真实人类"。在医疗、保险、金融、物流等场景，语音不是附加 UI，而是实际劳动过程的一部分。谁能在低延迟、情绪处理、合规转人工和审计回溯之间建立稳定闭环，谁就更可能拥有最终分发权。

## 这对 AI 产品判断意味着什么

对产品判断而言，2026 年最容易犯的错误是把"当前利润集中点"误认为"长期护城河所在"。模型原生 Agent 公司今天的优势是真实的，但必须继续把阶段性性能瓶颈转化为结构性资产：专有工作流、专有 context、专有 eval、分发控制权，以及组织级嵌入。否则，今天的耦合优势会在下一轮模块化中被重新摊薄。

更具体地说，2026 年的产品判断至少要分三层：

1. **哪一层 today is not good enough**：如果是可靠执行，利润先在 Harness；如果是企业嵌入，利润在 workflow/context；如果是结果交付，利润在 vertical app。
2. **哪一层能够积累不可迁移资产**：执行 trace、专有评估标准、结果归因体系、客户关系与分发控制权。
3. **哪一层最可能被模型原生能力反向吃掉**：越接近通用能力包装、越缺少私有反馈回路的产品，越容易被基础模型厂商下压。

## 参考链接

- [Breakthrough Ideas for 2004 — Harvard Business Review](https://hbr.org/2004/02/breakthrough-ideas-for-2004)
  - 作者：Clayton Christensen
  - 发布日期：2004-02
- [Netflix and the Conservation of Attractive Profits — Stratechery](https://stratechery.com/2015/netflix-and-the-conservation-of-attractive-profits/)
  - 作者：Ben Thompson
  - 发布日期：2015
- [OpenClaw 是一个信号｜2026 Long-Horizon Agent 投资地图](https://www.google.com/search?q=OpenClaw+%E6%98%AF%E4%B8%80%E4%B8%AA%E4%BF%A1%E5%8F%B7%EF%BD%9C2026+Long-Horizon+Agent+%E6%8A%95%E8%B5%84%E5%9C%B0%E5%9B%BE)
  - 作者：Haina
  - 发布日期：N/A
- [OpenClaw](https://openclaw.ai/)
  - 作者：OpenClaw
  - 发布日期：N/A
- [OpenClaw Docs](https://docs.openclaw.ai/index)
  - 作者：OpenClaw
  - 发布日期：N/A
- [Temporal Docs](https://docs.temporal.io/)
  - 作者：Temporal
  - 发布日期：N/A
- [用户提供 PDF（本地文件）](/Users/dexter/Downloads/Mar.31_webinar%20paper.pdf)
  - 作者：Mert Demirer, Andrey Fradkin, Nadav Tadelis, Sida Peng
  - 发布日期：2025-12-12
- [Harness is the New Dataset：模型智能提升的下一个关键方向](https://mp.weixin.qq.com/s/9qI83Ne-Ac_R9y-yJ6SVnQ)
  - 作者：Celia
  - 发布日期：N/A

## 相关笔记

下面这些笔记分别对应这篇文章里的理论起点、当前瓶颈、落地方法与产业验证，因此一起构成了“利润为什么先停在这里、之后又会往哪里走”的完整链路。

- [[2026-03-16 - Christensen利润守恒定律的机制案例与局限]]（本文的理论起点）
- [[2026-03-16 - Agent压倒泡沫叙事的资本开支逻辑]]（提供 2026 年产业判断的一手材料：算力需求、企业采用与模型+harness 集成利润的现实语境）
- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]（解释模型与 Harness 为什么会在 Agent 时代重新形成性能瓶颈）
- [[2026-03-16 - Context Layer的两种形态可编码知识与执行涌现知识]]（解释利润在中间层趋于标准化之后为何更可能向下游 context 层迁移）
- [[2025-09-15 - AI时代护城河的双层结构从智能内核到商业外壳]]（将价值链利润迁移与护城河形成机制连接起来）
- [[2026-03-07 - AI Agent时代按成果收费的全景研究]]（说明为什么 Long-Horizon Agent 一旦能交付结果，预算会从软件支出转向劳动支出）
- [[2026-04-01 - 打造 AI Agent 员工的操作方法论]]（从实际部署角度解释 Long-Horizon Agent 为什么需要岗位定义、状态管理与渐进授权）
- [[2026-04-04 - LLM智能市场的供给定价与需求结构]]（为“模型 token 商品化而利润不回流到模型层”提供 2025 年 API 市场的实证背景）
- [[2026-03-02 - AI采用格局的真实分裂从泛用到深用]]（补充为什么即便企业实验多模型，真正深度使用仍会集中在少数默认工作流与主模型上）
- [[2026-04-04 - AI代理决策偏差与机器消费者心理]]（从机器排序与机器推荐视角补充未来分发控制权为何会成为新的利润控制点）
- [[2026-04-04 - MetaHarness把Harness优化变成代码搜索]]（提供“execution trace + harness search”如何把 Harness 变成可积累资产的研究证据）
- [[2026-04-10 - 原始会话记录应附着运行时而非长期Store]]（从运行时架构层面补充为什么 session、thread history 与 archive access layer 会先成为可积累资产，而不是被长期 Store 吞并）
- [[2026-04-09 - Harness把执行轨迹变成智能飞轮]]（把 “The Harness is the Dataset” 压缩成中文语境下更清晰的三层框架，并补上创业机会与 coordination engineering 的外延判断）
