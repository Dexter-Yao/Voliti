# Changelog

All notable changes to Voliti will be documented in this file.

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
