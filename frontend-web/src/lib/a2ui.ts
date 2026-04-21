// ABOUTME: A2UI 组件类型目录，精确镜像 backend/src/voliti/a2ui.py
// ABOUTME: 8 种 UI 原语 + Payload/Response 交互协议

import { z } from "zod";

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

export interface SelectOption {
  label: string;
  value: string;
}

// ---------------------------------------------------------------------------
// Display components
// ---------------------------------------------------------------------------

export interface TextComponent {
  kind: "text";
  text: string;
}

export interface ImageComponent {
  kind: "image";
  src: string;
  alt: string;
}

export interface ProtocolPromptComponent {
  kind: "protocol_prompt";
  observation: string;
  question: string;
}

// ---------------------------------------------------------------------------
// Input components
// ---------------------------------------------------------------------------

export interface SliderComponent {
  kind: "slider";
  key: string;
  label: string;
  min: number;
  max: number;
  step: number;
  value: number | null;
}

export interface TextInputComponent {
  kind: "text_input";
  key: string;
  label: string;
  placeholder: string;
  value: string;
}

export interface NumberInputComponent {
  kind: "number_input";
  key: string;
  label: string;
  unit: string;
  value: number | null;
}

export interface SelectComponent {
  kind: "select";
  key: string;
  label: string;
  options: SelectOption[];
  value: string;
}

export interface MultiSelectComponent {
  kind: "multi_select";
  key: string;
  label: string;
  options: SelectOption[];
  value: string[];
}

// ---------------------------------------------------------------------------
// Discriminated union of all components
// ---------------------------------------------------------------------------

export type Component =
  | TextComponent
  | ImageComponent
  | ProtocolPromptComponent
  | SliderComponent
  | TextInputComponent
  | NumberInputComponent
  | SelectComponent
  | MultiSelectComponent;

// ---------------------------------------------------------------------------
// Payload and Response
// ---------------------------------------------------------------------------

export interface A2UIPayload {
  type: "a2ui";
  components: Component[];
  layout: "half" | "three-quarter" | "full";
  metadata: Record<string, string>;
}

/**
 * A2UI 交互形态分类，通过 payload.metadata.surface 传达。
 * 取值集合与后端 docs/05_Runtime_Contracts.md §8.5 保持同步。
 */
export const SurfaceSchema = z.enum([
  "onboarding",
  "coaching",
  "intervention",
  "witness-card",
  "plan-builder",
]);
export type Surface = z.infer<typeof SurfaceSchema>;

export const InterventionKindSchema = z.enum([
  "future-self-dialogue",
  "scenario-rehearsal",
  "metaphor-collaboration",
  "cognitive-reframing",
]);
export type InterventionKind = z.infer<typeof InterventionKindSchema>;

/**
 * 从 payload metadata 解析交互形态。
 * 值不识别或缺失时降级为 "coaching"（契约向前兼容）。
 */
export function resolveSurface(metadata: Record<string, string>): Surface {
  return SurfaceSchema.safeParse(metadata.surface).data ?? "coaching";
}

/**
 * 仅当 surface="intervention" 时返回具体手法标识，否则返回 null。
 */
export function resolveInterventionKind(
  metadata: Record<string, string>,
): InterventionKind | null {
  if (resolveSurface(metadata) !== "intervention") return null;
  return InterventionKindSchema.safeParse(metadata.intervention_kind).data ?? null;
}

export interface A2UIResponse {
  action: "submit" | "reject" | "skip";
  interrupt_id: string | null;
  data: Record<string, unknown>;
  reason: string | null;
}

// ---------------------------------------------------------------------------
// Zod schemas — used only for the runtime type guard
// ---------------------------------------------------------------------------

const SelectOptionSchema = z.object({
  label: z.string(),
  value: z.string(),
});

const ComponentSchema = z.discriminatedUnion("kind", [
  z.object({ kind: z.literal("text"), text: z.string() }),
  z.object({ kind: z.literal("image"), src: z.string(), alt: z.string() }),
  z.object({
    kind: z.literal("protocol_prompt"),
    observation: z.string(),
    question: z.string(),
  }),
  z.object({
    kind: z.literal("slider"),
    key: z.string(),
    label: z.string(),
    min: z.number(),
    max: z.number(),
    step: z.number(),
    value: z.number().nullable(),
  }),
  z.object({
    kind: z.literal("text_input"),
    key: z.string(),
    label: z.string(),
    placeholder: z.string(),
    value: z.string(),
  }),
  z.object({
    kind: z.literal("number_input"),
    key: z.string(),
    label: z.string(),
    unit: z.string(),
    value: z.number().nullable(),
  }),
  z.object({
    kind: z.literal("select"),
    key: z.string(),
    label: z.string(),
    options: z.array(SelectOptionSchema),
    value: z.string(),
  }),
  z.object({
    kind: z.literal("multi_select"),
    key: z.string(),
    label: z.string(),
    options: z.array(SelectOptionSchema),
    value: z.array(z.string()),
  }),
]);

const A2UIPayloadSchema = z.object({
  type: z.literal("a2ui"),
  components: z.array(ComponentSchema),
  layout: z.union([
    z.literal("half"),
    z.literal("three-quarter"),
    z.literal("full"),
  ]),
  metadata: z.record(z.string(), z.string()),
});

// ---------------------------------------------------------------------------
// Type guard
// ---------------------------------------------------------------------------

export function isA2UIPayload(value: unknown): value is A2UIPayload {
  return A2UIPayloadSchema.safeParse(value).success;
}

// ---------------------------------------------------------------------------
// Interrupt 解析工具（LangGraph interrupt 结构 → A2UI payload / id）
// ---------------------------------------------------------------------------

export function extractA2UIPayload(interrupt: unknown): A2UIPayload | null {
  if (!interrupt) return null;
  const rawValue = Array.isArray(interrupt)
    ? interrupt[0]?.value ?? interrupt[0]
    : (interrupt as { value?: unknown })?.value ?? interrupt;
  if (isA2UIPayload(rawValue)) return rawValue;
  return null;
}

export function extractInterruptId(interrupt: unknown): string | null {
  if (!interrupt) return null;
  if (Array.isArray(interrupt) && interrupt.length > 0) {
    return interrupt[0]?.id ?? interrupt[0]?.ns ?? null;
  }
  return (interrupt as { id?: string })?.id ?? null;
}
