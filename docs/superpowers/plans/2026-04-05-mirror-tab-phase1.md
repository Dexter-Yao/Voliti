# MIRROR Tab Phase 1: 基础框架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 3-Tab（COACH/MAP/JOURNAL）重组为 2-Tab（COACH/MIRROR），MIRROR 整合 Chapter 元数据、硬编码 Dashboard、统一事件流（含 InterventionCard 里程碑），带日折叠和类型过滤。

**Architecture:** MIRROR 是纯展示层，数据来源全部复用现有 SwiftData 模型（BehaviorEvent + InterventionCard + Chapter）。MirrorViewModel 合并原 JournalViewModel 和 MapViewModel 的查询逻辑。事件流新增 `signatureImage` 事件类型，通过 `cardId` 关联 InterventionCard。Dashboard 本阶段硬编码体重 + 卡路里两个指标。

**Tech Stack:** Swift 6 / SwiftUI / SwiftData / @Observable MVVM

**Phase 边界：**
- Phase 1（本计划）：2-Tab 重组 + Chapter Context + 硬编码 Dashboard + 统一事件流 + 过滤器 + 日折叠 + 里程碑详情
- Phase 0（后续独立计划）：LifeSign SSE 同步管道
- Phase 2（后续独立计划）：Coach 治理 Dashboard 配置 + LifeSign 展示

---

## File Map

### 新增文件
| File | Responsibility |
|------|----------------|
| `Features/Mirror/MirrorView.swift` | MIRROR 页主视图，组合四个区域 + 事件流 |
| `Features/Mirror/MirrorViewModel.swift` | 合并查询 Chapter + BehaviorEvent + InterventionCard |
| `Features/Mirror/ChapterContextSection.swift` | Chapter 身份宣言 + 目标 + Day N |
| `Features/Mirror/DashboardSection.swift` | 硬编码体重 + 卡路里指标卡片 |
| `Features/Mirror/PulseSection.swift` | 7 日趋势迷你图占位 |
| `Features/Mirror/EventStreamSection.swift` | 过滤器 + 日折叠 + 事件列表 |
| `Features/Mirror/FilterBar.swift` | 过滤器 pill 按钮组 |

### 修改文件
| File | Change |
|------|--------|
| `ContentView.swift` | 3-Tab → 2-Tab，MAP/JOURNAL → MIRROR |
| `Core/Data/Models/BehaviorEvent.swift` | 新增 `signatureImage` 事件类型 + `cardId` 字段 |
| `Core/Data/ModelContainerSetup.swift` | 无变化（模型不变） |
| `Features/Journal/EventRow.swift` | 新增 `signatureImage` 类型渲染（缩略图） |

### 保留不动
| File | Reason |
|------|--------|
| `Features/Map/CardDetailView.swift` | 里程碑详情页复用 |
| `Features/Map/CardGallery.swift` | 保留但 MIRROR 不使用（Phase 2 可能复用） |
| `Features/Journal/JournalView.swift` | 保留文件不删除，ContentView 不再引用 |
| `Features/Journal/JournalViewModel.swift` | 同上 |
| `Features/Map/MapView.swift` | 同上 |
| `Features/Map/MapViewModel.swift` | 同上 |

---

## Task 1: BehaviorEvent 扩展 signatureImage 事件类型

**Files:**
- Modify: `frontend-ios/Voliti/Core/Data/Models/BehaviorEvent.swift:7-27` (EventType enum)
- Modify: `frontend-ios/Voliti/Core/Data/Models/BehaviorEvent.swift:30-85` (BehaviorEvent class)

- [ ] **Step 1: 扩展 EventType 枚举**

在 `BehaviorEvent.swift` 的 `EventType` 枚举中新增 `signatureImage` case：

```swift
enum EventType: String, Codable {
    case meal
    case exercise
    case weighIn = "weigh_in"
    case waterIntake = "water_intake"
    case stateCheckin = "state_checkin"
    case goalUpdate = "goal_update"
    case appAction = "app_action"
    case signatureImage = "signature_image"

    var label: String {
        switch self {
        case .meal: "饮食"
        case .exercise: "运动"
        case .weighIn: "体重"
        case .waterIntake: "饮水"
        case .stateCheckin: "状态"
        case .goalUpdate: "目标"
        case .appAction: "操作"
        case .signatureImage: "里程碑"
        }
    }
}
```

