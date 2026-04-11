<!-- ABOUTME: Voliti 运行时 harness 方案文档，定义基于 DeepAgent 的最小定制路径、复用边界、会话配置、提示词装配、语义边界与记忆生命周期 -->
<!-- ABOUTME: 本文面向实现与评审，强调尽量复用 DeepAgent 现有组件、模块和能力，不引入平行运行时框架 -->

# Voliti Runtime Harness 最小定制方案

> 相关文档：
> 产品定位见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。
> 设计理念见 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。
> 系统结构见 [`03_Architecture.md`](03_Architecture.md)。
> 基础设施里程碑见 [`05_Runtime_Foundation_Milestone.md`](05_Runtime_Foundation_Milestone.md)。
> 运行时契约见 [`06_Runtime_Contracts.md`](06_Runtime_Contracts.md)。

## 一、文档职责

本文回答以下问题：

1. Voliti 应如何基于 DeepAgent 构建长期教练场景的运行时 harness。
2. 哪些能力应直接复用 DeepAgent 现有组件、模块与扩展点。
3. 哪些产品语义必须由 Voliti 以最小定制方式补充。
4. `Session Profile`、提示词装配、语义边界、记忆生命周期、archive / retrieval 在系统中的正式位置是什么。
5. 下一步实现时，应先做什么，后做什么，如何避免增加长期技术负债。

本文不承担以下职责：

1. 不替代 [`06_Runtime_Contracts.md`](06_Runtime_Contracts.md) 的正式契约定义。
2. 不替代 [`05_Runtime_Foundation_Milestone.md`](05_Runtime_Foundation_Milestone.md) 的分期与风险控制。
3. 不引入独立于 DeepAgent 的平行运行时框架、第二套 middleware 框架或第二套 memory runtime。

## 二、执行结论

Voliti 的正确方向可以压缩成一句话：

**以 DeepAgent 作为唯一运行时底座，仅补最小的 Voliti 产品语义定制。**

这句话的工程含义如下：

1. DeepAgent 继续承担主要执行机制：模型循环、middleware 栈、backend、memory files、tools、subagents、summarization、thread / checkpoint 运行时能力。
2. Voliti 不再设计或实现平行的 harness framework。
3. Voliti 只补四类最小定制：
   - `SessionProfile`
   - Prompt Layering Policy
   - Semantic Boundary Policy
   - Memory Lifecycle Policy
4. 这四类定制优先落为轻量配置对象、helper 与 policy，而不是新的 manager、registry、orchestrator 或 runtime layer。

## 三、核心设计意图

### 3.1 设计目标

Voliti 需要的不是一个“更复杂的 Agent 系统”，而是一个：

1. 对用户只呈现单一 `Coach` 角色。
2. 对系统内部具有清楚边界与单一事实入口。
3. 能跨会话保持长期关系，但不被陈旧上下文绑架。
4. 能把 archive、semantic memory、candidate signals、runtime evidence 明确区分开的运行时结构。

### 3.2 非目标

本方案明确不追求以下目标：

1. 不追求自建通用 Agent framework。
2. 不追求把所有潜在能力抽象成可插拔平台。
3. 不追求在当前阶段引入第二套生命周期 taxonomy。
4. 不追求为未来所有场景预埋厚重扩展体系。

### 3.3 设计总原则

1. 正确性优先于灵活性。
2. 复用 DeepAgent 现有能力优先于新增抽象。
3. 先定义语义边界，再定义实现形态。
4. 先补单一事实入口，再补复杂流程。
5. 任何新增对象都必须回答：不用它是否会导致边界失真；如果不会，就不应新增。

## 四、当前系统真实基础

Voliti 当前并不缺底层能力。以下关键能力已经存在于代码中：

### 4.1 DeepAgent 装配入口

[`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py) 已经通过 `create_deep_agent(...)` 组装以下内容：

1. `model`
2. `system_prompt`
3. `backend`
4. `memory`
5. `tools`
6. `subagents`
7. `middleware`

这说明 Voliti 当前已经是在 **DeepAgent 的完整装配面** 上工作，而不是在其外侧套了一层自建执行器。

### 4.2 backend 分层

[`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py) 当前通过：

1. `CompositeBackend`
2. `StoreBackend`
3. `StateBackend`

实现了 `/user/` 持久化、其他路径临时化的基本分层。这已经足以支撑“长期语义 vs 运行时状态”的主干结构。

### 4.3 middleware 扩展点

