// ABOUTME: MIRROR 页支持性指标组件，3列等宽布局
// ABOUTME: 由 Coach Onboarding 确定指标，Phase B 先硬编码默认值

import SwiftUI

struct SupportMetricSection: View {
    let metrics: [SupportMetricItem]

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Array(metrics.enumerated()), id: \.element.key) { index, metric in
                if index > 0 {
                    StarpathDivider(opacity: 0.10, thickness: 1)
                        .frame(width: 1, height: 48)
                }

                VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                    Text(metric.label)
                        .starpathMono(size: 10)

                    Text(metric.value ?? "—")
                        .starpathSerif(size: 20)

                    HStack(spacing: StarpathTokens.spacingXS) {
                        if let sub = metric.subLabel {
                            Text(sub)
                                .starpathMono(size: 10)
                                .foregroundStyle(StarpathTokens.obsidian40)
                        }

                        if metric.showsEstimatedBadge {
                            Text("推断")
                                .starpathMono(size: 9, uppercase: false)
                                .foregroundStyle(StarpathTokens.copper)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.leading, index == 0 ? 0 : StarpathTokens.spacingMD)
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }
}

struct SupportMetricItem: Identifiable {
    let key: String
    let label: String
    let value: String?
    let subLabel: String?
    let showsEstimatedBadge: Bool

    var id: String { key }
}
