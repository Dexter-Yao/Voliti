// ABOUTME: 行为事件 SwiftData 模型，通用维度设计
// ABOUTME: kind + metrics + context 替代固定枚举和 flat union

import Foundation
import SwiftData

// MARK: - Metric Entry

struct MetricEntry: Codable, Equatable {
    let key: String
    let value: Double?
    let quality: MetricQuality
}

enum MetricQuality: String, Codable {
    case reported
    case estimated
    case missing
}

// MARK: - Behavior Event

@Model
final class BehaviorEvent {
    var id: String
    var timestamp: Date
    var recordedAt: Date
    var kind: String
    var evidence: String
    var summary: String?
    var metricsJSON: Data?
    var contextJSON: Data?
    var tags: [String]
    var refsJSON: Data?

    // MARK: - Decoded Accessors

    var metrics: [MetricEntry] {
        guard let data = metricsJSON else { return [] }
        return (try? JSONDecoder().decode([MetricEntry].self, from: data)) ?? []
    }

    var context: [String: String] {
        guard let data = contextJSON else { return [:] }
        return (try? JSONDecoder().decode([String: String].self, from: data)) ?? [:]
    }

    var refs: [String: String] {
        guard let data = refsJSON else { return [:] }
        return (try? JSONDecoder().decode([String: String].self, from: data)) ?? [:]
    }

    // MARK: - Init

    init(
        id: String = UUID().uuidString,
        timestamp: Date = .now,
        recordedAt: Date = .now,
        kind: String,
        evidence: String,
        summary: String? = nil,
        tags: [String] = []
    ) {
        self.id = id
        self.timestamp = timestamp
        self.recordedAt = recordedAt
        self.kind = kind
        self.evidence = evidence
        self.summary = summary
        self.tags = tags
    }

    // MARK: - Kind

    static let kindLabels: [String: String] = [
        "observation": "行为",
        "state": "状态",
        "milestone": "里程碑",
        "moment": "时刻",
        "reflection": "复盘",
        "system": "系统",
    ]

    var kindLabel: String {
        Self.kindLabels[kind] ?? kind
    }

    static let hiddenKinds: Set<String> = ["system"]

    // MARK: - Metric Helpers

    func setMetrics(_ entries: [MetricEntry]) {
        metricsJSON = try? JSONEncoder().encode(entries)
    }

    func setContext(_ dict: [String: String]) {
        contextJSON = try? JSONEncoder().encode(dict)
    }

    func setRefs(_ dict: [String: String]) {
        refsJSON = try? JSONEncoder().encode(dict)
    }
}
