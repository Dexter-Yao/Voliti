<!-- ABOUTME: Voliti 运行时基础设施里程碑方案，定义本轮基础契约收敛的目标状态、实施工作流与验证要求 -->
<!-- ABOUTME: 本文负责实施路径与阶段控制，不承担运行时契约真相定义职责 -->

# Voliti 运行时基础设施里程碑

> 相关文档：
> 产品定位见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。
> 设计理念见 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。
> 系统结构见 [`03_Architecture.md`](03_Architecture.md)。
> 运行时契约见 [`06_Runtime_Contracts.md`](06_Runtime_Contracts.md)。
> 精确视觉规格见项目根目录 [`DESIGN.md`](/Users/dexter/DexterOS/products/Voliti/DESIGN.md)。

## 一、文档目的

本文不是缺陷清单，而是 Voliti 当前阶段的运行时基础设施里程碑方案。其职责是回答以下问题：

1. 为什么当前必须先收敛基础契约，而不是继续叠加功能。
2. 本轮基础设施里程碑要达到什么目标状态。
3. 需要按哪些工作流实施，哪些内容明确延后，哪些内容不纳入本轮。
4. 用哪些验证与风险控制手段，确保切换后系统不再继续制造静默失真。

本文不承担运行时真相定义。所有正式契约均以 [`06_Runtime_Contracts.md`](06_Runtime_Contracts.md) 为准。

## 一点五、命名实施约束

本轮实现必须优先使用供应商中立命名，避免把当前集成工具名称抬升为产品概念。

1. 产品层与契约层优先使用 `Runtime Session History`、`Conversation Archive Access Layer`、`Conversation Record`、`Semantic Memory Store`、`Trace Provider` 等中立术语。
2. `LangGraph`、`LangSmith` 等名称只出现在 adapter、client、integration 与运维说明中。
3. 后续新增代码、测试夹具与文档标题不得把供应商名直接写入领域对象名称。

## 二、里程碑定位

### 2.1 问题本质

本轮全库审查暴露的核心问题，不是若干独立 bug，而是以下基础事实尚未被系统稳定承载：

1. 谁是当前用户。
2. 哪些状态以后端为真，哪些状态只存在于设备本地。
3. Store、session、A2UI、错误封装、记忆分层是否由同一份契约约束。
4. 当系统失败或降级时，`Coach`、用户与开发者是否看到同一条可解释链路。

如果这些边界继续模糊，后续 Witness Card、Journey 分析、长期记忆、主动触达等能力都会建立在漂移数据之上。

### 2.2 本轮目标

本轮完成后，Voliti 应从“减脂场景下可运行但边界漂移的 Agent 应用”，进入“减脂场景下有清晰运行时真相、可持续扩展的长期教练系统”。

本文只对减脂场景负责，但所有底层设计均不得阻断未来扩展更多会话类型与长期行为对齐场景。

## 三、目标状态

### 3.1 共享真相

1. backend 是共享持久化真相的唯一权威来源。
2. iOS 本地数据只承担设备本地状态、缓存与投影职责。
3. 所有共享持久化访问都必须受稳定 `user_id` 约束。

### 3.2 运行时契约

1. Store 结构只有一套正式定义。
2. session type 由 backend 持有并校验。
3. A2UI 的合法性与一次性由服务端统一收口。
4. 错误封装对 `Coach`、用户与开发者均可解释，但技术细节只进入日志与 trace。

### 3.3 记忆系统

1. 运行时状态层、原始记录归档层、语义记忆层、可观测性层边界清楚。
2. 原始 transcript 默认不自动进入上下文，只能显式检索。
3. `Coach` 是语义记忆主写入者，后台分析只提供候选信号。

### 3.4 用户体验

1. 写操作触发关键契约错误时直接阻断，不再静默继续。
2. 读操作允许只读降级，但必须显式标记“缓存 / 非最新状态”。
3. 流式 assistant 输出在完成前均为临时态，不进入 durable 历史。

### 3.5 验证体系

1. backend、eval、iOS 至少各有一个稳定验证入口。
2. 跨端 contract fixture tests 覆盖关键契约与状态转换。
3. 至少一条真实纵向路径验证 iOS → backend → Store → iOS projection。

