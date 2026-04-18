// ABOUTME: Web 语音转写 API
// ABOUTME: 接收浏览器录音文件，调用 DashScope Qwen ASR，并返回统一转写结果

import { NextResponse } from "next/server";

import { getAuthenticatedUser } from "@/lib/auth/server-user";
import { detectAudioDurationMs } from "@/lib/audio-duration";
import {
  isVoiceUploadMimeTypeSupported,
  MAX_VOICE_AUDIO_BYTES,
  parseDashScopeTranscriptionResponse,
  type VoiceTranscriptionResult,
} from "@/lib/voice";

export const runtime = "nodejs";

const DASHSCOPE_URL =
  "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation";
const DASHSCOPE_MODEL = "qwen3-asr-flash";

function jsonError(status: number, error: string) {
  return NextResponse.json({ error }, { status });
}

async function fileToDataUrl(file: File): Promise<string> {
  const buffer = Buffer.from(await file.arrayBuffer());
  const base64 = buffer.toString("base64");
  return `data:${file.type};base64,${base64}`;
}

async function requestDashScopeTranscription(
  audioDataUrl: string,
): Promise<VoiceTranscriptionResult> {
  const apiKey = process.env.DASHSCOPE_API_KEY;
  if (!apiKey) {
    throw new Error("服务器未配置 DASHSCOPE_API_KEY。");
  }

  const response = await fetch(DASHSCOPE_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: DASHSCOPE_MODEL,
      input: {
        messages: [
          { role: "system", content: [{ text: "" }] },
          { role: "user", content: [{ audio: audioDataUrl }] },
        ],
      },
      parameters: {
        asr_options: {
          enable_itn: false,
        },
      },
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    const error =
      payload?.message ??
      payload?.error?.message ??
      "DashScope 语音转写请求失败。";
    throw new Error(error);
  }

  return parseDashScopeTranscriptionResponse(payload, {
    sourceDurationMs: null,
    model: DASHSCOPE_MODEL,
  });
}

export async function POST(request: Request) {
  try {
    const user = await getAuthenticatedUser();
    if (!user) {
      return jsonError(401, "请先登录后再继续。");
    }

    const formData = await request.formData();
    const audio = formData.get("audio");

    if (!(audio instanceof File)) {
      return jsonError(400, "缺少语音文件。");
    }
    if (!audio.type || !isVoiceUploadMimeTypeSupported(audio.type)) {
      return jsonError(415, "当前语音格式暂不支持。");
    }
    if (audio.size <= 0) {
      return jsonError(400, "语音文件为空。");
    }
    if (audio.size > MAX_VOICE_AUDIO_BYTES) {
      return jsonError(413, "语音文件过大，请缩短录音后重试。");
    }

    const sourceDurationMs = await detectAudioDurationMs(audio);
    const audioDataUrl = await fileToDataUrl(audio);
    const draft = await requestDashScopeTranscription(audioDataUrl);

    return NextResponse.json({
      ...draft,
      sourceDurationMs,
    });
  } catch (error) {
    const message =
      error instanceof Error && error.message.trim()
        ? error.message
        : "语音转写失败，请稍后重试。";
    return jsonError(500, message);
  }
}
