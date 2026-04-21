// ABOUTME: Plan Builder 全屏 overlay 外壳
// ABOUTME: 复用 intervention 的视觉语言（parchment + copper top-sig），Layout 自行渲染 body/footer

"use client";

import { useEffect, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";

function formatDate(now: Date = new Date()): string {
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${mm}-${dd}`;
}

interface PlanBuilderShellProps {
  onRequestClose: () => void;
  children: ReactNode;
}

export function PlanBuilderShell({ onRequestClose, children }: PlanBuilderShellProps) {
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
        <div className="absolute inset-0 intervention-backdrop" aria-hidden />

        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label="方案共建"
          className="relative flex h-full w-full flex-col"
          style={{ backgroundColor: "var(--parchment)" }}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.3, ease: "easeOut", delay: 0.1 }}
        >
          <div
            className="h-px intervention-ribbon intervention-ribbon-breathing"
            aria-hidden
          />

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
              方案 · 共建
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

          <div className="flex flex-1 flex-col overflow-hidden">{children}</div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
