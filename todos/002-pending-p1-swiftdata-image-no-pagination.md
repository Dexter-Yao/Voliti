---
status: done
priority: p1
issue_id: "002"
tags: [code-review, performance, ios]
dependencies: []
---

# SwiftData imageData 内联存储 + 消息/事件无分页加载

## Problem Statement

`ChatMessage.imageData` 和 `InterventionCard.imageData` 直接作为 SwiftData 属性存储二进制图片数据，未使用 `@Attribute(.externalStorage)`。同时 `CoachViewModel.loadMessages()`、`JournalViewModel.loadEvents()`、`MapViewModel.loadCards()` 均无 `fetchLimit`，全量加载所有记录。二者叠加：随使用时间增长，应用启动将加载所有历史图片到内存，导致 OOM。

## Findings

- `ChatMessage.swift:13` — `var imageData: Data?` 无 `.externalStorage`
- `InterventionCard.swift:10` — `var imageData: Data?` 无 `.externalStorage`
- `CoachViewModel.swift:218-226` — `FetchDescriptor<ChatMessage>` 无 fetchLimit、无 predicate
- `JournalViewModel.swift:22-25` — `FetchDescriptor<BehaviorEvent>` 无 fetchLimit
- `MapViewModel.swift:29-32` — `FetchDescriptor<InterventionCard>` 无 fetchLimit

## Proposed Solutions

### Option A: externalStorage + fetchLimit（推荐）
1. 两个 imageData 属性添加 `@Attribute(.externalStorage)`（2 行改动）
2. loadMessages 添加 fetchLimit=50 + reverse sort + threadID predicate
3. Journal/Map 添加 fetchLimit=30
- Pros: 最小改动，立即生效，SwiftData 自动处理迁移
- Cons: 需实现"加载更多"交互
- Effort: Small
- Risk: Low

## Acceptance Criteria

- [ ] imageData 使用 @Attribute(.externalStorage)
- [ ] loadMessages 有 fetchLimit 和 predicate
- [ ] Journal/Map 有 fetchLimit
- [ ] 1000 条消息时应用启动内存 < 100MB

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Performance Oracle Agent |
