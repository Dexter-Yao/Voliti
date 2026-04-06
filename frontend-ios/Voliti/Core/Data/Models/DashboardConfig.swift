// ABOUTME: Dashboard 指标配置 SwiftData 模型，由 Coach 治理
// ABOUTME: 北极星指标 + 3 个支持性指标定义，值由 MetricComputer 从事件流计算

import Foundation
import SwiftData

@Model
final class DashboardConfig {
    var id: String
    var northStarJSON: Data?
    var supportMetricsJSON: Data?
    var userGoal: String?
    var lastUpdated: Date

    init(
        id: String = "default",
        userGoal: String? = nil,
        lastUpdated: Date = .now
    ) {
        self.id = id
        self.userGoal = userGoal
        self.lastUpdated = lastUpdated
    }

    @Transient private var _northStarCache: NorthStarMetricConfig??
    @Transient private var _supportMetricsCache: [SupportMetricConfig]?

    var northStar: NorthStarMetricConfig? {
        get {
            if let cached = _northStarCache { return cached }
            guard let data = northStarJSON else { _northStarCache = .some(nil); return nil }
            let decoded = try? JSONDecoder().decode(NorthStarMetricConfig.self, from: data)
            _northStarCache = .some(decoded)
            return decoded
        }
        set {
            northStarJSON = try? JSONEncoder().encode(newValue)
            _northStarCache = .some(newValue)
        }
    }

    var supportMetrics: [SupportMetricConfig] {
        get {
            if let cached = _supportMetricsCache { return cached }
            guard let data = supportMetricsJSON else { _supportMetricsCache = []; return [] }
            let decoded = (try? JSONDecoder().decode([SupportMetricConfig].self, from: data)) ?? []
            _supportMetricsCache = decoded
            return decoded
        }
        set {
            supportMetricsJSON = try? JSONEncoder().encode(newValue)
            _supportMetricsCache = newValue
        }
    }
}

// MARK: - Metric Type

enum MetricType: String, Codable {
    case numeric
    case scale
    case ordinal
    case ratio
}

// MARK: - Delta Direction

enum DeltaDirection: String, Codable {
    case decrease
    case increase
}

// MARK: - North Star Config

struct NorthStarMetricConfig: Codable {
    let key: String
    let label: String
    let type: MetricType
    let unit: String
    let deltaDirection: DeltaDirection
    let scaleMax: Int?
    let ratioDenominator: Int?

    enum CodingKeys: String, CodingKey {
        case key, label, type, unit
        case deltaDirection = "delta_direction"
        case scaleMax = "scale_max"
        case ratioDenominator = "ratio_denominator"
    }
}

// MARK: - Support Metric Config

struct SupportMetricConfig: Codable {
    let key: String
    let label: String
    let type: MetricType
    let unit: String
    let order: Int
    let scaleMax: Int?
    let ratioDenominator: Int?

    enum CodingKeys: String, CodingKey {
        case key, label, type, unit, order
        case scaleMax = "scale_max"
        case ratioDenominator = "ratio_denominator"
    }
}
