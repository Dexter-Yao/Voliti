// ABOUTME: LangGraph SDK client 工厂函数
// ABOUTME: 处理相对路径 apiUrl（如 /api），在浏览器端补全 origin

import { Client } from "@langchain/langgraph-sdk";

function resolveApiUrl(apiUrl: string): string {
  // 相对路径在浏览器端需要补全 origin
  if (apiUrl.startsWith("/") && typeof window !== "undefined") {
    return `${window.location.origin}${apiUrl}`;
  }
  return apiUrl;
}

export function createClient(
  apiUrl: string,
  apiKey: string | undefined,
  authScheme: string | undefined,
) {
  return new Client({
    apiKey,
    apiUrl: resolveApiUrl(apiUrl),
    ...(authScheme && {
      defaultHeaders: {
        "X-Auth-Scheme": authScheme,
      },
    }),
  });
}
