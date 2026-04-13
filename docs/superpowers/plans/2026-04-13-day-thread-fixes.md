# 天级 Thread 重组后修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复天级 Thread 重组后的 6 个已确认问题 — 跨用户状态污染、封存绕过、时区不一致、Pipeline 触发、常量唯一事实

**Architecture:** 6 个独立修复，无相互依赖。每个 Task 可独立 commit。Pipeline 触发通过 LangGraph 官方 Cron API 实现（graph node 包装现有 pipeline 函数）。前端常量集中到 `thread-utils.ts`，不新建文件。

**Tech Stack:** Python 3.12+ / DeepAgent 0.4.x / LangGraph SDK / Next.js 15 / TypeScript

---

### Task 1: BriefingMiddleware 实例级状态 → 请求级状态

DeepAgent 的 `CompiledStateGraph` 是进程级单例，挂载的 middleware 实例也是单例。`_loaded = True` 在第一个用户请求后永久保持，后续所有用户的 briefing 加载被跳过。DeepAgent 官方的 `MemoryMiddleware` 用 state 级别判断（`"memory_contents" in state`），不用实例变量。

**Files:**
- Modify: `backend/src/voliti/middleware/briefing.py:28-33, 86-107, 120-126`
- Test: `backend/tests/test_briefing_middleware.py`

- [ ] **Step 1: 更新 test_briefing_middleware.py — 添加跨请求隔离测试**

在已有测试文件末尾添加：

```python
def test_briefing_reloads_per_request(mock_backend_with_briefing):
    """验证 middleware 在每次 wrap_model_call 时重新加载（非实例缓存）。"""
    mw = BriefingMiddleware()
    mock_backend = mock_backend_with_briefing

    # 第一次请求
    request1 = _make_request(state={}, runtime=MagicMock())
    mw._resolve_backend = MagicMock(return_value=mock_backend)
    with patch("voliti.middleware.briefing.get_session_type", return_value="coaching"):
        mw.wrap_model_call(request1, lambda r: r)
    assert mw.should_inject() is True

    # 重置 — 模拟新请求（新用户），briefing 文件不同
    mw._briefing = None  # 清除上一次的结果
    empty_backend = MagicMock()
    empty_backend.download_files.return_value = [MagicMock(error="file_not_found", content=None)]
    mw._resolve_backend = MagicMock(return_value=empty_backend)

    request2 = _make_request(state={}, runtime=MagicMock())
    with patch("voliti.middleware.briefing.get_session_type", return_value="coaching"):
        mw.wrap_model_call(request2, lambda r: r)
    # 第二次请求应该重新加载（不复用第一次的结果）
    assert mw.should_inject() is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && uv run python -m pytest tests/test_briefing_middleware.py::test_briefing_reloads_per_request -v`
Expected: FAIL — 因为当前 `_loaded = True` 跳过了第二次加载

- [ ] **Step 3: 修改 BriefingMiddleware — 移除 `_loaded`，每次请求重新加载**

```python
class BriefingMiddleware(PromptInjectionMiddleware):
    """预计算 Briefing 注入 Middleware。"""

    def __init__(self, *, backend: BACKEND_TYPES | None = None) -> None:
        super().__init__()
        self._backend = backend
        self._briefing: str | None = None

    # should_inject / get_prompt / _resolve_backend / _download_briefing / _adownload_briefing 不变

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        self._briefing = None
        if get_session_type() != "onboarding":
            backend = self._resolve_backend(state=request.state, runtime=request.runtime)
            if backend is not None:
                self._briefing = self._download_briefing(backend)
                if self._briefing:
                    logger.debug("BriefingMW: briefing loaded (%d chars)", len(self._briefing))
        return super().wrap_model_call(request, handler)

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        self._briefing = None
        if get_session_type() != "onboarding":
            backend = self._resolve_backend(state=request.state, runtime=request.runtime)
            if backend is not None:
                self._briefing = await self._adownload_briefing(backend)
                if self._briefing:
                    logger.debug("BriefingMW: briefing loaded (%d chars)", len(self._briefing))
        return await super().awrap_model_call(request, handler)
```

