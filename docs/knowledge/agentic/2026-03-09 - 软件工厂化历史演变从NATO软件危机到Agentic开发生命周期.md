---
type: source
author: 多源综合（McIlroy, Parnas, SEI, Greenfield/Short, Cusumano, Humble/Farley）
published: N/A
source_url: missing
topics:
  - software factory
  - software engineering history
  - CMM
  - continuous delivery
  - platform engineering
created: 2026-03-09
updated: 2026-03-09
status: active
canonical: false
---

# 软件工厂化历史演变从NATO软件危机到Agentic开发生命周期

## 一句话简介

软件行业从 1968 年 NATO 会议的"组件工厂"愿望，经 CMM、CASE 工具、软件产品线、DevOps 到 2026 年 Agentic SDLC，始终在解决同一问题：把不可预测的人类智力劳动转译为可度量、可复用、可持续改进的结构化系统。

## Takeaway

1. **CASE 工具的失败揭示了"规格说明"的底层矛盾**：让代码自动生成的前提是完备的规格说明，而写完备规格说明的认知成本往往高于直接写代码——这一矛盾在 2026 年因自然语言处理能力的跨越而首次被打破。
2. **工厂化的核心从未改变——改变的只是自动化对象**：从"让人遵守流程"（CMM），到"让代码遵守流水线"（DevOps），到"让 Agent 遵守 Harness"（Agentic），每一代工厂化都把上一代的人工干预变成自动约束。
3. **平台工程把"最佳实践"制度化为"黄金路径"**：这是 harness engineering 的制度前史——两者共同追求"让正确的事成为最省力的事"。

---

## 摘要

### NATO 1968：软件危机的工业化诊断

1968 年 NATO 软件工程会议是"软件工厂化"愿望的起点。[[M.D. McIlroy]] 在会议上提出一个核心诊断：软件行业像"自耕农（crofter）"，而非"工业化生产者（industrialists）"。硬件行业已有标准件目录，可按性能、鲁棒性、精度等维度选型；软件行业则缺乏类似的"组件市场"，每个项目都是从零开始的手工活。

McIlroy 的具体提案是建立"软件组件子产业"：像买电阻、螺丝一样购买标准软件例程，并能按规格选型。这次会议奠定了"软件工程（software engineering）"这一术语的语境：软件需要像工程学科一样被严格、系统地对待，而不是依赖个人天才。

### Parnas 1976：程序家族与变化的共性管理

[[David L. Parnas]] 在 1976 年提出"程序家族（program families）"概念：一组程序若共享某些属性并在其他方面有差异，应当作为"家族"来研究，提前设计其共性与变化点，避免每次都把项目当作完全独特的手工活。这是软件产品线思想的早期版本，核心洞察是：**管理变化的共性比管理单个项目的完美更重要**。

### CMM：把"英雄主义"变成可复制的过程

卡内基梅隆大学软件工程研究所（[[SEI]]）推动的能力成熟度模型（CMM，1990 年代系统化）将工厂化冲动引向"过程管理层"：

- **核心诊断**：很多组织依赖"英雄式努力（heroic effort）"，成功不可复用；软件方法与工具的收益在无纪律的项目中无法实现
- **解决路径**：建立组织级过程基础设施，让软件开发成为"可管理的、可度量的、可改进的"过程
- **权力转移**：从"写代码能力最强的人"转向"定义过程标准的人（过程改进专家）"

CMM 的隐含代价：初级开发者逐渐被视为"可替换的执行层"，议价能力下降。这是 Taylor 主义在软件行业的直接应用。

### CASE 工具时代：规格说明的认知代价

1990 年代，行业寄希望于 CASE（计算机辅助软件工程）工具：让开发者通过画图或高层规格自动生成代码。这一波工厂化以失败告终。

根本矛盾：**自动生成代码的前提是一套完备、无歧义的规格说明，而人类撰写这种规格的认知成本往往高于直接写代码**。当"规格即代码"的门槛比"写代码"更高时，工具失去了存在理由。

