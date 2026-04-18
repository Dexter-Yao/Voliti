// ABOUTME: LangGraph 提交配置测试
// ABOUTME: 锁定普通消息与 A2UI resume 必须沿用当前 session_type

import { describe, expect, it } from "vitest";

import { buildSubmitConfig } from "./stream-config";

describe("buildSubmitConfig", () => {
  it("preserves onboarding session_type for onboarding turns", () => {
    expect(buildSubmitConfig("onboarding")).toEqual({
      configurable: {
        session_type: "onboarding",
      },
    });
  });

  it("only carries the trusted session_type from the client", () => {
    expect(buildSubmitConfig("coaching")).toEqual({
      configurable: {
        session_type: "coaching",
      },
    });
  });
});
