// ABOUTME: 干预卡片双列画廊
// ABOUTME: 样式：无圆角、1px obsidian-20 边框、图片 80% 宽 3:4 比例

import SwiftUI

struct CardGallery: View {
    let cards: [InterventionCard]
    var onSelect: (InterventionCard) -> Void

    private let columns = [
        GridItem(.flexible(), spacing: StarpathTokens.spacingLG),
        GridItem(.flexible(), spacing: StarpathTokens.spacingLG),
    ]

    var body: some View {
        LazyVGrid(columns: columns, spacing: StarpathTokens.spacingLG) {
            ForEach(cards, id: \.id) { card in
                CardThumbnail(card: card)
                    .onTapGesture { onSelect(card) }
            }
        }
    }
}

private struct CardThumbnail: View {
    let card: InterventionCard

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            // 图片
            if let imageData = card.imageData, let uiImage = UIImage(data: imageData) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFill()
                    .frame(maxWidth: .infinity)
                    .aspectRatio(3.0 / 4.0, contentMode: .fit)
                    .clipped()
            } else {
                Rectangle()
                    .fill(StarpathTokens.obsidian10)
                    .aspectRatio(3.0 / 4.0, contentMode: .fit)
            }

            // 文案
            Text(card.caption)
                .starpathSerif()
                .lineLimit(2)

            // 时间戳
            Text(card.timestamp, style: .date)
                .starpathMono()
        }
        .padding(StarpathTokens.spacingMD)
        .overlay {
            Rectangle()
                .stroke(StarpathTokens.obsidian20, lineWidth: 1)
        }
    }
}
