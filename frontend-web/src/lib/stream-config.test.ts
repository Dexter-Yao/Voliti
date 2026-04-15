// ABOUTME: LangGraph 提交配置测试
// ABOUTME: 锁定普通消息与 A2UI resume 必须沿用当前 session_type

import { describe, expect, it } from "vitest";

import { buildSubmitConfig } from "./stream-config";

describe("buildSubmitConfig", () => {
  it("preserves onboarding session_type for onboarding turns", () => {
    expect(buildSubmitConfig("u_dexter", "onboarding")).toEqual({
      configurable: {
        user_id: "u_dexter",
        session_type: "onboarding",
      },
    });
  });

  it("falls back to an empty user_id when the device identity is missing", () => {
    expect(buildSubmitConfig(null, "coaching")).toEqual({
      configurable: {
        user_id: "",
        session_type: "coaching",
      },
    });
  });
});