## 四、已接受的架构决策

本轮 CEO 审查已接受以下决策，并视为本里程碑的正式边界：

### 4.1 运行时契约与文档分工

1. 新增独立契约主文档 [`06_Runtime_Contracts.md`](06_Runtime_Contracts.md)。
2. [`03_Architecture.md`](03_Architecture.md) 只承担系统结构与数据流说明。
3. 本文负责实施路径、分期与风险控制。
4. `AGENTS.md` 与 `CLAUDE.md` 必须链接到新的文档分工。

### 4.2 身份与权限

1. 当前使用设备本地稳定匿名 ID 作为 `user_id`。
2. backend 严格校验 `user_id` 格式。
3. Reset 同时要求 `user_id` 边界和显式 destructive intent。

### 4.3 会话与中断

1. session type 由 backend 持有并校验。
2. 会话差异通过轻量 `session profile` 定义，而不是多套 agent 或厚重 registry。
3. A2UI payload snapshot 存于 backend 会话状态。
4. A2UI response 同时校验合法性与一次性。

### 4.4 错误与降级

1. 写操作 `fail closed`，读操作允许受控只读降级。
2. 错误使用结构化 envelope，并附可读说明。
3. 技术细节不进入 `Coach` 上下文，只通过 `debug_context_ref` 指向日志与 LangSmith。
4. 平台只对安全幂等的基础设施错误自动重试。

### 4.5 记忆系统

1. 将分层记忆架构纳入正式方案。
2. 原始记录只允许通过显式检索进入 `Coach` 上下文。
3. transcript retrieval 默认小窗口、摘要优先。
4. archive 默认异步 / 后置写入，不阻塞主对话路径。
5. 当前不单独设“本地私有数据层”，只区分后端权威数据与设备本地状态。

### 4.6 实施策略

1. 不设计长期兼容层；旧测试数据优先一次性迁移或清理。
2. 旧数据迁移 / 清理由 backend 提供一次性工具，不交给 iOS 运行时承担。
3. 本轮禁止新增 durable fallback；现有 fallback 必须可观测且有退出条件。
4. 本轮定位为基础设施里程碑，而不是一次性修补项目。
5. 迁移 / 清理脚本失败时，切换必须阻断，不允许带已知残留继续进入正式运行状态。

## 五、明确延后项

以下事项已被明确延后，不纳入本轮强制交付，但需要保留在后续待办中：

1. 可执行契约包。
2. 日志与 LangSmith 的系统化脱敏治理。
3. 关键失败模式 runbook。
4. 检索索引层。
5. 契约变更治理流程。

## 六、不纳入本轮的扩张项

以下方向已明确不纳入本轮范围：

1. 长期双协议兼容层。
2. 多垂类平台化 framing。
3. 重型 session registry / service / manager 体系。
4. 大而全的 deployment ceremony 与 cutover checklist。
5. 面向未来账号体系的多层身份抽象。

## 七、实施批次切分

当前总方案保持不变，但实现明确拆成两个连续批次，避免第一批落地重新滑回“大包提交”。

| 工作流 | Batch 1 | Batch 2 |
|------|---------|---------|
| A 身份边界与 Reset 约束 | 必做 | — |
| B Store 契约收口 | 必做 | — |
| C Session 与 A2UI 边界治理 | 必做 | — |
| D 错误处理与用户态收口 | 仅做阻断、只读降级、流式临时态、onboarding durable 完成态 | 补齐统一用户态状态覆盖与更完整错误呈现 |
| E 分层记忆架构落地 | 仅做文档定版与 archive 不阻塞主对话路径 | 落地显式检索、摘要优先、`Coach` 语义记忆主写入边界 |
| F 测试与验证链恢复 | 必做跨端 fixture tests、A2UI 一次性测试、迁移测试、API / integration 层最小 E2E | 继续扩展更高层 eval、长期回归集与后续 UI 自动化 |
| G 可观测性与文档对齐 | 必做文档分工、correlation id、少量事件名与字段底板 | 继续完善 LangSmith 闭环、runbook 与后续治理项 |

### 7.1 Batch 1 交付边界

Batch 1 只负责建立最小可信闭环，范围如下：

