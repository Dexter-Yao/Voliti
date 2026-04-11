// ABOUTME: 请求上下文辅助类型，定义 user_id、correlation_id 与 session_type 的统一注入规则
// ABOUTME: 所有用户触发链路通过此处构造 configurable，避免请求边界散落重复逻辑

import Foundation

enum RequestContext {
    static func configurable(
        sessionType: SessionType,
        preferredLanguage: String,
        correlationID: String
    ) -> [String: Any] {
        var configurable: [String: Any] = [
            "session_type": sessionType.rawValue,
            "user_id": APIConfiguration.userID,
            "correlation_id": correlationID,
        ]
        if preferredLanguage != "system" {
            configurable["preferred_language"] = preferredLanguage
        }
        return configurable
    }
}
