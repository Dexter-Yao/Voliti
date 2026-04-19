// ABOUTME: Voliti Store 契约辅助类型
// ABOUTME: 定义当前用户 namespace、正式 key 与文件封装值的统一解包规则

import Foundation

enum StoreContractError: Error {
    case invalidEnvelope
    case invalidJSON
}

enum StoreContract {
    static let namespacePrefix = "voliti"
    static let profileContextKey = "/profile/context.md"
    static let profileDashboardConfigKey = "/profile/dashboardConfig"
    static let chapterCurrentKey = "/chapter/current.json"
    static let timelineMarkersKey = "/timeline/markers.json"
    static let copingPlansPrefix = "/coping_plans/"

    static var userNamespace: [String] {
        [namespacePrefix, APIConfiguration.userID]
    }

    static var interventionsNamespace: [String] {
        userNamespace + ["interventions"]
    }

    static func unwrapText(from value: [String: Any]) throws -> String {
        guard let lines = value["content"] as? [String] else {
            throw StoreContractError.invalidEnvelope
        }
        return lines.joined(separator: "\n")
    }

    static func unwrapJSONDictionary(from value: [String: Any]) throws -> [String: Any] {
        let text = try unwrapText(from: value)
        guard let data = text.data(using: .utf8),
              let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw StoreContractError.invalidJSON
        }
        return json
    }

    static func unwrapJSONArray(from value: [String: Any]) throws -> [[String: Any]] {
        let text = try unwrapText(from: value)
        guard let data = text.data(using: .utf8),
              let json = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw StoreContractError.invalidJSON
        }
        return json
    }
}
