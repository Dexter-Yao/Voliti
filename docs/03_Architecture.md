<!-- ABOUTME: Voliti 系统结构文档，说明核心组件、端到端架构、数据流、技术选型与部署视图 -->
<!-- ABOUTME: 本文只描述系统结构，不承担运行时契约真相定义职责 -->

# Voliti 系统架构

> 相关文档：
> 产品定位见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。
> 设计理念见 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。
> 设计规格见项目根目录 [`DESIGN.md`](/Users/dexter/DexterOS/products/Voliti/DESIGN.md)。
> 运行时契约见 [`05_Runtime_Contracts.md`](05_Runtime_Contracts.md)。

## 一、文档职责

本文描述 Voliti 当前系统的结构关系、端到端拓扑、核心组件、关键数据流、技术选型与部署形态。凡涉及以下内容，以 [`05_Runtime_Contracts.md`](05_Runtime_Contracts.md) 为准：

1. Store 正式结构、路径语义、文件封装值契约。
2. 会话类型（`session_type`）、A2UI、错误封装的正式语义。
3. 记忆分层、语义边界分类与用户态状态覆盖。
4. 可观测性字段与事件契约。

产品定位的"为什么"辩护不在本文范围内，见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。

## 二、端到端架构

Voliti 当前运行时形态：用户在浏览器中与单一 Coach Agent 对话，后端以 LangGraph Runtime 承载共享持久化真相，日终 Pipeline 周期性蒸馏长期语义记忆，eval 以离线方式验证同一份契约。

### 2.1 总览

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                                  浏 览 器                                     │
│                        Web MVP · Next.js 15 + React 19                        │
│        History 栏  │  Chat 栏（SSE 流）  │  Mirror 栏（投影视图）              │
│           ↑                   ↑                     ↑                         │
│        天级 thread       useStream hook      /api/me/coach-context            │
└──────────────┬──────────────────────────────────────────┬──────────────────────┘
               │ Supabase Auth（邮箱+密码）                │ 服务端 Route Handler
               │ → Supabase UUID = user_id                │ → 并行读 Store keys
               ▼                                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Next.js Server Boundary                               │
│  middleware.ts：验证 Supabase session                                          │
│  /api/[...path]/route.ts：注入 configurable.user_id + session_type            │
│  /api/me/coach-context/route.ts：聚合 Mirror 数据 + assertValidStoreJson 守护  │
└──────────────┬───────────────────────────────────────────────────────────────┘
               │ SSE（LangGraph SDK）  configurable: { user_id, session_type }
               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    LangGraph Runtime — 单一 Coach Agent                       │
│                                                                              │
│   Middleware 栈（外 → 内执行）：                                                │
│     1. StripDeepAgentDefaultsMiddleware   剥离 DeepAgent 内置 prompt / Todo    │
│     2. SessionTypeMiddleware              按 session_type 注入 onboarding.j2   │
│     3. SkillsGateMiddleware               coaching session 注入 skills 元数据  │
│     4. BriefingMiddleware                 从 Store 读 briefing.md 注入 system  │
│                                                                              │
│   Tools（动态组合）：                                                           │
│     • fan_out（通用 A2UI）                                                     │
│     • add_forward_marker（前瞻标记写入）                                        │
│     • fan_out_future_self_dialogue / _scenario_rehearsal /                   │
│       _metaphor_collaboration / _cognitive_reframing                         │
│     • issue_witness_card                                                     │
│                                                                              │
│   Backend（CompositeBackend 路由）：                                            │
│     /user/…           → StoreBackend    （ns: ("voliti", user_id)）           │
│     /skills/coach/…   → ReadOnlyFilesystemBackend                            │
│     其他              → StateBackend    （当前 run 临时状态）                   │
└──────────────┬───────────────────────────────────────────────────────────────┘
               │ Store.put / Store.get  （契约见 05 §6；强格式路径经 Pydantic 校验）
               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│               LangGraph Store — 共享持久化真相（namespace: voliti/{uid}）       │
