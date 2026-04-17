---
type: map
topics:
  - LLM
  - evaluation
  - RAG
  - synthetic data
  - agentic AI
created: 2026-03-01
updated: 2026-04-06
status: canonical
canonical: true
review_after: 2026-07-04
---

# LLM 评估体系

## 导读

本 Map 回答一个在 LLM 应用开发中被严重低估的问题：**你怎么知道你的 AI 系统变得更好了，而不是只是感觉更好了？**

直觉和 vibe check 在原型阶段还行，在生产阶段是灾难。这张 Map 积累的是「评估即工程」的完整方法论——从为什么要 Eval 先行，到具体如何对 RAG、Agent 工作流分步诊断，再到如何用合成数据构建覆盖足够广的测试集，最后用陷阱清单对常见错误做自检。

**知识脉络**：评估哲学（为什么 Eval 是系统设计的核心）→ 方法论骨架（Hamel 体系）→ 实操示范（OpenAI Cookbook）→ 特定场景诊断（RAG + Agent）→ 数据集构建 → 陷阱识别 → 多模态延伸

**Hamel Husain 三篇**（评估体系、RAG/Agent 诊断、合成数据集）构成本 Map 的骨架，建议按顺序读完再展开其他节点。

## 阅读起点

[[2026-02-14 - Hamel Husain LLM应用评估体系原理与操作方法]] 是整张 Map 的锚点，确立评估体系的基本认识论。

---

## 评估原则与整体框架

在写第一行 Agent 代码之前，你需要先确立「怎么判断对错」的标准。这一节建立这个标准。

- [[2026-02-14 - Hamel Husain LLM应用评估体系原理与操作方法]] — 来源：Hamel Husain、Shreya Shankar，跨越 2024–2026 年四篇文章的提炼。核心方法论：以 **error analysis**（错误分析）为中心——不从抽象指标出发，而是从真实失败案例出发，归纳失败模式，再针对性设计评估维度。包含断言层（Assertions）、LLM-as-Judge 校准方法、以及多层评估覆盖的操作细节。本组必读首篇。
- [[2026-02-15 - OpenAI Cookbook Eval驱动系统设计方法论]] — 来源：Shikhar Kwatra（OpenAI Cookbook）。将评估驱动开发落地为可操作的实验设计：如何用「证据链」替代「感觉」，如何构建最小可验证的 Eval 循环，如何建立系统变更与性能变化之间的可复现关联。与 Hamel 方法论形成互补——Hamel 侧重评估体系设计，OpenAI Cookbook 侧重迭代流程设计。

## 特定场景诊断

通用评估框架在 RAG 和 Agent 工作流上需要专门适配——这两类系统的失败模式与诊断方法都不同。

- [[2026-02-14 - Hamel Husain RAG与Agent工作流评估分步诊断方法]] — 来源：Hamel Husain、Shreya Shankar。RAG 评估分两阶段：检索阶段（IR 指标：召回率、精确率、MRR）和生成阶段（语义一致性、幻觉率、引用准确率）。Agent 工作流评估使用「转换失败矩阵」（Transition Failure Matrix），逐步骤分析失败发生在哪个状态转换节点。是诊断 RAG/Agent 问题时最直接可用的参考。
- [[2026-02-08 - Agent评估方法论与抗AI评估设计]] — 来源：Anthropic（Mikaela Grace, Jeremy Hadfield, Tristan Hume）。解决一个更难的问题：当被评估的模型越来越聪明，它会开始「学会」通过评估而不是「真正做好任务」——即 Eval Saturation（评估饱和）。提出 Swiss Cheese Model（多层评估叠加，每层有不同盲点）和抗 AI 评估设计的原则，是长期维护评估体系的必读参考。
- [[2026-03-11 - Anthropic skill-creator Eval 框架的设计与使用方法]] — 来源：Anthropic。将软件单元测试范式引入 Skill 开发：通过结构化测试用例和 with-skill/baseline 并行对比，量化验证 Skill 是否真正有效。是评估驱动开发在具体工具（Claude Code Skills）中的可操作实现。

## 数据集构建

好的评估依赖好的测试集。测试集来自哪里？如何确保它覆盖了真实系统行为的足够多样性？

- [[2026-02-14 - Hamel Husain 合成数据驱动的评估数据集构建流程]] — 来源：Hamel Husain、Shreya Shankar。核心方法：通过场景分类（Scenario Taxonomy）系统枚举评估维度，再用 LLM 生成合成样本填充每个场景桶，最后用人工验证确保合成数据的真实性。关键洞察：合成数据不是「造假」，而是用可控的方式生成真实系统在边缘场景下可能遭遇但在真实流量中罕见的案例。

## 陷阱与误区

知道「正确做法」还不够——同样重要的是知道哪些「看起来合理」的做法实际上是错的。

- [[2026-02-13 - 产品级LLM评估的常见陷阱与误区]] — 来源：OpenAI, Anthropic, Google, Braintrust, Hamel Husain, ACL 综合（2024–2026）。七类高频错误：用 LLM-as-Judge 但没有校准 Judge 本身的偏差、用平均分掩盖尾部失败、评估集与训练集泄露、过早固化评估维度（导致评估体系无法随产品演化）等。可直接用作项目评估设计的反向 checklist。
- [[2026-04-06 - Hamel Husain 评估复位与数据科学价值]] — 来源：Hamel Husain。将“API 化并未替代评估工程”具体化为五类执行坑：通用指标偏差、未验证 judge、实验设计缺口、标注失真与过度自动化。
- [[2026-04-04 - AI代理决策偏差与机器消费者心理]] — 作者：Dexter。把 LLM-as-a-judge 的偏差问题从评测场景推进到商业决策场景：来源标签、机器风格、位置顺序与 sponsored 信号都会系统性影响模型判断，说明“让 AI 评估”本身也是需要被评估的对象。

## 多模态延伸

当 Agent 系统涉及语音和图像输出时，文本评估框架需要专门适配，否则会产生严重的评估盲区。

- [[2026-02-08 - 语音与图像评估的Gate-Grade框架与分阶段建设]] — 来源：OpenAI Cookbook。语音评估维度（自然度、情感一致性、发音准确率）与图像评估维度（视觉一致性、美学质量、语义对齐）的构建方法。Gate-Grade 框架：先做二元门控（是否可接受），再做细粒度打分（哪个维度好）。Crawl-Walk-Run 框架：按评估复杂度分阶段建设多模态评估能力。
- [[2026-02-14 - LLM输出一致性与召回率最大化]] — 作者：Dexter，基于并行研究 Agent 成果整合。将「一致性」重新定义为「跨次调用的高召回率稳定性」，而非「每次输出完全相同」。提出三类实操策略：搜索接地（减少幻觉）、多路径并行采样（提高召回率上限）、输出模板化（降低格式方差）。

## 相关 Map

- [[Topic - Agentic AI 系统构建]] — 评估方法在工程架构中的定位：Eval 驱动开发作为系统设计的首要原则

## Canonical Nodes

- [[2026-02-14 - Hamel Husain LLM应用评估体系原理与操作方法]]
- [[2026-02-14 - Hamel Husain RAG与Agent工作流评估分步诊断方法]]
- [[2026-02-15 - OpenAI Cookbook Eval驱动系统设计方法论]]
- [[2026-02-13 - 产品级LLM评估的常见陷阱与误区]]

## 覆盖缺口

- 评估数据集如何随产品演化持续更新，目前只有原则性材料，缺少长期维护 SOP
- 面向中文内容与商业判断任务的 judge calibration 经验仍未单独沉淀
