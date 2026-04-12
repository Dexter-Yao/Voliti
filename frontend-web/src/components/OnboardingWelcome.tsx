// ABOUTME: 首次用户 Onboarding 欢迎层
// ABOUTME: localStorage 标记完成状态，点击后进入 Coach 对话

"use client";

import { useState, useEffect } from "react";
import { Button } from "./ui/button";

const ONBOARDING_KEY = "voliti_onboarding_complete";

export function OnboardingWelcome({
  children,
}: {
  children: React.ReactNode;
}) {
  const [showWelcome, setShowWelcome] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const done = localStorage.getItem(ONBOARDING_KEY);
    if (!done) {
      setShowWelcome(true);
    }
  }, []);

  const handleStart = () => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setShowWelcome(false);
  };

  // SSR: 不渲染欢迎层，直接显示内容
  if (!mounted) return <>{children}</>;

  if (!showWelcome) return <>{children}</>;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#F4F0E8]">
      <div className="mx-auto max-w-md px-8 text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-[#1A1816]">
          Voliti
        </h1>
        <p className="mt-3 font-serif-coach text-lg text-[#1A1816]/70">
          AI Fat-Loss Leadership Coach
        </p>
        <p className="mt-6 text-sm leading-relaxed text-[#1A1816]/50">
          Your personal coach for sustainable fat loss.
          <br />
          Let&apos;s start with a conversation to understand you.
        </p>
        <Button
          onClick={handleStart}
          className="mt-8 bg-[#1A1816] px-8 py-3 text-[#F4F0E8] hover:bg-[#1A1816]/90"
        >
          Start Conversation
        </Button>
      </div>
    </div>
  );
}
