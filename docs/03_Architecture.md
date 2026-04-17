<!-- ABOUTME: Voliti 系统结构文档，说明核心组件、数据流、部署路径与测试视图 -->
<!-- ABOUTME: 本文只描述系统结构，不承担运行时契约真相定义职责 -->

# Voliti 系统架构

> 相关文档：
> 产品定位见 [`01_Product_Foundation.md`](01_Product_Foundation.md)。
> 设计理念见 [`02_Design_Philosophy.md`](02_Design_Philosophy.md)。
> 设计规格见项目根目录 [`DESIGN.md`](/Users/dexter/DexterOS/products/Voliti/DESIGN.md)。
> 运行时契约见 [`05_Runtime_Contracts.md`](05_Runtime_Contracts.md)。


## 一、文档职责

本文描述 Voliti 当前系统的结构关系、主要组件、关键数据流与部署形态。凡涉及以下内容，均以 [`05_Runtime_Contracts.md`](05_Runtime_Contracts.md) 为准：

1. Store 正式结构。
2. session type、A2UI、错误封装的正式语义。
3. 记忆分层与用户态状态覆盖。
4. 观测字段与事件契约。

## 二、系统总览

Voliti 由四部分组成：

1. **Web MVP 客户端**：当前开发优先级。Next.js 15 + React 19，三栏布局（History | Chat | Mirror），A2UI 交互面板。
2. **iOS 原生客户端**：SwiftUI 原生体验，功能与 Web 端对齐。
3. **LangGraph backend**：负责单一 Coach Agent 的运行时、共享持久化真相与会话执行。
4. **eval 模块**：负责对 Coach Agent 行为进行离线评估与验证。

当前系统遵循两个结构性原则：

1. 用户只面对单一 Coach Agent。
2. 共享持久化真相由 backend 持有，客户端负责设备本地状态与投影。

## 三、核心组件

### 3.1 Web MVP 客户端

**技术栈**

1. Next.js 15 / React 19 / TypeScript / Tailwind CSS 4 / shadcn/ui
2. LangGraph SDK（useStream hook）
3. SSE 与 LangGraph backend 通信

**职责**

1. 呈现 Coach 对话与 A2UI 结构化交互（8 种组件 + 拒绝理由 + 重置 + 键盘快捷键）。
2. 管理天级 Thread（一天一个会话，自动创建/复用）。
3. 持有设备本地状态（localStorage）：Onboarding 完成标记、Witness Card 缓存。
4. Mirror 面板从 LangGraph Store 同步数据：Identity 从 `profile` 读取，Goal 从 `/goal/current.json` 读取，Chapter/指标/LifeSign 从相应路径读取。
5. Supabase Auth 认证 + middleware 同步 `voliti_user_id` cookie + 服务端 `configurable` 注入（user_id + session_type）。

### 3.2 iOS 原生客户端

**技术栈**

1. SwiftUI
2. SwiftData
3. SSE 与 LangGraph backend 通信

**职责**

1. 呈现 Coach 对话与结构化交互。
2. 持有设备本地状态、缓存与投影视图。
3. 管理 thread 标识、草稿、临时输入和系统权限相关状态。
4. 将共享持久化请求发送到 backend。

### 3.3 Coach Agent

**运行形态**

当前 backend 使用单一 Coach Agent 作为用户唯一可见的智能体入口。其运行时可组合以下能力：

1. 系统 prompt。
2. memory 文件读取。
3. middleware 注入。
4. A2UI 工具。
5. 专项 subagent。

**当前稳定特征**

1. 用户不会直接接触后台分析代理。
2. 会话差异通过 `session profile` 组合，而不是多套独立 agent。
3. Witness Card 等专项能力通过工具或 subagent 组合进入主运行时。

### 3.4 LangGraph Store 与运行态

backend 同时承载两类后端状态：

1. **共享持久化真相**
   - 长期语义记忆
   - 会话完成态
   - 业务状态
2. **运行时临时状态**
   - 当前执行周期内的中断状态
   - A2UI payload snapshot
   - 会话过程态

当前原始会话记录的 canonical source 附着于运行时会话历史。产品层通过 `Conversation Archive Access Layer` 将其规范化为稳定的 `Conversation Record` 视图，再供显式检索消费。

正式边界以 [`05_Runtime_Contracts.md`](05_Runtime_Contracts.md) 为准。

### 3.5 Eval 模块

eval 是独立 Python 包，用于：

1. 跑本地或开发环境下的行为评估。
2. 验证特定模型、配置或提示词组合。
3. 为回归测试和多模型对比提供离线检查入口。

eval 不是运行时系统的一部分，但它必须遵守同一份 Store 与会话契约。

## 四、关键数据流

### 4.1 标准对话流

```text
用户输入
  → iOS 客户端
    → SSE 请求到 backend
      → Coach Agent 运行
        → 读取所需 memory / state
        → 可选调用工具或 subagent
      → 流式返回响应
    → iOS 渲染临时 assistant 输出
      → 收到完成信号后转为正式消息
```

### 4.2 A2UI 中断流

```text
Coach 调用 A2UI 工具
  → backend 生成 interrupt 与 payload snapshot
    → iOS 渲染结构化交互面板
      → 用户提交 / 取消
        → backend 校验合法性与一次性
          → 通过后恢复会话
```

### 4.3 共享状态同步流

```text
backend 写入共享持久化状态
  → LangGraph Store
    → iOS 按契约解包
      → 更新本地投影视图
```

### 4.4 原始记录归档流

```text
Runtime Session History
  → Conversation Archive Access Layer
    → 规范化为 Conversation Record
      → 默认不自动进入 Coach 上下文
        → 仅在显式检索时提供摘要或片段
```

## 五、当前技术选型

