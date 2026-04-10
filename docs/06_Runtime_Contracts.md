<!-- ABOUTME: Voliti 运行时契约主文档，定义跨端共享的权威数据边界、协议结构与可观测性底板 -->
<!-- ABOUTME: 本文只描述运行时真相与契约，不承担整改排期、实施历史或版本叙事职责 -->

# Voliti 运行时契约

> 相关文档：
> 产品定位见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。
> 设计理念见 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。
> 系统结构见 [`03_Architecture.md`](03_Architecture.md)。
> 基础设施实施路径见 [`05_Runtime_Foundation_Milestone.md`](05_Runtime_Foundation_Milestone.md)。

## 一、文档职责

本文是 Voliti 运行时契约的唯一权威来源，负责定义以下内容：

1. 共享持久化真相由谁持有。
2. backend、iOS、eval 必须共同遵守的数据结构与协议边界。
3. 用户身份、会话类型、A2UI、错误信号、记忆分层、可观测性字段的正式定义。
4. 用户可见状态与运行时状态之间的最小映射。

本文不承担以下职责：

1. 不描述具体整改分期、执行顺序与风险管理。
2. 不承担系统结构总览、部署拓扑与技术选型说明。
3. 不记录历史版本叙事；变化仅进入文末变更记录。

## 二、命名约束

运行时契约、实现代码与文档必须优先使用供应商中立命名，避免把当前集成工具的品牌或内部字段抬升为产品概念。

### 2.1 推荐术语

| 产品 / 契约术语 | 含义 |
|------|------|
| `Runtime Session History` | 运行时原始会话来源，承载 thread / checkpoint 等价语义 |
| `Conversation Archive Access Layer` | 对运行时原始会话的规范化读取层 |
| `Conversation Record` | 稳定、供应商中立的归一化会话记录视图 |
| `Semantic Memory Store` | 跨会话长期语义记忆层 |
| `Trace Provider` | 可替换的 trace / run 观测后端 |
| `Runtime Checkpoint Reference` | 指向底层运行时 checkpoint 的稳定引用 |

### 2.2 命名规则

1. 产品与契约层不得直接使用 `LangGraph`、`LangSmith` 等供应商名作为领域对象名称。
2. 供应商名只允许出现在 adapter、client、integration 或运维说明中。
3. 供应商特定字段进入产品层时，必须先映射为中立命名，例如 `runtime_checkpoint_ref`、`trace_ref`。
4. retrieval、archive、memory、trace 四类对象不得在命名上互相替代。

## 三、文档分工

| 文档 | 职责 |
|------|------|
| [`03_Architecture.md`](03_Architecture.md) | 系统结构、组件关系、数据流、部署与测试视图 |
| [`05_Runtime_Foundation_Milestone.md`](05_Runtime_Foundation_Milestone.md) | 基础设施里程碑的目标状态、实施工作流、验证矩阵与风险控制 |
| `AGENTS.md` / `CLAUDE.md` | 代理协作入口、工具链与仓库级工作约束 |
| 本文 | 运行时契约、权威边界与跨端统一语义 |

补充约束：

1. 跨端 contract fixture tests 必须消费同一套版本化共享 fixture 源。
2. 共享 fixture 源只服务于运行时契约一致性验证，不等同于 `eval` 中面向模型行为的 dataset、evaluator 或 experiment 体系。
3. 共享 fixture 源的正式目录为仓库根级 `tests/contracts/fixtures/`，不归属 backend、iOS 或 `eval` 任一端私有测试目录。

## 四、权威数据模型

### 4.1 共享持久化真相

Voliti 的共享持久化真相由 backend 持有，并落于 LangGraph Store。凡是构成以下任一语义的数据，均属于共享持久化真相：

1. 用户身份边界下的长期语义记忆。
2. 会话类型与会话完成态。
3. A2UI 中断与消费状态。
4. 需要跨会话、跨恢复路径保持一致的业务状态。

### 4.2 设备本地状态

设备本地状态仅存在客户端，用于承载设备能力、界面投影或临时过程，不构成共享持久化真相。当前典型范围包括：

1. UI 偏好与展示状态。
2. 系统权限状态。
3. 本地 thread 标识缓存。
4. 未提交草稿与临时输入缓冲。
5. 本地通知调度状态。

设备本地状态不得被误认为后端权威状态，也不得在未明确定义前自动上云。
客户端允许展示临时态、pending 态或 loading 态，但不得在 backend 成功写入前乐观写入 durable 投影视图。

