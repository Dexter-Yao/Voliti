<!-- ABOUTME: Voliti 运行时契约主文档，定义跨端共享的权威数据边界、协议结构与可观测性底板 -->
<!-- ABOUTME: 本文只描述运行时真相与契约，不承担整改排期、实施历史或版本叙事职责 -->

# Voliti 运行时契约

> 相关文档：
> 产品定位见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。
> 设计理念见 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。
> 系统结构见 [`03_Architecture.md`](03_Architecture.md)。

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
| [`03_Architecture.md`](03_Architecture.md) | 系统结构、组件关系、数据流、部署与测试视图、技术选型与守护边界 |
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

`user_id` 是 LangGraph 运行时与 Store namespace 使用的应用级稳定身份标识。它必须来自受信任的应用边界，而不是来自任意前端输入。

当前约束如下：

1. 身份验证由 Supabase Auth 负责（邮箱+密码）。`user_id` 直接使用 Supabase Auth 的 UUID，无需额外映射层。
2. Next.js middleware 在验证 Supabase session 后，将 UUID 同步写入 `voliti_user_id` cookie，供客户端代码读取。
3. 服务端通过 `configurable.user_id` 向 LangGraph 运行时注入该 UUID。
4. 客户端只能消费已经解析完成的应用级 `user_id`，不能自行生成或重写共享持久化身份。

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

### 5.4 Supabase Auth 边界

1. Supabase Auth 负责账号注册、登录、密码重置、会话签发与失效。
2. Voliti backend 与 LangGraph runtime 只消费 Supabase UUID 作为 `user_id`，不直接依赖 JWT token 结构作为 Store namespace。
3. `configurable.user_id` 由 Next.js 服务端在受信任边界注入（middleware 验证 session → 设置 `voliti_user_id` cookie → 客户端读取并注入 `configurable`），不能由浏览器脚本自由拼装。
4. 若需要用户迁移或合并，必须通过显式迁移流程执行，不允许在运行时静默改写 namespace。

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
/profile/dashboardConfig
/goal/current.json
/goal/archive/{id}.json
/chapter/current.json
/ledger/{yyyy-mm-dd}/{hhmmss}_{kind}.json
/coach/AGENTS.md
/lifesigns.md
/timeline-calendar.md
/derived/briefing.md
/day_summary/{yyyy-mm-dd}.md
/conversation_archive/{yyyy-mm-dd}.md
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

当前实现采用 fail-closed 规则：

1. `configurable.session_type` 缺失时，请求直接失败。
2. `configurable.session_type` 非法时，请求直接失败。
3. backend 不允许静默回退到 `coaching`。

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
2. `system_prompt_name`
3. `memory_paths`

当前 backend 实现已按上述最小形态收口，会话差异通过同一 profile 入口驱动 `system_prompt`、`memory` 与 middleware 装配。

约束如下：

1. backend 负责维护 profile 定义与运行时解释。
2. iOS 只能消费 backend 暴露出的稳定会话字段，不复制 profile 逻辑。
3. eval 只能基于同一份 backend 定义构造测试输入，不另起一套平行 profile 模型。
4. 任何会话类型扩展都必须优先修改 backend 的唯一 profile 入口，再扩散到客户端或评估。

### 7.4 系统触发器

客户端在特定时机自动发送系统触发消息，Coach 根据触发器类型执行对应行为（A2UI fan_out）。

1. `[daily_checkin] {HH:MM}` — 当日首次创建 coaching thread 时由前端自动发送。包含用户本地时间，Coach 执行轻量状态收集（fan_out: 1-2 sliders + optional text_input）。
2. `[daily_review]` — 日终回顾触发器（当前保留定义，未实现自动触发）。

触发消息使用 `DO_NOT_RENDER_ID_PREFIX`，在消息列表中对用户不可见。

### 7.5 客户端边界

1. onboarding 与 coaching 必须使用不同 thread。
2. 加载历史、发送消息、resume interrupt 必须使用同一套 thread 选择逻辑。
3. 本地不得以启发式消息数量写入 durable 完成态。
4. thread 选择失败时必须进入明确错误态，不允许隐式回退到其他 thread 或静默新建默认 thread。
5. 桌面端在 `onboarding_complete: true` 成功写入前，必须保持 onboarding 专属全屏 surface，不得暴露标准 coaching workspace。
6. 标准 coaching workspace 包括历史栏、Mirror、设置入口，以及面向 `coaching` 的默认 thread 自动选择与挂载。
7. onboarding 判定未收敛前，客户端不得抢先挂载标准 workspace，也不得预先创建 `coaching` thread。
8. 桌面端 onboarding surface、thread 选择与 `session_type` 必须由同一已解析状态驱动，不得由彼此独立的本地启发式分别决定。
9. 设置页的补采入口属于 `Re-entry`，必须创建 `session_type: onboarding` 的独立 thread，并保持全屏 onboarding surface。
10. `Re-entry` 不得通过清空 `onboarding_complete` 或伪造 reset 达成；其 durable 前提是 profile 仍保持 `onboarding_complete: true`。

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

