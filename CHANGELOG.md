# Changelog

All notable changes to Voliti will be documented in this file.

## [0.1.2.0] - 2026-04-09

### Fixed
- JourneyAnalysisMiddleware 因缺少 summarizer model profile 导致完全不可用
- eval judge.py 和 report.html.j2 中 A2UI 字段名未随 content→text, name→key 重命名同步
- eval cli.py `from copy import replace` 在 Python 3.12 下报 ImportError
- eval config.py 默认端口 2024 与实际 dev server 端口 2025 不一致
- fan_out 工具 Pydantic ValidationError 直接上溢到 LangGraph runtime，改为返回友好错误
- 全链路 timeout 统一为 `defaults.yaml` 的 `turn_timeout_seconds`（300s）单一来源，Judge/Auditor/CoachClient/图片生成 API 不再各自硬编码
- 错误消息泄露内部实现细节（Azure 错误码、endpoint URL）到 Coach 对话
- clearUserStore 遗漏 interventions/timeline/derived/coach 四个 namespace，重置不彻底
- SSEClient 未解析 LangGraph error 事件类型，用户在 Agent 出错时无限等待
- InputBar 建议回复 pill 字号 14px 不符合 DESIGN.md 规格 13px
- ThinkingCard 展开区字号 14px 与标题 13px 层级倒挂
- Onboarding Coach 标识使用固定 minHeight 而非 DESIGN.md 要求的垂直 30% 定位

### Changed
- processStream 嵌套 Task 提取为 postStreamSync() 方法，存储 syncTask 引用支持取消
- upgradeCardImage 改为传递 PersistentIdentifier 而非 @Model 引用（Swift 6 并发安全）
- 依赖约束收紧：deepagents <0.5.0 上限、openai >=2.0.0、eval jinja2 >=3.1.6

### Removed
- eval report.py model_pass_any 死代码

## [0.1.1.0] - 2026-04-09

### Fixed
- Onboarding 对话滚动失效：fullScreenCover 内 ScrollView 需 NavigationStack 包裹才能正确传递手势
- Onboarding 推荐回复 pill 横向滚动：fixedSize 使 pill 文本不被截断
- Onboarding 完成检测：新增本地 fallback（3+ Coach 回复即标记完成），防止 Store 不可用时用户永久卡在 Onboarding
- A2UI 字段名前后端不一致：content→text, name→key 全链路重命名（Pydantic 模型、Swift 类型、渲染器、测试）
- fan_out 工具有时以 JSON 文本而非 tool call 输出：prompt 明确要求 tool call 调用
- 12 处设计规格偏差：字体大小、边距、颜色对齐 DESIGN.md（ThinkingCard、TimestampSeparator、SettingsView、NorthStarMetric、InputBar、TabBar）

### Added
- OnboardingGreeting 共享常量：客户端即时显示 + 后端 prepend 使用同一文案源
- Coach 问候语后端对齐：首条用户消息附带 priorAssistantMessage 确保 LangGraph 对话历史完整

### Changed
- A2UI 协议字段规范化：TextComponent.content→text, 输入组件 name→key（单一事实原则）
- pitch 材料归入 docs/pitch/ 子目录
- 清理已完成的临时实施计划文档

## [0.1.0.0] - 2026-04-07

Initial tracked version. Witness Card 见证系统、Coach 时间感知、S-PDCA 行为对齐核心。
