// ABOUTME: Coach 对话页主视图，承载 MessageList + InputBar + FanOutPanel
// ABOUTME: A2UI 中断时以 sheet 形式弹出扇出面板

import SwiftUI
import SwiftData

struct CoachView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(NotificationService.self) private var notificationService
    @State private var viewModel = CoachViewModel()

    var body: some View {
        NavigationStack {
        ZStack(alignment: .bottom) {
            StarpathTokens.parchment
                .ignoresSafeArea()

            MessageList(
                messages: viewModel.messages,
                isStreaming: viewModel.isStreaming
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
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                NavigationLink {
                    SettingsView()
                } label: {
                    Image(systemName: "gearshape")
                        .font(.system(size: 14))
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
        }
        .onAppear {
            viewModel.configure(modelContext: modelContext)
            viewModel.triggerDailyCheckinIfNeeded()
        }
        .onChange(of: notificationService.pendingDeepLink) { _, newValue in
            guard let link = newValue else { return }
            notificationService.pendingDeepLink = nil
            let intent: NotificationIntent = (link == .review) ? .review : .checkin
            viewModel.triggerFromNotification(intent)
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
        .alert("连接错误", isPresented: showingError) {
            Button("确定") { viewModel.errorMessage = nil }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
        } // NavigationStack
    }

    private var showingError: Binding<Bool> {
        Binding(
            get: { viewModel.errorMessage != nil },
            set: { if !$0 { viewModel.errorMessage = nil } }
        )
    }
}
