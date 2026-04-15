// ABOUTME: Onboarding 桌面壳层状态机
// ABOUTME: 统一约束全屏引导、Thread 挂载与标准 workspace 暴露时机

export type OnboardingSurface = "checking" | "welcome" | "conversation" | "coaching";
export type OnboardingEntryIntent = "none" | "reentry";

export interface OnboardingSurfaceInput {
  onboardingResolved: boolean;
  requiresOnboarding: boolean;
  onboardingConversationActive: boolean;
  onboardingEntryIntent?: OnboardingEntryIntent;
  onboardingThreadReady?: boolean;
}

export function resolveOnboardingSurface(
  input: OnboardingSurfaceInput,
): OnboardingSurface {
  const entryIntent = input.onboardingEntryIntent ?? "none";
  const onboardingThreadReady = input.onboardingThreadReady ?? false;

  if (!input.onboardingResolved) {
    return "checking";
  }

  if (
    input.onboardingConversationActive
    || (entryIntent === "reentry" && onboardingThreadReady)
  ) {
    return "conversation";
  }

  if (input.requiresOnboarding) {
    return "welcome";
  }

  if (entryIntent === "reentry") {
    return "checking";
  }

  return "coaching";
}

export function shouldMountPrimaryWorkspace(
  surface: OnboardingSurface,
): boolean {
  return surface === "conversation" || surface === "coaching";
}

export function shouldUseOnboardingThreadShell(
  surface: OnboardingSurface,
): boolean {
  return surface === "conversation";
}

export function shouldAutoEnsureCoachingThread(
  input: Pick<OnboardingSurfaceInput, "onboardingEntryIntent"> & {
    surface: OnboardingSurface;
  },
): boolean {
  return input.surface === "coaching" && (input.onboardingEntryIntent ?? "none") === "none";
}

export function shouldAutoStartReentrySession(
  input: OnboardingSurfaceInput,
): boolean {
  const entryIntent = input.onboardingEntryIntent ?? "none";
  const onboardingThreadReady = input.onboardingThreadReady ?? false;

  return (
    input.onboardingResolved
    && !input.requiresOnboarding
    && !input.onboardingConversationActive
    && !onboardingThreadReady
    && entryIntent === "reentry"
  );
}