1. `user_id` 隔离与 Reset 边界。
2. Store 契约统一与 iOS 解包收口。
3. session type、A2UI snapshot、A2UI 一次性语义。
4. onboarding durable 完成态修复。
5. Store 分页与 cleanup 完整性。
6. 跨端 contract fixture tests。
7. API / integration 层最小纵向 E2E。
8. 文档分工、最小观测字段底板与 LangSmith 正式角色定义。

Batch 1 的 observability 只负责建立最小可关联闭环，不扩张为高基数数据采集系统。当前阶段只记录关键事件、最小字段底板与必要 debug refs，不在 Batch 1 记录大段原文、重复上下文或膨胀 payload。

### 7.2 Batch 2 承接边界

Batch 2 在 Batch 1 通过后继续承接以下内容：

1. 分层记忆架构的代码级落地。
2. transcript archive 的显式检索能力。
3. 更完整的用户态状态覆盖。
4. 更完整的 observability 闭环。
5. 更高层的 eval、回归与长期质量护栏。

### 7.3 实施落位表

为避免实现阶段平地新起 service / manager，本轮收口点优先落位到以下现有模块：

| 收口点 | 优先落位 |
|------|---------|
| `user_id` 解析与校验 | backend `agent.py` 相邻模块；iOS `Core/Network` |
| Store 文件封装值解包器 | iOS `Core/Network`；eval `store.py` 相邻模块 |
| Store 路径 / key 常量来源 | backend / eval 共用常量模块；iOS 对应 `Core/Network` 常量定义 |
| `session profile` | backend `agent.py` 相邻模块 |
| A2UI payload schema 与 snapshot 校验 | backend `a2ui.py` 相邻模块 |
| error envelope 构造 | backend 统一错误收口模块 |
| thread 选择与本地会话投影 | iOS `LangGraphAPI.swift` 与 `CoachViewModel.swift` |
| Store 同步与本地投影视图更新 | iOS `StoreSyncService.swift` |

约束如下：

1. 优先在现有目录与相邻模块内收口，不新增厚重 service、manager、coordinator 体系。
2. 如果某个收口点必须新建文件，应优先作为现有模块的轻量辅助模块，而不是新的抽象层。
3. eval 只补足与 backend 契约对齐所需的最小辅助代码，不复制完整运行时结构。

## 八、关键图示

### 8.1 A2UI interrupt / resume 状态机

```text
Coach 调用 A2UI 工具
  ↓
backend 生成 payload snapshot
  ↓
[INTERRUPT_OPEN]
  ├── 用户提交合法输入
  │     ↓
  │   backend 校验字段 + 枚举 + 范围 + 一次性
  │     ↓
  │   [CONSUMED] → 恢复会话
  │
  ├── 用户 reject / skip
  │     ↓
  │   [CONSUMED] → 恢复会话
  │
  ├── 重复提交 / 双击 / 旧响应晚到
  │     ↓
  │   [REJECTED_ALREADY_CONSUMED]
  │
  └── 非法字段 / 越界值 / 过期 interrupt
        ↓
      [REJECTED_INVALID]
```

### 8.2 多步写入与 completion marker 流程

```text
复合流程开始
  ↓
写入步骤 1
  ↓
写入步骤 2
  ↓
写入步骤 3
  ↓
写入 completion marker
  ↓
[COMPLETED]

任何中途失败
  ↓
[PARTIAL]
  ↓
重入时读取已有步骤
  ↓
从未完成处继续

约束：
- 没有 completion marker = 不算完成
- 本地不得用启发式 durable 补写“已完成”
```

### 8.3 状态与存储分层图

```text
                    +------------------------------+
                    | backend 权威持久化真相        |
                    | Store / session / completion |
                    +--------------+---------------+
                                   |
                                   | 同步 / 解包
                                   v
                    +------------------------------+
                    | iOS 本地投影视图与设备状态    |
                    | SwiftData / thread / draft   |
                    +--------------+---------------+
                                   |
            +----------------------+----------------------+
            |                                             |
            v                                             v
+------------------------------+          +------------------------------+
| 原始记录归档层               |          | 可观测性层                   |
| transcript archive           |          | logs / LangSmith / events    |
| 默认不 auto-load             |          | 不进入 Coach 默认上下文      |
+------------------------------+          +------------------------------+

约束：
- backend 是共享真相
- iOS 本地状态不是共享真相
- archive 不是默认 memory
- observability 不是产品记忆
```

