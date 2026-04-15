// ABOUTME: 服务端 Supabase 客户端工厂（Server Component / Server Action / Route Handler）
// ABOUTME: 每次请求必须新建实例，不可跨请求复用

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Server Component 调用时忽略——middleware 会负责刷新 session
          }
        },
      },
    },
  );
}
