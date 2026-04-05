// ABOUTME: MIRROR 页 LifeSign 摘要卡片，Dashboard 与 Pulse 之间的独立一级入口
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

                if plans.isEmpty {
                    Text("与 Coach 对话中创建你的第一个应对预案")
                        .starpathSans()
                        .foregroundStyle(StarpathTokens.obsidian40)
                } else {
                    let active = plans.filter { $0.status == "active" }
                    let totalSuccess = active.reduce(0) { $0 + $1.successCount }
                    let totalAttempts = active.reduce(0) { $0 + $1.totalAttempts }

                    HStack(spacing: StarpathTokens.spacingSM) {
                        Text("\(active.count) 预案")
                            .starpathSans()

                        Text("·")
                            .foregroundStyle(StarpathTokens.obsidian40)

                        if totalAttempts > 0 {
                            Text("激活 \(totalAttempts) 成功 \(totalSuccess)")
                                .starpathSans()
                                .foregroundStyle(StarpathTokens.obsidian40)
                        } else {
                            Text("待激活")
                                .starpathSans()
                                .foregroundStyle(StarpathTokens.obsidian40)
                        }

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