Voliti 已经在使用 DeepAgent / LangChain 的 middleware 扩展机制：

1. [`backend/src/voliti/middleware/session_type.py`](../backend/src/voliti/middleware/session_type.py)
2. [`backend/src/voliti/middleware/journey_analysis.py`](../backend/src/voliti/middleware/journey_analysis.py)
3. [`backend/src/voliti/middleware/base.py`](../backend/src/voliti/middleware/base.py)

这说明会话差异、条件注入、慢路径分析都已经建立在现有扩展点上，而不是依赖新框架。

### 4.4 archive 与 retrieval

以下模块已经把“运行时原始记录”和“显式检索”主线初步拆开：

1. [`backend/src/voliti/runtime_session_history_langgraph.py`](../backend/src/voliti/runtime_session_history_langgraph.py)
2. [`backend/src/voliti/conversation_archive.py`](../backend/src/voliti/conversation_archive.py)
3. [`backend/src/voliti/conversation_retrieval.py`](../backend/src/voliti/conversation_retrieval.py)

这意味着 archive / retrieval 方向已经正确，关键在于进一步明确其政策边界。

### 4.5 语义边界 helper

[`backend/src/voliti/semantic_memory.py`](../backend/src/voliti/semantic_memory.py) 已经存在。这虽然还不够完整，但已经说明 Voliti 当前需要的主要不是新 memory 框架，而是更清晰的边界分类。

## 五、DeepAgent 应直接复用的能力

这部分是本方案最重要的前提。以下能力应明确视为 **直接复用**，不另造轮子。

### 5.1 执行循环

DeepAgent 已经提供：

1. 模型调用主循环。
2. tool calling。
3. middleware 调度。
4. subagent 集成。

Voliti 不应重写这部分。

### 5.2 backend 与持久化机制

DeepAgent / LangGraph 已经提供：

1. thread-scoped 运行时状态。
2. Store-backed 长期持久化。
3. checkpoint / history。
4. backend route 分流能力。

Voliti 不应实现第二套 state / store runtime。

### 5.3 context management 机制

DeepAgent 已经提供：

1. `system_prompt`
2. `memory=...`
3. `skills=...`
4. summarization / compaction
5. middleware 运行时注入

Voliti 需要的是 **如何使用这些机制**，而不是再做一个新的 prompt framework。

### 5.4 tool 与 subagent 面

DeepAgent 已经允许：

1. 自定义 tools
2. 自定义 subagents
3. tool-level middleware
4. human-in-the-loop interrupt

Voliti 的 A2UI、Witness Card、archive retrieval 都应继续保持在这个能力面上。

## 六、Voliti 必须补的最小定制

这部分是本方案真正要求新增的内容。它们之所以必要，不是因为 DeepAgent 缺少机制，而是因为 DeepAgent 不会替产品定义业务语义。

### 6.1 `SessionProfile`

这是最必要的一项。

原因：

1. DeepAgent 能承载 profile 的结果，但不会定义 `coaching` 与 `onboarding` 的业务语义。
2. 目前这些差异分散在 prompt、middleware、tests 与代码分支中。
3. 如果没有单一入口，后续每新增一种会话都会继续扩散复杂性。

最小要求：

1. 它必须是轻量配置对象。
2. backend 是其唯一权威入口。
3. 不得做成 registry、manager、service 或第二套 orchestrator。

### 6.2 Prompt Layering Policy

这项定制是必要的，但应保持很薄。

原因：

1. DeepAgent 已支持 system prompt、memory files 与 middleware 注入。
2. 但它不会替 Voliti 定义“哪类信息属于哪一层、谁优先、谁不能覆盖谁”。
3. Voliti 当前的提示词装配已经能做，但仍主要依赖散落约定。

最小要求：

1. 只定义分层与优先级。
2. 不单独引入新的 runtime phase。
3. 不做独立 prompt framework。

### 6.3 Semantic Boundary Policy

这是第二个必须补强的核心。

原因：

1. DeepAgent 能存、能读、能注入，但不知道哪些路径是权威长期语义。
2. 也不知道哪些是候选洞察、archive 证据、runtime-only evidence 或 observability。
3. 如果没有统一边界，系统会自然滑向 transcript、memory、derived signals 混写。

最小要求：

1. 继续扩展现有 [`backend/src/voliti/semantic_memory.py`](../backend/src/voliti/semantic_memory.py)。
2. 不新建 memory backend。
3. 让该 helper 成为单一分类入口。

### 6.4 Memory Lifecycle Policy

