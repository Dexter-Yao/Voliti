// ABOUTME: Coach 对话页 ViewModel，管理流式消息和 A2UI 中断
// ABOUTME: 管理 SSE 流生命周期，确保 UI 状态与后端中断协议一致

import Foundation
import SwiftUI
import SwiftData
import Observation
import os

private let logger = Logger(subsystem: "com.voliti", category: "CoachViewModel")

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

    private let api = LangGraphAPI()
    private var modelContext: ModelContext?
    private var streamTask: Task<Void, Never>?
    private var syncService: StoreSyncService?
    private var sessionMode: String = "coaching"

    private func trace(_ message: String) {
#if DEBUG
        print("[CoachViewModel] \(message)")
#endif
    }

    @ObservationIgnored
    @AppStorage("lastCheckinDate") private var lastCheckinDate: String = ""

    @ObservationIgnored
    @AppStorage("onboardingComplete") var onboardingComplete = false

    func configure(modelContext: ModelContext, sessionMode: String = "coaching") {
        self.modelContext = modelContext
        self.sessionMode = sessionMode
        self.syncService = StoreSyncService(modelContext: modelContext)
        loadMessages()
    }

    /// 根据 sessionMode 确保正确的 thread
    private func ensureCorrectThread() async throws -> String {
        if sessionMode == "onboarding" {
            return try await api.ensureOnboardingThread()
        }
        return try await api.ensureThread()
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

    private static let dateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    private static func todayString() -> String {
        dateFormatter.string(from: Date())
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
            var assistantMessage: ChatMessage?
            do {
                let threadID = try await ensureCorrectThread()

                let msg = ChatMessage(
                    role: .assistant,
                    textContent: "",
                    threadID: threadID
                )
                assistantMessage = msg

                await MainActor.run {
                    self.messages.append(msg)
                }

                let stream = try api.streamRun(
                    threadID: threadID,
                    message: tag,
                    imageData: nil,
                    sessionMode: self.sessionMode
                )

                await processStream(stream, assistantMessage: msg)
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isStreaming = false
                    if let msg = assistantMessage, msg.textContent.isEmpty {
                        self.messages.removeLast()
                    }
                }
            }
        }
    }

    // MARK: - Send Message

    func sendMessage(_ text: String, imageData: Data? = nil) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        guard !isStreaming else { return }
        suggestedReplies = []

        trace("sendMessage start, textCount=\(text.count), hasImage=\(imageData != nil)")
        isStreaming = true
        errorMessage = nil

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let threadID = try await ensureCorrectThread()
                trace("ensureThread ok, threadID=\(threadID), mode=\(self.sessionMode)")

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

                // Onboarding 首条用户消息：prepend 硬编码问候语，让 LLM 看到完整对话历史
                let priorGreeting: String? = {
                    guard self.sessionMode == "onboarding" else { return nil }
                    let userCount = self.messages.lazy.filter({ $0.role == .user }).prefix(2).count
                    return userCount == 1 ? OnboardingGreeting.text : nil
                }()

                let stream = try api.streamRun(
                    threadID: threadID,
                    message: text,
                    imageData: imageData,
                    sessionMode: self.sessionMode,
                    priorAssistantMessage: priorGreeting
                )
                trace("streamRun created, entering processStream, prependedGreeting=\(priorGreeting != nil)")

                await processStream(stream, assistantMessage: assistantMessage)
                trace("processStream returned")
            } catch {
                trace("sendMessage failed: \(error.localizedDescription)")
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
        let threadID: String? = sessionMode == "onboarding"
            ? APIConfiguration.onboardingThreadID
            : APIConfiguration.threadID
        guard let threadID else { return }

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
        var eventCount = 0

        trace("processStream started")
        logger.info("processStream: started")

        for await event in stream {
            if Task.isCancelled { break }
            eventCount += 1

            switch event {
            case .token(let content):
                guard !content.isEmpty else { break }
                trace("event #\(eventCount): token \(content.count) chars")
                fullContent = content
                let stripped = Self.stripFencedBlocks(from: fullContent)
                logger.debug("processStream: token \(eventCount), fullContent=\(fullContent.count) chars, stripped=\(stripped.count) chars")
                await MainActor.run {
                    assistantMessage.textContent = stripped
                }

            case .message(_, let content):
                guard !content.isEmpty else { break }
                trace("event #\(eventCount): message \(content.count) chars")
                fullContent = content
                let stripped = Self.stripFencedBlocks(from: fullContent)
                logger.info("processStream: message \(eventCount), fullContent=\(fullContent.count) chars, stripped=\(stripped.count) chars")
                await MainActor.run {
                    assistantMessage.textContent = stripped
                }

            case .interrupt(let data):
                trace("event #\(eventCount): interrupt \(data.count) bytes")
                logger.info("processStream: interrupt at event \(eventCount), fullContent=\(fullContent.count) chars, data=\(data.count) bytes")
                if let payload = try? JSONDecoder().decode(A2UIPayload.self, from: data) {
                    logger.info("processStream: A2UI decoded, \(payload.components.count) components")
                    await MainActor.run {
                        if !fullContent.isEmpty {
                            assistantMessage.textContent = Self.stripFencedBlocks(from: fullContent)
                            self.modelContext?.insert(assistantMessage)
                        }
                        self.activeInterrupt = payload
                        self.isStreaming = false
                    }
                    return
                } else {
                    trace("interrupt decode failed")
                    logger.error("processStream: A2UI decode FAILED")
                }

            case .done:
                trace("event #\(eventCount): done")
                logger.info("processStream: done at event \(eventCount)")
                break

            case .error(let error):
                trace("event #\(eventCount): error \(error.localizedDescription)")
                logger.error("processStream: error at event \(eventCount): \(error.localizedDescription)")
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                }
            }
        }

        trace("processStream loop ended, events=\(eventCount), fullContentChars=\(fullContent.count)")
        logger.info("processStream: loop ended after \(eventCount) events, fullContent=\(fullContent.count) chars")

        await MainActor.run {
            let (afterThinking, thinking) = Self.extractCoachThinking(from: fullContent)
            let (cleaned, replies) = Self.extractSuggestedReplies(from: afterThinking)
            assistantMessage.textContent = cleaned
            assistantMessage.thinkingStrategy = thinking?.strategy
            assistantMessage.thinkingObservations = thinking?.observations
            assistantMessage.thinkingActions = thinking?.actions
            self.suggestedReplies = replies
            self.modelContext?.insert(assistantMessage)
            self.isStreaming = false
            Task { [weak self] in
                await self?.syncService?.syncAll()
                if let self, !self.onboardingComplete {
                    let storeComplete = await self.syncService?.checkOnboardingComplete() ?? false
                    if storeComplete {
                        await MainActor.run { self.onboardingComplete = true }
                    } else if self.sessionMode == "onboarding" {
                        // InMemoryStore 重启后丢失数据时的降级判断：
                        // 统计非空 assistant 消息数，避免用户卡在 Onboarding fullScreenCover
                        let assistantCount = self.messages.lazy
                            .filter { $0.role == .assistant && !$0.textContent.isEmpty }
                            .prefix(3).count
                        if assistantCount >= 3 {
                            await MainActor.run { self.onboardingComplete = true }
                        }
                    }
                }
            }
            self.trace("processStream finalized, cleanedChars=\(cleaned.count), replies=\(replies.count)")
            logger.info("processStream: final text=\(cleaned.count) chars, replies=\(replies.count)")
        }
    }

    // MARK: - Content Sanitization Pipeline
    //
    // Coach 消息从 SSE 流到屏幕需要剥离所有内部数据，只保留用户可见文本。
    // 需要清洗的内容类型：
    //   1. Fenced JSON blocks — coach_thinking / suggested_replies（由 LLM 按约定输出）
    //   2. Tool output artifacts — write_file/read_file 返回的文件路径（LLM 偶尔回显）
    // 每种模式用独立 regex，按顺序应用。新增模式在此处添加。

    private static let sanitizationPatterns: [(NSRegularExpression, String)] = [
        // Fenced JSON blocks（含未闭合的流式状态）
        (try! NSRegularExpression(
            pattern: "```json:(?:coach_thinking|suggested_replies)\\n[\\s\\S]*?(?:```|$)"
        ), "fenced_block"),
        // Tool output: Python 风格文件路径数组 ['/user/...', '/user/...']
        (try! NSRegularExpression(
            pattern: "\\['/user/[^\\]]*\\]"
        ), "tool_output"),
    ]

    /// 流式文本内容清洗：剥离所有内部数据，只保留用户可见文本
    static func stripFencedBlocks(from content: String) -> String {
        var text = content
        for (pattern, _) in sanitizationPatterns {
            let range = NSRange(text.startIndex..., in: text)
            text = pattern.stringByReplacingMatches(in: text, range: range, withTemplate: "")
        }
        text = text.trimmingCharacters(in: .whitespacesAndNewlines)
        // 流式阶段 fenced block 正在逐字构建时，regex 还匹配不到完整 tag，
        // 但剩余文本以 ``` 开头说明是 partial opening，不应展示给用户
        if text.hasPrefix("```") { return "" }
        return text
    }

    // MARK: - Fenced JSON Block Extraction

    private static let thinkingRegex = try! NSRegularExpression(
        pattern: "```json:coach_thinking\\n(\\{.*?\\})\\n```",
        options: .dotMatchesLineSeparators
    )

    private static let repliesRegex = try! NSRegularExpression(
        pattern: "```json:suggested_replies\\n(\\[.*?\\])\\n```",
        options: .dotMatchesLineSeparators
    )

    /// 用指定 regex 从文本中提取 fenced JSON block，返回清理后文本和 JSON Data
    private static func extractTaggedJSON(from content: String, using regex: NSRegularExpression) -> (String, Data?) {
        guard let match = regex.firstMatch(in: content, range: NSRange(content.startIndex..., in: content)),
              let jsonRange = Range(match.range(at: 1), in: content),
              let jsonData = String(content[jsonRange]).data(using: .utf8) else {
            return (content, nil)
        }
        let fullMatchRange = Range(match.range, in: content)!
        var cleaned = content
        cleaned.removeSubrange(fullMatchRange)
        cleaned = cleaned.trimmingCharacters(in: .whitespacesAndNewlines)
        return (cleaned, jsonData)
    }

    private struct CoachThinkingPayload: Decodable {
        let strategy: String
        let observations: [String]?
        let actions: [String]?
    }

    /// 从 Assistant 消息中提取 coach_thinking 标记并返回策略、观察和操作
    static func extractCoachThinking(from content: String) -> (String, (strategy: String, observations: [String], actions: [String])?) {
        let (cleaned, data) = extractTaggedJSON(from: content, using: thinkingRegex)
        guard let data else { return (cleaned, nil) }
        guard let payload = try? JSONDecoder().decode(CoachThinkingPayload.self, from: data) else {
            logger.warning("coach_thinking block matched but JSON decode failed")
            return (cleaned, nil)
        }
        return (cleaned, (payload.strategy, payload.observations ?? [], payload.actions ?? []))
    }

    /// 从 Assistant 消息中提取 suggested_replies 标记并返回清理后的文本和建议列表
    static func extractSuggestedReplies(from content: String) -> (String, [String]) {
        let (cleaned, data) = extractTaggedJSON(from: content, using: repliesRegex)
        guard let data else { return (cleaned, []) }
        guard let replies = try? JSONDecoder().decode([String].self, from: data) else {
            logger.warning("suggested_replies block matched but JSON decode failed")
            return (cleaned, [])
        }
        return (cleaned, replies)
    }

    // MARK: - Intervention Card Persistence

    /// 用户 accept 体验式干预时，持久化卡片到 SwiftData。
    /// 先用 payload 中的缩略图创建卡片，然后异步从 Store 下载原图替换。
    private func persistInterventionCardIfAccepted(payload: A2UIPayload, data: [String: Any]) {
        guard let decision = data["decision"] as? String, decision == "accept" else { return }

        var thumbnailData: Data?
        var caption = ""
        var purpose = ""

        for component in payload.components {
            switch component {
            case .image(let img):
                if img.src.hasPrefix("data:") {
                    thumbnailData = Data.fromDataURL(img.src)
                }
                purpose = img.alt
            case .text(let txt):
                caption = txt.text
            default:
                break
            }
        }

        guard thumbnailData != nil || !caption.isEmpty else { return }

        let card = InterventionCard(
            imageData: thumbnailData,
            caption: caption,
            purpose: purpose
        )
        modelContext?.insert(card)

        let event = BehaviorEvent(
            timestamp: card.timestamp,
            kind: "moment",
            evidence: "",
            summary: caption
        )
        event.setRefs(["card_id": card.id])
        modelContext?.insert(event)

        if !onboardingComplete {
            onboardingComplete = true
        }

        // 异步从 Store 下载原图替换缩略图
        if let cardID = payload.cardID {
            Task { [weak self] in
                await self?.upgradeCardImage(card: card, cardID: cardID)
            }
        }
    }

    /// 从 LangGraph Store 下载原图，替换 InterventionCard 中的缩略图
    private func upgradeCardImage(card: InterventionCard, cardID: String) async {
        let namespace = ["voliti", "user", "interventions"]

        do {
            guard let value = try await api.fetchStoreItem(namespace: namespace, key: cardID),
                  let imageDataURL = value["imageData"] as? String,
                  let fullImage = Data.fromDataURL(imageDataURL) else {
                trace("upgradeCardImage: no image data for \(cardID)")
                return
            }

            await MainActor.run {
                card.imageData = fullImage
            }
            trace("upgradeCardImage: upgraded \(cardID), \(fullImage.count) bytes")
        } catch {
            trace("upgradeCardImage failed: \(error.localizedDescription)")
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
