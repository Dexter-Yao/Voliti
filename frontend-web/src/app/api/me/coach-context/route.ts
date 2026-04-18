// ABOUTME: 已登录用户的教练上下文聚合接口
// ABOUTME: 在服务端按受信任用户边界读取 Store，返回 onboarding、Mirror 与最近前瞻摘要

import { NextResponse } from "next/server";

import { getAuthenticatedUser } from "@/lib/auth/server-user";
import { createServerLangGraphClient } from "@/lib/langgraph/server";
import {
  buildAcceptedWitnessCardsFromStoreItems,
  buildMirrorDataFromStoreValues,
  type WitnessCard,
  type MirrorData,
} from "@/lib/mirror-contract";

export const runtime = "nodejs";

const STORE_KEYS = {
  briefing: "/derived/briefing.md",
  chapter: "/chapter/current.json",
  copingPlans: "/coping_plans_index.md",
  dashboardConfig: "/profile/dashboardConfig",
  goal: "/goal/current.json",
  markers: "/timeline/markers.json",
  profile: "/profile/context.md",
} as const;

interface ForwardMarkerSummary {
  id: string;
  date: string;
  description: string;
  riskLevel: string;
  linkedLifeSign: string | null;
}

interface CoachContextResponse {
  briefing: string | null;
  mirrorData: MirrorData;
  onboardingComplete: boolean;
  witnessCards: WitnessCard[];
  upcomingMarkers: ForwardMarkerSummary[];
}

function jsonError(status: number, error: string) {
  return NextResponse.json({ error }, { status });
}

function unwrapFileValue(
  value: Record<string, unknown> | null | undefined,
): string {
  const content = value?.content;
  if (Array.isArray(content) && content.every((line) => typeof line === "string")) {
    return content.join("\n");
  }
  return "";
}

async function getStoreValue(
  key: string,
  namespace: string[],
): Promise<Record<string, unknown> | null> {
  try {
    const client = createServerLangGraphClient();
    const item = await client.store.getItem(namespace, key);
    return (item?.value as Record<string, unknown> | undefined) ?? null;
  } catch {
    return null;
  }
}

async function getAcceptedWitnessCards(
  namespace: string[],
): Promise<WitnessCard[]> {
  try {
    const client = createServerLangGraphClient();
    const items: Array<{
      key: string;
      value: Record<string, unknown> | null;
      createdAt?: string;
      updatedAt?: string;
    }> = [];
    const pageSize = 100;

    for (let offset = 0; ; offset += pageSize) {
      const page = await client.store.searchItems(
        [...namespace, "interventions"],
        {
          limit: pageSize,
          offset,
        },
      );

      items.push(...page.items);
      if (page.items.length < pageSize) break;
    }

    return buildAcceptedWitnessCardsFromStoreItems(items);
  } catch {
    return [];
  }
}

function parseUpcomingMarkers(markersText: string): ForwardMarkerSummary[] {
  try {
    const parsed = JSON.parse(markersText) as {
      markers?: Array<Record<string, unknown>>;
    };
    const now = Date.now();

    return (parsed.markers ?? [])
      .filter((marker) => marker.status === "upcoming")
      .map((marker) => ({
        id: typeof marker.id === "string" ? marker.id : "",
        date: typeof marker.date === "string" ? marker.date : "",
        description:
          typeof marker.description === "string" ? marker.description : "",
        riskLevel:
          typeof marker.risk_level === "string" ? marker.risk_level : "medium",
        linkedLifeSign:
          typeof marker.linked_lifesign === "string"
            ? marker.linked_lifesign
            : null,
      }))
      .filter((marker) => marker.id && marker.date && marker.description)
      .filter((marker) => {
        const timestamp = Date.parse(marker.date);
        return Number.isFinite(timestamp) && timestamp >= now;
      })
      .sort((a, b) => Date.parse(a.date) - Date.parse(b.date))
      .slice(0, 3);
  } catch {
    return [];
  }
}

export async function GET() {
  const user = await getAuthenticatedUser();
  if (!user) {
    return jsonError(401, "请先登录后再继续。");
  }

  const namespace = ["voliti", user.id];
  const [
    profileValue,
    goalValue,
    chapterValue,
    dashboardConfigValue,
    copingPlansValue,
    briefingValue,
    markersValue,
    witnessCards,
  ] = await Promise.all([
    getStoreValue(STORE_KEYS.profile, namespace),
    getStoreValue(STORE_KEYS.goal, namespace),
    getStoreValue(STORE_KEYS.chapter, namespace),
    getStoreValue(STORE_KEYS.dashboardConfig, namespace),
    getStoreValue(STORE_KEYS.copingPlans, namespace),
    getStoreValue(STORE_KEYS.briefing, namespace),
    getStoreValue(STORE_KEYS.markers, namespace),
    getAcceptedWitnessCards(namespace),
  ]);

  const profileText = unwrapFileValue(profileValue);
  const response: CoachContextResponse = {
    briefing: unwrapFileValue(briefingValue) || null,
    mirrorData: buildMirrorDataFromStoreValues({
      chapterValue,
      copingPlansValue,
      dashboardConfigValue,
      goalValue,
      profileValue,
    }),
    onboardingComplete: profileText.includes("onboarding_complete: true"),
    witnessCards,
    upcomingMarkers: parseUpcomingMarkers(unwrapFileValue(markersValue)),
  };

  return NextResponse.json(response, {
    headers: {
      "Cache-Control": "no-store",
    },
  });
}
