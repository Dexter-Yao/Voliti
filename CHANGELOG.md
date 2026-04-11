# Changelog

All notable changes to Voliti will be documented in this file.

## [0.1.4.0] - 2026-04-12

### Added
- Mirror 日志区范围选择 sheet，支持 `近7天`、`近30天`、`近90天`、`本篇章` 与自定义日期范围
- `VolitiUITests` 最小 UI smoke，覆盖 Mirror 日志范围切换后的真实交互链路
- Mirror 日志范围与显示一致性的回归测试，覆盖空态、筛选后空态、范围扩大与无 chapter 边界

### Changed
- Mirror 页改为“长期镜面 + 独立日志浏览区”结构，日期范围仅作用于日志区，不再影响上半部分全局摘要
- Mirror 事件流改为按当前日志范围全量查询并惰性渲染，移除旧的“最近 N 条”分页语义
- 北极星指标、支持指标与历史页统一复用同一套显示语义，单位、数值格式与 `estimated` 标记保持一致

### Fixed
- stale 异常态改为提供明确“刷新数据”恢复动作，并在异常期间禁用日志范围切换
- 日志范围切换失败时，本地偏好不再提前写入，避免失败回退后界面状态与持久化状态分叉
- 测试环境默认改用内存容器，避免 UI 测试误写本地 SwiftData 数据
- Mirror 在无 chapter 时不再恢复或应用无效的 `本篇章` 日志范围

## [0.1.3.0] - 2026-04-12

### Fixed
- `session_type` 运行时契约改为 fail-closed，缺失或非法值不再静默回退到 `coaching`
- Journey Analysis 在真实 `awrap_model_call()` 路径中复用 DeepAgent backend factory，避免分析慢路径因拿不到 backend 而失效
- `MemoryLifecycleMiddleware` 改为在 `edit_file` / `write_file` 的真实写入面阻止未确认的权威语义写入
- conversation archive / retrieval 的 live integration 脚本改为使用运行当天日期作为 `time_hint`，避免 `all` 窗口检索因固定日期自然失效

### Added
- `backend/tests/test_session_type.py`，覆盖严格 `session_type` 解析与失败路径

### Changed
- 权威语义写入现在需要显式确认上下文：`semantic_write_confirmed`、`semantic_write_source_kind`、`semantic_write_source_name`

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
