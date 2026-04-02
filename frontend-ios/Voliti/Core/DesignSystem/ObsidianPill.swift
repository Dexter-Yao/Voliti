// ABOUTME: Obsidian Pill 主交互按钮，全圆角黑色胶囊
// ABOUTME: 支持 filled（主操作）和 outline（次要操作）两种样式

import SwiftUI

struct ObsidianPill: View {
    let label: String
    var style: Style = .filled
    var disabled: Bool = false
    var action: () -> Void

    enum Style {
        case filled
        case outline
    }

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.system(size: StarpathTokens.fontSizeSM, weight: .medium))
                .foregroundStyle(foregroundColor)
                .padding(.horizontal, StarpathTokens.spacingMD)
                .padding(.vertical, StarpathTokens.spacingSM)
                .background(backgroundColor)
                .clipShape(Capsule())
                .overlay {
                    if style == .outline {
                        Capsule()
                            .stroke(StarpathTokens.obsidian, lineWidth: 1)
                    }
                }
        }
        .disabled(disabled)
        .opacity(disabled ? 0.4 : 1.0)
    }

    private var foregroundColor: Color {
        switch style {
        case .filled: StarpathTokens.parchment
        case .outline: StarpathTokens.obsidian
        }
    }

    private var backgroundColor: Color {
        switch style {
        case .filled: StarpathTokens.obsidian
        case .outline: .clear
        }
    }
}
