// ABOUTME: 触觉反馈服务，遵循 Starpath "冷静、精准" 原则
// ABOUTME: light(滑块) / medium(提交) / success(卡片接受)，常规消息无触觉

import UIKit

enum HapticService {
    private static let lightGenerator = UIImpactFeedbackGenerator(style: .light)
    private static let mediumGenerator = UIImpactFeedbackGenerator(style: .medium)
    private static let notificationGenerator = UINotificationFeedbackGenerator()

    static func prepare() {
        lightGenerator.prepare()
        mediumGenerator.prepare()
        notificationGenerator.prepare()
    }

    /// A2UI 滑块值变化
    static func light() {
        lightGenerator.impactOccurred()
    }

    /// A2UI 提交
    static func medium() {
        mediumGenerator.impactOccurred()
    }

    /// 干预卡片被接受
    static func success() {
        notificationGenerator.notificationOccurred(.success)
    }
}
