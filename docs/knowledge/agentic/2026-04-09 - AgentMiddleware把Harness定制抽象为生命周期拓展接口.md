---
type: source
author: Sydney Runkle
published: 2026-03-26
source_url: https://blog.langchain.com/how-middleware-lets-you-customize-your-agent-harness/
topics:
  - "[[agent middleware]]"
  - "[[agent harness]]"
  - "[[harness engineering]]"
  - "[[LangChain]]"
  - "[[Deep Agents]]"
created: 2026-04-09
updated: 2026-04-10
---

# AgentMiddleware把Harness定制抽象为生命周期拓展接口

## 一句话简介

这篇文章将 Agent Middleware 定义为围绕 agent harness 核心循环布设的一组 hooks，使开发者无需重写 harness，也能在模型调用、工具执行与任务生命周期各阶段插入确定性策略、业务逻辑与生产化控制。

## Takeaway

1. **文章的核心主张不是“再造一种 agent 框架”，而是把 harness 定制接口标准化**：真正困难的不是替换 prompt 或 tools，而是修改核心循环；middleware 让这类修改从“改框架”变成“通过生命周期拓展接口插入控制逻辑”。
2. **middleware 的价值在于把应用方真正需要的控制点显式化**：输入校验、PII 处理、动态选工具、上下文压缩、重试、人工介入、资源初始化与清理，都被放到可组合的生命周期节点上。
3. **LangChain 试图把 production agent 的关键能力从 prompt 技巧转成系统机制**：合规、上下文管理、重试与 tool gating 在文中都被描述为确定性工程问题，而不是提示词问题。
4. **Deep Agents 被呈现为一个建立在 `create_agent` 之上的“带默认中间件栈的 harness”**：LangChain 借此说明 middleware 不只是扩展点，也是构建更高层 harness 的基础抽象。
5. **这篇文章的长期价值在于抽象层，不在于具体内置 middleware 名单**：hook 体系作为控制平面相对稳定；具体 middleware、文档链接与产品边界则具有明显时效性。

---

## 摘要

### Agent harness 的最小定义

作者首先把 agent harness 定义为连接模型、环境、数据、记忆与工具的系统，而其不可约核心非常简单：模型在循环中调用工具。`create_agent` 被定位为对这条最小循环的抽象，而不是预先塞满各种策略的厚重框架（Sydney Runkle, 2026-03-26）。

> "LLM, running in a loop, calling tools."

这一铺垫的作用是先把“什么属于 harness 的核心”讲清楚，再引出“哪些定制不该通过重写核心来完成”。

### 为什么 LangChain 认为需要 middleware

文章区分了两类定制难度。系统提示词与工具列表的调整相对直接，`create_agent` 已允许用户传入 system prompt 与 tools；但凡是会改变核心循环行为的需求，例如在每次模型调用前执行额外步骤、在工具结果出来后做统一检查、在任务开始或结束时处理外部资源，都会迅速变成“改 harness 内核”的问题（Sydney Runkle, 2026-03-26）。

作者据此提出 `AgentMiddleware`：不是重新发明 agent，而是在现有 harness 上暴露一组前后置与包裹式 hooks，使开发者能在不放弃底层基础设施的前提下实现应用级定制（Sydney Runkle, 2026-03-26）。

### Hook 模型如何覆盖整个 agent 生命周期

文章给出的 middleware 生命周期有六个关键节点（Sydney Runkle, 2026-03-26）：

- `before_agent`：在一次 invocation 开始时运行一次，适合加载记忆、连接资源、校验输入
- `before_model`：在每次模型调用前执行，适合裁剪历史、过滤 PII、重写上下文
- `wrap_model_call`：完整包裹模型调用，适合缓存、重试、动态模型请求、工具绑定调整
- `wrap_tool_call`：完整包裹工具执行，适合注入上下文、拦截结果、控制工具是否实际运行
- `after_model`：模型返回后、工具执行前运行，适合 human-in-the-loop
- `after_agent`：一次任务完成后运行一次，适合保存结果、发送通知、清理资源

作者明确强调 middleware 是可组合的，因此 LangChain 试图把“agent 定制”表述为“在一条固定核心循环周围组合多个控制逻辑”，而不是“针对每种需求重做一套 agent executor”（Sydney Runkle, 2026-03-26）。

### 常见定制需求被归纳为五类

文章将实际需求归纳为几个反复出现的簇（Sydney Runkle, 2026-03-26）。

第一类是**业务逻辑与合规**。作者认为这类要求不能只靠 prompt，因为它们本质上是必须稳定触发的确定性策略，例如 PII redaction 与 moderation。

> "You can't prompt your way to HIPAA compliance."

在这个语境下，文中用 `PIIMiddleware` 作为例子，说明可以在 `before_model` 与 `after_model` 等节点对输入、输出和工具输出做 mask / redact / hash，必要时抛出错误（Sydney Runkle, 2026-03-26；LangChain Docs，访问于 2026-04-09）。