这项定制也是必要的，但重点仍是 policy，而不是 engine。

原因：

1. DeepAgent / LangGraph 已提供短期 state、长期 store、summarization、后台 consolidation 这些机制。
2. 但不会替 Voliti 决定什么时候写入、什么时候晋升、什么时候丢弃、什么时候只作为候选。
3. 这正是长期教练系统最关键的产品语义。

最小要求：

1. 定义生命周期规则。
2. 不新建第二套 memory runtime。
3. 优先通过 helper、middleware policy 和测试收口。

## 七、Voliti 不应新增的内容

这一节同样关键，因为它直接决定长期技术负债。

### 7.1 不新增第二套 harness framework

不应新增：

1. `Voliti Harness Builder Framework`
2. `HarnessExtension` 新体系
3. 第二套 lifecycle 框架

原因是这些抽象会直接与 DeepAgent 现有机制重叠。

### 7.2 不新增厚重会话管理层

不应新增：

1. `SessionRegistry`
2. `SessionManager`
3. 多层 profile service

Voliti 只需要一个轻量 `SessionProfile` 入口。

### 7.3 不新增平行 memory / archive 系统

不应新增：

1. 自建 semantic memory backend
2. transcript 双写到长期 Store
3. archive 复制式持久化

这些做法都会制造双份真相。

## 八、目标结构

Voliti 更合理的结构应表达为：

```text
create_deep_agent(
  model=...,
  system_prompt=...,
  backend=...,
  memory=...,
  tools=...,
  subagents=...,
  middleware=[
    session-aware behavior,
    journey analysis,
    tool policy,
    completion policy,
  ],
)
```

其上方只补少量 helper / policy：

1. `resolve_session_profile(session_type)`
2. `assemble_prompt_layers(...)`
3. `classify_memory_path(path)`
4. `should_complete_session(...)`
5. `should_run_journey_analysis(...)`

注意：

1. 这些是 **产品语义 helper**。
2. 它们不是新 runtime。
3. 它们的职责是让已有 DeepAgent 装配点更清晰。

## 九、Session Profile 详细方案

### 9.1 角色

`SessionProfile` 是 `session_type` 的唯一业务语义解释器。

它回答：

1. 这个会话要暴露哪些 prompt layers。
2. 这个会话启用哪些 middleware 行为。
3. 这个会话允许哪些 tools。
4. 这个会话可读写哪些 memory 类型。
5. 这个会话何时算完成。

### 9.2 最小字段

最小字段建议如下：

1. `session_type`
2. `prompt_layer_policy`
3. `middleware_policy`
4. `tool_policy`
5. `memory_policy`
6. `completion_policy`
7. `slow_path_policy`

这里不建议新增更多字段。原因是这些字段已经足够承载当前两类会话差异。

### 9.3 当前两类 profile 的正式意图

| Session Type | 核心意图 | 关键约束 |
|--------------|----------|----------|
| `onboarding` | 建立初始关系、采集基础画像、完成进入长期教练前的必要状态 | 独立 thread、独立完成条件、默认不做 Journey 分析 |
| `coaching` | 承载长期行为对齐与持续教练 | 可消费长期语义记忆，可按策略消费 candidate signals，可显式检索 archive |

### 9.4 实现落点

`SessionProfile` 最合理的落点，是 [agent.py](/Users/dexter/DexterOS/products/Voliti/.worktrees/runtime-harness-control-plane/backend/src/voliti/agent.py) 相邻的轻量模块，而不是新的目录层级。

## 十、提示词装配方案

### 10.1 设计原则

提示词装配不做成独立组件层，只做一个薄的 policy / helper。

### 10.2 装配位置

装配位置应继续依附于现有 middleware / system prompt 机制，尤其是 `before_model` 阶段内部。

也就是说：

1. 顶层生命周期不新增 phase。
2. prompt layering 是 `before_model` 内部的固定子流程。
3. 现有 `PromptInjectionMiddleware` 仍可继续复用。

### 10.3 五层结构

Voliti 仍建议采用五层提示词结构：

1. Voliti Core Prompt
2. Session-Specific Prompt
3. Authoritative Semantic Memory
4. Candidate Signals
5. Runtime Evidence

### 10.4 重点约束

这部分是执行上最关键的约束：

1. 当前用户最新意图优先级最高。
2. 当前会话内临时判断可覆盖长期默认值。
3. 长期权威语义只是默认背景，不是绝对命令。
4. candidate signals 只能作为参考，不得压过当前意图。
5. archive evidence 只作为证据，不自动改写长期记忆。

