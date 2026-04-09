// ABOUTME: 扇出半 UI 面板，从底部以 sheet 方式弹出
// ABOUTME: 支持 half/three-quarter/full 三种高度，映射 SwiftUI presentationDetents

import SwiftUI

struct FanOutPanel: View {
    let payload: A2UIPayload
    var onSubmit: ([String: Any]) -> Void
    var onReject: () -> Void
    var onSkip: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 顶部细线
            StarpathDivider(opacity: 0.20)

            // 标题（protocol_prompt 不显示标题）
            if !payload.hasProtocolPrompt {
                HStack {
                    Button {
                        onReject()
                    } label: {
                        HStack(spacing: StarpathTokens.spacingXS) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 12))
                            Text("返回对话")
                        }
                        .starpathSans()
                        .foregroundStyle(StarpathTokens.obsidian40)
                    }
                    .accessibilityLabel("返回对话")
                    Spacer()
                }
                .padding(.horizontal, StarpathTokens.spacingMD)
                .padding(.top, StarpathTokens.spacingSM)
            }

            // 内容
            ScrollView {
                A2UIRenderer(
                    components: payload.components,
                    onSubmit: onSubmit,
                    onReject: onReject,
                    onSkip: onSkip
                )
            }
        }
    }
}

// MARK: - Layout → Detents

extension A2UILayout {
    var detents: Set<PresentationDetent> {
        switch self {
        case .half: [.fraction(0.5)]
        case .threeQuarter: [.fraction(0.75)]
        case .full: [.large]
        }
    }
}
