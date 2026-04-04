// ABOUTME: 对话消息列表，Coach 左对齐 Serif / 用户右对齐 Sans
// ABOUTME: 无气泡背景，间隔 > 30 分钟时显示时间戳

import SwiftUI

struct MessageList: View {
    let messages: [ChatMessage]
    let isStreaming: Bool
    var thinkingBlocks: [String: ThinkingBlock] = [:]
    var thinkingDefaultExpanded: Bool = true

    @State private var lastScrollDate = Date.distantPast

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: StarpathTokens.messageGap) {
                    ForEach(Array(messages.enumerated()), id: \.element.id) { index, message in
                        VStack(spacing: StarpathTokens.spacingXS) {
                            // 时间戳（间隔 > 30 分钟时显示）
                            if shouldShowTimestamp(at: index) {
                                Text(message.timestamp, style: .time)
                                    .starpathMono()
                                    .frame(maxWidth: .infinity)
                                    .padding(.top, StarpathTokens.spacingSM)
                            }

                            // 消息内容
                            MessageBubble(
                                message: message,
                                thinkingBlock: thinkingBlocks[message.id],
                                thinkingDefaultExpanded: thinkingDefaultExpanded
                            )
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

    private func shouldShowTimestamp(at index: Int) -> Bool {
        guard index > 0 else { return true }
        let current = messages[index].timestamp
        let previous = messages[index - 1].timestamp
        return current.timeIntervalSince(previous) > 1800 // 30 分钟
    }
}

// MARK: - Message Bubble

private struct MessageBubble: View {
    let message: ChatMessage
    var thinkingBlock: ThinkingBlock?
    var thinkingDefaultExpanded: Bool = true

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 60) }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: StarpathTokens.spacingXS) {
                // 思路卡片（仅 assistant 消息）
                if message.role == .assistant, let block = thinkingBlock {
                    ThinkingCard(block: block, defaultExpanded: thinkingDefaultExpanded)
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
                    if message.role == .assistant {
                        Text(message.textContent)
                            .starpathSerif()
                    } else {
                        Text(message.textContent)
                            .starpathSans()
                    }
                }
            }

            if message.role == .assistant { Spacer(minLength: 60) }
        }
    }
}
