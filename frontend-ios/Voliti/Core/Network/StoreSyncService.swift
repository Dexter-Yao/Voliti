// ABOUTME: LangGraph Store → SwiftData 同步服务
// ABOUTME: 对话结束后拉取 LifeSign、DashboardConfig、Chapter、LedgerEvents，写入本地

import Foundation
import SwiftData
import os

private let logger = Logger(subsystem: "com.voliti", category: "StoreSyncService")

@MainActor
final class StoreSyncService {
    private let api = LangGraphAPI()
    private let modelContext: ModelContext
    private static let isoFormatter = ISO8601DateFormatter()

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    // MARK: - Full Sync

    func syncAll() async {
        async let a: () = syncLifeSignPlans()
        async let b: () = syncDashboardConfig()
        async let c: () = syncChapter()
        async let d: () = syncLedgerEvents()
        _ = await (a, b, c, d)
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

            let descriptor = FetchDescriptor<DashboardConfig>(
                predicate: #Predicate { $0.id == "default" }
            )
            let existing = try modelContext.fetch(descriptor).first

            let config = existing ?? DashboardConfig()
            if existing == nil {
                modelContext.insert(config)
            }

            // Parse north_star
            if let nsRaw = value["north_star"] as? [String: Any] {
                let nsData = try JSONSerialization.data(withJSONObject: nsRaw)
                config.northStarJSON = nsData
            }

            // Parse support_metrics
            if let smRaw = value["support_metrics"] as? [[String: Any]] {
                let smData = try JSONSerialization.data(withJSONObject: smRaw)
                config.supportMetricsJSON = smData
            }

            config.userGoal = value["user_goal"] as? String
            config.lastUpdated = .now

            logger.info("Dashboard config sync: north_star=\(config.northStar?.key ?? "nil"), support=\(config.supportMetrics.count)")
        } catch {
            logger.error("Dashboard config sync failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Chapter

    func syncChapter() async {
        do {
            guard let value = try await api.fetchStoreItem(
                namespace: ["voliti", "user", "chapter"],
                key: "current"
            ) else {
                logger.info("No current chapter in Store")
                return
            }

            guard let chapterId = value["id"] as? String,
                  let identityStatement = value["identity_statement"] as? String,
                  let goal = value["goal"] as? String else {
                logger.error("Chapter data missing required fields")
                return
            }

            let startDate: Date
            if let dateStr = value["start_date"] as? String {
                startDate = Self.isoFormatter.date(from: dateStr) ?? .now
            } else {
                startDate = .now
            }

            var descriptor = FetchDescriptor<Chapter>(
                predicate: #Predicate { $0.id == chapterId }
            )
            descriptor.fetchLimit = 1

            if let existing = try modelContext.fetch(descriptor).first {
                existing.identityStatement = identityStatement
                existing.goal = goal
                existing.startDate = startDate
            } else {
                let chapter = Chapter(
                    id: chapterId,
                    identityStatement: identityStatement,
                    goal: goal,
                    startDate: startDate
                )
                modelContext.insert(chapter)
            }

            logger.info("Chapter sync: \(chapterId) — \(identityStatement)")
        } catch {
            logger.error("Chapter sync failed: \(error.localizedDescription)")
        }
    }

    // MARK: - Ledger Events

    func syncLedgerEvents() async {
        do {
            let items = try await api.searchStoreItems(
                namespace: ["voliti", "user", "ledger"]
            )

            for item in items {
                // Store item 结构：顶层 key 作为事件 id，value 包含事件字段
                guard let eventId = item["key"] as? String,
                      let value = item["value"] as? [String: Any] else {
                    logger.warning("Ledger item missing key or value, skipping")
                    continue
                }

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
        } catch {
            logger.error("Ledger sync failed: \(error.localizedDescription)")
        }
    }
}
