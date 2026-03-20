// ABOUTME: 21 天 Chapter 周期 SwiftData 模型
// ABOUTME: 承载身份宣言、目标和关联的干预卡片

import Foundation
import SwiftData

@Model
final class Chapter {
    var id: String
    var identityStatement: String
    var goal: String
    var startDate: Date
    @Relationship var cards: [InterventionCard]?

    init(
        id: String = UUID().uuidString,
        identityStatement: String,
        goal: String,
        startDate: Date = .now,
        cards: [InterventionCard]? = nil
    ) {
        self.id = id
        self.identityStatement = identityStatement
        self.goal = goal
        self.startDate = startDate
        self.cards = cards
    }

    var currentDay: Int {
        Calendar.current.dateComponents([.day], from: startDate, to: .now).day ?? 0
    }
}
