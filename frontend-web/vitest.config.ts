// ABOUTME: Vitest 解析配置
// ABOUTME: 为 src 别名与 Next 源码测试提供统一入口

import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});
