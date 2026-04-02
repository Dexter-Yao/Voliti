// ABOUTME: A2UI 文本输入组件，用于自由文本填写
// ABOUTME: 样式：透明背景，1px obsidian-10 边框，4px 圆角

import SwiftUI

struct A2UITextInput: View {
    let config: TextInputData
    @Binding var value: String

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(config.label)
                .starpathMono()

            TextField(config.placeholder ?? "", text: $value, axis: .vertical)
                .lineLimit(2...5)
                .starpathSans()
                .padding(StarpathTokens.spacingSM)
                .background(
                    RoundedRectangle(cornerRadius: 4)
                        .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                )
        }
    }
}
