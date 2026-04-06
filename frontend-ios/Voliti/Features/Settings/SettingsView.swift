// ABOUTME: Settings 主页，Form + Section 分组，Starpath 零圆角风格
// ABOUTME: 包含 profile 展示、偏好设置、重置功能、账户占位

import SwiftUI
import SwiftData
import UserNotifications
import os

private let logger = Logger(subsystem: "com.voliti", category: "SettingsView")

struct SettingsView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @AppStorage("showThinkingExpanded") private var showThinkingExpanded = false
    @AppStorage("preferredLanguage") private var preferredLanguage = "system"
    @AppStorage("checkinReminderEnabled") private var checkinReminderEnabled = true
    @AppStorage("checkinReminderTime") private var checkinReminderTime: Double = 28800.0

    @State private var profileItems: [(key: String, value: String)] = []
    @State private var isLoadingProfile = true
    @State private var showResetConfirmation = false
    @State private var isResetting = false
    @State private var resetWarning: String?
    @State private var showOnboarding = false
    @State private var notificationDenied = false

    private let api = LangGraphAPI()

    var body: some View {
        ZStack {
            Form {
                profileSection
                preferencesSection
                accountSection
                dataSection
                aboutSection
            }
            .scrollContentBackground(.hidden)
            .background(StarpathTokens.parchment)
            .navigationBarTitleDisplayMode(.inline)

            if isResetting {
                resetOverlay
            }
        }
        .onAppear { loadProfile() }
        .confirmationDialog(
            "此操作将永久删除所有对话历史、行为记录和教练配置，无法恢复。",
            isPresented: $showResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("确认重置", role: .destructive) { performReset() }
        }
        .fullScreenCover(isPresented: $showOnboarding) {
            OnboardingView(isReEntry: true)
        }
    }

    // MARK: - Profile Section

    private var profileSection: some View {
        Section {
            ProfileInfoSection(
                profileItems: profileItems,
                isLoading: isLoadingProfile
            )

            Button {
                showOnboarding = true
            } label: {
                Text("继续了解我")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, StarpathTokens.spacingSM)
                    .background(
                        Capsule()
                            .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                    )
            }
            .buttonStyle(.plain)
            .listRowBackground(Color.clear)
        } header: {
            sectionHeader("我的信息")
        }
    }

    // MARK: - Preferences Section

    private var preferencesSection: some View {
        Section {
            Toggle(isOn: $showThinkingExpanded) {
                Text("思考过程默认展开")
                    .starpathSans()
            }

            Picker(selection: $preferredLanguage) {
                Text("跟随系统").tag("system")
                Text("中文").tag("zh")
                Text("English").tag("en")
            } label: {
                Text("语言")
                    .starpathSans()
            }

            Toggle(isOn: $checkinReminderEnabled) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("签到提醒")
                        .starpathSans()
                    if notificationDenied {
                        Button {
                            if let url = URL(string: UIApplication.openNotificationSettingsURLString) {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            Text("需要开启通知权限")
                                .font(.custom("DM Sans", size: 12))
                                .foregroundStyle(StarpathTokens.riskRed)
                        }
                    }
                }
            }
            .onChange(of: checkinReminderEnabled) { _, enabled in
                if enabled { requestNotificationPermission() }
                else { cancelNotification() }
            }

            if checkinReminderEnabled && !notificationDenied {
                DatePicker(
                    "提醒时间",
                    selection: reminderDateBinding,
                    displayedComponents: .hourAndMinute
                )
                .onChange(of: checkinReminderTime) { _, _ in
                    scheduleNotification()
                }
            }
        } header: {
            sectionHeader("显示与交互")
        }
    }

    // MARK: - Account Section

    private var accountSection: some View {
        Section {
            HStack {
                Text("登录 / 注册")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian20)
                Spacer()
                Text("即将推出")
                    .starpathMono(size: StarpathTokens.fontSizeXS)
                    .foregroundStyle(StarpathTokens.obsidian20)
            }
        } header: {
            sectionHeader("账户")
        }
    }

    // MARK: - Data Section

    private var dataSection: some View {
        Section {
            Button(role: .destructive) {
                showResetConfirmation = true
            } label: {
                Text("重置所有数据")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.riskRed)
            }

            if let resetWarning {
                Text(resetWarning)
                    .font(.custom("DM Sans", size: 12))
                    .foregroundStyle(StarpathTokens.riskRed)
            }

            HStack {
                Text("删除账户")
                    .starpathSans()
                    .foregroundStyle(StarpathTokens.obsidian20)
                Spacer()
                Text("即将推出")
                    .starpathMono(size: StarpathTokens.fontSizeXS)
                    .foregroundStyle(StarpathTokens.obsidian20)
            }
        } header: {
            sectionHeader("数据与隐私")
        }
    }

    // MARK: - About Section

    private var aboutSection: some View {
        Section {
            HStack {
                Text("版本")
                    .starpathSans()
                Spacer()
                Text(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0")
                    .starpathMono(size: StarpathTokens.fontSizeXS)
                    .foregroundStyle(StarpathTokens.obsidian40)
            }
        } header: {
            sectionHeader("关于")
        }
    }

    // MARK: - Reset Overlay

    private var resetOverlay: some View {
        StarpathTokens.parchment.opacity(0.9)
            .ignoresSafeArea()
            .overlay {
                VStack(spacing: StarpathTokens.spacingMD) {
                    ProgressView()
                        .tint(StarpathTokens.obsidian40)
                    Text("正在重置...")
                        .starpathSans()
                        .foregroundStyle(StarpathTokens.obsidian40)
                }
            }
    }

    // MARK: - Section Header

    private func sectionHeader(_ title: String) -> some View {
        Text(title.uppercased())
            .font(.custom("JetBrainsMono-Regular", size: StarpathTokens.fontSizeXS))
            .foregroundStyle(StarpathTokens.obsidian40)
            .tracking(2)
    }

    // MARK: - Profile Loading

    private func loadProfile() {
        Task {
            defer { isLoadingProfile = false }
            do {
                guard let value = try await api.fetchStoreItem(
                    namespace: ["voliti", "user", "profile"],
                    key: "context"
                ) else {
                    profileItems = []
                    return
                }

                // Store context 可能是结构化 dict 或 content 字符串
                if let content = value["content"] as? String {
                    profileItems = parseContentString(content)
                } else {
                    profileItems = value.compactMap { key, val in
                        let strVal = "\(val)"
                        guard !strVal.isEmpty, strVal != "<null>" else { return nil }
                        return (key: key, value: strVal)
                    }
                }
            } catch {
                logger.warning("Profile load failed: \(error.localizedDescription)")
                profileItems = []
            }
        }
    }

    private func parseContentString(_ content: String) -> [(key: String, value: String)] {
        content
            .components(separatedBy: "\n")
            .compactMap { line -> (key: String, value: String)? in
                let parts = line.split(separator: ":", maxSplits: 1)
                guard parts.count == 2 else { return nil }
                let key = parts[0].trimmingCharacters(in: .whitespaces)
                let value = parts[1].trimmingCharacters(in: .whitespaces)
                guard !value.isEmpty else { return nil }
                return (key: key, value: value)
            }
    }

    // MARK: - Reset

    private func performReset() {
        Task {
            isResetting = true
            let warning = await ResetService.resetAll(modelContext: modelContext)
            resetWarning = warning
            isResetting = false

            // dismiss + delay → ContentView 检测 onboardingComplete=false → fullScreenCover
            dismiss()
            try? await Task.sleep(for: .milliseconds(300))
            UserDefaults.standard.set(false, forKey: "onboardingComplete")
        }
    }

    // MARK: - Notification

    private func requestNotificationPermission() {
        Task {
            let center = UNUserNotificationCenter.current()
            do {
                let granted = try await center.requestAuthorization(options: [.alert, .sound])
                if granted {
                    notificationDenied = false
                    scheduleNotification()
                } else {
                    notificationDenied = true
                    checkinReminderEnabled = false
                }
            } catch {
                logger.warning("Notification permission error: \(error.localizedDescription)")
                notificationDenied = true
                checkinReminderEnabled = false
            }
        }
    }

    private func scheduleNotification() {
        let center = UNUserNotificationCenter.current()
        center.removePendingNotificationRequests(withIdentifiers: ["voliti_daily_checkin"])

        let content = UNMutableNotificationContent()
        content.title = "Voliti"
        content.body = preferredLanguage == "en" ? "Time to check in with your coach" : "是时候和教练聊聊了"
        content.sound = .default

        let totalSeconds = Int(checkinReminderTime)
        var dateComponents = DateComponents()
        dateComponents.hour = totalSeconds / 3600
        dateComponents.minute = (totalSeconds % 3600) / 60

        let trigger = UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: true)
        let request = UNNotificationRequest(identifier: "voliti_daily_checkin", content: content, trigger: trigger)

        center.add(request) { error in
            if let error {
                logger.warning("Failed to schedule notification: \(error.localizedDescription)")
            }
        }
    }

    private func cancelNotification() {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: ["voliti_daily_checkin"])
    }

    // MARK: - Reminder Date Binding

    private var reminderDateBinding: Binding<Date> {
        Binding(
            get: {
                Calendar.current.startOfDay(for: .now)
                    .addingTimeInterval(checkinReminderTime)
            },
            set: { newDate in
                let calendar = Calendar.current
                let components = calendar.dateComponents([.hour, .minute], from: newDate)
                checkinReminderTime = Double((components.hour ?? 8) * 3600 + (components.minute ?? 0) * 60)
            }
        )
    }
}
