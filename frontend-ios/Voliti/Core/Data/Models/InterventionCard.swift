// ABOUTME: 教练干预卡片 SwiftData 模型
// ABOUTME: 存储 AI 生成图片（binary）、文案、干预类型和时间戳

import Foundation
import SwiftData

@Model
final class InterventionCard {
    var id: String
    @Attribute(.externalStorage) var imageData: Data?
    var caption: String
    var purpose: String
    var timestamp: Date

    init(
        id: String = UUID().uuidString,
        imageData: Data? = nil,
        caption: String,
        purpose: String,
        timestamp: Date = .now
    ) {
        self.id = id
        self.imageData = imageData
        self.caption = caption
        self.purpose = purpose
        self.timestamp = timestamp
    }
}
