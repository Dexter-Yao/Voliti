// ABOUTME: 从 LangGraph Store 读取 Mirror 面板数据
// ABOUTME: namespace ("voliti", user_id)，路径与 store_contract.py 一致

import { createClient } from "@/providers/client";
import {
  buildMirrorDataFromStoreValues,
  unwrapFileValue,
  type MirrorData,
} from "./mirror-contract";
import { getUserId } from "./user";

export type { MirrorData } from "./mirror-contract";

const STORE_KEYS = {
  dashboardConfig: "/profile/dashboardConfig",
  chapter: "/chapter/current.json",
  copingPlans: "/coping_plans_index.md",
  goal: "/goal/current.json",
  profile: "/profile/context.md",
} as const;

async function getStoreValue(
  client: ReturnType<typeof createClient>,
  namespace: string[],
  key: string,
): Promise<Record<string, unknown> | null> {
  try {
    const item = await client.store.getItem(namespace, key);
    return (item?.value as Record<string, unknown> | undefined) ?? null;
  } catch {
    return null;
  }
}

export async function fetchMirrorData(): Promise<MirrorData> {
  const userId = getUserId();
  if (!userId) return buildMirrorDataFromStoreValues({});

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return buildMirrorDataFromStoreValues({});

  const client = createClient(apiUrl, undefined, undefined);
  const namespace = ["voliti", userId];
  const [chapterValue, copingPlansValue, dashboardConfigValue, goalValue, profileValue] =
    await Promise.all([
      getStoreValue(client, namespace, STORE_KEYS.chapter),
      getStoreValue(client, namespace, STORE_KEYS.copingPlans),
      getStoreValue(client, namespace, STORE_KEYS.dashboardConfig),
      getStoreValue(client, namespace, STORE_KEYS.goal),
      getStoreValue(client, namespace, STORE_KEYS.profile),
    ]);

  return buildMirrorDataFromStoreValues({
    chapterValue,
    copingPlansValue,
    dashboardConfigValue,
    goalValue,
    profileValue,
  });
}

export async function fetchOnboardingComplete(): Promise<boolean> {
  const userId = getUserId();
  if (!userId) return false;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return false;
  const client = createClient(apiUrl, undefined, undefined);
  try {
    const item = await client.store.getItem(["voliti", userId], "/profile/context.md");
    if (!item?.value) return false;
    const text = unwrapFileValue(item.value as Record<string, unknown>);
    return text.includes("onboarding_complete: true");
  } catch {
    return false;
  }
}
