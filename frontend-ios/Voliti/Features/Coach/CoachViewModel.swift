// ABOUTME: Coach 对话页 ViewModel，管理流式消息和 A2UI 中断
// ABOUTME: 管理 SSE 流生命周期，确保 UI 状态与后端中断协议一致

import Foundation
import SwiftUI
import SwiftData
import Observation
import os

private let logger = Logger(subsystem: "com.voliti", category: "CoachViewModel")

/// Coach 的思路块，展示观察和策略选择
struct ThinkingBlock {
    let strategy: String
    let observations: [String]
}

/// 通知点击携带的意图类型
enum NotificationIntent {
    case checkin
    case review
}

@MainActor
@Observable
final class CoachViewModel {
    var messages: [ChatMessage] = []
    var isStreaming = false
    var errorMessage: String?
    var activeInterrupt: A2UIPayload?
    var suggestedReplies: [String] = []
    var thinkingBlocks: [String: ThinkingBlock] = [:]
    /// 全局控制思路卡片默认展开/折叠。预留迁移到统一配置中心。
    var thinkingDefaultExpanded: Bool = true

    private let api = LangGraphAPI()
    private var modelContext: ModelContext?
    private var streamTask: Task<Void, Never>?

    @ObservationIgnored
    @AppStorage("lastCheckinDate") private var lastCheckinDate: String = ""

    @ObservationIgnored
    @AppStorage("onboardingComplete") var onboardingComplete = false

    func configure(modelContext: ModelContext) {
        self.modelContext = modelContext
        loadMessages()
    }

    // MARK: - Daily Check-in

    /// 检查今天是否为首次打开，如果是且已完成 Onboarding，则发送系统触发消息启动 Check-in
    func triggerDailyCheckinIfNeeded() {
        guard onboardingComplete else { return }
        guard !isStreaming else { return }

        let today = Self.todayString()
        guard lastCheckinDate != today else { return }

        lastCheckinDate = today
        sendSystemTrigger("[daily_checkin]")
    }

    /// 通知点击后触发对应流程
    func triggerFromNotification(_ intent: NotificationIntent) {
        guard onboardingComplete else { return }
        guard !isStreaming else { return }

        switch intent {
        case .checkin:
            lastCheckinDate = Self.todayString()
            sendSystemTrigger("[daily_checkin]")
        case .review:
            sendSystemTrigger("[daily_review]")
        }
    }

