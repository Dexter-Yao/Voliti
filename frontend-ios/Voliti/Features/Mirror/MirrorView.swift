// ABOUTME: MIRROR 页主视图，按 DESIGN.md 层级组合各区域
// ABOUTME: Chapter → NorthStar → Support → LifeSign → Filter + EventStream

import SwiftUI
import SwiftData

struct MirrorView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = MirrorViewModel()
    @AppStorage("onboardingComplete") private var onboardingComplete = false
    @State private var showWeightHistory = false

    var body: some View {
        NavigationStack {
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

                // North Star
                NorthStarMetric(
                    label: viewModel.northStarConfig?.label ?? "北极星",
                    value: viewModel.northStarDisplayValue,
                    unit: viewModel.northStarConfig?.unit ?? "KG",
                    delta: viewModel.northStarDelta,
                    trendData: viewModel.northStarTrend,
                    onViewAll: { showWeightHistory = true }
                )
                .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // Support Metrics
                SupportMetricSection(metrics: viewModel.supportMetrics)
                    .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // LifeSign 摘要
                LifeSignSummaryCard(plans: viewModel.lifeSignPlans) {
                    viewModel.showLifeSignList = true
                }
                .padding(.vertical, StarpathTokens.spacingLG)

                StarpathDivider()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // Event Stream
                VStack(alignment: .leading, spacing: StarpathTokens.spacingMD) {
                    FilterBar(
                        kindCounts: viewModel.kindCounts,
                        selectedKind: $viewModel.selectedFilterKind
                    )
                    .padding(.horizontal, StarpathTokens.spacingMD)
                    .padding(.top, StarpathTokens.spacingLG)

                    if viewModel.filteredGroupedEvents.isEmpty {
                        emptyState
                    } else {
                        EventStreamSection(
                            groups: viewModel.filteredGroupedEvents,
                            isExpanded: viewModel.isExpanded,
                            toggleExpanded: viewModel.toggleExpanded,
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
        .sheet(isPresented: $viewModel.showLifeSignList) {
            NavigationStack {
                LifeSignListView(plans: viewModel.lifeSignPlans)
            }
        }
        .navigationDestination(isPresented: $showWeightHistory) {
            MetricHistoryView(
                metricKey: viewModel.northStarConfig?.key ?? "weight",
                metricLabel: viewModel.northStarConfig?.label ?? "体重记录"
            )
        }
        .toolbar(.hidden)
        } // NavigationStack
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
}
