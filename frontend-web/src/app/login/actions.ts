// ABOUTME: 登录/登出 server actions，验证密码并管理 cookies
// ABOUTME: 密码映射从 VOLITI_USER_MAP 环境变量读取（password:user_id 格式）

"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

function parseUserMap(): Map<string, string> {
  const raw = process.env.VOLITI_USER_MAP ?? "";
  const map = new Map<string, string>();
  for (const entry of raw.split(",")) {
    const trimmed = entry.trim();
    if (!trimmed) continue;
    const colonIdx = trimmed.indexOf(":");
    if (colonIdx <= 0) continue;
    const password = trimmed.slice(0, colonIdx);
    const userId = trimmed.slice(colonIdx + 1);
    if (password && userId) {
      map.set(password, userId);
    }
  }
  return map;
}

export async function loginAction(
  _prevState: { error: string } | null,
  formData: FormData,
): Promise<{ error: string } | null> {
  const password = formData.get("password") as string;
  if (!password) {
    return { error: "请输入访问密码" };
  }

  const userMap = parseUserMap();
  const userId = userMap.get(password);

  if (!userId) {
    return { error: "密码错误，请重试" };
  }

  // 后端要求 user_id 满足 ^[A-Za-z0-9][A-Za-z0-9_-]{7,63}$（最少 8 字符）
  const paddedUserId = userId.length >= 8 ? userId : `u_${userId.padEnd(6, "0")}`;

  const cookieStore = await cookies();
  cookieStore.set("voliti_access", paddedUserId, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30, // 30 天
  });
  // 前端可读的 user_id cookie，用于 Thread 搜索和 configurable 注入
  cookieStore.set("voliti_user_id", paddedUserId, {
    httpOnly: false,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });

  redirect("/");
}

export async function logoutAction(): Promise<never> {
  const cookieStore = await cookies();
  cookieStore.delete("voliti_access");
  cookieStore.delete("voliti_user_id");
  redirect("/login");
}
