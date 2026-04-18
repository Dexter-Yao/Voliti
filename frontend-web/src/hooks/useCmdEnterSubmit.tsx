import { useEffect } from "react";

/**
 * Cmd/Ctrl + Enter 触发提交的全局快捷键。
 * 避开 IME composition（中文输入法多次 Enter）。
 */
export function useCmdEnterSubmit(
  handleSubmit: () => void,
  isSubmitting: boolean,
): void {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !e.isComposing) {
        e.preventDefault();
        if (!isSubmitting) handleSubmit();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSubmit, isSubmitting]);
}
