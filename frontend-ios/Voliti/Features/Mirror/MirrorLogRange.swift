// ABOUTME: Mirror 日志区时间范围模型，定义本地 UI 选择、标题与日期区间解析
// ABOUTME: 仅服务日志区浏览，不承担全页状态或共享持久化职责

import Foundation

enum MirrorLogRangeError: Error, Equatable {
    case endBeforeStart
    case endAfterToday
}

enum MirrorLogRange: Equatable {
    case last7Days
    case last30Days
    case last90Days
    case chapter
    case custom(startDate: Date, endDate: Date)

    static let defaultValue: MirrorLogRange = .last30Days

    var storageValue: String {
        switch self {
        case .last7Days:
            "last7Days"
        case .last30Days:
            "last30Days"
        case .last90Days:
            "last90Days"
        case .chapter:
            "chapter"
        case let .custom(startDate, endDate):
            "\(Self.storageDateFormatter.string(from: startDate))|\(Self.storageDateFormatter.string(from: endDate))"
        }
    }

    func title(calendar: Calendar = .current) -> String {
        switch self {
        case .last7Days:
            "近7天"
        case .last30Days:
            "近30天"
        case .last90Days:
            "近90天"
        case .chapter:
            "本篇章"
        case let .custom(startDate, endDate):
            "\(Self.fullDateFormatter(calendar: calendar).string(from: startDate)) - \(Self.fullDateFormatter(calendar: calendar).string(from: endDate))"
        }
    }

    func interval(chapter: Chapter?, calendar: Calendar = .current, today: Date = .now) -> DateInterval? {
        let endDate = calendar.date(byAdding: .day, value: 1, to: calendar.startOfDay(for: today))!

        switch self {
        case .last7Days:
            let startDate = calendar.date(byAdding: .day, value: -6, to: calendar.startOfDay(for: today))!
            return DateInterval(start: startDate, end: endDate)
        case .last30Days:
            let startDate = calendar.date(byAdding: .day, value: -29, to: calendar.startOfDay(for: today))!
            return DateInterval(start: startDate, end: endDate)
        case .last90Days:
            let startDate = calendar.date(byAdding: .day, value: -89, to: calendar.startOfDay(for: today))!
            return DateInterval(start: startDate, end: endDate)
        case .chapter:
            guard let chapter else { return nil }
            return DateInterval(start: calendar.startOfDay(for: chapter.startDate), end: endDate)
        case let .custom(startDate, endDate):
            return DateInterval(
                start: calendar.startOfDay(for: startDate),
                end: calendar.date(byAdding: .day, value: 1, to: calendar.startOfDay(for: endDate))!
            )
        }
    }

    static func validatedCustom(
        startDate: Date,
        endDate: Date,
        today: Date = .now,
        calendar: Calendar = .current
    ) throws -> MirrorLogRange {
        let normalizedStart = calendar.startOfDay(for: startDate)
        let normalizedEnd = calendar.startOfDay(for: endDate)
        let normalizedToday = calendar.startOfDay(for: today)

        guard normalizedEnd >= normalizedStart else {
            throw MirrorLogRangeError.endBeforeStart
        }

        guard normalizedEnd <= normalizedToday else {
            throw MirrorLogRangeError.endAfterToday
        }

        return .custom(startDate: normalizedStart, endDate: normalizedEnd)
    }

    static func fromStorageValue(_ rawValue: String) -> MirrorLogRange? {
        switch rawValue {
        case "last7Days":
            return .last7Days
        case "last30Days":
            return .last30Days
        case "last90Days":
            return .last90Days
        case "chapter":
            return .chapter
        default:
            let parts = rawValue.split(separator: "|").map(String.init)
            guard parts.count == 2,
                  let startDate = storageDateFormatter.date(from: parts[0]),
                  let endDate = storageDateFormatter.date(from: parts[1]) else {
                return nil
            }
            return .custom(startDate: startDate, endDate: endDate)
        }
    }

    private static func fullDateFormatter(calendar: Calendar) -> DateFormatter {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.dateFormat = "yyyy.MM.dd"
        return formatter
    }

    private static let storageDateFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()
}

enum LogDisplayState: Equatable {
    case loading
    case ready
    case emptyInRange
    case emptyAfterFilter
    case failed
}
