// ABOUTME: coach-context route 契约测试
// ABOUTME: 锁定 plan-view 上游错误分流与用户本地日期透传

import { beforeEach, describe, expect, it, vi } from "vitest";

const getAuthenticatedUserMock = vi.fn();
const getItemMock = vi.fn();
const searchItemsMock = vi.fn();

vi.mock("@/lib/auth/server-user", () => ({
  getAuthenticatedUser: getAuthenticatedUserMock,
}));

vi.mock("@/lib/langgraph/server", () => ({
  createServerLangGraphClient: vi.fn(() => ({
    store: {
      getItem: getItemMock,
      searchItems: searchItemsMock,
    },
  })),
}));

describe("coach-context route", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
    getAuthenticatedUserMock.mockReset();
    getItemMock.mockReset();
    searchItemsMock.mockReset();

    getAuthenticatedUserMock.mockResolvedValue({ id: "user_0001" });
    getItemMock.mockResolvedValue(null);
    searchItemsMock.mockResolvedValue({ items: [] });
  });

  it("forwards the user-local today header to /plan-view", async () => {
    vi.stubEnv("LANGGRAPH_API_URL", "http://127.0.0.1:2025");
    vi.stubEnv("LANGSMITH_API_KEY", "test-key");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: "Plan 尚未创建" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      }),
    );

    const { GET } = await import("./route");
    await GET(
      new Request("http://localhost/api/me/coach-context", {
        headers: {
          "x-voliti-user-today": "2026-04-22",
          "x-voliti-user-timezone": "Asia/Shanghai",
        },
      }) as any,
    );

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/plan-view/user_0001?today=2026-04-22"),
      expect.objectContaining({
        cache: "no-store",
        headers: expect.objectContaining({
          accept: "application/json",
          "x-api-key": "test-key",
        }),
      }),
    );
  });

  it("returns a degraded no_plan payload when /plan-view responds 404", async () => {
    vi.stubEnv("LANGGRAPH_API_URL", "http://127.0.0.1:2025");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: "Plan 尚未创建" }), {
        status: 404,
        headers: { "content-type": "application/json" },
      }),
    );

    const { GET } = await import("./route");
    const response = await GET(
      new Request("http://localhost/api/me/coach-context", {
        headers: { "x-voliti-user-today": "2026-04-22" },
      }) as any,
    );
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.plan).toBeNull();
    expect(body.planView).toBeNull();
    expect(body.planDegradedReason).toBe("no_plan");
  });

  it("surfaces plan-view upstream failures instead of flattening them into no_plan", async () => {
    vi.stubEnv("LANGGRAPH_API_URL", "http://127.0.0.1:2025");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ error: "boom" }), {
        status: 500,
        headers: { "content-type": "application/json" },
      }),
    );

    const { GET } = await import("./route");
    const response = await GET(
      new Request("http://localhost/api/me/coach-context", {
        headers: { "x-voliti-user-today": "2026-04-22" },
      }) as any,
    );
    const body = await response.json();

    expect(response.status).toBe(502);
    expect(body.error).toContain("plan_view");
  });
});
