// ABOUTME: 已登录用户的教练上下文聚合接口
// ABOUTME: 在服务端按受信任用户边界读取 Store，返回 onboarding、Mirror 与最近前瞻摘要

import { NextResponse } from "next/server";

import { getAuthenticatedUser } from "@/lib/auth/server-user";
import { createServerLangGraphClient } from "@/lib/langgraph/server";
import {
  buildAcceptedWitnessCardsFromStoreItems,
  buildMirrorDataFromStoreValues,
  parseJsonFileValue,
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
  isPast: boolean;
}

interface CoachContextResponse {
  briefing: string | null;
  mirrorData: MirrorData;
  onboardingComplete: boolean;
  witnessCards: WitnessCard[];
  upcomingMarkers: ForwardMarkerSummary[];
  allMarkers: ForwardMarkerSummary[];
}

function jsonError(status: number, error: string) {
  return NextResponse.json({ error }, { status });
}

function assertValidStoreJson(
  value: Record<string, unknown> | null,
  requiredKeys: readonly string[],
  storeKey: string,
): void {
  if (value === null) return;
  const parsed = parseJsonFileValue<Record<string, unknown>>(value);
  if (parsed === null) {
    throw new Error(`[${storeKey}] JSON 解析失败`);
  }
  for (const key of requiredKeys) {
    if (parsed[key] === undefined) {
      throw new Error(`[${storeKey}] 必要字段缺失：${key}`);
    }
  }
}

// 与 backend/src/voliti/contracts/__init__.py 中 Pydantic 必填字段镜像；模型演进时需同步
const STORE_REQUIRED_KEYS = {
  chapter: ["chapter_number", "goal_id", "start_date", "planned_end_date", "process_goals"],
  goal: ["id", "description", "north_star_target", "start_date", "target_date"],
  dashboardConfig: ["north_star", "support_metrics"],
  markers: ["markers"],
} as const;

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

function parseAllMarkers(markersText: string): ForwardMarkerSummary[] {
  try {
    const parsed = JSON.parse(markersText) as {
      markers?: Array<Record<string, unknown>>;
    };
    const now = Date.now();

    return (parsed.markers ?? [])
      .map((marker) => {
        const date = typeof marker.date === "string" ? marker.date : "";
        const timestamp = Date.parse(date);
        return {
          id: typeof marker.id === "string" ? marker.id : "",
          date,
          description:
            typeof marker.description === "string" ? marker.description : "",
          riskLevel:
            typeof marker.risk_level === "string" ? marker.risk_level : "medium",
          linkedLifeSign:
            typeof marker.linked_lifesign === "string"
              ? marker.linked_lifesign
              : null,
          isPast: Number.isFinite(timestamp) && timestamp < now,
        };
      })
      .filter((marker) => marker.id && marker.date && marker.description)
      .sort((a, b) => Date.parse(b.date) - Date.parse(a.date));
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

  try {
    assertValidStoreJson(chapterValue, STORE_REQUIRED_KEYS.chapter, STORE_KEYS.chapter);
    assertValidStoreJson(goalValue, STORE_REQUIRED_KEYS.goal, STORE_KEYS.goal);
    assertValidStoreJson(
      dashboardConfigValue,
      STORE_REQUIRED_KEYS.dashboardConfig,
      STORE_KEYS.dashboardConfig,
    );
    assertValidStoreJson(markersValue, STORE_REQUIRED_KEYS.markers, STORE_KEYS.markers);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Store 数据结构异常";
    return jsonError(500, message);
  }

  const profileText = unwrapFileValue(profileValue);
  const allMarkers = parseAllMarkers(unwrapFileValue(markersValue));
  const now = Date.now();
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
    upcomingMarkers: allMarkers
      .filter((m) => !m.isPast && Date.parse(m.date) >= now)
      .sort((a, b) => Date.parse(a.date) - Date.parse(b.date))
      .slice(0, 3),
    allMarkers,
  };

  return NextResponse.json(response, {
    headers: {
      "Cache-Control": "no-store",
    },
  });
}
