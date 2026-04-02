// ABOUTME: A2UI 滑块输入组件，用于 1-10 量表（能量、情绪、压力等）
// ABOUTME: 样式：2px 轨道 obsidian-10，16px thumb obsidian，标签 mono 大写

import SwiftUI

struct SliderInput: View {
    let config: SliderData
    @Binding var value: Double

    private var minValue: Double { Double(config.min ?? 1) }
    private var maxValue: Double { Double(config.max ?? 10) }
    private var stepValue: Double { Double(config.step ?? 1) }

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            HStack {
                Text(config.label)
                    .starpathMono()
                Spacer()
                Text("\(Int(value))")
                    .starpathMono(size: StarpathTokens.fontSizeSM, uppercase: false)
            }

            Slider(
                value: $value,
                in: minValue...maxValue,
                step: stepValue
            )
            .tint(StarpathTokens.obsidian)
        }
    }
}
