# MIRROR Phase 0 + Phase 2: LifeSign 同步 + Coach 治理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 LifeSign 本地同步管道（Phase 0）和 Coach 治理的 Dashboard 配置 + LifeSign 摘要展示（Phase 2），让 MIRROR Tab 从静态骨架变为数据驱动的自我画像。

**Architecture:** 对话结束后 iOS 主动从 LangGraph Store 拉取 LifeSign 和 Dashboard 配置数据（pull-after-conversation），写入本地 SwiftData。MIRROR 页新增 LifeSign 摘要卡片（Dashboard 和 Pulse 之间），DashboardSection 改为由 Coach 配置驱动。Coach prompt 新增 Dashboard 配置指令和用户目标采集。BehaviorEvent 扩展 5 种 LifeSign 事件类型。

**Tech Stack:** Swift 6 / SwiftUI / SwiftData / Python / Jinja2 (Coach prompt)

---

## File Map

### 新增文件（iOS）
| File | Responsibility |
|------|----------------|
| `Core/Data/Models/LifeSignPlan.swift` | LifeSign 预案 SwiftData 模型 |
| `Core/Data/Models/DashboardConfig.swift` | Dashboard 指标配置 SwiftData 模型 |
| `Core/Network/StoreSyncService.swift` | LangGraph Store → SwiftData 同步服务 |
| `Features/Mirror/LifeSignSummaryCard.swift` | MIRROR 页 LifeSign 摘要卡片 |
| `Features/Mirror/LifeSignListView.swift` | LifeSign 预案列表页 |
| `Features/Mirror/LifeSignDetailView.swift` | LifeSign 预案详情页 |

### 修改文件（iOS）
| File | Change |
|------|--------|
| `Core/Data/Models/BehaviorEvent.swift` | 新增 5 种 LifeSign 事件类型 + planId/planName 字段 |
| `Core/Data/ModelContainerSetup.swift` | 注册 LifeSignPlan + DashboardConfig |
| `Core/Network/LangGraphAPI.swift` | 新增 searchStoreItems 方法 |
| `Features/Coach/CoachViewModel.swift` | processStream 结束后触发 Store 同步 |
| `Features/Mirror/MirrorView.swift` | 插入 LifeSignSummaryCard，DashboardSection 接 config |
| `Features/Mirror/MirrorViewModel.swift` | 加载 LifeSignPlan + DashboardConfig |
| `Features/Mirror/DashboardSection.swift` | 改为 config 驱动（动态指标列表） |
| `Features/Mirror/EventStreamSection.swift` | LifeSign 事件行渲染 |
| `Features/Journal/EventRow.swift` | LifeSign 事件 buildDataSummary |
| `VolitiApp.swift` | Preview 注册新模型 |
| `ContentView.swift` | Preview 注册新模型 |

### 修改文件（Backend）
| File | Change |
|------|--------|
| `backend/prompts/coach_system.j2` | Dashboard 配置指令 + 用户目标采集 + LifeSign 数据结构约束 |

---

## Task 1: LifeSignPlan SwiftData 模型

**Files:**
- Create: `frontend-ios/Voliti/Core/Data/Models/LifeSignPlan.swift`
- Modify: `frontend-ios/Voliti/Core/Data/ModelContainerSetup.swift`

- [ ] **Step 1: 创建 LifeSignPlan 模型**

```swift
// ABOUTME: LifeSign 预案 SwiftData 模型，从 LangGraph Store 同步
// ABOUTME: 存储 if-then 应对策略的本地镜像

import Foundation
import SwiftData

@Model
final class LifeSignPlan {
    var id: String
    var trigger: String
    var copingResponse: String
    var successCount: Int
    var totalAttempts: Int
    var status: String
    var lastUpdated: Date

    init(
        id: String,
        trigger: String,
        copingResponse: String,
        successCount: Int = 0,
        totalAttempts: Int = 0,
        status: String = "active",
        lastUpdated: Date = .now
    ) {
        self.id = id
        self.trigger = trigger
        self.copingResponse = copingResponse
        self.successCount = successCount
        self.totalAttempts = totalAttempts
        self.status = status
        self.lastUpdated = lastUpdated
    }

    var successRate: Double {
        guard totalAttempts > 0 else { return 0 }
        return Double(successCount) / Double(totalAttempts)
    }
}
```

