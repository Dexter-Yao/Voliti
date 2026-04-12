// ABOUTME: 主页面入口 — Onboarding 欢迎 → Coach 对话
// ABOUTME: OnboardingWelcome 采集名字后创建 onboarding thread，名字作为首条消息自动发送

"use client";

import { Thread } from "@/components/thread";
import { StreamProvider, startOnboardingThread } from "@/providers/Stream";
import { ThreadProvider } from "@/providers/Thread";
import { ArtifactProvider } from "@/components/thread/artifact";
import { A2UIInterruptHandler } from "@/components/a2ui/A2UIInterruptHandler";
import { OnboardingWelcome } from "@/components/OnboardingWelcome";
import { Toaster } from "@/components/ui/sonner";
import { getUserId } from "@/lib/user";
import React, { useState } from "react";
import { useQueryState } from "nuqs";

function MainApp() {
  const [, setThreadId] = useQueryState("threadId");
  const [pendingName, setPendingName] = useState<string | null>(null);

  const handleOnboardingStart = async (name: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const assistantId = process.env.NEXT_PUBLIC_ASSISTANT_ID;
    const userId = getUserId();
    if (!apiUrl || !assistantId || !userId) return;

    const resolvedUrl =
      apiUrl.startsWith("/") && typeof window !== "undefined"
        ? `${window.location.origin}${apiUrl}`
        : apiUrl;

    const threadId = await startOnboardingThread(
      resolvedUrl,
      userId,
      assistantId,
    );
    if (threadId) {
      setPendingName(name);
      setThreadId(threadId);
    }
  };

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
