"use client";

import { Button } from "@/components/ui/button";

interface InterventionSubmitButtonProps {
  label: string;
  onSubmit: () => void;
  isSubmitting: boolean;
  /** 提交中的占位文案；默认 "提交中…"。 */
  submittingLabel?: string;
}

/**
 * Intervention 底部提交按钮。
 * 颜色来自 Starpath primary（obsidian → parchment），4px 圆角与 intervention 外壳一致。
 */
export function InterventionSubmitButton({
  label,
  onSubmit,
  isSubmitting,
  submittingLabel = "提交中…",
}: InterventionSubmitButtonProps) {
  return (
    <Button
      type="button"
      onClick={onSubmit}
      disabled={isSubmitting}
      className="rounded-[4px] px-6 py-2 text-sm font-sans-user"
    >
      {isSubmitting ? submittingLabel : label}
    </Button>
  );
}
