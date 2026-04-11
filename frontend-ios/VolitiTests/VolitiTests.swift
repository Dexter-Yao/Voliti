// ABOUTME: Voliti 核心测试套件
// ABOUTME: 覆盖 MetricComputer、BehaviorEvent 解码、ResetService 执行顺序

import Testing
import Foundation
import SwiftData
@testable import Voliti

private func sharedStoreFixtureURL(named name: String) -> URL {
    let fileURL = URL(fileURLWithPath: #filePath)
    return fileURL
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .appendingPathComponent("tests/contracts/fixtures/store/\(name)")
}

private func loadSharedStoreFixture(named name: String) throws -> [String: Any] {
    let data = try Data(contentsOf: sharedStoreFixtureURL(named: name))
    let object = try JSONSerialization.jsonObject(with: data)
    guard let value = object as? [String: Any] else {
        throw StoreContractError.invalidJSON
    }
    return value
}

private func requestBodyData(from request: URLRequest) throws -> Data? {
    if let body = request.httpBody {
        return body
    }

    guard let stream = request.httpBodyStream else {
        return nil
    }

    stream.open()
    defer { stream.close() }

    var data = Data()
    let bufferSize = 1024
    let buffer = UnsafeMutablePointer<UInt8>.allocate(capacity: bufferSize)
    defer { buffer.deallocate() }

    while stream.hasBytesAvailable {
        let read = stream.read(buffer, maxLength: bufferSize)
        if read < 0 {
            throw stream.streamError ?? URLError(.badServerResponse)
        }
        if read == 0 {
            break
        }
        data.append(buffer, count: read)
    }

    return data
}

private func makeInMemoryContainer() throws -> ModelContainer {
    let schema = Schema(versionedSchema: VolitiSchemaV1.self)
    let config = ModelConfiguration(
        schema: schema,
        isStoredInMemoryOnly: true,
        cloudKitDatabase: .none
    )
    return try ModelContainer(
        for: schema,
        migrationPlan: VolitiMigrationPlan.self,
        configurations: [config]
    )
}

private final class MockURLProtocol: URLProtocol, @unchecked Sendable {
    private static let sessionHeader = "X-Voliti-Mock-Session-ID"
    private static let lock = NSLock()
    nonisolated(unsafe) private static var requestHandlers: [String: @Sendable (URLRequest) throws -> (HTTPURLResponse, Data)] = [:]

    static func registerHandler(
        _ handler: @escaping @Sendable (URLRequest) throws -> (HTTPURLResponse, Data)
    ) -> String {
        let sessionID = UUID().uuidString
        lock.lock()
        requestHandlers[sessionID] = handler
        lock.unlock()
        return sessionID
    }

    static func handler(for sessionID: String) -> (@Sendable (URLRequest) throws -> (HTTPURLResponse, Data))? {
        lock.lock()
        defer { lock.unlock() }
        return requestHandlers[sessionID]
    }

    override class func canInit(with request: URLRequest) -> Bool {
        true
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        request
    }

    override func startLoading() {
        guard let sessionID = request.value(forHTTPHeaderField: Self.sessionHeader),
              let handler = Self.handler(for: sessionID) else {
            client?.urlProtocol(self, didFailWithError: URLError(.badServerResponse))
            return
        }

        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}

private func makeMockSession(
    handler: @escaping @Sendable (URLRequest) throws -> (HTTPURLResponse, Data)
) -> URLSession {
    let configuration = URLSessionConfiguration.ephemeral
    configuration.protocolClasses = [MockURLProtocol.self]
    let sessionID = MockURLProtocol.registerHandler(handler)
    configuration.httpAdditionalHeaders = [ "X-Voliti-Mock-Session-ID": sessionID ]
    return URLSession(configuration: configuration)
}

private final class LockedRecorder<Value>: @unchecked Sendable {
    private let lock = NSLock()
    private var value: Value

    init(_ value: Value) {
        self.value = value
    }

    func withValue<Result>(_ body: (inout Value) -> Result) -> Result {
        lock.lock()
        defer { lock.unlock() }
        return body(&value)
    }

    func snapshot() -> Value {
        lock.lock()
        defer { lock.unlock() }
        return value
    }
}

// MARK: - MetricComputer Tests

@Suite("MetricComputer")
struct MetricComputerTests {

    private func makeEvent(
        kind: String = "observation",
        timestamp: Date = .now,
        metrics: [MetricEntry] = []
    ) -> BehaviorEvent {
        let event = BehaviorEvent(
            id: UUID().uuidString,
            timestamp: timestamp,
            recordedAt: .now,
            kind: kind,
            evidence: "test",
            tags: []
        )
        if !metrics.isEmpty {
            event.setMetrics(metrics)
        }
        return event
    }

    private func daysAgo(_ n: Int) -> Date {
        Calendar.current.date(byAdding: .day, value: -n, to: Calendar.current.startOfDay(for: .now))!
    }

    // MARK: - currentValue

    @Test func currentValue_happyPath() {
        let events = [
            makeEvent(timestamp: daysAgo(1), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 71.5, quality: .reported)]),
        ]
        let result = MetricComputer.currentValue(for: "weight", from: events)
        #expect(result == 71.5)
    }

    @Test func currentValue_noData() {
        let result = MetricComputer.currentValue(for: "weight", from: [])
        #expect(result == nil)
    }

    @Test func currentValue_missingExcluded() {
        let events = [
            makeEvent(metrics: [MetricEntry(key: "weight", value: nil, quality: .missing)]),
        ]
        let result = MetricComputer.currentValue(for: "weight", from: events)
        #expect(result == nil)
    }

    @Test func currentValue_estimatedIncluded() {
        let events = [
            makeEvent(metrics: [MetricEntry(key: "weight", value: 72.0, quality: .estimated)]),
        ]
        let result = MetricComputer.currentValue(for: "weight", from: events)
        #expect(result == 72.0)
    }

    @Test func currentValue_latestEventWins() {
        let events = [
            makeEvent(timestamp: daysAgo(2), metrics: [MetricEntry(key: "kcal", value: 1200, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "kcal", value: 1800, quality: .reported)]),
        ]
        let result = MetricComputer.currentValue(for: "kcal", from: events)
        #expect(result == 1800)
    }

    // MARK: - trend

    @Test func trend_full7Days() {
        let events = (0..<7).map { day in
            makeEvent(
                timestamp: daysAgo(6 - day),
                metrics: [MetricEntry(key: "weight", value: 73.0 - Double(day) * 0.3, quality: .reported)]
            )
        }
        let trend = MetricComputer.trend(for: "weight", from: events)
        #expect(trend.count == 7)
        #expect(trend.allSatisfy { $0 != nil })
    }

    @Test func trend_sparse() {
        let events = [
            makeEvent(timestamp: daysAgo(5), metrics: [MetricEntry(key: "weight", value: 73.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(1), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
        ]
        let trend = MetricComputer.trend(for: "weight", from: events)
        #expect(trend.count == 7)
        let nonNilCount = trend.compactMap { $0 }.count
        #expect(nonNilCount == 2)
    }

    @Test func trend_empty() {
        let trend = MetricComputer.trend(for: "weight", from: [])
        #expect(trend.count == 7)
        #expect(trend.allSatisfy { $0 == nil })
    }

    // MARK: - trendQualities

    @Test func trendQualities_mixedQuality() {
        let events = [
            makeEvent(timestamp: daysAgo(1), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 71.5, quality: .estimated)]),
        ]
        let qualities = MetricComputer.trendQualities(for: "weight", from: events)
        #expect(qualities.count == 7)
        #expect(qualities.last == .estimated)
    }

    // MARK: - delta

    @Test func delta_normalDecrease() {
        let events = [
            makeEvent(timestamp: daysAgo(7), metrics: [MetricEntry(key: "weight", value: 73.0, quality: .reported)]),
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
        ]
        let delta = MetricComputer.delta(for: "weight", from: events, direction: .decrease)
        #expect(delta != nil)
        #expect(delta!.value < 0)
        #expect(delta!.isPositive == true)
    }

    @Test func delta_noReference() {
        let events = [
            makeEvent(timestamp: daysAgo(0), metrics: [MetricEntry(key: "weight", value: 72.0, quality: .reported)]),
        ]
        let delta = MetricComputer.delta(for: "weight", from: events, direction: .decrease)
        #expect(delta == nil)
    }

    // MARK: - format

    @Test func format_numeric() {
        let result = MetricComputer.format(value: 72.3, type: .numeric, scaleMax: nil, ratioDenominator: nil)
        #expect(result.contains("72"))
    }

    @Test func format_nil() {
        let result = MetricComputer.format(value: nil, type: .numeric, scaleMax: nil, ratioDenominator: nil)
        #expect(result == "—")
    }

    @Test func format_scale() {
        let result = MetricComputer.format(value: 7.0, type: .scale, scaleMax: 10, ratioDenominator: nil)
        #expect(result.contains("7"))
        #expect(result.contains("10"))
    }

    @Test func format_ratio() {
        let result = MetricComputer.format(value: 5.0, type: .ratio, scaleMax: nil, ratioDenominator: 7)
        #expect(result.contains("5"))
        #expect(result.contains("7"))
    }
}

// MARK: - Mirror Log Range Tests

@Suite("MirrorLogRange")
struct MirrorLogRangeTests {
    private let calendar = Calendar.current

    @Test func validatedCustomRejectsEndBeforeStart() {
        let start = calendar.startOfDay(for: .now)
        let end = calendar.date(byAdding: .day, value: -1, to: start)!

        #expect(throws: MirrorLogRangeError.endBeforeStart) {
            try MirrorLogRange.validatedCustom(startDate: start, endDate: end, today: .now, calendar: calendar)
        }
    }

    @Test func validatedCustomRejectsFutureEndDate() {
        let start = calendar.startOfDay(for: .now)
        let end = calendar.date(byAdding: .day, value: 1, to: start)!

        #expect(throws: MirrorLogRangeError.endAfterToday) {
            try MirrorLogRange.validatedCustom(startDate: start, endDate: end, today: .now, calendar: calendar)
        }
    }

    @Test func customTitleUsesFullDateFormat() throws {
        let start = calendar.date(from: DateComponents(year: 2026, month: 4, day: 1))!
        let end = calendar.date(from: DateComponents(year: 2026, month: 4, day: 11))!
        let range = try MirrorLogRange.validatedCustom(startDate: start, endDate: end, today: end, calendar: calendar)

        #expect(range.title(calendar: calendar) == "2026.04.01 - 2026.04.11")
    }
}

