// ABOUTME: 单条事件行，通用维度渲染
// ABOUTME: kind 标签 + 时间 + 摘要 + metrics 列表 + 证据引用

import SwiftUI

struct EventRow: View {
    let event: BehaviorEvent

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            HStack(alignment: .firstTextBaseline) {
                // 事件类型标签
                Text(event.kindLabel)
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

            // 通用 metrics 展示
            if !event.metrics.isEmpty {
                let parts = event.metrics.compactMap { entry -> String? in
                    guard let value = entry.value else { return nil }
                    let formatted = value.truncatingRemainder(dividingBy: 1) == 0
                        ? String(format: "%.0f", value)
                        : String(format: "%.1f", value)
                    return "\(entry.key): \(formatted)"
                }
                if !parts.isEmpty {
                    Text(parts.joined(separator: " · "))
                        .starpathMono(uppercase: false)
                }
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
}
