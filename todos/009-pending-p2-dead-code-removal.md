---
status: pending
priority: p2
issue_id: "009"
tags: [code-review, simplicity]
dependencies: []
---

# 4 个未使用 Service/Feature 文件 + schemas.py 无生产消费者

## Problem Statement

5 个文件/模块共计 ~545 行代码无任何生产消费者，违反 YAGNI 原则。增加认知负担，给出错误的功能完整性印象。

## Findings

**iOS 死文件（~286 LOC）：**
- `Services/NotificationService.swift` (65 LOC) — 无任何引用
- `Services/HapticService.swift` (32 LOC) — 无任何调用
- `Features/Health/HealthKitManager.swift` (121 LOC) — 无任何实例化
- `Features/Health/HealthPermissionView.swift` (68 LOC) — 无任何展示路径

**后端死代码：**
- `backend/src/voliti/schemas.py` (~161 LOC) — 仅被 test_schemas.py 导入，无生产代码使用

**iOS 死类型（~83 LOC）：**
- `A2UITypes.swift:185-252` — `A2UIResponse`, `A2UIAction`, `AnyCodable` 未使用
- `A2UITypes.swift:61-72` — `encode(to:)` 未使用（仅解码）
- `CoachViewModel.swift:211-213` — `cancelStream()` 未调用

## Proposed Solutions

### Option A: 删除所有死代码（推荐）
移除上述文件和代码段。需要时从 git 历史恢复。
- Effort: Small
- Risk: None（无消费者）

### Option B: 保留 schemas.py 作为设计文档
仅删除 iOS 死文件，保留 schemas.py 并加注释标明为参考文档。
- Effort: Small

## Acceptance Criteria

- [ ] 所有死文件已删除
- [ ] Xcode 项目引用已清理
- [ ] 后端测试仍通过

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Code Simplicity Reviewer |
