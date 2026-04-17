---
type: source
author: Hamel Husain；Shreya Shankar
published: 2024-03-29 / 2025-03-24 / 2026-01-15
source_url: https://hamel.dev/blog/posts/llm-evals-faq/
topics:
  - synthetic data
  - dataset design
  - LLM evaluation
  - scenario coverage
  - error analysis
created: 2026-02-28
updated: 2026-02-28
status: active
canonical: false
---

# Hamel Husain：合成数据驱动的评估数据集构建流程

## 一句话简介

合成数据的目的不是伪造"正确答案"，而是结构化生成用户输入以触发真实系统行为，从而得到可复跑 traces 进行 error analysis；核心方法是"维度设计→tuples→两步生成→场景覆盖验证"，并对不可验证/高风险领域保持谨慎。

## Takeaway

1. 先定维度，再用 tuples 显式表达覆盖蓝图，并先手工写 20 个 tuples 建立直觉 (Husain & Shankar, 2026)
2. 用两步生成（tuples→自然语言）降低同质化，并将样本跑进真实系统做场景覆盖验证 (Husain & Shankar, 2026)
3. 对不可验证与高风险领域保持谨慎，避免合成数据替代真实样本 (Husain & Shankar, 2026)

---

## 摘要

### 何时需要合成数据：没有用户也要能开始迭代

在早期或数据稀缺阶段，团队常陷入"没有数据就无法评估"的僵局。合成数据可以有效启动评估与迭代，尤其适用于你能够验证场景触发与输出质量的产品场景。(Husain, 2025; Husain & Shankar, 2026)

一个关键约束是：合成数据更适合生成**用户输入**，而不应直接生成"期望输出/标准答案"。原因是合成输出会把生成模型的偏好与盲点写入基准，从而弱化评估的判别力。(Husain & Shankar, 2026)

### 维度（Dimensions）：用结构描述用户差异

合成数据要从"维度"开始：每个维度描述用户输入中一种重要差异来源（例如功能、场景、用户画像、语气、语言、地域等）。维度的选择应尽量来自失败假设：你认为系统最可能在哪类差异下失败。在缺乏失败直觉时，建议先让自己或朋友充分使用应用，形成初步失败假设，再回到维度设计。(Husain & Shankar, 2026)

### Tuples（元组）：维度取值组合的"结构化蓝图"

tuples 指"从每个维度选一个取值形成组合"。例如一个客服系统可以定义：

- Issue Type：billing / technical / general
- Mood：frustrated / neutral / happy
- Prior Context：new / follow-up / resolved

则 tuple 可能是：(`billing`, `frustrated`, `follow-up`)。(Husain & Shankar, 2026)

tuples 的工程价值：
1. 覆盖面可检查：你能明确知道生成了哪些组合与缺哪些组合。
2. 语言更去同质化：避免"同一句式换词"导致表面多样、实则重复。
3. 有利于分层分析：后续可以按 tuple 维度切片统计失败率，快速定位薄弱环节。(Husain & Shankar, 2026)

建议先手工写约 20 个 tuples，以建立问题空间直觉，并暴露维度设计是否合理（是否有大量无效组合、是否遗漏关键差异）。(Husain & Shankar, 2026)

### 两步生成：先 Tuples，后自然语言用户输入

推荐两步生成法：先生成结构化 tuples，再把 tuples 转成自然语言用户输入。其核心动机是把"覆盖控制"与"语言实现"分离：覆盖由 tuples 保证，多样表达由第二步语言生成实现，从而显著降低同质化。(Husain & Shankar, 2026)

### 两条生成策略：全组合后过滤 vs 直接生成 Tuples

**全组合（cross product）后过滤**：先生成维度取值的全组合，再过滤无效组合。优点是覆盖性强，适合大多数组合有效的场景。

**直接生成 tuples**：让 LLM 直接生成 tuples。优点是更自然，缺点是容易偏向常见组合并漏掉稀有边界，适合大量组合无效的场景。

选择标准是"覆盖与有效性"的成本权衡：无效组合太多时，全组合会浪费；边界组合很关键时，直接生成会漏。(Husain & Shankar, 2026)

### 场景覆盖验证：确保样本真的触发目标情境

合成数据常见失败是"看似覆盖，实际没触发"。例如想测"no matches found"，但输入在测试库里仍有匹配，导致评估无法压力测试该场景。

因此需要进行场景覆盖验证：把合成输入跑进真实系统与测试数据库，确认它确实触发目标场景（no-match 就必须返回 0 结果，multiple-match 就必须返回多个结果等）。(Husain, 2025; Husain & Shankar, 2026)

### 何时不应依赖合成数据

合成数据可能误导的情形：复杂专业领域内容（法律/医疗等）、低资源语言/方言、无法验证样本真实性、高风险领域、代表性不足群体等。

核心判断标准是：你是否能为"这条合成样本像真"提供验证路径；若不能，合成数据容易掩盖关键边界失败。(Husain & Shankar, 2026)

---

## 参考链接

- [LLM Evals: Everything You Need to Know](https://hamel.dev/blog/posts/llm-evals-faq/)
  - 作者：Hamel Husain；Shreya Shankar
  - 发布日期：2026-01-15

- [A Field Guide to Rapidly Improving AI Products](https://hamel.dev/blog/posts/field-guide/)
  - 作者：Hamel Husain
  - 发布日期：2025-03-24

- [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
  - 作者：Hamel Husain
  - 发布日期：2024-03-29

## 相关笔记

- [[2026-02-15 - OpenAI Cookbook Eval驱动系统设计方法论]]（补充合成数据与评估数据集构建的工程路径）
- [[Topic - LLM 评估体系]]（纳入评估数据集主题入口）
