// ABOUTME: Intervention 模式通用外壳（全屏 overlay + 呼吸线 + top-sig）
// ABOUTME: 按 intervention_kind 分派到四种 Layout；签名条由各 Layout 自行渲染

"use client";

import { useEffect, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { InterventionKind } from "@/lib/a2ui";

const KIND_ZH: Record<InterventionKind, string> = {
  "future-self-dialogue": "和未来自我对话",
  "scenario-rehearsal": "场景预演",
  "metaphor-collaboration": "隐喻协作",
  "cognitive-reframing": "认知重构",
};

function formatDate(now: Date = new Date()): string {
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${mm}-${dd}`;
}

interface InterventionShellProps {
  kind: InterventionKind;
  onRequestClose: () => void;
  children: ReactNode;
}

export function InterventionShell({
  kind,
  onRequestClose,
  children,
}: InterventionShellProps) {
  // Escape 键关闭；遮罩点击不关闭（防误触）
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onRequestClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onRequestClose]);

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-stretch justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* Backdrop：不可点击关闭（防误触） */}
        <div className="absolute inset-0 intervention-backdrop" aria-hidden />

        {/* 外壳主容器 */}
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label={`体验式 · ${KIND_ZH[kind]}`}
          className="relative flex h-full w-full flex-col bg-parchment"
          style={{ backgroundColor: "var(--parchment)" }}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.3, ease: "easeOut", delay: 0.1 }}
        >
          {/* 顶部 copper 呼吸线 */}
          <div
            className="h-px intervention-ribbon intervention-ribbon-breathing"
            aria-hidden
          />

          {/* Top signature 条 */}
          <header
            className="flex items-baseline justify-between px-6 py-2"
            style={{
              fontFamily: "var(--font-mono), ui-monospace, monospace",
            }}
          >
            <span
              className="text-[10px] uppercase"
              style={{
                color: "var(--copper)",
                letterSpacing: "2px",
                opacity: 0.8,
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
              }}
            >
              体验式 · {KIND_ZH[kind]}
            </span>
            <span
              className="text-[10px] uppercase"
              style={{
                color: "rgba(26, 24, 22, 0.4)",
                letterSpacing: "1px",
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
              }}
            >
              VOLITI · {formatDate()}
            </span>
          </header>

          {/* Body：由具体 Layout 渲染（含自己的 body + footer/signature strip） */}
          <div className="flex flex-1 flex-col overflow-hidden">{children}</div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
