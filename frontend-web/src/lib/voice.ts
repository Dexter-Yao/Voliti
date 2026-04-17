// ABOUTME: Web 语音输入共享契约与组合器辅助函数
// ABOUTME: 统一录音格式选择、转写响应解析、单一草稿真相与消息元数据结构

export const MAX_VOICE_RECORDING_MS = 90_000;
export const MAX_VOICE_AUDIO_BYTES = 10 * 1024 * 1024;
export const VOICE_TRANSCRIPTIONS_PATH = "/api/voice/transcriptions";

export const SUPPORTED_VOICE_UPLOAD_MIME_TYPES = [
  "audio/webm",
  "audio/webm;codecs=opus",
  "audio/mp4",
  "audio/mpeg",
  "audio/mp3",
  "audio/wav",
  "audio/x-wav",
  "audio/mpga",
  "audio/ogg",
  "audio/ogg;codecs=opus",
  "audio/aac",
] as const;

const RECORDER_MIME_TYPE_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
  "",
] as const;

type DashScopeMessageContentBlock = {
  text?: string;
};

type DashScopeAudioAnnotation = {
  type?: string;
  language?: string;
  emotion?: string;
};

type DashScopeTranscriptionResponse = {
  output?: {
    choices?: Array<{
      message?: {
        annotations?: DashScopeAudioAnnotation[];
        content?: DashScopeMessageContentBlock[];
      };
    }>;
  };
};

export interface VoiceTranscriptionResult {
  text: string;
  provider: "qwen";
  model: string;
  sourceDurationMs: number | null;
  language: string | null;
  emotion: string | null;
}

export interface VoiceMessageMetadata {
  provider: "qwen";
  model: string;
  sourceDurationMs: number | null;
  language: string | null;
  emotion: string | null;
  confirmed: boolean;
}

export interface ComposerDraft {
  text: string;
  voiceMetadata: VoiceMessageMetadata | null;
}

export function pickVoiceRecordingMimeType(
  isTypeSupported: (mimeType: string) => boolean,
): string {
  for (const mimeType of RECORDER_MIME_TYPE_CANDIDATES) {
    if (!mimeType || isTypeSupported(mimeType)) {
      return mimeType;
    }
  }
  return "";
}

export function isVoiceUploadMimeTypeSupported(mimeType: string): boolean {
  return SUPPORTED_VOICE_UPLOAD_MIME_TYPES.includes(
    mimeType as (typeof SUPPORTED_VOICE_UPLOAD_MIME_TYPES)[number],
  );
}

export function mergeVoiceDraftText(
  currentInput: string,
  transcript: string,
): string {
  const nextTranscript = transcript.trim();
  if (!nextTranscript) return currentInput;

  const previous = currentInput.trim();
  if (!previous) return nextTranscript;
  return `${previous}\n\n${nextTranscript}`;
}

export function createEmptyComposerDraft(): ComposerDraft {
  return {
    text: "",
    voiceMetadata: null,
  };
}

export function createVoiceMessageMetadata(
  transcription: VoiceTranscriptionResult,
  confirmed: boolean,
): VoiceMessageMetadata {
  return {
    provider: transcription.provider,
    model: transcription.model,
    sourceDurationMs: transcription.sourceDurationMs,
    language: transcription.language,
    emotion: transcription.emotion,
    confirmed,
  };
}

export function applyVoiceTranscriptionToComposerDraft(
  previous: ComposerDraft,
  transcription: VoiceTranscriptionResult,
): ComposerDraft {
  const nextText = mergeVoiceDraftText(previous.text, transcription.text);
  return {
    text: nextText,
    voiceMetadata: createVoiceMessageMetadata(
      transcription,
      previous.text.trim().length === 0,
    ),
  };
}

export function updateComposerDraftText(
  previous: ComposerDraft,
  text: string,
): ComposerDraft {
  if (!text.trim()) {
    return {
      text,
      voiceMetadata: null,
    };
  }
  if (!previous.voiceMetadata) {
    return {
      ...previous,
      text,
    };
  }
  return {
    text,
    voiceMetadata: {
      ...previous.voiceMetadata,
      confirmed: false,
    },
  };
}

export function extractTranscriptText(
  response: DashScopeTranscriptionResponse,
): string {
  const blocks = response.output?.choices?.[0]?.message?.content ?? [];
  return blocks
    .map((block) => block.text?.trim() ?? "")
    .filter(Boolean)
    .join("\n")
    .trim();
}

function extractAudioAnnotation(
  response: DashScopeTranscriptionResponse,
): DashScopeAudioAnnotation | null {
  const annotations = response.output?.choices?.[0]?.message?.annotations ?? [];
  return (
    annotations.find((annotation) => annotation.type === "audio_info") ?? null
  );
}

export function parseDashScopeTranscriptionResponse(
  response: DashScopeTranscriptionResponse,
  options: {
    sourceDurationMs: number | null;
    model: string;
  },
): VoiceTranscriptionResult {
  const text = extractTranscriptText(response);
  if (!text) {
    throw new Error("DashScope transcription response did not contain text");
  }

  const annotation = extractAudioAnnotation(response);
  return {
    text,
    provider: "qwen",
    model: options.model,
    sourceDurationMs: options.sourceDurationMs,
    language: annotation?.language ?? null,
    emotion: annotation?.emotion ?? null,
  };
}

export function buildVoiceMessageAdditionalKwargs(
  metadata: VoiceMessageMetadata,
) {
  return {
    input_mode: "voice",
    voice: {
      provider: metadata.provider,
      model: metadata.model,
      language: metadata.language,
      emotion: metadata.emotion,
      source_duration_ms: metadata.sourceDurationMs,
      confirmed: metadata.confirmed,
    },
  };
}
