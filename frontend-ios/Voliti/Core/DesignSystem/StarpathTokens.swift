// ABOUTME: Starpath Protocol 设计 tokens，定义颜色、字体、间距等视觉常量
// ABOUTME: 所有值精确映射 docs/design-system/design-tokens.json

import SwiftUI

enum StarpathTokens {

    // MARK: - 核心色彩

    /// 主文字、主按钮背景、强调元素 (#1A1816)
    static let obsidian = Color(red: 0.102, green: 0.094, blue: 0.086)

    /// 页面背景、面板背景、主按钮文字 (#F5F1EB)
    static let parchment = Color(red: 0.961, green: 0.945, blue: 0.922)

    /// Map 页暗色主题背景 (#2A2520)
    static let warmDark = Color(red: 0.165, green: 0.145, blue: 0.125)

    /// 系统级风险标记，禁止用于行为评判 (#8B3A3A)
    static let riskRed = Color(red: 0.545, green: 0.227, blue: 0.227)

    /// 对齐状态指示，低饱和冷绿灰 (#8A9A8A)
    static let aligned = Color(red: 0.541, green: 0.604, blue: 0.541)

    /// 对齐状态冷蓝变体，图片生成与 Map 卡片状态指示 (#8AACB8)
    static let alignedCool = Color(red: 0.541, green: 0.675, blue: 0.722)

    // MARK: - 透明度变体

    /// 细分割线、输入框边框、滑块轨道
    static let obsidian10 = obsidian.opacity(0.10)

    /// Journal 周分隔线
    static let obsidian15 = obsidian.opacity(0.15)

    /// 扇出面板顶部细线、Map 卡片边框
    static let obsidian20 = obsidian.opacity(0.20)

    /// 次要标签、时间戳、占位符文字
    static let obsidian40 = obsidian.opacity(0.40)

    // MARK: - 字号

    /// 等宽标签、时间戳、数据单位 (12px)
    static let fontSizeXS: CGFloat = 12

    /// 界面操作文字、按钮文案 (14px)
    static let fontSizeSM: CGFloat = 14

    /// 主要正文、Coach 消息 (16px)
    static let fontSizeBase: CGFloat = 16

    /// 扇出面板标题 (18px)
    static let fontSizeLG: CGFloat = 18

    /// Map 页身份宣言 (24px)
    static let fontSizeXL: CGFloat = 24

    // MARK: - 间距

    static let spacingXS: CGFloat = 4
    static let spacingSM: CGFloat = 8
    static let spacingMD: CGFloat = 16
    static let spacingLG: CGFloat = 24
    static let spacingXL: CGFloat = 32

    // MARK: - 行高

    static let lineHeightBody: CGFloat = 1.6

    // MARK: - 布局

    /// 消息间距
    static let messageGap: CGFloat = 16
}
