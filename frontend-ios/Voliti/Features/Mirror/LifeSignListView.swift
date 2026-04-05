// ABOUTME: LifeSign 预案列表页，从摘要卡片点击进入
// ABOUTME: 展示所有 active 预案，点击进入详情

import SwiftUI

struct LifeSignListView: View {
    let plans: [LifeSignPlan]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 0) {
                ForEach(activePlans, id: \.id) { plan in
                    NavigationLink {
                        LifeSignDetailView(plan: plan)
                    } label: {
                        planRow(plan)
                    }
                    .buttonStyle(.plain)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }
            }
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
        .navigationTitle("LifeSign")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("关闭") { dismiss() }
                    .foregroundStyle(StarpathTokens.obsidian)
            }
        }
    }

    private var activePlans: [LifeSignPlan] {
        plans.filter { $0.status == "active" }
            .sorted { $0.lastUpdated > $1.lastUpdated }
    }

    private func planRow(_ plan: LifeSignPlan) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
            Text(plan.trigger)
                .starpathSans()

            Text("→ \(plan.copingResponse)")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)

            HStack(spacing: StarpathTokens.spacingSM) {
                if plan.totalAttempts > 0 {
                    Text("\(plan.successCount)/\(plan.totalAttempts) 成功")
                        .starpathMono()
                } else {
                    Text("待激活")
                        .starpathMono()
                }
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
        .padding(.vertical, StarpathTokens.spacingSM)
    }
}
