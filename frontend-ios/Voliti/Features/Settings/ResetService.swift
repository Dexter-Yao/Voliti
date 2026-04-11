// ABOUTME: 重置逻辑，清除 SwiftData + AppStorage + LangGraph Store
// ABOUTME: 执行顺序保证中断安全：onboardingComplete 最先，SwiftData 最后

import Foundation
import SwiftData
import os

private let logger = Logger(subsystem: "com.voliti", category: "ResetService")

@MainActor
enum ResetService {
    /// 执行完整重置，按中断安全顺序
    /// - Returns: 如果 Store 清除失败，返回警告消息；全部成功返回 nil
    static func resetAll(
        modelContext: ModelContext,
        clearRemoteStore: @MainActor @Sendable () async throws -> Void = {
            try await LangGraphAPI().clearUserStore()
        }
    ) async -> String? {
        var storeWarning: String?

        // 1. 先设 onboardingComplete = false（中断安全）
        UserDefaults.standard.set(false, forKey: "onboardingComplete")
        logger.info("Reset step 1: onboardingComplete = false")

        // 2. 清除后端 Store 数据
        do {
            try await clearRemoteStore()
            logger.info("Reset step 2: Store cleared")
        } catch {
            logger.warning("Reset step 2: Store clear failed — \(error.localizedDescription)")
            storeWarning = "部分云端数据可能未完全清除"
        }

        // 3. 清除 SwiftData
        // ABOUTME: 新增 SwiftData model 时需同步更新此列表
        do {
            try modelContext.delete(model: BehaviorEvent.self)
            try modelContext.delete(model: DashboardConfig.self)
            try modelContext.delete(model: Chapter.self)
            try modelContext.delete(model: LifeSignPlan.self)
            try modelContext.delete(model: InterventionCard.self)
            try modelContext.delete(model: ChatMessage.self)
            try modelContext.save()
            logger.info("Reset step 3: SwiftData cleared")
        } catch {
            logger.error("Reset step 3: SwiftData clear failed — \(error.localizedDescription)")
        }

        // 4. 重置 thread IDs 与本地身份
        APIConfiguration.threadID = nil
        APIConfiguration.onboardingThreadID = nil
        APIConfiguration.clearLocalIdentity()
        logger.info("Reset step 4: thread IDs and local identity cleared")

        // 5. 清除其他 AppStorage 值
        let keysToRemove = [
            "lastCheckinDate",
            "showThinkingExpanded",
            "preferredLanguage",
            "checkinReminderEnabled",
            "checkinReminderTime",
            ProjectionFreshness.userDefaultsKey,
        ]
        for key in keysToRemove {
            UserDefaults.standard.removeObject(forKey: key)
        }
        logger.info("Reset step 5: AppStorage cleared")

        return storeWarning
    }
}
