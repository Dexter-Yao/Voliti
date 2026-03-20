// ABOUTME: HealthKit 数据管理器，读取体重、睡眠、步数
// ABOUTME: 渐进式权限请求，支持体重写回

import Foundation
import HealthKit
import Observation

@Observable
final class HealthKitManager {
    var isWeightAuthorized = false
    var isSleepAuthorized = false
    var isStepsAuthorized = false

    private let store = HKHealthStore()
    private var isAvailable: Bool { HKHealthStore.isHealthDataAvailable() }

    // MARK: - Authorization

    func requestWeightAccess() async throws {
        guard isAvailable else { return }
        let types: Set<HKSampleType> = [
            HKQuantityType(.bodyMass),
            HKQuantityType(.bodyFatPercentage),
        ]
        let shareTypes: Set<HKSampleType> = [HKQuantityType(.bodyMass)]
        try await store.requestAuthorization(toShare: shareTypes, read: types)
        isWeightAuthorized = store.authorizationStatus(for: HKQuantityType(.bodyMass)) == .sharingAuthorized
    }

    func requestSleepAccess() async throws {
        guard isAvailable else { return }
        let types: Set<HKObjectType> = [HKCategoryType(.sleepAnalysis)]
        try await store.requestAuthorization(toShare: [], read: types)
        isSleepAuthorized = store.authorizationStatus(for: HKCategoryType(.sleepAnalysis)) != .notDetermined
    }

    func requestStepsAccess() async throws {
        guard isAvailable else { return }
        let types: Set<HKObjectType> = [
            HKQuantityType(.stepCount),
            HKQuantityType(.activeEnergyBurned),
        ]
        try await store.requestAuthorization(toShare: [], read: types)
        isStepsAuthorized = store.authorizationStatus(for: HKQuantityType(.stepCount)) != .notDetermined
    }

    // MARK: - Read

    func latestWeight() async throws -> Double? {
        try await latestQuantity(.bodyMass, unit: .gramUnit(with: .kilo))
    }

    func sleepHoursLastNight() async throws -> Double? {
        let sleepType = HKCategoryType(.sleepAnalysis)
        let calendar = Calendar.current
        let now = Date()
        let startOfToday = calendar.startOfDay(for: now)
        let startOfYesterday = calendar.date(byAdding: .day, value: -1, to: startOfToday)!

        let predicate = HKQuery.predicateForSamples(
            withStart: startOfYesterday,
            end: startOfToday,
            options: .strictStartDate
        )

        let descriptor = HKSampleQueryDescriptor(
            predicates: [.categorySample(type: sleepType, predicate: predicate)],
            sortDescriptors: [SortDescriptor(\.startDate)]
        )

        let samples = try await descriptor.result(for: store)
        let totalSeconds = samples.reduce(0.0) { sum, sample in
            sum + sample.endDate.timeIntervalSince(sample.startDate)
        }
        return totalSeconds > 0 ? totalSeconds / 3600.0 : nil
    }

    func stepCountToday() async throws -> Int? {
        let stepType = HKQuantityType(.stepCount)
        let startOfDay = Calendar.current.startOfDay(for: .now)
        let predicate = HKQuery.predicateForSamples(
            withStart: startOfDay,
            end: .now,
            options: .strictStartDate
        )

        let descriptor = HKStatisticsQueryDescriptor(
            predicate: .quantitySample(type: stepType, predicate: predicate),
            options: .cumulativeSum
        )

        let result = try await descriptor.result(for: store)
        guard let sum = result?.sumQuantity() else { return nil }
        return Int(sum.doubleValue(for: .count()))
    }

    // MARK: - Write

    func writeWeight(_ kg: Double, date: Date = .now) async throws {
        let type = HKQuantityType(.bodyMass)
        let quantity = HKQuantity(unit: .gramUnit(with: .kilo), doubleValue: kg)
        let sample = HKQuantitySample(type: type, quantity: quantity, start: date, end: date)
        try await store.save(sample)
    }

    // MARK: - Helpers

    private func latestQuantity(_ identifier: HKQuantityTypeIdentifier, unit: HKUnit) async throws -> Double? {
        let type = HKQuantityType(identifier)
        let descriptor = HKSampleQueryDescriptor(
            predicates: [.quantitySample(type: type)],
            sortDescriptors: [SortDescriptor(\.startDate, order: .reverse)],
            limit: 1
        )

        let samples = try await descriptor.result(for: store)
        return samples.first?.quantity.doubleValue(for: unit)
    }
}
