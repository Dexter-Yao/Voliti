// ABOUTME: 主页面入口 — Onboarding 欢迎 → Coach 对话
// ABOUTME: OnboardingWelcome 采集名字后在全屏内继续对话，完成后展示确认再切换

"use client";

import { Thread } from "@/components/thread";
import { StreamProvider } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { A2UIInterruptHandler } from "@/components/a2ui/A2UIInterruptHandler";
import { OnboardingWelcome } from "@/components/OnboardingWelcome";
import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/sonner";
import { getUserId } from "@/lib/user";
import { fetchOnboardingComplete } from "@/lib/store-sync";
import {
  type OnboardingEntryIntent,
  shouldAutoStartReentrySession,
  shouldAutoEnsureCoachingThread,
  resolveOnboardingSurface,
  shouldMountPrimaryWorkspace,
  shouldUseOnboardingThreadShell,
} from "@/lib/onboarding-surface";
import { ensureTodayThread, startOnboardingThread } from "@/lib/thread-bootstrap";
import { SESSION_TYPE_COACHING, SESSION_TYPE_ONBOARDING } from "@/lib/thread-utils";
import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useQueryState } from "nuqs";
import { toast } from "sonner";

const ONBOARDING_KEY = "voliti_onboarding_complete";

function resolveUrl(apiUrl: string): string {
  return apiUrl.startsWith("/") && typeof window !== "undefined"
    ? `${window.location.origin}${apiUrl}`
    : apiUrl;
}

function OnboardingComplete({ onConfirm }: { onConfirm: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#F4EDE3]">
      <div className="mx-auto max-w-md px-8 text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-[#1A1816]">
          准备好了
        </h1>
        <p className="mt-4 font-serif-coach text-base leading-relaxed text-[#1A1816]/70">
          我已经记住了你告诉我的一切。从现在开始，我会陪你走这段路。
        </p>
        <Button
          onClick={onConfirm}
          className="mt-8 w-full bg-[#1A1816] px-8 py-3 text-[#F4F0E8] hover:bg-[#1A1816]/90"
        >
          开始旅程
        </Button>
      </div>
    </div>
  );
}

function buildCheckinTrigger(): string {
  const now = new Date();
  const time = now.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `[daily_checkin] ${time}`;
}

