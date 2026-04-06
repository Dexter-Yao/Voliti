// ABOUTME: MIRROR 页 ViewModel，统一查询 Chapter + BehaviorEvent + InterventionCard
// ABOUTME: 指标数据由 MetricComputer 从事件流计算，DashboardConfig 仅存配置

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
    var selectedFilterKind: String?
    var expandedDates: Set<Date> = []
    var selectedCard: InterventionCard?
    var lifeSignPlans: [LifeSignPlan] = []
    var dashboardConfig: DashboardConfig?
    var showLifeSignList = false

    private var allEvents: [BehaviorEvent] = []
    private var metricEvents: [BehaviorEvent] = []
    private var modelContext: ModelContext?
    private var timelinePageSize = 50
    private var allTimelineLoaded = false

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadData()
    }

    func reload() {
        loadData()
    }

    // MARK: - North Star (computed from event stream)

    var northStarConfig: NorthStarMetricConfig? {
        dashboardConfig?.northStar
    }

    var northStarDisplayValue: String? {
        guard let config = northStarConfig else { return nil }
        let value = MetricComputer.currentValue(for: config.key, from: metricEvents)
        guard value != nil else { return nil }
        return MetricComputer.format(value: value, type: config.type, scaleMax: config.scaleMax, ratioDenominator: config.ratioDenominator)
    }

    var northStarDelta: Delta? {
        guard let config = northStarConfig else { return nil }
        return MetricComputer.delta(for: config.key, from: metricEvents, direction: config.deltaDirection)
    }

    var northStarTrend: [Double?] {
        guard let config = northStarConfig else { return [] }
        return MetricComputer.trend(for: config.key, from: metricEvents)
    }

    // MARK: - Support Metrics (computed from event stream)

    var supportMetrics: [SupportMetricItem] {
        let configs = dashboardConfig?.supportMetrics ?? []
        guard !configs.isEmpty else { return defaultSupportMetrics }
        return configs
            .sorted { $0.order < $1.order }
            .map { config in
                let value = MetricComputer.currentValue(for: config.key, from: metricEvents)
                return SupportMetricItem(
                    key: config.key,
                    label: config.label,
                    value: MetricComputer.format(value: value, type: config.type, scaleMax: config.scaleMax, ratioDenominator: config.ratioDenominator),
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

    var kindCounts: [(kind: String, count: Int)] {
        var counts: [String: Int] = [:]
        for event in allEvents where !BehaviorEvent.hiddenKinds.contains(event.kind) {
            counts[event.kind, default: 0] += 1
        }
        return counts
            .sorted { $0.key < $1.key }
            .map { (kind: $0.key, count: $0.value) }
    }

    // MARK: - Filtering

    var filteredGroupedEvents: [(date: Date, events: [BehaviorEvent])] {
        guard let filterKind = selectedFilterKind else { return groupedEvents }
        return groupedEvents.compactMap { group in
            let filtered = group.events.filter { $0.kind == filterKind }
            return filtered.isEmpty ? nil : (date: group.date, events: filtered)
        }
    }

    // MARK: - Timeline Pagination

    func loadMoreEvents() {
        guard let modelContext, !allTimelineLoaded else { return }
        var descriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        descriptor.fetchOffset = allEvents.count
        descriptor.fetchLimit = timelinePageSize
        do {
            let more = try modelContext.fetch(descriptor)
            if more.count < timelinePageSize { allTimelineLoaded = true }
            allEvents.append(contentsOf: more)
            rebuildGroupedEvents()
        } catch {
            logger.error("Failed to load more events: \(error.localizedDescription)")
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

    private func rebuildGroupedEvents() {
        let calendar = Calendar.current
        let displayEvents = allEvents.filter { !BehaviorEvent.hiddenKinds.contains($0.kind) }
        var grouped: [Date: [BehaviorEvent]] = [:]
        for event in displayEvents {
            let dayStart = calendar.startOfDay(for: event.timestamp)
            grouped[dayStart, default: []].append(event)
        }
        groupedEvents = grouped
            .sorted { $0.key > $1.key }
            .map { (date: $0.key, events: $0.value) }
    }

    private func loadData() {
        guard let modelContext else { return }
        let calendar = Calendar.current

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

        // Timeline events (paginated)
        allTimelineLoaded = false
        var eventDescriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        eventDescriptor.fetchLimit = timelinePageSize
        do {
            allEvents = try modelContext.fetch(eventDescriptor)
            if allEvents.count < timelinePageSize { allTimelineLoaded = true }
        } catch {
            logger.error("Failed to load events: \(error.localizedDescription)")
        }

        // Metric events (14 days for trend/delta calculation)
        let fourteenDaysAgo = calendar.date(byAdding: .day, value: -14, to: calendar.startOfDay(for: .now))!
        let metricDescriptor = FetchDescriptor<BehaviorEvent>(
            predicate: #Predicate { $0.timestamp >= fourteenDaysAgo },
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        do {
            metricEvents = try modelContext.fetch(metricDescriptor)
        } catch {
            logger.error("Failed to load metric events: \(error.localizedDescription)")
        }

        rebuildGroupedEvents()
    }
}
