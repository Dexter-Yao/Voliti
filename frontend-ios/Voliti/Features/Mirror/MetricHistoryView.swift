// ABOUTME: 指定指标的历史记录列表页，从北极星 "查看全部记录" 导航进入
// ABOUTME: 按日期倒序展示记录，含分页加载（初始 50 条，滚动到底部加载更多）

import SwiftUI
import SwiftData

struct MetricHistoryView: View {
    let metricKey: String
    let metricLabel: String

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext
    @State private var records: [BehaviorEvent] = []
    @State private var displayCount = 50

    var body: some View {
        List {
            ForEach(Array(records.prefix(displayCount).enumerated()), id: \.element.id) { index, event in
                metricRow(event)
                    .listRowBackground(StarpathTokens.parchment)
                    .listRowSeparatorTint(StarpathTokens.obsidian10)
                    .onAppear {
                        // 滚动接近底部时加载更多
                        if index == displayCount - 5 && displayCount < records.count {
                            displayCount += 50
                        }
                    }
            }
        }
        .listStyle(.plain)
        .background(StarpathTokens.parchment)
        .scrollContentBackground(.hidden)
        .navigationTitle("")
        .toolbar {
            ToolbarItem(placement: .principal) {
                Text(metricLabel)
                    .starpathMono(size: StarpathTokens.fontSizeXS)
            }
            ToolbarItem(placement: .topBarLeading) {
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: StarpathTokens.fontSizeSM))
                        .foregroundStyle(StarpathTokens.obsidian)
                }
            }
        }
        .navigationBarBackButtonHidden()
        .onAppear { loadRecords() }
    }

    private func metricRow(_ event: BehaviorEvent) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                Text(event.timestamp, format: .dateTime.month().day().weekday(.wide))
                    .starpathSans()

                Text(event.timestamp, style: .time)
                    .starpathMono()
            }

            Spacer()

            HStack(alignment: .firstTextBaseline, spacing: StarpathTokens.spacingXS) {
                if let entry = event.metrics.first(where: { $0.key == metricKey }),
                   let value = entry.value {
                    let formatted = value.truncatingRemainder(dividingBy: 1) == 0
                        ? String(format: "%.0f", value)
                        : String(format: "%.1f", value)
                    Text(formatted)
                        .starpathSerif(size: StarpathTokens.fontSizeXL)
                    Text(metricKey.uppercased())
                        .starpathMono()
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
        }
        .padding(.vertical, StarpathTokens.spacingXS)
    }

    private func loadRecords() {
        let descriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        do {
            let all = try modelContext.fetch(descriptor)
            records = all.filter { event in
                event.metrics.contains { $0.key == metricKey }
            }
        } catch {
            records = []
        }
    }
}
