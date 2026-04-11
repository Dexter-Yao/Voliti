// ABOUTME: MIRROR 页主视图，按 DESIGN.md 层级组合各区域
// ABOUTME: Chapter → NorthStar → Support → LifeSign → Filter + EventStream

import SwiftUI
import SwiftData

struct MirrorView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = MirrorViewModel()
    @AppStorage("onboardingComplete") private var onboardingComplete = false
    @AppStorage(ProjectionFreshness.userDefaultsKey) private var storeProjectionIsStale = false
    @AppStorage("mirrorLogRangeSelection") private var storedLogRangeSelection = MirrorLogRange.defaultValue.storageValue
    @State private var showWeightHistory = false
    @State private var showLogRangeSheet = false

    var body: some View {
        NavigationStack {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if storeProjectionIsStale {
                    staleProjectionBanner
                        .padding(.bottom, StarpathTokens.spacingLG)
                }

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
                    unit: viewModel.northStarDisplayUnit ?? viewModel.northStarConfig?.unit ?? "KG",
                    showsEstimatedBadge: viewModel.northStarShowsEstimatedBadge,
                    delta: viewModel.northStarDelta,
                    trendData: viewModel.northStarTrend,
                    trendQualities: viewModel.northStarTrendQualities,
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
                    HStack(alignment: .center, spacing: StarpathTokens.spacingMD) {
                        Text("LOG / 日志")
                            .starpathMono(size: 10)
                            .foregroundStyle(StarpathTokens.copper)

                        Spacer()

                        Button {
                            showLogRangeSheet = true
                        } label: {
                            HStack(spacing: StarpathTokens.spacingXS) {
                                Text(viewModel.logRange.title())
                                    .starpathMono(size: 10, uppercase: false)
                                Image(systemName: "chevron.down")
                                    .font(.system(size: StarpathTokens.fontSizeXS))
                            }
                            .foregroundStyle(
                                canChooseLogRange
                                    ? StarpathTokens.obsidian
                                    : StarpathTokens.obsidian40
                            )
                        }
                        .accessibilityIdentifier("mirror.logRangeButton")
                        .disabled(!canChooseLogRange)
                    }
                    .padding(.horizontal, StarpathTokens.spacingMD)
                    .padding(.top, StarpathTokens.spacingLG)

                    if viewModel.shouldShowLogFilters {
                        FilterBar(
                            kindCounts: viewModel.kindCounts,
                            selectedKind: $viewModel.selectedFilterKind
                        )
                        .padding(.horizontal, StarpathTokens.spacingMD)
                    }

                    switch viewModel.logDisplayState {
                    case .loading:
                        logLoadingState
                    case .emptyInRange:
                        emptyInRangeState
                    case .emptyAfterFilter:
                        emptyAfterFilterState
                    case .ready:
                        EventStreamSection(
                            groups: viewModel.filteredGroupedEvents,
                            isExpanded: viewModel.isExpanded,
                            toggleExpanded: viewModel.toggleExpanded,
                            cardLookup: viewModel.card(for:),
                            onCardTap: { card in
                                viewModel.selectedCard = card
                            }
                        )
                    case .failed:
                        logFailedState
                    }
                }
            }
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
        .onAppear {
            viewModel.configure(modelContext: modelContext)
            if let restoredRange = MirrorLogRange.fromStorageValue(storedLogRangeSelection),
               restoredRange != viewModel.logRange {
                viewModel.applyLogRange(restoredRange)
            }
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
        .sheet(isPresented: $showLogRangeSheet) {
            MirrorLogRangeSheet(
                currentRange: viewModel.logRange,
                hasChapter: viewModel.chapter != nil,
                onSelectRange: { range in
                    viewModel.applyLogRange(range)
                }
            )
        }
        .onChange(of: viewModel.logRange) { _, newRange in
            storedLogRangeSelection = newRange.storageValue
        }
        .navigationDestination(isPresented: $showWeightHistory) {
            MetricHistoryView(
                metricKey: viewModel.northStarConfig?.key ?? "weight",
                metricLabel: viewModel.northStarConfig?.label ?? "体重记录",
                metricType: viewModel.northStarConfig?.type ?? .numeric,
                metricUnit: viewModel.northStarConfig?.unit,
                scaleMax: viewModel.northStarConfig?.scaleMax,
                ratioDenominator: viewModel.northStarConfig?.ratioDenominator
            )
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(.hidden, for: .navigationBar)
        .settingsToolbar()
        } // NavigationStack
    }

    // MARK: - Empty State

    private var canChooseLogRange: Bool {
        !storeProjectionIsStale && !viewModel.isRefreshingProjection
    }

    private var logLoadingState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            ProgressView()
            Text("正在更新日志")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("请稍候，正在切换当前日志范围")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL)
        .padding(.horizontal, StarpathTokens.spacingXL)
        .accessibilityIdentifier("mirror.log.loading")
    }

    private var emptyInRangeState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("当前范围内暂无记录")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("换一个日志范围，或继续与 Coach 对话后再回来查看")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL)
        .padding(.horizontal, StarpathTokens.spacingXL)
        .accessibilityIdentifier("mirror.log.emptyInRange")
    }

    private var emptyAfterFilterState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("当前筛选条件下暂无记录")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Button("查看全部") {
                viewModel.selectedFilterKind = nil
            }
            .buttonStyle(.plain)
            .starpathSans()
            .foregroundStyle(StarpathTokens.copper)
            .accessibilityIdentifier("mirror.log.showAll")
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL)
        .padding(.horizontal, StarpathTokens.spacingXL)
        .accessibilityIdentifier("mirror.log.emptyAfterFilter")
    }

    private var logFailedState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("日志范围切换失败")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("请稍后重试")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL)
        .padding(.horizontal, StarpathTokens.spacingXL)
        .accessibilityIdentifier("mirror.log.failed")
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

    private var staleProjectionBanner: some View {
        HStack(spacing: StarpathTokens.spacingSM) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: StarpathTokens.fontSizeXS))
            VStack(alignment: .leading, spacing: StarpathTokens.spacingXS) {
                Text("当前数据暂未更新到最新状态")
                    .starpathSans(size: StarpathTokens.fontSizeSM)
                Text("请刷新数据后再切换日志范围")
                    .starpathSans(size: StarpathTokens.fontSizeSM)
                    .foregroundStyle(StarpathTokens.obsidian40)
            }
            Spacer()
            Button(viewModel.isRefreshingProjection ? "刷新中..." : "刷新数据") {
                Task {
                    let service = StoreSyncService(modelContext: modelContext)
                    let freshness = await viewModel.refreshProjection(using: service)
                    storeProjectionIsStale = freshness == .stale
                }
            }
            .buttonStyle(.plain)
            .disabled(viewModel.isRefreshingProjection)
            .starpathSans(size: StarpathTokens.fontSizeSM)
            .accessibilityIdentifier("mirror.stale.refresh")
        }
        .foregroundStyle(StarpathTokens.copper)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, StarpathTokens.spacingMD)
        .padding(.vertical, StarpathTokens.spacingSM)
        .background(StarpathTokens.obsidian05)
        .accessibilityIdentifier("mirror.stale.banner")
    }
}
