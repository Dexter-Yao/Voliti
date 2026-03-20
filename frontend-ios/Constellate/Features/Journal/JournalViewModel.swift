// ABOUTME: Journal 页 ViewModel，按日分组查询行为事件
// ABOUTME: 逆时间序，仅显示有数据的日子

import Foundation
import SwiftData
import Observation

@Observable
final class JournalViewModel {
    var groupedEvents: [(date: Date, events: [BehaviorEvent])] = []

    private var modelContext: ModelContext?

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadEvents()
    }

    private func loadEvents() {
        guard let modelContext else { return }

        let descriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        guard let events = try? modelContext.fetch(descriptor) else { return }

        let calendar = Calendar.current
        var grouped: [Date: [BehaviorEvent]] = [:]
        for event in events {
            let dayStart = calendar.startOfDay(for: event.timestamp)
            grouped[dayStart, default: []].append(event)
        }

        groupedEvents = grouped
            .sorted { $0.key > $1.key }
            .map { (date: $0.key, events: $0.value) }
    }
}
