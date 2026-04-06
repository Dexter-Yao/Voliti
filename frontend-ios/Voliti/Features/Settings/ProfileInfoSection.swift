// ABOUTME: Settings 页"我的信息"区域，只读展示 Coach 已掌握的 profile 信息
// ABOUTME: 数据来源为 LangGraph Store /voliti/user/profile/context

import SwiftUI

struct ProfileInfoSection: View {
    let profileItems: [(key: String, value: String)]
    let isLoading: Bool

    var body: some View {
        if isLoading {
            ForEach(0..<3, id: \.self) { _ in
                HStack {
                    Text("加载中")
                        .starpathMono(size: StarpathTokens.fontSizeXS)
                    Spacer()
                    Text("...")
                        .starpathSerif()
                }
                .redacted(reason: .placeholder)
            }
        } else if profileItems.isEmpty {
            Text("与 Coach 对话后，信息将在此展示")
                .starpathSans()
                .foregroundStyle(StarpathTokens.obsidian40)
        } else {
            ForEach(profileItems, id: \.key) { item in
                HStack(alignment: .top) {
                    Text(Self.labelFor(item.key))
                        .starpathMono(size: StarpathTokens.fontSizeXS)
                        .foregroundStyle(StarpathTokens.obsidian40)
                        .frame(width: 80, alignment: .leading)
                    Spacer()
                    Text(item.value)
                        .starpathSerif()
                        .multilineTextAlignment(.trailing)
                }
            }
        }
    }

    // MARK: - Label Mapping
    // ABOUTME: 新增 model 字段时同步更新此映射

    static let keyLabels: [String: String] = [
        "name": "称呼",
        "goal": "目标",
        "current_weight": "当前体重",
        "target_weight": "目标体重",
        "height": "身高",
        "age": "年龄",
        "lifestyle": "生活方式",
        "constraints": "约束条件",
        "motivation": "动力来源",
    ]

    static func labelFor(_ key: String) -> String {
        keyLabels[key] ?? key
    }
}
