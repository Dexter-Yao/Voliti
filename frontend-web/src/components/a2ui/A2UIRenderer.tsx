// ABOUTME: A2UI 组件渲染器，将 Component[] 渲染为交互表单
// ABOUTME: 8 种组件类型、重置、拒绝理由、Cmd+Enter 提交

"use client";

import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import type {
  Component,
  SliderComponent,
  TextInputComponent,
  NumberInputComponent,
  SelectComponent,
  MultiSelectComponent,
} from "@/lib/a2ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Undo2 } from "lucide-react";

// --- Initial data builder ---

function buildInitialData(components: Component[]): Record<string, unknown> {
  const data: Record<string, unknown> = {};
  for (const c of components) {
    if ("key" in c) {
      switch (c.kind) {
        case "slider":
          data[c.key] = c.value ?? Math.round((c.min + c.max) / 2);
          break;
        case "text_input":
          data[c.key] = c.value ?? "";
          break;
        case "number_input":
          data[c.key] = c.value != null ? String(c.value) : "";
          break;
        case "select":
          data[c.key] = c.value ?? "";
          break;
        case "multi_select":
          data[c.key] = c.value ?? [];
          break;
      }
    }
  }
  return data;
}

// --- Individual renderers ---

function TextDisplay({ text }: { text: string }) {
  return <p className="font-serif-coach text-[#1A1816]/80 leading-relaxed">{text}</p>;
}

function ImageDisplay({ src, alt }: { src: string; alt: string }) {
  return (
    <img
      src={src}
      alt={alt}
      className="w-full rounded-none object-cover"
    />
  );
}

function ProtocolPrompt({
  observation,
  question,
}: {
  observation: string;
  question: string;
}) {
  return (
    <div className="space-y-3 border-l-2 border-[#B87333] pl-4">
      <p className="text-sm text-[#1A1816]/60">{observation}</p>
      <p className="font-serif-coach text-lg italic text-[#1A1816]">
        &ldquo;{question}&rdquo;
      </p>
    </div>
  );
}

