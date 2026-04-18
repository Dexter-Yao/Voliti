// ABOUTME: LangGraph 代理路由
// ABOUTME: 所有请求在服务端校验 Supabase 会话，并注入受信任的 user_id 到 LangGraph 请求体

import { NextRequest, NextResponse } from "next/server";

import { getAuthenticatedUser } from "@/lib/auth/server-user";

export const runtime = "nodejs";

function getCorsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
  };
}

function jsonError(status: number, error: string) {
  return NextResponse.json({ error }, { status });
}

function isSessionType(value: unknown): value is "coaching" | "onboarding" {
  return value === "coaching" || value === "onboarding";
}

function injectTrustedUserId(body: unknown, userId: string): unknown {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return body;
  }

  const next = { ...(body as Record<string, unknown>) };

  if (
    next.configurable
    && typeof next.configurable === "object"
    && !Array.isArray(next.configurable)
  ) {
    next.configurable = {
      ...(next.configurable as Record<string, unknown>),
      user_id: userId,
    };
  }

  if (next.config && typeof next.config === "object" && !Array.isArray(next.config)) {
    const config = { ...(next.config as Record<string, unknown>) };
    const configurable =
      config.configurable && typeof config.configurable === "object" && !Array.isArray(config.configurable)
        ? (config.configurable as Record<string, unknown>)
        : {};

    const sessionType = configurable.session_type;
    if (sessionType !== undefined && !isSessionType(sessionType)) {
      throw new Error("session_type 仅支持 coaching 或 onboarding。");
    }

    config.configurable = {
      ...configurable,
      user_id: userId,
    };
    next.config = config;
  }

  if (next.metadata && typeof next.metadata === "object" && !Array.isArray(next.metadata)) {
    const metadata = { ...(next.metadata as Record<string, unknown>) };
    const sessionType = metadata.session_type;
    if (sessionType !== undefined && !isSessionType(sessionType)) {
      throw new Error("metadata.session_type 仅支持 coaching 或 onboarding。");
    }
    next.metadata = {
      ...metadata,
      user_id: userId,
    };
  }

  return next;
}

async function buildProxyRequestBody(
  request: NextRequest,
  userId: string,
): Promise<BodyInit | undefined> {
  if (!["POST", "PUT", "PATCH"].includes(request.method)) {
    return undefined;
  }

  const rawBody = await request.text();
  if (!rawBody) {
    return undefined;
  }

  const contentType = request.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return rawBody;
  }

  const parsed = JSON.parse(rawBody) as unknown;
  return JSON.stringify(injectTrustedUserId(parsed, userId));
}

function resolvePath(request: NextRequest) {
  return request.nextUrl.pathname.replace(/^\/?api\//, "");
}

async function forwardRequest(
  request: NextRequest,
  method: string,
): Promise<NextResponse> {
  const user = await getAuthenticatedUser();
  if (!user) {
    return jsonError(401, "请先登录后再继续。");
  }

  const apiUrl = process.env.LANGGRAPH_API_URL;
  if (!apiUrl) {
    return jsonError(500, "服务器未配置 LANGGRAPH_API_URL。");
  }

  try {
    const url = new URL(request.url);
    const searchParams = new URLSearchParams(url.search);
    searchParams.delete("_path");
    searchParams.delete("nxtP_path");

    const response = await fetch(
      `${apiUrl}/${resolvePath(request)}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`,
      {
        method,
        headers: {
          "Content-Type": request.headers.get("content-type") ?? "application/json",
          "x-api-key": process.env.LANGSMITH_API_KEY ?? "",
        },
        body: await buildProxyRequestBody(request, user.id),
      },
    );

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        ...Object.fromEntries(response.headers.entries()),
        ...getCorsHeaders(),
      },
    });
  } catch (error) {
    const message =
      error instanceof Error && error.message.trim()
        ? error.message
        : "LangGraph 代理请求失败。";
    return jsonError(500, message);
  }
}

export async function GET(request: NextRequest) {
  return forwardRequest(request, "GET");
}

export async function POST(request: NextRequest) {
  return forwardRequest(request, "POST");
}

export async function PUT(request: NextRequest) {
  return forwardRequest(request, "PUT");
}

export async function PATCH(request: NextRequest) {
  return forwardRequest(request, "PATCH");
}

export async function DELETE(request: NextRequest) {
  return forwardRequest(request, "DELETE");
}

export function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(),
  });
}
