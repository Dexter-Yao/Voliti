// ABOUTME: Starpath Protocol 细线分割组件
// ABOUTME: 用于面板顶部、内容区域分隔，遵循 obsidian 透明度层级

import SwiftUI

struct StarpathDivider: View {
    var opacity: Double = 0.10
    var thickness: CGFloat = 1

    var body: some View {
        Rectangle()
            .fill(StarpathTokens.obsidian.opacity(opacity))
            .frame(height: thickness)
    }
}