### 4.3 版本字段策略

显式版本字段只存在于持久化边界，不进入所有瞬时协议。当前需要带版本信息的对象包括：

1. Store 文件封装值。
2. 一次性迁移或清理记录。
3. 必要的错误封装对象。

## 五、用户身份契约

### 5.1 `user_id` 来源

当前阶段的 `user_id` 由客户端生成并持久化为设备本地稳定匿名标识。未来如引入账号体系，应通过独立迁移策略完成身份合并，不在当前契约内预置多层身份模型。

### 5.2 `user_id` 约束

1. 所有共享持久化访问必须显式携带 `user_id`。
2. backend 对缺失或非法 `user_id` 的持久化访问直接拒绝。
3. `user_id` 必须满足统一格式校验，不允许自由字符串落入 Store 边界。
4. 客户端不得依赖 backend 默认共享 namespace。

### 5.3 Reset 契约

1. Reset 仅作用于当前 `user_id` 边界。
2. Reset 除 `user_id` 外，还必须携带显式 destructive intent。
3. Reset 清空所有会影响产品状态的设备本地状态。
4. Reset 不触碰系统级授权状态。

## 六、Store 契约

### 6.1 Namespace

统一 namespace 为：

```text
("voliti", user_id)
```

### 6.2 Key

统一 key 为路径型字符串。示例：

```text
/profile/context.md
/profile/dashboard-config.json
/chapter/current.json
/coping-plans/{plan_id}.json
/ledger/{yyyy-mm-dd}/{hhmmss}_{kind}.json
/timeline/markers.json
/coach/AGENTS.md
```

### 6.3 Value

统一 value 为文件封装结构：

```json
{
  "version": "1",
  "content": ["..."],
  "created_at": "2026-04-09T10:00:00Z",
  "modified_at": "2026-04-09T10:00:00Z"
}
```

约束如下：

1. `content` 是唯一承载业务正文的字段。
2. Markdown、纯文本、JSON 均先通过 `content` 还原，再由上层做二次解析。
3. 客户端不得把 Store `value` 直接当作业务对象。
4. 所有跨端解析都必须经过同一套文件解包逻辑。

### 6.4 唯一收口点

Store 在代码中只允许存在两个唯一收口点：

1. **文件封装值解包器**
   - 负责把统一 `value` 结构还原为文本或 JSON 载荷。
   - backend、iOS、eval 均必须复用该语义，不得在业务逻辑中直接猜测 `content` 形态。
2. **路径 / key 常量来源**
   - 负责定义 profile、chapter、timeline、coach memory、coping plans、ledger 等正式路径。
   - backend、iOS、eval 不得在业务逻辑中散写硬编码 key 字符串。

如果未来扩展新路径，必须先更新路径常量来源，再修改调用方。

### 6.5 持久化完成语义

涉及多步写入的流程一律采用“分步提交，最终完成标记最后写入”的模型。只有完成标记成功写入后，流程才视为完成。重入时必须支持幂等恢复。

## 七、会话契约

### 7.1 会话类型

`session_type` 由 backend 持有并校验。客户端可以选择和消费会话类型，但不能重定义会话身份。

当前文档只对减脂场景负责，已定义的核心类型包括：

1. `coaching`
2. `onboarding`

未来允许扩展更多类型，但扩展必须仍服从本文约束。

### 7.2 Session Profile

会话差异通过轻量 `session profile` 定义，而不是多套 agent 或厚重注册系统。每个 profile 至少定义以下内容：

1. 核心 prompt 注入规则。
2. 启用的 middleware 集。
3. 工具可见性与使用边界。
4. 需要读取或写入的状态范围。
5. 完成条件与完成标记。

### 7.3 最小代码形态

`session profile` 的唯一权威入口位于 backend。当前阶段只允许采用声明式配置对象或等价的轻量数据结构，不引入新的厚重 service、manager 或 registry 体系。

最小形态至少暴露以下稳定字段：

1. `session_type`
2. prompt injection policy
3. middleware set
4. tool policy
5. completion policy

约束如下：

1. backend 负责维护 profile 定义与运行时解释。
2. iOS 只能消费 backend 暴露出的稳定会话字段，不复制 profile 逻辑。
3. eval 只能基于同一份 backend 定义构造测试输入，不另起一套平行 profile 模型。
4. 任何会话类型扩展都必须优先修改 backend 的唯一 profile 入口，再扩散到客户端或评估。

