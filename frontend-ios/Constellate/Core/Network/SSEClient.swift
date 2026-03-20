// ABOUTME: Server-Sent Events 客户端，解析 LangGraph 流式响应
// ABOUTME: 基于 URLSession AsyncBytes，无第三方依赖

import Foundation

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
                                if let event = Self.parseEvent(type: currentEvent, data: currentData) {
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

    private static func parseEvent(type: String, data: String) -> SSEEvent? {
        guard let jsonData = data.data(using: .utf8) else { return nil }

        switch type {
        case "messages/partial":
            return parsePartialMessage(jsonData)
        case "messages/complete":
            return parseCompleteMessage(jsonData)
        case "values":
            return parseValuesForInterrupt(jsonData)
        case "end":
            return .done
        default:
            return nil
        }
    }

    private static func parsePartialMessage(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
              let last = json.last,
              let content = last["content"] as? String,
              let type = last["type"] as? String,
              type == "ai" else {
            return nil
        }
        return .token(content)
    }

    private static func parseCompleteMessage(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
              let last = json.last,
              let content = last["content"] as? String,
              let type = last["type"] as? String else {
            return nil
        }
        return .message(role: type == "ai" ? "assistant" : "user", content: content)
    }

    private static func parseValuesForInterrupt(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let interrupt = json["interrupt"] as? [String: Any],
              let value = interrupt["value"] as? [[String: Any]],
              let first = value.first else {
            return nil
        }

        if let type = first["type"] as? String, type == "a2ui" {
            if let payloadData = try? JSONSerialization.data(withJSONObject: first) {
                return .interrupt(payloadData)
            }
        }
        return nil
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
