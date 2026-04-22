// ABOUTME: 从 LangGraph Store 读取 Mirror 面板数据
// ABOUTME: namespace ("voliti", user_id)，路径与 store_contract.py 一致

import {
  type CopingPlan,
  type DashboardConfigData,
  type PlanDocumentData,
  type PlanViewData,
  type WitnessCard,
} from "./mirror-contract";

export type {
  CopingPlan,
  DashboardConfigData,
  PlanDocumentData,
  PlanViewData,
  WitnessCard,
} from "./mirror-contract";

export interface ForwardMarkerSummary {
  id: string;
  date: string;
  description: string;
  riskLevel: string;
  linkedLifeSign: string | null;
  isPast: boolean;
}

export interface CoachContextData {
  briefing: string | null;
  onboardingComplete: boolean;
  plan: PlanDocumentData | null;
  planView: PlanViewData | null;
  planDegradedReason: string | null;
  dashboardConfig: DashboardConfigData | null;
  copingPlans: CopingPlan[];
  identityStatement: string | null;
  witnessCards: WitnessCard[];
  upcomingMarkers: ForwardMarkerSummary[];
  allMarkers: ForwardMarkerSummary[];
}

function formatDateInTimeZone(now: Date, timeZone: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const year = parts.find((part) => part.type === "year")?.value ?? "1970";
  const month = parts.find((part) => part.type === "month")?.value ?? "01";
  const day = parts.find((part) => part.type === "day")?.value ?? "01";
  return `${year}-${month}-${day}`;
}

export function buildCoachContextRequestHeaders(
  now: Date = new Date(),
  timeZone: string = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
): Record<string, string> {
  return {
    "x-voliti-user-timezone": timeZone,
    "x-voliti-user-today": formatDateInTimeZone(now, timeZone),
  };
}

async function fetchCoachContextInternal(): Promise<CoachContextData> {
  const response = await fetch("/api/me/coach-context", {
    cache: "no-store",
    credentials: "include",
    headers: buildCoachContextRequestHeaders(),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(payload?.error || "无法读取当前教练上下文。");
  }

  const payload = await response.json() as CoachContextData;
  return {
    briefing: payload.briefing ?? null,
    onboardingComplete: Boolean(payload.onboardingComplete),
    plan: payload.plan ?? null,
    planView: payload.planView ?? null,
    planDegradedReason: payload.planDegradedReason ?? null,
    dashboardConfig: payload.dashboardConfig ?? null,
    copingPlans: payload.copingPlans ?? [],
    identityStatement: payload.identityStatement ?? null,
    witnessCards: payload.witnessCards ?? [],
    upcomingMarkers: payload.upcomingMarkers ?? [],
    allMarkers: payload.allMarkers ?? [],
  };
}

export async function fetchCoachContext(): Promise<CoachContextData> {
  return fetchCoachContextInternal();
}

export async function fetchOnboardingComplete(): Promise<boolean> {
  const payload = await fetchCoachContextInternal();
  return payload.onboardingComplete;
}
