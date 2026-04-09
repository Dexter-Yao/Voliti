// ABOUTME: LangGraph REST API 客户端，管理 Thread 和 Run 生命周期
// ABOUTME: 处理流式对话、A2UI 中断/恢复、Store 查询

import Foundation

struct LangGraphAPI: Sendable {
    private let sseClient: SSEClient
    private let session: URLSession

    init(
        session: URLSession = .shared,
        sseClient: SSEClient = SSEClient()
    ) {
        self.session = session
        self.sseClient = sseClient
    }
    
    private func trace(_ message: String) {
#if DEBUG
        print("[LangGraphAPI] \(message)")
#endif
    }

    // MARK: - Thread Management

    /// 创建新的对话线程
    func createThread(metadata: [String: String] = [:]) async throws -> String {
        let url = APIConfiguration.baseURL.appendingPathComponent("threads")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        Self.applyAuth(&request)

        var body: [String: Any] = [:]
        body["metadata"] = metadata.merging([
            "user_id": APIConfiguration.userID,
            "correlation_id": APIConfiguration.makeCorrelationID(),
        ]) { current, _ in current }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)
        try validateResponse(response)

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let threadID = json["thread_id"] as? String else {
            throw NetworkError.invalidJSON
        }
        return threadID
    }

    /// 确保有可用的 Coaching Thread ID
    func ensureThread() async throws -> String {
        try await ensureThread(
            existing: APIConfiguration.threadID,
            sessionMode: "coaching",
            save: { APIConfiguration.threadID = $0 }
        )
    }

    /// 确保有可用的 Onboarding Thread ID
    func ensureOnboardingThread() async throws -> String {
        try await ensureThread(
            existing: APIConfiguration.onboardingThreadID,
            sessionMode: "onboarding",
            save: { APIConfiguration.onboardingThreadID = $0 }
        )
    }

    private func ensureThread(
        existing: String?,
        sessionMode: String,
        save: @Sendable (String) -> Void
    ) async throws -> String {
        if let existing { return existing }
        let threadID = try await createThread(metadata: ["session_mode": sessionMode])
        save(threadID)
        return threadID
    }

    // MARK: - Streaming

    /// 发送消息并获取流式响应
    func streamRun(threadID: String, message: String, imageData: Data? = nil, sessionMode: String = "coaching", priorAssistantMessage: String? = nil) throws -> AsyncStream<SSEEvent> {
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

        let preferredLanguage = UserDefaults.standard.string(forKey: "preferredLanguage") ?? "system"
        let configurable = RequestContext.configurable(
            sessionMode: sessionMode,
            preferredLanguage: preferredLanguage,
            correlationID: APIConfiguration.makeCorrelationID()
        )

        var inputMessages: [[String: Any]] = []
        if let prior = priorAssistantMessage {
            inputMessages.append(["role": "assistant", "content": prior])
        }
        inputMessages.append(["role": "user", "content": content])

        let body: [String: Any] = [
            "assistant_id": APIConfiguration.assistantID,
            "input": [
                "messages": inputMessages
            ],
            "config": ["configurable": configurable],
            "stream_mode": ["messages", "values"],
            "stream_subgraphs": true,
        ]

        let request = try buildStreamRequest(threadID: threadID, body: body)
        trace("streamRun request ready: threadID=\(threadID), textCount=\(message.count), hasImage=\(imageData != nil), url=\(request.url?.absoluteString ?? "<nil>")")
        return sseClient.stream(request: request)
    }

    /// 恢复 A2UI 中断
    func resumeInterrupt(
        threadID: String,
        action: String,
        data: [String: Any] = [:],
        interruptID: String? = nil,
        sessionMode: String = "coaching"
    ) throws -> AsyncStream<SSEEvent> {
        let preferredLanguage = UserDefaults.standard.string(forKey: "preferredLanguage") ?? "system"
        let body = Self.makeResumeBody(
            action: action,
            data: data,
            sessionMode: sessionMode,
            preferredLanguage: preferredLanguage,
            correlationID: APIConfiguration.makeCorrelationID(),
            interruptID: interruptID
        )

        let request = try buildStreamRequest(threadID: threadID, body: body)
        trace("resumeInterrupt request ready: threadID=\(threadID), action=\(action), url=\(request.url?.absoluteString ?? "<nil>")")
        return sseClient.stream(request: request)
    }

    static func makeResumeBody(
        action: String,
        data: [String: Any],
        sessionMode: String,
        preferredLanguage: String,
        correlationID: String,
        interruptID: String?
    ) -> [String: Any] {
        var resumeBody: [String: Any] = [
            "action": action,
            "data": data,
        ]
        if let interruptID {
            resumeBody["interrupt_id"] = interruptID
        }

        return [
            "assistant_id": APIConfiguration.assistantID,
            "command": ["resume": resumeBody],
            "config": ["configurable": RequestContext.configurable(
                sessionMode: sessionMode,
                preferredLanguage: preferredLanguage,
                correlationID: correlationID
            )],
            "stream_mode": ["messages", "values"],
            "stream_subgraphs": true,
        ]
    }

    // MARK: - Store

    /// 向 LangGraph Store 写入单个 item
    func putStoreItem(namespace: [String], key: String, value: [String: Any]) async throws {
        let url = APIConfiguration.baseURL.appendingPathComponent("store/items")
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        Self.applyAuth(&request)

        let body: [String: Any] = [
            "namespace": namespace,
            "key": key,
            "value": value,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)
        try validateResponse(response)
    }

    /// 从 LangGraph Store 获取单个 item 的 value。item 不存在时返回 nil。
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

        let (data, response) = try await session.data(for: request)

        // Store 在 item 不存在时可能返回 404 或非 JSON 响应，视为 nil
        guard let http = response as? HTTPURLResponse else { return nil }
        guard (200..<300).contains(http.statusCode) else { return nil }

        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let value = json["value"] as? [String: Any] else {
            return nil
        }
        return value
    }

    /// 从 LangGraph Store 搜索指定 namespace 下的所有 items
    func searchStoreItems(namespace: [String]) async throws -> [[String: Any]] {
        let url = APIConfiguration.baseURL.appendingPathComponent("store/items/search")
        var allItems: [[String: Any]] = []
        var offset = 0
        let limit = 100

        while true {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            Self.applyAuth(&request)

            let body: [String: Any] = [
                "namespace_prefix": namespace,
                "limit": limit,
                "offset": offset,
            ]
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await session.data(for: request)
            try validateResponse(response)

            guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let items = json["items"] as? [[String: Any]] else {
                return allItems
            }

            allItems.append(contentsOf: items)
            if items.count < limit {
                return allItems
            }
            offset += limit
        }
    }

    // MARK: - Store Deletion

    /// 清除指定 namespace 下的所有 Store items
    func deleteStoreItems(namespace: [String]) async throws {
        let items = try await searchStoreItems(namespace: namespace)
        try await withThrowingTaskGroup(of: Void.self) { group in
            for item in items {
                guard let key = item["key"] as? String else { continue }
                group.addTask { try await self.deleteStoreItem(namespace: namespace, key: key) }
            }
            try await group.waitForAll()
        }
    }

    /// 删除单个 Store item
    private func deleteStoreItem(namespace: [String], key: String) async throws {
        let url = APIConfiguration.baseURL.appendingPathComponent("store/items")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        Self.applyAuth(&request)

        let body: [String: Any] = [
            "namespace": namespace,
            "key": key,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await session.data(for: request)
        // 404 表示 item 已不存在，视为成功
        if let http = response as? HTTPURLResponse, http.statusCode != 404 {
            try validateResponse(response)
        }
    }

    /// 清除所有用户 Store 数据
    /// 使用 namespace_prefix wildcard 搜索，无需硬编码子 namespace 列表
    func clearUserStore() async throws {
        let items = try await searchStoreItems(namespace: StoreContract.userNamespace)
        try await withThrowingTaskGroup(of: Void.self) { group in
            for item in items {
                guard let key = item["key"] as? String,
                      let namespace = item["namespace"] as? [String] else { continue }
                group.addTask { try await self.deleteStoreItem(namespace: namespace, key: key) }
            }
            try await group.waitForAll()
        }
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
