// ABOUTME: A2UI 底部抽屉，使用 shadcn Sheet 渲染 A2UI 交互面板
// ABOUTME: 布局映射 half=50vh, three-quarter=75vh, full=100vh；surface 驱动视觉外壳差异化

"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { resolveSurface, type A2UIPayload, type Surface } from "@/lib/a2ui";
import { cn } from "@/lib/utils";
import { A2UIRenderer } from "./A2UIRenderer";

const LAYOUT_HEIGHT: Record<A2UIPayload["layout"], string> = {
  half: "50vh",
  "three-quarter": "75vh",
  full: "100vh",
};

/**
 * Surface 视觉外壳映射。
 * - intervention：体验式干预形态，最小标记用 copper 顶边 + 更多留白；
 *   完整视觉规格由后续设计阶段决定（docs/09 §5.2 / M7）。
 * - witness-card / onboarding / coaching：保持现有视觉。
 */
const SURFACE_CLASS: Record<Surface, string> = {
  onboarding: "",
  coaching: "",
  intervention: "border-t-2 border-t-[var(--copper)] py-8",
  "witness-card": "",
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

  // data-surface 作为 CSS 主题钩子预留给未来干预视觉规格（M7）；当前仅 intervention 形态有样式
  return (
    <Sheet open={!!payload} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="bottom"
        data-surface={surface}
        className={cn(
          "mx-auto max-w-[480px] overflow-y-auto rounded-t-lg p-6",
          SURFACE_CLASS[surface],
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