function MainApp() {
  const [threadId, setThreadId] = useQueryState("threadId");
  const [onboardingEntry, setOnboardingEntry] = useQueryState("onboarding");
  const [pendingName, setPendingName] = useState<string | null>(null);
  const [checkinTrigger, setCheckinTrigger] = useState<string | null>(null);
  const [onboardingResolved, setOnboardingResolved] = useState(false);
  const [requiresOnboarding, setRequiresOnboarding] = useState(false);
  const [onboardingActive, setOnboardingActive] = useState(false);
  const [startingOnboarding, setStartingOnboarding] = useState(false);
  const [onboardingDone, setOnboardingDone] = useState(false);
  const pendingCoachingThreadRef = useRef<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onboardingEntryIntent: OnboardingEntryIntent = onboardingEntry === "reentry" ? "reentry" : "none";

  useEffect(() => {
    let cancelled = false;

    const loadOnboardingState = async () => {
      try {
        const backendDone = await fetchOnboardingComplete();
        if (cancelled) return;
        if (backendDone) {
          localStorage.setItem(ONBOARDING_KEY, "true");
        }
        setRequiresOnboarding(!backendDone);
      } catch {
        if (cancelled) return;
        setRequiresOnboarding(true);
      } finally {
        if (!cancelled) {
          setOnboardingResolved(true);
        }
      }
    };

    loadOnboardingState();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleOnboardingStart = async (name: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
    const userId = getUserId();
    if (!apiUrl || !assistantId || !userId) {
      console.error("[onboarding] guard failed:", { apiUrl: !!apiUrl, assistantId: !!assistantId, userId });
      toast.error(`无法启动引导：${!apiUrl ? "缺少 API_URL" : !assistantId ? "缺少 ASSISTANT_ID" : "未获取到用户身份，请刷新页面"}`);
      return;
    }

    setStartingOnboarding(true);

    try {
      const result = await startOnboardingThread(
        resolveUrl(apiUrl),
        userId,
        assistantId,
      );
      if (!result) {
        toast.error("暂时无法进入引导对话，请重试");
        return;
      }

      setPendingName(name);
      setThreadId(result.threadId);
      setOnboardingActive(true);
    } finally {
      setStartingOnboarding(false);
    }
  };

  // Onboarding 完成检测：轮询 Store，检测到 onboarding_complete 后展示确认
  useEffect(() => {
    if (!onboardingActive || !requiresOnboarding) return;
    let cancelled = false;

    const check = async () => {
      const done = await fetchOnboardingComplete();
      if (!done || cancelled) return;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
      const userId = getUserId();
      if (!apiUrl || !assistantId || !userId) return;
      const result = await ensureTodayThread(
        resolveUrl(apiUrl), userId, assistantId, SESSION_TYPE_COACHING,
      );
      if (result && !cancelled) {
        pendingCoachingThreadRef.current = result.threadId;
        if (result.isNew) setCheckinTrigger(buildCheckinTrigger());
        setRequiresOnboarding(false);
        setOnboardingDone(true);
        setOnboardingActive(false);
      }
    };

    check();
    pollingRef.current = setInterval(check, 8000);
    return () => {
      cancelled = true;
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [onboardingActive, requiresOnboarding, setThreadId]);

  const onboardingInput = useMemo(() => ({
    onboardingResolved,
    requiresOnboarding,
    onboardingConversationActive: onboardingActive,
    onboardingEntryIntent,
    onboardingThreadReady: Boolean(threadId),
  }), [
    onboardingResolved,
    requiresOnboarding,
    onboardingActive,
    onboardingEntryIntent,
    threadId,
  ]);

  useEffect(() => {
    if (!shouldAutoStartReentrySession(onboardingInput) || startingOnboarding) return;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
    const userId = getUserId();
    if (!apiUrl || !assistantId || !userId) return;

    let cancelled = false;
    setStartingOnboarding(true);

    startOnboardingThread(resolveUrl(apiUrl), userId, assistantId)
      .then((result) => {
        if (!result || cancelled) {
          toast.error("暂时无法进入补充引导，请稍后重试");
          return;
        }
        setThreadId(result.threadId);
        setOnboardingActive(true);
      })
      .finally(() => {
        if (!cancelled) {
          setStartingOnboarding(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [onboardingInput, setThreadId, startingOnboarding]);

  const handleConfirmJourney = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    if (pendingCoachingThreadRef.current) {
      setThreadId(pendingCoachingThreadRef.current);
    }
    setOnboardingDone(false);
    window.location.reload();
  }, [setThreadId]);

  const handleNewThread = useCallback(() => {
    if (!onboardingActive) {
      setCheckinTrigger(buildCheckinTrigger());
    }
  }, [onboardingActive]);

  const initialMessage = pendingName ?? checkinTrigger;
  const handleInitialMessageSent = useCallback(() => {
    setPendingName(null);
    setCheckinTrigger(null);
  }, []);

  const onboardingSurface = resolveOnboardingSurface(onboardingInput);
  const autoEnsureCoachingThread = shouldAutoEnsureCoachingThread({
    surface: onboardingSurface,
    onboardingEntryIntent,
  });
  const mountPrimaryWorkspace = shouldMountPrimaryWorkspace(onboardingSurface);
  const onboardingThreadShell = shouldUseOnboardingThreadShell(onboardingSurface);

  const handleExitReentry = useCallback(async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
    const userId = getUserId();
    if (!apiUrl || !assistantId || !userId) return;

    const result = await ensureTodayThread(
      resolveUrl(apiUrl), userId, assistantId, SESSION_TYPE_COACHING,
    );
    if (!result) {
      toast.error("暂时无法返回教练主页，请重试");
      return;
    }
    if (result.isNew) {
      setCheckinTrigger(buildCheckinTrigger());
    }
    setOnboardingActive(false);
    setOnboardingEntry(null);
    setThreadId(result.threadId);
  }, [setOnboardingEntry, setThreadId]);

  if (onboardingDone) {
    return <OnboardingComplete onConfirm={handleConfirmJourney} />;
  }

  return (
    <OnboardingWelcome
      surface={onboardingSurface}
      onStart={handleOnboardingStart}
      isStarting={startingOnboarding}
      toolbar={onboardingEntryIntent === "reentry" ? (
        <div className="flex justify-end px-4 pt-4">
          <Button
            variant="ghost"
            className="text-[#1A1816]/60 hover:text-[#1A1816]"
            onClick={handleExitReentry}
          >
            返回主页
          </Button>
        </div>
      ) : undefined}
    >
      {mountPrimaryWorkspace ? (
        <ThreadProvider>
          <StreamProvider
            autoEnsureThread={autoEnsureCoachingThread}
            onNewThread={handleNewThread}
          >
            <ArtifactProvider>
              <Thread
                initialMessage={initialMessage}
                onInitialMessageSent={handleInitialMessageSent}
                onboardingMode={onboardingThreadShell}
              />
              <A2UIInterruptHandler
                sessionType={onboardingThreadShell ? SESSION_TYPE_ONBOARDING : SESSION_TYPE_COACHING}
              />
            </ArtifactProvider>
          </StreamProvider>
        </ThreadProvider>
      ) : null}
    </OnboardingWelcome>
  );
}

export default function DemoPage(): React.ReactNode {
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <Toaster />
      <MainApp />
    </React.Suspense>
  );
}