    private static func todayString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }

    // MARK: - System Trigger

    /// 向后端发送系统触发消息，不创建本地 ChatMessage，不在 UI 显示
    private func sendSystemTrigger(_ tag: String) {
        guard !isStreaming else { return }
        suggestedReplies = []

        isStreaming = true
        errorMessage = nil

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let threadID = try await api.ensureThread()

                let assistantMessage = ChatMessage(
                    role: .assistant,
                    textContent: "",
                    threadID: threadID
                )

                await MainActor.run {
                    self.messages.append(assistantMessage)
                }

                let stream = try api.streamRun(
                    threadID: threadID,
                    message: tag,
                    imageData: nil
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

    // MARK: - Send Message

    func sendMessage(_ text: String, imageData: Data? = nil) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        guard !isStreaming else { return }
        suggestedReplies = []

        isStreaming = true
        errorMessage = nil

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let threadID = try await api.ensureThread()

                let userMessage = ChatMessage(
                    role: .user,
                    textContent: text,
                    imageData: imageData,
                    threadID: threadID
                )
                let assistantMessage = ChatMessage(
                    role: .assistant,
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
        guard let payload = activeInterrupt else { return }
        persistInterventionCardIfAccepted(payload: payload, data: data)
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
            role: .assistant,
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
            let (afterThinking, thinkingBlock) = Self.extractCoachThinking(from: fullContent)
            let (cleaned, replies) = Self.extractSuggestedReplies(from: afterThinking)
            assistantMessage.textContent = cleaned
            if let block = thinkingBlock {
                self.thinkingBlocks[assistantMessage.id] = block
            }
            self.suggestedReplies = replies
            self.modelContext?.insert(assistantMessage)
            self.isStreaming = false
        }
    }

    // MARK: - Coach Thinking Parsing

    /// 从 Assistant 消息中提取 coach_thinking 标记并返回思路块和剩余文本
    static func extractCoachThinking(from content: String) -> (String, ThinkingBlock?) {
        let pattern = "```json:coach_thinking\\n(\\{.*?\\})\\n```"
        guard let regex = try? NSRegularExpression(pattern: pattern, options: .dotMatchesLineSeparators),
              let match = regex.firstMatch(in: content, range: NSRange(content.startIndex..., in: content)),
              let jsonRange = Range(match.range(at: 1), in: content) else {
            return (content, nil)
        }

        let jsonString = String(content[jsonRange])
        guard let data = jsonString.data(using: .utf8),
              let dict = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let strategy = dict["strategy"] as? String else {
            return (content, nil)
        }

        let observations = dict["observations"] as? [String] ?? []
        let block = ThinkingBlock(strategy: strategy, observations: observations)

        let fullMatchRange = Range(match.range, in: content)!
        var cleaned = content
        cleaned.removeSubrange(fullMatchRange)
        cleaned = cleaned.trimmingCharacters(in: .whitespacesAndNewlines)

        return (cleaned, block)
    }

    // MARK: - Suggested Replies Parsing

    /// 从 Assistant 消息中提取 suggested_replies 标记并返回清理后的文本和建议列表
    static func extractSuggestedReplies(from content: String) -> (String, [String]) {
        let pattern = "```json:suggested_replies\\n(\\[.*?\\])\\n```"
        guard let regex = try? NSRegularExpression(pattern: pattern, options: .dotMatchesLineSeparators),
              let match = regex.firstMatch(in: content, range: NSRange(content.startIndex..., in: content)),
              let jsonRange = Range(match.range(at: 1), in: content) else {
            return (content, [])
        }

        let jsonString = String(content[jsonRange])
        guard let data = jsonString.data(using: .utf8),
              let replies = try? JSONDecoder().decode([String].self, from: data) else {
            return (content, [])
        }

        let fullMatchRange = Range(match.range, in: content)!
        var cleaned = content
        cleaned.removeSubrange(fullMatchRange)
        cleaned = cleaned.trimmingCharacters(in: .whitespacesAndNewlines)

        return (cleaned, replies)
    }

    // MARK: - Intervention Card Persistence

    /// 用户 accept 体验式干预时，从 payload 提取图片和文案，持久化到 SwiftData
    private func persistInterventionCardIfAccepted(payload: A2UIPayload, data: [String: Any]) {
        guard let decision = data["decision"] as? String, decision == "accept" else { return }

        var cardImageData: Data?
        var caption = ""
        var purpose = ""

        for component in payload.components {
            switch component {
            case .image(let img):
                if img.src.hasPrefix("data:") {
                    cardImageData = Data.fromDataURL(img.src)
                }
                purpose = img.alt
            case .text(let txt):
                caption = txt.content
            default:
                break
            }
        }

        guard cardImageData != nil || !caption.isEmpty else { return }

        let card = InterventionCard(
            imageData: cardImageData,
            caption: caption,
            purpose: purpose
        )
        modelContext?.insert(card)

        if !onboardingComplete {
            onboardingComplete = true
        }
    }

    // MARK: - Load from SwiftData

    private func loadMessages() {
        guard let modelContext else { return }
        let currentThreadID = APIConfiguration.threadID
        var descriptor = FetchDescriptor<ChatMessage>(
            predicate: currentThreadID.map { id in
                #Predicate<ChatMessage> { $0.threadID == id }
            },
            sortBy: [SortDescriptor(\.timestamp, order: .reverse)]
        )
        descriptor.fetchLimit = 100
        do {
            let saved = try modelContext.fetch(descriptor)
            messages = saved.reversed()
        } catch {
            logger.error("Failed to load messages: \(error.localizedDescription)")
        }
    }
}

// MARK: - Data URL Decoder

extension Data {
    /// 从 data URL（data:image/...;base64,...）解码图片数据
    static func fromDataURL(_ string: String) -> Data? {
        guard let commaIndex = string.firstIndex(of: ",") else { return nil }
        let base64 = String(string[string.index(after: commaIndex)...])
        return Data(base64Encoded: base64)
    }
}