// MARK: - Mirror ViewModel Tests

@Suite("MirrorViewModel")
@MainActor
struct MirrorViewModelTests {
    private let calendar = Calendar.current

    private final class StubSyncService: StoreSyncing {
        private let freshness: ProjectionFreshness

        init(freshness: ProjectionFreshness) {
            self.freshness = freshness
        }

        func syncAll() async -> ProjectionFreshness {
            freshness
        }

        func checkOnboardingComplete() async -> Bool {
            true
        }
    }

    private func makeEvent(
        kind: String = "observation",
        timestamp: Date = .now,
        summary: String? = nil,
        metrics: [MetricEntry] = []
    ) -> BehaviorEvent {
        let event = BehaviorEvent(
            id: UUID().uuidString,
            timestamp: timestamp,
            recordedAt: timestamp,
            kind: kind,
            evidence: "test",
            summary: summary,
            tags: []
        )
        if !metrics.isEmpty {
            event.setMetrics(metrics)
        }
        return event
    }

    private func daysAgo(_ n: Int) -> Date {
        calendar.date(byAdding: .day, value: -n, to: calendar.startOfDay(for: .now))!
    }

    @Test func defaultLogRangeIsLast30Days() throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let viewModel = MirrorViewModel()

        viewModel.configure(modelContext: modelContext)

