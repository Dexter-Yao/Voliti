// ABOUTME: 流式内容清洗
// ABOUTME: 移除 tool output 和 error 信息，只保留用户可见文本

const TOOL_OUTPUT_RE = /\['\/user\/[^\]]*\]/g;
const TOOL_ERROR_RE =
  /Error invoking tool '[^']*' with kwargs \{[^}]*\} with error:[^\n]*/g;

/**
 * 移除 tool output 和 error 信息，只保留用户可见文本。
 */
export function stripInternalOutput(content: string): string {
  let text = content;
  text = text.replace(TOOL_OUTPUT_RE, "");
  text = text.replace(TOOL_ERROR_RE, "");
  return text.trim();
}
