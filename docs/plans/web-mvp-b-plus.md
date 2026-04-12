<!-- ABOUTME: Voliti Web MVP 实现计划，方案 B+：三栏可折叠布局 + 按天对话历史 -->
<!-- ABOUTME: 基于 agent-chat-ui fork，供 10 位早期付费用户验证的 Web 端教练体验 -->

# Voliti Web MVP — 方案 B+：三栏可折叠布局 + 按天对话历史

## Context

导师反馈核心建议：**先卖后建**。Fork `agent-chat-ui`（Next.js 15 / React 19 / TypeScript / Tailwind / shadcn/ui），部署为密码保护的 Web 应用供 10 位早期用户验证。

**已选定方案 B+**：三栏布局（左：按天对话历史 | 中：Coach 对话 | 右：Mirror 数据面板），两侧可折叠可拖拽。

线框图：`~/.gstack/projects/Dexter-Yao-Voliti/designs/voliti-web-mvp-20260412/option-b-plus.html`

---

## 核心架构决策

### 1. 三栏可拖拽布局

使用 `react-resizable-panels`（shadcn/ui 的 Resizable 组件底层库）：

```tsx
<PanelGroup direction="horizontal" autoSaveId="voliti-layout">
  <Panel id="history" collapsible collapsedSize={0} minSize={15} maxSize={25} defaultSize={18} />
  <PanelResizeHandle />
  <Panel id="chat" minSize={35} />
  <PanelResizeHandle />
  <Panel id="mirror" collapsible collapsedSize={0} minSize={15} maxSize={30} defaultSize={22} />
</PanelGroup>
```

- `autoSaveId` 自动持久化到 localStorage
- 折叠后显示 icon 按钮（汉堡菜单 / 网格图标）
- 移动端：两侧默认折叠，左侧覆盖层（overlay）展开

### 2. 按天 Thread 分割

**原则**：Thread 按天轮换，Store 跨天持久。

- 每天第一次访问 → 创建新 Thread，metadata: `{ user_id, date: "2026-04-12", session_type: "coaching" }`
- 同一天内所有对话在同一 Thread 中连续
- Coach system prompt 启动时从 Store 加载完整上下文（用户画像、Chapter、LifeSign、行为趋势）
- 侧边栏：`client.threads.search({ metadata: { user_id } })` 获取所有 Thread，按 `date` 分组显示

**后端影响**：
- `retrieve_conversation_archive()` 已支持跨 Thread 检索（按 `user_id` metadata），无需修改
- Thread 创建时需注入 `date` metadata（前端在 `threads.create()` 时写入，不是 configurable）
- Coach prompt 上下文加载机制不变（从 Store 读取）

### 3. A2UI 渲染：底部抽屉（shadcn Sheet）

与 iOS FanOutPanel 保持一致。`layout` 映射：half → 50vh, three-quarter → 75vh, full → 100vh。

---

## 功能映射总表

| iOS 功能 | Web 状态 | 实现方式 |
|----------|---------|---------|
| Coach 对话（SSE + Markdown） | **P1** | agent-chat-ui 基线 |
| Thinking Card | **P1** | 解析 fenced block，可折叠卡片 |
| Suggested Reply Pills | **P1** | 输入框上方水平药丸 |
| A2UI 8 种组件 | **P1** | 自定义中断渲染 + shadcn Sheet |
| 图片上传/展示 | **P1** | agent-chat-ui 已有 |
| 密码登录（10 用户） | **P1** | Next.js middleware + cookie |
| 三栏可拖拽布局 | **P1** | react-resizable-panels |
| 按天对话历史 | **P1** | Thread metadata + 左侧边栏分组 |
| Onboarding | **P1** | 全屏欢迎层 → 对话 |
| Mirror 数据面板 | **P2** | 右侧 Artifact 面板 + Store 同步 |
| Witness Card | **P2** | A2UI 已支持 + localStorage 存储 |
| 设置面板 | **P2** | shadcn Sheet 抽屉 |
| LifeSign 列表 | **延后** | Coach 对话中文本呈现 |
| Journal 时间线 | **延后** | 验证后再建 |
| 语音输入 | **砍掉** | — |
| 推送通知 | **砍掉** | — |

---

## Phase 1：核心对话 + 三栏布局 + 按天历史（~6 天）

### Step 1.1 — Fork 与项目初始化

