// ABOUTME: 行为事件 SwiftData 模型，flat union 设计
// ABOUTME: 映射 backend/src/voliti/schemas.py 的 7 种事件类型

import Foundation
import SwiftData

enum EventType: String, Codable {
    case meal
    case exercise
    case weighIn = "weigh_in"
    case waterIntake = "water_intake"
    case stateCheckin = "state_checkin"
    case goalUpdate = "goal_update"
    case appAction = "app_action"

    var label: String {
        switch self {
        case .meal: "饮食"
        case .exercise: "运动"
        case .weighIn: "体重"
        case .waterIntake: "饮水"
        case .stateCheckin: "状态"
        case .goalUpdate: "目标"
        case .appAction: "操作"
        }
    }
}

@Model
final class BehaviorEvent {
    var id: String
    var timestamp: Date
    var type: EventType
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
        type: EventType,
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
