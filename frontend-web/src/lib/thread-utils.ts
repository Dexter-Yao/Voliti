// ABOUTME: Thread 状态判断工具函数
// ABOUTME: 提供 thread sealed 状态等跨组件共享的判断逻辑

import { Thread } from "@langchain/langgraph-sdk";

export function isThreadSealed(thread: Thread): boolean {
  const meta = thread.metadata as Record<string, unknown> | undefined;
  return meta?.segment_status === "sealed";
}
