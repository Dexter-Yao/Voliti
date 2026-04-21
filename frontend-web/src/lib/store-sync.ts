// ABOUTME: 从 LangGraph Store 读取 Mirror 面板数据
// ABOUTME: namespace ("voliti", user_id)，路径与 store_contract.py 一致

import {
  type MirrorData,
  type PlanDocumentData,
  type PlanViewData,
  type WitnessCard,
} from "./mirror-contract";

export type {
  MirrorData,
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
  mirrorData: MirrorData;
  onboardingComplete: boolean;
  plan: PlanDocumentData | null;
  planView: PlanViewData | null;
  witnessCards: WitnessCard[];
  upcomingMarkers: ForwardMarkerSummary[];
  allMarkers: ForwardMarkerSummary[];
}

const EMPTY_MIRROR_DATA: MirrorData = {
  chapter: null,
  copingPlans: [],
  dashboardConfig: null,
  identity_statement: null,
  goal: null,
};

async function fetchCoachContextInternal(): Promise<CoachContextData> {
  const response = await fetch("/api/me/coach-context", {
    cache: "no-store",
    credentials: "include",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: string } | null;
    throw new Error(payload?.error || "无法读取当前教练上下文。");
  }

  const payload = await response.json() as CoachContextData;
  return {
    briefing: payload.briefing ?? null,
    mirrorData: payload.mirrorData ?? EMPTY_MIRROR_DATA,
    onboardingComplete: Boolean(payload.onboardingComplete),
    plan: payload.plan ?? null,
    planView: payload.planView ?? null,
    witnessCards: payload.witnessCards ?? [],
    upcomingMarkers: payload.upcomingMarkers ?? [],
    allMarkers: payload.allMarkers ?? [],
  };
}

export async function fetchCoachContext(): Promise<CoachContextData> {
  return fetchCoachContextInternal();
}

export async function fetchMirrorData(): Promise<MirrorData> {
  const payload = await fetchCoachContextInternal();
  return payload.mirrorData;
}

export async function fetchOnboardingComplete(): Promise<boolean> {
  const payload = await fetchCoachContextInternal();
  return payload.onboardingComplete;
}
