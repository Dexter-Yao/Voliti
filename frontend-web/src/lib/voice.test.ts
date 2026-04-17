// ABOUTME: Web 语音输入契约测试
// ABOUTME: 锁定转写结果解析、录音格式选择、草稿合并与消息元数据边界

import { describe, expect, it } from "vitest";

import {
  applyVoiceTranscriptionToComposerDraft,
  buildVoiceMessageAdditionalKwargs,
  createEmptyComposerDraft,
  extractTranscriptText,
  mergeVoiceDraftText,
  parseDashScopeTranscriptionResponse,
  pickVoiceRecordingMimeType,
  updateComposerDraftText,
} from "./voice";

describe("voice helpers", () => {
  it("prefers webm opus when the recorder supports it", () => {
    expect(
      pickVoiceRecordingMimeType(
        (mimeType) => mimeType === "audio/webm;codecs=opus",
      ),
    ).toBe("audio/webm;codecs=opus");
  });

  it("falls back to mp4 when webm is unavailable", () => {
    expect(
      pickVoiceRecordingMimeType((mimeType) => mimeType === "audio/mp4"),
    ).toBe("audio/mp4");
  });

  it("appends a transcript under the existing draft", () => {
    expect(mergeVoiceDraftText("今天有点乱。", "刚刚又想吃夜宵")).toBe(
      "今天有点乱。\n\n刚刚又想吃夜宵",
    );
  });

  it("uses the transcript as the whole draft when the composer is empty", () => {
    expect(mergeVoiceDraftText("  ", "我刚开完会，脑子很累")).toBe(
      "我刚开完会，脑子很累",
    );
  });

  it("extracts transcript text from DashScope content blocks", () => {
    expect(
      extractTranscriptText({
        output: {
          choices: [
            {
              message: {
                content: [{ text: "欢迎与使用阿里云。" }],
              },
            },
          ],
        },
      }),
    ).toBe("欢迎与使用阿里云。");
  });

  it("parses a DashScope transcription response into a voice draft", () => {
    expect(
      parseDashScopeTranscriptionResponse(
        {
          output: {
            choices: [
              {
                message: {
                  annotations: [
                    { type: "audio_info", language: "zh", emotion: "neutral" },
                  ],
                  content: [{ text: "今天晚饭后又有点想加餐。" }],
                },
              },
            ],
          },
        },
        { sourceDurationMs: 18250, model: "qwen3-asr-flash" },
      ),
    ).toEqual({
      emotion: "neutral",
      language: "zh",
      model: "qwen3-asr-flash",
      provider: "qwen",
      sourceDurationMs: 18250,
      text: "今天晚饭后又有点想加餐。",
    });
  });

  it("writes text and confirmed voice metadata into a single empty composer draft", () => {
    expect(
      applyVoiceTranscriptionToComposerDraft(createEmptyComposerDraft(), {
        emotion: "neutral",
        language: "zh",
        model: "qwen3-asr-flash",
        provider: "qwen",
        sourceDurationMs: 18250,
        text: "今天晚饭后又有点想加餐。",
      }),
    ).toEqual({
      text: "今天晚饭后又有点想加餐。",
      voiceMetadata: {
        confirmed: true,
        emotion: "neutral",
        language: "zh",
        model: "qwen3-asr-flash",
        provider: "qwen",
        sourceDurationMs: 18250,
      },
    });
  });

  it("marks voice metadata unconfirmed when the composer already contains text", () => {
    expect(
      applyVoiceTranscriptionToComposerDraft(
        {
          text: "今天上午已经吃超了。",
          voiceMetadata: null,
        },
        {
          emotion: "neutral",
          language: "zh",
          model: "qwen3-asr-flash",
          provider: "qwen",
          sourceDurationMs: 18250,
          text: "刚刚又想加餐。",
        },
      ),
    ).toEqual({
      text: "今天上午已经吃超了。\n\n刚刚又想加餐。",
      voiceMetadata: {
        confirmed: false,
        emotion: "neutral",
        language: "zh",
        model: "qwen3-asr-flash",
        provider: "qwen",
        sourceDurationMs: 18250,
      },
    });
  });

  it("invalidates confirmed voice metadata when the user edits the draft", () => {
    expect(
      updateComposerDraftText(
        {
          text: "今天晚饭后又有点想加餐。",
          voiceMetadata: {
            confirmed: true,
            emotion: "neutral",
            language: "zh",
            model: "qwen3-asr-flash",
            provider: "qwen",
            sourceDurationMs: 18250,
          },
        },
        "今天晚饭后又有点想加餐，但我先喝水。",
      ),
    ).toEqual({
      text: "今天晚饭后又有点想加餐，但我先喝水。",
      voiceMetadata: {
        confirmed: false,
        emotion: "neutral",
        language: "zh",
        model: "qwen3-asr-flash",
        provider: "qwen",
        sourceDurationMs: 18250,
      },
    });
  });

  it("clears voice metadata when the composer text becomes empty", () => {
    expect(
      updateComposerDraftText(
        {
          text: "今天晚饭后又有点想加餐。",
          voiceMetadata: {
            confirmed: true,
            emotion: "neutral",
            language: "zh",
            model: "qwen3-asr-flash",
            provider: "qwen",
            sourceDurationMs: 18250,
          },
        },
        "   ",
      ),
    ).toEqual({
      text: "   ",
      voiceMetadata: null,
    });
  });

  it("builds message metadata for a confirmed voice draft", () => {
    expect(
      buildVoiceMessageAdditionalKwargs({
        confirmed: true,
        emotion: "neutral",
        language: "zh",
        model: "qwen3-asr-flash",
        provider: "qwen",
        sourceDurationMs: 18250,
        text: "今天晚饭后又有点想加餐。",
      }),
    ).toEqual({
      input_mode: "voice",
      voice: {
        confirmed: true,
        emotion: "neutral",
        language: "zh",
        model: "qwen3-asr-flash",
        provider: "qwen",
        source_duration_ms: 18250,
      },
    });
  });
});
