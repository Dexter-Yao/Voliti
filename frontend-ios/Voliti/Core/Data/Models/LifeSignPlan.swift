// ABOUTME: LifeSign 预案 SwiftData 模型，从 LangGraph Store 同步
// ABOUTME: 存储 if-then 应对策略的本地镜像

import Foundation
import SwiftData

@Model
final class LifeSignPlan {
    var id: String
    var trigger: String
    var copingResponse: String
    var status: String
    var lastUpdated: Date

    init(
        id: String,
        trigger: String,
        copingResponse: String,
        status: String = "active",
        lastUpdated: Date = .now
    ) {
        self.id = id
        self.trigger = trigger
        self.copingResponse = copingResponse
        self.status = status
        self.lastUpdated = lastUpdated
    }
}
