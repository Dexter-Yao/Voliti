---
type: source
author: Hamel Husain；Shreya Shankar
published: 2026-01-15
source_url: https://hamel.dev/blog/posts/llm-evals-faq/
topics:
  - RAG evaluation
  - IR metrics
  - agentic workflows
  - transition failure matrix
  - LLM evaluation
created: 2026-02-28
updated: 2026-02-28
status: active
canonical: false
---

# Hamel Husain：RAG 与 Agent 工作流评估分步诊断方法

## 一句话简介

RAG 评估必须拆成检索与生成两套独立指标体系；复杂 Agent 工作流采用"先端到端成功，再分步诊断"的两阶段策略，并用 transition failure matrix 将链路失败热点压缩为可行动的修复优先级。

## Takeaway

1. RAG 评估必须拆成检索（IR 指标）与生成（error analysis + aligned judge）两套体系，不能打一个"RAG 分数"
2. Chunk size 是可调超参数：固定输出任务倾向大块，扩展输出任务倾向小块，须实验验证而非凭经验固定
3. Agentic workflows 采用"端到端成功→分步诊断"两阶段评估；transition failure matrix 将失败热点结构化为最高 ROI 修复清单

---

## 摘要

### RAG 评估：检索是搜索问题，生成是生成问题

Husain & Shankar 明确反对将 RAG 视为单一模块打一个"RAG 分数"，要求把评估拆成两类独立问题。(Husain & Shankar, 2026)

**检索评估（Retrieval）**：属于信息检索（IR）问题，应优先使用传统 IR 指标，如 Recall@k、Precision@k、MRR 等。关键前提是有"查询→相关文档"的配对数据集（query-doc pairs）。构建思路：从语料中抽取事实或关键要点，再反向生成能命中这些要点的问题，从而得到可用于离线检索评估的配对集。(Husain & Shankar, 2026)

**生成评估（Generation）**：关注模型是否使用了检索上下文、是否忠实于上下文、是否真正回答了问题。仍应使用 error analysis 识别失败模式，并通过人工标注与经验证的 LLM-as-judge 来度量。强调不要直接套用"现成 judge prompt"；judge 的 TPR/TNR 必须在人工标注集上验证，否则其结论可能与真实质量标准不一致。(Husain & Shankar, 2026)

### Chunk Size：按任务类型调参

Chunk size 是需要实验验证的超参数，即使文档能放进上下文窗口，也不意味着"单大块"效果最好。(Husain & Shankar, 2026)

- **固定输出任务**（输出长度不随输入增长，如定位某条条款、抽取某个数字）：倾向更大 chunk，但要避免引入无关文本干扰，并警惕长上下文中段注意力瓶颈。
- **扩展输出任务**（输出随输入增长，如分段总结、穷举抽取）：倾向更小 chunk，并尽量尊重段落/章节边界；常用方式是分块处理再汇总（map-reduce），以提升覆盖与完整性。

### Agentic Workflows：先端到端，后分步诊断

对 agentic workflows 的推荐是两阶段评估：(Husain & Shankar, 2026)

**阶段一：端到端任务成功**：将 agent 视为黑盒，先问"是否达成用户目标"，并为每个任务定义清晰的成功规则（正确答案、正确副作用、正确状态变更等）。在 error analysis 中优先定位首个上游失败。

**阶段二：分步诊断（step-level diagnostics）**：在具备足够 instrumentation（工具调用与返回、检索结果、中间产物等）后，对关键环节分别诊断：工具选择是否恰当、参数抽取是否完整、是否能从空结果/API 失败恢复、是否保持约束、效率（步数/耗时/成本）、关键里程碑是否达成等。

其管理意图是把"链路很长"转化为"哪一步坏得最多"，从而使修复具有方向性与可验证性。

### Transition Failure Matrix：失败热点结构化为 ROI 投入地图

Transition failure matrix（状态转移失败矩阵）的做法：(Husain & Shankar, 2026)

1. 为工作流定义一组状态/阶段（如 DecideTool → GenSQL → ExecSQL → Summarize）。
2. 对每条失败 trace，标注"最后成功状态"与"首次失败状态"。
3. 统计每一对状态转移上的失败次数，形成矩阵热区。

矩阵的价值在于：把大量复杂 trace 压缩为可行动的热点图谱——团队可以直接看到"哪个转移最容易坏"，并优先投入修复与回归验证。该方法也用于对比不同实验/方案的失败分布变化，以评估某次改动是"真正减少了关键失败"还是"把失败迁移到别处"。(Husain & Shankar, 2026)

### 多轮对话与人类交接

调试多轮对话时先做端到端 Pass/Fail，再聚焦第一个上游失败；必要时将问题简化为最小单轮可复现用例，以确认失败是否依赖上下文。(Husain & Shankar, 2026)

对人类交接（handoff），trace 应覆盖到用户需求解决或会话结束为止，并记录交接原因、上下文传递、等待时间与最终解决情况；交接的必要性与质量应作为失败 taxonomy 的组成部分进行评估。(Husain & Shankar, 2026)

---

## 参考链接

- [LLM Evals: Everything You Need to Know](https://hamel.dev/blog/posts/llm-evals-faq/)
  - 作者：Hamel Husain；Shreya Shankar
  - 发布日期：2026-01-15

- [A Field Guide to Rapidly Improving AI Products](https://hamel.dev/blog/posts/field-guide/)
  - 作者：Hamel Husain
  - 发布日期：2025-03-24

## 相关笔记

- [[Topic - LLM 评估体系]]（纳入 RAG 与 Agent 工作流评估主题入口）
- [[Topic - Agentic AI 系统构建]]（连接工作流评估与 Agent 系统设计）
