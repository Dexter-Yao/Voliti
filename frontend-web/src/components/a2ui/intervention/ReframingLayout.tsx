// ABOUTME: Cognitive Reframing · 上层左右对比（verbatim = 隐含判决）+ 下层候选/自写
// ABOUTME: 字号 clamp + 最小硬锁；<880px 三栏降为纵向 + = 旋转 90°

"use client";

import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import type { InterventionLayoutProps } from "./types";
import { SignatureStrip } from "./SignatureStrip";
import { InterventionSubmitButton } from "./InterventionSubmitButton";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useCmdEnterSubmit } from "@/hooks/useCmdEnterSubmit";
import { findFirstByKind, findVerdictTextAfterProto } from "./slot-mapping";

export function ReframingLayout({
  components,
  isSubmitting,
  onSubmit,
}: InterventionLayoutProps) {
  const proto = useMemo(
    () => findFirstByKind(components, "protocol_prompt"),
    [components],
  );
  const verdict = useMemo(
    () => findVerdictTextAfterProto(components),
    [components],
  );
  const select = useMemo(
    () => findFirstByKind(components, "select"),
    [components],
  );
  const input = useMemo(
    () => findFirstByKind(components, "text_input"),
    [components],
  );

  const [selectedOption, setSelectedOption] = useState<string>(select?.value ?? "");
  const [writeOwn, setWriteOwn] = useState<string>(input?.value ?? "");

  const isNarrow = useMediaQuery("(max-width: 880px)");

  const handleSubmit = useCallback(() => {
    const data: Record<string, unknown> = {};
    if (select) data[select.key] = selectedOption;
    if (input) data[input.key] = writeOwn;
    onSubmit(data);
  }, [select, input, selectedOption, writeOwn, onSubmit]);

  useCmdEnterSubmit(handleSubmit, isSubmitting);

  return (
    <div className="flex h-full flex-col">
      {/* Canvas */}
      <div className="mx-auto flex w-full max-w-[1100px] flex-1 flex-col gap-6 overflow-y-auto p-8">
        {/* 上层：左右对比 */}
        <div
          className="grid gap-6"
          style={{
            gridTemplateColumns: isNarrow ? "1fr" : "1fr auto 1fr",
            alignItems: "stretch",
          }}
        >
          {/* 左：verbatim */}
          <motion.div
            className="flex flex-col gap-2 p-4"
            style={{
              backgroundColor: "rgba(26,24,22,0.05)",
              borderLeft: "2px solid rgba(26,24,22,0.2)",
              minWidth: 0,
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <span
              className="text-[10px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "rgba(26,24,22,0.4)",
              }}
            >
              你刚说的话
            </span>
            <p
              className="font-serif-coach intervention-reframing-verbatim italic leading-snug"
              style={{
                color: "var(--obsidian)",
                wordBreak: "break-word",
              }}
            >
              <span style={{ color: "rgba(26,24,22,0.4)" }}>&ldquo;</span>
              {proto?.observation ?? ""}
              <span style={{ color: "rgba(26,24,22,0.4)" }}>&rdquo;</span>
            </p>
          </motion.div>

          {/* 中：= */}
          <motion.div
            className="flex flex-col items-center justify-center gap-1 px-2"
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.8, ease: "easeOut" }}
          >
            <span
              className="intervention-reframing-equals font-medium leading-none"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                color: "var(--copper)",
                letterSpacing: "2px",
                transform: isNarrow ? "rotate(90deg)" : undefined,
              }}
              aria-hidden
            >
              =
            </span>
            <span
              className="text-[9px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "var(--copper)",
                opacity: 0.7,
              }}
            >
              你签下了
            </span>
          </motion.div>

          {/* 右：verdict */}
          <motion.div
            className="flex flex-col gap-2 p-4"
            style={{
              backgroundColor: "rgba(184,115,51,0.04)",
              borderLeft: "2px solid var(--copper)",
              minWidth: 0,
            }}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 1.1 }}
          >
            <span
              className="text-[10px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "var(--copper)",
              }}
            >
              这句话其实在说
            </span>
            <p
              className="font-serif-coach intervention-reframing-verdict italic leading-relaxed"
              style={{
                color: verdict ? "var(--obsidian)" : "rgba(26,24,22,0.4)",
                wordBreak: "break-word",
              }}
            >
              {verdict?.text ?? "你把它签成 ="}
            </p>
          </motion.div>
        </div>

        {/* 中央质询 */}
        {proto ? (
          <motion.div
            className="px-6 py-4 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 1.5 }}
          >
            <p
              className="font-serif-coach intervention-reframing-inquiry italic leading-relaxed"
              style={{ color: "var(--obsidian)", wordBreak: "break-word" }}
            >
              {proto.question}
            </p>
          </motion.div>
        ) : null}

        <div
          aria-hidden
          style={{
            height: "1px",
            background: "rgba(26,24,22,0.1)",
            margin: "8px 0",
          }}
        />

        {/* 下层：候选 + 自写 */}
        <div className="flex flex-col gap-3">
          {select && select.options.length > 0 ? (
            <>
              <div
                className="text-[10px] uppercase"
                style={{
                  fontFamily: "JetBrains Mono, ui-monospace, monospace",
                  letterSpacing: "2px",
                  color: "rgba(26,24,22,0.4)",
                }}
              >
                <strong style={{ color: "var(--copper)", fontWeight: "normal" }}>
                  还有一些读法
                </strong>{" "}
                · 把右边换成 ——
              </div>
              {select.options.map((opt, i) => (
                <motion.button
                  key={opt.value}
                  type="button"
                  onClick={() => setSelectedOption(opt.value)}
                  className="font-serif-coach intervention-reframing-candidate w-full p-4 text-left transition-colors"
                  style={{
                    border:
                      selectedOption === opt.value
                        ? "1px solid var(--copper)"
                        : "1px solid rgba(26,24,22,0.1)",
                    backgroundColor:
                      selectedOption === opt.value
                        ? "rgba(184,115,51,0.06)"
                        : "transparent",
                    color: "var(--obsidian)",
                    wordBreak: "break-word",
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 1.9 + i * 0.08 }}
                >
                  {opt.label}
                </motion.button>
              ))}
            </>
          ) : null}

          {input ? (
            <motion.div
              className="flex flex-col gap-2"
              style={{
                borderTop: "1px dashed rgba(26,24,22,0.1)",
                paddingTop: "16px",
                marginTop: "8px",
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 2.4 }}
            >
              <label
                className="text-[10px] uppercase"
                style={{
                  fontFamily: "JetBrains Mono, ui-monospace, monospace",
                  letterSpacing: "2px",
                  color: "rgba(26,24,22,0.4)",
                }}
              >
                {input.label || "或者你自己写一个"}
              </label>
              <textarea
                className="font-serif-coach intervention-reframing-candidate resize-none bg-transparent outline-none"
                style={{
                  minHeight: "72px",
                  border: "1px solid rgba(26,24,22,0.1)",
                  borderRadius: "4px",
                  padding: "8px 16px",
                  color: "var(--obsidian)",
                }}
                value={writeOwn}
                onChange={(e) => setWriteOwn(e.target.value)}
                placeholder={input.placeholder || ""}
              />
            </motion.div>
          ) : null}
        </div>
      </div>

      <SignatureStrip
        hint="两个都可以保留 · Cmd+Enter 继续"
        actions={
          <InterventionSubmitButton
            label="这么说"
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        }
      />
    </div>
  );
}
