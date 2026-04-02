// ABOUTME: 本地通知服务，管理权限请求和每日教练提醒调度
// ABOUTME: 支持晨间 Check-in 和晚间复盘两类定时提醒，通过 DeepLink 区分意图

import UserNotifications
import Observation
import os

private let logger = Logger(subsystem: "com.voliti", category: "NotificationService")

@MainActor
@Observable
final class NotificationService: NSObject {

    enum NotificationID {
        static let morningCheckin = "voliti.morning.checkin"
        static let eveningReview = "voliti.evening.review"
    }

    enum DeepLink: Equatable {
        case checkin
        case review
    }

    private(set) var isAuthorized = false
    var pendingDeepLink: DeepLink?

    private let center = UNUserNotificationCenter.current()

    override init() {
        super.init()
        center.delegate = self
    }

    // MARK: - Permission

    func requestPermissionAndSchedule() async {
        do {
            let granted = try await center.requestAuthorization(
                options: [.alert, .sound, .badge]
            )
            isAuthorized = granted
            if granted {
                await scheduleDefaultReminders()
            }
            logger.info("Notification permission: \(granted)")
        } catch {
            logger.error("Notification permission error: \(error.localizedDescription)")
        }
    }

    func checkCurrentStatus() async {
        let settings = await center.notificationSettings()
        isAuthorized = settings.authorizationStatus == .authorized
    }

    // MARK: - Schedule

    func scheduleDefaultReminders() async {
        await scheduleMorningCheckin(hour: 8, minute: 0)
        await scheduleEveningReview(hour: 21, minute: 0)
    }

    func scheduleMorningCheckin(hour: Int, minute: Int) async {
        var dateComponents = DateComponents()
        dateComponents.hour = hour
        dateComponents.minute = minute

        let trigger = UNCalendarNotificationTrigger(
            dateMatching: dateComponents,
            repeats: true
        )

        let content = UNMutableNotificationContent()
        content.title = "Voliti"
        content.body = "新的一天。先感知一下自己的状态。"
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: NotificationID.morningCheckin,
            content: content,
            trigger: trigger
        )

        do {
            try await center.add(request)
            logger.info("Morning checkin scheduled at \(hour):\(minute)")
        } catch {
            logger.error("Morning checkin schedule failed: \(error.localizedDescription)")
        }
    }

    func scheduleEveningReview(hour: Int, minute: Int) async {
        var dateComponents = DateComponents()
        dateComponents.hour = hour
        dateComponents.minute = minute

        let trigger = UNCalendarNotificationTrigger(
            dateMatching: dateComponents,
            repeats: true
        )

        let content = UNMutableNotificationContent()
        content.title = "Voliti"
        content.body = "今天结束了。回顾一下。"
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: NotificationID.eveningReview,
            content: content,
            trigger: trigger
        )

        do {
            try await center.add(request)
            logger.info("Evening review scheduled at \(hour):\(minute)")
        } catch {
            logger.error("Evening review schedule failed: \(error.localizedDescription)")
        }
    }

    func cancelAll() {
        center.removeAllPendingNotificationRequests()
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationService: UNUserNotificationCenterDelegate {
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        [.banner, .sound]
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        let identifier = response.notification.request.identifier
        let link: DeepLink = (identifier == NotificationID.eveningReview) ? .review : .checkin

        await MainActor.run {
            pendingDeepLink = link
        }
    }
}
