// ABOUTME: 对话消息 SwiftData 模型
// ABOUTME: 映射 LangGraph 流式消息，支持文本和图片附件

import Foundation
import SwiftData

enum MessageRole: String, Codable {
    case user
    case assistant
}

@Model
final class ChatMessage {
    var id: String
    var role: MessageRole
    var textContent: String
    @Attribute(.externalStorage) var imageData: Data?
    var timestamp: Date
    var threadID: String
    var thinkingStrategy: String?
    var thinkingObservations: [String]?

    init(
        id: String = UUID().uuidString,
        role: MessageRole,
        textContent: String,
        imageData: Data? = nil,
        timestamp: Date = .now,
        threadID: String,
        thinkingStrategy: String? = nil,
        thinkingObservations: [String]? = nil
    ) {
        self.id = id
        self.role = role
        self.textContent = textContent
        self.imageData = imageData
        self.timestamp = timestamp
        self.threadID = threadID
        self.thinkingStrategy = thinkingStrategy
        self.thinkingObservations = thinkingObservations
    }
}
