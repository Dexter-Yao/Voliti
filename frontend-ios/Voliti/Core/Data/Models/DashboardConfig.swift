// ABOUTME: Dashboard 指标配置 SwiftData 模型，由 Coach 治理
// ABOUTME: 北极星指标 + 3 个支持性指标，4 种指标类型，Coach 写入 current_value

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

    var northStar: NorthStarMetricConfig? {
        get {
            guard let data = northStarJSON else { return nil }
            return try? JSONDecoder().decode(NorthStarMetricConfig.self, from: data)
        }
        set {
            northStarJSON = try? JSONEncoder().encode(newValue)
        }
    }

    var supportMetrics: [SupportMetricConfig] {
        get {
            guard let data = supportMetricsJSON else { return [] }
            return (try? JSONDecoder().decode([SupportMetricConfig].self, from: data)) ?? []
        }
        set {
            supportMetricsJSON = try? JSONEncoder().encode(newValue)
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

// MARK: - Metric Value (discriminated union)

enum MetricValue: Codable, Equatable {
    case numeric(value: Double, unit: String)
    case scale(value: Int, min: Int, max: Int)
    case ordinal(value: String, options: [String])
    case ratio(numerator: Int, denominator: Int)

    var displayText: String {
        switch self {
        case .numeric(let v, let unit):
            if v == v.rounded() {
                return "\(Int(v)) \(unit)"
            }
            return String(format: "%.1f %@", v, unit)
        case .scale(let v, _, _):
            return "\(v)"
        case .ordinal(let v, _):
            return v
        case .ratio(let n, let d):
            return "\(n)/\(d)"
        }
    }

    var numericValue: Double? {
        switch self {
        case .numeric(let v, _): return v
        case .scale(let v, _, _): return Double(v)
        case .ordinal(let v, let opts):
            guard let idx = opts.firstIndex(of: v) else { return nil }
            return Double(idx)
        case .ratio(let n, let d):
            guard d > 0 else { return nil }
            return Double(n) / Double(d)
        }
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case value, unit, min, max, options, numerator, denominator
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        if let numerator = try? container.decode(Int.self, forKey: .numerator),
           let denominator = try? container.decode(Int.self, forKey: .denominator) {
            self = .ratio(numerator: numerator, denominator: denominator)
        } else if let options = try? container.decode([String].self, forKey: .options),
                  let value = try? container.decode(String.self, forKey: .value) {
            self = .ordinal(value: value, options: options)
        } else if let min = try? container.decode(Int.self, forKey: .min),
                  let max = try? container.decode(Int.self, forKey: .max),
                  let value = try? container.decode(Int.self, forKey: .value) {
            self = .scale(value: value, min: min, max: max)
        } else {
            let value = try container.decode(Double.self, forKey: .value)
            let unit = (try? container.decode(String.self, forKey: .unit)) ?? ""
            self = .numeric(value: value, unit: unit)
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        switch self {
        case .numeric(let v, let unit):
            try container.encode(v, forKey: .value)
            try container.encode(unit, forKey: .unit)
        case .scale(let v, let min, let max):
            try container.encode(v, forKey: .value)
            try container.encode(min, forKey: .min)
            try container.encode(max, forKey: .max)
        case .ordinal(let v, let opts):
            try container.encode(v, forKey: .value)
            try container.encode(opts, forKey: .options)
        case .ratio(let n, let d):
            try container.encode(n, forKey: .numerator)
            try container.encode(d, forKey: .denominator)
        }
    }
}

// MARK: - North Star Config

struct NorthStarMetricConfig: Codable {
    let key: String
    let label: String
    let type: MetricType
    let unit: String
    let deltaDirection: DeltaDirection
    let currentValue: MetricValue?

    enum CodingKeys: String, CodingKey {
        case key, label, type, unit
        case deltaDirection = "delta_direction"
        case currentValue = "current_value"
    }
}

enum DeltaDirection: String, Codable {
    case decrease
    case increase
}

// MARK: - Support Metric Config

struct SupportMetricConfig: Codable {
    let key: String
    let label: String
    let type: MetricType
    let unit: String
    let order: Int
    let currentValue: MetricValue?

    enum CodingKeys: String, CodingKey {
        case key, label, type, unit, order
        case currentValue = "current_value"
    }
}
