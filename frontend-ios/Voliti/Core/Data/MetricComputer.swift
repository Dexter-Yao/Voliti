// ABOUTME: 确定性计算组件，从事件流推导指标的当前值、趋势和差值
// ABOUTME: 纯函数设计，输入事件数组，输出计算结果

import Foundation

enum MetricComputer {

    /// 取指定 key 的最新非 missing 值
    static func currentValue(for key: String, from events: [BehaviorEvent]) -> Double? {
        events
            .sorted { $0.timestamp > $1.timestamp }
            .lazy
            .compactMap { event in
                event.metrics.first { $0.key == key && $0.quality != .missing }
            }
            .first?
            .value
    }

    /// N 天趋势数组，每天取最新非 missing 值
    static func trend(for key: String, days: Int = 7, from events: [BehaviorEvent]) -> [Double?] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)

        return (0..<days).reversed().map { daysAgo in
            let dayStart = calendar.date(byAdding: .day, value: -daysAgo, to: today)!
            let dayEnd = calendar.date(byAdding: .day, value: 1, to: dayStart)!

            return events
                .filter { $0.timestamp >= dayStart && $0.timestamp < dayEnd }
                .sorted { $0.timestamp > $1.timestamp }
                .lazy
                .compactMap { event in
                    event.metrics.first { $0.key == key && $0.quality != .missing }
                }
                .first?
                .value
        }
    }

    /// N 天趋势的 quality 数组，与 trend() 对应
    static func trendQualities(for key: String, days: Int = 7, from events: [BehaviorEvent]) -> [MetricQuality?] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)

        return (0..<days).reversed().map { daysAgo in
            let dayStart = calendar.date(byAdding: .day, value: -daysAgo, to: today)!
            let dayEnd = calendar.date(byAdding: .day, value: 1, to: dayStart)!

            return events
                .filter { $0.timestamp >= dayStart && $0.timestamp < dayEnd }
                .sorted { $0.timestamp > $1.timestamp }
                .lazy
                .compactMap { event in
                    event.metrics.first { $0.key == key && $0.quality != .missing }
                }
                .first?
                .quality
        }
    }

    /// 差值：当前值 vs period 前同日的值
    static func delta(
        for key: String,
        period: DeltaPeriod = .week,
        from events: [BehaviorEvent],
        direction: DeltaDirection
    ) -> Delta? {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)

        guard let current = currentValue(for: key, from: events) else { return nil }

        let referenceDate: Date
        switch period {
        case .week:
            referenceDate = calendar.date(byAdding: .day, value: -7, to: today)!
        case .month:
            referenceDate = calendar.date(byAdding: .month, value: -1, to: today)!
        }

        let refEnd = calendar.date(byAdding: .day, value: 1, to: referenceDate)!
        let referenceValue = events
            .filter { $0.timestamp >= referenceDate && $0.timestamp < refEnd }
            .sorted { $0.timestamp > $1.timestamp }
            .lazy
            .compactMap { event in
                event.metrics.first { $0.key == key && $0.quality != .missing }
            }
            .first?
            .value

        guard let referenceValue else { return nil }

        let deltaValue = current - referenceValue
        let isPositive = direction == .decrease ? deltaValue <= 0 : deltaValue >= 0

        return Delta(
            value: deltaValue,
            period: period.label,
            isPositive: isPositive
        )
    }

    /// 格式化数值为显示字符串
    static func format(
        value: Double?,
        type: MetricType,
        scaleMax: Int? = nil,
        ratioDenominator: Int? = nil
    ) -> String {
        guard let value else { return "—" }
        switch type {
        case .numeric:
            return value.truncatingRemainder(dividingBy: 1) == 0
                ? String(format: "%.0f", value)
                : String(format: "%.1f", value)
        case .scale:
            return "\(Int(value))/\(scaleMax ?? 10)"
        case .ordinal:
            return String(format: "%.0f", value)
        case .ratio:
            return "\(Int(value))/\(ratioDenominator ?? 7)"
        }
    }
}

// MARK: - Delta Period

enum DeltaPeriod {
    case week
    case month

    var label: String {
        switch self {
        case .week: "本周"
        case .month: "本月"
        }
    }
}
