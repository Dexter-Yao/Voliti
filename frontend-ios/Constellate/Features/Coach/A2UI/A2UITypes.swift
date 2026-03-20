// ABOUTME: A2UI 协议类型定义，精确映射 backend/src/constellate/a2ui.py
// ABOUTME: 8 种组件类型 + Payload + Response，通过 kind 字段 discriminate

import Foundation

// MARK: - Select Option

struct SelectOption: Codable, Sendable, Hashable {
    let label: String
    let value: String
}

// MARK: - Component Types

enum A2UIComponent: Codable, Sendable {
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

    func encode(to encoder: Encoder) throws {
        switch self {
        case .text(let d): try d.encode(to: encoder)
        case .image(let d): try d.encode(to: encoder)
        case .protocolPrompt(let d): try d.encode(to: encoder)
        case .slider(let d): try d.encode(to: encoder)
        case .textInput(let d): try d.encode(to: encoder)
        case .numberInput(let d): try d.encode(to: encoder)
        case .select(let d): try d.encode(to: encoder)
        case .multiSelect(let d): try d.encode(to: encoder)
        }
    }

    /// 输入组件的 name（用于收集响应数据）
    var inputName: String? {
        switch self {
        case .slider(let d): d.name
        case .textInput(let d): d.name
        case .numberInput(let d): d.name
        case .select(let d): d.name
        case .multiSelect(let d): d.name
        case .text, .image, .protocolPrompt: nil
        }
    }

    /// 是否为输入组件
    var isInput: Bool { inputName != nil }

    /// 是否为 protocol_prompt
    var isProtocolPrompt: Bool {
        if case .protocolPrompt = self { return true }
        return false
    }
}

// MARK: - Display Components

struct TextComponentData: Codable, Sendable {
    let kind: String
    let content: String
}

struct ImageComponentData: Codable, Sendable {
    let kind: String
    let src: String
    let alt: String?
}

struct ProtocolPromptData: Codable, Sendable {
    let kind: String
    let observation: String
    let question: String
}

// MARK: - Input Components

struct SliderData: Codable, Sendable {
    let kind: String
    let name: String
    let label: String
    let min: Int?
    let max: Int?
    let step: Int?
    let value: Int?
}

struct TextInputData: Codable, Sendable {
    let kind: String
    let name: String
    let label: String
    let placeholder: String?
    let value: String?
}

struct NumberInputData: Codable, Sendable {
    let kind: String
    let name: String
    let label: String
    let unit: String?
    let value: Double?
}

struct SelectData: Codable, Sendable {
    let kind: String
    let name: String
    let label: String
    let options: [SelectOption]
    let value: String?
}

struct MultiSelectData: Codable, Sendable {
    let kind: String
    let name: String
    let label: String
    let options: [SelectOption]
    let value: [String]?
}

// MARK: - Payload & Response

struct A2UIPayload: Codable, Sendable, Identifiable {
    let type: String
    let components: [A2UIComponent]
    let layout: A2UILayout

    let id: String = UUID().uuidString

    /// 是否包含 protocol_prompt 组件
    var hasProtocolPrompt: Bool {
        components.contains { $0.isProtocolPrompt }
    }

    /// 是否包含输入组件
    var hasInputs: Bool {
        components.contains { $0.isInput }
    }
}

enum A2UILayout: String, Codable, Sendable {
    case half
    case threeQuarter = "three-quarter"
    case full
}

struct A2UIResponse: Codable, Sendable {
    let action: A2UIAction
    let data: [String: AnyCodable]

    init(action: A2UIAction, data: [String: Any] = [:]) {
        self.action = action
        self.data = data.mapValues { AnyCodable($0) }
    }
}

enum A2UIAction: String, Codable, Sendable {
    case submit
    case reject
    case skip
}

// MARK: - AnyCodable Helper

struct AnyCodable: Codable, Sendable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let int = try? container.decode(Int.self) { value = int }
        else if let double = try? container.decode(Double.self) { value = double }
        else if let string = try? container.decode(String.self) { value = string }
        else if let bool = try? container.decode(Bool.self) { value = bool }
        else if let array = try? container.decode([String].self) { value = array }
        else { value = "" }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let v as Int: try container.encode(v)
        case let v as Double: try container.encode(v)
        case let v as String: try container.encode(v)
        case let v as Bool: try container.encode(v)
        case let v as [String]: try container.encode(v)
        default: try container.encode("\(value)")
        }
    }
}
