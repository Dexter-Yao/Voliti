<!-- ABOUTME: Voliti 运行时 harness 重组方案文档，定义基于 DeepAgent 的复用边界、会话配置、提示词装配、语义边界、记忆生命周期与重组路径 -->
<!-- ABOUTME: 本文面向实现与评审，强调尽量复用 DeepAgent 现有组件、模块和能力，并将当前运行时结构重组为更清晰的单一事实入口 -->

# Voliti Runtime Harness 重组方案

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
5. 在当前阶段，这四类定制优先落在现有文件与现有模块中；只有当重复度和复杂度真实超过阈值时，才考虑抽出新文件。

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

### 4.6 现有 sub-agent 实践

Voliti 当前已经有专门的图片生成 sub-agent：

1. [`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py) 中的 `witness_card_composer`
2. [`backend/src/voliti/tools/experiential.py`](../backend/src/voliti/tools/experiential.py) 中的图片生成能力

这说明：

1. DeepAgent 的 subagent 机制已经足以承载“边界清楚、目标单一”的专长任务。
2. Voliti 当前更应优先复用 subagent，而不是为类似需求发明新的系统层概念。
3. 这也反向说明，不是所有后台动作都应被设计成 agent；只有像图片生成这样职责单一、边界清楚的任务，才天然适合 subagent 形态。

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

### 6.5 当前阶段的文件策略

基于当前代码规模和真实复杂度，本方案增加一个明确约束：

1. 上述四类最小定制，当前阶段优先落在现有文件中。
2. 不以“概念完整”为理由提前新增文件。
3. 只有当某一项规则已经在多个现有文件中重复出现，并且继续内联会降低可读性时，才允许抽出独立文件。

当前更合理的落点是：

1. `SessionProfile`：先落在 [`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py) 相邻逻辑或现有会话相关模块。
2. Prompt Layering Policy：先落在 [`backend/src/voliti/middleware/base.py`](../backend/src/voliti/middleware/base.py) 与 [`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py) 的 helper 中。
3. Semantic Boundary Policy：继续扩展 [`backend/src/voliti/semantic_memory.py`](../backend/src/voliti/semantic_memory.py)。
4. Memory Lifecycle Policy：先落在 [`backend/src/voliti/middleware/journey_analysis.py`](../backend/src/voliti/middleware/journey_analysis.py)、[`backend/src/voliti/conversation_archive.py`](../backend/src/voliti/conversation_archive.py) 与相关 helper 中。

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

1. `get_session_profile(session_type)`
2. `assemble_prompt_layers(...)`
3. `classify_memory_path(path)`
4. `should_complete_session(...)`
5. `should_run_journey_analysis(...)`

注意：

1. 这些是 **产品语义 helper**。
2. 它们不是新 runtime。
3. 它们的职责是让已有 DeepAgent 装配点更清晰。
4. 在当前阶段，它们优先以内联 helper 或现有文件内小对象形式存在，而不是先抽成新模块。

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

当前已经落地的最小字段如下：

1. `session_type`
2. `system_prompt_name`
3. `memory_paths`
4. `enable_journey_analysis`

这组字段当前已经足以承载 `coaching` 与 `onboarding` 的已实现差异。更厚的 `tool_policy`、`completion_policy` 与 `slow_path_policy` 仍保留为后续扩展方向，但当前尚未做成 profile 字段。

### 9.3 当前两类 profile 的正式意图

| Session Type | 核心意图 | 关键约束 |
|--------------|----------|----------|
| `onboarding` | 建立初始关系、采集基础画像、完成进入长期教练前的必要状态 | 独立 thread、独立完成条件、默认不做 Journey 分析 |
| `coaching` | 承载长期行为对齐与持续教练 | 可消费长期语义记忆，可按策略消费 candidate signals，可显式检索 archive |

### 9.4 当前实现落点

`SessionProfile` 当前已经落在 [`backend/src/voliti/session_type.py`](../backend/src/voliti/session_type.py)，并由 [`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py) 消费。

当前已实现的效果是：

1. `create_coach_agent(...)` 不再散写 memory 列表，而是从 profile 推导。
2. `system_prompt` 名称由 profile 提供。
3. `JourneyAnalysisMiddleware` 的启停由 profile 中的 `enable_journey_analysis` 决定。
4. 当前 profile 仍是轻量配置对象，没有长成新的管理层。

## 十、提示词装配方案

### 10.1 设计原则

提示词装配不做成独立组件层，只做一个薄的 policy / helper。

### 10.2 装配位置