        #expect(viewModel.logRange == .last30Days)
    }

    @Test func logDisplayStateIsEmptyInRangeWhenNoVisibleEventsExist() throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let viewModel = MirrorViewModel()

        modelContext.insert(makeEvent(kind: "system", timestamp: .now))
        try modelContext.save()

        viewModel.configure(modelContext: modelContext)

        #expect(viewModel.logDisplayState == .emptyInRange)
        #expect(viewModel.filteredGroupedEvents.isEmpty)
    }

    @Test func selectedFilterProducesEmptyAfterFilterWhenRangeStillHasLogs() throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let viewModel = MirrorViewModel()

        modelContext.insert(makeEvent(kind: "observation", timestamp: .now, summary: "today"))
        modelContext.insert(makeEvent(kind: "state", timestamp: daysAgo(45), summary: "old state"))
        try modelContext.save()

        viewModel.configure(modelContext: modelContext)
        viewModel.selectedFilterKind = "state"

        #expect(viewModel.logDisplayState == .emptyAfterFilter)
    }

    @Test func selectedFilterRemainsVisibleWhenCountDropsToZero() throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let viewModel = MirrorViewModel()

        modelContext.insert(makeEvent(kind: "observation", timestamp: .now, summary: "today"))
        modelContext.insert(makeEvent(kind: "state", timestamp: daysAgo(45), summary: "old state"))
        try modelContext.save()

        viewModel.configure(modelContext: modelContext)
        viewModel.selectedFilterKind = "state"

        let stateCount = viewModel.kindCounts.first { $0.kind == "state" }?.count
        #expect(stateCount == 0)
        #expect(viewModel.shouldShowLogFilters == true)
    }

    @Test func applyingWiderLogRangeLoadsOlderEvents() throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let viewModel = MirrorViewModel()

        modelContext.insert(makeEvent(kind: "observation", timestamp: .now, summary: "today"))
        modelContext.insert(makeEvent(kind: "state", timestamp: daysAgo(45), summary: "old state"))
        try modelContext.save()

        viewModel.configure(modelContext: modelContext)
        viewModel.applyLogRange(.last90Days)

        #expect(viewModel.logRange == .last90Days)
        #expect(viewModel.kindCounts.contains { $0.kind == "state" && $0.count == 1 })
        #expect(viewModel.logDisplayState == .ready)
    }

    @Test func refreshProjectionReloadsCurrentLogRangeAndStoresFreshness() async throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let viewModel = MirrorViewModel()
        let syncService = StubSyncService(freshness: .fresh)

        modelContext.insert(makeEvent(kind: "observation", timestamp: .now, summary: "today"))
        try modelContext.save()

        viewModel.configure(modelContext: modelContext)
        viewModel.applyLogRange(.last90Days)

        modelContext.insert(makeEvent(kind: "state", timestamp: daysAgo(45), summary: "older"))
        try modelContext.save()

        ProjectionFreshnessStore.current = .stale
        defer {
            ProjectionFreshnessStore.current = .fresh
        }

        let freshness = await viewModel.refreshProjection(using: syncService)

        #expect(freshness == .fresh)
        #expect(ProjectionFreshnessStore.current == .fresh)
        #expect(viewModel.isRefreshingProjection == false)
        #expect(viewModel.kindCounts.contains { $0.kind == "state" && $0.count == 1 })
    }
}