### 7.4 客户端边界

1. onboarding 与 coaching 必须使用不同 thread。
2. 加载历史、发送消息、resume interrupt 必须使用同一套 thread 选择逻辑。
3. 本地不得以启发式消息数量写入 durable 完成态。
4. thread 选择失败时必须进入明确错误态，不允许隐式回退到其他 thread 或静默新建默认 thread。

## 八、A2UI 契约

### 8.1 Payload Snapshot

每次 A2UI interrupt 的原始 payload snapshot 存于 backend 会话状态。该 snapshot 是 resume 校验的唯一权威来源。

### 8.2 Resume 校验

resume 同时校验以下两类约束：

1. **合法性**
   - 提交字段必须来自当前 payload。
   - 枚举型输入必须命中服务端选项。
   - 数值型输入必须满足服务端范围与类型约束。
2. **一次性**
   - interrupt 必须处于当前有效状态。
   - 已消费、已过期或旧版本 snapshot 的提交必须被拒绝。
   - 双击提交、重复 resume、旧响应晚到均视为无效。

### 8.3 长期存储边界

原始 A2UI payload snapshot 不进入长期 Store。长期 Store 只保存该次交互真正产生的业务结果。

## 九、错误封装契约

### 9.1 目标

错误信息必须同时满足两类消费者：

1. `Coach` 需要足以做下一步判断。
2. 开发者需要足以追踪到底层执行链。

### 9.2 Error Envelope

统一错误封装至少包含以下字段：

```json
{
  "version": "1",
  "error_code": "store.contract.decode_failed",
  "retryable": false,
  "user_action_needed": false,
  "coach_message": "当前资料读取失败，我需要重新获取上下文后再继续。",
  "debug_context_ref": "corr_..."
}
```

约束如下：

1. `Coach` 只接收决策够用的信息。
2. 原始 provider 名称、HTTP 细节、内部路径、namespace、store key、interrupt id 等技术细节不得进入 `Coach` 上下文。
3. 幂等的基础设施错误可由平台自动重试。
4. 参数错误、校验错误、语义失败和可能重复执行的副作用错误直接返回 `Coach`。

### 9.3 读写失败策略

1. 写操作一律 `fail closed`。
2. 读操作允许受控只读降级。
3. 只读降级必须在用户界面显式标明“缓存 / 非最新状态”。
4. durable 投影视图只能由统一同步 / 解包路径刷新，不允许由客户端乐观补写。
5. 写接口成功只表示权威写入已完成，不授权客户端绕过同步 / 解包链直接拼装 durable 投影。

## 十、记忆分层契约

### 10.1 运行时状态层

用于承载当前执行周期内的临时状态，包括：

1. session profile
2. A2UI payload snapshot
3. interrupt 消费状态
4. 当前 thread 的运行态上下文

此层不构成长期语义记忆。

### 10.2 原始记录归档层

原始记录归档层的 canonical source 优先附着在 `Runtime Session History`，而不是首先复制到长期 Store。产品层必须先通过 `Conversation Archive Access Layer` 读取该层，再将其规范化为稳定的 `Conversation Record` 视图。

此层主要承载：

1. thread / checkpoint 等价的原始会话顺序。
2. interrupt、恢复、运行时任务等可追溯引用。
3. 按需回放、复盘与显式检索所需的原始来源。

约束如下：

1. 默认不 auto-load 给 `Coach`。
2. 只允许通过显式检索进入 `Coach` 上下文。
3. 默认检索小窗口、摘要优先。
4. 当前显式检索至少支持 `window=recent|all`，并允许用 `time_hint` 作为时间前缀过滤提示。
5. `excerpt` 必须返回围绕命中消息的有限片段，不得默认回传整段会话原文；当前实现以不超过 4 条消息为上限。
6. 不预设 raw transcript 双写到长期 Store；如未来增加派生摘要层，必须明确其从属于原始记录层，而不是成为第二份权威真相。

### 10.3 语义记忆层

用于保存长期教练关系所需的高信号记忆，例如：

1. 用户画像与偏好。
2. chapter、LifeSign、timeline markers。
3. 未来节日、行程计划等对长期陪伴有持续价值的信息。
4. `Coach` 明确认定并写入的长期语义结论。

`Coach` 是语义记忆主写入者。后台分析流程只生成候选信号，不直接改写权威语义记忆。

当前阶段，权威语义记忆路径至少包括：