### 5.1 为什么保留单一 Coach Agent

1. 用户面对统一关系对象，产品语义更清晰。
2. 会话差异通过 profile、middleware、工具边界组合，不需要平行的 agent 世界。
3. 运行时控制面更集中，便于约束 Store、session、A2UI 与错误语义。

### 5.2 为什么使用 A2UI

1. 教练对话中的结构化交互不可预先穷举。
2. 同一组基础组件可以复用到补采、反思、干预与确认场景。
3. 单一 interrupt / resume 机制有助于客户端收口。

### 5.3 为什么采用分层记忆

1. 原始 transcript、长期语义记忆与 observability 有不同职责。
2. 原始记录默认不应污染上下文。
3. 语义记忆需要由 `Coach` 主导写入，而不是简单堆积原始数据。

### 5.4 DeepAgent 复用边界

Voliti 以 DeepAgent 作为唯一运行时底座。以下能力直接复用，不另造轮子：

1. 执行循环（模型调用、tool calling、middleware 调度、subagent 集成）。
2. backend 与持久化机制（thread-scoped 运行时状态、Store-backed 长期持久化、checkpoint / history、backend route 分流）。
3. context management（system_prompt、memory files、summarization / compaction、middleware 运行时注入）。
4. tool 与 subagent 面（自定义 tools、自定义 subagents、tool-level middleware、human-in-the-loop interrupt）。

Voliti 在此基础上仅补四类最小产品语义定制：

1. `SessionProfile`：轻量配置对象，定义会话类型的 prompt、middleware、memory 差异。
2. Prompt Layering Policy：五层提示词结构的分层与优先级规则。
3. Semantic Boundary Policy：权威语义、候选信号、archive 证据、运行时状态、可观测性的统一分类。
4. Memory Lifecycle Policy：记忆的捕获、蒸馏、注入与整理规则。当前包括六维用户画像结构、四分区 Coach 记忆协议、信息凝练原则、Chapter 转移时的强制 review，以及从原始事件到长期语义的分层蒸馏链路（ledger → day_summary → briefing → profile/coach memory）。
5. Skills 机制：基于 DeepAgent `SkillsMiddleware` 承载四种体验式干预手段（未来自我对话、场景预演、隐喻协作、认知重构）；通过 `CompositeBackend` 新增 `/skills/coach/` 路由挂载只读 `FilesystemBackend`（指向仓库 `backend/skills/coach/`）；`SkillsGateMiddleware` 仅在 coaching session 注入元数据到 system prompt，onboarding 跳过以保持引导节奏。完整规格见 `docs/10_Experiential_Interventions.md`。

### 5.5 架构守护清单

以下方向已被明确排除，防止长期技术负债：

1. 不新增第二套 harness framework 或平行执行器。
2. 不新增厚重会话管理层（SessionRegistry / SessionManager / 多层 profile service）。
3. 不新增平行 memory / archive 系统（不自建 semantic memory backend、不做 transcript 双写到长期 Store）。
4. 不新增独立 prompt framework 或新的 runtime phase taxonomy。
5. 当前阶段不引入独立 consolidation agent；仅当后台任务需要跨会话、跨时间窗口运行时才考虑升级。

## 六、部署视图

### 6.1 Backend

**本地开发**

```bash
cd backend && uv run langgraph dev --port 2025
```

**目标部署形态**

1. LangGraph Cloud 负责 agent runtime。
2. Store 使用正式后端实现承载共享持久化真相。

### 6.2 iOS 客户端

1. 通过 Xcode 构建。
2. 通过 SSE 与 backend 通信。
3. 本地使用 SwiftData 承载设备本地状态与投影视图。

### 6.3 当前阶段说明

当前仓库处于基础设施收口阶段，因此部署重点不是横向扩展，而是：

1. 先建立可信运行时边界。
2. 再恢复跨端验证能力。
3. 最后再承接更复杂的长期记忆与主动干预能力。

## 七、测试视图

### 7.1 Backend / Eval

当前至少需要覆盖：

1. Store 契约与解包逻辑。
2. A2UI 合法性与一次性语义。
3. 迁移 / 清理脚本。
4. eval 默认入口与关键客户端接口。

### 7.2 iOS

当前至少需要覆盖：

1. Store 投影视图解包与同步。
2. thread 选择与 onboarding 状态恢复。
3. 流式 assistant 临时态与完成态切换。
4. A2UI 提交与错误态呈现。

### 7.3 跨端验证

本轮必须具备：

1. 跨端 contract fixture tests。
2. 关键状态转换测试。
3. 至少一条 iOS → backend → Store → iOS projection 的真实纵向路径。
4. conversation archive / retrieval 的 live integration 脚本。

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-12 | 初始创建：系统架构总览、核心组件、数据流程、技术选型与部署视图 |
| 2026-04-09 | 重写文档职责：移除失真的运行时细节，将 Store、session、A2UI、错误与记忆边界统一指向 `05_Runtime_Contracts.md` |
| 2026-04-10 | 同步原始会话记录主线：以 `Runtime Session History` 与 `Conversation Archive Access Layer` 取代 archive 双写叙述，并补充 live integration 验证入口 |
| 2026-04-12 | 合并原 `08_Runtime_Harness_Control_Plane.md` 的 DeepAgent 复用边界与守护清单到技术选型章节；交叉引用更新为 `05_Runtime_Contracts.md` |
| 2026-04-14 | 更新 Mirror 面板数据源描述：Identity 从 `profile` 读取，Goal 从 `/goal/current.json` 读取 |
| 2026-04-15 | 更新 Web 客户端认证职责描述：Supabase Auth 负责身份验证，middleware 同步 `voliti_user_id` cookie，服务端注入 `user_id`（Supabase UUID）与 `session_type` |
