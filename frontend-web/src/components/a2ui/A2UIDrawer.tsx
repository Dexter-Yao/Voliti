// ABOUTME: A2UI 底部抽屉，使用 shadcn Sheet 渲染非 intervention 形态
// ABOUTME: surface="intervention" 走全屏 overlay 分支，按 intervention_kind 分派到四种 Layout

"use client";

import type { FC } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  resolveSurface,
  resolveInterventionKind,
  type A2UIPayload,
  type Surface,
  type InterventionKind,
} from "@/lib/a2ui";
import { cn } from "@/lib/utils";
import { A2UIRenderer } from "./A2UIRenderer";
import { InterventionShell } from "./intervention/InterventionShell";
import { FutureSelfLayout } from "./intervention/FutureSelfLayout";
import { ScenarioLayout } from "./intervention/ScenarioLayout";
import { MetaphorLayout } from "./intervention/MetaphorLayout";
import { ReframingLayout } from "./intervention/ReframingLayout";
import type { InterventionLayoutProps } from "./intervention/types";
import { PlanBuilderShell } from "./plan-builder/PlanBuilderShell";
import { PlanBuilderLayout } from "./plan-builder/PlanBuilderLayout";

const LAYOUT_HEIGHT: Record<A2UIPayload["layout"], string> = {
  half: "50vh",
  "three-quarter": "75vh",
  full: "100vh",
};

/**
 * Surface 视觉外壳映射（仅非全屏 overlay 的 surface 使用）。
 * intervention 与 plan-builder 走全屏 overlay，不经过 Sheet。
 */
const SURFACE_CLASS: Record<
  Exclude<Surface, "intervention" | "plan-builder">,
  string
> = {
  onboarding: "",
  coaching: "",
  "witness-card": "",
};

const LAYOUT_BY_KIND: Record<InterventionKind, FC<InterventionLayoutProps>> = {
  "future-self-dialogue": FutureSelfLayout,
  "scenario-rehearsal": ScenarioLayout,
  "metaphor-collaboration": MetaphorLayout,
  "cognitive-reframing": ReframingLayout,
};

interface A2UIDrawerProps {
  payload: A2UIPayload | null;
  isSubmitting: boolean;
  onSubmit: (data: Record<string, unknown>) => void;
  onReject: (reason: string) => void;
  onSkip: () => void;
  onClose: () => void;
}

export function A2UIDrawer({
  payload,
  isSubmitting,
  onSubmit,
  onReject,
  onSkip,
  onClose,
}: A2UIDrawerProps) {
  if (!payload) return null;

  const surface = resolveSurface(payload.metadata);
  const kind = resolveInterventionKind(payload.metadata);

  // Intervention 分支：全屏 overlay + 专用 Layout
  if (surface === "intervention" && kind) {
    const Layout = LAYOUT_BY_KIND[kind];
    return (
      <InterventionShell kind={kind} onRequestClose={onClose}>
        <Layout
          components={payload.components}
          isSubmitting={isSubmitting}
          onSubmit={onSubmit}
          onReject={onReject}
          onSkip={onSkip}
        />
      </InterventionShell>
    );
  }

  // Plan Builder 分支：全屏 overlay + 专用 Layout
  if (surface === "plan-builder") {
    return (
      <PlanBuilderShell onRequestClose={onClose}>
        <PlanBuilderLayout
          components={payload.components}
          isSubmitting={isSubmitting}
          onSubmit={onSubmit}
          onReject={onReject}
          onSkip={onSkip}
        />
      </PlanBuilderShell>
    );
  }

  // 其他 surface：保持现有 Sheet 视觉（intervention / plan-builder 分支上面已 return）
  const sheetSurface = surface === "intervention" ? "coaching" : surface;
  return (
    <Sheet open={!!payload} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="bottom"
        data-surface={surface}
        className={cn(
          "mx-auto max-w-[480px] overflow-y-auto rounded-t-lg p-6",
          SURFACE_CLASS[sheetSurface],
        )}
        style={{ maxHeight: LAYOUT_HEIGHT[payload.layout] }}
      >
        <SheetHeader className="sr-only">
          <SheetTitle>教练交互</SheetTitle>
        </SheetHeader>
        <A2UIRenderer
          components={payload.components}
          onSubmit={onSubmit}
          onReject={onReject}
          onSkip={onSkip}
          isSubmitting={isSubmitting}
        />
      </SheetContent>
    </Sheet>
  );
}
