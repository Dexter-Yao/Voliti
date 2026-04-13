// ABOUTME: 设置抽屉，包含重置引导流程和退出登录操作
// ABOUTME: 退出登录通过 server action 清除 httpOnly cookie

"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { logoutAction } from "@/app/login/actions";

interface SettingsDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDrawer({ open, onOpenChange }: SettingsDrawerProps) {
  const handleResetOnboarding = () => {
    localStorage.removeItem("voliti_onboarding_complete");
    window.location.reload();
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[320px]">
        <SheetHeader>
          <SheetTitle>设置</SheetTitle>
        </SheetHeader>

        <div className="mt-6 flex flex-col gap-6">
          {/* 账户操作 */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-[#1A1816]/60">账户</h3>
            <Button
              variant="ghost"
              className="w-full justify-start text-sm text-[#1A1816]/60"
              onClick={handleResetOnboarding}
            >
              重置引导流程
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
