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
    private static let isoFormatter = ISO8601DateFormatter()

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
