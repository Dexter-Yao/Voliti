// ABOUTME: A2UI 底部抽屉，使用 shadcn Sheet 渲染 A2UI 交互面板
// ABOUTME: 布局映射：half=50vh, three-quarter=75vh, full=100vh

"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { A2UIPayload } from "@/lib/a2ui";
import { A2UIRenderer } from "./A2UIRenderer";

const LAYOUT_HEIGHT: Record<A2UIPayload["layout"], string> = {
  half: "50vh",
  "three-quarter": "75vh",
  full: "100vh",
};

interface A2UIDrawerProps {
  payload: A2UIPayload | null;
  isSubmitting: boolean;
  onSubmit: (data: Record<string, unknown>) => void;
  onReject: () => void;
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

  return (
    <Sheet open={!!payload} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="bottom"
        className="mx-auto max-w-[480px] overflow-y-auto rounded-t-lg p-6"
        style={{ maxHeight: LAYOUT_HEIGHT[payload.layout] }}
      >
        <SheetHeader className="sr-only">
          <SheetTitle>Coach Input</SheetTitle>
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
