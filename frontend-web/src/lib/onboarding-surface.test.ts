// ABOUTME: Onboarding 桌面壳层契约测试
// ABOUTME: 以纯状态机约束 workspace 挂载时机与全屏对话阶段

import { describe, expect, it } from "vitest";

import {
  type OnboardingSurfaceInput,
  resolveOnboardingSurface,
  shouldAutoEnsureCoachingThread,
  shouldAutoStartReentrySession,
  shouldMountPrimaryWorkspace,
  shouldUseOnboardingThreadShell,
} from "./onboarding-surface";

function makeInput(
  overrides: Partial<OnboardingSurfaceInput> = {},
): OnboardingSurfaceInput {
  return {
    onboardingResolved: true,
    requiresOnboarding: false,
    onboardingConversationActive: false,
    onboardingEntryIntent: "none",
    onboardingThreadReady: false,
    ...overrides,
  };
}

describe("onboarding surface contract", () => {
  it("blocks the primary workspace before onboarding status resolves", () => {
    const input = makeInput({ onboardingResolved: false });
    const surface = resolveOnboardingSurface(input);

    expect(surface).toBe("checking");
    expect(shouldAutoEnsureCoachingThread({ surface, onboardingEntryIntent: input.onboardingEntryIntent })).toBe(false);
    expect(shouldAutoStartReentrySession(input)).toBe(false);
    expect(shouldMountPrimaryWorkspace(surface)).toBe(false);
    expect(shouldUseOnboardingThreadShell(surface)).toBe(false);
  });

  it("keeps new users on the welcome surface before the onboarding thread starts", () => {
    const input = makeInput({ requiresOnboarding: true });
    const surface = resolveOnboardingSurface(input);

    expect(surface).toBe("welcome");
    expect(shouldAutoEnsureCoachingThread({ surface, onboardingEntryIntent: input.onboardingEntryIntent })).toBe(false);
    expect(shouldAutoStartReentrySession(input)).toBe(false);
    expect(shouldMountPrimaryWorkspace(surface)).toBe(false);
    expect(shouldUseOnboardingThreadShell(surface)).toBe(false);
  });

  it("switches to the full-screen onboarding conversation surface after the onboarding thread starts", () => {
    const input = makeInput({
      requiresOnboarding: true,
      onboardingConversationActive: true,
    });
    const surface = resolveOnboardingSurface(input);

    expect(surface).toBe("conversation");
    expect(shouldAutoEnsureCoachingThread({ surface, onboardingEntryIntent: input.onboardingEntryIntent })).toBe(false);
    expect(shouldAutoStartReentrySession(input)).toBe(false);
    expect(shouldMountPrimaryWorkspace(surface)).toBe(true);
    expect(shouldUseOnboardingThreadShell(surface)).toBe(true);
  });

  it("allows the standard coaching workspace only after onboarding is no longer required", () => {
    const input = makeInput();
    const surface = resolveOnboardingSurface(input);

    expect(surface).toBe("coaching");
    expect(shouldAutoEnsureCoachingThread({ surface, onboardingEntryIntent: input.onboardingEntryIntent })).toBe(true);
    expect(shouldAutoStartReentrySession(input)).toBe(false);
    expect(shouldMountPrimaryWorkspace(surface)).toBe(true);
    expect(shouldUseOnboardingThreadShell(surface)).toBe(false);
  });

  it("suppresses the standard workspace while settings re-entry is waiting to start", () => {
    const input = makeInput({ onboardingEntryIntent: "reentry" });
    const surface = resolveOnboardingSurface(input);

    expect(surface).toBe("checking");
    expect(shouldAutoEnsureCoachingThread({ surface, onboardingEntryIntent: input.onboardingEntryIntent })).toBe(false);
    expect(shouldAutoStartReentrySession(input)).toBe(true);
    expect(shouldMountPrimaryWorkspace(surface)).toBe(false);
  });

  it("keeps settings re-entry on the full-screen onboarding surface once the onboarding thread is ready", () => {
    const input = makeInput({
      onboardingEntryIntent: "reentry",
      onboardingThreadReady: true,
    });
    const surface = resolveOnboardingSurface(input);

    expect(surface).toBe("conversation");
    expect(shouldAutoEnsureCoachingThread({ surface, onboardingEntryIntent: input.onboardingEntryIntent })).toBe(false);
    expect(shouldAutoStartReentrySession(input)).toBe(false);
    expect(shouldUseOnboardingThreadShell(surface)).toBe(true);
  });
});
