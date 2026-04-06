// ABOUTME: MIRROR 页 ViewModel，统一查询 Chapter + BehaviorEvent + InterventionCard
// ABOUTME: 指标数据从 DashboardConfig 读取（Coach 写入），不做本地计算

import Foundation
import SwiftData
import Observation
import os

private let logger = Logger(subsystem: "com.voliti", category: "MirrorViewModel")

@MainActor
@Observable
final class MirrorViewModel {
    var chapter: Chapter?
    var cards: [InterventionCard] = []
    var groupedEvents: [(date: Date, events: [BehaviorEvent])] = []
    var selectedFilterType: EventType?
    var expandedDates: Set<Date> = []
    var selectedCard: InterventionCard?
    var lifeSignPlans: [LifeSignPlan] = []
    var dashboardConfig: DashboardConfig?
    var showLifeSignList = false

    private var allEvents: [BehaviorEvent] = []
    private var modelContext: ModelContext?

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadData()
    }

    func reload() {
        loadData()
    }

    // MARK: - North Star (from DashboardConfig)

    var northStarConfig: NorthStarMetricConfig? {
        dashboardConfig?.northStar
    }

    var northStarDisplayValue: String? {
        northStarConfig?.currentValue?.displayText
    }

    var northStarDelta: Delta? {
        // Delta requires historical data — for now return nil
        // Coach can write trend data in future iterations
        nil
    }

    var northStarTrend: [Double?] {
        // Trend requires 7-day historical data
        // For weight, compute from ledger as a convenience
        guard northStarConfig?.key == "weight" else { return [] }
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        return (0..<7).reversed().map { daysAgo in
            let dayStart = calendar.date(byAdding: .day, value: -daysAgo, to: today)!
            let dayEnd = calendar.date(byAdding: .day, value: 1, to: dayStart)!
            return allEvents
                .first {
                    $0.type == .weighIn
                        && $0.weightKg != nil
                        && $0.timestamp >= dayStart
                        && $0.timestamp < dayEnd
                }?.weightKg
        }
    }

    // MARK: - Support Metrics (from DashboardConfig)

    var supportMetrics: [SupportMetricItem] {
        let configs = dashboardConfig?.supportMetrics ?? []
        guard !configs.isEmpty else {
            return defaultSupportMetrics
        }
        return configs
            .sorted { $0.order < $1.order }
            .map { config in
                SupportMetricItem(
                    key: config.key,
                    label: config.label,
                    value: config.currentValue?.displayText,
                    subLabel: config.unit.isEmpty ? nil : config.unit
                )
            }
    }

    private var defaultSupportMetrics: [SupportMetricItem] {
        [
            SupportMetricItem(key: "calories", label: "今日摄入", value: nil, subLabel: "KCAL"),
            SupportMetricItem(key: "state", label: "今日状态", value: nil, subLabel: nil),
            SupportMetricItem(key: "consistency", label: "本周一致性", value: nil, subLabel: nil),
        ]
    }

    // MARK: - Dynamic Filter

    var eventTypeCounts: [(type: EventType, count: Int)] {
        var counts: [EventType: Int] = [:]
        for event in allEvents {
            counts[event.type, default: 0] += 1
        }
        return counts
            .filter { $0.value > 0 }
            .sorted { $0.key.label < $1.key.label }
            .map { (type: $0.key, count: $0.value) }
    }

    // MARK: - Filtering

    var filteredGroupedEvents: [(date: Date, events: [BehaviorEvent])] {
        guard let filterType = selectedFilterType else { return groupedEvents }
        return groupedEvents.compactMap { group in
            let filtered = group.events.filter { $0.type == filterType }
            return filtered.isEmpty ? nil : (date: group.date, events: filtered)
        }
    }

    // MARK: - Day Collapse

    func isExpanded(_ date: Date) -> Bool {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let yesterday = calendar.date(byAdding: .day, value: -1, to: today)!
        if date >= yesterday { return true }
        return expandedDates.contains(date)
    }

    func toggleExpanded(_ date: Date) {
        if expandedDates.contains(date) {
            expandedDates.remove(date)
        } else {
            expandedDates.insert(date)
        }
    }

    // MARK: - Card Lookup

    func card(for cardId: String) -> InterventionCard? {
        cards.first { $0.id == cardId }
    }

    // MARK: - Delete

    func deleteCard(_ card: InterventionCard) {
        modelContext?.delete(card)
        cards.removeAll { $0.id == card.id }
    }

    // MARK: - Private

    private func loadData() {
        guard let modelContext else { return }

        // Chapter
        let chapterDescriptor = FetchDescriptor<Chapter>(
            sortBy: [SortDescriptor(\.startDate, order: .reverse)]
        )
        do {
            chapter = try modelContext.fetch(chapterDescriptor).first
        } catch {
            logger.error("Failed to load chapter: \(error.localizedDescription)")
        }

        // Cards
        var cardDescriptor = FetchDescriptor<InterventionCard>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        cardDescriptor.fetchLimit = 50
        do {
            cards = try modelContext.fetch(cardDescriptor)
        } catch {
            logger.error("Failed to load cards: \(error.localizedDescription)")
        }

        // LifeSign Plans
        let planDescriptor = FetchDescriptor<LifeSignPlan>(
            sortBy: [SortDescriptor(\.lastUpdated, order: .reverse)]
        )
        do {
            lifeSignPlans = try modelContext.fetch(planDescriptor)
        } catch {
            logger.error("Failed to load LifeSign plans: \(error.localizedDescription)")
        }

        // Dashboard Config
        let configDescriptor = FetchDescriptor<DashboardConfig>(
            predicate: #Predicate { $0.id == "default" }
        )
        do {
            dashboardConfig = try modelContext.fetch(configDescriptor).first
        } catch {
            logger.error("Failed to load dashboard config: \(error.localizedDescription)")
        }

        // Events
        var eventDescriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        eventDescriptor.fetchLimit = 200
        do {
            allEvents = try modelContext.fetch(eventDescriptor)
        } catch {
            logger.error("Failed to load events: \(error.localizedDescription)")
        }

        let calendar = Calendar.current
        var grouped: [Date: [BehaviorEvent]] = [:]
        for event in allEvents {
            let dayStart = calendar.startOfDay(for: event.timestamp)
            grouped[dayStart, default: []].append(event)
        }
        groupedEvents = grouped
            .sorted { $0.key > $1.key }
            .map { (date: $0.key, events: $0.value) }
    }
}
