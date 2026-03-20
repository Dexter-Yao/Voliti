// ABOUTME: 行为事件 SwiftData 模型，flat union 设计
// ABOUTME: 映射 backend/src/constellate/schemas.py 的 7 种事件类型

import Foundation
import SwiftData

@Model
final class BehaviorEvent {
    var id: String
    var timestamp: Date
    var type: String
    var evidence: String
    var summary: String?
    var tags: [String]

    // Meal
    var kcal: Double?
    var proteinG: Double?
    var carbG: Double?
    var fatG: Double?
    var fiberG: Double?
    var confidence: Double?

    // Exercise
    var exerciseType: String?
    var durationMin: Double?
    var kcalBurned: Double?
    var intensity: String?

    // Weight
    var weightKg: Double?
    var bodyFatPct: Double?

    // Water
    var waterMl: Double?

    // State check-in
    var energy: Int?
    var mood: Int?
    var stress: Int?
    var sleepHours: Double?
    var sleepQuality: Int?

    // Goal / App Action
    var details: String?
    var action: String?

    init(
        id: String = UUID().uuidString,
        timestamp: Date = .now,
        type: String,
        evidence: String,
        summary: String? = nil,
        tags: [String] = []
    ) {
        self.id = id
        self.timestamp = timestamp
        self.type = type
        self.evidence = evidence
        self.summary = summary
        self.tags = tags
    }
}
