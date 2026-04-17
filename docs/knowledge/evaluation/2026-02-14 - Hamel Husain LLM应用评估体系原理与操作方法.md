---
type: source
author: Hamel Husain；Shreya Shankar
published: 2024-03-29 / 2024-10-29 / 2025-03-24 / 2026-01-15
source_url: https://hamel.dev/blog/posts/evals/
topics:
  - LLM evaluation
  - error analysis
  - LLM-as-judge
  - assertions
  - AI product development
created: 2026-02-14
updated: 2026-02-14
status: active
canonical: false
---

# Hamel Husain：LLM 应用评估体系原理与操作方法

## 一句话简介

评估不是附加成本，而是开发过程的组成部分；以 error analysis 为中心，将真实失败转化为可管理的失败分类法与可复跑的评估集，再用断言库与 LLM-as-judge 分层覆盖，支撑快速迭代与稳定交付。

## Takeaway

1. 用 error analysis 生成失败 taxonomy 与根因分布，决定真正该测什么 (Husain & Shankar, 2026)
2. 用断言库覆盖客观底线与不变量，用 LLM-as-judge 覆盖主观质量并通过领域专家批注对齐 (Husain, 2024-10)
3. 用 CI/生产分工与 prompts 的 Git 版本化治理，把评估闭环嵌入交付流程 (Husain & Shankar, 2026)

---

## 摘要

### 评估的目标：把"质量"变成可重复的反馈回路

该系列文章的共同主张是：AI 团队最常见的失败不是"模型不够强"，而是无法系统性回答"改动是否让产品更好"，导致迭代进入打地鼠模式：修一个问题冒出另一个、只能靠 vibe check、prompt 越写越长。(Husain, 2024)

评估系统的核心价值不是生成更多指标，而是让团队形成稳定闭环：看数据 → 识别失败 → 归因与优先级 → 修复与回归 → 再看数据。(Husain, 2025; Husain & Shankar, 2026)

> "Start with error analysis, not infrastructure." (Husain & Shankar, 2026)

### 成本分层：断言库优先，LLM judge 慎用

**Level 1：断言/单元测试**：用于可代码验证的底线规则与系统不变量，适合高频运行（每次提示词/代码改动）。同一批断言既可用于回归测试，也可用于数据清洗与必要的自动重试/回退。(Husain, 2024; Husain & Shankar, 2026)

**Level 2：人工评审 + 模型评审**：覆盖断言难以表达的主观标准（是否真正解决用户问题等）。前提是 trace 记录完整且查看成本足够低，否则评审无法稳定发生。(Husain, 2024)

**Level 3：A/B 测试**：验证对业务行为与结果的真实影响，适用于成熟阶段与重大变更决策。(Husain, 2024)

对"通用现成指标"持系统性怀疑：helpfulness/coherence 等分数可能制造进展幻觉；成熟用法是把它们当作"探索信号"来找异常 traces，而不是作为质量结论。(Husain, 2025; Husain & Shankar, 2026)

### 最小可行评估配置（MVES）

每次重大变更后，用约 30 分钟复核 20–50 条输出/trace，并指定一个懂用户结果的人作为质量裁决者（benevolent dictator）。核心是把评估落到现实交互上，而不是先建设复杂平台。大量开发时间会花在 error analysis 上；这不是浪费，而是"理解失败"的必要成本。(Husain & Shankar, 2026)

### Error analysis：open coding → axial coding → 理论饱和

Error analysis 是评估系统的核心活动，其价值是决定"到底该写哪些 eval"，避免被通用指标牵引。(Husain & Shankar, 2026)

**Open coding（开放式编码）**：人工评审 trace，用开放式语言记录"不符合预期的现象与原因"。起步阶段聚焦"第一个上游失败"，因为上游错误常导致后续一连串表象问题；先修上游通常能连带修复下游。(Husain & Shankar, 2026)

**Axial coding（主轴编码）**：把 open coding 的自由文本备注聚类归并为失败 taxonomy，并为每一类给出可复用的判定口径与代表样例；统计各类频次形成根因分布。可使用 LLM 辅助归并与整理，但 taxonomy 需要人工复核，否则容易形成不可行动的大类。(Husain & Shankar, 2026)

**理论饱和**：当继续增加样本时几乎不再出现新失败类型，说明 taxonomy 达到饱和；经验口径是至少复核约 100 条 traces。(Husain & Shankar, 2026)

### LLM-as-judge（Critique Shadowing）

先找主领域专家对样本做 Pass/Fail 并写足够详细的 critiques；再将这些专家样例用于 few-shot judge prompt 的迭代对齐，直到 judge 与专家判断在代表性样本上收敛。二元判定优先于 Likert 刻度：Likert 在实践中往往带来更低一致性、更高标注成本；细腻信息应由批注承载，二元判定用于决策清晰。(Husain, 2024-10; Husain & Shankar, 2026)

### 为什么通常不采用 eval-driven development（先写评估再开发）

一般不建议在功能实现前大量预写 evaluators。LLM 应用的失败空间巨大且难以事前枚举；过早写 eval 往往优化"想象中的问题"而非真实高频失败，并在早期造成探索阻塞。合理例外：当约束非常清晰且可验证时（如"必须输出合法 JSON schema""不得泄露内部 ID"），提前写断言/guardrail 可能是低成本且必要的。(Husain & Shankar, 2026)

### 工程治理：CI vs 生产；guardrails vs evaluators；提示词版本化

**CI 评估集**：通常小而精（100+ 条），覆盖核心能力、回归与边界；成本敏感，倾向确定性断言。

**生产评估**：基于采样 traces 异步运行；缺少参考答案时使用 reference-free 的 LLM judge，关注置信区间下界是否越过阈值；生产发现的新失败应回灌 CI 防回归。

**Guardrails** 是在线关键路径的快速拦截（低延迟、可解释、低误杀）；**Evaluators** 多用于离线衡量与改进，不直接阻断用户输出。

**提示词版本化偏向 Git**：把 prompts 当作软件工件纳入 Git，可追溯、可审阅、可回滚，并尽量与代码原子发布。(Husain & Shankar, 2026)

---

## 参考链接

- [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
  - 作者：Hamel Husain
  - 发布日期：2024-03-29

- [Using LLM-as-a-Judge For Evaluation: A Complete Guide](https://hamel.dev/blog/posts/llm-judge/index.html)
  - 作者：Hamel Husain
  - 发布日期：2024-10-29

- [A Field Guide to Rapidly Improving AI Products](https://hamel.dev/blog/posts/field-guide/)
  - 作者：Hamel Husain
  - 发布日期：2025-03-24

- [LLM Evals: Everything You Need to Know](https://hamel.dev/blog/posts/llm-evals-faq/)
  - 作者：Hamel Husain；Shreya Shankar
  - 发布日期：2026-01-15

## 相关笔记

- [[2026-02-14 - LLM输出一致性与召回率最大化]]（补充应用评估中的稳定性指标）
- [[Topic - LLM 评估体系]]（纳入应用评估主题入口）
- [[2026-04-06 - Hamel Husain 评估复位与数据科学价值]]（补充同源观点：API 时代数据科学工作的责任重心与产品级评估闭环）
