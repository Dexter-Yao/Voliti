// ABOUTME: Voliti 核心测试套件
// ABOUTME: 覆盖 MetricComputer、BehaviorEvent 解码、ResetService 执行顺序

import Testing
import Foundation
@testable import Voliti

// MARK: - MetricComputer Tests

@Suite("MetricComputer")
struct MetricComputerTests {

    private func makeEvent(
        kind: String = "observation",
        timestamp: Date = .now,
        metrics: [MetricEntry] = []
    ) -> BehaviorEvent {
        let event = BehaviorEvent(
            id: UUID().uuidString,
            timestamp: timestamp,
            recordedAt: .now,
            kind: kind,
            evidence: "test",
            tags: []
        )
        if !metrics.isEmpty {
            event.setMetrics(metrics)
        }
        return event
    }

    private func daysAgo(_ n: Int) -> Date {
        Calendar.current.date(byAdding: .day, value: -n, to: Calendar.current.startOfDay(for: .now))!
    }

    // MARK: - currentValue

    @Test func currentValue_happyPath() {
        let events = [
            makeEvent(timestamp: daysAgo(1), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 71.5, quality: .reported)]),
        ]
        let result = MetricComputer.currentValue(for: "weight", from: events)
        #expect(result == 71.5)
    }

    @Test func currentValue_noData() {
        let result = MetricComputer.currentValue(for: "weight", from: [])
        #expect(result == nil)
    }

    @Test func currentValue_missingExcluded() {
        let events = [
            makeEvent(metrics: [MetricEntry(key: "weight", value: nil, quality: .missing)]),
        ]
        let result = MetricComputer.currentValue(for: "weight", from: events)
        #expect(result == nil)
    }

    @Test func currentValue_estimatedIncluded() {
        let events = [
            makeEvent(metrics: [MetricEntry(key: "weight", value: 72.0, quality: .estimated)]),
        ]
        let result = MetricComputer.currentValue(for: "weight", from: events)
        #expect(result == 72.0)
    }

    @Test func currentValue_latestEventWins() {
        let events = [
            makeEvent(timestamp: daysAgo(2), metrics: [MetricEntry(key: "kcal", value: 1200, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "kcal", value: 1800, quality: .reported)]),
        ]
        let result = MetricComputer.currentValue(for: "kcal", from: events)
        #expect(result == 1800)
    }

    // MARK: - trend

    @Test func trend_full7Days() {
        let events = (0..<7).map { day in
            makeEvent(
                timestamp: daysAgo(6 - day),
                metrics: [MetricEntry(key: "weight", value: 73.0 - Double(day) * 0.3, quality: .reported)]
            )
        }
        let trend = MetricComputer.trend(for: "weight", from: events)
        #expect(trend.count == 7)
        #expect(trend.allSatisfy { $0 != nil })
    }

    @Test func trend_sparse() {
        let events = [
            makeEvent(timestamp: daysAgo(5), metrics: [MetricEntry(key: "weight", value: 73.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(1), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
        ]
        let trend = MetricComputer.trend(for: "weight", from: events)
        #expect(trend.count == 7)
        let nonNilCount = trend.compactMap { $0 }.count
        #expect(nonNilCount == 2)
    }

    @Test func trend_empty() {
        let trend = MetricComputer.trend(for: "weight", from: [])
        #expect(trend.count == 7)
        #expect(trend.allSatisfy { $0 == nil })
    }

    // MARK: - trendQualities

    @Test func trendQualities_mixedQuality() {
        let events = [
            makeEvent(timestamp: daysAgo(1), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 71.5, quality: .estimated)]),
        ]
        let qualities = MetricComputer.trendQualities(for: "weight", from: events)
        #expect(qualities.count == 7)
        #expect(qualities.last == .estimated)
    }

    // MARK: - delta

    @Test func delta_normalDecrease() {
        let events = [
            makeEvent(timestamp: daysAgo(7), metrics: [MetricEntry(key: "weight", value: 73.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
        ]
        let delta = MetricComputer.delta(for: "weight", from: events, direction: .decrease)
        #expect(delta != nil)
        #expect(delta!.value < 0)
        #expect(delta!.isPositive == true)
    }

    @Test func delta_noReference() {
        let events = [
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
        ]
        let delta = MetricComputer.delta(for: "weight", from: events, direction: .decrease)
        #expect(delta == nil)
    }

    // MARK: - format

    @Test func format_numeric() {
        let result = MetricComputer.format(value: 72.3, type: .numeric, scaleMax: nil, ratioDenominator: nil)
        #expect(result.contains("72"))
    }

    @Test func format_nil() {
        let result = MetricComputer.format(value: nil, type: .numeric, scaleMax: nil, ratioDenominator: nil)
        #expect(result == "—")
    }

    @Test func format_scale() {
        let result = MetricComputer.format(value: 7.0, type: .scale, scaleMax: 10, ratioDenominator: nil)
        #expect(result.contains("7"))
        #expect(result.contains("10"))
    }

    @Test func format_ratio() {
        let result = MetricComputer.format(value: 5.0, type: .ratio, scaleMax: nil, ratioDenominator: 7)
        #expect(result.contains("5"))
        #expect(result.contains("7"))
    }
}

// MARK: - BehaviorEvent Tests

@Suite("BehaviorEvent")
struct BehaviorEventTests {

    @Test func metricsDecoding() {
        let event = BehaviorEvent(
            id: "test",
            timestamp: .now,
            recordedAt: .now,
            kind: "observation",
            evidence: "test",
            tags: []
        )
        let entries = [
            MetricEntry(key: "weight", value: 72.3, quality: .reported),
            MetricEntry(key: "kcal", value: nil, quality: .missing),
        ]
        event.setMetrics(entries)

        let decoded = event.metrics
        #expect(decoded.count == 2)
        #expect(decoded[0].key == "weight")
        #expect(decoded[0].value == 72.3)
        #expect(decoded[0].quality == .reported)
        #expect(decoded[1].value == nil)
        #expect(decoded[1].quality == .missing)
    }

    @Test func contextRoundTrip() {
        let event = BehaviorEvent(
            id: "test",
            timestamp: .now,
            recordedAt: .now,
            kind: "state",
            evidence: "test",
            tags: []
        )
        event.setContext(["situation": "午休", "social": "alone"])

        let ctx = event.context
        #expect(ctx["situation"] == "午休")
        #expect(ctx["social"] == "alone")
    }

    @Test func kindLabel() {
        #expect(BehaviorEvent.kindLabels["observation"] == "行为")
        #expect(BehaviorEvent.kindLabels["state"] == "状态")
        #expect(BehaviorEvent.kindLabels["nonexistent"] == nil)
    }

    @Test func hiddenKinds() {
        #expect(BehaviorEvent.hiddenKinds.contains("system"))
    }
}

// MARK: - ProfileInfoSection Label Mapping

@Suite("ProfileInfoSection")
struct ProfileInfoSectionTests {

    @Test func knownKeyMapping() {
        // 直接测试 static dict
        let labels = ProfileInfoSection.keyLabels
        #expect(labels["name"] == "称呼")
        #expect(labels["goal"] == "目标")
    }

    @Test func unknownKeyFallback() {
        let labels = ProfileInfoSection.keyLabels
        #expect(labels["unknown_field"] == nil)
    }
}
