// ABOUTME: 聊天时间戳分隔组件，按消��间隔自���选择��示格式
// ABOUTME: 5 级规则：<5min 不显示 / 5-30min 时��� / 30min+ 上下午 / 跨天相对 / ≥7天完整日期

import SwiftUI

struct TimestampSeparator: View {
    let current: Date
    let previous: Date?

    var body: some View {
        if let text = formattedText {
            Text(text)
                .starpathMono(size: 11, uppercase: false)
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, StarpathTokens.spacingSM)
        }
    }

    private var formattedText: String? {
        guard let previous else {
            return dateSeparatorText(for: current)
        }

        let interval = current.timeIntervalSince(previous)

        // < 5 min: 不显示
        if abs(interval) < 300 { return nil }

        let calendar = Calendar.current
        let currentDay = calendar.startOfDay(for: current)
        let previousDay = calendar.startOfDay(for: previous)

        // 同一天
        if currentDay == previousDay {
            if abs(interval) < 1800 {
                // 5-30 min: 仅��间
                return shortTimeText(current)
            } else {
                // > 30 min: 上午/下午 + 时间
                return periodTimeText(current)
            }
        }

        // 跨天
        return dateSeparatorText(for: current)
    }

    private func dateSeparatorText(for date: Date) -> String {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let target = calendar.startOfDay(for: date)
        let dayDiff = calendar.dateComponents([.day], from: target, to: today).day ?? 0

        if dayDiff == 0 {
            return localizedToday
        } else if dayDiff == 1 {
            return "\(localizedYesterday) \(shortTimeText(date))"
        } else if dayDiff < 7 {
            return "\(weekdayText(date)) \(shortTimeText(date))"
        } else {
            return "\(fullDateText(date)) \(shortTimeText(date))"
        }
    }

    // MARK: - Formatters

    private func shortTimeText(_ date: Date) -> String {
        Self.shortTimeFormatter.string(from: date)
    }

    private func periodTimeText(_ date: Date) -> String {
        Self.periodTimeFormatter.string(from: date)
    }

    private func weekdayText(_ date: Date) -> String {
        Self.weekdayFormatter.string(from: date)
    }

    private func fullDateText(_ date: Date) -> String {
        Self.fullDateFormatter.string(from: date)
    }

    private var localizedToday: String {
        Locale.current.language.languageCode?.identifier == "zh" ? "今天" : "Today"
    }

    private var localizedYesterday: String {
        Locale.current.language.languageCode?.identifier == "zh" ? "昨天" : "Yesterday"
    }

    private static let shortTimeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm"
        return f
    }()

    private static let periodTimeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .none
        f.timeStyle = .short
        return f
    }()

    private static let weekdayFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "EEEE"
        return f
    }()

    private static let fullDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = DateFormatter.dateFormat(fromTemplate: "MMMd", options: 0, locale: .current)
        return f
    }()
}