// MARK: - Metric Display Tests

@Suite("MetricDisplay")
struct MetricDisplayTests {
    @Test func recordUsesConfiguredUnitAndEstimatedMarker() {
        let entry = MetricEntry(key: "weight", value: 72.3, quality: .estimated)
        let config = NorthStarMetricConfig(
            key: "weight",
            label: "体重",
            type: .numeric,
            unit: "KG",
            deltaDirection: .decrease,
            scaleMax: nil,
            ratioDenominator: nil
        )

        let display = MetricDisplay.record(entry: entry, config: config)

        #expect(display.value == "72.3")
        #expect(display.unit == "KG")
        #expect(display.showsEstimatedBadge == true)
    }
}

// MARK: - BehaviorEvent Tests

@Suite("BehaviorEvent")
struct BehaviorEventTests {

    @Test func metricsDecoding() {
        let event = BehaviorEvent(
            id: "test",
            timestamp: .now,
            recordedAt: .now,
            kind: "observation",
            evidence: "test",
            tags: []
        )
        let entries = [
            MetricEntry(key: "weight", value: 72.3, quality: .reported),
            MetricEntry(key: "kcal", value: nil, quality: .missing),
        ]
        event.setMetrics(entries)

        let decoded = event.metrics
        #expect(decoded.count == 2)
        #expect(decoded[0].key == "weight")
        #expect(decoded[0].value == 72.3)
        #expect(decoded[0].quality == .reported)
        #expect(decoded[1].value == nil)
        #expect(decoded[1].quality == .missing)
    }

    @Test func contextRoundTrip() {
        let event = BehaviorEvent(
            id: "test",
            timestamp: .now,
            recordedAt: .now,
            kind: "state",
            evidence: "test",
            tags: []
        )
        event.setContext(["situation": "午休", "social": "alone"])

        let ctx = event.context
        #expect(ctx["situation"] == "午休")
        #expect(ctx["social"] == "alone")
    }

    @Test func kindLabel() {
        #expect(BehaviorEvent.kindLabels["observation"] == "行为")
        #expect(BehaviorEvent.kindLabels["state"] == "状态")
        #expect(BehaviorEvent.kindLabels["nonexistent"] == nil)
    }

    @Test func hiddenKinds() {
        #expect(BehaviorEvent.hiddenKinds.contains("system"))
    }
}

// MARK: - ProfileInfoSection Label Mapping

@Suite("ProfileInfoSection")
struct ProfileInfoSectionTests {

    @Test func knownKeyMapping() {
        // 直接测试 static dict
        let labels = ProfileInfoSection.keyLabels
        #expect(labels["name"] == "称呼")
        #expect(labels["goal"] == "目标")
    }

    @Test func unknownKeyFallback() {
        let labels = ProfileInfoSection.keyLabels
        #expect(labels["unknown_field"] == nil)
    }
}

// MARK: - Runtime Contract Tests

@MainActor
@Suite("RuntimeContract")
struct RuntimeContractTests {
    private func fixtureURL(named name: String) -> URL {
        sharedStoreFixtureURL(named: name)
    }

    private func loadFixture(named name: String) throws -> [String: Any] {
        try loadSharedStoreFixture(named: name)
    }


