// ABOUTME: Coach 思路卡片，展示教练的观察和策略选择
// ABOUTME: 默认折叠，点击展开，视觉上与消息正文明确区分

import SwiftUI

struct ThinkingCard: View {
    let strategy: String
    let observations: [String]
    let actions: [String]

    @State private var isExpanded: Bool

    init(strategy: String, observations: [String], actions: [String] = []) {
        self.strategy = strategy
        self.observations = observations
        self.actions = actions
        _isExpanded = State(initialValue: false)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 标题行（始终可见）
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(spacing: StarpathTokens.spacingSM) {
                    Image(systemName: "lightbulb.min")
                        .font(.system(size: StarpathTokens.fontSizeXS))
                        .foregroundStyle(StarpathTokens.obsidian40)

                    Text(strategy)
                        .starpathSans(size: 13)
                        .foregroundStyle(StarpathTokens.obsidian40)
                        .lineLimit(isExpanded ? nil : 1)

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.system(size: StarpathTokens.fontSizeXS))
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
            .buttonStyle(.plain)

            // 展开区域
            if isExpanded && (!observations.isEmpty || !actions.isEmpty) {
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    ForEach(Array(observations.enumerated()), id: \.offset) { _, text in
                        itemRow(bullet: "·", text: text, color: StarpathTokens.obsidian40)
                    }
                    ForEach(Array(actions.enumerated()), id: \.offset) { _, text in
                        itemRow(bullet: "→", text: text, color: StarpathTokens.obsidian, bulletColor: StarpathTokens.copper)
                    }
                }
                .padding(.top, StarpathTokens.spacingXS)
                .padding(.leading, StarpathTokens.spacingLG)
            }
        }
        .padding(.horizontal, StarpathTokens.spacingSM)
        .padding(.vertical, StarpathTokens.spacingSM)
        .overlay(
            Rectangle()
                .frame(width: 2)
                .foregroundStyle(StarpathTokens.obsidian10),
            alignment: .leading
        )
    }

    private func itemRow(bullet: String, text: String, color: Color, bulletColor: Color? = nil) -> some View {
        HStack(alignment: .top, spacing: StarpathTokens.spacingSM) {
            Text(bullet)
                .foregroundStyle(bulletColor ?? color)
            Text(text)
                .starpathSans(size: 13)
                .foregroundStyle(color)
        }
    }
}
