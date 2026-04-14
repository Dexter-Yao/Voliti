// ABOUTME: MIRROR 页 LifeSign 摘要卡片，支持性指标与事件流之间的独立一级入口
// ABOUTME: 展示预案数量和本周执行统计，点击进入 LifeSign 列表

import SwiftUI

struct LifeSignSummaryCard: View {
    let plans: [LifeSignPlan]
    var onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                Text("LIFESIGN")
                    .starpathMono()
                    .foregroundStyle(StarpathTokens.copper)

                if plans.isEmpty {
                    Text("与 Coach 对话中创建你的第一个应对预案")
                        .starpathSans()
                        .foregroundStyle(StarpathTokens.obsidian40)
                } else {
                    let active = plans.filter { $0.status == "active" }

                    HStack(spacing: StarpathTokens.spacingSM) {
                        Text("\(active.count) 预案")
                            .starpathSans()

                        Spacer()

                        Image(systemName: "chevron.right")
                            .font(.system(size: StarpathTokens.fontSizeXS))
                            .foregroundStyle(StarpathTokens.obsidian40)
                    }
                }
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
        }
        .buttonStyle(.plain)
    }
}
