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

// --- Onboarding Phase 0 问候语（前端硬编码，作为 assistant message 写入 thread） ---
export const ONBOARDING_GREETING = `你好。

我是 Voliti Coach——你的 AI 减脂私密行为教练。

无论你是想认真做一个可以长期维持的减脂方案，还是只想随时问问今天该怎么吃、为什么反复坚持不下来，都可以告诉我。我会记得你的每一个细节，不评判你的任何选择。

我和其他减脂产品不太一样——我不追求让你快速瘦下来。我想帮你找到一种可以一直走下去的节奏：在压力、疲劳、冲动来袭的时候，依然守得住你自己已经做出的选择。

我们先聊一下吧。`;

// --- Thread 状态判断 ---
export function isThreadSealed(thread: Thread): boolean {
  const meta = thread.metadata as Record<string, unknown> | undefined;
  return meta?.segment_status === SEGMENT_STATUS_SEALED;
}
