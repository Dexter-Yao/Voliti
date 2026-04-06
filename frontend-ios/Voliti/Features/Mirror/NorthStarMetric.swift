// ABOUTME: MIRROR 页北极星指标组件，展示核心追踪数值 + 7日趋势
// ABOUTME: 三种空状态：完全空 / 有指标无数据 / 数据不足7天

import SwiftUI

struct NorthStarMetric: View {
    let label: String
    let value: String?
    let unit: String
    let delta: Delta?
    let trendData: [Double?]
    var onViewAll: (() -> Void)?
    @State private var selectedDayIndex: Int?

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            // 标签行
            HStack(spacing: StarpathTokens.spacingXS) {
                Text("\u{2605}")
                    .font(.system(size: 10))
                    .foregroundStyle(StarpathTokens.copper)
                Text(label)
                    .starpathMono(size: 10)
                    .foregroundStyle(StarpathTokens.copper)
            }

            // 数值行
            HStack(alignment: .firstTextBaseline, spacing: StarpathTokens.spacingSM) {
                Text(value ?? "—")
                    .starpathSerif(size: StarpathTokens.fontSize2XL)

                Text(unit)
                    .starpathMono()
                    .foregroundStyle(StarpathTokens.obsidian40)

                if let delta {
                    deltaView(delta)
                }
            }

            // 趋势图
            trendChart

            // 查看全部
            if value != nil, let onViewAll {
                Button(action: onViewAll) {
                    HStack {
                        Spacer()
                        Text("查看全部记录 \u{203A}")
                            .starpathMono(size: 10)
                            .foregroundStyle(StarpathTokens.obsidian40)
                    }
                    .frame(minHeight: 44)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    // MARK: - Delta

    private func deltaView(_ delta: Delta) -> some View {
        HStack(spacing: 2) {
            Image(systemName: delta.value >= 0 ? "arrow.up" : "arrow.down")
                .font(.system(size: 9, weight: .medium))
            Text(String(format: "%.1f", abs(delta.value)))
                .starpathMono(size: StarpathTokens.fontSizeXS, uppercase: false)
            Text(delta.period)
                .starpathMono(size: StarpathTokens.fontSizeXS, uppercase: false)
        }
        .foregroundStyle(delta.isPositive ? StarpathTokens.aligned : StarpathTokens.riskRed)
    }

    // MARK: - Trend Chart

    @ViewBuilder
    private var trendChart: some View {
        let hasAnyData = trendData.contains { $0 != nil }

        if !hasAnyData && value == nil {
            // 完全空状态
            emptyTrendPlaceholder("与 Coach 对话后开始记录")
        } else if !hasAnyData {
            // 有指标名无数据
            emptyTrendPlaceholder("记录第一次\(label)后显示趋势")
        } else {
            // 有数据（可能不足7天）
            filledTrendChart
        }
    }

    private func emptyTrendPlaceholder(_ message: String) -> some View {
        VStack(spacing: StarpathTokens.spacingXS) {
            RoundedRectangle(cornerRadius: 0)
                .strokeBorder(style: StrokeStyle(lineWidth: 1, dash: [4, 4]))
                .foregroundStyle(StarpathTokens.obsidian10)
                .frame(height: 40)

            Text(message)
                .starpathMono(size: 10, uppercase: false)
                .foregroundStyle(StarpathTokens.obsidian40)
        }
    }

    private var filledTrendChart: some View {
        let values = trendData.compactMap { $0 }
        let maxVal = values.max() ?? 1
        let minVal = values.min() ?? 0
        let range = max(maxVal - minVal, 0.1)

        return VStack(spacing: StarpathTokens.spacingXS) {
            HStack(alignment: .bottom, spacing: 4) {
                ForEach(Array(trendData.enumerated()), id: \.offset) { index, dataPoint in
                    let isToday = index == trendData.count - 1
                    let isSelected = selectedDayIndex == index
                    if let val = dataPoint {
                        let normalized = CGFloat((val - minVal) / range)
                        let height = max(2, normalized * 36 + 4)
                        VStack(spacing: 2) {
                            if isSelected {
                                Text(String(format: "%.1f", val))
                                    .font(.custom("JetBrainsMono-Regular", size: 9))
                                    .foregroundStyle(StarpathTokens.copper)
                            }
                            Rectangle()
                                .fill(barColor(isToday: isToday, isSelected: isSelected))
                                .frame(maxWidth: .infinity, minHeight: 2, idealHeight: height, maxHeight: height)
                        }
                        .frame(maxWidth: .infinity)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            withAnimation(.easeInOut(duration: 0.15)) {
                                selectedDayIndex = isSelected ? nil : index
                            }
                        }
                    } else {
                        Color.clear
                            .frame(maxWidth: .infinity, minHeight: 2, idealHeight: 2, maxHeight: 40)
                    }
                }
            }
            .frame(minHeight: 40)

            // 日期标签
            HStack(spacing: 0) {
                ForEach(Array(dayLabels().enumerated()), id: \.offset) { index, dayLabel in
                    Text(dayLabel)
                        .font(.custom("JetBrainsMono-Regular", size: 9))
                        .foregroundStyle(
                            selectedDayIndex == index
                                ? StarpathTokens.copper
                                : StarpathTokens.obsidian40
                        )
                        .frame(maxWidth: .infinity)
                }
            }
        }
    }

    private func barColor(isToday: Bool, isSelected: Bool) -> Color {
        (isSelected || isToday) ? StarpathTokens.copper : StarpathTokens.obsidian10
    }

    private static let weekdayFormatter: DateFormatter = {
        let f = DateFormatter()
        f.locale = Locale.current
        f.dateFormat = "E"
        return f
    }()

    private func dayLabels() -> [String] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        return (0..<7).reversed().map { daysAgo in
            let date = calendar.date(byAdding: .day, value: -daysAgo, to: today)!
            if daysAgo == 0 {
                return Locale.current.language.languageCode?.identifier == "zh" ? "今" : "Today"
            }
            return String(Self.weekdayFormatter.string(from: date).prefix(1))
        }
    }
}

// MARK: - Delta Model

struct Delta {
    let value: Double
    let period: String
    let isPositive: Bool
}
