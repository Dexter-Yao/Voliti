// ABOUTME: 对话消息列表，Coach 左对齐 Serif / 用户右对齐 Sans + 圆角面板
// ABOUTME: 时间戳由 TimestampSeparator 组件按 5 级规则自动显示

import SwiftUI

struct MessageList: View {
    let messages: [ChatMessage]
    let isStreaming: Bool

    @State private var lastScrollDate = Date.distantPast

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: StarpathTokens.messageGap) {
                    ForEach(Array(messages.enumerated()), id: \.element.id) { index, message in
                        VStack(spacing: StarpathTokens.spacingXS) {
                            TimestampSeparator(
                                current: message.timestamp,
                                previous: index > 0 ? messages[index - 1].timestamp : nil
                            )

                            MessageBubble(message: message)
                        }
                        .id(message.id)
                    }

                    // 流式指示器
                    if isStreaming, let last = messages.last, last.role == .assistant, last.textContent.isEmpty {
                        HStack(spacing: StarpathTokens.spacingXS) {
                            ProgressView()
                                .scaleEffect(0.7)
                            Text("...")
                                .starpathSerif()
                        }
                        .padding(.leading, StarpathTokens.spacingMD)
                    }
                }
                .padding(.horizontal, StarpathTokens.spacingMD)
                .padding(.top, StarpathTokens.spacingMD)
                .padding(.bottom, StarpathTokens.spacingXL * 2 + StarpathTokens.spacingMD)
            }
            .onChange(of: messages.count) {
                if let lastID = messages.last?.id {
                    withAnimation(.easeOut(duration: 0.2)) {
                        proxy.scrollTo(lastID, anchor: .bottom)
                    }
                }
            }
            .onChange(of: messages.last?.textContent) {
                let now = Date()
                guard now.timeIntervalSince(lastScrollDate) > 0.15 else { return }
                lastScrollDate = now
                if let lastID = messages.last?.id {
                    proxy.scrollTo(lastID, anchor: .bottom)
                }
            }
        }
    }

}

// MARK: - Message Bubble

private struct MessageBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 60) }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: StarpathTokens.spacingXS) {
                // 思路卡片（仅 assistant 消息）
                if message.role == .assistant, let strategy = message.thinkingStrategy {
                    ThinkingCard(strategy: strategy, observations: message.thinkingObservations ?? [], actions: message.thinkingActions ?? [])
                }

                // 图片附件
                if let imageData = message.imageData, let uiImage = UIImage(data: imageData) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFit()
                        .frame(maxWidth: 200, maxHeight: 200)
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                }

                // 文本
                if !message.textContent.isEmpty {
                    MessageContentView(
                        text: message.textContent,
                        role: message.role
                    )
                }
            }

            if message.role == .assistant { Spacer(minLength: 60) }
        }
    }
}

// MARK: - Message Content View
//
// 消息文本渲染组件。根据角色选择排版样式，统一处理 Markdown。
//   - Assistant: Serif 字体 + inline Markdown（bold/italic/code/链接/删除线）
//   - User: Sans 字体，纯文本（用户输入不含 Markdown）
//
// 使用 Apple AttributedString(markdown:) 解析 inline Markdown，
// interpretedSyntax = .inlineOnlyPreservingWhitespace 保留换行但不解析块级元素。

private struct MessageContentView: View {
    let text: String
    let role: MessageRole

    var body: some View {
        switch role {
        case .assistant:
            Text(renderedMarkdown)
                .starpathSerif()
        case .user:
            Text(text)
                .starpathSans()
                .padding(.horizontal, StarpathTokens.spacingSM + StarpathTokens.spacingXS)
                .padding(.vertical, StarpathTokens.spacingSM)
                .background(StarpathTokens.obsidian05)
                .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    private var renderedMarkdown: AttributedString {
        guard let attributed = try? AttributedString(
            markdown: text,
            options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)
        ) else {
            return AttributedString(text)
        }
        return attributed
    }
}
