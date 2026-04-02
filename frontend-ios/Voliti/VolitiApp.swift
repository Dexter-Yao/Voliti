// ABOUTME: Voliti iOS 应用入口
// ABOUTME: 配置 SwiftData ModelContainer，初始化通知服务，Onboarding 完成后请求通知权限

import SwiftUI
import SwiftData

@main
struct VolitiApp: App {
    let modelContainer: ModelContainer
    @State private var notificationService = NotificationService()
    @AppStorage("onboardingComplete") private var onboardingComplete = false

    init() {
        do {
            modelContainer = try ModelContainerSetup.create()
        } catch {
            fatalError("ModelContainer 创建失败: \(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(notificationService)
                .task {
                    await notificationService.checkCurrentStatus()
                    if onboardingComplete && notificationService.isAuthorized {
                        await notificationService.scheduleDefaultReminders()
                    }
                }
                .onChange(of: onboardingComplete) { _, isComplete in
                    if isComplete {
                        Task {
                            await notificationService.requestPermissionAndSchedule()
                        }
                    }
                }
        }
        .modelContainer(modelContainer)
    }
}
