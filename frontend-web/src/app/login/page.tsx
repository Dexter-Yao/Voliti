// ABOUTME: 密码登录页，10 位早期用户通过密码进入
// ABOUTME: 使用 server action 验证密码，设置 cookie 后跳转主页

"use client";

import { useActionState } from "react";
import { loginAction } from "./actions";

export default function LoginPage() {
  const [state, formAction, isPending] = useActionState(loginAction, null);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F4F0E8]">
      <div className="w-full max-w-sm px-6">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-[#1A1816]">Voliti</h1>
          <p className="mt-1 font-serif-coach text-sm text-[#1A1816]/60">AI 减脂教练</p>
          <p className="mt-3 text-xs text-[#1A1816]/40">
            早期体验，请输入访问密码
          </p>
        </div>

        <form action={formAction} className="space-y-4">
          <input
            type="password"
            name="password"
            placeholder="访问密码"
            autoFocus
            required
            className="w-full rounded-[4px] border border-[#1A1816]/10 bg-white px-4 py-3 text-[#1A1816] placeholder:text-[#1A1816]/30 focus:border-[#B87333] focus:outline-none focus:ring-1 focus:ring-[#B87333]"
          />

          {state?.error && (
            <p className="text-sm text-red-600">{state.error}</p>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full rounded-none bg-[#1A1816] px-4 py-3 text-sm font-medium text-[#F4F0E8] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isPending ? "验证中..." : "进入"}
          </button>
        </form>
      </div>
    </div>
  );
}
