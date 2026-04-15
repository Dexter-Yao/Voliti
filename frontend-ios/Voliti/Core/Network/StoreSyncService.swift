// ABOUTME: LangGraph Store → SwiftData 同步服务
// ABOUTME: 对话结束后拉取 LifeSign、DashboardConfig、Chapter、LedgerEvents，写入本地

import Foundation
import SwiftData
import os

private let logger = Logger(subsystem: "com.voliti", category: "StoreSyncService")

enum ProjectionFreshness: String, Sendable {
    static let userDefaultsKey = "storeProjectionIsStale"
    static let bannerText = "缓存 / 非最新状态"

    case fresh
    case stale
}

enum ProjectionFreshnessStore {
    static var current: ProjectionFreshness {
        get {
            UserDefaults.standard.bool(forKey: ProjectionFreshness.userDefaultsKey) ? .stale : .fresh
        }
        set {
            UserDefaults.standard.set(newValue == .stale, forKey: ProjectionFreshness.userDefaultsKey)
        }
    }
}

@MainActor
protocol StoreSyncing: AnyObject {
    func syncAll() async -> ProjectionFreshness
    func checkOnboardingComplete() async -> Bool
}

@MainActor
final class StoreSyncService: StoreSyncing {
    private let modelContext: ModelContext
    private let fetchStoreItem: @Sendable ([String], String) async throws -> [String: Any]?
    private let searchStoreItems: @Sendable ([String]) async throws -> [[String: Any]]
    private static let isoFormatter = ISO8601DateFormatter()

    init(
        modelContext: ModelContext,
        fetchStoreItem: @escaping @Sendable ([String], String) async throws -> [String: Any]? = { namespace, key in
            try await LangGraphAPI().fetchStoreItem(namespace: namespace, key: key)
        },
        searchStoreItems: @escaping @Sendable ([String]) async throws -> [[String: Any]] = { namespace in
            try await LangGraphAPI().searchStoreItems(namespace: namespace)
        }
    ) {
        self.modelContext = modelContext
        self.fetchStoreItem = fetchStoreItem
        self.searchStoreItems = searchStoreItems
    }

    // MARK: - Full Sync

    func syncAll() async -> ProjectionFreshness {
        async let lifeSignFresh = syncLifeSignPlans()
        async let dashboardFresh = syncDashboardConfig()
        async let chapterFresh = syncChapter()
        async let ledgerFresh = syncLedgerEvents()
        let statuses = await [lifeSignFresh, dashboardFresh, chapterFresh, ledgerFresh]
        return statuses.allSatisfy { $0 } ? .fresh : .stale
    }

    /// 检查 profile 中是否包含 onboarding_complete 标记
    func checkOnboardingComplete() async -> Bool {
        do {
            guard let value = try await fetchStoreItem(
                StoreContract.userNamespace,
                StoreContract.profileContextKey
            ) else {
                return false
            }
            let content = try StoreContract.unwrapText(from: value)
            return content.contains("onboarding_complete: true")
        } catch {
            logger.warning("Failed to check onboarding status: \(error.localizedDescription)")
            return false
        }
    }

    private func fetchUserItems() async throws -> [[String: Any]] {
        try await searchStoreItems(StoreContract.userNamespace)
    }

    private func decodeJSONValue(_ item: [String: Any]) throws -> [String: Any] {
        guard let value = item["value"] as? [String: Any] else {
            throw StoreContractError.invalidEnvelope
        }
        return try StoreContract.unwrapJSONDictionary(from: value)
    }

    // MARK: - LifeSign Plans