- [ ] **Step 2: 注册到 ModelContainer**

在 `ModelContainerSetup.swift` 的 schema 数组中追加 `LifeSignPlan.self`：

```swift
let schema = Schema([
    ChatMessage.self,
    BehaviorEvent.self,
    InterventionCard.self,
    Chapter.self,
    LifeSignPlan.self,
])
```

- [ ] **Step 3: 同步更新 VolitiApp.swift 和 ContentView.swift 的 Preview modelContainer**

ContentView.swift Preview 中的 `modelContainer(for:)` 数组追加 `LifeSignPlan.self`。

- [ ] **Step 4: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 5: Commit**

```bash
git add frontend-ios/Voliti/Core/Data/Models/LifeSignPlan.swift frontend-ios/Voliti/Core/Data/ModelContainerSetup.swift frontend-ios/Voliti/ContentView.swift
git commit -m "feat: LifeSignPlan SwiftData 模型"
```

---

## Task 2: DashboardConfig SwiftData 模型

**Files:**
- Create: `frontend-ios/Voliti/Core/Data/Models/DashboardConfig.swift`
- Modify: `frontend-ios/Voliti/Core/Data/ModelContainerSetup.swift`

- [ ] **Step 1: 创建 DashboardConfig 模型**

```swift
// ABOUTME: Dashboard 指标配置 SwiftData 模型，由 Coach 在 Onboarding 配置
// ABOUTME: 存储用户需要追踪的指标列表和显示顺序

import Foundation
import SwiftData

@Model
final class DashboardConfig {
    var id: String
    var metrics: [DashboardMetric]
    var userGoal: String?
    var lastUpdated: Date

    init(
        id: String = "default",
        metrics: [DashboardMetric] = [],
        userGoal: String? = nil,
        lastUpdated: Date = .now
    ) {
        self.id = id
        self.metrics = metrics
        self.userGoal = userGoal
        self.lastUpdated = lastUpdated
    }
}

struct DashboardMetric: Codable, Hashable {
    let key: String
    let label: String
    let unit: String
    let order: Int
}
```

- [ ] **Step 2: 注册到 ModelContainer**

在 `ModelContainerSetup.swift` 的 schema 数组中追加 `DashboardConfig.self`：

```swift
let schema = Schema([
    ChatMessage.self,
    BehaviorEvent.self,
    InterventionCard.self,
    Chapter.self,
    LifeSignPlan.self,
    DashboardConfig.self,
])
```

同步更新 ContentView.swift Preview。

- [ ] **Step 3: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 4: Commit**

```bash
git add frontend-ios/Voliti/Core/Data/Models/DashboardConfig.swift frontend-ios/Voliti/Core/Data/ModelContainerSetup.swift frontend-ios/Voliti/ContentView.swift
git commit -m "feat: DashboardConfig SwiftData 模型"
```

---

## Task 3: LangGraphAPI 扩展 — searchStoreItems

**Files:**
- Modify: `frontend-ios/Voliti/Core/Network/LangGraphAPI.swift`

现有 `fetchStoreItem` 按 namespace + key 获取单个 item。LifeSign 同步需要列出 `coping_plans/` 下的所有 item。LangGraph Store API 支持 `POST /store/items/search` 按 namespace prefix 搜索。

- [ ] **Step 1: 新增 searchStoreItems 方法**

在 `LangGraphAPI.swift` 的 `// MARK: - Store` 区域内，`fetchStoreItem` 方法后面追加：