## 九、实施工作流

### 工作流 A：身份边界与 Reset 约束

**目标**  
建立共享持久化访问的用户隔离边界，并为 destructive 操作加上明确意图约束。

**主要任务**

1. iOS 持久化设备本地稳定匿名 `user_id`。
2. 所有共享持久化请求统一附带 `configurable.user_id`。
3. backend 拒绝缺失或非法 `user_id` 的持久化访问。
4. Reset 仅清空当前用户命名空间，并清空会影响产品状态的本地状态。

**完成标准**

1. 两个不同 `user_id` 的设备互不可见。
2. Reset 不会影响其他用户数据。
3. Reset 后本地不残留 thread、缓存、草稿等污染后续状态的设备数据。

### 工作流 B：Store 契约收口

**目标**  
让 backend、iOS、eval 三端对 Store 结构只有一套理解。

**主要任务**

1. 落地用户级 namespace + 路径型 key + 文件封装值契约。
2. 为 Store 定义两个唯一收口点：文件封装值解包器、路径 / key 常量来源。
3. iOS 新增统一解包层，不再在业务函数中猜测结构。
4. 清理所有同步函数中的多套 value 假设与散落 key 硬编码。
5. 明确多步写入流程的 completion marker 模型。

**完成标准**

1. profile、chapter、dashboard、LifeSign、ledger 可按同一协议读取。
2. Store 项数超过 100 时，reset 与 sync 仍然完整。
3. backend、iOS、eval 均不再在业务逻辑中散写正式 Store key。
4. 旧数据迁移 / 清理工具具备专门测试。

### 工作流 C：Session 与 A2UI 边界治理

**目标**  
消除 onboarding / coaching 的线程错位，恢复 A2UI 服务端信任边界。

**主要任务**

1. backend 持有并校验 `session_type`。
2. 落地轻量 `session profile` 定义。
3. A2UI payload snapshot 进入 backend 会话状态。
4. A2UI response 增加合法性与一次性校验。
5. 修复 onboarding durable fallback 与错误 thread 加载问题。

**完成标准**

1. onboarding 与 coaching 的加载、发送、resume 使用同一套 thread 语义。
2. 非法 A2UI 输入、旧 interrupt、双提交流程均被稳定拒绝。
3. onboarding 完成态只由服务端完成标记驱动。
4. thread 选择失败时进入明确错误态，不做隐式 thread 回退。

### 工作流 D：错误处理与用户态收口

**目标**  
把错误从静默状态转为可解释、可恢复、可降级的运行时信号。

**主要任务**

1. 定义统一错误 envelope。
2. 区分自动重试错误与直接交还 `Coach` 的语义错误。
3. 明确写操作阻断、读操作降级策略。
4. 落地用户态状态覆盖图，统一 loading / empty / partial / stale / error / success。
5. 修复流式 assistant 临时态与 durable 历史之间的边界。

**职责边界**

1. backend 负责统一错误 envelope 与降级语义定义。
2. iOS 负责消费 backend 返回的稳定错误语义，并映射为用户可见状态。
3. `StoreSyncService` 只负责状态同步与投影视图更新，不得发明新的 durable fallback 或平行错误语义。
4. `CoachViewModel` 只负责会话态呈现与流式状态切换，不得自行写入新的 durable 完成态判定规则。
5. iOS 可以展示临时态、pending 态或 loading 态，但不得在 backend 成功写入前乐观写入 durable 投影视图。
6. backend 写接口成功后，durable 投影视图仍统一通过 `StoreSyncService` 的同步 / 解包路径刷新，不直接使用写接口返回值局部拼装。

**完成标准**

1. 错误不再以自由文本或静默 fallback 的形式散落。
2. `Coach` 能获得足够决策信息，但看不到技术细节。
3. 只读降级界面都会显式标记“缓存 / 非最新状态”。

### 工作流 E：分层记忆架构落地

**目标**  
把 transcript archive、语义记忆、运行时状态与 observability 正式分层。

**主要任务**