    @Test func requestContextInjectsUserAndCorrelation() {
        let configurable = RequestContext.configurable(
            sessionType: .onboarding,
            preferredLanguage: "zh-Hans",
            correlationID: "corr_test"
        )

        #expect(configurable["session_type"] as? String == SessionType.onboarding.rawValue)
        #expect(configurable["user_id"] as? String == APIConfiguration.userID)
        #expect(configurable["correlation_id"] as? String == "corr_test")
        #expect(configurable["preferred_language"] as? String == "zh-Hans")
    }

    @Test func storeContractUnwrapsTextEnvelope() throws {
        let value: [String: Any] = [
            "version": "1",
            "content": ["line1", "line2"],
            "created_at": "2026-04-09T10:00:00Z",
            "modified_at": "2026-04-09T10:00:00Z",
        ]

        let text = try StoreContract.unwrapText(from: value)
        #expect(text == "line1\nline2")
    }

    @Test func storeContractUnwrapsJSONEnvelope() throws {
        let value: [String: Any] = [
            "version": "1",
            "content": ["{\"id\":\"chapter_1\",\"goal\":\"walk\"}"],
            "created_at": "2026-04-09T10:00:00Z",
            "modified_at": "2026-04-09T10:00:00Z",
        ]

        let json = try StoreContract.unwrapJSONDictionary(from: value)
        #expect(json["id"] as? String == "chapter_1")
        #expect(json["goal"] as? String == "walk")
    }

    @Test func storeContractLoadsSharedDashboardFixture() throws {
        let value = try loadFixture(named: "dashboard_config.value.json")
        let json = try StoreContract.unwrapJSONDictionary(from: value)
        #expect(json["fixture_type"] as? String == "dashboard_config")
    }

    @Test func storeContractBuildsInterventionsNamespace() {
        #expect(StoreContract.interventionsNamespace == [
            "voliti",
            APIConfiguration.userID,
            "interventions",
        ])
    }

    @Test func onboardingCompletionDependsOnlyOnStoreMarker() {
        #expect(CoachViewModel.shouldMarkOnboardingComplete(storeComplete: true) == true)
        #expect(CoachViewModel.shouldMarkOnboardingComplete(storeComplete: false) == false)
    }

    @Test func a2uiPayloadCapturesInterruptIDFromLangGraphEnvelope() throws {
        let payloadData = SSEClient.makeA2UIPayloadData(from: [
            "id": "interrupt_123",
            "value": [
                "type": "a2ui",
                "components": [],
                "layout": "three-quarter",
            ],
        ])

        #expect(payloadData != nil)
        let payload = try JSONDecoder().decode(A2UIPayload.self, from: try #require(payloadData))
        #expect(payload.interruptID == "interrupt_123")
    }

    @Test func resumeBodyIncludesInterruptID() throws {
        let body = LangGraphAPI.makeResumeBody(
            action: "submit",
            data: ["energy": 7],
            sessionType: .onboarding,
            preferredLanguage: "zh-Hans",
            correlationID: "corr_test",
            interruptID: "interrupt_123"
        )

        let command = try #require(body["command"] as? [String: Any])
        let resume = try #require(command["resume"] as? [String: Any])
        let config = try #require(body["config"] as? [String: Any])
        let configurable = try #require(config["configurable"] as? [String: Any])

        #expect(resume["interrupt_id"] as? String == "interrupt_123")
        #expect(configurable["correlation_id"] as? String == "corr_test")
        #expect(configurable["session_type"] as? String == SessionType.onboarding.rawValue)
    }
}

@Suite("OnboardingIntegration")
@MainActor
struct OnboardingIntegrationTests {
    private final class StubSyncService: StoreSyncing {
        private(set) var syncAllCallCount = 0
        private let storeComplete: Bool

        init(storeComplete: Bool) {
            self.storeComplete = storeComplete
        }

        func syncAll() async -> ProjectionFreshness {
            syncAllCallCount += 1
            return .fresh
        }

        func checkOnboardingComplete() async -> Bool {
            storeComplete
        }
    }

    @Test func storeSyncServiceReadsWrappedOnboardingMarkerFromSharedFixture() async throws {
        let modelContext = ModelContext(try makeInMemoryContainer())
        let fixture = try loadSharedStoreFixture(named: "profile_context.value.json")
        let expectedNamespace = StoreContract.userNamespace
        let expectedKey = StoreContract.profileContextKey

        let service = StoreSyncService(
            modelContext: modelContext,
            fetchStoreItem: { namespace, key in
                #expect(namespace == expectedNamespace)
                #expect(key == expectedKey)
                return fixture
            },
            searchStoreItems: { _ in [] }
        )

        let result = await service.checkOnboardingComplete()
        #expect(result == true)
    }

