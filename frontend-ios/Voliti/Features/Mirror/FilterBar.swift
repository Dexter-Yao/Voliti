// ABOUTME: MIRROR 页事件流动态过滤器，只显示有记录的事件类型
// ABOUTME: 每个 pill 带计数，零记录类型不渲染

import SwiftUI

struct FilterBar: View {
    let typeCounts: [(type: EventType, count: Int)]
    @Binding var selectedType: EventType?

    var body: some View {
        HStack(spacing: StarpathTokens.spacingSM) {
            // 全部
            filterPill(
                label: "全部",
                count: typeCounts.reduce(0) { $0 + $1.count },
                isSelected: selectedType == nil
            ) {
                selectedType = nil
            }

            // 各类型
            ForEach(typeCounts, id: \.type) { item in
                filterPill(
                    label: item.type.label,
                    count: item.count,
                    isSelected: selectedType == item.type
                ) {
                    selectedType = item.type
                }
            }

            Spacer()
        }
    }

    private func filterPill(label: String, count: Int, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: StarpathTokens.spacingXS) {
                Text(label)
                    .starpathSans(size: 13)
                Text("\(count)")
                    .starpathMono(size: 10, uppercase: false)
            }
            .foregroundStyle(
                isSelected
                    ? StarpathTokens.parchment
                    : StarpathTokens.obsidian
            )
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingSM)
            .background(
                isSelected
                    ? StarpathTokens.obsidian
                    : Color.clear
            )
            .clipShape(Capsule())
            .overlay {
                if !isSelected {
                    Capsule()
                        .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                }
            }
        }
    }
}
