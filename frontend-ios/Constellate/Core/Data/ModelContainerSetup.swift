// ABOUTME: SwiftData ModelContainer 配置
// ABOUTME: MLP 阶段仅本地存储，后续启用 CloudKit 同步

import SwiftData

enum ModelContainerSetup {
    static func create() throws -> ModelContainer {
        let schema = Schema([
            ChatMessage.self,
            BehaviorEvent.self,
            InterventionCard.self,
            Chapter.self,
        ])
        let config = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            cloudKitDatabase: .none
        )
        return try ModelContainer(for: schema, configurations: [config])
    }
}
