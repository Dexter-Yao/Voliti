// ABOUTME: A2UI 协议类型定义，精确映射 backend/src/voliti/a2ui.py
// ABOUTME: 8 种组件类型 + Payload + Response，通过 kind 字段 discriminate

import Foundation

// MARK: - Select Option

struct SelectOption: Codable, Sendable, Hashable {
    let label: String
    let value: String
}

// MARK: - Component Types

enum A2UIComponent: Decodable, Sendable {
    case text(TextComponentData)
    case image(ImageComponentData)
    case protocolPrompt(ProtocolPromptData)
    case slider(SliderData)
    case textInput(TextInputData)
    case numberInput(NumberInputData)
    case select(SelectData)
    case multiSelect(MultiSelectData)

    // MARK: - Coding

    enum CodingKeys: String, CodingKey {
        case kind
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let kind = try container.decode(String.self, forKey: .kind)

        let singleContainer = try decoder.singleValueContainer()
        switch kind {
        case "text":
            self = .text(try singleContainer.decode(TextComponentData.self))
        case "image":
            self = .image(try singleContainer.decode(ImageComponentData.self))
        case "protocol_prompt":
            self = .protocolPrompt(try singleContainer.decode(ProtocolPromptData.self))
        case "slider":
            self = .slider(try singleContainer.decode(SliderData.self))
        case "text_input":
            self = .textInput(try singleContainer.decode(TextInputData.self))
        case "number_input":
            self = .numberInput(try singleContainer.decode(NumberInputData.self))
        case "select":
            self = .select(try singleContainer.decode(SelectData.self))
        case "multi_select":
            self = .multiSelect(try singleContainer.decode(MultiSelectData.self))
        default:
            throw DecodingError.dataCorruptedError(
                forKey: .kind, in: container,
                debugDescription: "Unknown component kind: \(kind)"
            )
        }
    }

    /// 输入组件的 key（用于收集响应数据）
    var inputKey: String? {
        switch self {
        case .slider(let d): d.key
        case .textInput(let d): d.key
        case .numberInput(let d): d.key
        case .select(let d): d.key
        case .multiSelect(let d): d.key
        case .text, .image, .protocolPrompt: nil
        }
    }

    /// 是否为输入组件
    var isInput: Bool { inputKey != nil }

    /// 是否为 protocol_prompt
    var isProtocolPrompt: Bool {
        if case .protocolPrompt = self { return true }
        return false
    }
}

// MARK: - Display Components

struct TextComponentData: Codable, Sendable {
    let kind: String
    let text: String
}

struct ImageComponentData: Codable, Sendable {
    let kind: String
    let src: String
    let alt: String
}

struct ProtocolPromptData: Codable, Sendable {
    let kind: String
    let observation: String
    let question: String
}

// MARK: - Input Components

struct SliderData: Codable, Sendable {
    let kind: String
    let key: String
    let label: String
    let min: Int?
    let max: Int?
    let step: Int?
    let value: Int?
}

struct TextInputData: Codable, Sendable {
    let kind: String
    let key: String
    let label: String
    let placeholder: String?
    let value: String
}

struct NumberInputData: Codable, Sendable {
    let kind: String
    let key: String
    let label: String
    let unit: String?
    let value: Double?
}

struct SelectData: Codable, Sendable {
    let kind: String
    let key: String
    let label: String
    let options: [SelectOption]
    let value: String
}

struct MultiSelectData: Codable, Sendable {
    let kind: String
    let key: String
    let label: String
    let options: [SelectOption]
    let value: [String]
}

// MARK: - Payload & Response

struct A2UIPayload: Decodable, Sendable, Identifiable {
    let type: String
    let components: [A2UIComponent]
    let layout: A2UILayout
    let metadata: [String: String]?

    /// 客户端生成的唯一标识，用于 SwiftUI 列表渲染，不参与 JSON 解码。
    var id: String = UUID().uuidString

    private enum CodingKeys: String, CodingKey {
        case type, components, layout, metadata
    }

    /// 是否包含 protocol_prompt 组件
    var hasProtocolPrompt: Bool {
        components.contains { $0.isProtocolPrompt }
    }

    /// 干预卡片 ID（用于从 Store 下载原图）
    var cardID: String? {
        metadata?["card_id"]
    }
}

enum A2UILayout: String, Codable, Sendable {
    case half
    case threeQuarter = "three-quarter"
    case full
}