    @Test func onboardingSessionUsesDedicatedThreadAndMarksCompletionAfterSync() async throws {
        let modelContext = ModelContext(try makeInMemoryContainer())
        let syncService = StubSyncService(storeComplete: true)
        let viewModel = CoachViewModel()

        APIConfiguration.threadID = "coach-thread"
        APIConfiguration.onboardingThreadID = "onboarding-thread"
        UserDefaults.standard.set(false, forKey: "onboardingComplete")
        defer {
            APIConfiguration.threadID = nil
            APIConfiguration.onboardingThreadID = nil
            UserDefaults.standard.removeObject(forKey: "onboardingComplete")
        }

        viewModel.configure(
            modelContext: modelContext,
            sessionType: .onboarding,
            syncService: syncService
        )

        let threadID = try await viewModel.ensureCorrectThread()
        #expect(threadID == "onboarding-thread")

        await viewModel.postStreamSync()

        #expect(syncService.syncAllCallCount == 1)
        #expect(viewModel.onboardingComplete == true)
    }
}

@Suite("BackendIntegration")
@MainActor
struct BackendIntegrationTests {
    @Test func onboardingCompletionUsesLiveStoreProjection() async throws {
        guard ProcessInfo.processInfo.environment["VOLITI_E2E_BACKEND"] == "1" else {
            return
        }

        let modelContext = ModelContext(try makeInMemoryContainer())
        let api = LangGraphAPI()
        let fixture = try loadSharedStoreFixture(named: "profile_context.value.json")
        let viewModel = CoachViewModel()

        APIConfiguration.threadID = nil
        APIConfiguration.onboardingThreadID = nil
        UserDefaults.standard.set(false, forKey: "onboardingComplete")
        defer {
            APIConfiguration.threadID = nil
            APIConfiguration.onboardingThreadID = nil
            UserDefaults.standard.removeObject(forKey: "onboardingComplete")
        }

        viewModel.configure(modelContext: modelContext, sessionType: .onboarding)

        let threadID = try await viewModel.ensureCorrectThread()
        #expect(!threadID.isEmpty)
        #expect(APIConfiguration.onboardingThreadID == threadID)

        try await api.putStoreItem(
            namespace: StoreContract.userNamespace,
            key: StoreContract.profileContextKey,
            value: fixture
        )
        defer {
            Task {
                try? await api.deleteStoreItems(namespace: StoreContract.userNamespace)
            }
        }

        await viewModel.postStreamSync()

        #expect(viewModel.onboardingComplete == true)
    }
}

@MainActor
@Suite("StorePagination")
struct StorePaginationTests {
    @Test func requestBodyDataReadsFromHTTPBodyStream() throws {
        let payload = Data("{\"offset\":100}".utf8)
        var request = URLRequest(url: URL(string: "https://example.com")!)
        request.httpBodyStream = InputStream(data: payload)

        let body = try requestBodyData(from: request)

        #expect(body == payload)
    }

