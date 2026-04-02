// ABOUTME: A2UI 数值输入组件，用于体重等精确数值
// ABOUTME: 样式：透明背景，1px obsidian-10 边框，4px 圆角，单位标签 obsidian-40

import SwiftUI

struct NumberInput: View {
    let config: NumberInputData
    @Binding var value: String

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(config.label)
                .starpathMono()

            HStack(spacing: StarpathTokens.spacingSM) {
                TextField("", text: $value)
                    .keyboardType(.decimalPad)
                    .starpathSans()
                    .padding(StarpathTokens.spacingSM)
                    .background(
                        RoundedRectangle(cornerRadius: 4)
                            .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                    )

                if let unit = config.unit, !unit.isEmpty {
                    Text(unit)
                        .starpathSans()
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
        }
    }
}
