// ABOUTME: Onboarding 全屏对话界面，Coach 发起对话
// ABOUTME: 两个视觉阶段：居中模式（Coach 独白）→ 对话模式（正常聊天）
// ABOUTME: isReEntry=true 时跳过 Step 1-2，直接进入对话模式（设置页"继续了解我"入口）

import SwiftUI
import SwiftData

struct OnboardingView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss
    @State private var viewModel = CoachViewModel()
    @State private var phase: OnboardingPhase = .welcome
    @State private var selectedReply: String?

    /// re-entry 模式跳过 Step 1-2，直接进入对话模式
    var isReEntry: Bool = false

    var body: some View {
        ZStack {
            StarpathTokens.onboardingWarm
                .ignoresSafeArea()
                .allowsHitTesting(false)

            // Copper 渐变呼吸线
            copperBreathingLine

            if isReEntry {
                // re-entry 直接进入对话模式
                conversationPhase
            } else {
                switch phase {
                case .welcome:
                    welcomePhase
                case .conversation:
                    conversationPhase
                }
            }

            // re-entry 时显示关闭按钮
            if isReEntry {
                VStack {
                    HStack {
                        Spacer()
                        Button { dismiss() } label: {
                            Image(systemName: "xmark")
                                .font(.system(size: 14))
                                .foregroundStyle(StarpathTokens.obsidian40)
                                .frame(width: 44, height: 44)
                        }
                        .accessibilityLabel("关闭")
                    }
                    .padding(.horizontal, StarpathTokens.spacingSM)
                    Spacer()
                }
            }
        }
        .onAppear {
            viewModel.configure(modelContext: modelContext, sessionMode: "onboarding")
            injectGreetingIfNeeded()
            // 上次 session 已有对话记录，跳过 welcome 居中阶段
            if !isReEntry && viewModel.messages.count > 1 && phase == .welcome {
                phase = .conversation
            }
        }
        .sheet(item: $viewModel.activeInterrupt) { payload in
            FanOutPanel(
                payload: payload,
                onSubmit: { data in
                    viewModel.submitA2UIResponse(data)
                },
                onReject: {
                    viewModel.rejectA2UI()
                },
                onSkip: {
                    viewModel.skipA2UI()
                }
            )
            .presentationDetents(payload.layout.detents)
            .presentationDragIndicator(.hidden)
            .presentationBackground(StarpathTokens.parchment.opacity(0.98))
        }
    }

    // MARK: - Welcome Phase (centered, Coach speaks first)

    private var welcomePhase: some View {
        GeometryReader { geometry in
        VStack(spacing: 0) {
            Spacer()
                .frame(minHeight: geometry.size.height * 0.3)

            // Coach 标识
            Text("VOLITI COACH")
                .font(.custom("JetBrainsMono-Regular", size: StarpathTokens.fontSizeXS))
                .foregroundStyle(StarpathTokens.copper)
                .tracking(2)
                .padding(.bottom, StarpathTokens.spacingLG)

            // Coach 欢迎消息
            if let firstMessage = viewModel.messages.first(where: { $0.role == .assistant }) {
                Text(firstMessage.textContent)
                    .starpathSerif(size: StarpathTokens.fontSizeLG)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, StarpathTokens.spacingXL)
                    .padding(.bottom, StarpathTokens.spacingXL)
            } else {
                // Coach 还没发消息，显示加载
                ProgressView()
                    .tint(StarpathTokens.obsidian40)
                    .padding(.bottom, StarpathTokens.spacingXL)
            }

            Spacer()

            // Quick Reply pills (vertical)
            if !viewModel.suggestedReplies.isEmpty {
                VStack(spacing: StarpathTokens.spacingSM) {
                    ForEach(viewModel.suggestedReplies, id: \.self) { reply in
                        Button {
                            selectReply(reply)
                        } label: {
                            Text(reply)
                                .starpathSans()
                                .foregroundStyle(StarpathTokens.obsidian)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, StarpathTokens.spacingSM + 2)
                                .background(
                                    Capsule()
                                        .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                                )
                        }
                    }
                }
                .padding(.horizontal, StarpathTokens.spacingXL)
                .padding(.bottom, StarpathTokens.spacingXL)
            }

            // 文字输入区（当最后一个 pill 是"让我想想"类触发时显示）
            if viewModel.suggestedReplies.isEmpty && viewModel.messages.count > 0 {
                InputBar(
                    onSend: { text, imageData in
                        viewModel.sendMessage(text, imageData: imageData)
                        transitionToConversation()
                    },
                    disabled: viewModel.isStreaming
                )
            }
        }
        }
    }

    // MARK: - Conversation Phase (normal chat, no Tab bar)

    private var conversationPhase: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                StarpathTokens.onboardingWarm
                    .ignoresSafeArea()

                MessageList(
                    messages: viewModel.messages,
                    isStreaming: viewModel.isStreaming,
                    hideThinking: true
                )

                VStack(spacing: 0) {
                    StarpathDivider()
                    InputBar(
                        onSend: { text, imageData in
                            viewModel.sendMessage(text, imageData: imageData)
                        },
                        disabled: viewModel.isStreaming,
                        suggestedReplies: viewModel.suggestedReplies,
                        onSuggestionTap: { reply in
                            viewModel.suggestedReplies = []
                            viewModel.sendMessage(reply, imageData: nil)
                        }
                    )
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(.hidden, for: .navigationBar)
        }
    }

    // MARK: - Greeting

    private func injectGreetingIfNeeded() {
        guard viewModel.messages.isEmpty else { return }
        let greeting = ChatMessage(
            role: .assistant,
            textContent: OnboardingGreeting.text,
            threadID: "onboarding"
        )
        viewModel.messages.append(greeting)
    }

    // MARK: - Actions

    private func selectReply(_ reply: String) {
        viewModel.suggestedReplies = []
        viewModel.sendMessage(reply, imageData: nil)
        transitionToConversation()
    }

    private func transitionToConversation() {
        withAnimation(.easeOut(duration: 0.3)) {
            phase = .conversation
        }
    }

    // MARK: - Copper Breathing Line

    private var copperBreathingLine: some View {
        CopperBreathingLine()
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .allowsHitTesting(false)
            .accessibilityHidden(true)
    }
}

// MARK: - Phase

private enum OnboardingPhase {
    case welcome
    case conversation
}

// MARK: - Copper Breathing Line

private struct CopperBreathingLine: View {
    @State private var opacity: Double = 0.1

    var body: some View {
        GeometryReader { geo in
            LinearGradient(
                colors: [.clear, StarpathTokens.copper, .clear],
                startPoint: .leading,
                endPoint: .trailing
            )
            .frame(width: geo.size.width * 0.6, height: 1)
            .frame(maxWidth: .infinity)
        }
        .frame(height: 1)
        .opacity(opacity)
        .onAppear {
            withAnimation(
                .easeInOut(duration: 5.0)
                .repeatForever(autoreverses: true)
            ) {
                opacity = 0.3
            }
        }
    }
}
