// ABOUTME: Chapter 本地投影 SwiftData 模型
// ABOUTME: 承载阶段标题、里程碑和关联的干预卡片

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
        title: String,
        milestone: String,
        startDate: Date = .now,
        cards: [InterventionCard]? = nil
    ) {
        self.id = id
        self.identityStatement = title
        self.goal = milestone
        self.startDate = startDate
        self.cards = cards
    }

    var title: String {
        get { identityStatement }
        set { identityStatement = newValue }
    }

    var milestone: String {
        get { goal }
        set { goal = newValue }
    }

    var currentDay: Int {
        Calendar.current.dateComponents([.day], from: startDate, to: .now).day ?? 0
    }
}
