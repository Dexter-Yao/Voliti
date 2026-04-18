# AGENTS.md

This file provides guidance to AI coding agents (Codex, Claude Code, etc.) when working with code in this repository.

## 产品上下文

Voliti 是 AI 减脂行为教练。底层提供饮食指导、运动建议、方案制定与每日跟进；差异化价值在于帮助用户在失控前预防、失控后防止螺旋、跨时间识别行为模式。核心方法论：**S-PDCA（State → Plan → Do → Check → Act）**。

本仓库为 Monorepo，包含 Web MVP、iOS 原生客户端和 Python/LangGraph 云端后端。

关键参考文档：

| 文档 | 路径 | 职责 |
|------|------|------|
| 产品定位 | `docs/01_Product_Foundation.md` | 理论基础、S-PDCA、目标人群、核心机制 |
| 设计理念 | `docs/02_Design_Philosophy.md` | 设计哲学（Why）、信息层级、交互原则、节奏设计 |
| 设计规格 | `DESIGN.md` | **tokens、色值、字号、组件规则、聊天规则（What + How）** |
| 系统架构 | `docs/03_Architecture.md` | 系统结构、组件关系、数据流、技术选型、DeepAgent 复用边界与守护清单 |
| Witness Card | `docs/04_Image_Generation.md` | Witness Card 图片生成技术、统一视觉体系、卡片结构 |
| 运行时契约 | `docs/05_Runtime_Contracts.md` | **共享持久化真相、Store、session、A2UI、错误、记忆分层、可观测性边界** |
| GTM 洞察 | `docs/06_Go_To_Market_Insights.md` | 走向市场的战略思考与定位分析 |
| 用户研究 | `docs/07_User_Research.md` | **综合研究报告：核心画像、跨源验证发现、产品与 GTM 含义** |
| 用户旅程地图 | `docs/08_Customer_Journey_Map.md` | **核心 Persona 端到端旅程、关键时刻、流失触发器与产品机会优先级** |
| 竞品格局 | `docs/09_Competitive_Landscape.md` | **中美竞品矩阵、白空间/红海判断、渠道与 AI 演进趋势** |
| 已知问题 | `docs/11_Known_Issues.md` | **记录当前确认存在、暂不阻断发布的技术问题边界、观察条件与升级准则** |
| Design Tokens | `docs/design-system/design-tokens.json` | 色彩、字体、间距精确值（机器可读） |
| 组件规则 | `docs/design-system/component-rules.json` | 组件渲染规则（机器可读） |
| 用户研究原始数据 | `docs/user-research/` | 访谈记录、社媒分析、问卷数据与平台级洞察 |
| 知识库 | `docs/knowledge/` | 行为科学理论基础、AI 教练有效性实证、评估方法论 |

## 项目结构

```
Voliti/
├── frontend-web/     — Web MVP（Next.js 15 + React 19 + Tailwind + shadcn/ui）
├── frontend-ios/     — iOS 原生客户端（SwiftUI + SwiftData）
├── backend/          — Python/LangGraph 云端后端（Coach Agent）
├── eval/             — Coach Agent 行为评估模块（Petri-inspired）
├── tests/contracts/  — 跨端契约夹具与 live integration 脚本
└── docs/             — 共享文档（产品、设计系统、研究资料）
```

## 开发工具链

### Backend（Python）
- Python ≥ 3.12，包管理使用 **uv**（不使用 pip/poetry）
- `backend/pyproject.toml` 为依赖与配置来源
- 运行入口：`cd backend && uv run main.py`
- 开发服务器：`cd backend && uv run langgraph dev --port 2025`
- 添加依赖：`cd backend && uv add <package>`
- 部署：LangGraph Cloud

### Eval（Python）
- 独立 Python 包，借鉴 Petri 框架评估 Coach Agent 行为合规性
- `eval/pyproject.toml` 为依赖与配置来源
- 运行评估：`cd eval && uv run python -m voliti_eval`（默认 lite profile，10 维 10 seed）
- 完整评估：`cd eval && uv run python -m voliti_eval --profile full`（15 维 16 seed）
- 多模型对比：`cd eval && uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3`
- 验证配置：`cd eval && uv run python -m voliti_eval --dry-run`
- 前置依赖：需先启动 backend dev server
- 评分体系：二元判定（PASS/FAIL），lite 10 维 / full 15 维，Must-Pass / Stretch 分级
- 参考文档：`eval/README.md`