    func syncLifeSignPlans() async -> Bool {
        do {
            let userItems = try await fetchUserItems()
            let items = userItems.filter { item in
                guard let key = item["key"] as? String else { return false }
                return key.hasPrefix(StoreContract.copingPlansPrefix) && key.hasSuffix(".json")
            }

            for item in items {
                let value = try decodeJSONValue(item)
                guard let planId = value["id"] as? String else { continue }

                let triggerData = value["trigger"] as? [String: Any]
                let trigger = triggerData?["situation"] as? String ?? ""
                let copingResponse = value["action"] as? String ?? value["coping_response"] as? String ?? ""
                let status = value["status"] as? String ?? "active"
                let lastUpdatedStr = value["last_updated"] as? String

                let lastUpdated: Date
                if let str = lastUpdatedStr {
                    lastUpdated = Self.isoFormatter.date(from: str) ?? .now
                } else {
                    lastUpdated = .now
                }

                let descriptor = FetchDescriptor<LifeSignPlan>(
                    predicate: #Predicate { $0.id == planId }
                )
                if let existing = try modelContext.fetch(descriptor).first {
                    existing.trigger = trigger
                    existing.copingResponse = copingResponse
                    existing.status = status
                    existing.lastUpdated = lastUpdated
                } else {
                    let plan = LifeSignPlan(
                        id: planId,
                        trigger: trigger,
                        copingResponse: copingResponse,
                        status: status,
                        lastUpdated: lastUpdated
                    )
                    modelContext.insert(plan)
                }
            }

            let remoteIDs: Set<String> = Set(items.compactMap { item in
                guard let value = try? decodeJSONValue(item) else { return nil }
                return value["id"] as? String
            })
            let allLocal = try modelContext.fetch(FetchDescriptor<LifeSignPlan>())
            for local in allLocal where !remoteIDs.contains(local.id) {
                modelContext.delete(local)
            }

            logger.info("LifeSign sync: \(items.count) plans from Store")
            return true
        } catch {
            logger.error("LifeSign sync failed: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - Dashboard Config

    func syncDashboardConfig() async -> Bool {
        do {
            guard let value = try await fetchStoreItem(
                StoreContract.userNamespace,
                StoreContract.profileDashboardConfigKey
            )
            else {
                logger.info("No dashboardConfig in Store")
                return true
            }
            let json = try StoreContract.unwrapJSONDictionary(from: value)

            let descriptor = FetchDescriptor<DashboardConfig>(
                predicate: #Predicate { $0.id == "default" }
            )
            let existing = try modelContext.fetch(descriptor).first

            let config = existing ?? DashboardConfig()
            if existing == nil {
                modelContext.insert(config)
            }

            // Parse north_star
            if let nsRaw = json["north_star"] as? [String: Any] {
                let nsData = try JSONSerialization.data(withJSONObject: nsRaw)
                config.northStarJSON = nsData
            }

            // Parse support_metrics
            if let smRaw = json["support_metrics"] as? [[String: Any]] {
                let smData = try JSONSerialization.data(withJSONObject: smRaw)
                config.supportMetricsJSON = smData
            }

            config.userGoal = json["user_goal"] as? String
            config.lastUpdated = .now

            logger.info("Dashboard config sync: north_star=\(config.northStar?.key ?? "nil"), support=\(config.supportMetrics.count)")
            return true
        } catch {
            logger.error("Dashboard config sync failed: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - Chapter

    func syncChapter() async -> Bool {
        do {
            guard let value = try await fetchStoreItem(
                StoreContract.userNamespace,
                StoreContract.chapterCurrentKey
            ) else {
                logger.info("No current chapter in Store")
                return true
            }
            let json = try StoreContract.unwrapJSONDictionary(from: value)

            guard let chapterId = json["id"] as? String,
                  let title = json["title"] as? String,
                  let milestone = json["milestone"] as? String else {
                logger.error("Chapter data missing required fields")
                return false
            }

            let startDate: Date
            if let dateStr = json["start_date"] as? String {
                startDate = Self.isoFormatter.date(from: dateStr) ?? .now
            } else {
                startDate = .now
            }

            var descriptor = FetchDescriptor<Chapter>(
                predicate: #Predicate { $0.id == chapterId }
            )
            descriptor.fetchLimit = 1

            if let existing = try modelContext.fetch(descriptor).first {
                existing.title = title
                existing.milestone = milestone
                existing.startDate = startDate
            } else {
                let chapter = Chapter(
                    id: chapterId,
                    title: title,
                    milestone: milestone,
                    startDate: startDate
                )
                modelContext.insert(chapter)
            }

            logger.info("Chapter sync: \(chapterId) — \(title)")
            return true
        } catch {
            logger.error("Chapter sync failed: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - Ledger Events

    func syncLedgerEvents() async -> Bool {
        do {
            let userItems = try await fetchUserItems()
            let items = userItems.filter { item in
                guard let key = item["key"] as? String else { return false }
                return key.hasPrefix(StoreContract.ledgerPrefix)
            }

            for item in items {
                // Store item 结构：顶层 key 作为事件 id，value 包含事件字段
                guard let eventId = item["key"] as? String else {
                    logger.warning("Ledger item missing key or value, skipping")
                    continue
                }
                let value = try decodeJSONValue(item)

                guard let kind = value["kind"] as? String,
                      let timestampStr = value["timestamp"] as? String,
                      let evidence = value["evidence"] as? String else {
                    logger.warning("Ledger event \(eventId) missing required fields (kind/timestamp/evidence), skipping")
                    continue
                }

                guard let timestamp = Self.isoFormatter.date(from: timestampStr) else {
                    logger.warning("Ledger event \(eventId) has unparseable timestamp '\(timestampStr)', skipping")
                    continue
                }

                let recordedAt: Date
                if let recordedAtStr = value["recorded_at"] as? String {
                    recordedAt = Self.isoFormatter.date(from: recordedAtStr) ?? .now
                } else {
                    recordedAt = .now
                }

                // 去重：已存在则跳过，不覆盖本地数据
                var descriptor = FetchDescriptor<BehaviorEvent>(
                    predicate: #Predicate { $0.id == eventId }
                )
                descriptor.fetchLimit = 1
                guard try modelContext.fetch(descriptor).isEmpty else { continue }

                let event = BehaviorEvent(
                    id: eventId,
                    timestamp: timestamp,
                    recordedAt: recordedAt,
                    kind: kind,
                    evidence: evidence,
                    summary: value["summary"] as? String,
                    tags: value["tags"] as? [String] ?? []
                )

                // metrics: [[String: Any]] → [MetricEntry] → Data
                if let metricsRaw = value["metrics"] as? [[String: Any]] {
                    do {
                        let metricsData = try JSONSerialization.data(withJSONObject: metricsRaw)
                        let entries = try JSONDecoder().decode([MetricEntry].self, from: metricsData)
                        event.setMetrics(entries)
                    } catch {
                        logger.warning("Ledger event \(eventId) metrics parse error: \(error.localizedDescription), storing without metrics")
                    }
                }

                // context: [String: Any] → flatten to [String: String] → Data
                if let contextRaw = value["context"] as? [String: Any] {
                    let contextStrings = contextRaw.compactMapValues { "\($0)" }
                    event.setContext(contextStrings)
                }

                // refs: [String: Any] → flatten to [String: String] → Data
                if let refsRaw = value["refs"] as? [String: Any] {
                    let refsStrings = refsRaw.compactMapValues { "\($0)" }
                    event.setRefs(refsStrings)
                }

                modelContext.insert(event)
            }

            logger.info("Ledger sync: \(items.count) items processed")
            return true
        } catch {
            logger.error("Ledger sync failed: \(error.localizedDescription)")
            return false
        }
    }
}
