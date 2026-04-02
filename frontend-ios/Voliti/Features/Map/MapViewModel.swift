// ABOUTME: Map 页 ViewModel，管理干预卡片和 Chapter 元数据
// ABOUTME: 从 SwiftData 本地查询，支持删除操作

import Foundation
import SwiftData
import Observation
import os

private let logger = Logger(subsystem: "com.voliti", category: "MapViewModel")

@MainActor
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

        var cardDescriptor = FetchDescriptor<InterventionCard>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        cardDescriptor.fetchLimit = 50
        do {
            cards = try modelContext.fetch(cardDescriptor)
        } catch {
            logger.error("Failed to load cards: \(error.localizedDescription)")
        }

        let chapterDescriptor = FetchDescriptor<Chapter>(
            sortBy: [SortDescriptor(\.startDate, order: .reverse)]
        )
        do {
            chapter = try modelContext.fetch(chapterDescriptor).first
        } catch {
            logger.error("Failed to load chapter: \(error.localizedDescription)")
        }
    }
}
