// ABOUTME: MIRROR 页 Dashboard 区域，展示关键指标
// ABOUTME: 由 Coach 配置驱动（DashboardConfig），无 config 时回退到体重 + 卡路里

import SwiftUI

struct DashboardSection: View {
    let config: DashboardConfig?
    let latestWeight: Double?
    let todayCalories: Int?
    let userGoal: String?

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingMD) {
            // 用户目标
            if let goal = displayGoal, !goal.isEmpty {
                Text(goal)
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
            }

            // 指标卡片
            HStack(spacing: StarpathTokens.spacingLG) {
                ForEach(Array(displayMetrics.enumerated()), id: \.element.key) { index, metric in
                    if index > 0 {
                        StarpathDivider(opacity: 0.10, thickness: 1)
                            .frame(width: 1, height: 40)
                    }
                    metricCard(
                        label: metric.label,
                        value: metricValue(for: metric.key),
                        unit: metric.unit
                    )
                }
                Spacer()
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    // MARK: - Display Logic

    private var displayGoal: String? {
        userGoal ?? config?.userGoal
    }

    private var displayMetrics: [DashboardMetric] {
        if let config, !config.metrics.isEmpty {
            return config.metrics.sorted { $0.order < $1.order }
        }
        return [
            DashboardMetric(key: "weight", label: "体重", unit: "KG", order: 0),
            DashboardMetric(key: "calories", label: "今日卡路里", unit: "KCAL", order: 1),
        ]
    }

    private func metricValue(for key: String) -> String? {
        switch key {
        case "weight":
            return latestWeight.map { String(format: "%.1f", $0) }
        case "calories":
            return todayCalories.map { "\($0)" }
        default:
            return nil
        }
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