- Fork `langchain-ai/agent-chat-ui` → `frontend-web/`
- `package.json`: `"voliti-web"`
- 安装：`npm add react-resizable-panels`（shadcn Resizable 的底层依赖）
- 环境变量：`NEXT_PUBLIC_API_URL=/api`, `NEXT_PUBLIC_ASSISTANT_ID=coach`, `LANGGRAPH_API_URL`, `LANGGRAPH_API_KEY`, `VOLITI_USER_MAP`

### Step 1.2 — 密码认证

- **新建** `src/middleware.ts` — 检查 `voliti_access` cookie
- **新建** `src/app/login/page.tsx` — 密码 → server action → 设置 cookie（含 user_id）

### Step 1.3 — 三栏可拖拽布局

- **修改** `src/components/thread/index.tsx` — 替换现有 CSS Grid 布局为 PanelGroup
- 左面板：`<HistorySidebar />`（新建）
- 中面板：现有 chat 组件
- 右面板：`<MirrorPanel />`（新建，P2 填充内容）
- 两个 `<PanelResizeHandle />` 渲染为竖线拖拽手柄
- 折叠状态：显示 icon 按钮，`ref.current.expand()` 展开
- 移动端 `@media (max-width: 768px)`：两侧默认折叠，左侧覆盖层模式

**关键文件**：
- `src/components/thread/index.tsx`（主布局重构）
- `src/components/layout/ResizableLayout.tsx`（新建，PanelGroup 封装）

### Step 1.4 — 按天对话历史侧边栏

- **新建** `src/components/history/HistorySidebar.tsx`
  - 调用 `client.threads.search({ metadata: { user_id }, limit: 100 })`
  - 按 `thread.metadata.date` 分组，渲染日期标题 + Thread 列表
  - 今天的日期标题用 copper 色 + "今天" 标签
  - 点击 Thread → 更新 URL `?threadId=`
  - Chapter 分界线：检测 Thread metadata 中的 chapter 变化
  
- **修改** `src/providers/Stream.tsx`
  - 移除配置表单
  - 注入 `configurable: { session_type, user_id, date: todayString(), correlation_id }`
  - 每天首次加载时检查今天是否已有 Thread：
    - `threads.search({ metadata: { user_id, date: today } })` → 有则复用，无则新建
  - `user_id` 从登录 cookie 读取
  
- **修改** `src/providers/Thread.tsx`
  - `getThreads()` 搜索时传入 `metadata: { user_id }`
  
- Chat header 显示当前日期 + "Fresh Start" 标签（仅当天新 Thread 时）

### Step 1.5 — Voliti 设计系统

- **修改** `src/app/globals.css` — Starpath tokens 覆盖 CSS 变量
- **修改** `tailwind.config.js` — 字体映射（LXGW WenKai / DM Sans / JetBrains Mono）
- 拖拽手柄样式：2px obsidian-10 竖线，hover 时变 copper

### Step 1.6 — A2UI 类型系统 + 组件库

- **新建** `src/lib/a2ui.ts` — 精确镜像 `backend/src/voliti/a2ui.py`
- **新建** `src/components/a2ui/` — 8 个组件 + Drawer + InterruptHandler + Renderer
- **修改** `src/components/thread/messages/ai.tsx` — 中断分发逻辑

### Step 1.7 — 流式内容清洗 + Thinking Card + Suggested Replies

- 移植 `CoachViewModel.stripFencedBlocks` / `extractCoachThinking` / `extractSuggestedReplies`
- **新建** `src/components/thread/ThinkingCard.tsx`
- **修改** `src/components/thread/index.tsx` — 药丸行

### Step 1.8 — Onboarding 流程

- **新建** `src/components/OnboardingWelcome.tsx`
- localStorage `onboarding_complete` 标记 + Store 检查

---

## Phase 1.5：CEO Review 新增范围（~1 天）

### Step 1.9 — 用户反馈收集

- **新建** `src/components/feedback/FeedbackButton.tsx`
  - 右下角浮动按钮，点击弹出文本输入框
  - 提交后存入 LangGraph Store namespace `("voliti", user_id)` key `/feedback/{timestamp}`
  - 包含 timestamp、当前 threadId、用户文字

### Step 1.10 — 消息级 👍/👎 评价

