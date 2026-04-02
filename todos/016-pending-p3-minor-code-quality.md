---
status: pending
priority: p3
issue_id: "016"
tags: [code-review, quality]
dependencies: []
---

# 其他代码质量小问题合集

## Problem Statement

多个低优先级代码质量改进项，单独不值得建 todo，合并处理。

## Findings

1. **A2UITextInput 命名不一致** — `TextInput.swift:6` 类名 `A2UITextInput` 带前缀，同目录其他组件（NumberInput/SliderInput/SelectInput）不带前缀
2. **CameraService 名称不精确** — 仅做图片压缩，不涉及相机功能，应为 `ImageCompressor`
3. **MessageList magic number** — `MessageList.swift:45` `.padding(.bottom, 80)` 硬编码
4. **UserDefaults key 硬编码** — `APIConfiguration.swift:22` `"voliti_thread_id"` 应提为常量
5. **LangGraphAPI URL 构建重复** — `buildStreamRequest` 和 `buildResumeRequest` 大量重复 header/URL 代码
6. **Registry 测试直接操作私有属性** — 应提供 `reset()` 类方法
7. **schemas.py Union vs | 不一致** — 混用 Union 和 | 语法
8. **PromptRegistry kwargs 类型** — `**kwargs: str` 过于严格，应为 `**kwargs: Any`
9. **experiential.py response 变量 shadowing** — Gemini response 和 A2UI response 同名
10. **StarpathTokens 6 个未使用 token** — fontSerif/fontSans/fontMono/lineHeightHeading/lineHeightData/mapCardImageRatio
11. **EventRow 无意义 computed properties** — `eventType`/`eventTypeLabel` 纯转发
12. **LangGraphAPI @unchecked Sendable** — 无可变状态，可去掉 @unchecked

## Proposed Solutions

批量处理，按文件分组修改。
- Effort: Medium (collectively)
- Risk: Low

## Acceptance Criteria

- [ ] 上述 12 项逐一处理
- [ ] 编译通过，测试通过

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | 多 Agent 综合 |
