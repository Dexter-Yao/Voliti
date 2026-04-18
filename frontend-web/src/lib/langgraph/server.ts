// ABOUTME: 服务端 LangGraph 客户端工厂
// ABOUTME: 仅在受信任边界中使用，直接连接 LANGGRAPH_API_URL 读取或转发数据

import { Client } from "@langchain/langgraph-sdk";

export function createServerLangGraphClient() {
  const apiUrl = process.env.LANGGRAPH_API_URL;
  if (!apiUrl) {
    throw new Error("服务器未配置 LANGGRAPH_API_URL。");
  }

  return new Client({
    apiUrl,
    apiKey: process.env.LANGSMITH_API_KEY,
  });
}
