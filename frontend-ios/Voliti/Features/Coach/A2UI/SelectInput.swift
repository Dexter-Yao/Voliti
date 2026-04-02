// ABOUTME: A2UI 单选组件，胶囊形按钮行内排列
// ABOUTME: 样式：999px 圆角，选中时 obsidian 背景 + parchment 文字

import SwiftUI

struct SelectInput: View {
    let config: SelectData
    @Binding var value: String

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text(config.label)
                .starpathMono()

            FlowLayout(spacing: StarpathTokens.spacingXS) {
                ForEach(config.options, id: \.value) { option in
                    OptionPill(
                        label: option.label,
                        isSelected: value == option.value
                    ) {
                        value = option.value
                    }
                }
            }
        }
    }
}

// MARK: - Multi Select

struct MultiSelectInput: View {
    let config: MultiSelectData
    @Binding var values: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text(config.label)
                .starpathMono()

            FlowLayout(spacing: StarpathTokens.spacingXS) {
                ForEach(config.options, id: \.value) { option in
                    OptionPill(
                        label: option.label,
                        isSelected: values.contains(option.value)
                    ) {
                        if values.contains(option.value) {
                            values.removeAll { $0 == option.value }
                        } else {
                            values.append(option.value)
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Option Pill

private struct OptionPill: View {
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .starpathSans()
                .foregroundStyle(isSelected ? StarpathTokens.parchment : StarpathTokens.obsidian)
                .padding(.horizontal, StarpathTokens.spacingMD)
                .padding(.vertical, StarpathTokens.spacingSM)
                .background(isSelected ? StarpathTokens.obsidian : .clear)
                .clipShape(Capsule())
                .overlay {
                    Capsule()
                        .stroke(
                            isSelected ? StarpathTokens.obsidian : StarpathTokens.obsidian10,
                            lineWidth: 1
                        )
                }
        }
        .animation(.easeInOut(duration: 0.15), value: isSelected)
    }
}

// MARK: - Flow Layout

struct FlowLayout: Layout {
    var spacing: CGFloat = 4

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrange(proposal: proposal, subviews: subviews)
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrange(proposal: proposal, subviews: subviews)
        for (index, position) in result.positions.enumerated() {
            subviews[index].place(
                at: CGPoint(x: bounds.minX + position.x, y: bounds.minY + position.y),
                proposal: .unspecified
            )
        }
    }

    private func arrange(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        let maxWidth = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var rowHeight: CGFloat = 0
        var totalHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if currentX + size.width > maxWidth, currentX > 0 {
                currentX = 0
                currentY += rowHeight + spacing
                rowHeight = 0
            }
            positions.append(CGPoint(x: currentX, y: currentY))
            currentX += size.width + spacing
            rowHeight = max(rowHeight, size.height)
            totalHeight = currentY + rowHeight
        }

        return (CGSize(width: maxWidth, height: totalHeight), positions)
    }
}
