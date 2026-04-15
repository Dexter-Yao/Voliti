// ABOUTME: Onboarding 桌面入口层
// ABOUTME: 仅根据外部 surface 契约决定欢迎页、等待态与全屏对话容器

"use client";

import { useState } from "react";
import { Button } from "./ui/button";
import { type OnboardingSurface } from "@/lib/onboarding-surface";
import { ONBOARDING_GREETING } from "@/lib/thread-utils";

export function OnboardingWelcome({
  children,
  surface,
  onStart,
  isStarting = false,
  toolbar,
}: {
  children: React.ReactNode;
  surface: OnboardingSurface;
  onStart?: (name: string) => void;
  isStarting?: boolean;
  toolbar?: React.ReactNode;
}) {
  const [name, setName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    await onStart?.(trimmed);
  };

  if (surface === "coaching") return <>{children}</>;

  if (surface === "conversation") {
    return (
      <div className="fixed inset-0 z-50 flex flex-col bg-[#F4EDE3]">
        {toolbar}
        {children}
      </div>
    );
  }

  if (surface === "checking") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#F4EDE3]">
        <div className="mx-auto max-w-md px-8 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-[#1A1816]">
            Voliti
          </h1>
          <p className="mt-4 font-serif-coach text-base leading-relaxed text-[#1A1816]/70">
            正在准备你的教练空间。
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#F4EDE3]">
      <div className="mx-auto max-w-md px-8">
        <h1 className="text-center text-3xl font-semibold tracking-tight text-[#1A1816]">
          Voliti
        </h1>
        <p className="mt-3 text-center font-serif-coach text-lg text-[#1A1816]/70">
          AI 减脂行为教练
        </p>

        <div className="mt-8 space-y-4 text-sm leading-relaxed text-[#1A1816]/80">
          {ONBOARDING_GREETING.split("\n\n").map((paragraph, i) => (
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
            disabled={isStarting}
            onChange={(e) => setName(e.target.value)}
            placeholder="输入你的名字"
            className="mt-2 w-full rounded-[4px] border border-[#1A1816]/10 bg-white px-4 py-3 text-sm text-[#1A1816] placeholder:text-[#1A1816]/30 focus:border-[#1A1816]/30 focus:outline-none"
          />
          <Button
            type="submit"
            disabled={!name.trim() || isStarting}
            className="mt-4 w-full bg-[#1A1816] px-8 py-3 text-[#F4F0E8] hover:bg-[#1A1816]/90 disabled:opacity-40"
          >
            {isStarting ? "正在进入对话..." : "开始对话"}
          </Button>
        </form>
      </div>
    </div>
  );
}
