// ABOUTME: 设置抽屉面板，包含 Thinking 开关、重置 Onboarding、登出
// ABOUTME: 登出通过 server action 正确清除 httpOnly cookie

"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useQueryState, parseAsBoolean } from "nuqs";
import { logoutAction } from "@/app/login/actions";

interface SettingsDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDrawer({ open, onOpenChange }: SettingsDrawerProps) {
  const [hideToolCalls, setHideToolCalls] = useQueryState(
    "hideToolCalls",
    parseAsBoolean.withDefault(false),
  );

  const handleResetOnboarding = () => {
    localStorage.removeItem("voliti_onboarding_complete");
    window.location.reload();
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[320px]">
        <SheetHeader>
          <SheetTitle>Settings</SheetTitle>
        </SheetHeader>

        <div className="mt-6 flex flex-col gap-6">
          {/* Display settings */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-[#1A1816]/60">Display</h3>
            <div className="flex items-center justify-between">
              <Label
                htmlFor="hide-tool-calls"
                className="text-sm text-[#1A1816]"
              >
                Hide Tool Calls
              </Label>
              <Switch
                id="hide-tool-calls"
                checked={hideToolCalls ?? false}
                onCheckedChange={setHideToolCalls}
              />
            </div>
          </div>

          <Separator />

          {/* Account actions */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-[#1A1816]/60">Account</h3>
            <Button
              variant="ghost"
              className="w-full justify-start text-sm text-[#1A1816]/60"
              onClick={handleResetOnboarding}
            >
              Reset Onboarding
            </Button>
            <form action={logoutAction}>
              <Button
                type="submit"
                variant="ghost"
                className="w-full justify-start text-sm text-red-500 hover:text-red-600"
              >
                Log Out
              </Button>
            </form>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
