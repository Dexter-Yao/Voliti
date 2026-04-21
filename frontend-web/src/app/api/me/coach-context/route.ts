// ABOUTME: 已登录用户的教练上下文聚合接口
// ABOUTME: 在服务端按受信任用户边界读取 Store + 调 LangGraph custom_route 派生 plan_view

import { NextResponse } from "next/server";

import { getAuthenticatedUser } from "@/lib/auth/server-user";
import { createServerLangGraphClient } from "@/lib/langgraph/server";
import {
  buildAcceptedWitnessCardsFromStoreItems,
  parseCopingPlans,
  parseIdentityStatement,
  parseJsonFileValue,
  unwrapFileValue,
  type CopingPlan,
  type DashboardConfigData,
  type PlanDocumentData,
  type PlanViewData,
  type WitnessCard,
} from "@/lib/mirror-contract";
import type { ForwardMarkerSummary } from "@/lib/store-sync";

export const runtime = "nodejs";

const STORE_KEYS = {
  briefing: "/derived/briefing.md",
  copingPlans: "/coping_plans_index.md",
  dashboardConfig: "/profile/dashboardConfig",
  markers: "/timeline/markers.json",
  profile: "/profile/context.md",
} as const;

interface CoachContextResponse {
  briefing: string | null;
  onboardingComplete: boolean;
  plan: PlanDocumentData | null;
  planView: PlanViewData | null;
  dashboardConfig: DashboardConfigData | null;
  copingPlans: CopingPlan[];
  identityStatement: string | null;
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

// 与 backend/src/voliti/contracts/ 中 Pydantic 必填字段镜像；模型演进时需同步
const STORE_REQUIRED_KEYS = {
  dashboardConfig: ["north_star", "support_metrics"],
  markers: ["markers"],
} as const;

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

async function fetchPlanViewPayload(
  userId: string,
): Promise<{ plan: PlanDocumentData; planView: PlanViewData } | null> {
  const apiUrl = process.env.LANGGRAPH_API_URL;
  if (!apiUrl) return null;

  const url = `${apiUrl.replace(/\/$/, "")}/plan-view/${encodeURIComponent(userId)}`;
  const headers: Record<string, string> = { accept: "application/json" };
  if (process.env.LANGSMITH_API_KEY) {
    headers["x-api-key"] = process.env.LANGSMITH_API_KEY;
  }

  try {
    const response = await fetch(url, { headers, cache: "no-store" });
    if (response.status === 404) return null;
    if (!response.ok) {
      console.error(
        `plan-view upstream non-ok: ${response.status} ${await response.text()}`,
      );
      return null;
    }
    const body = (await response.json()) as {
      plan: PlanDocumentData;
      plan_view: PlanViewData;
    };
    return { plan: body.plan, planView: body.plan_view };
  } catch (err) {
    console.error("plan-view fetch failed", err);
    return null;
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
    dashboardConfigValue,
    copingPlansValue,
    briefingValue,
    markersValue,
    witnessCards,
    planPayload,
  ] = await Promise.all([
    getStoreValue(STORE_KEYS.profile, namespace),
    getStoreValue(STORE_KEYS.dashboardConfig, namespace),
    getStoreValue(STORE_KEYS.copingPlans, namespace),
    getStoreValue(STORE_KEYS.briefing, namespace),
    getStoreValue(STORE_KEYS.markers, namespace),
    getAcceptedWitnessCards(namespace),
    fetchPlanViewPayload(user.id),
  ]);

  try {
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
  const copingMarkdown = unwrapFileValue(copingPlansValue);
  const allMarkers = parseAllMarkers(unwrapFileValue(markersValue));
  const now = Date.now();

  const response: CoachContextResponse = {
    briefing: unwrapFileValue(briefingValue) || null,
    onboardingComplete: profileText.includes("onboarding_complete: true"),
    plan: planPayload?.plan ?? null,
    planView: planPayload?.planView ?? null,
    dashboardConfig: parseJsonFileValue<DashboardConfigData>(dashboardConfigValue),
    copingPlans: copingMarkdown ? parseCopingPlans(copingMarkdown) : [],
    identityStatement: profileText ? parseIdentityStatement(profileText) : null,
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
