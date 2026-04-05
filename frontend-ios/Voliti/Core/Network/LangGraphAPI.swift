// ABOUTME: LangGraph REST API 客户端，管理 Thread 和 Run 生命周期
// ABOUTME: 处理流式对话、A2UI 中断/恢复、Store 查询

import Foundation

struct LangGraphAPI: Sendable {
    private let sseClient = SSEClient()

    // MARK: - Thread Management

    /// 创建新的对话线程
    func createThread() async throws -> String {
        let url = APIConfiguration.baseURL.appendingPathComponent("threads")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        Self.applyAuth(&request)
        request.httpBody = try JSONSerialization.data(withJSONObject: [:])

        let (data, response) = try await URLSession.shared.data(for: request)
        try validateResponse(response)

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let threadID = json["thread_id"] as? String else {
            throw NetworkError.invalidJSON
        }
        return threadID
    }

    /// 确保有可用的 Thread ID
    func ensureThread() async throws -> String {
        if let existing = APIConfiguration.threadID {
            return existing
        }
        let threadID = try await createThread()
        APIConfiguration.threadID = threadID
        return threadID
    }

    // MARK: - Streaming

    /// 发送消息并获取流式响应
    func streamRun(threadID: String, message: String, imageData: Data? = nil) throws -> AsyncStream<SSEEvent> {
        var content: [[String: Any]] = [
            ["type": "text", "text": message]
        ]

        if let imageData {
            let base64 = imageData.base64EncodedString()
            content.append([
                "type": "image_url",
                "image_url": ["url": "data:image/jpeg;base64,\(base64)"]
            ])
        }

        let timestamp = ISO8601DateFormatter().string(from: Date())
        content.insert(["type": "text", "text": "[\(timestamp)] "], at: 0)

        let body: [String: Any] = [
            "assistant_id": APIConfiguration.assistantID,
            "input": [
                "messages": [
                    ["role": "user", "content": content]
                ]
            ],
            "stream_mode": ["messages", "values"],
            "stream_subgraphs": true,
        ]

        let request = try buildStreamRequest(threadID: threadID, body: body)
        return sseClient.stream(request: request)
    }

    /// 恢复 A2UI 中断
    func resumeInterrupt(threadID: String, action: String, data: [String: Any] = [:]) throws -> AsyncStream<SSEEvent> {
        let body: [String: Any] = [
            "assistant_id": APIConfiguration.assistantID,
            "command": ["resume": ["action": action, "data": data]],
            "stream_mode": ["messages", "values"],
            "stream_subgraphs": true,
        ]

        let request = try buildStreamRequest(threadID: threadID, body: body)
        return sseClient.stream(request: request)
    }

    // MARK: - Store

    /// 从 LangGraph Store 获取单个 item 的 value
    func fetchStoreItem(namespace: [String], key: String) async throws -> [String: Any]? {
        let ns = namespace.joined(separator: ".")
        var components = URLComponents(
            url: APIConfiguration.baseURL.appendingPathComponent("store/items"),
            resolvingAgainstBaseURL: false
        )!
        components.queryItems = [
            URLQueryItem(name: "namespace", value: ns),
            URLQueryItem(name: "key", value: key),
        ]

        var request = URLRequest(url: components.url!)
        request.httpMethod = "GET"
        Self.applyAuth(&request)

        let (data, response) = try await URLSession.shared.data(for: request)
        try validateResponse(response)

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let value = json["value"] as? [String: Any] else {
            return nil
        }
        return value
    }

    // MARK: - Request Builder

    private func buildStreamRequest(threadID: String, body: [String: Any]) throws -> URLRequest {
        let url = APIConfiguration.baseURL
            .appendingPathComponent("threads")
            .appendingPathComponent(threadID)
            .appendingPathComponent("runs")
            .appendingPathComponent("stream")

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        Self.applyAuth(&request)
        request.timeoutInterval = 300
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        return request
    }

    // MARK: - Authentication

    /// 附加 x-api-key header（仅在 apiKey 配置时生效）
    private static func applyAuth(_ request: inout URLRequest) {
        if let key = APIConfiguration.apiKey {
            request.setValue(key, forHTTPHeaderField: "x-api-key")
        }
    }

    // MARK: - Validation

    private func validateResponse(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw NetworkError.httpError(code)
        }
    }
}
