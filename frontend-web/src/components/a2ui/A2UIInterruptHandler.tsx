// ABOUTME: A2UI 中断处理器，检测 LangGraph interrupt 并渲染 Drawer
// ABOUTME: 处理 submit/reject/skip 三种 action 的 resume；监听 stream.error 做错误恢复

"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useStreamContext } from "@/providers/Stream";
import { extractA2UIPayload, extractInterruptId, type A2UIPayload, type A2UIResponse } from "@/lib/a2ui";
import { A2UIDrawer } from "./A2UIDrawer";
import { toast } from "sonner";
import { SESSION_TYPE_COACHING, type SessionType } from "@/lib/thread-utils";
import { buildSubmitConfig } from "@/lib/stream-config";

export function A2UIInterruptHandler({
  sessionType = SESSION_TYPE_COACHING,
}: {
  sessionType?: SessionType;
}) {
  const stream = useStreamContext();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pendingResumeRef = useRef(false);

  const a2uiPayload = useMemo(
    (): A2UIPayload | null => extractA2UIPayload(stream.interrupt),
    [stream.interrupt],
  );

  const interruptId = useMemo(
    () => extractInterruptId(stream.interrupt),
    [stream.interrupt],
  );

  const submitConfig = useMemo(
    () => buildSubmitConfig(sessionType),
    [sessionType],
  );

  useEffect(() => {
    if (!stream.error || !pendingResumeRef.current) return;
    pendingResumeRef.current = false;
    setIsSubmitting(false);

    toast.error("网络错误，教练已收到通知", {
      richColors: true,
      closeButton: true,
    });

    const fallbackResponse: A2UIResponse = {
      action: "skip",
      interrupt_id: interruptId,
      data: {},
      reason: null,
    };
    stream.submit(undefined, {
      config: submitConfig,
      command: { resume: fallbackResponse },
    });
  }, [stream.error, stream, interruptId, submitConfig]);

  useEffect(() => {
    if (!stream.interrupt && pendingResumeRef.current) {
      pendingResumeRef.current = false;
      setIsSubmitting(false);
    }
  }, [stream.interrupt]);

  const resumeWithAction = useCallback(
    (action: A2UIResponse["action"], data: Record<string, unknown> = {}, reason: string | null = null) => {
      setIsSubmitting(true);
      pendingResumeRef.current = true;

      const response: A2UIResponse = {
        action,
        interrupt_id: interruptId,
        data: action === "submit" ? data : {},
        reason: action === "reject" ? reason : null,
      };

      stream.submit(undefined, {
        config: submitConfig,
        command: { resume: response },
      });
    },
    [stream, interruptId, submitConfig],
  );

  const handleSubmit = useCallback(
    (data: Record<string, unknown>) => resumeWithAction("submit", data),
    [resumeWithAction],
  );

  const handleReject = useCallback(
    (reason: string) => resumeWithAction("reject", {}, reason || null),
    [resumeWithAction],
  );

  const handleSkip = useCallback(
    () => resumeWithAction("skip"),
    [resumeWithAction],
  );

  const handleClose = useCallback(() => {
    if (!isSubmitting) {
      resumeWithAction("skip");
    }
  }, [isSubmitting, resumeWithAction]);

  return (
    <A2UIDrawer
      payload={a2uiPayload}
      isSubmitting={isSubmitting}
      onSubmit={handleSubmit}
      onReject={handleReject}
      onSkip={handleSkip}
      onClose={handleClose}
    />
  );
}