装配位置应继续依附于现有 middleware / system prompt 机制，尤其是 `before_model` 阶段内部。

也就是说：

1. 顶层生命周期不新增 phase。
2. prompt layering 是 `before_model` 内部的固定子流程。
3. 现有 `PromptInjectionMiddleware` 仍可继续复用。
4. 当前阶段不新增独立 prompt 装配文件，先在现有 middleware / helper 中收口。

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

当前 [`semantic_memory.py`](../backend/src/voliti/semantic_memory.py) 已经落地以下分类：

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

### 11.4 “候选信号”的正式定义

本文中的 `candidate_signal`，是指：

**从运行时事实中提炼出来、对 Coach 推理有帮助、但还不应被视为权威长期语义的派生判断。**

它与权威长期语义的关键区别是：

1. 它可过期、可重算、可被推翻。
2. 它可以进入当前提示词，但不能自动晋升为长期记忆。
3. 它的默认法律地位是“参考信号”，不是“稳定事实”。

典型候选信号包括：

1. Journey brief
2. pattern index
3. 隐性成就判断
4. 阶段性行为模式判断

### 11.5 候选信号的当前实现状态

当前系统里，候选信号已经处于**已落地 producer + 已落地注入消费 + 未完成 consolidation** 的中间状态。

当前真实存在的 producer 是：

1. [`backend/src/voliti/middleware/journey_analysis.py`](../backend/src/voliti/middleware/journey_analysis.py)

它当前会：

1. 读取 `/user/timeline/markers.json`
2. 读取 `/user/coach/AGENTS.md`
3. 尝试读取 `/user/derived/pattern_index.md`
4. 扫描近 30 天 ledger 中的 observation / state / LifeSign success
5. 生成 `Journey Analysis Brief`
6. 通过 `get_candidate_signal()` 将该 brief 暴露为显式 `candidate_signal`
7. 将该 brief 注入当前 invocation 的 system prompt

当前已持久化的只有：

1. `/user/derived/last_journey_analysis.json`

这个文件当前只承担 freshness marker 作用，不保存完整分析结果。

因此，当前候选信号链路的状态是：

1. 概念已成立
2. producer 已存在
3. 当前 invocation 的 consumer 已存在
4. freshness marker 已存在
5. 完整的持久化、promotion、过期与重算协议尚未形成

这意味着候选信号当前不是纯构想，但也不是完整端到端闭环。

## 十二、记忆生命周期方案

### 12.1 生命周期结构

Voliti 的记忆系统继续采用以下五段结构：

1. `Capture`
2. `Candidate Distillation`
3. `Injection`
4. `Consolidation`
5. `Observation`

### 12.2 五段链路的正式职责

| 阶段 | 当前输入 | 当前输出 | 当前主要落点 | 当前是否已有实现 |
|------|----------|----------|--------------|------------------|
| `Capture` | 用户消息、tool result、A2UI payload、runtime state、ledger events | 原始运行时事实 | thread / checkpoint、`/ledger/...`、tool envelope | 已有 |
| `Candidate Distillation` | markers、coach memory、ledger、近期行为片段 | candidate signals | 当前由 `JourneyAnalysisMiddleware` 产出 candidate signal 视图；freshness marker 落在 `/user/derived/...` | 已有 |
| `Injection` | 权威语义、候选信号、archive evidence、runtime evidence | 当前 invocation 的模型输入 | `system_prompt` + `memory` + middleware 注入 | 已有 |
| `Consolidation` | 本轮候选信号、显式确认的稳定结论、completion 结果 | promotion 判定、候选层 cleanup、freshness 约束 | 当前由 `MemoryLifecycleMiddleware` 占住 `after_agent` 落点，但尚未执行实际整理 | 已部分落地 |
| `Observation` | 上述全链路中的关键决策与结果 | trace、event、eval sample | logs / trace / metrics | 已有基础 |

这张表的重点是：Voliti 当前缺的不是某一层完全不存在，而是 **`Candidate Distillation` 与 `Consolidation` 之间缺少正式规则**。

### 12.3 当前已有实现与缺口

当前已经存在的部分：

1. `memory=` 的文件式长期记忆加载。
2. session / thread 历史。
3. `JourneyAnalysisMiddleware` 作为候选信号 producer。
4. archive retrieval 的显式检索。
5. summarization / compaction 机制。

当前尚未收口的关键缺口：

1. 候选信号何时真正执行 promotion 仍未落地。
2. 冲突、过期、重算与淘汰缺少统一执行策略。
3. `after_agent` 当前只占住 consolidation 落点，尚未执行真正整理。

