// ABOUTME: Metaphor Collaboration · 景深镜头（前景 verbatim · 后景 Clean Language 问题）
// ABOUTME: ProtocolPrompt.observation 渲染为前景 34px；.question 渲染为后景 15px muted

"use client";

import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import type { InterventionLayoutProps } from "./types";
import { SignatureStrip } from "./SignatureStrip";
import { InterventionSubmitButton } from "./InterventionSubmitButton";
import { findFirstByKind } from "./slot-mapping";
import { useCmdEnterSubmit } from "@/hooks/useCmdEnterSubmit";

export function MetaphorLayout({
  components,
  isSubmitting,
  onSubmit,
}: InterventionLayoutProps) {
  const proto = useMemo(
    () => findFirstByKind(components, "protocol_prompt"),
    [components],
  );
  const input = useMemo(
    () => findFirstByKind(components, "text_input"),
    [components],
  );

  const [value, setValue] = useState(input?.value ?? "");

  const handleSubmit = useCallback(() => {
    if (!input) {
      onSubmit({});
      return;
    }
    onSubmit({ [input.key]: value });
  }, [input, value, onSubmit]);

  useCmdEnterSubmit(handleSubmit, isSubmitting);

  return (
    <div className="flex h-full flex-col">
      {/* Canvas · 居中 */}
      <div className="flex flex-1 flex-col justify-center overflow-y-auto px-8 py-12">
        <div className="mx-auto flex w-full max-w-[720px] flex-col gap-6">
          {/* 前景 · verbatim */}
          {proto ? (
            <motion.p
              className="font-serif-coach italic leading-snug"
              style={{
                fontSize: "34px",
                color: "var(--obsidian)",
                letterSpacing: "-0.3px",
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <span style={{ color: "var(--copper)", fontSize: "40px" }}>
                &ldquo;
              </span>
              {proto.observation}
              <span style={{ color: "var(--copper)", fontSize: "40px" }}>
                &rdquo;
              </span>
            </motion.p>
          ) : null}

          {/* 后景 · 问题 */}
          {proto ? (
            <motion.div
              className="flex flex-col gap-2"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 1.1 }}
            >
              <span
                className="text-[10px] uppercase"
                style={{
                  fontFamily: "JetBrains Mono, ui-monospace, monospace",
                  letterSpacing: "2px",
                  color: "var(--copper)",
                  opacity: 0.7,
                }}
              >
                COACH · 镜内
              </span>
              <p
                className="font-serif-coach italic leading-relaxed"
                style={{
                  fontSize: "15px",
                  color: "rgba(26,24,22,0.6)",
                  maxWidth: "520px",
                }}
              >
                {proto.question}
              </p>
            </motion.div>
          ) : null}

          {/* 输入区 */}
          {input ? (
            <motion.div
              className="flex flex-col"
              style={{
                borderTop: "1px solid rgba(26,24,22,0.1)",
                paddingTop: "16px",
                marginTop: "32px",
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 1.8 }}
            >
              <textarea
                className="font-serif-coach resize-none bg-transparent outline-none"
                style={{
                  fontSize: "16px",
                  minHeight: "80px",
                  color: "var(--obsidian)",
                }}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={input.placeholder || "……"}
              />
            </motion.div>
          ) : null}
        </div>
      </div>

      <SignatureStrip
        hint="拒绝 · Cmd+Enter 继续"
        actions={
          <InterventionSubmitButton
            label="继续"
            submittingLabel="继续中…"
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        }
      />
    </div>
  );
}
