// ABOUTME: 设置抽屉，包含 Onboarding 补采入口与退出登录操作
// ABOUTME: 退出登录通过 server action 调用 Supabase signOut

"use client";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { logoutAction } from "@/app/login/actions";
import { useQueryState } from "nuqs";

interface SettingsDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDrawer({ open, onOpenChange }: SettingsDrawerProps) {
  const [, setThreadId] = useQueryState("threadId");
  const [, setOnboardingEntry] = useQueryState("onboarding");

  const handleReenterOnboarding = async () => {
    onOpenChange(false);
    await setThreadId(null);
    await setOnboardingEntry("reentry");
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[320px]">
        <SheetHeader>
          <SheetTitle>设置</SheetTitle>
          <SheetDescription className="sr-only">
            账户设置与引导流程管理
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 flex flex-col gap-6">
          {/* 账户操作 */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-[#1A1816]/60">账户</h3>
            <Button
              variant="ghost"
              className="w-full justify-start text-sm text-[#1A1816]/60"
              onClick={handleReenterOnboarding}
            >
              继续了解我
            </Button>
            <form action={logoutAction}>
              <Button
                type="submit"
                variant="ghost"
                className="w-full justify-start text-sm text-red-500 hover:text-red-600"
              >
                退出登录
              </Button>
            </form>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