关键变更：删除 `_loaded` 标志和 `_maybe_load_sync` / `_maybe_load_async` 方法。每次 `wrap_model_call` 先重置 `_briefing = None`，然后重新加载。Briefing 文件很小（<500 bytes），Store 读取是本地操作，重复读取开销可忽略。

- [ ] **Step 4: 同步删除旧的 `_maybe_load_sync` 和 `_maybe_load_async` 方法**

删除 `briefing.py:86-118` 的 `_maybe_load_sync` 和 `_maybe_load_async` 方法。

- [ ] **Step 5: 更新已有测试 — 移除对 `_loaded` 的断言**

在 `test_briefing_middleware.py` 中搜索所有 `_loaded` 引用并删除。调整使用 `_maybe_load_sync` 的测试改为直接调用 `wrap_model_call`。

- [ ] **Step 6: 运行全部测试**

Run: `cd backend && uv run python -m pytest tests/test_briefing_middleware.py -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/voliti/middleware/briefing.py backend/tests/test_briefing_middleware.py
git commit -m "fix: BriefingMW 每次请求重新加载 — 消除实例级状态跨用户污染"
```

---

### Task 2: handleRegenerate 封存守卫

`handleSubmit` 有 `isSealed` 守卫，但 `handleRegenerate` 没有。用户查看已封存的历史 thread 时可通过"重新生成"向已封存 thread 发送请求。

**Files:**
- Modify: `frontend-web/src/components/thread/index.tsx:250`

- [ ] **Step 1: 在 handleRegenerate 添加 isSealed 守卫**

```typescript
  const handleRegenerate = (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    if (isSealed) return;
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
      streamSubgraphs: true,
      streamResumable: true,
    });
  };
```

只加第一行 `if (isSealed) return;`。

- [ ] **Step 2: 验证构建**

