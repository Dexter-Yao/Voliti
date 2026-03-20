// ABOUTME: Journal 页单条事件行
// ABOUTME: 类型标签 Sans + 时间 Mono + 摘要 + 证据引用

import SwiftUI

struct EventRow: View {
    let event: BehaviorEvent

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            HStack(alignment: .firstTextBaseline) {
                // 事件类型
                Text(eventTypeLabel)
                    .starpathSans()

                Spacer()

                // 时间
                Text(event.timestamp, style: .time)
                    .starpathMono()
            }

            // 摘要
            if let summary = event.summary, !summary.isEmpty {
                Text(summary)
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian)
            }

            // 数据摘要
            if let dataSummary = buildDataSummary() {
                Text(dataSummary)
                    .font(.system(size: StarpathTokens.fontSizeXS, design: .monospaced))
                    .foregroundStyle(StarpathTokens.obsidian40)
            }

            // 证据引用
            if !event.evidence.isEmpty {
                Text("「\(event.evidence)」")
                    .starpathSerif()
                    .foregroundStyle(StarpathTokens.obsidian40)
            }

            // 标签
            if !event.tags.isEmpty {
                HStack(spacing: StarpathTokens.spacingXS) {
                    ForEach(event.tags, id: \.self) { tag in
                        Text("[\(tag)]")
                            .font(.system(size: StarpathTokens.fontSizeXS, design: .monospaced))
                            .foregroundStyle(StarpathTokens.obsidian40)
                    }
                }
            }
        }
        .padding(.vertical, StarpathTokens.spacingSM)
    }

    private var eventTypeLabel: String {
        switch event.type {
        case "meal": "饮食"
        case "exercise": "运动"
        case "weigh_in": "体重"
        case "water_intake": "饮水"
        case "state_checkin": "状态"
        case "goal_update": "目标"
        case "app_action": "操作"
        default: event.type
        }
    }

    private func buildDataSummary() -> String? {
        var parts: [String] = []
        switch event.type {
        case "meal":
            if let kcal = event.kcal { parts.append("\(Int(kcal)) kcal") }
            if let p = event.proteinG { parts.append("P\(Int(p))g") }
        case "exercise":
            if let dur = event.durationMin { parts.append("\(Int(dur))min") }
            if let burned = event.kcalBurned { parts.append("\(Int(burned)) kcal") }
        case "weigh_in":
            if let kg = event.weightKg { parts.append("\(String(format: "%.1f", kg)) kg") }
        case "water_intake":
            if let ml = event.waterMl { parts.append("\(Int(ml)) ml") }
        case "state_checkin":
            if let e = event.energy { parts.append("E:\(e)") }
            if let m = event.mood { parts.append("M:\(m)") }
            if let s = event.stress { parts.append("S:\(s)") }
        default:
            break
        }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }
}