### 8.3 Reject Reason 语义

`reject` 响应可携带可选的 `reason` 字段，传递给 Coach 作为用户反馈。

约束如下：

1. `reason` 仅在 `action="reject"` 时有效。
2. `action="skip"` 和 `action="submit"` 的 `reason` 必须为 `null`。
3. `reason` 为可选字段（`null` 表示用户未提供理由）。
4. Coach 接收到的 `fan_out` 返回值包含 reason 原文（如 `"User rejected: 现在不方便回答"`）。

### 8.4 长期存储边界

原始 A2UI payload snapshot 不进入长期 Store。长期 Store 只保存该次交互真正产生的业务结果。

### 8.5 Surface 与 Intervention 分类

A2UI Payload 的 `metadata: dict[str, str]` 承载一条交互形态分类约定，供前端渲染层选择视觉外壳。

`metadata.surface` 取值（封闭集）：

| 取值 | 形态 | 使用方 |
|---|---|---|
| `"onboarding"` | 全屏引导采集 | Onboarding session 的 Coach |
| `"coaching"` | 日常对话内嵌（默认）| 常规 coaching session 的 Coach |
| `"intervention"` | 体验式干预形态 | `future-self-dialogue` / `scenario-rehearsal` / `metaphor-collaboration` / `cognitive-reframing` 四份 skill |
| `"witness-card"` | 见证卡片 | `compose_witness_card` 工具 |

`metadata.intervention_kind` 取值（仅当 `surface="intervention"` 时必填）：

- `"future-self-dialogue"` / `"scenario-rehearsal"` / `"metaphor-collaboration"` / `"cognitive-reframing"`

**前端契约**：

1. `surface` 缺失或不识别时，前端降级为 `"coaching"` 视觉，不抛错。
2. `intervention` 形态使用独立视觉外壳（更多留白、copper 细线、仪式化揭示）；具体视觉规格由 `/design-shotgun` 或 `/design-consultation` 单独产出，契约只约定分类键。
3. 其他三类形态保持现有视觉。

**运行时约束**：

1. `metadata` 键由 `A2UIPayload.metadata` 透传，后端 `validate_a2ui_response` 仅校验 `data` 字段，**不对 metadata 键做运行时校验**。
2. `surface` 与 `intervention_kind` 的正确写入依赖 Coach 系统提示词约束（`coach_system.j2` Section 3.5 + 四份 SKILL.md 的 A2UI Composition 节）与后续 eval 覆盖。
3. payload 构造侧需做最小断言：若 `surface="intervention"` 必带 `intervention_kind`。

完整规格见 `docs/10_Experiential_Interventions.md`。

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
7. retrieval 返回值必须显式声明 `evidence_kind="archive_source"` 与 `usage="runtime_evidence"`，以保证其在运行时只作为当前 invocation 的证据输入，而不是长期语义来源。

### 10.3 语义记忆层

用于保存长期教练关系所需的高信号记忆，例如：

1. 用户画像与偏好。
   - `/profile/context.md` 采用六维画像结构（Basics / Environment / Identity / Habits / Rhythm / Triggers），存储稳定生活事实。
   - `/coach/AGENTS.md` 采用四分区协议（Verified Patterns / Hypotheses / Coaching Notes / Claimed vs Revealed），存储 Coach 跨时间观察推断。
2. chapter、LifeSign、timeline markers。
3. 未来节日、行程计划等对长期陪伴有持续价值的信息。
4. `Coach` 明确认定并写入的长期语义结论。

`Coach` 是语义记忆主写入者。后台分析流程只生成候选信号，不直接改写权威语义记忆。

当前阶段，权威语义记忆路径至少包括：

1. `/profile/context.md`
2. `/profile/dashboardConfig`
3. `/goal/current.json`
4. `/goal/archive/{id}.json`
5. `/chapter/current.json`
6. `/chapter/archive/{id}.json`
7. `/coach/AGENTS.md`
8. `/lifesigns.md`
9. `/timeline-calendar.md`

以下内容不属于权威语义记忆：

1. `/ledger/...` 等事件历史。
2. `/derived/...` 等候选信号与分析结果。
3. `/day_summary/...` 日摘要（由日终 Pipeline 生成，≤60 字单句，属于 `archive_source`）。无会话日由 Pipeline 自动回填。
4. `/conversation_archive/{date}.md` 按天独立的完整会话归档（由日终 Pipeline 写入，属于 `archive_source`）。Coach 通过 `grep` 关键词定位日期后 `read_file` 单日文件，禁止一次性加载全部归档。
5. `/derived/briefing.md` 现纳入 Goal / Chapter / Process Goals 预计算摘要，作为 Coach 每日上下文的只读来源。

