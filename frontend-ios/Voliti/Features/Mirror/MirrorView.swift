// ABOUTME: MIRROR 页主视图，组合 Chapter Context + Dashboard + Pulse + Event Stream
// ABOUTME: 纯展示层，所有数据来自 MirrorViewModel

import SwiftUI
import SwiftData

struct MirrorView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = MirrorViewModel()
    @AppStorage("onboardingComplete") private var onboardingComplete = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // Chapter Context
                if let chapter = viewModel.chapter {
                    ChapterContextSection(chapter: chapter)
                        .padding(.bottom, StarpathTokens.spacingLG)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                } else if !onboardingComplete {
                    onboardingGuide
                        .padding(.bottom, StarpathTokens.spacingLG)

                    StarpathDivider()
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }

                // Dashboard
                DashboardSection(
                    latestWeight: viewModel.latestWeight,
                    todayCalories: viewModel.todayCalories
                )
                .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // Pulse
                PulseSection(mealCounts: mealCountsLast7Days)
                    .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // Event Stream
                VStack(alignment: .leading, spacing: StarpathTokens.spacingMD) {
                    FilterBar(selected: $viewModel.selectedFilter)
                        .padding(.horizontal, StarpathTokens.spacingMD)
                        .padding(.top, StarpathTokens.spacingLG)

                    if viewModel.filteredGroupedEvents.isEmpty {
                        emptyState
                    } else {
                        EventStreamSection(
                            groups: viewModel.filteredGroupedEvents,
                            isExpanded: viewModel.isExpanded,
                            toggleExpanded: viewModel.toggleExpanded,
                            eventCount: viewModel.eventCount,
                            cardLookup: viewModel.card(for:),
                            onCardTap: { card in
                                viewModel.selectedCard = card
                            }
                        )
                    }
                }
            }
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
        .onAppear {
            viewModel.configure(modelContext: modelContext)
        }
        .fullScreenCover(item: $viewModel.selectedCard) { card in
            NavigationStack {
                CardDetailView(card: card) {
                    viewModel.deleteCard(card)
                }
            }
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("尚无行为记录")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("与 Coach 对话后，行为事件将自动记录在此")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL)
        .padding(.horizontal, StarpathTokens.spacingXL)
    }

    private var onboardingGuide: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text("与 Coach 完成首次对话后")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("这里会显示你的数据面板")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    // MARK: - Pulse Data

    private var mealCountsLast7Days: [Int] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        return (0..<7).reversed().map { daysAgo in
            let date = calendar.date(byAdding: .day, value: -daysAgo, to: today)!
            return viewModel.groupedEvents
                .first { $0.date == date }?
                .events.filter { $0.type == .meal }.count ?? 0
        }
    }
}
