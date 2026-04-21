// ABOUTME: Plan Builder 全屏 overlay body
// ABOUTME: 渲染 text 只读段 + text_input 可编辑段 + 三个底部操作（确认 / 再谈谈 / 关闭）

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Component } from "@/lib/a2ui";

interface PlanBuilderLayoutProps {
  components: Component[];
  isSubmitting: boolean;
  onSubmit: (data: Record<string, unknown>) => void;
  onReject: (reason: string) => void;
  onSkip: () => void;
}

function buildInitialData(components: Component[]): Record<string, string> {
  const data: Record<string, string> = {};
  for (const c of components) {
    if (c.kind === "text_input") {
      data[c.key] = c.value ?? "";
    }
  }
  return data;
}

export function PlanBuilderLayout({
  components,
  isSubmitting,
  onSubmit,
  onReject,
  onSkip,
}: PlanBuilderLayoutProps) {
  const initialData = useMemo(() => buildInitialData(components), [components]);
  const [formData, setFormData] = useState<Record<string, string>>(() => ({
    ...initialData,
  }));
  const [discussMode, setDiscussMode] = useState(false);
  const [discussReason, setDiscussReason] = useState("");

  const hasChanges = useMemo(
    () =>
      Object.entries(formData).some(
        ([key, val]) => (val ?? "").trim() !== (initialData[key] ?? "").trim(),
      ),
    [formData, initialData],
  );

  const handleSubmit = useCallback(() => {
    onSubmit({ ...formData });
  }, [formData, onSubmit]);

  const handleDiscuss = useCallback(() => {
    onReject(discussReason.trim());
  }, [discussReason, onReject]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !e.isComposing) {
        e.preventDefault();
        if (!isSubmitting && !discussMode) handleSubmit();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSubmit, isSubmitting, discussMode]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-6 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-[#1A1816]/15 [&::-webkit-scrollbar-track]:bg-transparent">
        <div className="mx-auto flex max-w-[640px] flex-col gap-5">
          {components.map((component, i) => {
            if (component.kind === "text") {
              return (
                <p
                  key={i}
                  className="font-serif-coach text-[15px] leading-relaxed text-[#1A1816]/80 whitespace-pre-line"
                >
                  {component.text}
                </p>
              );
            }
            if (component.kind === "text_input") {
              return (
                <div key={component.key} className="space-y-1.5">
                  <Label
                    htmlFor={`plan-builder-${component.key}`}
                    className="font-mono-system text-[10px] uppercase tracking-[1.5px] text-[#1A1816]/50"
                  >
                    {component.label}
                  </Label>
                  <Input
                    id={`plan-builder-${component.key}`}
                    value={formData[component.key] ?? ""}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        [component.key]: e.target.value,
                      }))
                    }
                    disabled={isSubmitting || discussMode}
                    placeholder={component.placeholder || ""}
                    className="border-[#1A1816]/15 bg-transparent text-sm focus-visible:border-[#B87333] focus-visible:ring-[#B87333]/30"
                  />
                </div>
              );
            }
            return null;
          })}
        </div>
      </div>

      <footer
        className="border-t px-6 py-4"
        style={{ borderColor: "rgba(26,24,22,0.08)" }}
      >
        <div className="mx-auto flex max-w-[640px] flex-col gap-3">
          {discussMode ? (
            <>
              <Textarea
                value={discussReason}
                onChange={(e) => setDiscussReason(e.target.value)}
                placeholder="告诉教练哪里还想再谈谈……"
                className="min-h-[72px] resize-none border-[#1A1816]/15 text-sm focus:border-[#B87333] focus:ring-[#B87333]/30"
                autoFocus
                disabled={isSubmitting}
              />
              <div className="flex gap-3">
                <Button
                  size="sm"
                  onClick={handleDiscuss}
                  disabled={isSubmitting}
                  className="bg-[#1A1816] text-[#F4F0E8] hover:bg-[#1A1816]/90"
                >
                  发给教练
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setDiscussMode(false);
                    setDiscussReason("");
                  }}
                  disabled={isSubmitting}
                  className="text-[#1A1816]/50"
                >
                  返回
                </Button>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="flex-1 bg-[#1A1816] text-[#F4F0E8] hover:bg-[#1A1816]/90"
              >
                {isSubmitting
                  ? "提交中…"
                  : hasChanges
                  ? "确认这版"
                  : "就这样开始"}
              </Button>
              <Button
                variant="ghost"
                onClick={() => setDiscussMode(true)}
                disabled={isSubmitting}
                className="text-[#B87333] hover:text-[#965f29]"
              >
                我想再谈谈
              </Button>
              <Button
                variant="ghost"
                onClick={onSkip}
                disabled={isSubmitting}
                className="text-[#1A1816]/40 hover:text-[#1A1816]"
              >
                关闭
              </Button>
            </div>
          )}
        </div>
      </footer>
    </div>
  );
}
