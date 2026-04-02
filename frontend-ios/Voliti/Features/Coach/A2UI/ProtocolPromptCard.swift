// ABOUTME: 微干预卡片，Coach 检测到高压力或疲劳信号时触发
// ABOUTME: 样式：Serif 正文 + 引号问题 + ObsidianPill 双按钮（继续/暂停）

import SwiftUI

struct ProtocolPromptCard: View {
    let observation: String
    let question: String
    var onContinue: () -> Void
    var onPause: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingLG) {
            StarpathDivider(opacity: 0.20)

            Text(observation)
                .starpathSerif()

            Text("\u{201C}\(question)\u{201D}")
                .starpathSerif()

            StarpathDivider(opacity: 0.20)

            Spacer()

            HStack(spacing: StarpathTokens.spacingSM) {
                ObsidianPill(label: "继续对话", style: .outline) {
                    onContinue()
                }
                ObsidianPill(label: "暂停一下", style: .filled) {
                    onPause()
                }
            }
            .frame(maxWidth: .infinity)
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
        .padding(.vertical, StarpathTokens.spacingLG)
    }
}