### 10.5 不应做的事

1. 不做独立 `PromptBuilder` 框架。
2. 不做新的 phase taxonomy。
3. 不把所有上下文处理逻辑都做成一个庞大对象。

## 十一、语义边界方案

### 11.1 边界分类

建议把现有 [`semantic_memory.py`](../backend/src/voliti/semantic_memory.py) 扩展为以下分类：

1. `authoritative_semantic`
2. `candidate_signal`
3. `archive_source`
4. `runtime_only`
5. `observability_only`

### 11.2 每类的正式含义

| 类型 | 含义 | 是否可直接进入提示词 | 是否可直接写入长期语义 |
|------|------|----------------------|------------------------|
| `authoritative_semantic` | 跨会话复用的稳定语义 | 是 | 是 |
| `candidate_signal` | 候选洞察、可重算、可过期 | 按 policy 控制 | 否 |
| `archive_source` | 原始会话记录与其规范化读取视图 | 仅显式检索后作为 evidence | 否 |
| `runtime_only` | 当前执行状态、当前工具结果、A2UI 中断态 | 仅当前 invocation | 否 |
| `observability_only` | trace、metrics、eval artifacts | 否 | 否 |

### 11.3 落地要求

1. 所有 path 分类都应统一走同一 helper。
2. prompt、journey、archive、completion、eval 不得各自维护一套分类暗规则。
3. 该 helper 只解释边界，不承担持久化职责。

## 十二、记忆生命周期方案

### 12.1 生命周期结构

Voliti 的记忆系统继续采用以下五段结构：

1. `Capture`
2. `Candidate Distillation`
3. `Injection`
4. `Consolidation`
5. `Observation`

### 12.2 当前已有的部分

当前系统已经有：

1. `memory=` 的文件式长期记忆加载。
2. session / thread 历史。
3. `JourneyAnalysisMiddleware` 产出候选分析。
4. archive retrieval 的显式检索。
5. summarization / compaction 机制。

### 12.3 当前缺失的正式规则

当前最需要补的不是新功能，而是规则：

1. 候选信号何时有资格晋升为权威语义。
2. 哪些信息只能保留在会话层，不得进入长期层。
3. archive 结果是否只作为当前证据。
4. 冲突、过期、重算与淘汰如何处理。

### 12.4 落地要求

1. 优先补 `MemoryLifecyclePolicy`。
2. 暂不引入新的 memory engine。
3. 暂不引入新的后台调度系统，除非现有慢路径已无法表达。

## 十三、Archive / Retrieval 方案

### 13.1 正式位置

archive / retrieval 在 Voliti 中的位置应保持如下：

1. `Runtime Session History` 是原始记录 canonical source。
2. `Conversation Archive Access Layer` 是规范化读取层。
3. retrieval 是显式 tool。
4. retrieval 结果只作为当前 invocation 的 runtime evidence。

### 13.2 为什么不能进一步做厚

如果 archive 再被做厚，最容易出现以下问题：

1. transcript 双写。
2. archive 与 semantic memory 混用。
3. retrieval 自动注入 prompt。
4. 长期判断被一次性历史细节绑架。

因此，这部分应坚持“显式、小窗口、摘要优先”的策略。

## 十四、Journey Analysis 方案

### 14.1 正确位置

Journey Analysis 是一种慢路径候选洞察能力。

它应该：

1. 建立在现有 middleware / helper 上。
2. 写入 `/derived/...` 或等价候选路径。
3. 服务于推理参考，而不是直接写权威语义。

### 14.2 不应承担的职责

Journey Analysis 不应：

1. 直接做长期权威记忆写入。
2. 被包装成新的独立系统层。
3. 成为默认必须注入的长期真相。

## 十五、观测与飞轮

Voliti 的 observability 不应长成第二套系统。它只需回答以下问题：

1. 某次行为为什么发生。
2. 哪一条 policy 影响了当前输出。
3. 哪些 prompt layer / candidate signal / archive usage 真正改变了结果。

建议保留的关键字段：

1. `session_type`
2. `session_profile`
3. prompt layer provenance
4. memory provenance
5. archive retrieval usage
6. completion decision
7. journey analysis marker
8. trace reference / correlation id

## 十六、分阶段实施方案

### 16.1 Phase 0：命名与契约切换

本阶段已完成：

1. `session_mode` → `session_type`
2. backend、iOS、tests、eval 的统一命名收口
3. 本地身份切换逻辑同步清理

