// ABOUTME: A2UI form state 共享工具——初始化 / 脏判定等，在 A2UIRenderer 和 PlanBuilderLayout 之间复用

import type { Component } from "./a2ui";

/**
 * 从 components 列表派生 form 初始 state。
 *
 * - slider → `c.value ?? (min+max)/2` 四舍五入
 * - text_input / select → `c.value ?? ""`
 * - number_input → `c.value != null ? String(c.value) : ""`
 * - multi_select → `c.value ?? []`
 *
 * 非 input 组件（text / image / protocol_prompt）无 key，跳过。
 */
export function buildInitialFormData(components: Component[]): Record<string, unknown> {
  const data: Record<string, unknown> = {};
  for (const c of components) {
    if (!("key" in c)) continue;
    switch (c.kind) {
      case "slider":
        data[c.key] = c.value ?? Math.round((c.min + c.max) / 2);
        break;
      case "text_input":
        data[c.key] = c.value ?? "";
        break;
      case "number_input":
        data[c.key] = c.value != null ? String(c.value) : "";
        break;
      case "select":
        data[c.key] = c.value ?? "";
        break;
      case "multi_select":
        data[c.key] = c.value ?? [];
        break;
    }
  }
  return data;
}
