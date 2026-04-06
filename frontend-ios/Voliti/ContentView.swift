// ABOUTME: 应用根视图，自定义 TabBar 承载两个页签（COACH + MIRROR）
// ABOUTME: Starpath Protocol 规范：mono 字体、无图标、2px bottom border

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(NotificationService.self) private var notificationService
    @State private var selectedTab = 0

    private let tabs = ["COACH", "MIRROR"]

    var body: some View {
        VStack(spacing: 0) {
            Group {
                switch selectedTab {
                case 0: CoachView()
                case 1: MirrorView()
                default: CoachView()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            StarpathTabBar(tabs: tabs, selectedIndex: $selectedTab)
        }
        .onChange(of: notificationService.pendingDeepLink) { _, newValue in
            guard newValue != nil else { return }
            selectedTab = 0
            // pendingDeepLink 由 CoachView 消费后清除
        }
    }
}

// MARK: - Starpath TabBar

private struct StarpathTabBar: View {
    let tabs: [String]
    @Binding var selectedIndex: Int

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Array(tabs.enumerated()), id: \.offset) { index, label in
                Button {
                    selectedIndex = index
                } label: {
                    VStack(spacing: StarpathTokens.spacingXS) {
                        Text(label)
                            .font(.custom("JetBrainsMono-Regular", size: StarpathTokens.fontSizeXS))
                            .tracking(2)
                            .foregroundStyle(
                                index == selectedIndex
                                    ? StarpathTokens.obsidian
                                    : StarpathTokens.obsidian40
                            )

                        Rectangle()
                            .fill(index == selectedIndex ? StarpathTokens.obsidian : .clear)
                            .frame(height: 2)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.top, StarpathTokens.spacingSM)
                    .padding(.bottom, StarpathTokens.spacingXS)
                }
            }
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
        .background(StarpathTokens.parchment)
    }
}

#Preview {
    ContentView()
        .environment(NotificationService())
        .modelContainer(for: [
            ChatMessage.self,
            BehaviorEvent.self,
            InterventionCard.self,
            Chapter.self,
            LifeSignPlan.self,
            DashboardConfig.self,
        ], inMemory: true)
}
