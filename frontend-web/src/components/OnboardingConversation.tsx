// ABOUTME: 全屏居中 onboarding 对话组件，每步一个问题占满全屏
// ABOUTME: A2UI 组件内联渲染（不弹出抽屉），Coach 问题居中显示

"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import type { Message } from "@langchain/langgraph-sdk";
import { useStreamContext } from "@/providers/Stream";
import { extractA2UIPayload, extractInterruptId, type A2UIPayload, type A2UIResponse } from "@/lib/a2ui";
import { A2UIRenderer } from "./a2ui/A2UIRenderer";
import { ONBOARDING_GREETING, SESSION_TYPE_ONBOARDING } from "@/lib/thread-utils";
import { buildSubmitConfig } from "@/lib/stream-config";
import { DO_NOT_RENDER_ID_PREFIX } from "@/lib/ensure-tool-responses";
import { toast } from "sonner";
import { useQueryState } from "nuqs";

interface OnboardingConversationProps {
  pendingName: string | null;
  onNameSent: () => void;
}

export function OnboardingConversation({
  pendingName,
  onNameSent,
}: OnboardingConversationProps) {
  const stream = useStreamContext();
  const [threadId] = useQueryState("threadId");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pendingResumeRef = useRef(false);
  const initialSent = useRef(false);

  const submitConfig = useMemo(
    () => buildSubmitConfig(SESSION_TYPE_ONBOARDING),
    [],
  );

  // --- 初始消息发送：greeting(AI) + name(human) ---
  useEffect(() => {
    if (!pendingName || initialSent.current || stream.isLoading) return;
    if (!threadId) return;
    initialSent.current = true;

    const messages: Message[] = [
      {
        id: uuidv4(),
        type: "ai",
        content: ONBOARDING_GREETING,
      } as Message,
      {
        id: uuidv4(),
        type: "human",
        content: [{ type: "text", text: pendingName }] as Message["content"],
      },
    ];

    stream.submit(
      { messages },
      { config: submitConfig, streamMode: ["values"], streamSubgraphs: true, streamResumable: true },
    );
    onNameSent();
    // stream/submitConfig/onNameSent 刻意排除：initialSent ref 保证单次触发
  }, [pendingName, threadId, stream.isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

  // --- A2UI interrupt 检测 ---
  const a2uiPayload = useMemo(
    (): A2UIPayload | null => extractA2UIPayload(stream.interrupt),
    [stream.interrupt],
  );

  const interruptId = useMemo(
    () => extractInterruptId(stream.interrupt),
    [stream.interrupt],
  );

  // --- A2UI resume ---
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

  // --- Error recovery ---
  useEffect(() => {
    if (!stream.error || !pendingResumeRef.current) return;
    pendingResumeRef.current = false;
    setIsSubmitting(false);
    toast.error("网络错误，教练已收到通知", { richColors: true, closeButton: true });
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

  // --- 提取最新 Coach 消息文本 ---
  const coachText = useMemo(() => {
    const extractText = (content: Message["content"]): string =>
      typeof content === "string"
        ? content
        : (content ?? [])
            .filter((c): c is { type: "text"; text: string } => c.type === "text")
            .map((c) => c.text)
            .join("");

    for (let i = stream.messages.length - 1; i >= 0; i--) {
      const m = stream.messages[i];
      if (m.type !== "ai") continue;
      if (m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX)) continue;
      const text = extractText(m.content);
      if (text.trim()) return text;
    }
    return null;
  }, [stream.messages]);

  // --- 自由文本输入（无 interrupt 时） ---
  const [freeInput, setFreeInput] = useState("");
  const showFreeInput = !stream.isLoading && !a2uiPayload && !!coachText && initialSent.current;

  const handleFreeSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = freeInput.trim();
      if (!trimmed || stream.isLoading) return;

      const msg: Message = {
        id: uuidv4(),
        type: "human",
        content: [{ type: "text", text: trimmed }] as Message["content"],
      };
      stream.submit(
        { messages: [msg] },
        { config: submitConfig, streamMode: ["values"], streamSubgraphs: true, streamResumable: true },
      );
      setFreeInput("");
    },
    [freeInput, stream, submitConfig],
  );

  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      {/* 内容区：居中 */}
      <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto px-8">
        <div className="w-full max-w-[480px]">
          {/* Coach 标识（首步） */}
          {!coachText && !stream.isLoading && (
            <div className="mb-5 text-center">
              <span className="font-mono-system text-xs uppercase tracking-[2px] text-[#B87333]">
                VOLITI COACH
              </span>
            </div>
          )}

          {/* 思考态 */}
          {stream.isLoading && !coachText && (
            <div className="flex flex-col items-center gap-4">
              <span className="font-mono-system text-xs uppercase tracking-[2px] text-[#B87333]">
                VOLITI COACH
              </span>
              <div className="h-[2px] w-24 animate-pulse rounded-full bg-[#B87333]/30" />
            </div>
          )}

          {/* Coach 问题文本 */}
          {coachText && (
            <p className="font-serif-coach text-center text-base leading-[1.7] text-[#1A1816] whitespace-pre-line">
              {coachText}
            </p>
          )}

          {/* 步骤间思考态 */}
          {stream.isLoading && coachText && (
            <div className="mt-6 flex justify-center">
              <div className="h-[2px] w-24 animate-pulse rounded-full bg-[#B87333]/30" />
            </div>
          )}

          {/* A2UI 内联渲染 */}
          {a2uiPayload && !stream.isLoading && (
            <div className="mt-8">
              <A2UIRenderer
                components={a2uiPayload.components}
                onSubmit={handleSubmit}
                onReject={handleReject}
                onSkip={handleSkip}
                isSubmitting={isSubmitting}
                mode="onboarding"
              />
            </div>
          )}
        </div>
      </div>

      {/* 底部自由文本输入区（无 A2UI interrupt 时） */}
      {showFreeInput && (
        <div className="border-t border-[#1A1816]/5 px-8 pb-8 pt-4">
          <form
            onSubmit={handleFreeSubmit}
            className="mx-auto w-full max-w-[480px]"
          >
            <textarea
              value={freeInput}
              onChange={(e) => setFreeInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  const form = (e.target as HTMLElement).closest("form");
                  form?.requestSubmit();
                }
              }}
              placeholder="写下你的想法…"
              rows={1}
              className="field-sizing-content w-full max-h-32 resize-none rounded-[4px] border border-[#1A1816]/10 bg-transparent px-4 py-3 text-sm text-[#1A1816] placeholder:text-[#1A1816]/30 focus:border-[#B87333] focus:outline-none focus:ring-1 focus:ring-[#B87333]"
            />
            <button
              type="submit"
              disabled={!freeInput.trim()}
              className="mt-3 w-full rounded-full bg-[#1A1816] px-4 py-3 text-sm font-medium text-[#F4F0E8] transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              确认
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
