// ABOUTME: 登录/注册页，邮箱+密码认证
// ABOUTME: 支持登录/注册模式切换，使用 Supabase Auth

"use client";

import { useActionState, useState } from "react";
import { loginAction, signupAction } from "./actions";

export default function LoginPage() {
  const allowSelfSignup = process.env.NEXT_PUBLIC_ALLOW_SELF_SIGNUP === "true";
  const pilotContact = process.env.NEXT_PUBLIC_TRIAL_CONTACT;
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [loginState, loginFormAction, loginPending] = useActionState(
    loginAction,
    null,
  );
  const [signupState, signupFormAction, signupPending] = useActionState(
    signupAction,
    null,
  );

  const isLogin = !allowSelfSignup || mode === "login";
  const error = isLogin ? loginState?.error : signupState?.error;
  const isPending = isLogin ? loginPending : signupPending;

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F4F0E8]">
      <div className="w-full max-w-sm px-6">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-semibold text-[#1A1816]">Voliti</h1>
          <p className="mt-1 font-serif-coach text-sm text-[#1A1816]/60">
            AI 减脂行为教练
          </p>
          <p className="mt-4 text-xs leading-5 text-[#1A1816]/45">
            当前为邀请制试用，仅面向受邀用户开放。
            {pilotContact ? ` 账号与支持请联系 ${pilotContact}。` : ""}
          </p>
        </div>

        <form action={isLogin ? loginFormAction : signupFormAction} className="space-y-4">
          <input
            type="email"
            name="email"
            placeholder="邮箱"
            autoFocus
            required
            className="w-full rounded-[4px] border border-[#1A1816]/10 bg-transparent px-4 py-3 text-[#1A1816] placeholder:text-[#1A1816]/30 focus:border-[#B87333] focus:outline-none focus:ring-1 focus:ring-[#B87333]"
          />

          <input
            type="password"
            name="password"
            placeholder="密码"
            required
            minLength={6}
            className="w-full rounded-[4px] border border-[#1A1816]/10 bg-transparent px-4 py-3 text-[#1A1816] placeholder:text-[#1A1816]/30 focus:border-[#B87333] focus:outline-none focus:ring-1 focus:ring-[#B87333]"
          />

          {error && <p className="text-sm text-[#8B3A3A]">{error}</p>}

          <button
            type="submit"
            disabled={isPending}
            className="w-full rounded-full bg-[#1A1816] px-4 py-3 text-sm font-medium text-[#F4F0E8] transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {isPending
              ? "处理中..."
              : isLogin
                ? "登录"
                : "注册"}
          </button>
        </form>

        {allowSelfSignup && (
          <p className="mt-6 text-center text-xs text-[#1A1816]/40">
            {isLogin ? "没有账号？" : "已有账号？"}
            <button
              type="button"
              onClick={() => setMode(isLogin ? "signup" : "login")}
              className="ml-1 text-[#1A1816]/60 underline underline-offset-2 hover:text-[#1A1816]"
            >
              {isLogin ? "注册" : "登录"}
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
