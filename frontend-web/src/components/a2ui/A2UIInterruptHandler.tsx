// ABOUTME: A2UI 中断处理器，检测 LangGraph interrupt 并渲染 Drawer
// ABOUTME: 处理 submit/reject/skip 三种 action 的 resume 和网络错误恢复

"use client";

import { useState, useCallback, useMemo } from "react";
import { useStreamContext } from "@/providers/Stream";
import { isA2UIPayload, type A2UIPayload, type A2UIResponse } from "@/lib/a2ui";
import { A2UIDrawer } from "./A2UIDrawer";
import { toast } from "sonner";

export function A2UIInterruptHandler() {
  const stream = useStreamContext();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 从 stream.interrupt 中提取 A2UI payload
  const a2uiPayload = useMemo((): A2UIPayload | null => {
    const interrupt = stream.interrupt;
    if (!interrupt) return null;

    // interrupt 可能是数组或 {value} 包装
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

  const resumeWithAction = useCallback(
    async (action: A2UIResponse["action"], data: Record<string, unknown> = {}) => {
      setIsSubmitting(true);
      try {
        const response: A2UIResponse = {
          action,
          interrupt_id: interruptId,
          data: action === "submit" ? data : {},
        };

        stream.submit(undefined, {
          command: {
            resume: response,
          },
        });
      } catch (error) {
        console.error("A2UI resume failed:", error);

        // 网络失败：显示 banner，fallback resume 让 Coach 知道数据没收到
        toast.error("Network error. Coach has been notified.", {
          richColors: true,
          closeButton: true,
        });

        try {
          const fallbackResponse: A2UIResponse = {
            action: "skip",
            interrupt_id: interruptId,
            data: { _network_failure: true },
          };
          stream.submit(undefined, {
            command: {
              resume: fallbackResponse,
            },
          });
        } catch {
          // 连 fallback 也失败了，Thread 可能卡住
          toast.error("Connection lost. Please refresh the page.", {
            richColors: true,
            closeButton: true,
          });
        }
      } finally {
        setIsSubmitting(false);
      }
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
    // 不能直接关闭 Drawer，必须先 resume 否则 Thread 卡死
    // 关闭等同于 skip
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
