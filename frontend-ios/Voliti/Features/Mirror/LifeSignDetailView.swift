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
