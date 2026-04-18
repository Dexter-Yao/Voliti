// ABOUTME: Scenario Rehearsal · 推演对话流（场景锚条 + copper 虚线轨 + 对话流 + 底部输入）
// ABOUTME: 首个 TextComponent 提升为场景锚条；其他组件按序渲染；IF/THEN chip 模式极窄识别

"use client";

import { useState, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import type { Component, TextInputComponent } from "@/lib/a2ui";
import type { InterventionLayoutProps } from "./types";
import { SignatureStrip } from "./SignatureStrip";
import { InterventionSubmitButton } from "./InterventionSubmitButton";
import { splitFirstTextAsAnchor, isIfThenText } from "./slot-mapping";
import { useCmdEnterSubmit } from "@/hooks/useCmdEnterSubmit";

function FlowComponent({ component }: { component: Component }) {
  const copperLeftStyle = {
    borderLeft: "2px solid var(--copper)",
    paddingLeft: "16px",
  } as const;

  switch (component.kind) {
    case "text":
      // IF/THEN chip 极窄模式：匹配即套专属样式，否则普通 text
      if (isIfThenText(component.text)) {
        return (
          <span className="intervention-if-then-chip inline-block">
            {component.text}
          </span>
        );
      }
      return (
        <p
          className="font-serif-coach leading-relaxed"
          style={{
            fontSize: "16px",
            color: "var(--obsidian)",
            maxWidth: "90%",
          }}
        >
          {component.text}
        </p>
      );

    case "protocol_prompt":
      return (
        <div style={copperLeftStyle} className="flex flex-col gap-1">
          <p
            className="font-sans-user"
            style={{ fontSize: "13px", color: "rgba(26,24,22,0.6)" }}
          >
            {component.observation}
          </p>
          <p
            className="font-serif-coach italic leading-relaxed"
            style={{ fontSize: "16px", color: "var(--obsidian)" }}
          >
            {component.question}
          </p>
        </div>
      );

    default:
      // 其他 kind（select / text_input 等）留给底部输入区处理；
      // 这里只渲染叙事性组件
      return null;
  }
}

export function ScenarioLayout({
  components,
  isSubmitting,
  onSubmit,
}: InterventionLayoutProps) {
  const { anchor, rest } = useMemo(
    () => splitFirstTextAsAnchor(components),
    [components],
  );

  // 非末尾的叙事性组件（text / protocol_prompt）渲染到对话流；
  // 输入类组件（text_input / select）放到底部输入区
  const narrativeRest = useMemo(
    () => rest.filter((c) => c.kind === "text" || c.kind === "protocol_prompt"),
    [rest],
  );
  const input = useMemo(
    () => rest.find((c) => c.kind === "text_input") as TextInputComponent | undefined,
    [rest],
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
      {/* 场景锚条（固定顶部） */}
      {anchor ? (
        <div
          className="mx-8 flex flex-col gap-1 p-4"
          style={{
            backgroundColor: "rgba(26,24,22,0.05)",
            borderLeft: "2px solid var(--copper)",
          }}
        >
          <span
            className="text-[10px] uppercase"
            style={{
              fontFamily: "JetBrains Mono, ui-monospace, monospace",
              letterSpacing: "2px",
              color: "var(--copper)",
            }}
          >
            场景
          </span>
          <span
            className="font-serif-coach leading-relaxed"
            style={{ fontSize: "16px", color: "var(--obsidian)" }}
          >
            {anchor.text}
          </span>
        </div>
      ) : null}

      {/* 对话流 · 左侧 copper 虚线推演轨 */}
      <div className="relative flex flex-1 flex-col gap-6 overflow-y-auto px-8 pb-6 pl-12 pt-6">
        <div
          aria-hidden
          className="absolute bottom-6 top-6"
          style={{
            left: "32px",
            width: "2px",
            background:
              "repeating-linear-gradient(to bottom, rgba(184,115,51,0.55) 0 4px, transparent 4px 10px)",
          }}
        />
        {narrativeRest.map((c, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 + i * 0.1 }}
          >
            <FlowComponent component={c} />
          </motion.div>
        ))}
      </div>

      {/* 底部输入区 */}
      {input ? (
        <div
          className="flex flex-col gap-2 border-t px-8 py-3"
          style={{ borderColor: "rgba(26,24,22,0.1)" }}
        >
          {input.label ? (
            <label
              className="text-[10px] uppercase"
              style={{
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
                letterSpacing: "2px",
                color: "rgba(26,24,22,0.4)",
              }}
            >
              {input.label}
            </label>
          ) : null}
          <textarea
            className="font-serif-coach resize-none bg-transparent outline-none"
            style={{
              fontSize: "14px",
              minHeight: "56px",
              border: "1px solid rgba(26,24,22,0.1)",
              borderRadius: "4px",
              padding: "8px 16px",
              color: "var(--obsidian)",
            }}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={input.placeholder || ""}
          />
        </div>
      ) : null}

      <SignatureStrip
        hint="拒绝 · 跳过 · Cmd+Enter 继续"
        actions={
          <InterventionSubmitButton
            label="继续预演"
            submittingLabel="继续中…"
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
          />
        }
      />
    </div>
  );
}