- **修改** `src/components/thread/messages/ai.tsx`
  - 每条 Coach 消息 hover 态显示 👍/👎 图标
  - 点击后调用 LangSmith feedback API，关联 run_id + message_id
  - 已评价状态持久化到 localStorage

### Step 1.11 — 使用数据埋点

- **新建** `src/lib/analytics.ts`
  - 集成 PostHog SDK（`posthog-js`）
  - 埋点事件：session_start, message_sent, a2ui_submit/reject/skip, witness_card_accept/reject, feedback_submitted, thread_switch
  - `NEXT_PUBLIC_POSTHOG_KEY` 环境变量

### Step 1.12 — 消息编辑

- agent-chat-ui 已内置消息编辑能力，保持标准 UX
- 确认编辑功能在 Voliti 配置下正常工作（configurable 注入不受影响）

### Step 1.13 — A2UI resume 容错

- **修改** `src/components/a2ui/A2UIInterruptHandler.tsx`
  - onSubmit/onReject 包裹 try-catch
  - 失败时显示"网络不好，请稍后重试"横幅，保持抽屉开放
  - 提供"跳过"按钮：发送带 `{ _network_failure: true }` 标记的 resume，让 Coach 知道"因网络问题未收集到数据"并自行跟进
  - **不能只关闭 UI 抽屉**：Thread 在 interrupted 状态，必须先成功 resume 才能继续对话

### Step 1.14 — Mirror 空状态处理

- Onboarding 未完成时 Mirror 面板默认折叠（`collapsedSize={0}`）
- `onboarding_complete` 标记变为 true 后自动展开面板

---

## Phase 2：Mirror 面板 + Witness Card + 设置（~3 天）

### Step 2.1 — Mirror 面板内容

- **新建** `src/components/mirror/MirrorPanel.tsx`
  - Chapter 信息（身份宣言 + 目标 + Day N）
  - North Star 指标（值 + delta + 7 日柱状图，用 Recharts BarChart）
  - 3 个支持指标
  - LifeSign 预案列表（trigger + success rate）
  - Witness Card 缩略图画廊

- **新建** `src/lib/store-sync.ts` — 对话结束后从 Store 获取数据更新面板
  - `/profile/dashboardConfig` → 面板配置
  - `/chapter/current.json` → Chapter 信息
  - `/coping_plans_index.md` → LifeSign 列表

### Step 2.2 — Witness Card 存储 + 回看

- **新建** `src/lib/witness-card-store.ts` — localStorage 存储（上限 20 张）
- Mirror 面板底部：缩略图画廊，点击放大

### Step 2.3 — 设置面板

- **新建** `src/components/settings/SettingsDrawer.tsx`
- Thinking 开关、语言、重置

---

## Phase 3：部署 + 打磨（~1-2 天）

- 验证 SSE 代理、A2UI 中断 resume、响应式
- Vercel 部署 + 自定义域名

---

## 后端调整清单

| 调整项 | 影响范围 | 说明 |
|--------|---------|------|
| Thread metadata 注入 `date` | graph.py | 从 configurable 读取 `date`，写入 thread metadata |
| Conversation archive 跨天检索 | 已支持 | `retrieve_conversation_archive` 按 `user_id` 搜索所有 Thread |
| Coach prompt 上下文加载 | 不变 | Store 按 user_id namespace，与 Thread 无关 |
| 每日 Thread 首条消息 | 可选 | Coach 在新 Thread 首次交互时自动加载 Store 摘要作为上下文 |

---

## 关键文件清单

### 参考（只读）
- `backend/src/voliti/a2ui.py` — A2UI 类型契约
- `frontend-ios/Voliti/Features/Coach/CoachViewModel.swift` — 流处理、清洗、中断逻辑
- `frontend-ios/Voliti/Core/Network/LangGraphAPI.swift` — 请求体结构

### 新建（~22 个文件）
```
frontend-web/src/
├── middleware.ts
├── app/login/page.tsx
├── lib/
│   ├── a2ui.ts
│   ├── store-sync.ts
│   └── witness-card-store.ts
├── components/
│   ├── layout/ResizableLayout.tsx
│   ├── history/HistorySidebar.tsx
│   ├── mirror/MirrorPanel.tsx
│   ├── a2ui/
│   │   ├── A2UIDrawer.tsx
│   │   ├── A2UIRenderer.tsx
│   │   ├── A2UIInterruptHandler.tsx
│   │   ├── SliderInput.tsx
│   │   ├── TextInput.tsx
│   │   ├── NumberInput.tsx
│   │   ├── SelectInput.tsx
│   │   ├── MultiSelectInput.tsx
│   │   ├── ProtocolPromptCard.tsx
│   │   └── ImageDisplay.tsx
│   ├── thread/ThinkingCard.tsx
│   ├── OnboardingWelcome.tsx
│   └── settings/SettingsDrawer.tsx
```

