// ABOUTME: Map 页主视图，展示 Chapter 元数据和干预卡片归档
// ABOUTME: 设计哲学："Map Over Metrics"——用户在地图上，不是在数轴上

import SwiftUI
import SwiftData

struct MapView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var viewModel = MapViewModel()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingLG) {
                // Chapter 元数据
                if let chapter = viewModel.chapter {
                    chapterHeader(chapter)
                }

                // 卡片画廊
                if viewModel.cards.isEmpty {
                    emptyState
                } else {
                    CardGallery(cards: viewModel.cards) { card in
                        viewModel.selectedCard = card
                    }
                    .padding(.horizontal, StarpathTokens.spacingMD)
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

    // MARK: - Chapter Header

    private func chapterHeader(_ chapter: Chapter) -> some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            Text(chapter.identityStatement)
                .starpathSerif(size: StarpathTokens.fontSizeXL)

            HStack {
                Text(chapter.goal)
                    .starpathSans()
                Spacer()
                Text("Day \(chapter.currentDay)")
                    .starpathMono()
            }

            StarpathDivider()
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: StarpathTokens.spacingMD) {
            Text("尚无教练洞察")
                .starpathSerif(size: StarpathTokens.fontSizeLG)
            Text("随着对话的深入，Coach 会在关键时刻生成洞察卡片")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, StarpathTokens.spacingXL * 2)
        .padding(.horizontal, StarpathTokens.spacingXL)
    }
}
