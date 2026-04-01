# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 产品上下文

Constellate 是基于教练协议的长期行为对齐系统，减脂为首个落地场景。核心方法论：**S-PDCA（State → Plan → Do → Check → Act）**。

本仓库为 Monorepo，包含 iOS 原生客户端和 Python/LangGraph 云端后端。

关键参考文档：
- `docs/01_Product_Foundation.md` — 产品定位、理论基础、系统逻辑与数据架构
- `docs/02_Design_System.md` — 设计系统规范（Starpath Protocol）
- `docs/design-system/design-tokens.json` — 设计 tokens（颜色、字号、间距精确值）
- `docs/design-system/component-rules.json` — 组件渲染规则

## 项目结构

```
Constellate/
├── frontend-ios/     — iOS 原生客户端（SwiftUI + SwiftData）
├── backend/          — Python/LangGraph 云端后端（Coach Agent）
└── docs/             — 共享文档（产品、设计系统、研究资料）
```

## 开发工具链

### Backend（Python）
- Python ≥ 3.12，包管理使用 **uv**（不使用 pip/poetry）
- `backend/pyproject.toml` 为依赖与配置来源
- 运行入口：`cd backend && uv run main.py`
- 开发服务器：`cd backend && uv run langgraph dev --port 2024`
- 添加依赖：`cd backend && uv add <package>`
- 部署：LangGraph Cloud

### Frontend-iOS（Swift）
- Swift 6+ / SwiftUI / SwiftData
- 最低部署目标：iOS 18
- 架构：MVVM + @Observable
- Xcode 项目路径：`frontend-ios/Constellate.xcodeproj`
- 依赖管理：Swift Package Manager（最小化第三方依赖）

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
- XCTest 单元测试，XCUITest UI 测试

## 架构约定

- 用户只面对单一 Coach Agent，后台分析对用户透明
- iOS 客户端通过 SSE 与 LangGraph 后端通信，A2UI 协议处理结构化交互
- 数据持久化使用 SwiftData（本地优先），后端状态存于 LangGraph Store
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
| 2026-02-08 | 品牌重命名 Aligner → Constellate |
| 2026-02-09 | 架构约定新增"简单可组合模式优先"原则 |
| 2026-02-12 | 文档重命名：统一层级编号前缀 |
| 2026-03-20 | 项目重组为 Monorepo（frontend-ios + backend + docs）；iOS 原生客户端迁移；文档路径 doc/ → docs/ |
| 2026-03-31 | 添加 gstack skills 配置段落 |