这一矛盾在 2026 年因自然语言理解能力的跨越式提升而首次被打破：Agent 现在能从不精确的自然语言意图中合理推导出完整实现，并通过测试反馈迭代修正。

### Greenfield/Short 框架：软件工厂的现代定义

[[Jack Greenfield]] 与 [[Keith Short]] 在 2000 年代讨论软件工厂时，将软件业的"匠人依赖（craftsmanship dependency）"定义为核心瓶颈：成本、上市时间与质量压力必然推动行业向更自动化、更可预测的生产方式演进。

他们的定义：软件工厂 = "模型驱动的软件产品线（model-driven product line）"——用领域建模语言捕获元数据，自动化生成产品家族成员，将"供给链与大规模定制（mass customization）"视为远景目标。

**软件产品线定义**：一组共享"受管控特性"的系统，从共同核心资产以规定方式开发——"一次设计，多次复用"的正式化框架。

### 连续交付：把部署变成例行事务

连续交付（Continuous Delivery）将工厂化对象从"写代码"扩展到"安全、快速、可持续地交付变更"：

> 把包括新功能、配置、修复、实验在内的各类变更，安全、快速、可持续地交到生产或用户手中，使部署成为可按需执行的"可预测例行事务"。

DORA 研究的关键发现：高绩效组织能**同时**在吞吐与稳定性上领先，两者不是零和；高绩效组通过自动化减少手工工作，把技术人员从低价值重复劳动中释放出来。

### 平台工程：把最佳实践制度化为"黄金路径"

平台工程（Platform Engineering）把 DevOps 最佳实践变成可重用的内部产品：

- 平台团队作为"内部供应商"，提供自助化接口
- "黄金路径（golden paths）"把正确的做法变成最省力的做法
- 目标：降低开发者认知负荷、把治理与安全前置到平台设计

这是 harness engineering 的制度前史：harness 对 Agent 的约束作用与"黄金路径"对开发者的引导作用，逻辑上完全同构。

### 连续性与断裂

各阶段的连续主线：**把不确定性转译为可检查的结构**（接口、规范、测试、指标、流水线）。

| 阶段 | 自动化对象 | 人的角色 | 核心瓶颈 |
|------|-----------|---------|---------|
| CMM 时代 | 编码规范与流程 | 严格执行者 | 沟通与人才差异 |
| DevOps 时代 | 环境、部署、反馈 | 自动化编排者 | 上线成本与稳定性 |
| Agentic SDLC | 逻辑实现、测试、自修复 | 环境设计师与意图定义者 | 规格说明与验收效率 |

断裂点：当 Agent 的生成能力提高到可以承担大量执行与验证时，工厂化重心从"让人遵守流程"转向"让系统让 Agent 遵守规则"。

---

## 参考链接

- NATO Software Engineering Conference, 1968 — M.D. McIlroy 发言记录
- Parnas, D.L. (1976). "On the design and development of program families"
- Carnegie Mellon SEI — Capability Maturity Model (CMM)
- Greenfield, J. & Short, K. — Software Factories（Microsoft Press, 2004）
- Cusumano, M.A. (1991). *Japan's Software Factories*
- Humble, J. & Farley, D. (2010). *Continuous Delivery*
- DORA State of DevOps Report（历年）

## 相关笔记

- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]（harness engineering 是软件工厂化历史的最新阶段）
- [[2026-03-09 - Taylor到Autor数字生产工厂化的权力迁移理论]]（历史演变背后的劳动过程理论支柱）
- [[2026-01-29 - 80% 问题 Agentic 编程时代的理解债务]]（CASE 工具失败的认知成本问题在 Agent 时代以 comprehension debt 形式重现）
- [[2026-03-01 - Compound Engineering软件工程复利方法论]]（Compound Engineering 是"经验复利化"的当代版本，与 CMM 的"过程资产化"同源）
