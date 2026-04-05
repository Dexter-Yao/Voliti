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
    nonisolated private static func trace(_ message: String) {
#if DEBUG
        print("[SSEClient] \(message)")
#endif
    }

    /// 发起 SSE 流式请求，返回 AsyncStream<SSEEvent>
    func stream(request: URLRequest) -> AsyncStream<SSEEvent> {
        AsyncStream { continuation in
            let task = Task.detached {
                do {
                    Self.trace("stream() start: \(request.httpMethod ?? "GET") \(request.url?.absoluteString ?? "<nil>")")
                    let (bytes, response) = try await URLSession.shared.bytes(for: request)

                    guard let httpResponse = response as? HTTPURLResponse else {
                        Self.trace("invalid response type")
                        continuation.yield(.error(NetworkError.invalidResponse))
                        continuation.finish()
                        return
                    }

                    guard (200..<300).contains(httpResponse.statusCode) else {
                        Self.trace("HTTP status: \(httpResponse.statusCode)")
                        continuation.yield(.error(NetworkError.httpError(httpResponse.statusCode)))
                        continuation.finish()
                        return
                    }
                    Self.trace("connected: HTTP \(httpResponse.statusCode)")

                    var currentEvent = ""
                    var currentData = ""
                    var lineBuffer = Data()

                    // 手动逐字节解析行，替代 bytes.lines（后者对 SSE 空行分隔不可靠）
                    for try await byte in bytes {
                        if Task.isCancelled { break }

                        guard byte == UInt8(ascii: "\n") else {
                            lineBuffer.append(byte)
                            continue
                        }

                        // 遇到 \n → 构建当前行
                        var line = String(data: lineBuffer, encoding: .utf8) ?? ""
                        lineBuffer.removeAll(keepingCapacity: true)

                        // CRLF 兼容
                        if line.hasSuffix("\r") { line.removeLast() }

                        if line.isEmpty {
                            // 空行 = SSE 事件边界
                            if !currentData.isEmpty {
                                Self.trace("event complete: \(currentEvent), dataBytes=\(currentData.utf8.count)")
                                for event in Self.parseEvent(type: currentEvent, data: currentData) {
                                    Self.trace("yield \(Self.eventDescription(event))")
                                    continuation.yield(event)
                                }
                            }
                            currentEvent = ""
                            currentData = ""
                        } else if line.hasPrefix(":") {
                            // SSE 注释/heartbeat
                        } else if line.hasPrefix("event: ") {
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

                    // EOF flush
                    if !currentData.isEmpty {
                        Self.trace("flush at EOF: \(currentEvent), dataBytes=\(currentData.utf8.count)")
                        for event in Self.parseEvent(type: currentEvent, data: currentData) {
                            Self.trace("yield \(Self.eventDescription(event))")
                            continuation.yield(event)
                        }
                    }

                    Self.trace("bytes.lines ended; yielding done")
                    continuation.yield(.done)
                    continuation.finish()
                } catch {
                    if !Task.isCancelled {
                        Self.trace("stream error: \(error.localizedDescription)")
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
            trace("ignored event type: \(type)")
            return []
        }
    }

    nonisolated private static func parsePartialMessage(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
              let last = json.last,
              let type = last["type"] as? String,
              type == "ai",
              let content = extractContent(from: last["content"]) else {
            trace("parsePartialMessage: no AI string content")
            return nil
        }
        return .token(content)
    }

    nonisolated private static func parseCompleteMessage(_ data: Data) -> SSEEvent? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]],
              let last = json.last,
              let content = extractContent(from: last["content"]),
              let type = last["type"] as? String else {
            trace("parseCompleteMessage: decode failed")
            return nil
        }
        return .message(role: type == "ai" ? "assistant" : "user", content: content)
    }

    private static let logger = Logger(subsystem: "voliti", category: "SSEClient")

    nonisolated private static func parseValuesEvent(_ data: Data) -> [SSEEvent] {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            trace("parseValuesEvent: invalid JSON")
            return []
        }

        var events: [SSEEvent] = []

        // 先提取 AI 文本（确保 processStream 在处理 interrupt 前已有 fullContent）
        if let messages = json["messages"] as? [[String: Any]] {
            for msg in messages.reversed() {
                guard let type = msg["type"] as? String, type == "ai",
                      let content = extractContent(from: msg["content"]),
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

        if events.isEmpty {
            trace("parseValuesEvent: no message/interrupt found; keys=\(json.keys.sorted())")
        }
        return events
    }

    nonisolated private static func extractContent(from raw: Any?) -> String? {
        guard let raw else { return nil }
        if let string = raw as? String {
            return string
        }
        if let parts = raw as? [[String: Any]] {
            let text = parts.compactMap { part -> String? in
                guard let type = part["type"] as? String, type == "text" else { return nil }
                return part["text"] as? String
            }.joined()
            return text.isEmpty ? nil : text
        }
        return nil
    }

    nonisolated private static func eventDescription(_ event: SSEEvent) -> String {
        switch event {
        case .token(let content):
            return "token(\(content.count) chars)"
        case .message(let role, let content):
            return "message(role=\(role), \(content.count) chars)"
        case .interrupt(let data):
            return "interrupt(\(data.count) bytes)"
        case .done:
            return "done"
        case .error(let error):
            return "error(\(error.localizedDescription))"
        }
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
