// ABOUTME: Intervention Layout 底部签名条（签名 + hint + actions），与按钮不重叠
// ABOUTME: 独立一行：左 SIGNATURE_LABEL，右 hint + actions

"use client";

import type { ReactNode } from "react";
import { SIGNATURE_LABEL } from "./types";

interface SignatureStripProps {
  hint?: ReactNode;
  actions?: ReactNode;
}

export function SignatureStrip({ hint, actions }: SignatureStripProps) {
  return (
    <footer
      className="flex items-center justify-between border-t px-6 py-2"
      style={{
        borderColor: "rgba(26, 24, 22, 0.1)",
        backgroundColor: "var(--parchment)",
      }}
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
        {SIGNATURE_LABEL}
      </span>
      <div className="flex items-center gap-4">
        {hint ? (
          <span
            className="text-[10px]"
            style={{
              fontFamily: "JetBrains Mono, ui-monospace, monospace",
              letterSpacing: "1px",
              color: "rgba(26, 24, 22, 0.4)",
            }}
          >
            {hint}
          </span>
        ) : null}
        {actions}
      </div>
    </footer>
  );
}