### 16.2 Phase 1：Session Profile 收口

目标：

1. 引入轻量 `SessionProfile`
2. 让 [agent.py](/Users/dexter/DexterOS/products/Voliti/.worktrees/runtime-harness-control-plane/backend/src/voliti/agent.py) 从硬编码装配点转为 profile-aware 装配点

产出：

1. `SessionProfile`
2. `resolve_session_profile(...)`
3. profile-aware middleware / memory / tools 装配逻辑

### 16.3 Phase 2：提示词与语义边界收口

目标：

1. 落地 Prompt Layering Policy
2. 扩展 `semantic_memory.py`
3. 统一 authoritative / candidate / archive / runtime / observability 的解释口径

产出：

1. `assemble_prompt_layers(...)`
2. 完整的边界分类 helper
3. profile-aware prompt 装配规则

### 16.4 Phase 3：记忆生命周期与 policy 收口

目标：

1. 明确候选信号、长期语义、archive evidence 的生命周期规则
2. 把 completion、journey、archive gating 收口为明确 policy

产出：

1. `MemoryLifecyclePolicy`
2. `should_complete_session(...)`
3. `should_run_journey_analysis(...)`
4. archive retrieval policy

### 16.5 Phase 4：评估与飞轮接通

目标：

1. 固定 provenance 事件与 trace 字段
2. 接通 trace → eval → policy review 闭环

产出：

1. prompt / memory / completion provenance
2. 更稳定的 memory / journey / archive 评估基线

## 十七、验证与验收

### 17.1 必须验证的对象

1. `SessionProfile` 解析正确性
2. prompt layering helper 的顺序与优先级
3. `semantic_memory.py` 的边界分类准确性
4. archive retrieval 的显式 evidence 语义
5. candidate signal 不越权写入长期语义
6. completion policy 的 durable 标记正确性

### 17.2 必须具备的测试类型

1. backend unit tests：profile、prompt helper、memory boundary、completion policy
2. contract tests：iOS → backend → runtime / Store 的会话与 archive 链路
3. live integration：archive access、retrieval、tool wrapper
4. eval：distillation、injection、consolidation 三类记忆评估

### 17.3 关键失败模式

需要重点防守：

1. candidate signal 被误当成权威长期记忆。
2. archive retrieval 被静默自动注入默认上下文。
3. onboarding / coaching 漂移成两套平行逻辑。
4. prompt helper 再次长成一堆散落字符串拼接。
5. Voliti 定制逻辑滑向第二套平行框架。

## 十八、参考来源

### 18.1 官方资料

1. OpenAI, [Harness Engineering](https://openai.com/index/harness-engineering/)
2. OpenAI Developers, [Shell + Skills + Compaction: Tips for long-running agents that do real work](https://developers.openai.com/blog/skills-shell-tips)
3. OpenAI Cookbook, [Context Engineering for Personalization - State Management with Long-Term Memory Notes using OpenAI Agents SDK](https://developers.openai.com/cookbook/examples/agents_sdk/context_personalization)
4. OpenAI Cookbook, [Context Engineering - Short-Term Memory Management with Sessions](https://cookbook.openai.com/examples/agents_sdk/session_memory)
5. LangChain Docs, [Custom Middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
6. LangChain Docs, [Deep Agents Overview](https://docs.langchain.com/oss/python/deepagents/overview)
7. LangChain Docs, [Deep Agents Memory](https://docs.langchain.com/oss/python/deepagents/memory)

### 18.2 Dexter 知识库锚点

1. `Maps/Topic - Agentic AI 系统构建`
2. `Sources/2026-04-09 - AgentMiddleware把Harness定制抽象为生命周期拓展接口`
3. `Sources/2026-04-10 - OpenAI长程Agent的Skills、Shell、Compaction协同`
4. `Sources/2026-04-10 - OpenAI个性化记忆的状态分层与生命周期`
5. `Insights/2026-04-10 - 原始会话记录应附着运行时而非长期Store`
6. `Methods/2026-04-01 - 打造 AI Agent 员工的操作方法论`

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-11 | 初始创建：定义 Voliti 基于 DeepAgent 的最小定制方案，统一会话配置、提示词装配、语义边界、记忆生命周期与 archive 策略 |
| 2026-04-11 | 根据额外研究全面重写：明确 DeepAgent 为唯一运行时底座，收缩定制范围到 `SessionProfile`、Prompt Layering Policy、Semantic Boundary Policy 与 Memory Lifecycle Policy |
