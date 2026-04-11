// ABOUTME: Mirror 日志区范围选择 sheet，承载预设范围与自定义日期应用流程
// ABOUTME: 预设范围单击即生效，自定义仅在显式应用后生效

import SwiftUI

struct MirrorLogRangeSheet: View {
    let currentRange: MirrorLogRange
    let hasChapter: Bool
    let onSelectRange: (MirrorLogRange) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var mode: Mode = .presets
    @State private var customStartDate = Calendar.current.startOfDay(for: .now)
    @State private var customEndDate = Calendar.current.startOfDay(for: .now)
    @State private var customErrorMessage: String?

    private enum Mode {
        case presets
        case custom
    }

    var body: some View {
        NavigationStack {
            Group {
                switch mode {
                case .presets:
                    presetList
                case .custom:
                    customRangeForm
                }
            }
            .accessibilityIdentifier("mirror.logRangeSheet")
            .navigationTitle(mode == .presets ? "日志范围" : "自定义范围")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    if mode == .custom {
                        Button("返回") {
                            customErrorMessage = nil
                            mode = .presets
                        }
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                if case let .custom(startDate, endDate) = currentRange {
                    customStartDate = startDate
                    customEndDate = endDate
                }
            }
        }
    }

    private var presetList: some View {
        List {
            presetButton("近7天", range: .last7Days)
            presetButton("近30天", range: .last30Days)
            presetButton("近90天", range: .last90Days)

            Button {
                onSelectRange(.chapter)
                dismiss()
            } label: {
                HStack {
                    Text("本篇章")
                    Spacer()
                    if currentRange == .chapter {
                        Image(systemName: "checkmark")
                            .foregroundStyle(StarpathTokens.copper)
                    }
                }
            }
            .disabled(!hasChapter)
            .accessibilityIdentifier("mirror.logRange.chapter")

            if !hasChapter {
                Text("当前尚无篇章，暂不可按篇章查看")
                    .starpathSans(size: StarpathTokens.fontSizeSM)
                    .foregroundStyle(StarpathTokens.obsidian40)
            }

            Button {
                customErrorMessage = nil
                mode = .custom
            } label: {
                HStack {
                    Text("自定义")
                    Spacer()
                    if case .custom = currentRange {
                        Image(systemName: "checkmark")
                            .foregroundStyle(StarpathTokens.copper)
                    }
                }
            }
            .accessibilityIdentifier("mirror.logRange.custom")
        }
    }

    private var customRangeForm: some View {
        Form {
            DatePicker(
                "开始日期",
                selection: $customStartDate,
                displayedComponents: .date
            )

            DatePicker(
                "结束日期",
                selection: $customEndDate,
                in: ...Calendar.current.startOfDay(for: .now),
                displayedComponents: .date
            )

            if let customErrorMessage {
                Text(customErrorMessage)
                    .starpathSans(size: StarpathTokens.fontSizeSM)
                    .foregroundStyle(StarpathTokens.riskRed)
            }

            Button("应用") {
                applyCustomRange()
            }
            .accessibilityIdentifier("mirror.logRange.custom.apply")
        }
    }

    private func presetButton(_ title: String, range: MirrorLogRange) -> some View {
        Button {
            onSelectRange(range)
            dismiss()
        } label: {
            HStack {
                Text(title)
                Spacer()
                if currentRange == range {
                    Image(systemName: "checkmark")
                        .foregroundStyle(StarpathTokens.copper)
                }
            }
        }
        .accessibilityIdentifier("mirror.logRange.\(range.storageValue)")
    }

    private func applyCustomRange() {
        do {
            let range = try MirrorLogRange.validatedCustom(
                startDate: customStartDate,
                endDate: customEndDate,
                today: .now
            )
            onSelectRange(range)
            dismiss()
        } catch MirrorLogRangeError.endBeforeStart {
            customErrorMessage = "结束日期不能早于开始日期"
        } catch MirrorLogRangeError.endAfterToday {
            customErrorMessage = "结束日期不能晚于今天"
        } catch {
            customErrorMessage = "无法应用该日期范围"
        }
    }
}
