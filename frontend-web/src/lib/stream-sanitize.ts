// ABOUTME: 流式内容清洗，移植自 iOS CoachViewModel 的 fenced block 处理
// ABOUTME: 清除 coach_thinking/suggested_replies 块，提取结构化数据

// --- Sanitization patterns ---

const FENCED_BLOCK_RE =
  /```json:(?:coach_thinking|suggested_replies)\n[\s\S]*?(?:```|$)/g;
const TOOL_OUTPUT_RE = /\['\/user\/[^\]]*\]/g;

const THINKING_RE = /```json:coach_thinking\n(\{[\s\S]*?\})\n```/;
const REPLIES_RE = /```json:suggested_replies\n(\[[\s\S]*?\])\n```/;

// --- Types ---

export interface CoachThinking {
  strategy: string;
  observations: string[];
  actions: string[];
}

// --- Public API ---

/**
 * 移除所有内部 fenced block 和 tool output，只保留用户可见文本。
 * 流式过程中若遇到未闭合的 ``` 开头，返回空字符串防止闪烁。
 */
export function stripFencedBlocks(content: string): string {
  let text = content;
  text = text.replace(FENCED_BLOCK_RE, "");
  text = text.replace(TOOL_OUTPUT_RE, "");
  text = text.trim();
  if (text.startsWith("```")) return "";
  return text;
}

/**
 * 提取 coach_thinking 块，返回清洁文本和结构化思考数据。
 */
export function extractCoachThinking(
  content: string,
): [string, CoachThinking | null] {
  const match = content.match(THINKING_RE);
  if (!match || !match[1]) {
    return [content, null];
  }

  const cleaned = content.replace(THINKING_RE, "").trim();

  try {
    const raw = JSON.parse(match[1]) as Record<string, unknown>;
    return [
      cleaned,
      {
        strategy: (raw.strategy as string) ?? "",
        observations: Array.isArray(raw.observations) ? raw.observations : [],
        actions: Array.isArray(raw.actions) ? raw.actions : [],
      },
    ];
  } catch {
    return [cleaned, null];
  }
}

/**
 * 提取 suggested_replies 块，返回清洁文本和建议回复数组。
 */
export function extractSuggestedReplies(
  content: string,
): [string, string[]] {
  const match = content.match(REPLIES_RE);
  if (!match || !match[1]) {
    return [content, []];
  }

  const cleaned = content.replace(REPLIES_RE, "").trim();

  try {
    const arr = JSON.parse(match[1]);
    if (Array.isArray(arr) && arr.every((s) => typeof s === "string")) {
      return [cleaned, arr];
    }
    return [cleaned, []];
  } catch {
    return [cleaned, []];
  }
}
