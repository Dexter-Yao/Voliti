// ABOUTME: MIRROR 页 Dashboard 区域，展示关键指标
// ABOUTME: Phase 1 硬编码体重 + 卡路里；Phase 2 由 Coach 配置

import SwiftUI

struct DashboardSection: View {
    let latestWeight: Double?
    let todayCalories: Int?

    var body: some View {
        HStack(spacing: StarpathTokens.spacingLG) {
            metricCard(
                label: "体重",
                value: latestWeight.map { String(format: "%.1f", $0) },
                unit: "KG"
            )

            StarpathDivider(opacity: 0.10, thickness: 1)
                .frame(width: 1, height: 40)

            metricCard(
                label: "今日卡路里",
                value: todayCalories.map { "\($0)" },
                unit: "KCAL"
            )

            Spacer()
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    private func metricCard(label: String, value: String?, unit: String) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(label)
                .starpathMono()

            HStack(alignment: .firstTextBaseline, spacing: StarpathTokens.spacingXS) {
                Text(value ?? "—")
                    .starpathSerif(size: StarpathTokens.fontSizeXL)

                Text(unit)
                    .starpathMono()
            }
        }
    }
}
