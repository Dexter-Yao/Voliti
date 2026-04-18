// ABOUTME: Future Self Dialogue · 三栏状态格式塔（记忆 / 通道 / 在场）
// ABOUTME: 槽位分派：TextComponent → 左栏，TextInputComponent → 中栏，ProtocolPromptComponent → 右栏

"use client";

import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import type { InterventionLayoutProps } from "./types";
import { SignatureStrip } from "./SignatureStrip";
import { InterventionSubmitButton } from "./InterventionSubmitButton";
import { findFirstByKind } from "./slot-mapping";
import { useCmdEnterSubmit } from "@/hooks/useCmdEnterSubmit";

export function FutureSelfLayout({
  components,
  isSubmitting,
  onSubmit,
}: InterventionLayoutProps) {
  // 槽位分派：按 kind 取首个匹配
  const memoryText = useMemo(
    () => findFirstByKind(components, "text"),
    [components],
  );
  const futureProto = useMemo(
    () => findFirstByKind(components, "protocol_prompt"),
    [components],
  );
  const replyInput = useMemo(
    () => findFirstByKind(components, "text_input"),
    [components],
  );

  const [replyValue, setReplyValue] = useState(replyInput?.value ?? "");

  const handleSubmit = useCallback(() => {
    if (!replyInput) {
      onSubmit({});
      return;
    }
    onSubmit({ [replyInput.key]: replyValue });
  }, [replyInput, replyValue, onSubmit]);

  useCmdEnterSubmit(handleSubmit, isSubmitting);

  return (
    <div className="flex h-full flex-col">
      {/* 三栏主体 */}
      <div className="grid flex-1 gap-8 overflow-hidden px-8 py-6 lg:grid-cols-[0.9fr_1.1fr_1.3fr] grid-cols-1">
        {/* 栏 1 · 回忆（褪色） */}
        <motion.div
          className="flex flex-col gap-4 pr-4"
          style={{
            opacity: 0.55,
            borderRight: "1px dashed rgba(26,24,22,0.1)",
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.55 }}
          transition={{ duration: 0.4, delay: 0.6 }}
        >
          <div className="flex flex-col gap-1">
            <span
              className="font-serif-coach italic leading-tight"
              style={{ fontSize: "24px", color: "rgba(26,24,22,0.6)" }}
            >
              04-17
            </span>
            <span
              className="text-[10px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "rgba(26,24,22,0.4)",
              }}
            >
              ← 过去 · 你说过
            </span>
          </div>
          <div className="mt-auto flex flex-col gap-2">
            <p
              className="font-serif-coach italic leading-relaxed"
              style={{ fontSize: "15px", color: "rgba(26,24,22,0.6)" }}
            >
              {memoryText
                ? `"${memoryText.text}"`
                : ""}
            </p>
          </div>
        </motion.div>

        {/* 栏 2 · 通道 */}
        <motion.div
          className="flex flex-col justify-center gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, delay: 1.4 }}
        >
          <div className="flex flex-col items-center gap-1">
            <span
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                fontSize: "18px",
                letterSpacing: "2px",
                color: "rgba(26,24,22,0.6)",
              }}
            >
              → 送达
            </span>
            <span
              className="text-[10px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "rgba(26,24,22,0.4)",
              }}
            >
              此刻 · 通道
            </span>
          </div>

          {replyInput ? (
            <>
              <span
                className="text-[10px] uppercase"
                style={{
                  fontFamily: "JetBrains Mono, ui-monospace, monospace",
                  letterSpacing: "2px",
                  color: "rgba(26,24,22,0.4)",
                }}
              >
                {replyInput.label || "你要送给 TA 的话"}
              </span>
              <textarea
                className="font-serif-coach resize-none bg-transparent leading-relaxed outline-none"
                value={replyValue}
                onChange={(e) => setReplyValue(e.target.value)}
                placeholder={replyInput.placeholder || "……"}
                style={{
                  fontSize: "16px",
                  minHeight: "120px",
                  borderBottom: "1px solid rgba(26,24,22,0.2)",
                  padding: "8px 0",
                  color: "var(--obsidian)",
                }}
              />
            </>
          ) : null}

          <div
            className="flex items-center justify-between"
            style={{
              fontFamily: "JetBrains Mono, ui-monospace, monospace",
              fontSize: "10px",
              letterSpacing: "1px",
              color: "rgba(26,24,22,0.4)",
            }}
          >
            <span>Cmd + Enter</span>
            <span style={{ color: "var(--copper)" }}>→ 送到一年后</span>
          </div>
        </motion.div>

        {/* 栏 3 · 在场 */}
        <motion.div
          className="flex flex-col justify-between gap-4 pl-4"
          style={{
            borderLeft: "3px solid var(--copper)",
            background:
              "linear-gradient(to right, rgba(184,115,51,0.04), transparent 40%)",
          }}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.8 }}
        >
          <div className="flex flex-col gap-1">
            <span
              className="font-serif-coach font-medium leading-tight"
              style={{ fontSize: "24px", color: "var(--copper)" }}
            >
              2027-04
            </span>
            <span
              className="text-[10px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "var(--copper)",
                opacity: 0.8,
              }}
            >
              一年后 →
            </span>
          </div>

          {futureProto ? (
            <motion.div
              className="flex flex-col gap-3"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 1.1 }}
            >
              {/* role banner */}
              <div
                className="flex items-center gap-2 text-[10px] uppercase"
                style={{
                  fontFamily: "JetBrains Mono, ui-monospace, monospace",
                  letterSpacing: "2px",
                  color: "var(--copper)",
                }}
              >
                <span>TA 正在对你说</span>
                <span
                  className="h-px flex-1"
                  style={{
                    background: "rgba(184,115,51,0.4)",
                    marginLeft: "8px",
                  }}
                  aria-hidden
                />
              </div>
              <p
                className="font-serif-coach leading-relaxed"
                style={{ fontSize: "13px", color: "rgba(26,24,22,0.6)" }}
              >
                {futureProto.observation}
              </p>
              <p
                className="font-serif-coach italic leading-relaxed"
                style={{
                  fontSize: "18px",
                  color: "var(--obsidian)",
                }}
              >
                <span style={{ color: "var(--copper)" }}>&ldquo;</span>
                {futureProto.question}
                <span style={{ color: "var(--copper)" }}>&rdquo;</span>
              </p>
              <span
                className="text-[10px]"
                style={{
                  fontFamily: "JetBrains Mono, ui-monospace, monospace",
                  letterSpacing: "1px",
                  color: "var(--copper)",
                  opacity: 0.8,
                }}
              >
                — 04-17 · 一年后的你
              </span>
            </motion.div>
          ) : null}
        </motion.div>
      </div>

      <SignatureStrip
        hint="拒绝 · 跳过"
        actions={
          <InterventionSubmitButton
            label="送达"
            submittingLabel="送达中…"
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        }
      />
    </div>
  );
}
