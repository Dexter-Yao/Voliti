// ABOUTME: LangGraph 提交配置构造器
// ABOUTME: 统一普通消息与 A2UI resume 的 configurable.session_type 传递规则

import { type SessionType } from "./thread-utils";

export function buildSubmitConfig(
  userId: string | null | undefined,
  sessionType: SessionType,
) {
  return {
    configurable: {
      user_id: userId ?? "",
      session_type: sessionType,
    },
  };
}
