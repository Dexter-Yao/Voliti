// ABOUTME: Onboarding 欢迎层 — Coach 自我介绍 + 名字采集
// ABOUTME: 名字提交后以 session_type=onboarding 创建 thread，完成后由 Store 驱动退出

"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import { fetchOnboardingComplete } from "@/lib/store-sync";

const ONBOARDING_KEY = "voliti_onboarding_complete";

const GREETING_ZH = `你好。

我是 Voliti Coach——你的减脂教练。

无论是每天该怎么吃、怎么动，还是突然想放弃时该怎么办，我都会陪着你。不过我最擅长的，是帮你在压力、疲劳、冲动来袭的那些时刻，守住你自己已经做出的选择。

我会记住你的习惯、你容易失控的场景、你在意的那个身份。然后在关键时候提醒你——你想成为的那个人会怎么做。`;

export function useOnboardingState() {
  const [needsOnboarding, setNeedsOnboarding] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const done = localStorage.getItem(ONBOARDING_KEY);
    if (done) return;

    // localStorage 未标记完成时，查询后端确认
    fetchOnboardingComplete().then((backendDone) => {
      if (backendDone) {
        localStorage.setItem(ONBOARDING_KEY, "true");
      } else {
        setNeedsOnboarding(true);
      }
    }).catch(() => {
      setNeedsOnboarding(true);
    });
  }, []);

  const markComplete = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setNeedsOnboarding(false);
  }, []);

  return { needsOnboarding, mounted, markComplete };
}

export function OnboardingWelcome({
  children,
  onStart,
}: {
  children: React.ReactNode;
  onStart?: (name: string) => void;
}) {
  const { needsOnboarding, mounted, markComplete } = useOnboardingState();
  const [name, setName] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    onStart?.(trimmed);
    markComplete();
  };

  if (!mounted) return <>{children}</>;
  if (!needsOnboarding) return <>{children}</>;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#F4EDE3]">
      <div className="mx-auto max-w-md px-8">
        <h1 className="text-center text-3xl font-semibold tracking-tight text-[#1A1816]">
          Voliti
        </h1>
        <p className="mt-3 text-center font-serif-coach text-lg text-[#1A1816]/70">
          AI 减脂教练
        </p>

        <div className="mt-8 space-y-4 text-sm leading-relaxed text-[#1A1816]/80">
          {GREETING_ZH.split("\n\n").map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="mt-8">
          <label
            htmlFor="onboarding-name"
            className="block text-sm font-medium text-[#1A1816]/50"
          >
            怎么称呼你？
          </label>
          <input
            id="onboarding-name"
            type="text"
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="输入你的名字"
            className="mt-2 w-full rounded-lg border border-[#1A1816]/10 bg-white px-4 py-3 text-sm text-[#1A1816] placeholder:text-[#1A1816]/30 focus:border-[#1A1816]/30 focus:outline-none"
          />
          <Button
            type="submit"
            disabled={!name.trim()}
            className="mt-4 w-full bg-[#1A1816] px-8 py-3 text-[#F4F0E8] hover:bg-[#1A1816]/90 disabled:opacity-40"
          >
            开始对话
          </Button>
        </form>
      </div>
    </div>
  );
}
