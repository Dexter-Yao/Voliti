// ABOUTME: 主页面入口 — Onboarding 欢迎 → Coach 对话
// ABOUTME: OnboardingWelcome 采集名字后在全屏内继续对话，完成后展示确认再切换

"use client";

import { Thread } from "@/components/thread";
import { StreamProvider, startOnboardingThread, ensureTodayThread } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { A2UIInterruptHandler } from "@/components/a2ui/A2UIInterruptHandler";
import { OnboardingWelcome } from "@/components/OnboardingWelcome";
import { Button } from "@/components/ui/button";
import { Toaster } from "@/components/ui/sonner";
import { getUserId } from "@/lib/user";
import { fetchOnboardingComplete } from "@/lib/store-sync";
import { SESSION_TYPE_COACHING } from "@/lib/thread-utils";
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useQueryState } from "nuqs";

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

function MainApp() {
  const [, setThreadId] = useQueryState("threadId");
  const [pendingName, setPendingName] = useState<string | null>(null);
  const [onboardingActive, setOnboardingActive] = useState(false);
  const [onboardingDone, setOnboardingDone] = useState(false);
  const pendingCoachingThreadRef = useRef<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const handleOnboardingStart = async (name: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
    const userId = getUserId();
    if (!apiUrl || !assistantId || !userId) return;

    const threadId = await startOnboardingThread(
      resolveUrl(apiUrl),
      userId,
      assistantId,
    );
    if (threadId) {
      setPendingName(name);
      setThreadId(threadId);
      setOnboardingActive(true);
    }
  };

  // Onboarding 完成检测：轮询 Store，检测到 onboarding_complete 后展示确认
  useEffect(() => {
    if (!onboardingActive) return;
    let cancelled = false;

    const check = async () => {
      const done = await fetchOnboardingComplete();
      if (!done || cancelled) return;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
      const userId = getUserId();
      if (!apiUrl || !assistantId || !userId) return;
      const coachingThreadId = await ensureTodayThread(
        resolveUrl(apiUrl), userId, assistantId, SESSION_TYPE_COACHING,
      );
      if (coachingThreadId && !cancelled) {
        pendingCoachingThreadRef.current = coachingThreadId;
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
  }, [onboardingActive, setThreadId]);

  const handleConfirmJourney = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    if (pendingCoachingThreadRef.current) {
      setThreadId(pendingCoachingThreadRef.current);
    }
    setOnboardingDone(false);
    window.location.reload();
  }, [setThreadId]);

  if (onboardingDone) {
    return <OnboardingComplete onConfirm={handleConfirmJourney} />;
  }

  return (
    <OnboardingWelcome
      onStart={handleOnboardingStart}
      conversationActive={onboardingActive}
    >
      <ThreadProvider>
        <StreamProvider>
          <ArtifactProvider>
            <Thread
              initialMessage={pendingName}
              onInitialMessageSent={() => setPendingName(null)}
              onboardingMode={onboardingActive}
            />
            <A2UIInterruptHandler />
          </ArtifactProvider>
        </StreamProvider>
      </ThreadProvider>
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