1. 定义四层记忆架构与访问边界。
2. 以 `Runtime Session History` 作为原始记录层的 canonical source，先落地 `Conversation Archive Access Layer`。
3. transcript retrieval 改为显式检索、摘要优先、小窗口读取。
4. `Coach` 作为语义记忆主写入者落地到实际存储边界。
5. 为权威语义记忆路径与候选信号路径建立单一分类入口，禁止把 ledger、derived 或 conversation archive 直接当作长期记忆。

**完成标准**

1. 原始记录默认不自动进入上下文。
2. 语义记忆不再与日志、原始 transcript 混桶。
3. 不引入 raw transcript 到长期 Store 的双写真相。

### 工作流 F：测试与验证链恢复

**目标**  
恢复跨端验证可信度，让本轮变更有稳定护栏。

**主要任务**

1. 修复 `eval` 默认 pytest 入口。
2. 引入跨端 contract fixture tests，并定义单一、版本化的共享 fixture 源。
3. fixture tests 覆盖关键状态转换，不止是解析。
4. 共享 fixture 测试与模型行为评估型 `eval` 明确分层，不共用职责。
5. A2UI 专测 replay / double-submit / old response。
6. 增加 API / integration 层最小纵向 E2E 路径。

**测试边界**

1. 共享 fixture 源服务于 Store、session、A2UI 等跨端契约一致性验证。
2. 共享 fixture 源必须版本化、静态、可读，Batch 1 不引入动态生成器。
3. 模型行为评估、dataset、evaluator、experiment 继续归属 `eval` 体系，不与跨端契约 fixture tests 混用。
4. `eval` 在 Batch 1 只承担与 backend 契约对齐所需的最小测试入口，不扩张为统一测试总线。
5. 共享 fixture 源的正式落点为仓库根级共享测试目录 `tests/contracts/fixtures/`，不放入 `eval/`、`backend/tests/` 或 iOS 私有测试目录。

**Batch 1 测试归属与执行矩阵**

| 测试层 | 负责内容 | 不负责内容 | 最小执行入口 |
|------|---------|-----------|-------------|
| backend `pytest` | `user_id` 校验、session profile 入口、A2UI 合法性与一次性、错误 envelope、迁移 / 清理脚本 | iOS 投影视图、模型行为评分 | `cd backend && uv run python -m pytest` |
| iOS 测试（`VolitiTests`） | Store 解包、thread 选择、onboarding completion marker 投影、流式临时态与 durable 边界、只读降级映射 | backend 内部契约判定、模型行为评分 | `xcodebuild test -project frontend-ios/Voliti.xcodeproj -scheme Voliti -destination 'platform=iOS Simulator,name=<simulator>' -only-testing:VolitiTests` |
| 共享 contract fixture tests | Store、session、A2UI 的跨端共享样例解析与关键状态转换 | Judge / Auditor / seed 驱动评估 | 由 backend、iOS、eval 各自测试入口消费同一份共享 fixture 源 |
| `eval` 的 Batch 1 pytest | pytest 收集稳定性、与 backend 契约对齐所需的最小辅助测试 | dataset、evaluator、experiment、模型行为优劣判断 | `cd eval && uv run python -m pytest` |
| API / integration 层最小 E2E | `onboarding completion` 主路径的 iOS → backend → Store → iOS projection 纵向链路 | 真实 UI 自动化、长流程视觉验证、A2UI 作为唯一纵向主路径 | 纳入 Batch 1 自动化命令集，作为 release gate 之一 |

**Batch 1 最小必跑命令**

1. `cd backend && uv run python -m pytest`
2. `cd eval && uv run python -m pytest`
3. `xcodebuild test -project frontend-ios/Voliti.xcodeproj -scheme Voliti -destination 'platform=iOS Simulator,name=<simulator>' -only-testing:VolitiTests`
4. 一条 API / integration 层最小纵向 E2E 命令，绑定 `onboarding completion` 主路径，覆盖 thread 选择、completion marker、Store 落盘、iOS projection 与无本地 durable fallback

**Release Gate**

1. backend `pytest` 全绿。
2. `eval` 的 Batch 1 `pytest` 入口可稳定收集并通过。
3. iOS `VolitiTests` 覆盖本轮涉及的投影与会话边界并通过。
4. 共享 fixture 源在 backend、iOS、eval 三端均被成功消费。
5. API / integration 层最小纵向 E2E 通过。

