// ABOUTME: Onboarding 问候语常量，客户端硬编码显示 + 发送给后端作为对话历史
// ABOUTME: 文案与 DESIGN.md Onboarding Step 1 保持一致

import Foundation

enum OnboardingGreeting {

    static let textZH = "你好。\n\n我是你的教练，将陪你走接下来这段旅程。\n\n怎么称呼你？"
    static let textEN = "Hi there.\n\nI'm your coach, and I'll be walking this next stretch of the road with you.\n\nWhat should I call you?"

    /// 根据用户语言偏好返回对应文本（app 生命周期内不变，启动时计算一次）
    static let text: String = {
        let lang = UserDefaults.standard.string(forKey: "preferredLanguage") ?? "system"
        if lang == "en" { return textEN }
        if lang == "zh" { return textZH }
        let systemLang = Locale.current.language.languageCode?.identifier
        return systemLang == "en" ? textEN : textZH
    }()
}
