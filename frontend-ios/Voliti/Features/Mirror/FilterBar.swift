// ABOUTME: MIRROR 页事件流动态过滤器，只显示有记录的事件类型
// ABOUTME: 每个 pill 带计数，零记录类型不渲染

import SwiftUI

struct FilterBar: View {
    let kindCounts: [(kind: String, count: Int)]
    @Binding var selectedKind: String?

    var body: some View {
        HStack(spacing: StarpathTokens.spacingSM) {
            // 全部
            filterPill(
                label: "全部",
                count: kindCounts.reduce(0) { $0 + $1.count },
                isSelected: selectedKind == nil
            ) {
                selectedKind = nil
            }

            // 各类型
            ForEach(kindCounts, id: \.kind) { item in
                filterPill(
                    label: BehaviorEvent.kindLabels[item.kind] ?? item.kind,
                    count: item.count,
                    isSelected: selectedKind == item.kind
                ) {
                    selectedKind = item.kind
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