**完成标准**

1. `cd eval && uv run pytest` 可稳定收集与执行。
2. 至少一条 API / integration 测试以 `onboarding completion` 为主路径，覆盖 iOS → backend → Store → iOS projection。
3. backend、iOS、eval 从同一份共享 fixture 源消费契约样例。
4. 迁移 / 清理脚本具备专门测试。

### 工作流 G：可观测性与文档对齐

**目标**  
让日志、LangSmith 与文档系统同时回到可信基线。

**主要任务**

1. 统一 `correlation_id`。
2. 定义少量正式事件分类与最小字段标准。
3. 明确 LangSmith 作为正式观测入口之一的职责。
4. 修正文档失真点，完成契约主文档与架构文档分工。
5. 更新 `AGENTS.md`、`CLAUDE.md` 的文档入口。

**执行约束**

1. 用户触发链路的 `correlation_id` 由 iOS 在请求边界生成。
2. backend 对客户端传入的 `correlation_id` 只做透传与复用，不在同一链路中重生新的主标识。
3. 仅内部异步任务、补写路径或后台流程在缺失时允许 backend 补生成新的 `correlation_id`。

**完成标准**

1. 关键运行时事件可通过同一 `correlation_id` 串联。
2. 关键事件名与字段底板稳定统一。
3. 文档中不再保留与当前目标架构相冲突的运行时叙述。

## 十、实施分期

### Phase 0：阻断继续污染

包含工作流：

1. A 身份边界与 Reset 约束
2. B Store 契约收口
3. C Session 与 A2UI 边界治理

退出条件：

1. 无合法 `user_id` 的持久化访问会被拒绝。
2. Store 只有一套跨端可解析结构。
3. A2UI 旧响应、重复提交与非法输入可被稳定拒绝。

### Phase 1：恢复运行一致性

包含工作流：

1. D 错误处理与用户态收口
2. E 分层记忆架构落地

退出条件：

1. 写操作失败不再静默继续。
2. 读操作降级有明确用户态表达。
3. transcript archive、语义记忆与 observability 不再混用。

### Phase 2：恢复验证与说明可信度

包含工作流：

1. F 测试与验证链恢复
2. G 可观测性与文档对齐

退出条件：

1. 关键跨端路径具备自动化验证。
2. LangSmith、结构化日志与事件名形成最小观测闭环。
3. 文档体系与目标架构一致。

## 十一、验证矩阵

| 验证项 | 目标 | 通过标准 |
|------|------|---------|
| 双用户隔离验证 | Store 不串读串写 | 两个不同 `user_id` 的设备互不可见 |
| Reset 边界验证 | 删除只作用于当前用户 | 当前用户命名空间清空，其他用户保留，本地产品状态缓存同步清空 |
| Store 契约验证 | 三端对同一 fixture 理解一致 | backend / iOS / eval 对同一共享 fixture 源中的 Store fixture 解析一致 |
| Onboarding 完成态验证 | 仅服务端完成才完成 | 无 completion marker 时本地不得 durable 完成 |
| A2UI 合法性验证 | 服务端拒绝非法字段和值 | 提交非法 key、越界值、非法枚举时返回错误 |
| A2UI 一次性验证 | 服务端拒绝重放与双提交 | 已消费、过期、旧 interrupt 均被拒绝 |
| 读降级提示验证 | 用户态不伪装为最新真相 | 缓存视图明确标记“缓存 / 非最新状态” |
| 流式消息验证 | 未完成输出不进入 durable 历史 | SSE 中断或离页后无空白 assistant 污染 |
| 迁移 / 清理脚本验证 | 一次性迁移可靠 | 空数据、混合数据、重复执行、重入、分页清理均通过 |
| 最小纵向 E2E 验证 | `onboarding completion` 主路径打通 | API / integration 层的 `onboarding completion` 全链通过，且 thread 选择、completion marker 与本地投影一致 |

## 十二、主要风险与控制策略

### 10.1 已接受的阶段性风险

1. 当前不建设长期兼容层，采用一次性切换。
2. 当前暂不做日志与 LangSmith 的系统化脱敏治理。
3. 当前暂不写关键失败模式 runbook。
4. 当前主要依赖测试结果，不再额外增加切换成功清单。

