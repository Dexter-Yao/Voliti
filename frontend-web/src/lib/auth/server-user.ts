// ABOUTME: 服务端已登录用户读取辅助函数
// ABOUTME: 统一为 Route Handler 和 Server Action 提供受信任的 Supabase 用户边界

import type { User } from "@supabase/supabase-js";

import { createClient } from "@/lib/supabase/server";

export async function getAuthenticatedUser(): Promise<User | null> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return user;
}
