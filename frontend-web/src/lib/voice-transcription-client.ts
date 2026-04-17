// ABOUTME: 浏览器侧语音转写客户端
// ABOUTME: 将录音 Blob 提交到 Web API，并还原为统一的转写结果对象

import {
  type VoiceTranscriptionResult,
  VOICE_TRANSCRIPTIONS_PATH,
} from "./voice";

export async function transcribeVoiceBlob(
  blob: Blob,
): Promise<VoiceTranscriptionResult> {
  const formData = new FormData();
  formData.set(
    "audio",
    blob,
    blob.type.includes("mp4") ? "voice-input.mp4" : "voice-input.webm",
  );

  const response = await fetch(VOICE_TRANSCRIPTIONS_PATH, {
    method: "POST",
    body: formData,
  });

  const payload = (await response.json()) as
    | VoiceTranscriptionResult
    | { error?: string };

  if (!response.ok) {
    const message =
      "error" in payload && typeof payload.error === "string"
        ? payload.error
        : "语音转写失败，请稍后重试。";
    throw new Error(message);
  }

  return payload as VoiceTranscriptionResult;
}