│                                                                              │
│   权威语义（authoritative_semantic）                                           │
│     /profile/context.md            六维用户画像                                 │
│     /profile/dashboardConfig       Mirror 仪表盘配置                           │
│     /goal/current.json             北极星目标                                  │
│     /goal/archive/{id}.json        历史目标                                    │
│     /chapter/current.json          当前章节                                    │
│     /chapter/archive/{id}.json     历史章节                                    │
│     /coach/AGENTS.md               Coach 四分区记忆                            │
│     /coping_plans_index.md         LifeSign 预案索引                           │
│     /lifesigns.md                  LifeSign 主文件                             │
│     /timeline/markers.json         前瞻标记                                    │
│                                                                              │
│   候选信号（candidate_signal）                                                 │
│     /derived/briefing.md           Goal/Chapter/摘要的每日只读上下文            │
│                                                                              │
│   原始证据（archive_source）                                                   │
│     /day_summary/{yyyy-mm-dd}.md        日摘要（≤60 字单句）                   │
│     /conversation_archive/{yyyy-mm-dd}.md  按天会话归档                         │
│                                                                              │
│   interventions namespace                                                    │
│     ns: ("voliti", uid, "interventions")  Witness Card 存储                   │
└──────────────┬───────────────────────────────────────────────────────────────┘
               │ Cron 触发（按用户时区零点）
               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│   Day-End Pipeline                                                           │
│     seal_thread → generate_day_summary → archive_conversation →               │
│     backfill_missing_summaries → expire_passed_markers →                     │
│     compute_and_write_briefing                                               │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│   Eval（离线）                                                                │
│   本地或 CI 环境调用 backend dev server；消费 store_contract / a2ui / prompts  │
│   作为真相源，遵守同一份契约，不写入运行时 Store                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 结构性原则

1. 用户只面对单一 Coach Agent；后台分析对用户透明。
2. 共享持久化真相由 backend 持有；客户端只承载设备本地状态、缓存与投影视图。
3. 会话差异通过轻量 `SessionProfile` + middleware 注入表达，不引入平行 agent 或厚重 session manager。
4. 强格式 Store 路径双端 fail-closed：后端写入经 Pydantic 校验守护；前端读取经结构性必要字段守护。

## 三、核心组件

### 3.1 Web MVP 客户端

**技术栈**

1. Next.js 15 / React 19 / TypeScript / Tailwind CSS 4 / shadcn/ui
2. LangGraph SDK（`useStream` hook）
3. react-resizable-panels v4（History | Chat | Mirror 三栏布局）
4. Supabase Auth（邮箱+密码认证）

**职责**

1. 呈现 Coach 对话与 A2UI 结构化交互（8 种组件 + `reject` 理由 + 重置 + Cmd+Enter）。
2. 管理天级 Thread（一天一个 coaching 会话，自动创建/复用）。
3. 持有设备本地状态（localStorage）：UI 偏好、临时缓存、非业务状态。
4. Mirror 面板从 backend 聚合接口读取投影：Identity 从 profile、Goal 从 `/goal/current.json`、Chapter/指标/LifeSign/markers/Witness Card 从相应路径读取。
5. 系统触发器：当日首次创建 coaching thread 时发送 `[daily_checkin] HH:MM`；使用 `DO_NOT_RENDER_ID_PREFIX` 在 UI 中隐藏。
6. Onboarding 全屏 surface 与标准 coaching workspace 的切换由 `onboarding_complete` 判定驱动（契约见 05 §7.5）。

### 3.2 iOS 原生客户端

当前阶段已搁置。代码目录 `frontend-ios/` 保留，不参与 MVP 交付。未来恢复时必须遵守与 Web 相同的 Store / 会话 / A2UI 契约。

### 3.3 Coach Agent

**运行形态**

Coach Agent 由 `create_deep_agent()` 构造，运行时组合以下能力：

