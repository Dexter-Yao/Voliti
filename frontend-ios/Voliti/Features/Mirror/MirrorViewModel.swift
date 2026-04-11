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
    var selectedFilterKind: String? {
        didSet {
            rebuildLogPresentation()
        }
    }
    var expandedDates: Set<Date> = []
    var selectedCard: InterventionCard?
    var lifeSignPlans: [LifeSignPlan] = []
    var dashboardConfig: DashboardConfig?
    var showLifeSignList = false
    var logRange: MirrorLogRange = .defaultValue
    var logDisplayState: LogDisplayState = .loading
    var isRefreshingProjection = false

    private var logEvents: [BehaviorEvent] = []
    private var metricEvents: [BehaviorEvent] = []
    private var modelContext: ModelContext?

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
        guard let display = MetricDisplay.make(
            value: MetricComputer.currentValue(for: config.key, from: metricEvents),
            quality: MetricComputer.currentQuality(for: config.key, from: metricEvents),
            type: config.type,
            unit: config.unit,
            scaleMax: config.scaleMax,
            ratioDenominator: config.ratioDenominator
        ) else { return nil }
        return display.value
    }

    var northStarDisplayUnit: String? {
        guard let config = northStarConfig else { return nil }
        return MetricDisplay.make(
            value: MetricComputer.currentValue(for: config.key, from: metricEvents),
            quality: MetricComputer.currentQuality(for: config.key, from: metricEvents),
            type: config.type,
            unit: config.unit,
            scaleMax: config.scaleMax,
            ratioDenominator: config.ratioDenominator
        )?.unit
    }

    var northStarShowsEstimatedBadge: Bool {
        guard let config = northStarConfig else { return false }
        return MetricDisplay.make(
            value: MetricComputer.currentValue(for: config.key, from: metricEvents),
            quality: MetricComputer.currentQuality(for: config.key, from: metricEvents),
            type: config.type,
            unit: config.unit,
            scaleMax: config.scaleMax,
            ratioDenominator: config.ratioDenominator
        )?.showsEstimatedBadge ?? false
    }

    var northStarDelta: Delta? {
        guard let config = northStarConfig else { return nil }
        return MetricComputer.delta(for: config.key, from: metricEvents, direction: config.deltaDirection)
    }

    var northStarTrend: [Double?] {
        guard let config = northStarConfig else { return [] }
        return MetricComputer.trend(for: config.key, from: metricEvents)
    }

    var northStarTrendQualities: [MetricQuality?] {
        guard let config = northStarConfig else { return [] }
        return MetricComputer.trendQualities(for: config.key, from: metricEvents)
    }

    // MARK: - Support Metrics (computed from event stream)

    var supportMetrics: [SupportMetricItem] {
        let configs = dashboardConfig?.supportMetrics ?? []
        guard !configs.isEmpty else { return defaultSupportMetrics }
        return configs
            .sorted { $0.order < $1.order }
            .map { config in
                let value = MetricComputer.currentValue(for: config.key, from: metricEvents)
                let quality = MetricComputer.currentQuality(for: config.key, from: metricEvents)
                let display = MetricDisplay.make(
                    value: value,
                    quality: quality,
                    type: config.type,
                    unit: config.unit,
                    scaleMax: config.scaleMax,
                    ratioDenominator: config.ratioDenominator
                )
                return SupportMetricItem(
                    key: config.key,
                    label: config.label,
                    value: display?.value,
                    subLabel: display?.unit,
                    showsEstimatedBadge: display?.showsEstimatedBadge ?? false
                )
            }
    }

    private var defaultSupportMetrics: [SupportMetricItem] {
        [
            SupportMetricItem(key: "calories", label: "今日摄入", value: nil, subLabel: "KCAL", showsEstimatedBadge: false),
            SupportMetricItem(key: "state", label: "今日状态", value: nil, subLabel: nil, showsEstimatedBadge: false),
            SupportMetricItem(key: "consistency", label: "本周一致性", value: nil, subLabel: nil, showsEstimatedBadge: false),
        ]
    }

    // MARK: - Dynamic Filter

    var kindCounts: [(kind: String, count: Int)] {
        var counts: [String: Int] = [:]
        for event in logEvents where !BehaviorEvent.hiddenKinds.contains(event.kind) {
            counts[event.kind, default: 0] += 1
        }
        if let selectedFilterKind {
            counts[selectedFilterKind, default: 0] += 0
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

    var shouldShowLogFilters: Bool {
        switch logDisplayState {
        case .ready, .emptyAfterFilter:
            return !kindCounts.isEmpty || selectedFilterKind != nil
        case .loading, .emptyInRange, .failed:
            return false
        }
    }

    // MARK: - Log Range

    func applyLogRange(_ range: MirrorLogRange) {
        guard let modelContext else { return }

        let previousRange = logRange
        let previousEvents = logEvents
        let previousGroups = groupedEvents
        let previousState = logDisplayState

        logger.info(
            "Mirror log range apply started: current=\(previousRange.storageValue, privacy: .public) target=\(range.storageValue, privacy: .public)"
        )
        logDisplayState = .loading

        do {
            logEvents = try fetchLogEvents(for: range, modelContext: modelContext)
            logRange = range
            rebuildLogPresentation()
            logger.info(
                "Mirror log range apply succeeded: target=\(range.storageValue, privacy: .public) visible=\(self.visibleLogEventCount) filtered=\(self.filteredLogEventCount)"
            )
        } catch {
            logRange = previousRange
            logEvents = previousEvents
            groupedEvents = previousGroups
            logDisplayState = previousState == .loading ? .failed : previousState
            logger.error(
                "Mirror log range apply failed: current=\(previousRange.storageValue, privacy: .public) target=\(range.storageValue, privacy: .public) error=\(error.localizedDescription, privacy: .public)"
            )
        }
    }

    func refreshProjection(using syncService: StoreSyncing) async -> ProjectionFreshness {
        guard !isRefreshingProjection else {
            return ProjectionFreshnessStore.current
        }

        isRefreshingProjection = true
        logger.info("Mirror stale refresh started: range=\(self.logRange.storageValue, privacy: .public)")
        let freshness = await syncService.syncAll()
        ProjectionFreshnessStore.current = freshness
        loadData()
        isRefreshingProjection = false
        if freshness == .fresh {
            logger.info("Mirror stale refresh succeeded: freshness=fresh range=\(self.logRange.storageValue, privacy: .public)")
        } else {
            logger.error("Mirror stale refresh failed: freshness=stale range=\(self.logRange.storageValue, privacy: .public)")
        }
        return freshness
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

    private var visibleLogEvents: [BehaviorEvent] {
        logEvents.filter { !BehaviorEvent.hiddenKinds.contains($0.kind) }
    }

    private var visibleLogEventCount: Int {
        visibleLogEvents.count
    }

    private var filteredLogEventCount: Int {
        filteredGroupedEvents.reduce(0) { $0 + $1.events.count }
    }

    private func rebuildLogPresentation() {
        let calendar = Calendar.current
        var grouped: [Date: [BehaviorEvent]] = [:]
        for event in visibleLogEvents {
            let dayStart = calendar.startOfDay(for: event.timestamp)
            grouped[dayStart, default: []].append(event)
        }
        groupedEvents = grouped
            .sorted { $0.key > $1.key }
            .map { (date: $0.key, events: $0.value) }

        if visibleLogEventCount == 0 {
            logDisplayState = .emptyInRange
        } else if selectedFilterKind != nil && filteredGroupedEvents.isEmpty {
            logDisplayState = .emptyAfterFilter
        } else {
            logDisplayState = .ready
        }
    }

    private func fetchLogEvents(for range: MirrorLogRange, modelContext: ModelContext) throws -> [BehaviorEvent] {
        guard let interval = range.interval(chapter: chapter) else {
            return []
        }

        let start = interval.start
        let end = interval.end
        let descriptor = FetchDescriptor<BehaviorEvent>(
            predicate: #Predicate { $0.timestamp >= start && $0.timestamp < end },
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        return try modelContext.fetch(descriptor)
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

        do {
            logEvents = try fetchLogEvents(for: logRange, modelContext: modelContext)
            logger.info(
                "Mirror projection loaded: range=\(self.logRange.storageValue, privacy: .public) total=\(self.logEvents.count) visible=\(self.visibleLogEventCount)"
            )
        } catch {
            logEvents = []
            logDisplayState = .failed
            logger.error(
                "Mirror projection load failed: range=\(self.logRange.storageValue, privacy: .public) error=\(error.localizedDescription, privacy: .public)"
            )
            return
        }

        rebuildLogPresentation()
    }
}
