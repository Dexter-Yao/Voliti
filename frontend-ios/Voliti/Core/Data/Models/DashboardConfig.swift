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
