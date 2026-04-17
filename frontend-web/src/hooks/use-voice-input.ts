// ABOUTME: Web 语音输入状态机
// ABOUTME: 负责录音、停止、转写、重试与资源清理，不直接管理聊天消息

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { transcribeVoiceBlob } from "@/lib/voice-transcription-client";
import {
  MAX_VOICE_RECORDING_MS,
  pickVoiceRecordingMimeType,
  type VoiceTranscriptionResult,
} from "@/lib/voice";

export type VoiceCaptureState = "idle" | "recording" | "transcribing" | "error";

interface UseVoiceInputOptions {
  disabled?: boolean;
  onDraftReady: (draft: VoiceTranscriptionResult) => void;
}

function stopStreamTracks(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}

function getVoiceErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    if (error.name === "NotAllowedError") {
      return "麦克风权限未开启，请先允许浏览器访问麦克风。";
    }
    if (error.name === "NotFoundError") {
      return "未检测到可用麦克风。";
    }
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return "语音输入暂时不可用，请稍后重试。";
}

export function useVoiceInput({
  disabled = false,
  onDraftReady,
}: UseVoiceInputOptions) {
  const [state, setState] = useState<VoiceCaptureState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const discardRecordingRef = useRef(false);
  const timeoutIdRef = useRef<number | null>(null);
  const lastBlobRef = useRef<Blob | null>(null);

  const clearRecordingTimeout = useCallback(() => {
    if (timeoutIdRef.current !== null) {
      window.clearTimeout(timeoutIdRef.current);
      timeoutIdRef.current = null;
    }
  }, []);

  const clearRecorder = useCallback(() => {
    recorderRef.current = null;
    chunksRef.current = [];
    discardRecordingRef.current = false;
    stopStreamTracks(mediaStreamRef.current);
    mediaStreamRef.current = null;
    clearRecordingTimeout();
  }, [clearRecordingTimeout]);

  const finishTranscription = useCallback(
    async (blob: Blob) => {
      setState("transcribing");
      setErrorMessage(null);
      lastBlobRef.current = blob;

      try {
        const draft = await transcribeVoiceBlob(blob);
        onDraftReady(draft);
        lastBlobRef.current = null;
        setState("idle");
      } catch (error) {
        const message = getVoiceErrorMessage(error);
        setErrorMessage(message);
        setState("error");
        toast.error("语音转写失败", {
          description: message,
        });
      }
    },
    [onDraftReady],
  );

  const stopRecording = useCallback(
    (options?: { discard?: boolean }) => {
      const recorder = recorderRef.current;
      if (!recorder || recorder.state === "inactive") return;

      discardRecordingRef.current = options?.discard ?? false;
      clearRecordingTimeout();
      recorder.stop();
    },
    [clearRecordingTimeout],
  );

  const retryTranscription = useCallback(async () => {
    if (!lastBlobRef.current) return;
    await finishTranscription(lastBlobRef.current);
  }, [finishTranscription]);

  const clearError = useCallback(() => {
    setErrorMessage(null);
    if (state === "error") {
      setState("idle");
    }
  }, [state]);

  const discardLastRecording = useCallback(() => {
    lastBlobRef.current = null;
    setErrorMessage(null);
    setState("idle");
  }, []);

  const beginRecording = useCallback(async () => {
    if (disabled || state === "recording" || state === "transcribing") return;

    if (
      typeof window === "undefined" ||
      typeof navigator === "undefined" ||
      !navigator.mediaDevices?.getUserMedia
    ) {
      const message = "当前浏览器不支持麦克风录音。";
      setErrorMessage(message);
      setState("error");
      toast.error("语音输入不可用", { description: message });
      return;
    }

    if (typeof MediaRecorder === "undefined") {
      const message = "当前浏览器不支持语音录制。";
      setErrorMessage(message);
      setState("error");
      toast.error("语音输入不可用", { description: message });
      return;
    }

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      mediaStreamRef.current = mediaStream;
      chunksRef.current = [];
      discardRecordingRef.current = false;

      const mimeType = pickVoiceRecordingMimeType(
        (candidate) => !candidate || MediaRecorder.isTypeSupported(candidate),
      );
      const recorder = mimeType
        ? new MediaRecorder(mediaStream, { mimeType })
        : new MediaRecorder(mediaStream);

      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const shouldDiscard = discardRecordingRef.current;
        const chunks = [...chunksRef.current];
        const outputMimeType = recorder.mimeType || mimeType || "audio/webm";

        clearRecorder();

        if (shouldDiscard) {
          setState("idle");
          return;
        }

        if (!chunks.length) {
          const message = "未采集到语音内容，请重试。";
          setErrorMessage(message);
          setState("error");
          toast.error("语音输入失败", { description: message });
          return;
        }

        void finishTranscription(new Blob(chunks, { type: outputMimeType }));
      };

      recorder.start();
      setErrorMessage(null);
      setState("recording");
      timeoutIdRef.current = window.setTimeout(() => {
        stopRecording();
      }, MAX_VOICE_RECORDING_MS);
    } catch (error) {
      clearRecorder();
      const message = getVoiceErrorMessage(error);
      setErrorMessage(message);
      setState("error");
      toast.error("语音输入失败", { description: message });
    }
  }, [clearRecorder, disabled, finishTranscription, state, stopRecording]);

  useEffect(() => {
    if (state !== "recording") return;

    const handlePointerEnd = () => {
      stopRecording();
    };

    window.addEventListener("pointerup", handlePointerEnd);
    window.addEventListener("pointercancel", handlePointerEnd);
    return () => {
      window.removeEventListener("pointerup", handlePointerEnd);
      window.removeEventListener("pointercancel", handlePointerEnd);
    };
  }, [state, stopRecording]);

  useEffect(() => {
    return () => {
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
      clearRecorder();
    };
  }, [clearRecorder]);

  return {
    state,
    errorMessage,
    isRecording: state === "recording",
    isTranscribing: state === "transcribing",
    hasError: state === "error",
    beginRecording,
    stopRecording,
    retryTranscription,
    clearError,
    discardLastRecording,
  };
}