### Frontend-Web（TypeScript）
- Next.js 15 / React 19 / TypeScript / Tailwind CSS 4 / shadcn/ui
- 包管理使用 **pnpm**（不使用 npm/yarn）
- `frontend-web/package.json` 为依赖与配置来源
- 开发服务器：`cd frontend-web && pnpm dev`（需先启动 backend dev server）
- 构建：`cd frontend-web && pnpm build`
- 添加依赖：`cd frontend-web && pnpm add <package>`
- 设计系统：Starpath v2（obsidian/parchment/copper + LXGW WenKai/DM Sans/JetBrains Mono）
- 三栏可拖拽布局：react-resizable-panels v4（History | Chat | Mirror）
- 认证：Supabase Auth（邮箱+密码），`user_id` 直接使用 Supabase UUID
- A2UI 组件库：8 种组件类型 + 拒绝理由 + 重置 + Cmd+Enter 快捷键，精确镜像 `backend/src/voliti/a2ui.py`

### Frontend-iOS（Swift）
- Swift 6+ / SwiftUI / SwiftData
- 最低部署目标：iOS 18
- 架构：MVVM + @Observable
- Xcode 项目路径：`frontend-ios/Voliti.xcodeproj`
- 依赖管理：Swift Package Manager（最小化第三方依赖）

## 默认验证入口

- frontend-web：`cd frontend-web && pnpm build`
- backend：`cd backend && uv run python -m pytest`
- eval：`cd eval && uv run python -m pytest`
- iOS：`xcodebuild test -project frontend-ios/Voliti.xcodeproj -scheme Voliti -destination 'platform=iOS Simulator,name=<simulator>' -only-testing:VolitiTests`
- 契约 live integration：`cd backend && uv run python ../tests/contracts/run_onboarding_completion_e2e.py`

## 代码规范

### 通用
- 所有文件以 `// ABOUTME:` 或对应注释格式开头
- 文档使用正式中文，正文 evergreen，变更日志独立
- 注释说明 WHAT 或 WHY，不提及历史或对比

### Python
- 全量类型标注与 docstring

### Swift
- 遵循 Apple API Design Guidelines 命名规范
- SwiftUI 优先于 UIKit
- Feature-based 项目结构分组
- Swift Testing 框架单元测试（VolitiTests target），XCUITest UI 测试

## 开发优先级

- **当前阶段以 Web 版（浏览器桌面端）为唯一开发目标**，iOS 版暂时搁置
- 所有设计、讨论、mockup 默认针对桌面浏览器（≥1280px），除非明确指定移动端
- UI 设计和交互方案以桌面宽屏比例为基准

## 架构约定

- 用户只面对单一 Coach Agent，后台分析对用户透明
- iOS / Web 客户端通过 SSE 与 LangGraph 后端通信，A2UI 协议处理结构化交互
- 共享持久化真相由 LangGraph Store 持有；客户端只承载设备本地状态、缓存与投影视图
- 单一事实原则贯穿数据链各层
- **简单可组合模式优先**：不引入无消费者的抽象分组，不预设分类体系

## gstack