### 12.4 当前阶段的正式实施策略

当前阶段应按以下原则实施，不新增后台 agent：

1. `Capture` 继续依附现有 runtime、ledger、tool envelope 与 archive access layer。
2. `Candidate Distillation` 继续优先依附现有 middleware 与 helper，尤其是 [`backend/src/voliti/middleware/journey_analysis.py`](../backend/src/voliti/middleware/journey_analysis.py)。
3. `Injection` 通过现有 `system_prompt`、`memory` 与 middleware 注入机制完成。
4. `Consolidation` 当前明确落在六个原子阶段中的 `after_agent`，并已由 `MemoryLifecycleMiddleware` 占住正式落点。
5. `Observation` 继续复用现有 trace / event 通道，不新建 observability 子系统。

### 12.5 Consolidation 的当前落位与职责切分

在当前阶段，`Consolidation` 更适合作为现有“六个原子阶段”中的策略动作，而不是独立 agent。

更合理的职责划分如下：

| 阶段 | 当前记忆职责 | 不应承担的职责 |
|------|--------------|----------------|
| `wrap_tool_call` | 捕获工具结果、规范化结构化证据、标记可供后续蒸馏的输入 | 直接写入长期语义 |
| `after_model` | 当前阶段保留候选提炼与会后整理的正式 hook 落点 | 直接 promotion 到权威语义 |
| `after_agent` | 当前阶段保留 consolidation 的正式落点，并承载 promotion policy | 重新装配本轮 prompt |

明确约束：

1. `before_model` 负责装配当前输入，不负责会后整理。
2. `after_model` 当前阶段不执行 promotion。
3. `after_agent` 是当前最合理的 consolidation 落点。

### 12.6 Promotion 规则的最小正式版本

在当前阶段，只有满足以下条件的内容才允许从候选层晋升为权威长期语义：

1. 它具有跨会话复用价值，而不是只对本轮成立。
2. 它对未来教练决策有稳定影响。
3. 它来自用户明确表达、结构化工具结果、或 Coach 的高置信判断。
4. 它不属于原始 transcript、archive excerpt、日志、debug 或临时环境状态。

以下内容当前一律不得直接 promotion：

1. archive retrieval 返回的 summary / excerpt
2. 未经确认的行为模式判断
3. Journey Analysis 的单次摘要文本
4. 仅对当前会话成立的计划、临时安排、一次性情绪或上下文说明

当前这些禁止规则已经由 [`backend/src/voliti/middleware/base.py`](../backend/src/voliti/middleware/base.py) 中的 `MemoryLifecycleMiddleware` 接到真实文件写入面。

当前实现的正式写入约束如下：

1. 目标路径若属于 `authoritative_semantic`，则默认拒绝直接写入。
2. 只有存在显式确认写入上下文时，才允许继续写入。
3. 当前确认上下文使用以下运行时字段：
   - `configurable.semantic_write_confirmed`
   - `configurable.semantic_write_source_kind`
   - `configurable.semantic_write_source_name`
4. 候选路径与 freshness marker 路径继续允许正常写入。

### 12.7 当前阶段需要修改的现有文件

当前不新增文件前提下，记忆生命周期相关实现应主要收口到以下现有文件：

1. [`backend/src/voliti/middleware/journey_analysis.py`](../backend/src/voliti/middleware/journey_analysis.py)
   用于 candidate distillation、freshness 与 prompt injection 的当前主路径。
2. [`backend/src/voliti/semantic_memory.py`](../backend/src/voliti/semantic_memory.py)
   用于统一权威 / 候选 / archive / runtime / observability 分类。
3. [`backend/src/voliti/agent.py`](../backend/src/voliti/agent.py)
   用于挂接 `after_agent` consolidation policy 的装配入口。
4. [`backend/src/voliti/conversation_archive.py`](../backend/src/voliti/conversation_archive.py)
   用于维持 archive source 的证据层定位。

### 12.8 什么时候才需要独立后台 agent

只有当 consolidation 具备以下特征时，才值得升级为独立后台单元：

1. 不应阻塞当前回复。
2. 需要跨多个会话或更长时间窗口运行。
3. 需要按时间或环境变化主动触发，而不是依附某次用户消息。
4. 需要在用户未发起会话时仍持续工作。

因此，当前阶段不建议引入独立 consolidation agent。

未来如果 foundation 文档中的环境感知构想，真正演化为“用户不发消息也持续运行的后台任务”，再考虑独立 cron / worker / agent 会更合理。

## 十三、Archive / Retrieval 方案

