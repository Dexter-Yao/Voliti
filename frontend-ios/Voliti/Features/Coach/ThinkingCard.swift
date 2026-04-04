// ABOUTME: Coach 思路卡片，展示教练的观察和策略选择
// ABOUTME: 默认展开，点击切换折叠，视觉上与消息正文明确区分

import SwiftUI

struct ThinkingCard: View {
    let block: ThinkingBlock
    let defaultExpanded: Bool

    @State private var isExpanded: Bool = true

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // 标题行（始终可见）
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(spacing: StarpathTokens.spacingSM) {
                    Text("💡")
                        .font(.system(size: StarpathTokens.fontSizeSM))

                    Text(block.strategy)
                        .font(.system(size: StarpathTokens.fontSizeSM))
                        .foregroundStyle(StarpathTokens.obsidian40)
                        .lineLimit(isExpanded ? nil : 1)

                    Spacer()

                    Image(systemName: isExpanded ? "chevron.down" : "chevron.right")
                        .font(.system(size: 10))
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
            .buttonStyle(.plain)

            // 展开区域
            if isExpanded && !block.observations.isEmpty {
                VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                    ForEach(block.observations, id: \.self) { observation in
                        HStack(alignment: .top, spacing: StarpathTokens.spacingSM) {
                            Text("·")
                                .foregroundStyle(StarpathTokens.obsidian40)
                            Text(observation)
                                .font(.system(size: StarpathTokens.fontSizeSM))
                                .foregroundStyle(StarpathTokens.obsidian40)
                        }
                    }
                }
                .padding(.top, StarpathTokens.spacingXS)
                .padding(.leading, StarpathTokens.spacingMD + StarpathTokens.spacingSM)
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
        .onAppear {
            isExpanded = defaultExpanded
        }
    }
}
