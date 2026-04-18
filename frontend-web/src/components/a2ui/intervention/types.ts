// ABOUTME: Intervention Layout 组件的统一 props 接口与共享常量
// ABOUTME: 各 Layout 通过 component kind 做槽位分派，不解析内容字符串

import type { Component } from "@/lib/a2ui";

/** 底部签名条文案；Common Shell 契约的一部分（详见 DESIGN.md § Intervention 模式）。 */
export const SIGNATURE_LABEL = "EXPERIENTIAL · 体验式";

export interface InterventionLayoutProps {
  components: Component[];
  isSubmitting: boolean;
  onSubmit: (data: Record<string, unknown>) => void;
  onReject: (reason: string) => void;
  onSkip: () => void;
}
