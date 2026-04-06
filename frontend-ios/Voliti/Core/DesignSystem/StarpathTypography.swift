// ABOUTME: Starpath Protocol v2 排版 ViewModifier，提供三层字体样式
// ABOUTME: serif（叙事层 LXGW WenKai）、sans（界面层 DM Sans）、mono（信号层 JetBrains Mono）

import SwiftUI

// MARK: - Serif（叙事层）

struct StarpathSerifModifier: ViewModifier {
    var size: CGFloat = StarpathTokens.fontSizeBase

    func body(content: Content) -> some View {
        content
            .font(.custom("LXGWWenKai-Regular", size: size))
            .foregroundStyle(StarpathTokens.obsidian)
            .lineSpacing(size * (StarpathTokens.lineHeightBody - 1))
    }
}

// MARK: - Sans（界面层）

struct StarpathSansModifier: ViewModifier {
    var size: CGFloat = StarpathTokens.fontSizeSM

    func body(content: Content) -> some View {
        content
            .font(.custom("DMSans-Regular", size: size))
            .foregroundStyle(StarpathTokens.obsidian)
    }
}

// MARK: - Mono（信号层）

struct StarpathMonoModifier: ViewModifier {
    var size: CGFloat = StarpathTokens.fontSizeXS
    var uppercase: Bool = true

    func body(content: Content) -> some View {
        content
            .font(.custom("JetBrainsMono-Regular", size: size))
            .foregroundStyle(StarpathTokens.obsidian40)
            .textCase(uppercase ? .uppercase : nil)
            .tracking(uppercase ? 2 : 0)
    }
}

// MARK: - View Extensions

extension View {
    /// Coach 消息、Journal 叙事文本
    func starpathSerif(size: CGFloat = StarpathTokens.fontSizeBase) -> some View {
        modifier(StarpathSerifModifier(size: size))
    }

    /// 用户消息、按钮、输入框
    func starpathSans(size: CGFloat = StarpathTokens.fontSizeSM) -> some View {
        modifier(StarpathSansModifier(size: size))
    }

    /// 时间戳、标签、数据指标
    func starpathMono(size: CGFloat = StarpathTokens.fontSizeXS, uppercase: Bool = true) -> some View {
        modifier(StarpathMonoModifier(size: size, uppercase: uppercase))
    }
}