    @Test func mockSessionsKeepIndependentHandlers() async throws {
        let url = URL(string: "https://example.com/store/items/search")!

        let firstSession = makeMockSession { request in
            let response = HTTPURLResponse(
                url: try #require(request.url),
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data("first".utf8))
        }

        let secondSession = makeMockSession { request in
            let response = HTTPURLResponse(
                url: try #require(request.url),
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            return (response, Data("second".utf8))
        }

        async let firstResult = firstSession.data(from: url)
        async let secondResult = secondSession.data(from: url)
        let (firstData, secondData) = try await (firstResult.0, secondResult.0)

        #expect(String(decoding: firstData, as: UTF8.self) == "first")
        #expect(String(decoding: secondData, as: UTF8.self) == "second")
    }

    @Test func searchStoreItemsPaginatesPastFirstPage() async throws {
        let expectedFirstCount = 100
        let expectedSecondCount = 5
        let offsets = LockedRecorder<[Int]>([])
        let userNamespace = StoreContract.userNamespace

        let session = makeMockSession { request in
            let url = try #require(request.url)
            #expect(url.path == "/store/items/search")
            let bodyData = try requestBodyData(from: request)
            let body = try #require(bodyData)
            let json = try #require(JSONSerialization.jsonObject(with: body) as? [String: Any])
            let offset = try #require(json["offset"] as? Int)
            offsets.withValue { $0.append(offset) }

            let itemCount = offset == 0 ? expectedFirstCount : expectedSecondCount
            let items: [[String: Any]] = (0..<itemCount).map { index in
                ["key": "/ledger/item_\(offset + index)", "namespace": userNamespace]
            }
            let response = HTTPURLResponse(
                url: url,
                statusCode: 200,
                httpVersion: nil,
                headerFields: nil
            )!
            let data = try JSONSerialization.data(withJSONObject: ["items": items])
            return (response, data)
        }

        let api = LangGraphAPI(session: session)
        let items = try await api.searchStoreItems(namespace: userNamespace)

        #expect(items.count == expectedFirstCount + expectedSecondCount)
        #expect(offsets.snapshot() == [0, 100])
    }

    @Test func clearUserStoreDeletesAllReturnedItemsAcrossSubnamespaces() async throws {
        let expectedFirstCount = 100
        let expectedSecondCount = 3
        let offsets = LockedRecorder<[Int]>([])
        let deletedItems = LockedRecorder<Set<String>>([])
        let userNamespace = StoreContract.userNamespace

        let session = makeMockSession { request in
            let url = try #require(request.url)

            switch request.httpMethod {
            case "POST":
                #expect(url.path == "/store/items/search")
                let bodyData = try requestBodyData(from: request)
                let body = try #require(bodyData)
                let json = try #require(JSONSerialization.jsonObject(with: body) as? [String: Any])
                let offset = try #require(json["offset"] as? Int)
                offsets.withValue { $0.append(offset) }

                let itemCount = offset == 0 ? expectedFirstCount : expectedSecondCount
                let items: [[String: Any]] = (0..<itemCount).map { index in
                    let ordinal = offset + index
                    let subnamespace = ordinal.isMultiple(of: 2) ? "ledger" : "coping-plans"
                    return [
                        "key": "/\(subnamespace)/item_\(ordinal).json",
                        "namespace": userNamespace + [subnamespace],
                    ]
                }
                let response = HTTPURLResponse(
                    url: url,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: nil
                )!
                let data = try JSONSerialization.data(withJSONObject: ["items": items])
                return (response, data)

            case "DELETE":
                #expect(url.path == "/store/items")
                let bodyData = try requestBodyData(from: request)
                let body = try #require(bodyData)
                let json = try #require(JSONSerialization.jsonObject(with: body) as? [String: Any])
                let namespace = try #require(json["namespace"] as? [String])
                let key = try #require(json["key"] as? String)
                let token = namespace.joined(separator: "/") + "::" + key
                _ = deletedItems.withValue { $0.insert(token) }

                let response = HTTPURLResponse(
                    url: url,
                    statusCode: 204,
                    httpVersion: nil,
                    headerFields: nil
                )!
                return (response, Data())

            default:
                Issue.record("Unexpected method: \(request.httpMethod ?? "<nil>")")
                throw URLError(.badServerResponse)
            }
        }

        let api = LangGraphAPI(session: session)
        try await api.clearUserStore()

        let expectedDeletedItems: Set<String> = Set((0..<(expectedFirstCount + expectedSecondCount)).map { ordinal in
            let subnamespace = ordinal.isMultiple(of: 2) ? "ledger" : "coping-plans"
            let namespace = (userNamespace + [subnamespace]).joined(separator: "/")
            return namespace + "::" + "/\(subnamespace)/item_\(ordinal).json"
        })

        #expect(offsets.snapshot() == [0, 100])
        #expect(deletedItems.snapshot() == expectedDeletedItems)
    }
}

@Suite("ResetService")
@MainActor
struct ResetServiceTests {
    @Test func resetAllClearsProductStateWithoutTouchingSystemPermissions() async throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let previousUserID = APIConfiguration.userID
        modelContext.insert(ChatMessage(role: .assistant, textContent: "hello", threadID: "thread_1"))
        modelContext.insert(BehaviorEvent(timestamp: .now, kind: "state", evidence: "test"))
        try modelContext.save()

        APIConfiguration.threadID = "coach-thread"
        APIConfiguration.onboardingThreadID = "onboarding-thread"
        UserDefaults.standard.set(true, forKey: "onboardingComplete")
        UserDefaults.standard.set("zh-Hans", forKey: "preferredLanguage")
        UserDefaults.standard.set(true, forKey: "checkinReminderEnabled")
        UserDefaults.standard.set(true, forKey: ProjectionFreshness.userDefaultsKey)
        UserDefaults.standard.set(true, forKey: "notificationsAuthorized")

        defer {
            APIConfiguration.threadID = nil
            APIConfiguration.onboardingThreadID = nil
            UserDefaults.standard.removeObject(forKey: "onboardingComplete")
            UserDefaults.standard.removeObject(forKey: "preferredLanguage")
            UserDefaults.standard.removeObject(forKey: "checkinReminderEnabled")
            UserDefaults.standard.removeObject(forKey: ProjectionFreshness.userDefaultsKey)
            UserDefaults.standard.removeObject(forKey: "notificationsAuthorized")
        }

