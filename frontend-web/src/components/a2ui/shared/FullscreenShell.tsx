// ABOUTME: 全屏 overlay 共享外壳（parchment 底 + copper 呼吸线 + top-sig + Escape 关闭）
// ABOUTME: 被 InterventionShell / PlanBuilderShell 等场景外壳作为 thin-wrap 起点复用

"use client";

import { useEffect, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";

function formatMMDD(now: Date = new Date()): string {
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${mm}-${dd}`;
}

export interface FullscreenShellProps {
  /** 左侧 top-sig 文本，mono uppercase copper 色 */
  title: string;
  /** 右侧 top-sig 文本；默认 "VOLITI · MM-DD" */
  subtitle?: string;
  /** aria-label for the dialog role */
  ariaLabel?: string;
  onRequestClose: () => void;
  children: ReactNode;
}

export function FullscreenShell({
  title,
  subtitle,
  ariaLabel,
  onRequestClose,
  children,
}: FullscreenShellProps) {
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

  const resolvedSubtitle = subtitle ?? `VOLITI · ${formatMMDD()}`;

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

        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label={ariaLabel ?? title}
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
            style={{ fontFamily: "var(--font-mono), ui-monospace, monospace" }}
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
              {title}
            </span>
            <span
              className="text-[10px] uppercase"
              style={{
                color: "rgba(26, 24, 22, 0.4)",
                letterSpacing: "1px",
                fontFamily: "JetBrains Mono, ui-monospace, monospace",
              }}
            >
              {resolvedSubtitle}
            </span>
          </header>

          <div className="flex flex-1 flex-col overflow-hidden">{children}</div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
