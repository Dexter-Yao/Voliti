# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 产品上下文

Voliti 是基于教练协议的长期行为对齐系统，减脂为首个落地场景。核心方法论：**S-PDCA（State → Plan → Do → Check → Act）**。

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
| Design Tokens | `docs/design-system/design-tokens.json` | 色彩、字体、间距精确值（机器可读） |
| 组件规则 | `docs/design-system/component-rules.json` | 组件渲染规则（机器可读） |
| 设计系统参考 | `docs/design-system-reference/` | 设计语言、视觉规范、AI 生成指引（人类可读） |
| 用户研究 | `docs/user-research/` | 访谈记录、调研数据与跨访谈洞察 |
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
- 运行评估：`cd eval && uv run python -m voliti_eval`
- 多模型对比：`cd eval && uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3`
- 验证配置：`cd eval && uv run python -m voliti_eval --dry-run`
- 前置依赖：需先启动 backend dev server
- 评分体系：二元判定（PASS/FAIL），15 维度，Must-Pass / Stretch 分级
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
- 密码认证：VOLITI_USER_MAP 环境变量映射 password:user_id
- A2UI 组件库：8 种组件类型，精确镜像 `backend/src/voliti/a2ui.py`

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
| 2026-04-10 | 同步跨端契约验证入口与 conversation archive / retrieval live integration 入口 |
| 2026-04-12 | 文档体系精简 8 → 6：删除已完成的里程碑（05）和 Harness 方案（08），合并 DeepAgent 边界到架构文档；编号顺延；修正 Store key 示例；AGENTS.md 同步维护 |
| 2026-04-12 | 新增 frontend-web/ Web MVP（Next.js 15），项目结构、工具链、验证入口同步更新 |
| 2026-04-13 | 删除已完成的方案文档（docs/plans/）；架构约定修正为 iOS/Web 双端；AGENTS.md 同步 |
| 2026-04-13 | 天级 Thread 重组 Phase 1-3：删除 MemoryLifecycleMW + JourneyAnalysisMW + conversation archive 系统；新增 BriefingMW + briefing 计算 + 日终 Pipeline；MemoryMW 4→3 路径；Coach prompt 精简；前端封存 thread 只读 |
