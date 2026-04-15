// ABOUTME: 浏览器端 Supabase 客户端工厂
// ABOUTME: 内部 singleton，多次调用只创建一个实例

import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