### 10.2 控制策略

1. 迁移 / 清理工具必须专测，不依赖人工小心。
2. 不允许新增 durable fallback。
3. 关键运行时动作必须带 `correlation_id`。
4. 关键事件必须具备固定事件名与字段底板。
5. LangSmith 必须能作为 trace / run / thread 级正式观测入口使用。
6. 迁移 / 清理脚本若出现部分失败、重入未完成或分页未清干净，均不得继续切换。

### 10.3 回滚原则

1. 不回滚到共享 namespace。
2. 不回滚到无 `user_id` 的持久化访问。
3. 不允许通过重新引入 durable fallback 解决切换问题。
4. 如发生问题，只能在解包层、迁移脚本或客户端投影视图层局部收敛，不得放弃后端权威边界。

## 十三、建议执行顺序

1. 身份边界与 Reset 约束
2. Store 契约收口
3. Session 与 A2UI 边界治理
4. 错误处理与用户态收口
5. 分层记忆架构落地
6. 测试与验证链恢复
7. 可观测性与文档对齐

执行逻辑如下：

1. 先切断继续污染数据的入口。
2. 再恢复会话、记忆与错误处理的一致性。
3. 最后让测试、日志与文档成为可靠信号，而不是事后补丁。

## 十四、完成判定

当且仅当满足以下条件时，本轮基础设施里程碑可视为完成：

1. 不同 `user_id` 之间的共享持久化数据完全隔离。
2. backend、iOS、eval 对 Store 契约理解一致。
3. session type 与 A2UI 一次性语义由 backend 稳定持有与校验。
4. onboarding durable 完成态完全由服务端完成标记驱动。
5. transcript archive、语义记忆、设备本地状态与 observability 不再混用。
6. 至少一条 API / integration 层最小端到端路径自动化验证通过。
7. 关键运行时事件可通过 `correlation_id`、事件名与 LangSmith trace 串联。
8. 文档体系与目标架构一致，不再保留关键运行时失真叙述。

## 十五、下一阶段承接方向

本轮完成后，Voliti 将具备承接以下下一阶段能力的基础：

1. 更丰富的 session type 组合。
2. 更稳定的长期记忆检索与使用。
3. 更强的 `Coach` 自恢复与错误自解释能力。
4. 更可靠的主动触达、Journey 分析与长期陪伴策略。
5. 更完整的 LangSmith dataset / evaluator / experiment 闭环。

这些方向不属于本轮交付项，但本轮若未完成，后续能力会继续建立在不可信的运行时边界之上。

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-09 | 初始创建：基于全库审查结果，定义仓库一致性整改目标、工作流、分期计划、验证矩阵与风险控制 |
| 2026-04-09 | 升级定位为运行时基础设施里程碑；新增契约主文档分工、分层记忆架构、LangSmith 观测职责、用户态状态覆盖与明确延后项 |
| 2026-04-09 | 文档重命名为 `05_Runtime_Foundation_Milestone.md`，统一文件名、标题与文档分工语义 |

## 附录：GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | 范围与战略判断 | 5 | Clean | 历次评审以 selective expansion 为主，已有多轮 scope proposal / accept / defer 决策记录 |
| Codex Review | `/codex review` | 独立第二视角 | 4 | Issues Found | 历次评审均发现需要补强的问题，说明跨层契约与实现细节仍是高风险区 |
| Eng Review | `/plan-eng-review` | 架构与测试 | 5 | Clean with Gaps | 多轮评审持续指出 critical gaps，主要集中在架构边界、验证链与实现收口 |
| Design Review | `/plan-design-review` | UI / UX 缺口 | 2 | Mixed | 一轮 clean，一轮 issues found，说明用户态交互与呈现路径仍需逐项校验 |
| DX Review | `/plan-devex-review` | 开发体验缺口 | 0 | — | — |

**VERDICT:** REVIEW HISTORY EXISTS。当前仓库相关规划已有多轮 CEO / Eng / Design / Codex 评审历史，本轮文档已按“基础设施里程碑”口径重新收口，并建议后续在实现前补一轮 `/plan-eng-review` 锁定执行级约束。
