// ABOUTME: Server-Sent Events 客户端，解析 LangGraph 流式响应
// ABOUTME: 基于 URLSession AsyncBytes，无第三方依赖

import Foundation
import os.log

// MARK: - SSE Event Types

enum SSEEvent: Sendable {
    /// 流式文本 token
    case token(String)
    /// Coach 发送的完整消息
    case message(role: String, content: String)
    /// A2UI 中断（JSON data）
    case interrupt(Data)
    /// 流结束
    case done
    /// 错误
    case error(Error)
}

// MARK: - SSE Client

struct SSEClient: Sendable {

    /// 发起 SSE 流式请求，返回 AsyncStream<SSEEvent>
    func stream(request: URLRequest) -> AsyncStream<SSEEvent> {
        AsyncStream { continuation in
            let task = Task.detached {
                do {
                    let (bytes, response) = try await URLSession.shared.bytes(for: request)

                    guard let httpResponse = response as? HTTPURLResponse else {
                        continuation.yield(.error(NetworkError.invalidResponse))
                        continuation.finish()
                        return
                    }

                    guard (200..<300).contains(httpResponse.statusCode) else {
                        continuation.yield(.error(NetworkError.httpError(httpResponse.statusCode)))
                        continuation.finish()
                        return
                    }

                    var currentEvent = ""
                    var currentData = ""

                    for try await line in bytes.lines {
                        if Task.isCancelled { break }

                        if line.isEmpty {
                            if !currentData.isEmpty {
                                for event in Self.parseEvent(type: currentEvent, data: currentData) {
                                    continuation.yield(event)
                                }
                            }
                            currentEvent = ""
                            currentData = ""
                            continue
                        }

                        if line.hasPrefix("event: ") {
                            currentEvent = String(line.dropFirst(7))
                        } else if line.hasPrefix("data: ") {
                            let data = String(line.dropFirst(6))
                            if currentData.isEmpty {
                                currentData = data
                            } else {
                                currentData += "\n" + data
                            }
                        }
                    }

                    continuation.yield(.done)
                    continuation.finish()
                } catch {
                    if !Task.isCancelled {
                        continuation.yield(.error(error))
                    }
                    continuation.finish()
                }
            }

            continuation.onTermination = { _ in
                task.cancel()
            }
        }
    }

    // MARK: - Event Parsing

    nonisolated private static func parseEvent(type: String, data: String) -> [SSEEvent] {
        guard let jsonData = data.data(using: .utf8) else { return [] }

        switch type {
        case "messages/partial":
            if let event = parsePartialMessage(jsonData) { return [event] }
            return []
        case "messages/complete":
            if let event = parseCompleteMessage(jsonData) { return [event] }
            return []
        case "values":
            return parseValuesEvent(jsonData)
        case "end":
            return [.done]
        default:
            return []
        }
    }

    nonisolated private static func parsePartialMessage(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
              let last = json.last,
              let content = last["content"] as? String,
              let type = last["type"] as? String,
              type == "ai" else {
            return nil
        }
        return .token(content)
    }

    nonisolated private static func parseCompleteMessage(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
              let last = json.last,
              let content = last["content"] as? String,
              let type = last["type"] as? String else {
            return nil
        }
        return .message(role: type == "ai" ? "assistant" : "user", content: content)
    }

    private static let logger = Logger(subsystem: "voliti", category: "SSEClient")

    nonisolated private static func parseValuesEvent(_ data: Data) -> [SSEEvent] {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return []
        }

        var events: [SSEEvent] = []

        // 先提取 AI 文本（确保 processStream 在处理 interrupt 前已有 fullContent）
        if let messages = json["messages"] as? [[String: Any]] {
            for msg in messages.reversed() {
                guard let type = msg["type"] as? String, type == "ai",
                      let content = msg["content"] as? String,
                      !content.isEmpty else { continue }
                events.append(.message(role: "assistant", content: content))
                break
            }
        }

        // 再检查 interrupt — LangGraph REST API 使用 __interrupt__ key
        if let interrupts = json["__interrupt__"] as? [[String: Any]],
           let first = interrupts.first,
           let value = first["value"] as? [String: Any],
           let type = value["type"] as? String, type == "a2ui",
           let payloadData = try? JSONSerialization.data(withJSONObject: value) {
            events.append(.interrupt(payloadData))
        }

        return events
    }
}

// MARK: - Errors

enum NetworkError: LocalizedError, Sendable {
    case invalidResponse
    case invalidJSON
    case httpError(Int)

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid server response"
        case .invalidJSON: return "Invalid JSON response"
        case .httpError(let code): return "HTTP error: \(code)"
        }
    }
}
