// ABOUTME: 从 LangGraph Store 读取 Mirror 面板数据
// ABOUTME: namespace ("voliti", user_id)，路径与 store_contract.py 一致

import { createClient } from "@/providers/client";
import { getUserId } from "./user";

const STORE_KEYS = {
  dashboardConfig: "/profile/dashboardConfig",
  chapter: "/chapter/current.json",
  copingPlans: "/coping_plans_index.md",
} as const;

// --- Types ---

export interface ChapterData {
  chapter_number: number;
  identity_declaration: string;
  goal: string;
  start_date: string;
  north_star: {
    metric: string;
    unit: string;
    current_value: number | null;
    target_value: number | null;
    delta: number | null;
    history: number[];
  };
  support_metrics: Array<{
    metric: string;
    unit: string;
    current_value: number | null;
  }>;
}

export interface CopingPlan {
  trigger: string;
  plan: string;
  success_rate: number | null;
}

export interface MirrorData {
  chapter: ChapterData | null;
  copingPlans: CopingPlan[];
}

// --- File value unwrapping (mirrors store_contract.py) ---

function unwrapFileValue(value: Record<string, unknown>): string {
  const content = value?.content;
  if (Array.isArray(content) && content.every((line) => typeof line === "string")) {
    return content.join("\n");
  }
  return "";
}

function parseJsonFileValue(value: Record<string, unknown>): unknown | null {
  try {
    return JSON.parse(unwrapFileValue(value));
  } catch {
    return null;
  }
}

// --- Coping plans markdown parser ---

function parseCopingPlans(markdown: string): CopingPlan[] {
  const plans: CopingPlan[] = [];
  const lines = markdown.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("-") && !trimmed.startsWith("*")) continue;
    const text = trimmed.replace(/^[-*]\s*/, "");
    // Best effort: "trigger → plan" or just the line
    const arrowIdx = text.indexOf("→");
    if (arrowIdx >= 0) {
      plans.push({
        trigger: text.slice(0, arrowIdx).trim(),
        plan: text.slice(arrowIdx + 1).trim(),
        success_rate: null,
      });
    } else {
      plans.push({ trigger: text, plan: "", success_rate: null });
    }
  }

  return plans;
}

// --- Public API ---

export async function fetchMirrorData(): Promise<MirrorData> {
  const userId = getUserId();
  if (!userId) return { chapter: null, copingPlans: [] };

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return { chapter: null, copingPlans: [] };

  const client = createClient(apiUrl, undefined, undefined);
  const namespace = ["voliti", userId];

  let chapter: ChapterData | null = null;
  let copingPlans: CopingPlan[] = [];

  try {
    const chapterItem = await client.store.getItem(namespace, STORE_KEYS.chapter);
    if (chapterItem?.value) {
      const parsed = parseJsonFileValue(chapterItem.value as Record<string, unknown>);
      chapter = parsed as ChapterData;
    }
  } catch {
    // Store item may not exist yet
  }

  try {
    const copingItem = await client.store.getItem(namespace, STORE_KEYS.copingPlans);
    if (copingItem?.value) {
      const markdown = unwrapFileValue(copingItem.value as Record<string, unknown>);
      copingPlans = parseCopingPlans(markdown);
    }
  } catch {
    // Store item may not exist yet
  }

  return { chapter, copingPlans };
}