### 13.1 正式位置

archive / retrieval 在 Voliti 中的位置应保持如下：

1. `Runtime Session History` 是原始记录 canonical source。
2. `Conversation Archive Access Layer` 是规范化读取层。
3. retrieval 是显式 tool。
4. retrieval 结果只作为当前 invocation 的 runtime evidence。

### 13.2 当前真实链路

当前 archive / retrieval 主链已经存在，顺序如下：

1. [`backend/src/voliti/runtime_session_history_langgraph.py`](../backend/src/voliti/runtime_session_history_langgraph.py)
   负责把 LangGraph runtime history 暴露为 canonical source。
2. [`backend/src/voliti/conversation_archive.py`](../backend/src/voliti/conversation_archive.py)
   负责把原始记录规范化为 `Conversation Record`。
3. [`backend/src/voliti/conversation_retrieval.py`](../backend/src/voliti/conversation_retrieval.py)
   负责按 query / summary / excerpt 做检索与窗口整理。
4. [`backend/src/voliti/tools/conversation_archive.py`](../backend/src/voliti/tools/conversation_archive.py)
   作为显式 tool 暴露给 Coach。

这条链已经说明：Voliti 当前不缺 archive 基础设施，缺的是更严格的 product policy。

### 13.3 正式输入输出语义

archive retrieval 的正式输入应继续保持克制，只允许：

1. `query`
2. `window`
3. `detail_level`
4. `conversation_ref`
5. `time_hint`

archive retrieval 的正式输出应继续区分两种：

1. `summary`
   用于给 Coach 快速了解历史会话主题和结论。
2. `excerpt`
   仅在需要局部原文证据时返回围绕命中消息的有限窗口。

当前阶段的强约束：

1. `summary` 优先。
2. `excerpt` 必须保持小窗口。
3. retrieval 结果只在本轮作为 `runtime evidence` 使用。
4. retrieval 结果不得自动写入长期语义，也不得直接成为 candidate signal。
5. retrieval payload 当前已显式返回 `evidence_kind="archive_source"` 与 `usage="runtime_evidence"`。

### 13.4 实施上的明确要求

对后续代码重组，archive / retrieval 需要明确以下规则：

1. `Conversation Archive Access Layer` 只负责“读与规范化”，不承担语义判断。
2. `ConversationRetrievalEngine` 只负责“检索与窗口整理”，不承担长期记忆写入。
3. tool wrapper 只负责“暴露给 Coach 的调用界面与错误 envelope”，不承担 promotion。
4. prompt 装配阶段只把 retrieval 结果当作 `runtime evidence`。

### 13.5 为什么不能进一步做厚

如果 archive 再被做厚，最容易出现以下问题：

1. transcript 双写。
2. archive 与 semantic memory 混用。
3. retrieval 自动注入 prompt。
4. 长期判断被一次性历史细节绑架。

因此，这部分应坚持“显式、小窗口、摘要优先”的策略。

### 13.6 当前阶段需要修改的现有文件

当前不新增文件前提下，这一块的主要修改落点应是：

1. [`backend/src/voliti/conversation_archive.py`](../backend/src/voliti/conversation_archive.py)
2. [`backend/src/voliti/conversation_retrieval.py`](../backend/src/voliti/conversation_retrieval.py)
3. [`backend/src/voliti/tools/conversation_archive.py`](../backend/src/voliti/tools/conversation_archive.py)
4. [`backend/src/voliti/semantic_memory.py`](../backend/src/voliti/semantic_memory.py)
   用于保证 archive source 永远不被误判为权威长期语义。

## 十四、Journey Analysis 方案

### 14.1 正确位置

Journey Analysis 是一种慢路径候选洞察能力。

它应该：

1. 建立在现有 middleware / helper 上。
2. 写入 `/derived/...` 或等价候选路径。
3. 服务于推理参考，而不是直接写权威语义。
4. 当前主要 producer 是现有 `JourneyAnalysisMiddleware`，而不是独立后台 agent。

### 14.2 当前真实实现

[`backend/src/voliti/middleware/journey_analysis.py`](../backend/src/voliti/middleware/journey_analysis.py) 当前已经实现了以下流程：

1. 仅在异步 `awrap_model_call` 路径触发。
2. onboarding 会话跳过。
3. 通过 `/user/derived/last_journey_analysis.json` 做 3 天 freshness gate。
4. 读取：
   - `/user/timeline/markers.json`
   - `/user/coach/AGENTS.md`
   - `/user/derived/pattern_index.md`
   - 近 30 天 ledger 中的 observation / state / LifeSign success
