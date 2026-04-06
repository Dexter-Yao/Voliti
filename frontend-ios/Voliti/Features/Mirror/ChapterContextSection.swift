// ABOUTME: MIRROR 页 Chapter Context 区域
// ABOUTME: 展示当前 Chapter 身份宣言、目标、Day N

import SwiftUI

struct ChapterContextSection: View {
    let chapter: Chapter

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            // Chapter + Day
            Text("CHAPTER · DAY \(chapter.currentDay)")
                .starpathMono()

            // 身份宣言
            Text(chapter.identityStatement)
                .starpathSerif(size: StarpathTokens.fontSizeXL)

            // 目标
            Text(chapter.goal)
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }
}