```swift
    /// 从 LangGraph Store 搜索指定 namespace 下的所有 items
    func searchStoreItems(namespace: [String]) async throws -> [[String: Any]] {
        let url = APIConfiguration.baseURL.appendingPathComponent("store/items/search")

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        Self.applyAuth(&request)

        let body: [String: Any] = [
            "namespace_prefix": namespace,
            "limit": 100,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        try validateResponse(response)

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let items = json["items"] as? [[String: Any]] else {
            return []
        }
        return items
    }
```

- [ ] **Step 2: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Core/Network/LangGraphAPI.swift
git commit -m "feat: LangGraphAPI 新增 searchStoreItems 按 namespace 搜索"
```

---

## Task 4: StoreSyncService — Store → SwiftData 同步

**Files:**
- Create: `frontend-ios/Voliti/Core/Network/StoreSyncService.swift`

- [ ] **Step 1: 创建 StoreSyncService**

```swift
// ABOUTME: LangGraph Store → SwiftData 同步服务
// ABOUTME: 对话结束后拉取 LifeSign 和 DashboardConfig，写入本地

import Foundation
import SwiftData
import os

private let logger = Logger(subsystem: "com.voliti", category: "StoreSyncService")

@MainActor
final class StoreSyncService {
    private let api = LangGraphAPI()
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    // MARK: - Full Sync

    func syncAll() async {
        await syncLifeSignPlans()
        await syncDashboardConfig()
    }

    // MARK: - LifeSign Plans

