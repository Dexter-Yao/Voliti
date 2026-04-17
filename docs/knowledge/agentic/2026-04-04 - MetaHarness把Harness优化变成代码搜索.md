---
type: source
author: Yoonho Lee et al.
published: 2026-03-30
source_url: https://arxiv.org/html/2603.28052v1
topics:
  - harness engineering
  - context engineering
  - agentic coding
  - evaluation
  - retrieval
created: 2026-04-04
updated: 2026-04-05
status: canonical
canonical: true
review_after: 2026-07-04
---

# MetaHarness把Harness优化变成代码搜索

## 一句话简介

这篇论文提出 Meta-Harness，将原本主要依赖人工经验的 harness engineering 转化为一个由 coding agent 执行的外层搜索过程，直接在源码、分数与 execution traces 上迭代优化 harness。

## Takeaway

1. **作者将 harness 定义为包裹固定模型的有状态程序，而不只是 prompt 模板**：它决定存什么、取什么、何时取、如何组织后呈现给模型，因此模型表现往往与 harness 同等重要。
2. **作者将 context 理解为 harness 在当前步骤决定让模型看见的信息集合**：context 不是“更长的提示词”，而是由 harness 选择、排序、压缩并拼装后的可见世界。
3. **论文最核心的新增量不是又一个 benchmark 提升，而是证明 harness 本身可以成为可搜索的代码对象**：相比只看分数或摘要的 text optimization，保留原始 execution traces 并允许 agent 自主检索，是自动化 harness engineering 的关键。

---

## 摘要

## 问题定义

论文从一个直接但重要的观察出发：大型语言模型系统的表现不仅取决于模型权重，也取决于外层 harness。作者将 harness 定义为“决定存储、检索并向模型呈现什么信息的代码”，并指出在同一个基座模型上，仅仅更换 harness 就可能产生显著性能差异（Lee et al., 2026）。

> “The harness—the code that determines what to store, retrieve, and show to the model—often matters as much as the model itself.”
> (Lee et al., 2026)

在作者看来，现有 text optimization 方法并不适合这个问题。原因不在于它们完全无效，而在于它们通常只基于压缩过的反馈工作，例如只看当前候选、只看标量分数、或只看短摘要。harness 的影响往往跨越较长执行链条，很多失败要到若干步之后才显现；一旦反馈被过度压缩，真正可用于诊断的因果线索就丢失了（Lee et al., 2026）。

## Harness 与 Context 的定义

论文对两个核心概念给出了清晰而操作性的定义。

### Harness

作者将 harness 定义为**包裹语言模型的有状态程序（stateful program）**。这个程序在每一步负责构造 prompt、决定是否检索外部信息、维护状态，并在模型响应后更新内部状态。换言之，harness 并不是“一个写得更好的 prompt”，而是一段控制模型如何工作的外层代码（Lee et al., 2026）。

这意味着 harness 的优化目标不是“让模型说得更好听”，而是“让整个系统在目标任务分布上表现更好”。在文本分类、数学检索推理与 agentic coding 三类实验里，被优化的对象都不是模型参数，而是外层 harness 的具体实现。

### Context

作者没有把 context 当作一个抽象口号，而是将其落到系统行为层面：**context 是 harness 在当前步骤决定让模型看见的信息**。它可能包括任务描述、检索结果、working memory、历史状态、工具输出、环境信息与错误轨迹。context 的边界由 harness 决定，因此 context engineering 本质上是 harness engineering 的一部分（Lee et al., 2026）。

## Meta-Harness 的机制

Meta-Harness 是一个外层搜索系统，用于搜索“任务特定的 harness”。它本身也是一个更广义的 harness，因为它决定 proposer 在搜索过程中能看到什么信息；但除非特别说明，论文中的 harness 一般指被搜索与优化的任务内 harness（Lee et al., 2026）。

整个循环由三步构成：

### 1. 提案

系统使用一个 coding agent 作为 proposer。与只在固定 prompt 上生成候选方案的传统方法不同，这个 proposer 可以像工程师一样使用开发工具，读取文件系统中的历史工件，主动检查之前候选方案的源码、得分和执行轨迹，再提出新的 harness 代码（Lee et al., 2026）。

### 2. 评测

每个新 harness 会在目标任务上执行 rollout，并由任务特定 reward function 进行评分。若任务涉及多个目标，例如准确率与上下文成本，论文使用 Pareto dominance 评估候选方案（Lee et al., 2026）。

### 3. 归档

每次评测后，系统都会把新候选方案的源码、分数、prompt、tool calls、模型输出与状态更新等日志写入文件系统中的独立目录，形成可检索的经验库，供之后的 proposer 继续使用（Lee et al., 2026）。

## 与既有优化方法的差异