        var remoteClearCalled = false
        let warning = await ResetService.resetAll(
            modelContext: modelContext,
            clearRemoteStore: {
                remoteClearCalled = true
            }
        )
        let regeneratedUserID = APIConfiguration.userID

        let remainingMessages = try modelContext.fetch(FetchDescriptor<ChatMessage>())
        let remainingEvents = try modelContext.fetch(FetchDescriptor<BehaviorEvent>())

        #expect(warning == nil)
        #expect(remoteClearCalled == true)
        #expect(APIConfiguration.threadID == nil)
        #expect(APIConfiguration.onboardingThreadID == nil)
        #expect(regeneratedUserID != previousUserID)
        #expect(UserDefaults.standard.bool(forKey: "onboardingComplete") == false)
        #expect(UserDefaults.standard.object(forKey: "preferredLanguage") == nil)
        #expect(UserDefaults.standard.object(forKey: "checkinReminderEnabled") == nil)
        #expect(UserDefaults.standard.bool(forKey: ProjectionFreshness.userDefaultsKey) == false)
        #expect(UserDefaults.standard.bool(forKey: "notificationsAuthorized") == true)
        #expect(remainingMessages.isEmpty)
        #expect(remainingEvents.isEmpty)
    }

    @Test func resetAllRotatesLocalUserIdentityEvenWhenRemoteStoreClearFails() async throws {
        let container = try makeInMemoryContainer()
        let modelContext = ModelContext(container)
        let previousUserID = APIConfiguration.userID

        APIConfiguration.threadID = "coach-thread"
        APIConfiguration.onboardingThreadID = "onboarding-thread"

        defer {
            APIConfiguration.threadID = nil
            APIConfiguration.onboardingThreadID = nil
        }

        let warning = await ResetService.resetAll(
            modelContext: modelContext,
            clearRemoteStore: {
                throw URLError(.cannotConnectToHost)
            }
        )
        let regeneratedUserID = APIConfiguration.userID

        #expect(warning == "部分云端数据可能未完全清除")
        #expect(APIConfiguration.threadID == nil)
        #expect(APIConfiguration.onboardingThreadID == nil)
        #expect(regeneratedUserID != previousUserID)
    }
}

@Suite("ProjectionFreshness")
@MainActor
struct ProjectionFreshnessTests {
    private final class StubSyncService: StoreSyncing {
        private let freshness: ProjectionFreshness
        private let storeComplete: Bool

        init(freshness: ProjectionFreshness, storeComplete: Bool) {
            self.freshness = freshness
            self.storeComplete = storeComplete
        }

        func syncAll() async -> ProjectionFreshness {
            freshness
        }

        func checkOnboardingComplete() async -> Bool {
            storeComplete
        }
    }

    @Test func postStreamSyncMarksProjectionAsStaleWhenSyncFails() async throws {
        let modelContext = ModelContext(try makeInMemoryContainer())
        let viewModel = CoachViewModel()
        let staleSync = StubSyncService(freshness: .stale, storeComplete: false)

        ProjectionFreshnessStore.current = .fresh
        UserDefaults.standard.set(false, forKey: "onboardingComplete")
        defer {
            ProjectionFreshnessStore.current = .fresh
            UserDefaults.standard.removeObject(forKey: "onboardingComplete")
        }

        viewModel.configure(
            modelContext: modelContext,
            sessionType: .onboarding,
            syncService: staleSync
        )

        await viewModel.postStreamSync()

        #expect(ProjectionFreshnessStore.current == .stale)
        #expect(viewModel.onboardingComplete == false)
    }

    @Test func postStreamSyncClearsStaleProjectionAfterSuccessfulSync() async throws {
        let modelContext = ModelContext(try makeInMemoryContainer())
        let viewModel = CoachViewModel()
        let freshSync = StubSyncService(freshness: .fresh, storeComplete: true)

        ProjectionFreshnessStore.current = .stale
        UserDefaults.standard.set(false, forKey: "onboardingComplete")
        defer {
            ProjectionFreshnessStore.current = .fresh
            UserDefaults.standard.removeObject(forKey: "onboardingComplete")
        }

        viewModel.configure(
            modelContext: modelContext,
            sessionType: .onboarding,
            syncService: freshSync
        )

        await viewModel.postStreamSync()

        #expect(ProjectionFreshnessStore.current == .fresh)
        #expect(viewModel.onboardingComplete == true)
    }
}
