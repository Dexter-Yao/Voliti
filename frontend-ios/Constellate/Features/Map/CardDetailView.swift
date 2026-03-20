// ABOUTME: 干预卡片全屏详情视图
// ABOUTME: 支持全屏查看图片、阅读文案、删除卡片

import SwiftUI

struct CardDetailView: View {
    let card: InterventionCard
    var onDelete: () -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var showDeleteConfirm = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: StarpathTokens.spacingLG) {
                // 图片
                if let imageData = card.imageData, let uiImage = UIImage(data: imageData) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFit()
                        .frame(maxWidth: .infinity)
                        .padding(.horizontal, StarpathTokens.spacingMD)
                }

                // 文案
                Text(card.caption)
                    .starpathSerif()
                    .padding(.horizontal, StarpathTokens.spacingMD)

                // 元数据
                HStack {
                    Text(card.purpose)
                        .starpathMono()
                    Spacer()
                    Text(card.timestamp, style: .date)
                        .starpathMono()
                }
                .padding(.horizontal, StarpathTokens.spacingMD)

                StarpathDivider()

                // 删除按钮
                Button {
                    showDeleteConfirm = true
                } label: {
                    Text("删除卡片")
                        .font(.system(size: StarpathTokens.fontSizeSM))
                        .foregroundStyle(StarpathTokens.riskRed)
                }
                .padding(.horizontal, StarpathTokens.spacingMD)
            }
            .padding(.vertical, StarpathTokens.spacingLG)
        }
        .background(StarpathTokens.parchment)
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("关闭") { dismiss() }
                    .foregroundStyle(StarpathTokens.obsidian)
            }
        }
        .alert("确认删除", isPresented: $showDeleteConfirm) {
            Button("删除", role: .destructive) {
                onDelete()
                dismiss()
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("删除后无法恢复")
        }
    }
}
