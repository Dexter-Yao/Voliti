// ABOUTME: MIRROR 页 Pulse 区域，7 日行为趋势迷你图
// ABOUTME: Phase 1 占位实现，后续接入真实趋势数据

import SwiftUI

struct PulseSection: View {
    let mealCounts: [Int]

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text("7 日趋势")
                .starpathMono()

            if mealCounts.isEmpty {
                Text("数据积累中")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian40)
            } else {
                HStack(alignment: .bottom, spacing: 4) {
                    ForEach(Array(mealCounts.enumerated()), id: \.offset) { _, count in
                        let maxCount = mealCounts.max() ?? 1
                        let height = maxCount > 0
                            ? CGFloat(count) / CGFloat(maxCount) * 32
                            : 0
                        Rectangle()
                            .fill(StarpathTokens.obsidian.opacity(0.3))
                            .frame(width: 8, height: max(2, height))
                    }
                }
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }
}
