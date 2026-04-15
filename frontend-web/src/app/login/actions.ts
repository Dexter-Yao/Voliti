// ABOUTME: 登录/注册/登出 server actions，使用 Supabase Auth
// ABOUTME: 邮箱+密码认证，session 由 Supabase SSR 自动管理

"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

export async function loginAction(
  _prevState: { error: string } | null,
  formData: FormData,
): Promise<{ error: string }> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (!email || !password) {
    return { error: "请填写邮箱和密码" };
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    return { error: "邮箱或密码错误" };
  }

  revalidatePath("/", "layout");
  redirect("/");
}

export async function signupAction(
  _prevState: { error: string } | null,
  formData: FormData,
): Promise<{ error: string }> {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  if (!email || !password) {
    return { error: "请填写邮箱和密码" };
  }

  if (password.length < 6) {
    return { error: "密码至少 6 位" };
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signUp({ email, password });

  if (error) {
    return { error: error.message };
  }

  revalidatePath("/", "layout");
  redirect("/");
}

export async function logoutAction(): Promise<never> {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}
