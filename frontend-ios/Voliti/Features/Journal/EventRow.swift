// ABOUTME: Journal 页单条事件行
// ABOUTME: 类型标签 Sans + 时间 Mono + 摘要 + 证据引用

import SwiftUI

struct EventRow: View {
    let event: BehaviorEvent

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            HStack(alignment: .firstTextBaseline) {
                // 事件类型
                Text(event.type.label)
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
                    .starpathMono(uppercase: false)
            }

            // 证据引用
            if !event.evidence.isEmpty {
                Text("「\(event.evidence)」")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
            }

            // 标签
            if !event.tags.isEmpty {
                HStack(spacing: StarpathTokens.spacingXS) {
                    ForEach(event.tags, id: \.self) { tag in
                        Text("[\(tag)]")
                            .starpathMono(uppercase: false)
                    }
                }
            }
        }
        .padding(.vertical, StarpathTokens.spacingSM)
    }

    private func buildDataSummary() -> String? {
        var parts: [String] = []
        switch event.type {
        case .meal:
            if let kcal = event.kcal { parts.append("\(Int(kcal)) kcal") }
            if let p = event.proteinG { parts.append("P\(Int(p))g") }
        case .exercise:
            if let dur = event.durationMin { parts.append("\(Int(dur))min") }
            if let burned = event.kcalBurned { parts.append("\(Int(burned)) kcal") }
        case .weighIn:
            if let kg = event.weightKg { parts.append("\(String(format: "%.1f", kg)) kg") }
        case .waterIntake:
            if let ml = event.waterMl { parts.append("\(Int(ml)) ml") }
        case .stateCheckin:
            if let e = event.energy { parts.append("E:\(e)") }
            if let m = event.mood { parts.append("M:\(m)") }
            if let s = event.stress { parts.append("S:\(s)") }
        case .goalUpdate, .appAction:
            break
        }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }
}
