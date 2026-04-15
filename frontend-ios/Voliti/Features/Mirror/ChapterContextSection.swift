// ABOUTME: MIRROR 页 Chapter Context 区域
// ABOUTME: 展示当前 Chapter 标题、里程碑和 Day N

import SwiftUI

struct ChapterContextSection: View {
    let chapter: Chapter

    var body: some View {
        VStack(alignment: .leading, spacing: StarpathTokens.spacingSM) {
            // Chapter + Day
            Text("CHAPTER · DAY \(chapter.currentDay)")
                .starpathMono()

            Text(chapter.title)
                .starpathSerif(size: StarpathTokens.fontSizeXL)

            Text(chapter.milestone)
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        }
        .padding(.horizontal, StarpathTokens.spacingMD)
    }
}