function SliderInput({
  component,
  value,
  onChange,
}: {
  component: SliderComponent;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-2">
      <Label className="text-sm text-[#1A1816]/80">{component.label}</Label>
      <div className="flex items-center gap-3">
        <span className="text-xs text-[#1A1816]/40">{component.min}</span>
        <input
          type="range"
          min={component.min}
          max={component.max}
          step={component.step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-[#B87333]"
        />
        <span className="text-xs text-[#1A1816]/40">{component.max}</span>
        <span className="min-w-[2ch] text-center text-sm font-medium text-[#1A1816]">
          {value}
        </span>
      </div>
    </div>
  );
}

function TextInputField({
  component,
  value,
  onChange,
}: {
  component: TextInputComponent;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label className="text-sm text-[#1A1816]/80">{component.label}</Label>
      <Input
        type="text"
        placeholder={component.placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border-[#1A1816]/10 focus:border-[#B87333] focus:ring-[#B87333]"
      />
    </div>
  );
}

function NumberInputField({
  component,
  value,
  onChange,
}: {
  component: NumberInputComponent;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label className="text-sm text-[#1A1816]/80">{component.label}</Label>
      <div className="flex items-center gap-2">
        <Input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="border-[#1A1816]/10 focus:border-[#B87333] focus:ring-[#B87333]"
        />
        {component.unit && (
          <span className="text-sm text-[#1A1816]/50">{component.unit}</span>
        )}
      </div>
    </div>
  );
}

function SelectInput({
  component,
  value,
  onChange,
}: {
  component: SelectComponent;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label className="text-sm text-[#1A1816]/80">{component.label}</Label>
      <div className="flex flex-wrap gap-2">
        {component.options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`rounded-pill px-4 py-2 text-sm transition-colors ${
              value === opt.value
                ? "bg-[#1A1816] text-[#F4F0E8]"
                : "bg-[#1A1816]/5 text-[#1A1816] hover:bg-[#1A1816]/10"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function MultiSelectInput({
  component,
  value,
  onChange,
}: {
  component: MultiSelectComponent;
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const toggle = (optValue: string) => {
    if (value.includes(optValue)) {
      onChange(value.filter((v) => v !== optValue));
    } else {
      onChange([...value, optValue]);
    }
  };

  return (
    <div className="space-y-2">
      <Label className="text-sm text-[#1A1816]/80">{component.label}</Label>
      <div className="flex flex-wrap gap-2">
        {component.options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => toggle(opt.value)}
            className={`rounded-pill px-4 py-2 text-sm transition-colors ${
              value.includes(opt.value)
                ? "bg-[#1A1816] text-[#F4F0E8]"
                : "bg-[#1A1816]/5 text-[#1A1816] hover:bg-[#1A1816]/10"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// --- Main renderer ---

interface A2UIRendererProps {
  components: Component[];
  onSubmit: (data: Record<string, unknown>) => void;
  onReject: (reason: string) => void;
  onSkip: () => void;
  isSubmitting: boolean;
}

export function A2UIRenderer({
  components,
  onSubmit,
  onReject,
  onSkip,
  isSubmitting,
}: A2UIRendererProps) {
  const initialDataRef = useRef<Record<string, unknown>>(buildInitialData(components));
  const [formData, setFormData] = useState<Record<string, unknown>>(() => ({ ...initialDataRef.current }));
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const updateField = useCallback((key: string, value: unknown) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }, []);

  const hasChanges = useMemo(() => {
    return JSON.stringify(formData) !== JSON.stringify(initialDataRef.current);
  }, [formData]);

  const handleReset = useCallback(() => {
    setFormData({ ...initialDataRef.current });
  }, []);

  const handleSubmit = useCallback(() => {
    const processedData: Record<string, unknown> = {};
    for (const c of components) {
      if ("key" in c) {
        const val = formData[c.key];
        if (c.kind === "number_input" && typeof val === "string") {
          processedData[c.key] = val ? parseFloat(val) : null;
        } else {
          processedData[c.key] = val;
        }
      }
    }
    onSubmit(processedData);
  }, [components, formData, onSubmit]);

  const handleRejectConfirm = useCallback(() => {
    onReject(rejectReason.trim());
    setShowRejectInput(false);
    setRejectReason("");
  }, [onReject, rejectReason]);

  // Cmd/Ctrl + Enter 快捷键提交
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !e.isComposing) {
        e.preventDefault();
        if (!isSubmitting && hasInputs) handleSubmit();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleSubmit, isSubmitting]); // eslint-disable-line react-hooks/exhaustive-deps

  const hasInputs = components.some((c) => "key" in c);

  return (
    <div className="flex flex-col gap-5">
      {components.map((component, i) => {
        switch (component.kind) {
          case "text":
            return <TextDisplay key={i} text={component.text} />;
          case "image":
            return (
              <ImageDisplay key={i} src={component.src} alt={component.alt} />
            );
          case "protocol_prompt":
            return (
              <ProtocolPrompt
                key={i}
                observation={component.observation}
                question={component.question}
              />
            );
          case "slider":
            return (
              <SliderInput
                key={component.key}
                component={component}
                value={formData[component.key] as number}
                onChange={(v) => updateField(component.key, v)}
              />
            );
          case "text_input":
            return (
              <TextInputField
                key={component.key}
                component={component}
                value={formData[component.key] as string}
                onChange={(v) => updateField(component.key, v)}
              />
            );
          case "number_input":
            return (
              <NumberInputField
                key={component.key}
                component={component}
                value={formData[component.key] as string}
                onChange={(v) => updateField(component.key, v)}
              />
            );
          case "select":
            return (
              <SelectInput
                key={component.key}
                component={component}
                value={formData[component.key] as string}
                onChange={(v) => updateField(component.key, v)}
              />
            );
          case "multi_select":
            return (
              <MultiSelectInput
                key={component.key}
                component={component}
                value={formData[component.key] as string[]}
                onChange={(v) => updateField(component.key, v)}
              />
            );
        }
      })}

      {/* 拒绝理由输入 */}
      {showRejectInput && (
        <div className="space-y-2 border-t border-[#1A1816]/10 pt-3">
          <Textarea
            placeholder="告诉教练你为什么拒绝…"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            className="min-h-[60px] resize-none border-[#1A1816]/10 text-sm focus:border-[#B87333] focus:ring-[#B87333]"
            autoFocus
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleRejectConfirm}
              disabled={isSubmitting}
              className="bg-[#1A1816] text-[#F4F0E8] hover:bg-[#1A1816]/90"
            >
              确认拒绝
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => { setShowRejectInput(false); setRejectReason(""); }}
              disabled={isSubmitting}
              className="text-[#1A1816]/50"
            >
              取消
            </Button>
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      {!showRejectInput && (
        <div className="flex items-center gap-3 pt-2">
          {hasInputs && (
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex-1 bg-[#1A1816] text-[#F4F0E8] hover:bg-[#1A1816]/90"
            >
              {isSubmitting ? "提交中…" : "提交"}
            </Button>
          )}
          {hasChanges && (
            <Button
              variant="ghost"
              onClick={handleReset}
              disabled={isSubmitting}
              className="text-[#1A1816]/40 hover:text-[#1A1816]"
            >
              <Undo2 className="mr-1 size-3.5" />
              重置
            </Button>
          )}
          <Button
            variant="ghost"
            onClick={onSkip}
            disabled={isSubmitting}
            className="text-[#1A1816]/50 hover:text-[#1A1816]"
          >
            跳过
          </Button>
          <Button
            variant="ghost"
            onClick={() => setShowRejectInput(true)}
            disabled={isSubmitting}
            className="text-red-400 hover:text-red-500"
          >
            拒绝
          </Button>
        </div>
      )}
    </div>
  );
}
