// ABOUTME: Intervention Layout 的槽位分派纯函数（零内容解析 · 仅基于 component kind 与位置）
// ABOUTME: 从 Layout 组件中抽出以保证可测性；每个 Layout 只依赖这里的公共 helper

import type {
  Component,
  TextComponent,
  ProtocolPromptComponent,
  TextInputComponent,
  SelectComponent,
} from "@/lib/a2ui";

/**
 * 返回首个匹配指定 kind 的组件。无匹配时返回 undefined。
 * 用于所有 Layout 做"按 kind 取首个"的槽位分派。
 */
export function findFirstByKind<K extends Component["kind"]>(
  components: Component[],
  kind: K,
): Extract<Component, { kind: K }> | undefined {
  return components.find((c) => c.kind === kind) as
    | Extract<Component, { kind: K }>
    | undefined;
}

/**
 * 把首个 TextComponent 提升为"场景锚条"，剩余 component 作为流内容。
 * 用于 ScenarioLayout。若首个不是 text，anchor 为 null，所有组件都留在 rest。
 */
export function splitFirstTextAsAnchor(components: Component[]): {
  anchor: TextComponent | null;
  rest: Component[];
} {
  const [first, ...rest] = components;
  if (first && first.kind === "text") {
    return { anchor: first, rest };
  }
  return { anchor: null, rest: components };
}

/**
 * 在 ProtocolPrompt 之后寻找第一个 TextComponent（隐含判决槽位）。
 * 用于 ReframingLayout 右上栏：上层左右对比 verbatim / = / 隐含判决。
 * 若 ProtocolPrompt 不存在或其后无 text，返回 undefined。
 */
export function findVerdictTextAfterProto(
  components: Component[],
): TextComponent | undefined {
  const protoIdx = components.findIndex((c) => c.kind === "protocol_prompt");
  if (protoIdx < 0) return undefined;
  for (let i = protoIdx + 1; i < components.length; i += 1) {
    if (components[i].kind === "text") {
      return components[i] as TextComponent;
    }
  }
  return undefined;
}

/**
 * 场景预演的 IF/THEN chip 极窄模式识别。
 * 只匹配以 "IF " 开头、含 " → THEN " 的文本；不匹配即回退普通 text 渲染。
 */
export const IF_THEN_PATTERN = /^IF .+ → THEN /;

export function isIfThenText(text: string): boolean {
  return IF_THEN_PATTERN.test(text);
}

// Re-export 常用类型，便于 Layout 直接使用
export type {
  Component,
  TextComponent,
  ProtocolPromptComponent,
  TextInputComponent,
  SelectComponent,
};
