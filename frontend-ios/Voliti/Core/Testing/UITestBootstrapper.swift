// ABOUTME: UI 测试启动夹具，根据场景注入最小本地数据与用户偏好
// ABOUTME: 仅在显式环境变量下生效，避免干扰真实运行时路径

import Foundation
import SwiftData

enum UITestBootstrapper {
    static func bootstrapIfNeeded(modelContainer: ModelContainer) {
        guard let scenario = ProcessInfo.processInfo.environment["VOLITI_UI_TEST_SCENARIO"] else {
            return
        }

        switch scenario {
        case "mirrorLogRange":
            bootstrapMirrorLogRange(modelContainer: modelContainer)
        default:
            return
        }
    }

    @MainActor
    private static func bootstrapMirrorLogRange(modelContainer: ModelContainer) {
        let defaults = UserDefaults.standard
        defaults.set(true, forKey: "onboardingComplete")
        defaults.set(false, forKey: ProjectionFreshness.userDefaultsKey)
        defaults.set(MirrorLogRange.last30Days.storageValue, forKey: "mirrorLogRangeSelection")

        let modelContext = ModelContext(modelContainer)

        let recentTimestamp = Calendar.current.date(byAdding: .day, value: -2, to: .now)!
        let recentEvent = BehaviorEvent(
            id: "ui-test-recent-log",
            timestamp: recentTimestamp,
            recordedAt: recentTimestamp,
            kind: "observation",
            evidence: "最近日志证据",
            summary: "近30天记录"
        )

        let olderTimestamp = Calendar.current.date(byAdding: .day, value: -45, to: .now)!
        let olderEvent = BehaviorEvent(
            id: "ui-test-older-log",
            timestamp: olderTimestamp,
            recordedAt: olderTimestamp,
            kind: "state",
            evidence: "较早日志证据",
            summary: "45天前状态"
        )

        modelContext.insert(recentEvent)
        modelContext.insert(olderEvent)
        try? modelContext.save()
    }
}
