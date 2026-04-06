// ABOUTME: API 配置，管理 LangGraph 后端 base URL、assistant ID 和认证凭据
// ABOUTME: 本地开发使用局域网 IP，生产环境使用 LangGraph Cloud URL + x-api-key

import Foundation

enum APIConfiguration {
    /// LangGraph 后端 base URL
    /// 本地开发：http://192.168.x.x:2025（Mac 局域网 IP）
    /// 生产环境：LangGraph Cloud 部署 URL
    static var baseURL: URL {
        if let urlString = ProcessInfo.processInfo.environment["LANGGRAPH_API_URL"],
           let url = URL(string: urlString) {
            return url
        }
        return URL(string: "http://localhost:2025")!
    }

    /// LangGraph Cloud API Key（x-api-key header）
    /// 读取优先级：环境变量 → Info.plist
    /// 本地开发 server 无需 key，返回 nil 时不附加 header
    static var apiKey: String? {
        if let envKey = ProcessInfo.processInfo.environment["LANGGRAPH_API_KEY"],
           !envKey.isEmpty {
            return envKey
        }
        return Bundle.main.infoDictionary?["LANGGRAPH_API_KEY"] as? String
    }

    static let assistantID = "coach"

    private static let threadIDKey = "voliti_thread_id"
    private static let onboardingThreadIDKey = "voliti_onboarding_thread_id"

    /// 持久化 Coaching Thread ID
    static var threadID: String? {
        get { UserDefaults.standard.string(forKey: threadIDKey) }
        set { UserDefaults.standard.set(newValue, forKey: threadIDKey) }
    }

    /// 持久化 Onboarding Thread ID（独立采集会话）
    static var onboardingThreadID: String? {
        get { UserDefaults.standard.string(forKey: onboardingThreadIDKey) }
        set { UserDefaults.standard.set(newValue, forKey: onboardingThreadIDKey) }
    }
}