### 修改（~5 个文件）
- `src/components/thread/index.tsx` — 三栏布局、suggested replies、设置按钮
- `src/components/thread/messages/ai.tsx` — 中断分发、fenced block 清洗、ThinkingCard
- `src/providers/Stream.tsx` — 移除配置表单、注入 Voliti configurable、每日 Thread 逻辑
- `src/providers/Thread.tsx` — 按 user_id 搜索 Thread
- `src/app/globals.css` + `tailwind.config.js` — 设计系统

---

## 验证方案

1. **本地端到端**：backend dev server (port 2025) + frontend dev → 完整走通 onboarding → daily check-in → A2UI → Witness Card
2. **按天 Thread**：次日打开自动创建新 Thread；侧边栏按天分组显示；旧天对话可浏览
3. **三栏拖拽**：两侧可独立折叠/展开；拖拽手柄调整宽度；刷新后尺寸保持
4. **A2UI 中断**：submit/reject/skip 三种 action 正确 resume
5. **Fenced block**：流式过程中 coach_thinking / suggested_replies 不闪烁
6. **密码登录**：未登录重定向 /login；错误密码拒绝；正确密码进入
7. **移动端**：375px 宽度下两侧默认折叠；左侧覆盖层展开

---

## 技术风险

| 风险 | 缓解 |
|------|------|
| SSE 代理缓冲 | agent-chat-ui 主用例就是 SSE，先验证 |
| 中断 resume 协议不匹配 | 精确对标 iOS `resumeInterrupt` 请求体 |
| Thread metadata 搜索 bug | LangGraph GitHub #3298 报告过，部署前先验证 |
| LXGW WenKai 字体加载 | `next/font/local` 自托管 WOFF2 |
| react-resizable-panels SSR hydration | 用 cookie storage 替代 localStorage |

---

## CEO Review 扩展决策

| # | 扩展项 | 工量 | 决策 |
|---|--------|------|------|
| 1 | 用户反馈收集（浮动按钮 + Store） | S | ACCEPTED |
| 2 | 消息级 👍/👎 评价（LangSmith feedback） | S | ACCEPTED |
| 3 | 使用数据埋点（PostHog） | M | ACCEPTED |
| 4 | 消息编辑（agent-chat-ui 已有） | S | ACCEPTED |
| 5 | 暗色模式 | M | SKIPPED |

## CEO Review Findings

- **CRITICAL GAP（已修复）**：A2UI resume 失败时抽屉卡死 → 加入 try-catch + 重试 + 强制关闭
- **空状态设计**：Onboarding 未完成时 Mirror 面板默认折叠
- **已知限制**：按天 Thread 多 Tab 竞态（10 用户阶段可接受）

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-12 | 初始创建：基于导师反馈的 Web MVP 方案 B+ 详细实现计划 |
| 2026-04-12 | CEO Review (SELECTIVE EXPANSION): +4 扩展（反馈收集、👍/👎、PostHog、消息编辑），+A2UI 容错，+Mirror 空状态 |
| 2026-04-12 | Eng Review: date 改为 thread metadata（非 configurable）；A2UI 容错改为横幅+fallback resume；feedback namespace 修正；+4 核心测试区域 |

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | CLEAR | 5 proposals, 4 accepted, 0 deferred |
| Codex Review | `/codex review` | Independent 2nd opinion | 1 | issues_found | 10 findings, key issues addressed |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 3 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**CROSS-MODEL:** Codex 发现 10 个问题，其中 #1 (date metadata) 与 eng review 重合并已修正。#4 (A2UI 状态一致性) 是最有价值的新发现，已采纳并改进为 fallback resume 方案。#10 (整体过重) 是战略判断，CEO review 已讨论确认。
**UNRESOLVED:** 0
**VERDICT:** CEO + ENG CLEARED — ready to implement. 建议实现完成后运行 `/design-review`。
