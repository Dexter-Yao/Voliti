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

我是 Voliti Coach——你的减脂行为教练。

无论是每天该怎么吃、怎么动，还是突然想放弃时该怎么办，我都会陪着你。不过我最擅长的，是帮你在压力、疲劳、冲动来袭的那些时刻，守住你自己已经做出的选择。

我会记住你的习惯、你容易失控的场景、你在意的那个身份。然后在关键时候提醒你——你想成为的那个人会怎么做。`;

// --- Thread 状态判断 ---
export function isThreadSealed(thread: Thread): boolean {
  const meta = thread.metadata as Record<string, unknown> | undefined;
  return meta?.segment_status === SEGMENT_STATUS_SEALED;
}
