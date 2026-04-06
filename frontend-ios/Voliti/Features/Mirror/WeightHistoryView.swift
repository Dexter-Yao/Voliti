// ABOUTME: 体重历史记录列表页，从北极星 "查看全部记录" 导航进入
// ABOUTME: 按日期倒序展示体重记录，含 delta 变化和日期分组

import SwiftUI
import SwiftData

struct WeightHistoryView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext
    @State private var records: [BehaviorEvent] = []

    var body: some View {
        List {
            ForEach(records, id: \.id) { event in
                weightRow(event)
                    .listRowBackground(StarpathTokens.parchment)
                    .listRowSeparatorTint(StarpathTokens.obsidian10)
            }
        }
        .listStyle(.plain)
        .background(StarpathTokens.parchment)
        .scrollContentBackground(.hidden)
        .navigationTitle("")
        .toolbar {
            ToolbarItem(placement: .principal) {
                Text("体重记录")
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

    private func weightRow(_ event: BehaviorEvent) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                Text(event.timestamp, format: .dateTime.month().day().weekday(.wide))
                    .starpathSans()

                Text(event.timestamp, style: .time)
                    .starpathMono()
            }

            Spacer()

            HStack(alignment: .firstTextBaseline, spacing: StarpathTokens.spacingXS) {
                if let kg = event.weightKg {
                    Text(String(format: "%.1f", kg))
                        .starpathSerif(size: StarpathTokens.fontSizeXL)
                    Text("KG")
                        .starpathMono()
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
        }
        .padding(.vertical, StarpathTokens.spacingXS)
    }

    private func loadRecords() {
        var descriptor = FetchDescriptor<BehaviorEvent>(
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        descriptor.fetchLimit = 500
        do {
            let all = try modelContext.fetch(descriptor)
            records = all.filter { $0.type == .weighIn }
        } catch {
            records = []
        }
    }
}
