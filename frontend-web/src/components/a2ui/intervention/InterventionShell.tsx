// ABOUTME: Intervention 模式 thin-wrap（按 intervention_kind 决定标题，视觉外壳走共享 FullscreenShell）

"use client";

import type { ReactNode } from "react";
import type { InterventionKind } from "@/lib/a2ui";
import { FullscreenShell } from "../shared/FullscreenShell";

const KIND_ZH: Record<InterventionKind, string> = {
  "future-self-dialogue": "和未来自我对话",
  "scenario-rehearsal": "场景预演",
  "metaphor-collaboration": "隐喻协作",
  "cognitive-reframing": "认知重构",
};

interface InterventionShellProps {
  kind: InterventionKind;
  onRequestClose: () => void;
  children: ReactNode;
}

export function InterventionShell({ kind, onRequestClose, children }: InterventionShellProps) {
  const title = `体验式 · ${KIND_ZH[kind]}`;
  return (
    <FullscreenShell title={title} ariaLabel={title} onRequestClose={onRequestClose}>
      {children}
    </FullscreenShell>
  );
}