    func syncLifeSignPlans() async {
        do {
            let items = try await api.searchStoreItems(
                namespace: ["voliti", "user", "coping_plans"]
            )

            for item in items {
                guard let value = item["value"] as? [String: Any],
                      let planId = value["id"] as? String else { continue }

                let trigger = value["trigger"] as? String ?? ""
                let copingResponse = value["coping_response"] as? String ?? ""
                let successCount = value["success_count"] as? Int ?? 0
                let totalAttempts = value["total_attempts"] as? Int ?? 0
                let status = value["status"] as? String ?? "active"
                let lastUpdatedStr = value["last_updated"] as? String

                let lastUpdated: Date
                if let str = lastUpdatedStr {
                    lastUpdated = ISO8601DateFormatter().date(from: str) ?? .now
                } else {
                    lastUpdated = .now
                }

                // Upsert: 查找已有记录或创建新记录
                let descriptor = FetchDescriptor<LifeSignPlan>(
                    predicate: #Predicate { $0.id == planId }
                )
                if let existing = try modelContext.fetch(descriptor).first {
                    existing.trigger = trigger
                    existing.copingResponse = copingResponse
                    existing.successCount = successCount
                    existing.totalAttempts = totalAttempts
                    existing.status = status
                    existing.lastUpdated = lastUpdated
                } else {
                    let plan = LifeSignPlan(
                        id: planId,
                        trigger: trigger,
                        copingResponse: copingResponse,
                        successCount: successCount,
                        totalAttempts: totalAttempts,
                        status: status,
                        lastUpdated: lastUpdated
                    )
                    modelContext.insert(plan)
                }
            }

            // 删除 Store 中不存在的本地记录
            let remoteIds = Set(items.compactMap { ($0["value"] as? [String: Any])?["id"] as? String })
            let allLocal = try modelContext.fetch(FetchDescriptor<LifeSignPlan>())
            for local in allLocal where !remoteIds.contains(local.id) {
                modelContext.delete(local)
            }

            logger.info("LifeSign sync: \(items.count) plans from Store")
        } catch {
            logger.error("LifeSign sync failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Dashboard Config

    func syncDashboardConfig() async {
        do {
            guard let value = try await api.fetchStoreItem(
                namespace: ["voliti", "user", "profile"],
                key: "dashboardConfig"
            ) else {
                logger.info("No dashboardConfig in Store")
                return
            }

            guard let metricsRaw = value["metrics"] as? [[String: Any]] else { return }

            let metrics = metricsRaw.enumerated().compactMap { index, raw -> DashboardMetric? in
                guard let key = raw["key"] as? String,
                      let label = raw["label"] as? String else { return nil }
                let unit = raw["unit"] as? String ?? ""
                let order = raw["order"] as? Int ?? index
                return DashboardMetric(key: key, label: label, unit: unit, order: order)
            }

            let userGoal = value["user_goal"] as? String

            let descriptor = FetchDescriptor<DashboardConfig>(
                predicate: #Predicate { $0.id == "default" }
            )
            if let existing = try modelContext.fetch(descriptor).first {
                existing.metrics = metrics.sorted { $0.order < $1.order }
                existing.userGoal = userGoal
                existing.lastUpdated = .now
            } else {
                let config = DashboardConfig(
                    metrics: metrics.sorted { $0.order < $1.order },
                    userGoal: userGoal
                )
                modelContext.insert(config)
            }

            logger.info("Dashboard config sync: \(metrics.count) metrics")
        } catch {
            logger.error("Dashboard config sync failed: \(error.localizedDescription)")
        }
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Core/Network/StoreSyncService.swift
git commit -m "feat: StoreSyncService — LangGraph Store → SwiftData 同步"
```

---

## Task 5: CoachViewModel 集成同步触发

**Files:**
- Modify: `frontend-ios/Voliti/Features/Coach/CoachViewModel.swift`

对话结束后（processStream finalize 时）触发 StoreSyncService.syncAll()。

- [ ] **Step 1: 添加 syncService 属性和同步调用**

在 CoachViewModel 中添加一个 `syncService` 惰性属性。在 `processStream` 方法的 finalize 块（`await MainActor.run { ... }` 最后，`self.isStreaming = false` 之后）追加同步调用：

在 CoachViewModel 类中，`private var streamTask` 声明之后新增：

```swift
    private var syncService: StoreSyncService?
```

修改 `configure(modelContext:)` 方法，在 `loadMessages()` 之前初始化 syncService：

```swift
    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        self.syncService = StoreSyncService(modelContext: modelContext)
        loadMessages()
    }
```

在 `processStream` 方法的 finalize 块中，`self.isStreaming = false` 之后追加：

```swift
            // 对话结束后同步 Store 数据到本地
            Task { [weak self] in
                await self?.syncService?.syncAll()
            }
```

- [ ] **Step 2: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Coach/CoachViewModel.swift
git commit -m "feat: 对话结束后触发 Store 同步（LifeSign + DashboardConfig）"
```

---

## Task 6: BehaviorEvent 扩展 LifeSign 事件类型

**Files:**
- Modify: `frontend-ios/Voliti/Core/Data/Models/BehaviorEvent.swift`
- Modify: `frontend-ios/Voliti/Features/Journal/EventRow.swift`

- [ ] **Step 1: 新增 5 种 LifeSign 事件类型到 EventType 枚举**

在 `signatureImage` case 之后追加：

```swift
    case lifesignCreated = "lifesign_created"
    case lifesignUpdated = "lifesign_updated"
    case lifesignDeleted = "lifesign_deleted"
    case lifesignActivated = "lifesign_activated"
    case lifesignSucceeded = "lifesign_succeeded"
```

在 `label` computed property 中追加：

```swift
        case .lifesignCreated: "预案创建"
        case .lifesignUpdated: "预案更新"
        case .lifesignDeleted: "预案删除"
        case .lifesignActivated: "预案激活"
        case .lifesignSucceeded: "预案成功"
```

- [ ] **Step 2: 新增 LifeSign 事件字段到 BehaviorEvent**

在 `cardId` 字段之后追加：

```swift
    // LifeSign
    var planId: String?
    var planName: String?
```

- [ ] **Step 3: EventRow.buildDataSummary 处理新类型**

在 EventRow.swift 的 `buildDataSummary()` switch 中，`.signatureImage` case 前追加：

```swift
        case .lifesignCreated, .lifesignUpdated, .lifesignDeleted,
             .lifesignActivated, .lifesignSucceeded:
            if let name = event.planName { parts.append(name) }
```

- [ ] **Step 4: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 5: Commit**

```bash
git add frontend-ios/Voliti/Core/Data/Models/BehaviorEvent.swift frontend-ios/Voliti/Features/Journal/EventRow.swift
git commit -m "feat: BehaviorEvent 新增 5 种 LifeSign 事件类型 + planId/planName"
```

---

## Task 7: LifeSignSummaryCard 摘要卡片

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/LifeSignSummaryCard.swift`

CEO 审查决策：LifeSign 从事件流过滤器上提到 Dashboard 区域的独立摘要卡片，位于 Dashboard 和 Pulse 之间。

- [ ] **Step 1: 创建 LifeSignSummaryCard**

```swift
// ABOUTME: MIRROR 页 LifeSign 摘要卡片，Dashboard 与 Pulse 之间的独立一级入口
// ABOUTME: 展示预案数量和本周执行统计，点击进入 LifeSign 列表

import SwiftUI

struct LifeSignSummaryCard: View {
    let plans: [LifeSignPlan]
    var onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                Text("LIFESIGN")
                    .starpathMono()

                if plans.isEmpty {
                    Text("与 Coach 对话中创建你的第一个应对预案")
                        .starpathSans()
                        .foregroundStyle(StarpathTokens.obsidian40)
                } else {
                    let active = plans.filter { $0.status == "active" }
                    let totalSuccess = active.reduce(0) { $0 + $1.successCount }
                    let totalAttempts = active.reduce(0) { $0 + $1.totalAttempts }

                    HStack(spacing: StarpathTokens.spacingSM) {
                        Text("\(active.count) 预案")
                            .starpathSans()

                        Text("·")
                            .foregroundStyle(StarpathTokens.obsidian40)

                        if totalAttempts > 0 {
                            Text("激活 \(totalAttempts) 成功 \(totalSuccess)")
                                .starpathSans()
                                .foregroundStyle(StarpathTokens.obsidian40)
                        } else {
                            Text("待激活")
                                .starpathSans()
                                .foregroundStyle(StarpathTokens.obsidian40)
                        }

                        Spacer()

                        Image(systemName: "chevron.right")
                            .font(.system(size: StarpathTokens.fontSizeXS))
                            .foregroundStyle(StarpathTokens.obsidian40)
                    }
                }
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
        }
        .buttonStyle(.plain)
    }
}
```

- [ ] **Step 2: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 3: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/LifeSignSummaryCard.swift
git commit -m "feat: LifeSignSummaryCard 摘要卡片（Dashboard 与 Pulse 之间）"
```

---

## Task 8: LifeSignListView + LifeSignDetailView

**Files:**
- Create: `frontend-ios/Voliti/Features/Mirror/LifeSignListView.swift`
- Create: `frontend-ios/Voliti/Features/Mirror/LifeSignDetailView.swift`

- [ ] **Step 1: 创建 LifeSignListView**

```swift
// ABOUTME: LifeSign 预案列表页，从摘要卡片点击进入
// ABOUTME: 展示所有 active 预案，点击进入详情

import SwiftUI

struct LifeSignListView: View {
    let plans: [LifeSignPlan]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 0) {
                ForEach(activePlans, id: \.id) { plan in
                    NavigationLink {
                        LifeSignDetailView(plan: plan)
                    } label: {
                        planRow(plan)
                    }
                    .buttonStyle(.plain)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }
            }
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
        .navigationTitle("LifeSign")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("关闭") { dismiss() }
                    .foregroundStyle(StarpathTokens.obsidian)
            }
        }
    }

    private var activePlans: [LifeSignPlan] {
        plans.filter { $0.status == "active" }
            .sorted { $0.lastUpdated > $1.lastUpdated }
    }

    private func planRow(_ plan: LifeSignPlan) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(plan.trigger)
                .starpathSans()

            Text("→ \(plan.copingResponse)")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)

            HStack(spacing: StarpathTokens.spacingSM) {
                if plan.totalAttempts > 0 {
                    Text("\(plan.successCount)/\(plan.totalAttempts) 成功")
                        .starpathMono()
                } else {
                    Text("待激活")
                        .starpathMono()
                }
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
        .padding(.vertical, StarpathTokens.spacingSM)
    }
}
```

- [ ] **Step 2: 创建 LifeSignDetailView**

```swift
// ABOUTME: LifeSign 预案详情页
// ABOUTME: 展示触发条件、应对行为、执行统计

import SwiftUI

struct LifeSignDetailView: View {
    let plan: LifeSignPlan

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingLG) {
                // 触发条件
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    Text("IF")
                        .starpathMono()
                    Text(plan.trigger)
                        .starpathSerif()
                }

                StarpathDivider()

                // 应对行为
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    Text("THEN")
                        .starpathMono()
                    Text(plan.copingResponse)
                        .starpathSerif()
                }

                StarpathDivider()

                // 执行统计
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    Text("统计")
                        .starpathMono()

                    HStack(spacing: StarpathTokens.spacingLG) {
                        statItem(label: "激活", value: "\(plan.totalAttempts)")
                        statItem(label: "成功", value: "\(plan.successCount)")
                        if plan.totalAttempts > 0 {
                            statItem(
                                label: "成功率",
                                value: "\(Int(plan.successRate * 100))%"
                            )
                        }
                    }
                }

                StarpathDivider()

                // 最后更新
                Text(plan.lastUpdated, style: .date)
                    .starpathMono()
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
    }

    private func statItem(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(label)
                .starpathMono()
            Text(value)
                .starpathSerif(size: StarpathTokens.fontSizeLG)
        }
    }
}
```

- [ ] **Step 3: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 4: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/LifeSignListView.swift frontend-ios/Voliti/Features/Mirror/LifeSignDetailView.swift
git commit -m "feat: LifeSign 列表页 + 详情页（IF/THEN + 执行统计）"
```

---

## Task 9: DashboardSection 改为 Config 驱动

**Files:**
- Modify: `frontend-ios/Voliti/Features/Mirror/DashboardSection.swift`

将 DashboardSection 从硬编码（体重 + 卡路里）改为由 DashboardConfig 驱动。当没有 config 时回退到默认的体重 + 卡路里。

- [ ] **Step 1: 重写 DashboardSection**

```swift
// ABOUTME: MIRROR 页 Dashboard 区域，展示关键指标
// ABOUTME: 由 Coach 配置驱动（DashboardConfig），无 config 时回退到体重 + 卡路里

import SwiftUI

struct DashboardSection: View {
    let config: DashboardConfig?
    let latestWeight: Double?
    let todayCalories: Int?
    let userGoal: String?

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingMD) {
            // 用户目标（如果有）
            if let goal = displayGoal, !goal.isEmpty {
                Text(goal)
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
            }

            // 指标卡片
            HStack(spacing: StarpathTokens.spacingLG) {
                ForEach(Array(displayMetrics.enumerated()), id: \.element.key) { index, metric in
                    if index > 0 {
                        StarpathDivider(opacity: 0.10, thickness: 1)
                            .frame(width: 1, height: 40)
                    }
                    metricCard(
                        label: metric.label,
                        value: metricValue(for: metric.key),
                        unit: metric.unit
                    )
                }
                Spacer()
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    // MARK: - Display Logic

    private var displayGoal: String? {
        userGoal ?? config?.userGoal
    }

    private var displayMetrics: [DashboardMetric] {
        if let config, !config.metrics.isEmpty {
            return config.metrics.sorted { $0.order < $1.order }
        }
        // 回退默认指标
        return [
            DashboardMetric(key: "weight", label: "体重", unit: "KG", order: 0),
            DashboardMetric(key: "calories", label: "今日卡路里", unit: "KCAL", order: 1),
        ]
    }

    private func metricValue(for key: String) -> String? {
        switch key {
        case "weight":
            return latestWeight.map { String(format: "%.1f", $0) }
        case "calories":
            return todayCalories.map { "\($0)" }
        default:
            return nil
        }
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

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: 编译失败（MirrorView 调用签名不匹配），Task 10 一起修

- [ ] **Step 3: Commit（与 Task 10 一起）**

---

## Task 10: MirrorViewModel + MirrorView 集成

**Files:**
- Modify: `frontend-ios/Voliti/Features/Mirror/MirrorViewModel.swift`
- Modify: `frontend-ios/Voliti/Features/Mirror/MirrorView.swift`

- [ ] **Step 1: MirrorViewModel 加载 LifeSignPlan + DashboardConfig**

在 MirrorViewModel 中新增属性和加载逻辑。

新增属性（在 `var selectedCard` 之后）：

```swift
    var lifeSignPlans: [LifeSignPlan] = []
    var dashboardConfig: DashboardConfig?
    var showLifeSignList = false
```

在 `loadData()` 方法内，`// Events` 注释之前，追加：

```swift
        // LifeSign Plans
        let planDescriptor = FetchDescriptor<LifeSignPlan>(
            sortBy: [SortDescriptor(\.lastUpdated, order: .reverse)]
        )
        do {
            lifeSignPlans = try modelContext.fetch(planDescriptor)
        } catch {
            logger.error("Failed to load LifeSign plans: \(error.localizedDescription)")
        }

        // Dashboard Config
        let configDescriptor = FetchDescriptor<DashboardConfig>(
            predicate: #Predicate { $0.id == "default" }
        )
        do {
            dashboardConfig = try modelContext.fetch(configDescriptor).first
        } catch {
            logger.error("Failed to load dashboard config: \(error.localizedDescription)")
        }
```

- [ ] **Step 2: MirrorView 更新布局**

更新 MirrorView 的 ScrollView 内容，在 Dashboard 和 Pulse 之间插入 LifeSignSummaryCard。

将 DashboardSection 调用改为：

```swift
                DashboardSection(
                    config: viewModel.dashboardConfig,
                    latestWeight: viewModel.latestWeight,
                    todayCalories: viewModel.todayCalories,
                    userGoal: viewModel.dashboardConfig?.userGoal
                )
```

在 Dashboard 后面的 `StarpathDivider()` 之后、`// Pulse` 注释之前，插入 LifeSign 摘要卡片：

```swift
                // LifeSign 摘要
                LifeSignSummaryCard(plans: viewModel.lifeSignPlans) {
                    viewModel.showLifeSignList = true
                }
                .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)
```

在 `.fullScreenCover(item: $viewModel.selectedCard)` 之后追加 LifeSign 列表的 sheet：

```swift
        .sheet(isPresented: $viewModel.showLifeSignList) {
            NavigationStack {
                LifeSignListView(plans: viewModel.lifeSignPlans)
            }
        }
```

- [ ] **Step 3: 构建确认**

Run: `xcodebuild build -project Voliti.xcodeproj -target Voliti -sdk iphonesimulator 2>&1 | grep -E "BUILD|error:" | tail -3`
Expected: BUILD SUCCEEDED

- [ ] **Step 4: Commit**

```bash
git add frontend-ios/Voliti/Features/Mirror/MirrorViewModel.swift frontend-ios/Voliti/Features/Mirror/MirrorView.swift frontend-ios/Voliti/Features/Mirror/DashboardSection.swift
git commit -m "feat: MIRROR 集成 LifeSign 摘要 + Config 驱动 Dashboard"
```

---

## Task 11: Coach Prompt 变更 — Dashboard 配置 + 目标采集

**Files:**
- Modify: `backend/prompts/coach_system.j2`

- [ ] **Step 1: 在 Onboarding 部分追加 Dashboard 配置指令**

在 `coach_system.j2` 的 `## Onboarding` section，`**Completion requirements:**` 列表最后一项之后追加：

```
- Written dashboardConfig to `/user/profile/dashboardConfig` with initial metrics
- Written user goal to dashboardConfig (e.g., "12 weeks 75kg → 70kg")
```

- [ ] **Step 2: 在 Data Architecture 部分追加 dashboardConfig 路径**

在 `## Data Architecture` 的目录树中，`├── profile/notification_prefs.json` 之后追加：

```
├── profile/dashboardConfig          # Dashboard metrics + user goal
```

- [ ] **Step 3: 在 Tools 下的 File System 部分追加 dashboardConfig 写入说明**

在 `Use file tools only for **writes**` 之后的列表中追加：

```
- `/user/profile/dashboardConfig` — dashboard config (write during onboarding)
```

- [ ] **Step 4: 在 Onboarding 之后新增 Dashboard 配置段落**

在 `## Onboarding` section 末尾追加：

```

### Dashboard Configuration

During onboarding, ask the user which metrics they want to track (e.g., weight, body fat, calories, sleep, water). Write the config as:

```json
{
  "metrics": [
    {"key": "weight", "label": "体重", "unit": "KG", "order": 0},
    {"key": "calories", "label": "卡路里", "unit": "KCAL", "order": 1}
  ],
  "user_goal": "12 周 75kg → 70kg"
}
```

Write to `/user/profile/dashboardConfig`. Default to weight + calories if user doesn't specify.

**Stability constraint:** Do not change dashboard metrics unless the user explicitly requests it or the Act phase reveals a new tracking dimension is needed.
```

- [ ] **Step 5: 在 LifeSign 部分追加数据格式约束**

在 `## LifeSign — Coping Plans` section，`After any create/update/delete → sync coping_plans_index.md` 之后追加：

```

LifeSign file format (`/user/coping_plans/{id}.json`):
```json
{
  "id": "ls_001",
  "trigger": "下班后压力大想吃零食",
  "coping_response": "泡茶+阳台3分钟",
  "success_count": 2,
  "total_attempts": 5,
  "status": "active",
  "last_updated": "2026-04-05T14:30:52Z"
}
```

Field names use snake_case. Always include all fields when writing. The iOS client syncs these files to local storage for display in MIRROR.
```

- [ ] **Step 6: Commit**

```bash
git add backend/prompts/coach_system.j2
git commit -m "feat: Coach prompt — Dashboard 配置指令 + 目标采集 + LifeSign 格式约束"
```

---

## Self-Review Checklist

### 1. Spec Coverage
| Spec Requirement | Task |
|------------------|------|
| LifeSignPlan SwiftData 模型 | Task 1 |
| DashboardConfig SwiftData 模型 | Task 2 |
| LangGraph Store 搜索 API | Task 3 |
| Store → SwiftData 同步服务 | Task 4 |
| 对话结束后触发同步 | Task 5 |
| LifeSign 5 种事件类型 | Task 6 |
| LifeSign 摘要卡片（上提到 Dashboard 区域） | Task 7 |
| LifeSign 列表页 + 详情页 | Task 8 |
| Dashboard Config 驱动（取代硬编码） | Task 9 |
| MirrorView 集成 LifeSign + Config | Task 10 |
| Coach prompt Dashboard 配置指令 | Task 11 |
| Coach prompt 用户目标采集 | Task 11 |
| Coach prompt LifeSign 数据格式约束 | Task 11 |
| MirrorView.onAppear 防御性同步 | Task 10（configure 每次 onAppear 调用 loadData） |

### 2. Placeholder Scan
- 无 TBD/TODO
- DashboardSection 有完整的回退逻辑（无 config → 默认体重+卡路里）

### 3. Type Consistency
- `LifeSignPlan` 属性名在所有文件一致：id, trigger, copingResponse, successCount, totalAttempts, status, lastUpdated, successRate
- `DashboardConfig` 属性名一致：id, metrics, userGoal, lastUpdated
- `DashboardMetric` 属性名一致：key, label, unit, order
- `StoreSyncService` 方法名一致：syncAll(), syncLifeSignPlans(), syncDashboardConfig()
- Backend JSON 字段名 snake_case（trigger, coping_response, success_count, total_attempts, last_updated, user_goal）与 iOS 解析代码一致