1. `/profile/context.md`
2. `/profile/dashboardConfig`
3. `/chapter/current.json`
4. `/chapter/archive/{id}.json`
5. `/coach/AGENTS.md`
6. `/coping_plans_index.md`
7. `/coping_plans/{id}.json`
8. `/timeline/markers.json`

以下内容不属于权威语义记忆：

1. `/ledger/...` 等事件历史。
2. `/derived/...` 等候选信号与分析结果。
3. `Runtime Session History` 与 `Conversation Archive Access Layer` 提供的原始会话记录。

约束如下：

1. `Coach` 只能把跨会话仍有持续价值的结论写入权威语义记忆路径。
2. 原始事件、候选信号与会话归档只能作为证据来源，不得直接等同于长期语义记忆。
3. backend 的分析与中间件若产生候选信号，必须写入候选层，而不是直接覆盖权威语义记忆。

### 10.4 可观测性层

用于调试、排障、评估与回放，包括：

1. 结构化日志。
2. LangSmith traces。
3. 事件记录。
4. debug refs。

该层不等同于产品记忆，也不默认进入 `Coach` 上下文。

## 十一、用户态状态覆盖

当前必须统一覆盖以下用户态：

| 状态 | 说明 | 用户可见要求 |
|------|------|--------------|
| Loading | 正在等待远端真相或当前流式输出 | 可以显示进度，但不能伪装为完成 |
| Empty | 当前无数据或未开始该流程 | 明确说明为空，不显示陈旧占位 |
| Success | 已获取到权威结果 | 可正常交互 |
| Partial | 当前流程未完成，仅有临时态 | 不写入 durable 历史 |
| Stale | 当前仅展示缓存或降级视图 | 必须标记“缓存 / 非最新状态” |
| Error | 当前操作失败 | 不静默吞掉；若为只读降级，应保留可见状态说明 |

至少以下三条主路径必须按此表统一表达：

1. Coach 会话页
2. Onboarding 流程
3. Mirror / 历史投影视图

## 十二、可观测性最小契约

### 12.1 Correlation ID

关键运行时动作必须携带统一 `correlation_id`，至少贯穿以下链路：

1. iOS 请求
2. backend run
3. A2UI interrupt / resume
4. Store 关键写入
5. conversation archive access / retrieval
6. 错误封装
7. LangSmith trace

生成与透传规则如下：

1. 用户触发链路的 `correlation_id` 由 iOS 在请求边界生成。
2. backend 对来自客户端的 `correlation_id` 必须透传并复用，不得在同一链路中重生新的主标识。
3. 仅内部异步任务、补写路径或脱离客户端触发的后台流程，允许 backend 在缺失时补生成新的 `correlation_id`。

### 12.2 事件分类

关键路径必须使用固定事件名，而不是自由文本日志。事件名应保持少量、稳定、可搜索，例如：

1. `session.started`
2. `session.completed`
3. `a2ui.interrupt.created`
4. `a2ui.resume.rejected`
5. `store.write.completed`
6. `store.contract.decode_failed`
7. `conversation_archive.retrieval_failed`

### 12.3 最小字段标准

关键事件默认至少携带：

1. `correlation_id`
2. `event_name`
3. `result`
4. `user_id`
5. `session_type`
6. `thread_id`（如适用）
7. `error_code`（失败时）
8. `debug_context_ref`（失败时）

当前 Batch 1 的 observability 以“最小可关联”为原则，只记录关键事件和字段底板，不扩张高基数 payload、长文本原文或重复上下文。

### 12.4 LangSmith 角色

LangSmith 是 Voliti 的正式观测入口之一，负责：

1. run / trace / thread 级观测。
2. 与错误封装中的 `debug_context_ref` 形成追踪闭环。
3. 后续 dataset、evaluator、experiment 的评估闭环承接。

LangSmith 不替代结构化日志，也不替代 contract tests。

## 十三、延后项

以下事项已被明确延后，不属于当前契约强制交付：

1. 可执行契约包。
2. 全面日志与 LangSmith 脱敏治理。
3. 关键失败模式 runbook。
4. 检索索引层。
5. 契约变更治理流程。

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-09 | 初始创建：建立 Voliti 运行时契约主文档，定义身份、Store、会话、A2UI、错误、记忆分层、用户态与可观测性边界 |
| 2026-04-10 | 同步原始会话记录与观测契约：以 runtime history canonical source 与 retrieval 事件替代 archive 双写叙述 |
