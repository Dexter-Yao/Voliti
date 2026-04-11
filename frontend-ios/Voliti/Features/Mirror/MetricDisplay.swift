// ABOUTME: 指标显示值模型，统一首页与历史页的数值、单位和质量标记
// ABOUTME: 只负责展示语义，不负责事件流计算或业务状态管理

import Foundation

struct MetricDisplayValue: Equatable {
    let value: String
    let unit: String?
    let showsEstimatedBadge: Bool
}

enum MetricDisplay {
    static func make(
        value: Double?,
        quality: MetricQuality?,
        type: MetricType,
        unit: String?,
        scaleMax: Int?,
        ratioDenominator: Int?
    ) -> MetricDisplayValue? {
        guard value != nil else { return nil }
        return MetricDisplayValue(
            value: MetricComputer.format(
                value: value,
                type: type,
                scaleMax: scaleMax,
                ratioDenominator: ratioDenominator
            ),
            unit: normalizedUnit(unit),
            showsEstimatedBadge: quality == .estimated
        )
    }

    static func record(entry: MetricEntry, config: NorthStarMetricConfig) -> MetricDisplayValue {
        MetricDisplayValue(
            value: MetricComputer.format(
                value: entry.value,
                type: config.type,
                scaleMax: config.scaleMax,
                ratioDenominator: config.ratioDenominator
            ),
            unit: normalizedUnit(config.unit),
            showsEstimatedBadge: entry.quality == .estimated
        )
    }

    static func record(
        entry: MetricEntry,
        type: MetricType,
        unit: String?,
        scaleMax: Int?,
        ratioDenominator: Int?
    ) -> MetricDisplayValue {
        MetricDisplayValue(
            value: MetricComputer.format(
                value: entry.value,
                type: type,
                scaleMax: scaleMax,
                ratioDenominator: ratioDenominator
            ),
            unit: normalizedUnit(unit),
            showsEstimatedBadge: entry.quality == .estimated
        )
    }

    private static func normalizedUnit(_ unit: String?) -> String? {
        guard let unit, !unit.isEmpty else { return nil }
        return unit
    }
}