Meta-Harness 的关键设计不是一个更复杂的 search scaffold，而是**完整保留历史经验，并允许 proposer 自主选择读取什么**。作者认为，真正重要的并非“把更多 token 塞进同一个 prompt”，而是让 agent 在需要时访问原始工件，而不是被迫依赖一份预先压缩好的摘要（Lee et al., 2026）。

> “Meta-Harness preserves full experience history using a filesystem and allows the proposer to inspect anything necessary...”
> (Lee et al., 2026)

论文给出的对比也围绕这一点展开。OPRO、TextGrad、AlphaEvolve、GEPA、Feedback Descent 和 TTT-Discover 等方法，要么只使用窗口化历史，要么依赖摘要或分数；Meta-Harness 则暴露完整历史，并允许 proposer 通过 `grep`、`cat` 等终端工具主动检索（Lee et al., 2026）。

## 三组实验

### 在线文本分类

在在线文本分类任务中，Meta-Harness 以固定基座模型 GPT-OSS-120B 搜索分类 harness。论文报告其最终准确率达到 48.6%，超过 ACE 7.7 个点、超过 MCE 8.6 个点，同时上下文成本仅为 11.4K tokens，低于 ACE 的 50.8K 与 MCE 的 28.5K（Lee et al., 2026）。

更重要的是 ablation。若 proposer 只能看标量分数，最优搜索准确率只有 41.3；若给分数加摘要，反而进一步降到 38.7；完整 Meta-Harness 则达到 56.7。这一结果支持作者的核心主张：**raw execution traces 才是 harness 搜索中最有信息量的反馈形式**（Lee et al., 2026）。

### 数学检索增强推理

在数学推理任务中，作者不是优化模型，而是优化 retrieval harness。语料库包含约 53.5 万道已解数学题，经过去重与去污染处理。最终发现的 harness 并非复杂神经模块，而是按题目特征路由到不同子策略的 BM25 检索程序（Lee et al., 2026）。

在 200 道 IMO 级别问题上，这个 discovered harness 对 5 个未参与搜索的 held-out 模型平均带来 4.7 个点的提升。这里的意义不只是“检索更强”，而是说明 harness 搜索可以发现一套比人工统一策略更细粒度的 context construction logic（Lee et al., 2026）。

### TerminalBench-2 上的 Agentic Coding

在 TerminalBench-2 上，Meta-Harness 从 Terminus 2 与 Terminus-KIRA 等 hand-engineered harness 出发继续搜索。最终结果中，Opus 4.6 版本达到 76.4% pass rate，超过 Terminus-KIRA 的 74.7%；Haiku 4.5 版本达到 37.6%，位列该模型档位第一（Lee et al., 2026）。

附录显示，其中一个有效改动是为 agent 加入 environment snapshot bootstrap：在首轮推理前先抓取目录、语言、包管理器、内存等环境信息。这一改动并不复杂，但显著减少了 agent 在早期回合中的环境探测开销，说明许多 coding benchmark 上的失分并非来自推理本身，而来自 harness 对环境信息暴露不足（Lee et al., 2026）。

## 作者对 proposer 行为的解释

论文附录强调，proposer 并不只是“随机生成更多候选”。在若干失败案例中，它能够比较多个版本的退化点，识别共同原因，并将某些 prompt 层变动回退，只保留真正起作用的结构修复。这说明 proposer 至少在局部上具备基于历史失败进行因果归因的能力（Lee et al., 2026）。

## 论文结论

这篇论文的结论可以概括为一句话：**自动化 harness engineering 是可行的，而其前提不是更花哨的 prompt optimizer，而是让 coding agent 在完整历史工件上工作。** 作者据此主张，随着 coding agent 能力提升，harness 搜索应被视为一个独立且重要的研究方向（Lee et al., 2026）。

---

## 参考链接

- [Meta-Harness: End-to-End Optimization of Model Harnesses](https://arxiv.org/html/2603.28052v1)
  - 作者：Yoonho Lee, Roshen Nair, Qizheng Zhang, Kangwook Lee, Omar Khattab, Chelsea Finn
  - 发布日期：2026-03-30
- [Meta-Harness Project Page](https://yoonholee.com/meta-harness/)
  - 作者：Yoonho Lee et al.
  - 发布日期：N/A
- [TerminalBench-2 Artifact](https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact)
  - 作者：Stanford IRIS Lab
  - 发布日期：N/A

## 相关笔记

- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]（该文提出 harness engineering 的工程范式，这篇论文则进一步证明 harness 本身可以成为自动搜索对象）
- [[2026-03-16 - Agent时代利润先集中于模型与Harness耦合层]]（这篇论文提供了“为什么 harness 层可形成真实差异化资产”的机制层证据）
- [[2026-03-16 - Context Layer的两种形态可编码知识与执行涌现知识]]（execution traces 在本文中不是日志附件，而是 harness 搜索的关键信号，与该笔记的 trace 资产判断直接呼应）
- [[agentic coding]]（作为代码环境中 Agent 闭环执行的概念入口）
