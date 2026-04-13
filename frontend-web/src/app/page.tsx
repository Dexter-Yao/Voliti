// ABOUTME: 主页面入口 — Onboarding 欢迎 → Coach 对话
// ABOUTME: OnboardingWelcome 采集名字后创建 onboarding thread，名字作为首条消息自动发送

"use client";

import { Thread } from "@/components/thread";
import { StreamProvider, startOnboardingThread, ensureTodayThread } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { A2UIInterruptHandler } from "@/components/a2ui/A2UIInterruptHandler";
import { OnboardingWelcome } from "@/components/OnboardingWelcome";
import { Toaster } from "@/components/ui/sonner";
import { getUserId } from "@/lib/user";
import { fetchOnboardingComplete } from "@/lib/store-sync";
import { SESSION_TYPE_COACHING } from "@/lib/thread-utils";
import React, { useState, useEffect, useRef } from "react";
import { useQueryState } from "nuqs";

function resolveUrl(apiUrl: string): string {
  return apiUrl.startsWith("/") && typeof window !== "undefined"
    ? `${window.location.origin}${apiUrl}`
    : apiUrl;
}

function MainApp() {
  const [, setThreadId] = useQueryState("threadId");
  const [pendingName, setPendingName] = useState<string | null>(null);
  const [onboardingActive, setOnboardingActive] = useState(false);
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

  // Onboarding 完成检测：轮询 Store，检测到 onboarding_complete 后切换 coaching thread
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
        setThreadId(coachingThreadId);
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

  return (
    <OnboardingWelcome onStart={handleOnboardingStart}>
      <ThreadProvider>
        <StreamProvider>
          <ArtifactProvider>
            <Thread initialMessage={pendingName} onInitialMessageSent={() => setPendingName(null)} />
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
