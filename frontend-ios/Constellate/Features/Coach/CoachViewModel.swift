// ABOUTME: Coach 对话页 ViewModel，管理流式消息和 A2UI 中断
// ABOUTME: 映射 Web 版 ChatContainer.tsx 的核心逻辑

import Foundation
import SwiftData
import Observation

@Observable
final class CoachViewModel {
    var messages: [ChatMessage] = []
    var isStreaming = false
    var errorMessage: String?
    var activeInterrupt: A2UIPayload?

    private let api = LangGraphAPI()
    private var modelContext: ModelContext?
    private var streamTask: Task<Void, Never>?

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadMessages()
    }

    // MARK: - Send Message

    func sendMessage(_ text: String, imageData: Data? = nil) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        guard !isStreaming else { return }

        isStreaming = true
        errorMessage = nil

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let threadID = try await api.ensureThread()

                let userMessage = ChatMessage(
                    role: "user",
                    textContent: text,
                    imageData: imageData,
                    threadID: threadID
                )
                let assistantMessage = ChatMessage(
                    role: "assistant",
                    textContent: "",
                    threadID: threadID
                )

                await MainActor.run {
                    self.messages.append(userMessage)
                    self.modelContext?.insert(userMessage)
                    self.messages.append(assistantMessage)
                }

                let stream = try api.streamRun(
                    threadID: threadID,
                    message: text,
                    imageData: imageData
                )

                await processStream(stream, assistantMessage: assistantMessage)
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isStreaming = false
                }
            }
        }
    }

    // MARK: - A2UI Interrupt Handlers

    func submitA2UIResponse(_ data: [String: Any]) {
        guard activeInterrupt != nil else { return }
        activeInterrupt = nil
        resumeWithAction("submit", data: data)
    }

    func rejectA2UI() {
        guard activeInterrupt != nil else { return }
        activeInterrupt = nil
        resumeWithAction("reject")
    }

    func skipA2UI() {
        guard activeInterrupt != nil else { return }
        activeInterrupt = nil
        resumeWithAction("skip")
    }

    private func resumeWithAction(_ action: String, data: [String: Any] = [:]) {
        guard let threadID = APIConfiguration.threadID else { return }

        let assistantMessage = ChatMessage(
            role: "assistant",
            textContent: "",
            threadID: threadID
        )
        messages.append(assistantMessage)
        isStreaming = true

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let stream = try api.resumeInterrupt(
                    threadID: threadID,
                    action: action,
                    data: data
                )
                await processStream(stream, assistantMessage: assistantMessage)
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isStreaming = false
                    if assistantMessage.textContent.isEmpty {
                        self.messages.removeLast()
                    }
                }
            }
        }
    }

    // MARK: - Stream Processing

    private func processStream(_ stream: AsyncStream<SSEEvent>, assistantMessage: ChatMessage) async {
        var fullContent = ""

        for await event in stream {
            if Task.isCancelled { break }

            switch event {
            case .token(let content):
                fullContent = content
                await MainActor.run {
                    assistantMessage.textContent = fullContent
                }

            case .message(_, let content):
                fullContent = content
                await MainActor.run {
                    assistantMessage.textContent = fullContent
                }

            case .interrupt(let data):
                if let payload = try? JSONDecoder().decode(A2UIPayload.self, from: data) {
                    await MainActor.run {
                        self.activeInterrupt = payload
                        self.isStreaming = false
                    }
                    return
                }

            case .done:
                break

            case .error(let error):
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                }
            }
        }

        await MainActor.run {
            assistantMessage.textContent = fullContent
            self.modelContext?.insert(assistantMessage)
            self.isStreaming = false
        }
    }

    // MARK: - Cancel

    func cancelStream() {
        streamTask?.cancel()
        isStreaming = false
    }

    // MARK: - Load from SwiftData

    private func loadMessages() {
        guard let modelContext else { return }
        let descriptor = FetchDescriptor<ChatMessage>(
            sortBy: [SortDescriptor(\.timestamp)]
        )
        if let saved = try? modelContext.fetch(descriptor) {
            messages = saved
        }
    }
}
