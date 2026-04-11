// ABOUTME: SessionType 共享会话类型定义
// ABOUTME: 为请求契约、线程选择与界面流程提供唯一的会话类型事实来源

import Foundation

enum SessionType: String, Sendable {
    case coaching
    case onboarding
}
