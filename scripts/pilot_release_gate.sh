#!/usr/bin/env bash
# ABOUTME: 邀请制试用发布门槛脚本
# ABOUTME: 统一执行 backend、eval、frontend 与最终行为确认顺序，供发布前人工执行

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PID=""

cleanup() {
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}

wait_for_backend() {
  local url="http://127.0.0.1:2025/info"
  for _ in {1..60}; do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "后端在 60 秒内未启动完成：${url}" >&2
  return 1
}

trap cleanup EXIT

echo "==> backend tests"
(cd "${ROOT_DIR}/backend" && uv run python -m pytest)

echo "==> eval tests"
(cd "${ROOT_DIR}/eval" && uv run python -m pytest)

echo "==> frontend-web tests"
(cd "${ROOT_DIR}/frontend-web" && pnpm test)

echo "==> frontend-web build"
(cd "${ROOT_DIR}/frontend-web" && pnpm build)

echo "==> starting backend dev server on :2025"
(cd "${ROOT_DIR}/backend" && uv run langgraph dev --port 2025 >/tmp/voliti-langgraph.log 2>&1) &
BACKEND_PID=$!
wait_for_backend

echo "==> eval full gate"
(cd "${ROOT_DIR}/eval" && uv run python -m voliti_eval --profile full)

echo "==> eval compare gate"
(cd "${ROOT_DIR}/eval" && uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3 --profile full)

echo "==> manual report review"
echo "请检查 eval/output 中最新的 report.html 与 comparison.html，确认没有未解释的阻断项。"
