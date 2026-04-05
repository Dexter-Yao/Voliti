// ABOUTME: LifeSign 预案详情页
// ABOUTME: 展示触发条件、应对行为、执行统计

import SwiftUI

struct LifeSignDetailView: View {
    let plan: LifeSignPlan

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingLG) {
                // 触发条件
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    Text("IF")
                        .starpathMono()
                    Text(plan.trigger)
                        .starpathSerif()
                }

                StarpathDivider()

                // 应对行为
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    Text("THEN")
                        .starpathMono()
                    Text(plan.copingResponse)
                        .starpathSerif()
                }

                StarpathDivider()

                // 执行统计
                VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
                    Text("统计")
                        .starpathMono()

                    HStack(spacing: StarpathTokens.spacingLG) {
                        statItem(label: "激活", value: "\(plan.totalAttempts)")
                        statItem(label: "成功", value: "\(plan.successCount)")
                        if plan.totalAttempts > 0 {
                            statItem(
                                label: "成功率",
                                value: "\(Int(plan.successRate * 100))%"
                            )
                        }
                    }
                }

                StarpathDivider()

                Text(plan.lastUpdated, style: .date)
                    .starpathMono()
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
    }

    private func statItem(label: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(label)
                .starpathMono()
            Text(value)
                .starpathSerif(size: StarpathTokens.fontSizeLG)
        }
    }
}
