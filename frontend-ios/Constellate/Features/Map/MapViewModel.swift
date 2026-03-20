// ABOUTME: Map 页 ViewModel，管理干预卡片和 Chapter 元数据
// ABOUTME: 从 SwiftData 本地查询，支持删除操作

import Foundation
import SwiftData
import Observation

@Observable
final class MapViewModel {
    var cards: [InterventionCard] = []
    var chapter: Chapter?
    var selectedCard: InterventionCard?

    private var modelContext: ModelContext?

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadData()
    }

    func deleteCard(_ card: InterventionCard) {
        modelContext?.delete(card)
        cards.removeAll { $0.id == card.id }
    }

    private func loadData() {
        guard let modelContext else { return }

        let cardDescriptor = FetchDescriptor<InterventionCard>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        cards = (try? modelContext.fetch(cardDescriptor)) ?? []

        let chapterDescriptor = FetchDescriptor<Chapter>(
            sortBy: [SortDescriptor(\.startDate, order: .reverse)]
        )
        chapter = try? modelContext.fetch(chapterDescriptor).first
    }
}
