// ABOUTME: store-sync 请求头纯函数测试
// ABOUTME: 锁定 coach-context 调用时的用户本地日期与时区透传

import { describe, expect, it } from "vitest";

import { buildCoachContextRequestHeaders } from "./store-sync";

describe("buildCoachContextRequestHeaders", () => {
  it("formats YYYY-MM-DD from the caller-provided local timezone", () => {
    expect(
      buildCoachContextRequestHeaders(
        new Date("2026-04-21T16:30:00.000Z"),
        "Asia/Shanghai",
      ),
    ).toEqual({
      "x-voliti-user-timezone": "Asia/Shanghai",
      "x-voliti-user-today": "2026-04-22",
    });
  });
});
