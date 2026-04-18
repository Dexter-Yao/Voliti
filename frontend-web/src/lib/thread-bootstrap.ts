// ABOUTME: Thread 创建与复用规则
// ABOUTME: 定义 coaching 与 onboarding 的线程创建边界，供前端入口复用

import { createClient } from "../providers/client";
import { getTodayDateString } from "./user";
import {
  type SessionType,
  SEGMENT_STATUS_ACTIVE,
  SESSION_TYPE_ONBOARDING,
} from "./thread-utils";

export type EnsureThreadResult = { threadId: string; isNew: boolean };

export async function ensureTodayThread(
  apiUrl: string,
  assistantId: string,
  sessionType: SessionType = "coaching",
): Promise<EnsureThreadResult | null> {
  const client = createClient(apiUrl, undefined, undefined);
  const today = getTodayDateString();

  try {
    const existing = await client.threads.search({
      metadata: { date: today, session_type: sessionType },
      limit: 1,
    });

    if (existing.length > 0) {
      return { threadId: existing[0].thread_id, isNew: false };
    }

    const thread = await client.threads.create({
      metadata: {
        date: today,
        session_type: sessionType,
        graph_id: assistantId,
        segment_status: SEGMENT_STATUS_ACTIVE,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
    });

    return { threadId: thread.thread_id, isNew: true };
  } catch (e) {
    console.error("Failed to ensure today thread:", e);
    return null;
  }
}

export async function startOnboardingThread(
  apiUrl: string,
  assistantId: string,
): Promise<EnsureThreadResult | null> {
  const client = createClient(apiUrl, undefined, undefined);
  const today = getTodayDateString();

  try {
    const thread = await client.threads.create({
      metadata: {
        date: today,
        session_type: SESSION_TYPE_ONBOARDING,
        graph_id: assistantId,
        segment_status: SEGMENT_STATUS_ACTIVE,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
    });

    return { threadId: thread.thread_id, isNew: true };
  } catch (e) {
    console.error("Failed to create onboarding thread:", e);
    return null;
  }
}
