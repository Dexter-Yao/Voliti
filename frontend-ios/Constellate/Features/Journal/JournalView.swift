// ABOUTME: Journal 页主视图，按日分组展示行为事件时间线
// ABOUTME: 逆时间序，仅显示有数据的日子，禁止空状态占位和红绿色编码

import SwiftUI
import SwiftData

struct JournalView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = JournalViewModel()

    var body: some View {
        ScrollView {
            if viewModel.groupedEvents.isEmpty {
                emptyState
            } else {
                LazyVStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(viewModel.groupedEvents.enumerated()), id: \.element.date) { index, group in
                        // 日期标题
                        Text(group.date, format: .dateTime.year().month().day())
                            .starpathSerif()
                            .padding(.horizontal, StarpathTokens.spacingMD)
                            .padding(.top, index == 0 ? 0 : StarpathTokens.spacingLG)
                            .padding(.bottom, StarpathTokens.spacingSM)

                        // 事件列表
                        ForEach(group.events, id: \.id) { event in
                            EventRow(event: event)
                                .padding(.horizontal, StarpathTokens.spacingMD)
                            StarpathDivider()
                                .padding(.horizontal, StarpathTokens.spacingMD)
                        }

                        // 周/月边界粗线
                        if isWeekBoundary(at: index) {
                            StarpathDivider(opacity: 0.15, thickness: 2)
                                .padding(.horizontal, StarpathTokens.spacingMD)
                        }
                    }
                }
                .padding(.vertical, StarpathTokens.spacingLG)
            }
        }
        .background(StarpathTokens.parchment)
        .onAppear {
            viewModel.configure(modelContext: modelContext)
        }
    }

    private var emptyState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("尚无行为记录")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("与 Coach 对话后，行为事件将自动记录在此")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL * 2)
        .padding(.horizontal, StarpathTokens.spacingXL)
    }

    private func isWeekBoundary(at index: Int) -> Bool {
        let groups = viewModel.groupedEvents
        guard index + 1 < groups.count else { return false }

        let calendar = Calendar.current
        let currentWeek = calendar.component(.weekOfYear, from: groups[index].date)
        let nextWeek = calendar.component(.weekOfYear, from: groups[index + 1].date)
        return currentWeek != nextWeek
    }
}