- [ ] **Step 2: 新增 cardId 可选字段**

在 `BehaviorEvent` class 的属性列表中（`action` 字段后面），新增：

```swift
    // Signature Image
    var cardId: String?
```

- [ ] **Step 3: 构建并确认编译通过**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 4: Commit**

```bash
git add frontend-ios/Voliti/Core/Data/Models/BehaviorEvent.swift
git commit -m "feat: BehaviorEvent 新增 signatureImage 事件类型和 cardId 关联字段"
```

---

## Task 2: EventRow 支持 signatureImage 渲染

**Files:**
- Modify: `frontend-ios/Voliti/Features/Journal/EventRow.swift:56-77` (buildDataSummary)

- [ ] **Step 1: 在 buildDataSummary 中处理 signatureImage**

在 `buildDataSummary()` 的 switch 中，`goalUpdate, .appAction` case 前面新增：

```swift
        case .signatureImage:
            break
```

- [ ] **Step 2: 构建并确认编译通过**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Journal/EventRow.swift
git commit -m "feat: EventRow 支持 signatureImage 事件类型渲染"
```

---

## Task 3: FilterBar 过滤器组件

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/FilterBar.swift`

- [ ] **Step 1: 创建 FilterBar**

```swift
// ABOUTME: MIRROR 页事件流过滤器，单选 pill 按钮组
// ABOUTME: 过滤器映射：全部/里程碑（signatureImage）/数据（weighIn, stateCheckin）/饮食（meal, waterIntake）

import SwiftUI

enum EventFilter: String, CaseIterable {
    case all = "全部"
    case milestone = "里程碑"
    case data = "数据"
    case diet = "饮食"

    var matchingTypes: Set<EventType>? {
        switch self {
        case .all: nil
        case .milestone: [.signatureImage]
        case .data: [.weighIn, .stateCheckin]
        case .diet: [.meal, .waterIntake]
        }
    }

    func matches(_ event: BehaviorEvent) -> Bool {
        guard let types = matchingTypes else { return true }
        return types.contains(event.type)
    }
}

struct FilterBar: View {
    @Binding var selected: EventFilter

    var body: some View {
        HStack(spacing: StarpathTokens.spacingSM) {
            ForEach(EventFilter.allCases, id: \.self) { filter in
                Button {
                    selected = filter
                } label: {
                    Text(filter.rawValue)
                        .font(.system(size: StarpathTokens.fontSizeSM, weight: .medium))
                        .foregroundStyle(
                            filter == selected
                                ? StarpathTokens.parchment
                                : StarpathTokens.obsidian
                        )
                        .padding(.horizontal, StarpathTokens.spacingMD)
                        .padding(.vertical, StarpathTokens.spacingXS + 2)
                        .background(
                            filter == selected
                                ? StarpathTokens.obsidian
                                : Color.clear
                        )
                        .clipShape(Capsule())
                        .overlay {
                            if filter != selected {
                                Capsule()
                                    .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                            }
                        }
                }
            }
            Spacer()
        }
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/FilterBar.swift
git commit -m "feat: FilterBar 过滤器 pill 按钮组件"
```

---

## Task 4: MirrorViewModel

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/MirrorViewModel.swift`

- [ ] **Step 1: 创建 MirrorViewModel**

```swift
// ABOUTME: MIRROR 页 ViewModel，统一查询 Chapter + BehaviorEvent + InterventionCard
// ABOUTME: 提供按日分组事件、过滤、日折叠状态管理

import Foundation
import SwiftData
import Observation
import os

private let logger = Logger(subsystem: "com.voliti", category: "MirrorViewModel")

@MainActor
@Observable
final class MirrorViewModel {
    var chapter: Chapter?
    var cards: [InterventionCard] = []
    var groupedEvents: [(date: Date, events: [BehaviorEvent])] = []
    var selectedFilter: EventFilter = .all
    var expandedDates: Set<Date> = []
    var selectedCard: InterventionCard?