Run: `cd frontend-web && pnpm build`
Expected: 构建成功

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/thread/index.tsx
git commit -m "fix: handleRegenerate 添加 isSealed 守卫 — 防止封存 thread 被重新生成"
```

---

### Task 3: 前后端时区统一

前端 `getTodayDateString()` 用浏览器本地时间。后端 `day_end.py` 和 `briefing.py` 用 UTC。UTC+8 用户在 00:00-08:00 间使用时，前后端对"今天"的定义不同。

修复策略：后端从 thread metadata 读取 `timezone` 字段（前端创建 thread 时已写入 `Intl.DateTimeFormat().resolvedOptions().timeZone`），用它计算日期。前端不需改动。

**Files:**
- Modify: `backend/src/voliti/pipeline/day_end.py:187-188`
- Modify: `backend/src/voliti/briefing.py:214`
- Test: `backend/tests/test_day_end_pipeline.py`

- [ ] **Step 1: 在 day_end.py 顶部添加 zoneinfo import**

```python
from zoneinfo import ZoneInfo
```

- [ ] **Step 2: 修改 run_day_end_pipeline 接受 timezone 参数**

```python
async def run_day_end_pipeline(
    client: Any,
    *,
    user_id: str,
    namespace: tuple[str, ...],
    today: str | None = None,
    now: datetime | None = None,
    user_timezone: str | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if today is None:
        if user_timezone:
            try:
                tz = ZoneInfo(user_timezone)
                today = now.astimezone(tz).strftime("%Y-%m-%d")
            except (KeyError, ValueError):
                today = now.strftime("%Y-%m-%d")
        else:
            today = now.strftime("%Y-%m-%d")
    # ... 余下逻辑不变
```

- [ ] **Step 3: 修改 briefing.py 的 compute_and_write_briefing 同样接受 timezone**

```python
async def compute_and_write_briefing(
    *,
    client: Any,
    user_id: str,
    namespace: tuple[str, ...],
    threads: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
    user_timezone: str | None = None,
) -> str | None:
    now = now or datetime.now(timezone.utc)
    # user_timezone 用于 format_briefing 中的日期显示
    # ... 传递给需要日期计算的下游函数
```

- [ ] **Step 4: 添加时区测试**

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

async def test_pipeline_uses_user_timezone():
    """UTC+8 用户在 UTC 00:30（本地 08:30）时，today 应为本地日期。"""
    utc_time = datetime(2026, 4, 13, 0, 30, tzinfo=timezone.utc)
    # UTC 04-13 00:30 = 北京时间 04-13 08:30 → today 应为 "2026-04-13"
    result = await run_day_end_pipeline(
        client=mock_client,
        user_id="test_user_1",
        namespace=("voliti", "test_user_1"),
        now=utc_time,
        user_timezone="Asia/Shanghai",
    )
    assert result["today"] == "2026-04-13"

async def test_pipeline_utc_fallback_without_timezone():
    """无时区时回退到 UTC。"""
    utc_time = datetime(2026, 4, 13, 0, 30, tzinfo=timezone.utc)
    result = await run_day_end_pipeline(
        client=mock_client,
        user_id="test_user_1",
        namespace=("voliti", "test_user_1"),
        now=utc_time,
    )
    assert result["today"] == "2026-04-13"
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && uv run python -m pytest tests/test_day_end_pipeline.py -v`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/voliti/pipeline/day_end.py backend/src/voliti/briefing.py backend/tests/test_day_end_pipeline.py
git commit -m "fix: 后端 Pipeline 支持用户时区 — 从 thread metadata timezone 字段读取"
```

---

### Task 4: formatDateLabel 时区修复

`history/index.tsx:53` 用 `yesterday.toISOString().slice(0, 10)` 计算昨天日期。`.toISOString()` 返回 UTC，在 UTC+8 会偏移一天。

**Files:**
- Modify: `frontend-web/src/components/thread/history/index.tsx:46-55`

- [ ] **Step 1: 修改 formatDateLabel 用本地时间计算昨天**

```typescript
function formatDateLabel(dateStr: string): string {
  try {
    const date = new Date(dateStr + "T00:00:00");
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, "0")}-${String(yesterday.getDate()).padStart(2, "0")}`;
    if (dateStr === yesterdayStr) {
      return "Yesterday";
    }

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}
```

关键变更：不用 `.toISOString().slice(0, 10)`，改用与 `getTodayDateString()` 一致的本地时间手动格式化。

- [ ] **Step 2: 验证构建**

Run: `cd frontend-web && pnpm build`
Expected: 构建成功

- [ ] **Step 3: Commit**

```bash
git add frontend-web/src/components/thread/history/index.tsx
git commit -m "fix: formatDateLabel 用本地时间计算昨天 — 修复 UTC 偏移导致标签错误"
```

---

### Task 5: Pipeline 触发机制（LangGraph Cron API）

LangGraph Cron API 只能调度 graph run，不能调度任意 Python 函数。所以需要：
1. 创建一个轻量 LangGraph graph 包装 `run_day_end_pipeline`
2. 注册到 `langgraph.json`
3. 提供 cron 注册脚本

**Files:**
- Create: `backend/src/voliti/pipeline/graph.py`
- Modify: `backend/langgraph.json`
- Create: `backend/scripts/register_cron.py`
- Modify: `backend/src/voliti/pipeline/__init__.py`

- [ ] **Step 1: 创建 Pipeline Graph**

```python
# backend/src/voliti/pipeline/graph.py
# ABOUTME: 日终 Pipeline 的 LangGraph Graph 包装
# ABOUTME: 将 run_day_end_pipeline 包装为可被 Cron API 调度的 graph

from __future__ import annotations

import logging
from typing import Any, TypedDict

from langgraph.graph import StateGraph

from voliti.pipeline.day_end import run_day_end_pipeline
from voliti.store_contract import STORE_NAMESPACE_PREFIX

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """Pipeline graph 的 state schema。"""

    user_id: str
    results: dict[str, Any]


async def pipeline_node(state: PipelineState) -> dict[str, Any]:
    """执行日终 Pipeline 的 graph node。"""
    from langgraph_sdk import get_client

    user_id = state["user_id"]
    namespace = (STORE_NAMESPACE_PREFIX, user_id)

    client = get_client()
    result = await run_day_end_pipeline(
        client=client,
        user_id=user_id,
        namespace=namespace,
    )

    return {"results": result}


def build_pipeline_graph() -> Any:
    """构建日终 Pipeline graph。"""
    builder = StateGraph(PipelineState)
    builder.add_node("run_pipeline", pipeline_node)
    builder.set_entry_point("run_pipeline")
    builder.set_finish_point("run_pipeline")
    return builder.compile()


graph = build_pipeline_graph()
```

- [ ] **Step 2: 更新 pipeline/__init__.py**

```python
# ABOUTME: 日终 Pipeline 模块
# ABOUTME: 包含 Pipeline 执行逻辑和 LangGraph Graph 包装
```

- [ ] **Step 3: 注册到 langgraph.json**

```json
{
  "dependencies": ["."],
  "graphs": {
    "coach": "./src/voliti/graph.py:graph",
    "coach_qwen": "./src/voliti/graph.py:graph_qwen",
    "day_end_pipeline": "./src/voliti/pipeline/graph.py:graph"
  },
  "env": ".env"
}
```

- [ ] **Step 4: 创建 Cron 注册脚本**

```python
# backend/scripts/register_cron.py
# ABOUTME: 为每个活跃用户注册日终 Pipeline Cron
# ABOUTME: 使用 LangGraph SDK Cron API，每日 UTC 17:00（北京凌晨 01:00）触发

"""
用法：
  cd backend && uv run python scripts/register_cron.py --user-id <user_id>
  cd backend && uv run python scripts/register_cron.py --list
  cd backend && uv run python scripts/register_cron.py --delete <cron_id>
"""

from __future__ import annotations

import argparse
import asyncio
import os

from langgraph_sdk import get_client


API_URL = os.environ.get("LANGGRAPH_API_URL", "http://127.0.0.1:2025")
PIPELINE_ASSISTANT_ID = "day_end_pipeline"
DEFAULT_SCHEDULE = "0 17 * * *"  # UTC 17:00 = 北京 01:00


async def register(user_id: str, schedule: str = DEFAULT_SCHEDULE) -> None:
    client = get_client(url=API_URL)
    cron = await client.crons.create(
        assistant_id=PIPELINE_ASSISTANT_ID,
        schedule=schedule,
        input={"user_id": user_id},
        on_run_completed="delete",
        metadata={"user_id": user_id, "type": "day_end_pipeline"},
    )
    print(f"Cron registered: {cron['cron_id']} for user {user_id} @ {schedule}")


async def list_crons() -> None:
    client = get_client(url=API_URL)
    crons = await client.crons.search(assistant_id=PIPELINE_ASSISTANT_ID, limit=100)
    if not crons:
        print("No crons registered.")
        return
    for c in crons:
        meta = c.get("metadata", {})
        print(f"  {c['cron_id']}  user={meta.get('user_id', '?')}  schedule={c.get('schedule', '?')}")


async def delete(cron_id: str) -> None:
    client = get_client(url=API_URL)
    await client.crons.delete(cron_id)
    print(f"Cron deleted: {cron_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="管理日终 Pipeline Cron")
    parser.add_argument("--user-id", help="注册 cron 的用户 ID")
    parser.add_argument("--schedule", default=DEFAULT_SCHEDULE, help="Cron 表达式（默认 UTC 17:00）")
    parser.add_argument("--list", action="store_true", help="列出所有已注册的 cron")
    parser.add_argument("--delete", metavar="CRON_ID", help="删除指定 cron")
    args = parser.parse_args()

    if args.list:
        asyncio.run(list_crons())
    elif args.delete:
        asyncio.run(delete(args.delete))
    elif args.user_id:
        asyncio.run(register(args.user_id, args.schedule))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/voliti/pipeline/graph.py backend/src/voliti/pipeline/__init__.py backend/langgraph.json backend/scripts/register_cron.py
git commit -m "feat: Pipeline 触发机制 — LangGraph Cron API graph 包装 + 注册脚本"
```

---

### Task 6: session_type / segment_status 唯一事实

前端 `"coaching" | "onboarding"` 和 `"active"` / `"sealed"` 字面量散布在多个文件。集中到 `thread-utils.ts`（已有的 thread 工具文件），不新建文件。后端已有 `session_type.py` 作为唯一事实。

**Files:**
- Modify: `frontend-web/src/lib/thread-utils.ts`
- Modify: `frontend-web/src/providers/Stream.tsx`
- Modify: `frontend-web/src/components/thread/history/index.tsx`

- [ ] **Step 1: 在 thread-utils.ts 添加常量定义**

```typescript
// ABOUTME: Thread 状态判断工具函数与共享常量
// ABOUTME: session_type / segment_status 的前端唯一事实来源

import { Thread } from "@langchain/langgraph-sdk";

// --- Session Type（与 backend session_type.py 对齐） ---
export type SessionType = "coaching" | "onboarding";
export const SESSION_TYPE_COACHING: SessionType = "coaching";
export const SESSION_TYPE_ONBOARDING: SessionType = "onboarding";

// --- Segment Status ---
export type SegmentStatus = "active" | "sealed";
export const SEGMENT_STATUS_ACTIVE: SegmentStatus = "active";
export const SEGMENT_STATUS_SEALED: SegmentStatus = "sealed";

// --- Thread 状态判断 ---
export function isThreadSealed(thread: Thread): boolean {
  const meta = thread.metadata as Record<string, unknown> | undefined;
  return meta?.segment_status === SEGMENT_STATUS_SEALED;
}
```

- [ ] **Step 2: 更新 Stream.tsx — 使用导入的常量**

在 `Stream.tsx` 顶部：

```typescript
import {
  SessionType,
  SESSION_TYPE_COACHING,
  SEGMENT_STATUS_ACTIVE,
} from "@/lib/thread-utils";
```

修改 `ensureTodayThread` 签名：

```typescript
async function ensureTodayThread(
  apiUrl: string,
  userId: string,
  assistantId: string,
  sessionType: SessionType = SESSION_TYPE_COACHING,
): Promise<string | null> {
```

修改 thread creation metadata：

```typescript
segment_status: SEGMENT_STATUS_ACTIVE,
```

- [ ] **Step 3: 验证构建**

Run: `cd frontend-web && pnpm build`
Expected: 构建成功

- [ ] **Step 4: Commit**

```bash
git add frontend-web/src/lib/thread-utils.ts frontend-web/src/providers/Stream.tsx
git commit -m "refactor: session_type/segment_status 常量集中到 thread-utils.ts — 唯一事实原则"
```

---

### Task 7: 过时引用清理

重组后仍有若干文件引用已删除的组件。

**Files:**
- Modify: `docs/05_Runtime_Contracts.md`
- Modify: `backend/src/voliti/semantic_memory.py`
- Delete: `docs/memory-system-map.html`（整文件引用旧架构）
- Delete: `docs/tool-system-overview.html`（整文件引用旧架构）

- [ ] **Step 1: 更新 Runtime Contracts — 删除 journey_analysis 引用**

在 `05_Runtime_Contracts.md` 中搜索 `journey_analysis` 并更新为当前架构描述。

- [ ] **Step 2: semantic_memory.py 添加 day_summary 分类**

```python
_ARCHIVE_SOURCE_PREFIXES = ("/archive/", "/day_summary/")
```

- [ ] **Step 3: 删除过时的 HTML 参考文档**

```bash
git rm docs/memory-system-map.html docs/tool-system-overview.html
```

- [ ] **Step 4: Commit**

```bash
git add docs/05_Runtime_Contracts.md backend/src/voliti/semantic_memory.py
git commit -m "chore: 清理过时引用 — journey_analysis/旧 HTML 文档/day_summary 分类"
```

---

## DeepAgent 官方机制说明

**SummarizationMiddleware 默认 prompt**：DeepAgent 用一个 ~800 字的 `DEFAULT_SUMMARY_PROMPT` 做对话历史压缩，包含 SESSION INTENT / SUMMARY / ARTIFACTS / NEXT STEPS 四个段落。这是用于 **Agent 工作记忆压缩**（保持 Agent 能继续工作），不是用户可读日摘要。我们的 `_SUMMARY_SYSTEM_PROMPT`（`day_end.py:20-30`）是用于 **用户日摘要**（3-5 要点 + 情绪基调），两者用途不同，不应混用。当前实现正确。

**LangGraph Cron API**：只能调度 graph run（`client.crons.create(assistant_id=...)`），不能调度任意 Python 函数。Task 5 的 Pipeline Graph 包装是官方推荐模式。`on_run_completed="delete"` 自动清理每次 cron 创建的临时 thread。

**MemoryMiddleware 缺失文件处理**：`file_not_found` 错误码被 `continue` 静默跳过。新的 `lifesigns.md` 路径在文件不存在时不会报错。
