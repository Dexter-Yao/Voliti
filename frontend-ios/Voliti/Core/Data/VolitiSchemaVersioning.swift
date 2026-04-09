// ABOUTME: SwiftData 版本化 Schema 和迁移计划
// ABOUTME: V1 为基线快照，后续 schema 变更需新增 VersionedSchema + MigrationStage

import SwiftData

enum VolitiSchemaV1: VersionedSchema {
    static var versionIdentifier = Schema.Version(1, 0, 0)

    static var models: [any PersistentModel.Type] {
        [
            ChatMessage.self,
            BehaviorEvent.self,
            InterventionCard.self,
            Chapter.self,
            LifeSignPlan.self,
            DashboardConfig.self,
        ]
    }
}

enum VolitiMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] {
        [VolitiSchemaV1.self]
    }

    static var stages: [MigrationStage] { [] }
}