第二类是**动态 agent 控制**。文中用 `LLMToolSelectorMiddleware` 说明，middleware 可以在 `wrap_model_call` 中先运行一个更快的模型，从工具注册表里挑选当前任务真正相关的工具，只把需要的工具绑定进主模型调用，以减少上下文膨胀（Sydney Runkle, 2026-03-26；LangChain Docs，访问于 2026-04-09）。

第三类是**上下文管理**。作者把摘要压缩与上下文卸载明确描述为运行时问题，而不是一次性 prompt 设计问题。`SummarizationMiddleware` 的例子说明，当消息历史超过 token 阈值时，可以在 `before_model` 阶段先做摘要；其扩展也可以在 `wrap_tool_call` 中把冗长工具 I/O 卸载到文件系统（Sydney Runkle, 2026-03-26；LangChain Docs，访问于 2026-04-09）。

第四类是**生产可用性**。作者把 retry、fallback 与 human-in-the-loop 归为 demo 中不显眼、但生产系统不可缺少的能力，并以 `ModelRetryMiddleware` 说明如何在 `wrap_model_call` 中对 API 请求加重试、退避与初始延迟等策略（Sydney Runkle, 2026-03-26；LangChain Docs，访问于 2026-04-09）。

第五类是**工具集与外部资源生命周期**。`ShellToolMiddleware` 的例子表明，有些工具不是静态函数，而是带初始化与 teardown 的运行时资源；此时 middleware 可以在 `before_agent` / `after_agent` 中管理 shell 等外部环境，并把工具注入模型可见工具列表（Sydney Runkle, 2026-03-26；LangChain Docs，访问于 2026-04-09）。

### Deep Agents 被用作中间件栈案例

文章用 Deep Agents 作为案例，说明 middleware 不只是零散扩展点，而可以上升为更高层 harness 的基础设施。作者称 Deep Agents 完全建立在 `create_agent` 之上，只是在其上叠加了一套更有主张的 middleware stack，包括 `FilesystemMiddleware`、`SubagentMiddleware`、`SummarizationMiddleware` 与 `SkillsMiddleware` 等（Sydney Runkle, 2026-03-26）。

这一段的含义是：LangChain 想把生态分成两层。底层是最小循环 `create_agent`；上层可以是带默认中间件栈的成品 harness。应用开发者既可以从 barebones harness 起步，也可以从 Deep Agents 这种更强主张的 harness 起步，再继续叠加自己的 middleware。

### 为什么 LangChain 押注 middleware

在收束部分，作者提出一个重要判断：模型能力会继续上升，因此今天由 middleware 处理的一部分事情，未来可能被模型本身吸收，例如摘要、工具选择、输出裁剪；但应用方对“可定制控制杆”的需求不会消失，尤其是确定性政策执行、生产守护逻辑与场景化业务规则（Sydney Runkle, 2026-03-26）。

因此，文章真正押注的不是某个具体 middleware，而是一个抽象前提：**只要 agent 仍然需要 harness，harness 就仍然需要暴露干预点；middleware 是当前最干净的暴露方式。**

---

## 参考链接

- [How Middleware Lets You Customize Your Agent Harness](https://blog.langchain.com/how-middleware-lets-you-customize-your-agent-harness/)
  - 作者：Sydney Runkle
  - 发布日期：2026-03-26

- [LangChain Agents 文档](https://docs.langchain.com/oss/python/langchain/agents?ref=blog.langchain.com)
  - 作者：LangChain Docs
  - 发布日期：N/A

- [LangChain Built-in Middleware 文档](https://docs.langchain.com/oss/python/langchain/middleware/built-in?ref=blog.langchain.com#llm-tool-selector)
  - 作者：LangChain Docs
  - 发布日期：N/A

- [PII Middleware 文档](https://langchain-5e9cc07a-preview-srimpr-1771619406-31dcf4f.mintlify.app/oss/python/langchain/middleware/built-in?ref=blog.langchain.com#pii-detection)
  - 作者：LangChain Docs
  - 发布日期：N/A

- [Deep Agents Harness Guide](https://docs.langchain.com/oss/python/deepagents/harness?ref=blog.langchain.com)
  - 作者：LangChain Docs
  - 发布日期：N/A

## 相关笔记

- [[2026-02-08 - 长时间运行Agent的上下文管理与弹性设计]]（同样讨论 agent harness，但聚焦长时间运行任务中的状态持久化与恢复）
- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]（同样讨论 harness，但聚焦 agent-first coding 的控制平面、文档结构与治理机制）
- [[2026-03-16 - Agent时代利润先集中于模型与Harness耦合层]]（将 harness 从工程实现问题上升为价值捕获层问题）
- [[Topic - Agentic AI 系统构建]]（纳入 agent harness、上下文管理与生产化实践的主题导航）
