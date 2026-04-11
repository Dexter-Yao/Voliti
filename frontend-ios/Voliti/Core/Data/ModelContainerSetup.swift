// ABOUTME: SwiftData ModelContainer 配置
// ABOUTME: MLP 阶段仅本地存储，后续启用 CloudKit 同步

import Foundation
import SwiftData

enum ModelContainerSetup {
    static func create() throws -> ModelContainer {
        let environment = ProcessInfo.processInfo.environment
        let isRunningTests = environment["XCTestConfigurationFilePath"] != nil
        let isRunningUITests = environment["VOLITI_UI_TEST_SCENARIO"] != nil
        let schema = Schema(versionedSchema: VolitiSchemaV1.self)
        let config = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: isRunningTests || isRunningUITests,
            cloudKitDatabase: .none
        )
        return try ModelContainer(
            for: schema,
            migrationPlan: VolitiMigrationPlan.self,
            configurations: [config]
        )
    }
}