1. 系统 prompt（`PromptRegistry` + Jinja2 `SandboxedEnvironment`）。
2. 会话级 middleware 栈（剥离内置默认值、注入 onboarding / skills / briefing）。
3. 工具：通用 `fan_out`、`add_forward_marker`，以及 `backend/skills/coach/` 下动态加载的四个 intervention 专用工具与 `issue_witness_card`。
4. 虚拟文件系统（`CompositeBackend`）：`/user/…` 路由到 Store、`/skills/coach/…` 路由到只读文件系统、其他到 State。
5. 记忆路径：coaching 会话挂载 `/user/coach/AGENTS.md`、`/user/profile/context.md`、`/user/coping_plans_index.md`。

**当前稳定特征**

1. 用户不直接接触后台分析代理。
2. 会话差异通过 `SessionProfile` + middleware 组合，而非多套独立 agent。
3. Witness Card 与体验式干预通过 skill tool 组合进入主运行时，无 subagent。

### 3.4 LangGraph Store 与运行态

backend 同时承载两类状态：

1. **共享持久化真相**
   - 长期语义记忆（权威路径）
   - 会话完成态与业务状态
   - A2UI 中断消费状态
2. **运行时临时状态**
   - 当前 run 周期内的中断与 payload snapshot
   - 会话过程态与工具执行上下文

原始会话记录的 canonical source 附着于运行时会话历史，不双写到长期 Store。日终 Pipeline 将其规范化为 `/conversation_archive/{date}.md`（archive_source）与 `/day_summary/{date}.md`（archive_source），供 Coach 通过显式 `grep` → `read_file` 检索。

> `Runtime Session History` / `Conversation Archive Access Layer` / `Conversation Record` 为运行时契约文档中定义的供应商中立命名（见 05 §2），当前代码层以 `/conversation_archive/` 路径常量 + grep/read 检索模式实现，尚无独立封装层。

正式边界以 [`05_Runtime_Contracts.md`](05_Runtime_Contracts.md) 为准。

### 3.5 Day-End Pipeline

Day-End Pipeline 是周期性后台流程，按用户时区零点由 LangGraph Cron 触发。职责：

1. `seal_thread` — 当日 coaching thread 标记为 sealed。
2. `generate_day_summary` — 轻量模型生成日摘要写入 `/day_summary/{date}.md`。
3. `archive_conversation` — 完整会话归档写入 `/conversation_archive/{date}.md`。
4. `backfill_missing_summaries` — 7 天窗口内缺失日期自动回填。
5. `expire_passed_markers` — 超过当前时间的 `timeline/markers.json` 条目状态改为 `passed`。
6. `compute_and_write_briefing` — 预计算 Goal/Chapter/摘要上下文写入 `/derived/briefing.md`，供下一次 coaching 会话 BriefingMiddleware 直接注入。

### 3.6 Eval 模块

eval 是独立 Python 包，用于对 Coach Agent 行为做离线评估：

1. 跑本地或 CI 环境下的行为回归。
2. 验证特定模型、配置或提示词组合（lite 10 维 10 seed / full 15 维 20 seed / 多模型对比）。
3. 为 prompt 演进与多模型切换提供一致的评估入口。

eval 不是运行时系统的一部分，但必须遵守同一份 Store 与会话契约。契约真相源：`backend/src/voliti/store_contract.py`、`backend/src/voliti/a2ui.py`、`backend/prompts/`。

## 四、关键数据流

数据流仅描述组件联动顺序；所有字段、校验、错误封装语义以 05 为准。

### 4.1 标准对话流

```text
浏览器用户输入
  → Next.js API route 注入 configurable.user_id / session_type
    → SSE 传入 LangGraph Runtime
      → Middleware 栈依次注入 prompt / briefing / skills 元数据
        → Coach Agent 按需调用 tools / file backend
          → 流式返回 assistant 输出
      → 浏览器渲染临时态
        → 收到完成信号后转为正式消息
```

### 4.2 A2UI 中断流