Use the /browse skill from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.

Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /retro, /investigate, /document-release, /codex, /cso, /autoplan, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn.

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-08 | 初始创建：产品上下文、工具链、代码规范与架构约定 |
| 2026-02-08 | 品牌重命名 Aligner → Voliti |
| 2026-02-09 | 架构约定新增"简单可组合模式优先"原则 |
| 2026-02-12 | 文档重命名：统一层级编号前缀 |
| 2026-03-20 | 项目重组为 Monorepo（frontend-ios + backend + docs）；iOS 原生客户端迁移；文档路径 doc/ → docs/ |
| 2026-03-31 | 添加 gstack skills 配置段落 |
| 2026-04-04 | 新增 eval/ 评估模块；dev server 端口 2024 → 2025 |
| 2026-04-06 | Swift 测试框架更新 XCTest → Swift Testing（VolitiTests target） |
| 2026-04-07 | 图像生成文档从"干预 Prompt 模板"更新为"Witness Card 技术规格" |
| 2026-04-09 | Eval 工具链更新：二元评分、多模型对比（--compare）、Qwen 3.6 Plus 接入 |
| 2026-04-09 | 新增运行时契约文档；文档分工更新为产品 / 架构 / 契约结构 |
| 2026-04-10 | 同步跨端契约验证入口（conversation archive 系统后于 2026-04-13 删除） |
| 2026-04-12 | 文档体系精简 8 → 6：删除已完成的里程碑（05）和 Harness 方案（08），合并 DeepAgent 边界到架构文档；编号顺延；修正 Store key 示例；AGENTS.md 同步维护 |
| 2026-04-12 | 新增 frontend-web/ Web MVP（Next.js 15），项目结构、工具链、验证入口同步更新 |
| 2026-04-13 | 删除已完成的方案文档（docs/plans/）；架构约定修正为 iOS/Web 双端；AGENTS.md 同步 |
| 2026-04-13 | 天级 Thread 重组 Phase 1-3：删除 MemoryLifecycleMW + JourneyAnalysisMW + conversation archive 系统；新增 BriefingMW + briefing 计算 + 日终 Pipeline + Cron 触发；MemoryMW 4→3 路径；Coach prompt 精简；前端封存 thread 只读 + 常量集中 |
| 2026-04-13 | A2UI 增强（reject reason + 重置 + Cmd+Enter）；删除 agent-inbox 脚手架和死代码；架构文档新增 Web MVP 客户端章节 |
| 2026-04-13 | Eval lite profile 设为默认（10 维 10 seed）；Web QA 修复 6 项（tool 泄漏 + 设置面板 + onboarding 状态） |
| 2026-04-14 | 会话体验增强 5 项：记忆可见性 prompt 治理、daily_checkin 自动触发（A2UI）、Markdown 层次感引导 + blockquote copper 色、思考过渡态设计规格与实现、日摘要精简至 60 字 + 7 天滚动窗口注入 briefing |
| 2026-04-14 | 新增按天会话归档（conversation_archive/{date}.md）；Coach 三级记忆检索（memory/briefing → day_summary → grep archive）；禁止全量加载归档 |
| 2026-04-14 | 统一概念模型：Identity → Goal → Chapter → Process Goal → LifeSign 五层结构；Coach/Onboarding prompt 引入新概念；Mirror 面板适配；Store 契约新增 Goal 路径；eval 数据模型与 seeds 同步 |
| 2026-04-15 | onboarding surface、thread 语义与 Mirror 契约收口；运行时文档补齐外部认证边界 |
| 2026-04-15 | 认证重构：`VOLITI_USER_MAP` 密码门禁 → Supabase Auth（邮箱+密码）；`user_id` 使用 Supabase UUID；middleware 验证 session 并同步 `voliti_user_id` cookie；运行时契约与架构文档同步 |
| 2026-04-16 | 记忆体系重构：六维用户画像（profile/context.md）、四分区 Coach 记忆协议（coach/AGENTS.md）、剥离 DeepAgent 默认 memory_guidelines、Briefing 纳入 Goal/Chapter 摘要、Onboarding 扩展六维采集 |
| 2026-04-17 | 新增用户旅程地图文档（docs/08_Customer_Journey_Map.md）；补充核心 Persona 端到端旅程、关键时刻与优化优先级 |
| 2026-04-17 | 四种体验式干预手段 Skill 化：新增 `backend/skills/coach/` 四份 SKILL.md（future-self-dialogue / scenario-rehearsal / metaphor-collaboration / cognitive-reframing）；学术调研分册落入 `docs/experiential-interventions/`；新增 `docs/10_Experiential_Interventions.md` 应用方案；`SkillsGateMiddleware` 仅 coaching session 注入；`CompositeBackend` 新增 `/skills/coach/` 只读路由；A2UI 契约新增 `metadata.surface`（四取值含 `witness-card`）与 `intervention_kind`；Witness Card composer 补 `surface="witness-card"` |
| 2026-04-18 | Intervention 完整落地：四种 skill 各配专用工具 `fan_out_<kind>`（metadata + layout="full" 由代码硬编码）+ `agent.py` 动态扫描加载；`fan_out` 抽取 `_fan_out_core`；前端新增 `InterventionShell` + 四个 Layout（FutureSelf / Scenario / Metaphor / Reframing）+ 全屏 overlay（非 Sheet）；`DESIGN.md` 新增 Intervention 模式子章节（Common Shell / 四 Layout 规格 / 字号 clamp 最小值表）；`docs/05 § 8.5` 更新为 A2UI Metadata 语义键表；eval/seeds 新增 4 个 intervention 触发场景（full 16→20）；`docs/10` 精简为架构索引 |
| 2026-04-18 | 新增 `docs/11_Known_Issues.md`：记录 DeepAgents FilesystemMiddleware `context` 序列化 warning 的边界、影响范围、观察条件与升级准则 |
