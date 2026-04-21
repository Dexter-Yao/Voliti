// ABOUTME: 受控 info tooltip — 承载 Coach 的解释（why_this_chapter / why_this_goal 等叙事字段）
// ABOUTME: click toggle + 点击外部 / Escape 关闭；Parchment 底 + Serif 文本，与 Coach 叙事层一致

"use client";

import { useEffect, useRef, useState } from "react";
import { Info } from "lucide-react";

interface InfoTooltipProps {
  /** 内容：Coach 的解释文本或其他 ReactNode */
  children: React.ReactNode;
  /** 无障碍标签，默认"查看说明" */
  label?: string;
  /** 图标尺寸，默认 12px —— 与 Mono xs 基线对齐 */
  iconSize?: number;
  /** 展开方向：right-aligned（默认，向左展开，避免窄栏右侧溢出）/ left-aligned */
  align?: "right" | "left";
}

export function InfoTooltip({
  children,
  label = "查看说明",
  iconSize = 12,
  align = "right",
}: InfoTooltipProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;

    const onDocClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <span className="relative inline-flex" ref={rootRef}>
      <button
        type="button"
        aria-expanded={open}
        aria-label={label}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((prev) => !prev);
        }}
        className="inline-flex items-center justify-center text-[#1A1816]/30 transition-colors hover:text-[#B87333] focus:outline-none focus:text-[#B87333]"
      >
        <Info style={{ width: iconSize, height: iconSize }} />
      </button>
      {open && (
        <div
          role="tooltip"
          className={`absolute top-full z-50 mt-2 w-64 border border-[#1A1816]/15 bg-[#F4F0E8] px-3 py-2.5 font-serif-coach text-xs leading-5 text-[#1A1816]/75 shadow-[0_2px_8px_rgba(26,24,22,0.06)] ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {children}
        </div>
      )}
    </span>
  );
}
