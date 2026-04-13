// ABOUTME: Thread 状态判断工具函数与共享常量
// ABOUTME: session_type / segment_status 的前端唯一事实来源

import { Thread } from "@langchain/langgraph-sdk";

// --- Session Type（与 backend session_type.py 对齐） ---
export type SessionType = "coaching" | "onboarding";
export const SESSION_TYPE_COACHING: SessionType = "coaching";
export const SESSION_TYPE_ONBOARDING: SessionType = "onboarding";

// --- Segment Status ---
export type SegmentStatus = "active" | "sealed";
export const SEGMENT_STATUS_ACTIVE: SegmentStatus = "active";
export const SEGMENT_STATUS_SEALED: SegmentStatus = "sealed";

// --- Thread 状态判断 ---
export function isThreadSealed(thread: Thread): boolean {
  const meta = thread.metadata as Record<string, unknown> | undefined;
  return meta?.segment_status === SEGMENT_STATUS_SEALED;
}