```text
Coach 调用 fan_out / fan_out_<kind> / issue_witness_card
  → backend 生成 interrupt + payload snapshot（存于运行时会话状态）
    → 浏览器按 metadata.surface 分派到对应外壳渲染
      → 用户 submit / reject（含可选 reason）/ skip
        → backend 校验合法性与一次性（snapshot 匹配）
          → 通过后 tool 返回响应摘要，恢复会话
```

### 4.3 共享状态同步流

```text
backend 写入共享持久化状态
  → store_write_validated（强格式路径）/ store.put（其他）
    → LangGraph Store 落盘
      → 浏览器通过 /api/me/coach-context 聚合拉取
        → assertValidStoreJson 结构性守护
          → 更新 Mirror 投影视图
```

### 4.4 原始记录归档流

```text
Coaching Thread（当日）
  → Day-End Pipeline（Cron 零点触发）
    → day_summary + conversation_archive 写入 Store
      → 默认不自动进入 Coach 上下文
        → Coach 通过 grep → read_file 显式检索当日内容
```

## 五、技术选型

### 5.1 核心原则

设计选择的"为什么"见 [`01_Product_Foundation.md`](01_Product_Foundation.md) 与 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。本文仅列出结果。

| 选择 | 当前形态 |
|------|---------|
| agent 模型 | 单一 Coach Agent，差异通过 `SessionProfile` + middleware 表达 |
| 结构化交互 | A2UI 协议，8 种组件 + metadata 分派键（见 05 §8） |
| 记忆体系 | 权威 / 候选信号 / 原始证据 / 运行时 / 可观测性 / 非记忆六分类（见 05 §10） |
| 运行时底座 | DeepAgent（唯一运行时框架，不另造 harness） |

### 5.2 DeepAgent 复用边界

Voliti 以 DeepAgent 作为唯一运行时底座。直接复用以下能力：

1. 执行循环（模型调用、tool calling、middleware 调度）。
2. Backend 与持久化机制（thread-scoped 运行时状态、Store-backed 长期持久化、checkpoint/history、backend route 分流）。
3. Context management（system_prompt、memory files、summarization / compaction、middleware 运行时注入）。
4. Tool 面（自定义 tools、tool-level middleware、human-in-the-loop interrupt）。
5. Skills 机制（`SkillsMiddleware` + 只读文件系统路由）。

Voliti 在此基础上仅补五类最小产品语义定制：

1. **`SessionProfile`** — 声明式会话配置（`session_type`、`system_prompt_name`、`memory_paths`）。
2. **Prompt Layering Policy** — 五层提示词分层与优先级。
3. **Semantic Boundary Policy** — 权威/候选/原始/运行时/可观测性的统一分类（代码入口见 05 §10.4）。
4. **Memory Lifecycle Policy** — 捕获、蒸馏、注入、整理规则（详见 05 §10）。
5. **Experiential Intervention Skills** — 四种干预手段的 skill 定义与专用工具（详见 [`10_Experiential_Interventions.md`](10_Experiential_Interventions.md)）。

### 5.3 架构守护清单

以下方向明确排除，防止长期技术负债：

1. 不新增第二套 harness framework 或平行执行器。
2. 不新增厚重会话管理层（SessionRegistry / SessionManager / 多层 profile service）。
3. 不新增平行 memory / archive 系统（不自建 semantic memory backend、不做 transcript 双写到长期 Store）。
4. 不新增独立 prompt framework 或新的 runtime phase taxonomy。
5. 当前阶段不引入独立 consolidation agent；仅当后台任务需要跨会话、跨时间窗口运行时才考虑升级。
6. 不把 subagent 作为 Coach 能力扩展的默认手段；Witness Card 与体验式干预以 skill tool 方式组合进入主运行时。

## 六、部署视图

### 6.1 Backend

**本地开发**

```bash
cd backend && uv run langgraph dev --port 2025
```

**目标部署形态**

