// ABOUTME: A2UI 组件渲染器，根据 kind 分发到对应 SwiftUI 视图
// ABOUTME: 管理所有输入组件的 form state，汇总提交响应

import SwiftUI

struct A2UIRenderer: View {
    let components: [A2UIComponent]
    var onSubmit: ([String: Any]) -> Void
    var onReject: () -> Void
    var onSkip: () -> Void

    @State private var sliderValues: [String: Double] = [:]
    @State private var textValues: [String: String] = [:]
    @State private var numberValues: [String: String] = [:]
    @State private var selectValues: [String: String] = [:]
    @State private var multiSelectValues: [String: [String]] = [:]
    @State private var decodedImages: [Int: UIImage] = [:]

    private var hasInputs: Bool {
        components.contains { $0.isInput }
    }

    var body: some View {
        VStack(spacing: StarpathTokens.spacingLG) {
            ForEach(Array(components.enumerated()), id: \.offset) { index, component in
                componentView(for: component, at: index)
            }

            Spacer()

            // 操作按钮
            if !components.contains(where: { $0.isProtocolPrompt }) {
                actionButtons
            }
        }
        .padding(StarpathTokens.spacingMD)
        .onAppear {
            initializeValues()
            preDecodeImages()
        }
    }

    // MARK: - Component Dispatch

    @ViewBuilder
    private func componentView(for component: A2UIComponent, at index: Int) -> some View {
        switch component {
        case .text(let data):
            Text(data.content)
                .starpathSerif()

        case .image:
            if let uiImage = decodedImages[index] {
                GeometryReader { geometry in
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFit()
                        .frame(maxHeight: geometry.size.height * 0.6)
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                }
            }

        case .protocolPrompt(let data):
            ProtocolPromptCard(
                observation: data.observation,
                question: data.question,
                onContinue: { onSubmit([:]) },
                onPause: { onSkip() }
            )

        case .slider(let data):
            SliderInput(
                config: data,
                value: binding(for: data.name, in: $sliderValues, default: Double(data.value ?? data.min ?? 1))
            )

        case .textInput(let data):
            A2UITextInput(
                config: data,
                value: binding(for: data.name, in: $textValues, default: data.value)
            )

        case .numberInput(let data):
            NumberInput(
                config: data,
                value: binding(for: data.name, in: $numberValues, default: data.value.map { String($0) } ?? "")
            )

        case .select(let data):
            SelectInput(
                config: data,
                value: binding(for: data.name, in: $selectValues, default: data.value)
            )

        case .multiSelect(let data):
            MultiSelectInput(
                config: data,
                values: multiSelectBinding(for: data.name, default: data.value)
            )
        }
    }

    // MARK: - Action Buttons

    @ViewBuilder
    private var actionButtons: some View {
        HStack(spacing: StarpathTokens.spacingSM) {
            ObsidianPill(label: "取消", style: .outline) {
                onReject()
            }

            if hasInputs {
                ObsidianPill(label: "提交", style: .filled) {
                    onSubmit(collectValues())
                }
            }
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Value Management

    private func initializeValues() {
        for component in components {
            switch component {
            case .slider(let d):
                sliderValues[d.name] = Double(d.value ?? d.min ?? 1)
            case .textInput(let d):
                textValues[d.name] = d.value
            case .numberInput(let d):
                numberValues[d.name] = d.value.map { String($0) } ?? ""
            case .select(let d):
                selectValues[d.name] = d.value
            case .multiSelect(let d):
                multiSelectValues[d.name] = d.value
            default:
                break
            }
        }
    }

    private func collectValues() -> [String: Any] {
        var result: [String: Any] = [:]
        for (key, val) in sliderValues { result[key] = Int(val) }
        for (key, val) in textValues where !val.isEmpty { result[key] = val }
        for (key, val) in numberValues where !val.isEmpty {
            result[key] = Double(val) ?? val
        }
        for (key, val) in selectValues where !val.isEmpty { result[key] = val }
        for (key, val) in multiSelectValues where !val.isEmpty { result[key] = val }
        return result
    }

    // MARK: - Bindings

    private func binding<T>(for key: String, in dict: Binding<[String: T]>, default defaultValue: T) -> Binding<T> {
        Binding(
            get: { dict.wrappedValue[key] ?? defaultValue },
            set: { dict.wrappedValue[key] = $0 }
        )
    }

    private func multiSelectBinding(for key: String, default defaultValue: [String]) -> Binding<[String]> {
        Binding(
            get: { multiSelectValues[key] ?? defaultValue },
            set: { multiSelectValues[key] = $0 }
        )
    }

    // MARK: - Image Pre-Decoding

    private func preDecodeImages() {
        for (index, component) in components.enumerated() {
            if case .image(let data) = component,
               data.src.hasPrefix("data:"),
               let imageData = Data.fromDataURL(data.src),
               let uiImage = UIImage(data: imageData) {
                decodedImages[index] = uiImage
            }
        }
    }
}