    private var allEvents: [BehaviorEvent] = []
    private var modelContext: ModelContext?

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadData()
    }

    func reload() {
        loadData()
    }

    // MARK: - Dashboard Data

    var latestWeight: Double? {
        allEvents
            .first { $0.type == .weighIn && $0.weightKg != nil }?
            .weightKg
    }

    var todayCalories: Int? {
        let calendar = Calendar.current
        let todayStart = calendar.startOfDay(for: .now)
        let meals = allEvents.filter {
            $0.type == .meal
                && $0.kcal != nil
                && calendar.startOfDay(for: $0.timestamp) == todayStart
        }
        guard !meals.isEmpty else { return nil }
        return meals.compactMap(\.kcal).reduce(0) { $0 + Int($1) }
    }

    // MARK: - Filtering

    var filteredGroupedEvents: [(date: Date, events: [BehaviorEvent])] {
        if selectedFilter == .all { return groupedEvents }
        return groupedEvents.compactMap { group in
            let filtered = group.events.filter { selectedFilter.matches($0) }
            return filtered.isEmpty ? nil : (date: group.date, events: filtered)
        }
    }

    // MARK: - Day Collapse

    func isExpanded(_ date: Date) -> Bool {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let yesterday = calendar.date(byAdding: .day, value: -1, to: today)!
        if date >= yesterday { return true }
        return expandedDates.contains(date)
    }

    func toggleExpanded(_ date: Date) {
        if expandedDates.contains(date) {
            expandedDates.remove(date)
        } else {
            expandedDates.insert(date)
        }
    }

    func eventCount(for date: Date) -> Int {
        let group = filteredGroupedEvents.first { $0.date == date }
        return group?.events.count ?? 0
    }

    // MARK: - Card Lookup

    func card(for cardId: String) -> InterventionCard? {
        cards.first { $0.id == cardId }
    }

    // MARK: - Delete

    func deleteCard(_ card: InterventionCard) {
        modelContext?.delete(card)
        cards.removeAll { $0.id == card.id }
    }

    // MARK: - Private

    private func loadData() {
        guard let modelContext else { return }

        // Chapter
        let chapterDescriptor = FetchDescriptor<Chapter>(
            sortBy: [SortDescriptor(\.startDate, order: .reverse)]
        )
        do {
            chapter = try modelContext.fetch(chapterDescriptor).first
        } catch {
            logger.error("Failed to load chapter: \(error.localizedDescription)")
        }

        // Cards
        var cardDescriptor = FetchDescriptor<InterventionCard>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        cardDescriptor.fetchLimit = 50
        do {
            cards = try modelContext.fetch(cardDescriptor)
        } catch {
            logger.error("Failed to load cards: \(error.localizedDescription)")
        }

        // Events
        var eventDescriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        eventDescriptor.fetchLimit = 200
        do {
            allEvents = try modelContext.fetch(eventDescriptor)
        } catch {
            logger.error("Failed to load events: \(error.localizedDescription)")
        }

        let calendar = Calendar.current
        var grouped: [Date: [BehaviorEvent]] = [:]
        for event in allEvents {
            let dayStart = calendar.startOfDay(for: event.timestamp)
            grouped[dayStart, default: []].append(event)
        }
        groupedEvents = grouped
            .sorted { $0.key > $1.key }
            .map { (date: $0.key, events: $0.value) }
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/MirrorViewModel.swift
git commit -m "feat: MirrorViewModel 统一查询 Chapter + Events + Cards"
```

---

## Task 5: ChapterContextSection

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/ChapterContextSection.swift`

- [ ] **Step 1: 创建 ChapterContextSection**

```swift
// ABOUTME: MIRROR 页 Chapter Context 区域
// ABOUTME: 展示当前 Chapter 身份宣言、目标、Day N

import SwiftUI

struct ChapterContextSection: View {
    let chapter: Chapter

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            // Chapter + Day
            Text("CHAPTER \(chapterNumber) · DAY \(chapter.currentDay)")
                .starpathMono()

            // 身份宣言
            Text(chapter.identityStatement)
                .starpathSerif(size: StarpathTokens.fontSizeLG)

            // 目标
            Text(chapter.goal)
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    private var chapterNumber: Int {
        // Chapter ID 暂无序号，用 1 占位
        1
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/ChapterContextSection.swift
git commit -m "feat: ChapterContextSection 展示身份宣言和目标"
```

---

## Task 6: DashboardSection

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/DashboardSection.swift`

- [ ] **Step 1: 创建 DashboardSection（硬编码体重 + 卡路里）**

```swift
// ABOUTME: MIRROR 页 Dashboard 区域，展示关键指标
// ABOUTME: Phase 1 硬编码体重 + 卡路里；Phase 2 由 Coach 配置

import SwiftUI

struct DashboardSection: View {
    let latestWeight: Double?
    let todayCalories: Int?

    var body: some View {
        HStack(spacing: StarpathTokens.spacingLG) {
            metricCard(
                label: "体重",
                value: latestWeight.map { String(format: "%.1f", $0) },
                unit: "KG"
            )

            StarpathDivider(opacity: 0.10, thickness: 1)
                .frame(width: 1, height: 40)

            metricCard(
                label: "今日卡路里",
                value: todayCalories.map { "\($0)" },
                unit: "KCAL"
            )

            Spacer()
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    private func metricCard(label: String, value: String?, unit: String) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(label)
                .starpathMono()

            HStack(alignment: .firstTextBaseline, spacing: StarpathTokens.spacingXS) {
                Text(value ?? "—")
                    .starpathSerif(size: StarpathTokens.fontSizeXL)

                Text(unit)
                    .starpathMono()
            }
        }
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/DashboardSection.swift
git commit -m "feat: DashboardSection 硬编码体重 + 卡路里指标卡片"
```

---

## Task 7: PulseSection 占位

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/PulseSection.swift`

- [ ] **Step 1: 创建 PulseSection 占位**

```swift
// ABOUTME: MIRROR 页 Pulse 区域，7 日行为趋势迷你图
// ABOUTME: Phase 1 占位实现，后续接入真实趋势数据

import SwiftUI

struct PulseSection: View {
    let mealCounts: [Int]

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text("7 日趋势")
                .starpathMono()

            if mealCounts.isEmpty {
                Text("数据积累中")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
            } else {
                HStack(alignment: .bottom, spacing: 4) {
                    ForEach(Array(mealCounts.enumerated()), id: \.offset) { _, count in
                        let maxCount = mealCounts.max() ?? 1
                        let height = maxCount > 0
                            ? CGFloat(count) / CGFloat(maxCount) * 32
                            : 0
                        Rectangle()
                            .fill(StarpathTokens.obsidian.opacity(0.3))
                            .frame(width: 8, height: max(2, height))
                    }
                }
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/PulseSection.swift
git commit -m "feat: PulseSection 7 日趋势迷你图占位"
```

---

## Task 8: EventStreamSection 统一事件流

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/EventStreamSection.swift`

- [ ] **Step 1: 创建 EventStreamSection**

```swift
// ABOUTME: MIRROR 页统一事件流区域
// ABOUTME: 日折叠、过滤器联动、里程碑缩略图、周边界粗线

import SwiftUI

struct EventStreamSection: View {
    let groups: [(date: Date, events: [BehaviorEvent])]
    let isExpanded: (Date) -> Bool
    let toggleExpanded: (Date) -> Void
    let eventCount: (Date) -> Int
    let cardLookup: (String) -> InterventionCard?
    var onCardTap: ((InterventionCard) -> Void)?

    var body: some View {
        LazyVStack(alignment: .leading, spacing: 0) {
            ForEach(Array(groups.enumerated()), id: \.element.date) { index, group in
                if isExpanded(group.date) {
                    // 展开状态：日期标题 + 事件列表
                    expandedDay(group: group, index: index)
                } else {
                    // 折叠状态：日期 + 事件数摘要
                    collapsedDay(date: group.date, count: group.events.count)
                }

                // 周边界粗线
                if isWeekBoundary(at: index) {
                    StarpathDivider(opacity: 0.15, thickness: 2)
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }
            }
        }
    }

    // MARK: - Expanded Day

    private func expandedDay(group: (date: Date, events: [BehaviorEvent]), index: Int) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            // 日期标题（可点击折叠，今天和昨天除外）
            dayHeader(date: group.date, count: group.events.count, canCollapse: canCollapse(group.date))
                .padding(.top, index == 0 ? 0 : StarpathTokens.spacingLG)
                .padding(.bottom, StarpathTokens.spacingSM)

            ForEach(group.events, id: \.id) { event in
                eventRow(event)
                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)
            }
        }
    }

    private func eventRow(_ event: BehaviorEvent) -> some View {
        Group {
            if event.type == .signatureImage, let cardId = event.cardId,
               let card = cardLookup(cardId) {
                milestoneRow(event: event, card: card)
            } else {
                EventRow(event: event)
                    .padding(.horizontal, StarpathTokens.spacingMD)
            }
        }
    }

    private func milestoneRow(event: BehaviorEvent, card: InterventionCard) -> some View {
        Button {
            onCardTap?(card)
        } label: {
            HStack(spacing: StarpathTokens.spacingMD) {
                // 缩略图
                if let imageData = card.imageData, let uiImage = UIImage(data: imageData) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 48, height: 48)
                        .clipped()
                } else {
                    Rectangle()
                        .fill(StarpathTokens.obsidian10)
                        .frame(width: 48, height: 48)
                }

                VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(event.type.label)
                            .starpathSans()
                        Spacer()
                        Text(event.timestamp, style: .time)
                            .starpathMono()
                    }
                    if let summary = event.summary, !summary.isEmpty {
                        Text(summary)
                            .starpathSans()
                            .foregroundStyle(StarpathTokens.obsidian)
                    }
                }
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingSM)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Collapsed Day

    private func collapsedDay(date: Date, count: Int) -> some View {
        Button {
            toggleExpanded(date)
        } label: {
            HStack {
                Text(date, format: .dateTime.month().day())
                    .starpathSans()
                Text("·")
                    .foregroundStyle(StarpathTokens.obsidian40)
                Text("\(count) 条记录")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: StarpathTokens.fontSizeXS))
                    .foregroundStyle(StarpathTokens.obsidian40)
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingSM)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Day Header

    private func dayHeader(date: Date, count: Int, canCollapse: Bool) -> some View {
        Button {
            if canCollapse { toggleExpanded(date) }
        } label: {
            HStack {
                Text(dayLabel(date))
                    .starpathSerif()
                if canCollapse {
                    Image(systemName: "chevron.down")
                        .font(.system(size: StarpathTokens.fontSizeXS))
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
                Spacer()
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
        }
        .buttonStyle(.plain)
        .disabled(!canCollapse)
    }

    // MARK: - Helpers

    private func canCollapse(_ date: Date) -> Bool {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let yesterday = calendar.date(byAdding: .day, value: -1, to: today)!
        return date < yesterday
    }

    private func dayLabel(_ date: Date) -> String {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        if date == today { return "今天" }
        let yesterday = calendar.date(byAdding: .day, value: -1, to: today)!
        if date == yesterday { return "昨天" }
        let formatter = DateFormatter()
        formatter.dateFormat = "M月d日"
        return formatter.string(from: date)
    }

    private func isWeekBoundary(at index: Int) -> Bool {
        guard index + 1 < groups.count else { return false }
        let calendar = Calendar.current
        let currentWeek = calendar.component(.weekOfYear, from: groups[index].date)
        let nextWeek = calendar.component(.weekOfYear, from: groups[index + 1].date)
        return currentWeek != nextWeek
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/EventStreamSection.swift
git commit -m "feat: EventStreamSection 统一事件流（日折叠 + 里程碑缩略图）"
```

---

## Task 9: MirrorView 主视图

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/MirrorView.swift`

- [ ] **Step 1: 创建 MirrorView**

```swift
// ABOUTME: MIRROR 页主视图，组合 Chapter Context + Dashboard + Pulse + Event Stream
// ABOUTME: 纯展示层，所有数据来自 MirrorViewModel

import SwiftUI
import SwiftData

struct MirrorView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = MirrorViewModel()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // Chapter Context
                if let chapter = viewModel.chapter {
                    ChapterContextSection(chapter: chapter)
                        .padding(.bottom, StarpathTokens.spacingLG)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }

                // Dashboard
                DashboardSection(
                    latestWeight: viewModel.latestWeight,
                    todayCalories: viewModel.todayCalories
                )
                .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // Pulse
                PulseSection(mealCounts: mealCountsLast7Days)
                    .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // Event Stream
                VStack(alignment: .leading, spacing: StarpathTokens.spacingMD) {
                    FilterBar(selected: $viewModel.selectedFilter)
                        .padding(.horizontal, StarpathTokens.spacingMD)
                        .padding(.top, StarpathTokens.spacingLG)

                    if viewModel.filteredGroupedEvents.isEmpty {
                        emptyState
                    } else {
                        EventStreamSection(
                            groups: viewModel.filteredGroupedEvents,
                            isExpanded: viewModel.isExpanded,
                            toggleExpanded: viewModel.toggleExpanded,
                            eventCount: viewModel.eventCount,
                            cardLookup: viewModel.card(for:),
                            onCardTap: { card in
                                viewModel.selectedCard = card
                            }
                        )
                    }
                }
            }
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
        .onAppear {
            viewModel.configure(modelContext: modelContext)
        }
        .fullScreenCover(item: $viewModel.selectedCard) { card in
            NavigationStack {
                CardDetailView(card: card) {
                    viewModel.deleteCard(card)
                }
            }
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("尚无行为记录")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("与 Coach 对话后，行为事件将自动记录在此")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL)
        .padding(.horizontal, StarpathTokens.spacingXL)
    }

    // MARK: - Pulse Data

    private var mealCountsLast7Days: [Int] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        return (0..<7).reversed().map { daysAgo in
            let date = calendar.date(byAdding: .day, value: -daysAgo, to: today)!
            return viewModel.groupedEvents
                .first { $0.date == date }?
                .events.filter { $0.type == .meal }.count ?? 0
        }
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/MirrorView.swift
git commit -m "feat: MirrorView 主视图组合四个区域"
```

---

## Task 10: ContentView 3-Tab → 2-Tab

**Files:**
- Modify: `frontend-ios/Voliti/ContentView.swift`

- [ ] **Step 1: 更新 ContentView**

修改 `ContentView.swift`，将 3 个 tab 改为 2 个：

将 `private let tabs = ["COACH", "MAP", "JOURNAL"]` 改为：
```swift
    private let tabs = ["COACH", "MIRROR"]
```

将 `switch selectedTab` 块改为：
```swift
                switch selectedTab {
                case 0: CoachView()
                case 1: MirrorView()
                default: CoachView()
                }
```

更新 Preview，移除不再需要的 `Chapter.self`（Chapter 仍在 ModelContainer 中，不改）：

Preview 部分不需要改动，因为 ModelContainer 注册的 model 类型不变。

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/ContentView.swift
git commit -m "feat: ContentView 3-Tab → 2-Tab（COACH + MIRROR）"
```

---

## Task 11: CoachViewModel 自动创建 signatureImage 事件

**Files:**
- Modify: `frontend-ios/Voliti/Features/Coach/CoachViewModel.swift:394-434` (persistInterventionCardIfAccepted)

当用户 accept 体验式干预时，除了保存 InterventionCard，还需同步创建一条 `signatureImage` 类型的 BehaviorEvent，以便在 MIRROR 事件流中展示。

- [ ] **Step 1: 在 persistInterventionCardIfAccepted 方法末尾创建 BehaviorEvent**

在 `persistInterventionCardIfAccepted` 方法中，`modelContext?.insert(card)` 之后、`if !onboardingComplete` 之前，插入：

```swift
        let event = BehaviorEvent(
            timestamp: card.timestamp,
            type: .signatureImage,
            evidence: "",
            summary: caption
        )
        event.cardId = card.id
        modelContext?.insert(event)
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Coach/CoachViewModel.swift
git commit -m "feat: 接受干预卡片时同步创建 signatureImage 事件"
```

---

## Task 12: 空状态引导文案

**Files:**
- Modify: `frontend-ios/Voliti/Features/Mirror/MirrorView.swift`

- [ ] **Step 1: 区分 Onboarding 未完成和已完成但无数据**

在 MirrorView 中，在 `Chapter Context` 区域之前，加入 Onboarding 未完成时的引导：

在 MirrorView 中新增属性：
```swift
    @AppStorage("onboardingComplete") private var onboardingComplete = false
```

替换整个 `VStack` 中的 `// Chapter Context` 块（从 `if let chapter` 到对应的 `}`），改为：

```swift
                // Chapter Context
                if let chapter = viewModel.chapter {
                    ChapterContextSection(chapter: chapter)
                        .padding(.bottom, StarpathTokens.spacingLG)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                } else if !onboardingComplete {
                    onboardingGuide
                        .padding(.bottom, StarpathTokens.spacingLG)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }
```

新增 `onboardingGuide` computed property：
```swift
    private var onboardingGuide: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text("与 Coach 完成首次对话后")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("这里会显示你的数据面板")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }
```

- [ ] **Step 2: 构建确认**

Run: `cd frontend-ios && xcodebuild build -scheme Voliti -destination 'platform=iOS Simulator,name=iPhone 16' -quiet 2>&1 | tail -5`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/MirrorView.swift
git commit -m "feat: MIRROR 空状态引导文案（Onboarding 前/后）"
```

---

## Task 13: MIRROR 数据自动刷新

**Files:**
- Modify: `frontend-ios/Voliti/Features/Mirror/MirrorView.swift`

当用户从 COACH tab 切回 MIRROR tab 时，需刷新数据。

- [ ] **Step 1: 添加 scenePhase 刷新**

在 MirrorView 的 `.onAppear` 后，加入 scenePhase 监听，在回到前台时也刷新：

```swift
        .onAppear {
            viewModel.configure(modelContext: modelContext)
        }
        .onChange(of: modelContext.hasChanges) { _, _ in
            viewModel.reload()
        }
```

注意：`modelContext.hasChanges` 不适合做刷新触发。改用更简单的方案——每次 `onAppear` 都 reload：

将 `.onAppear` 修改为：

```swift
        .onAppear {
            if viewModel.groupedEvents.isEmpty {
                viewModel.configure(modelContext: modelContext)
            } else {
                viewModel.reload()
            }
        }
```

实际上 `configure` 内部已经调用 `loadData()`，而 `reload()` 也调用 `loadData()`。简化为始终调用 `configure`：

保持 `.onAppear { viewModel.configure(modelContext: modelContext) }` 不变。`configure` 每次都重新执行 `loadData()`。无需额外刷新机制。

- [ ] **Step 2: 此 Task 实际无需修改代码**

MirrorViewModel 的 `configure()` 方法每次 `onAppear` 都会重新加载数据。SwiftUI 在 tab 切换时会触发 `onAppear`。无需额外处理。

跳过此 Task。

---

## Self-Review Checklist

### 1. Spec Coverage
| Spec Requirement | Task |
|------------------|------|
| 2-Tab 重组（COACH + MIRROR） | Task 10 |
| Chapter Context 区域 | Task 5 |
| Dashboard 硬编码体重 + 卡路里 | Task 6 |
| LifeSign 摘要卡片 | Phase 2 scope（本计划不含） |
| Pulse 7 日趋势 | Task 7 |
| 统一事件流 | Task 8 |
| 过滤器（全部/里程碑/数据/饮食） | Task 3 |
| 日折叠（今天昨天展开，更早折叠） | Task 8 |
| signatureImage 事件类型 | Task 1 |
| 里程碑缩略图 + 点击详情 | Task 8, Task 9 |
| CardDetailView 复用 | Task 9（fullScreenCover） |
| 空状态设计 | Task 12 |
| Coach 创建卡片时同步创建事件 | Task 11 |
| MAP/JOURNAL 文件保留不删 | File Map |

### 2. Placeholder Scan
- 无 TBD/TODO
- PulseSection 是功能性占位（用 meal count 数据驱动），不是空壳

### 3. Type Consistency
- `EventFilter` 在 FilterBar.swift 定义，MirrorViewModel 引用
- `EventType.signatureImage` 在 BehaviorEvent.swift 定义，FilterBar 和 EventStreamSection 引用
- `MirrorViewModel` 方法名一致：`isExpanded(_:)`, `toggleExpanded(_:)`, `eventCount(for:)`, `card(for:)`
- `selectedCard` 类型 `InterventionCard?`，与 `fullScreenCover(item:)` 一致
