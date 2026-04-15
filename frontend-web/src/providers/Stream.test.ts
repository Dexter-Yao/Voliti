// ABOUTME: Stream 线程创建契约测试
// ABOUTME: 锁定 coaching 日线程复用与 onboarding 显式新建的边界

import { beforeEach, describe, expect, it, vi } from "vitest";

const createMock = vi.fn();
const searchMock = vi.fn();

vi.mock("../lib/user", () => ({
  getTodayDateString: vi.fn(() => "2026-04-15"),
}));

vi.mock("../providers/client", () => ({
  createClient: vi.fn(() => ({
    threads: {
      create: createMock,
      search: searchMock,
    },
  })),
}));

describe("thread bootstrap contract", () => {
  beforeEach(() => {
    createMock.mockReset();
    searchMock.mockReset();
  });

  it("reuses the same-day coaching thread when one already exists", async () => {
    const { ensureTodayThread } = await import("../lib/thread-bootstrap");

    searchMock.mockResolvedValue([{ thread_id: "coach-existing" }]);

    const result = await ensureTodayThread(
      "http://127.0.0.1:2025",
      "u_dexter",
      "coach",
    );

    expect(searchMock).toHaveBeenCalledWith({
      metadata: {
        user_id: "u_dexter",
        date: "2026-04-15",
        session_type: "coaching",
      },
      limit: 1,
    });
    expect(createMock).not.toHaveBeenCalled();
    expect(result).toEqual({ threadId: "coach-existing", isNew: false });
  });

  it("creates a fresh onboarding thread instead of reusing a same-day one", async () => {
    const { startOnboardingThread } = await import("../lib/thread-bootstrap");

    createMock.mockResolvedValue({ thread_id: "onboarding-fresh" });
    searchMock.mockResolvedValue([{ thread_id: "onboarding-existing" }]);

    const result = await startOnboardingThread(
      "http://127.0.0.1:2025",
      "u_dexter",
      "coach",
    );

    expect(searchMock).not.toHaveBeenCalled();
    expect(createMock).toHaveBeenCalledTimes(1);
    expect(createMock).toHaveBeenCalledWith({
      metadata: expect.objectContaining({
        user_id: "u_dexter",
        date: "2026-04-15",
        session_type: "onboarding",
        graph_id: "coach",
        segment_status: "active",
      }),
    });
    expect(result).toEqual({ threadId: "onboarding-fresh", isNew: true });
  });
});