1. LangGraph Cloud 承载 agent runtime 与 Cron 调度。
2. Store 使用正式后端实现承载共享持久化真相。
3. Supabase 承担用户身份、session 管理与密码策略。

### 6.2 Web 客户端

1. Next.js 生产构建（`pnpm build`）。
2. 通过 SSE 与 LangGraph Cloud 通信。
3. `/api/[...path]` 作为受信任边界，统一注入 `configurable.user_id` 与 `session_type`。
4. `/api/me/coach-context` 聚合 Mirror 投影数据并做结构性守护。

### 6.3 当前阶段说明

当前仓库处于契约收口阶段，部署重点不是横向扩展，而是：

1. 先建立可信运行时边界（身份、Store、A2UI、记忆分层）。
2. 再逐步接入工具层到 Pydantic 校验。
3. 最后再承接更复杂的长期记忆与主动干预能力。

## 七、测试视图

### 7.1 Backend / Eval

至少覆盖：

1. Store 契约与解包逻辑（`tests/test_store_contract.py`）。
2. 强格式路径的 Pydantic 校验（写入 fail-closed / 读取 fail-closed）。
3. A2UI 合法性、一次性、metadata 语义键。
4. Middleware 注入行为（session_type、briefing、skills_gate、strip defaults）。
5. Day-End Pipeline 各步骤与回填逻辑。
6. 语义边界分类函数。
7. Eval 默认入口（lite / full / compare）与 seed 场景执行。

### 7.2 Web 客户端

至少覆盖：

1. 认证链路与 `configurable.user_id` 注入边界。
2. Onboarding surface ↔ coaching workspace 切换。
3. A2UI 组件渲染、四种 Intervention Layout、Witness Card 展示。
4. Mirror 聚合接口的结构性守护与降级。
5. 系统触发器（`daily_checkin`）的不可见注入。

### 7.3 跨端验证

1. 跨端 contract fixture tests（根级 `tests/contracts/fixtures/`）。
2. 强格式 fixture 与 Pydantic 模型的参数化同步测试（`test_fixture_passes_contract_model`）。
3. onboarding 完成态端到端脚本（`tests/contracts/run_onboarding_completion_e2e.py`）。

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-12 | 初始创建：系统架构总览、核心组件、数据流程、技术选型与部署视图 |
| 2026-04-09 | 重写文档职责：移除失真的运行时细节，将 Store、session、A2UI、错误与记忆边界统一指向 `05_Runtime_Contracts.md` |
| 2026-04-10 | 同步原始会话记录主线：以 `Runtime Session History` 与 `Conversation Archive Access Layer` 取代 archive 双写叙述，并补充 live integration 验证入口 |
| 2026-04-12 | 合并原 `08_Runtime_Harness_Control_Plane.md` 的 DeepAgent 复用边界与守护清单到技术选型章节；交叉引用更新为 `05_Runtime_Contracts.md` |
| 2026-04-14 | 更新 Mirror 面板数据源描述：Identity 从 `profile` 读取，Goal 从 `/goal/current.json` 读取 |
| 2026-04-15 | 更新 Web 客户端认证职责描述：Supabase Auth 负责身份验证，服务端注入 `configurable.user_id`（Supabase UUID）与 `session_type` |
| 2026-04-18 | Witness Card 从专项 subagent 收口为 coach skill tool；Mirror 的 Witness Card 回看数据源收口为 LangGraph Store；DeepAgent 复用边界相应移除 subagent 依赖表述 |
| 2026-04-19 | 端到端重构：新增 §2 端到端架构图（中间件栈 / CompositeBackend 路由 / Store 语义分层 / Day-End Pipeline）；删除产品决策辩护（§5.1-5.3）、iOS 专项测试章节与 conversation archive retrieval live 脚本要求；iOS 端声明为当前搁置；数据流发起方统一为 Web 客户端；§5.4 Memory Lifecycle 精简指向 05；`Runtime Session History` / `Conversation Archive Access Layer` 标注为尚未封装为独立代码层；§3.5 新增 Day-End Pipeline 节 |