5. 调用 summarizer 模型生成 `Journey Analysis Brief`
6. 通过与 DeepAgent memory / filesystem 相同的 backend factory 解析真实 backend
7. 将 brief 通过 `get_candidate_signal()` 暴露为显式候选信号视图
8. 将 brief 注入当前 invocation 的 system prompt

这说明 Journey Analysis 当前已经不是构想，而是部分落地的现有 producer。

### 14.3 当前实现的不足

当前实现仍有四个关键缺口：

1. `pattern_index.md` 有 reader，但未形成清晰 writer 路径。
2. 完整分析结果未持久化，当前只持久化 freshness timestamp。
3. 生成的 brief 当前虽已暴露为显式 candidate signal，但还没有统一 candidate signal store。
4. 没有正式的 promotion / expiration / cleanup 规则。

### 14.4 当前阶段的正式目标

Journey Analysis 在当前阶段不应被扩展成更大系统，而应聚焦收口以下四件事：

1. 明确它是 `candidate_signal` producer，而不是权威记忆 writer。
2. 明确它当前的输入来源与输出边界。
3. 明确它在 `SessionProfile` 中的启停条件。
4. 明确它与 `after_agent` consolidation 的关系。

### 14.5 与 Consolidation 的关系

Journey Analysis 当前更合理的协作方式是：

1. `JourneyAnalysisMiddleware` 负责生成候选 brief。
2. `after_agent` consolidation policy 当前已具备正式落点，但尚未执行该 brief 的真正整理逻辑。
3. 不允许 Journey Analysis 直接越权写权威长期语义。

### 14.6 不应承担的职责

Journey Analysis 不应：

1. 直接做长期权威记忆写入。
2. 被包装成新的独立系统层。
3. 成为默认必须注入的长期真相。
4. 在当前阶段演化成新的后台运行时框架。

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

本阶段已完成：

1. 引入轻量 `SessionProfile`
2. `session_type.py` 成为 profile 的唯一权威入口
3. [agent.py](/Users/dexter/DexterOS/products/Voliti/.worktrees/runtime-harness-control-plane/backend/src/voliti/agent.py) 已转为 profile-aware 的 prompt / memory / middleware 装配

### 16.3 Phase 2：提示词与语义边界收口

当前状态：

1. `semantic_memory.py` 的六分类已落地
2. retrieval payload 的 `archive_source` / `runtime_evidence` 语义已落地
3. Prompt Layering Policy 仍以现有装配规则存在，尚未单独抽成 helper

### 16.4 Phase 3：记忆生命周期与 policy 收口

当前状态：

1. `JourneyAnalysisMiddleware` 已收口为 `candidate_signal` producer
2. `MemoryLifecycleMiddleware` 已注册为正式 policy 落点
3. promotion 禁止规则已在 `edit_file` / `write_file` 写入面执行
4. `after_agent` 仍未执行真正 consolidation

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
7. `after_agent` consolidation 不阻塞主回复且不越权写入

### 17.2 必须具备的测试类型

1. backend unit tests：profile、prompt helper、memory boundary、completion policy
2. contract tests：iOS → backend → runtime / Store 的会话与 archive 链路
3. live integration：archive access、retrieval、tool wrapper
4. eval：distillation、injection、consolidation 三类记忆评估
5. middleware tests：`after_model` 与 `after_agent` 的职责边界

### 17.3 关键失败模式

需要重点防守：

1. candidate signal 被误当成权威长期记忆。
2. archive retrieval 被静默自动注入默认上下文。
3. onboarding / coaching 漂移成两套平行逻辑。
4. prompt helper 再次长成一堆散落字符串拼接。
5. Voliti 定制逻辑滑向第二套平行框架。
6. 候选信号被误当成完整长期记忆闭环，导致 write boundary 失真。

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
| 2026-04-11 | 补充最新讨论：明确候选信号的定义与当前实现状态、consolidation 在六阶段中的当前落位、环境感知升级条件、图片 sub-agent 对架构的含义，以及当前阶段优先不新增文件的策略 |
| 2026-04-11 | 同步当前实现状态：写入 `SessionProfile`、语义边界五分类、archive retrieval evidence 语义、Journey Analysis 候选信号接口与 `MemoryLifecycleMiddleware` 的最小 policy 落点 |
| 2026-04-12 | 收紧当前实现状态：`session_type` 改为 fail-closed；Journey Analysis 改为通过共享 backend factory 解析真实 backend；权威语义写入边界改为在文件写入面执行 |
