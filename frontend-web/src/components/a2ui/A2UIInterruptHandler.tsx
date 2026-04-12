// ABOUTME: A2UI 中断处理器，检测 LangGraph interrupt 并渲染 Drawer
// ABOUTME: 处理 submit/reject/skip 三种 action 的 resume；监听 stream.error 做错误恢复

"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useStreamContext } from "@/providers/Stream";
import { isA2UIPayload, type A2UIPayload, type A2UIResponse } from "@/lib/a2ui";
import { A2UIDrawer } from "./A2UIDrawer";
import { toast } from "sonner";

export function A2UIInterruptHandler() {
  const stream = useStreamContext();
  const [isSubmitting, setIsSubmitting] = useState(false);
  // 追踪是否正在等待 A2UI resume 完成
  const pendingResumeRef = useRef(false);

  // 从 stream.interrupt 中提取 A2UI payload
  const a2uiPayload = useMemo((): A2UIPayload | null => {
    const interrupt = stream.interrupt;
    if (!interrupt) return null;

    const rawValue = Array.isArray(interrupt)
      ? interrupt[0]?.value ?? interrupt[0]
      : (interrupt as { value?: unknown })?.value ?? interrupt;

    if (isA2UIPayload(rawValue)) return rawValue;
    return null;
  }, [stream.interrupt]);

  const interruptId = useMemo(() => {
    const interrupt = stream.interrupt;
    if (!interrupt) return null;
    if (Array.isArray(interrupt) && interrupt.length > 0) {
      return interrupt[0]?.id ?? interrupt[0]?.ns ?? null;
    }
    return (interrupt as { id?: string })?.id ?? null;
  }, [stream.interrupt]);

  // 监听 stream.error：如果 resume 发出后遇到错误，尝试 fallback
  useEffect(() => {
    if (!stream.error || !pendingResumeRef.current) return;
    pendingResumeRef.current = false;
    setIsSubmitting(false);

    toast.error("Network error. Coach has been notified.", {
      richColors: true,
      closeButton: true,
    });

    // Fallback: skip with _network_failure context
    const fallbackResponse: A2UIResponse = {
      action: "skip",
      interrupt_id: interruptId,
      data: { _network_failure: true },
    };
    stream.submit(undefined, {
      command: { resume: fallbackResponse },
    });
  }, [stream.error, stream, interruptId]);

  // interrupt 消失说明 resume 成功
  useEffect(() => {
    if (!stream.interrupt && pendingResumeRef.current) {
      pendingResumeRef.current = false;
      setIsSubmitting(false);
    }
  }, [stream.interrupt]);

  const resumeWithAction = useCallback(
    (action: A2UIResponse["action"], data: Record<string, unknown> = {}) => {
      setIsSubmitting(true);
      pendingResumeRef.current = true;

      const response: A2UIResponse = {
        action,
        interrupt_id: interruptId,
        data: action === "submit" ? data : {},
      };

      stream.submit(undefined, {
        command: { resume: response },
      });
    },
    [stream, interruptId],
  );

  const handleSubmit = useCallback(
    (data: Record<string, unknown>) => resumeWithAction("submit", data),
    [resumeWithAction],
  );

  const handleReject = useCallback(
    () => resumeWithAction("reject"),
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
