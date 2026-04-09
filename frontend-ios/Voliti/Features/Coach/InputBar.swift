// ABOUTME: 底部输入栏，支持文本、语音输入和图片附件
// ABOUTME: 四控件：附件(+) → 文本输入 → 语音(🎤) → 发送(→)

import SwiftUI
import PhotosUI
import os

struct InputBar: View {
    var onSend: (String, Data?) -> Void
    var disabled: Bool = false
    var suggestedReplies: [String] = []
    var onSuggestionTap: ((String) -> Void)?

    @State private var text = ""
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var imageData: Data?
    @State private var speechService = SpeechService()
    @FocusState private var isFocused: Bool

    var body: some View {
        VStack(spacing: StarpathTokens.spacingXS) {
            // Suggested replies
            if !suggestedReplies.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: StarpathTokens.spacingSM) {
                        ForEach(suggestedReplies, id: \.self) { reply in
                            Button {
                                onSuggestionTap?(reply)
                            } label: {
                                Text(reply)
                                    .starpathSans(size: 13)
                                    .fixedSize(horizontal: true, vertical: false)
                                    .foregroundStyle(StarpathTokens.obsidian)
                                    .padding(.horizontal, StarpathTokens.spacingSM)
                                    .padding(.vertical, StarpathTokens.spacingXS)
                                    .background(
                                        Capsule()
                                            .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                                    )
                            }
                        }
                    }
                    .padding(.horizontal, StarpathTokens.spacingMD)
                }
            }

            // 图片预览
            if let imageData, let uiImage = UIImage(data: imageData) {
                HStack {
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFit()
                        .frame(height: 60)
                        .clipShape(RoundedRectangle(cornerRadius: 4))

                    Button {
                        self.imageData = nil
                        self.selectedPhoto = nil
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(StarpathTokens.obsidian40)
                    }

                    Spacer()
                }
                .padding(.horizontal, StarpathTokens.spacingMD)
            }

            HStack(alignment: .bottom, spacing: StarpathTokens.spacingSM) {
                // 附件按钮
                PhotosPicker(selection: $selectedPhoto, matching: .images) {
                    Image(systemName: "plus")
                        .font(.system(size: StarpathTokens.fontSizeBase))
                        .foregroundStyle(StarpathTokens.obsidian40)
                        .frame(width: 44, height: 44)
                }

                // 文本输入
                TextField("", text: $text, axis: .vertical)
                    .lineLimit(1...5)
                    .starpathSans()
                    .padding(.horizontal, StarpathTokens.spacingSM)
                    .padding(.vertical, StarpathTokens.spacingSM)
                    .background(
                        RoundedRectangle(cornerRadius: 4)
                            .stroke(StarpathTokens.obsidian10, lineWidth: 1)
                    )
                    .focused($isFocused)

                // 语音 / 发送按钮
                if canSend {
                    sendButton
                } else {
                    micButton
                }
            }
            .padding(.horizontal, StarpathTokens.spacingMD)
            .padding(.vertical, StarpathTokens.spacingSM)
        }
        .background(StarpathTokens.parchment)
        .onChange(of: selectedPhoto) {
            Task {
                if let data = try? await selectedPhoto?.loadTransferable(type: Data.self),
                   let uiImage = UIImage(data: data) {
                    imageData = CameraService.compressImage(uiImage)
                }
            }
        }
        .onChange(of: speechService.transcript) {
            if !speechService.transcript.isEmpty {
                text = speechService.transcript
            }
        }
        .onAppear {
            speechService.requestAuthorization()
        }
    }

    private var canSend: Bool {
        !disabled && (!text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || imageData != nil)
    }

    private var sendButton: some View {
        Button {
            send()
        } label: {
            Image(systemName: "arrow.up")
                .font(.system(size: StarpathTokens.fontSizeSM, weight: .semibold))
                .foregroundStyle(StarpathTokens.parchment)
                .frame(width: 32, height: 32)
                .background(StarpathTokens.obsidian)
                .clipShape(Circle())
        }
        .frame(width: 44, height: 44)
    }

    private var micButton: some View {
        Button {
            toggleRecording()
        } label: {
            Image(systemName: speechService.isRecording ? "stop.circle.fill" : "mic")
                .font(.system(size: StarpathTokens.fontSizeBase))
                .foregroundStyle(speechService.isRecording ? StarpathTokens.riskRed : StarpathTokens.obsidian40)
                .frame(width: 44, height: 44)
        }
        .disabled(!speechService.isAuthorized || disabled)
    }

    private func send() {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty || imageData != nil else { return }
        onSend(trimmed.isEmpty ? "[图片]" : trimmed, imageData)
        text = ""
        imageData = nil
        selectedPhoto = nil
    }

    private func toggleRecording() {
        if speechService.isRecording {
            speechService.stopRecording()
        } else {
            do {
                try speechService.startRecording()
            } catch {
                Logger(subsystem: "com.voliti", category: "InputBar")
                    .error("Failed to start recording: \(error.localizedDescription)")
            }
        }
    }
}
