// ABOUTME: Plan Builder 全屏 overlay thin-wrap（视觉外壳走 FullscreenShell 共享实现）

"use client";

import type { ReactNode } from "react";
import { FullscreenShell } from "../shared/FullscreenShell";

interface PlanBuilderShellProps {
  onRequestClose: () => void;
  children: ReactNode;
}

export function PlanBuilderShell({ onRequestClose, children }: PlanBuilderShellProps) {
  return (
    <FullscreenShell
      title="方案 · 共建"
      ariaLabel="方案共建"
      onRequestClose={onRequestClose}
    >
      {children}
    </FullscreenShell>
  );
}
