// ABOUTME: MIRROR 页事件流动态过滤器，承载日志类型切换与计数呈现
// ABOUTME: 已选类型在零计数时仍需保留，避免当前筛选条件被静默丢失

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
                isSelected: selectedKind == nil,
                identifier: "mirror.filter.all"
            ) {
                selectedKind = nil
            }

            // 各类型
            ForEach(kindCounts, id: \.kind) { item in
                filterPill(
                    label: BehaviorEvent.kindLabels[item.kind] ?? item.kind,
                    count: item.count,
                    isSelected: selectedKind == item.kind,
                    identifier: "mirror.filter.\(item.kind)"
                ) {
                    selectedKind = item.kind
                }
            }

            Spacer()
        }
    }

    private func filterPill(
        label: String,
        count: Int,
        isSelected: Bool,
        identifier: String,
        action: @escaping () -> Void
    ) -> some View {
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
        .accessibilityIdentifier(identifier)
    }
}