约束如下：

1. `Coach` 只能把跨会话仍有持续价值的结论写入权威语义记忆路径。
2. 原始事件、候选信号与会话归档只能作为证据来源，不得直接等同于长期语义记忆。
3. backend 的分析与中间件若产生候选信号，必须写入候选层，而不是直接覆盖权威语义记忆。
4. 当前实现中，`/derived/` 路径下的所有内容只能作为 `candidate_signal` 使用，不得直接 promotion 到权威语义。
5. 当前实现中，archive summary / excerpt、`runtime_only` 与 `observability_only` 内容一律不得直接 promotion 到权威语义。
6. 当前实现中，`authoritative_semantic` 路径的直接文件写入必须经过显式确认上下文，不允许未确认写入。
7. Coach 写入权威语义记忆时遵循信息凝练原则：最少 token 传递最大决策价值。记忆文件是索引和摘要，不是叙述。

当前实现使用以下运行时字段表达显式确认写入上下文：

1. `configurable.semantic_write_confirmed`
2. `configurable.semantic_write_source_kind`
3. `configurable.semantic_write_source_name`

### 10.4 语义边界分类

为避免 archive、候选信号与长期语义混写，backend 必须通过同一 helper 对路径进行以下分类：

1. `authoritative_semantic`
2. `candidate_signal`
3. `archive_source`
4. `runtime_only`
5. `observability_only`
6. `non_memory`

约束如下：

1. `/profile/...`、`/goal/...`、`/chapter/...`、`/coach/AGENTS.md`、`/lifesigns.md`、`/timeline-calendar.md` 属于 `authoritative_semantic`。
2. `/derived/...` 属于 `candidate_signal`。
3. `/archive/...`、`/day_summary/...`、`/conversation_archive/...` 属于 `archive_source`。
4. `/ledger/...` 属于 `runtime_only`。
5. `/observability/...` 属于 `observability_only`。
6. 该分类同时兼容 backend 视角路径与 `/user/...` 前缀路径，不允许调用方各自维护另一套归一化逻辑。

### 10.5 可观测性层

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
7. `briefing.load_failed`

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
| 2026-04-11 | 同步当前实现状态：补充 `SessionProfile` 最小字段、语义边界六分类、archive retrieval 的 `archive_source` / `runtime_evidence` 契约，以及当前已代码化的 promotion 禁止规则 |
| 2026-04-12 | 收紧当前实现状态：`session_type` 改为 fail-closed；Journey Analysis 改为通过共享 backend factory 解析真实 backend；权威语义写入边界改为在 `edit_file` / `write_file` 写入面执行 |
| 2026-04-12 | 编号调整 06 → 05；修正 Store key 示例（dashboardConfig、coping_plans）；移除已删除文档的交叉引用 |
| 2026-04-13 | §8.3 新增 Reject Reason 语义；原 §8.3 长期存储边界顺延为 §8.4 |
| 2026-04-14 | §7.4 新增系统触发器契约（daily_checkin / daily_review）；日摘要格式变更为 ≤60 字单句 + 无会话日回填 |
| 2026-04-14 | 新增 `/conversation_archive/{date}.md` 按天会话归档；Coach 通过 grep→read_file 两步检索，禁止全量加载；语义分类补充 archive_source |
| 2026-04-14 | §6.2 新增 `/goal/current.json` 与 `/goal/archive/{id}.json` 路径；§10.3 权威语义记忆路径新增 Goal 相关路径；§10.4 语义分类补充 `/goal/...` 属于 `authoritative_semantic` |
| 2026-04-15 | §5 更新 `user_id` 身份边界：应用级稳定身份必须来自受信任应用边界；新增外部认证供应商与稳定 `user_id` 解耦约束 |
| 2026-04-15 | §7.5 收紧桌面 onboarding 客户端边界：在 `onboarding_complete` 写入前保持全屏 onboarding surface，禁止抢先挂载标准 coaching workspace 或预建 coaching thread |
| 2026-04-15 | §7.5 新增设置页 Re-entry 约束：补采入口必须保持 `onboarding_complete: true`，通过独立 onboarding thread 进入全屏补采对话，不得伪造 reset |
| 2026-04-15 | §5.1 认证落地：`VOLITI_USER_MAP` 门禁 → Supabase Auth；§5.4 从"预见外部认证"更新为"Supabase Auth 边界"；`user_id` = Supabase UUID，无映射层 |
