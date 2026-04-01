---
status: done
priority: p1
issue_id: "003"
tags: [code-review, performance, security, backend]
dependencies: []
---

# 后端 _intervention_cache 无上限可导致 OOM

## Problem Statement

`experiential.py` 模块级 `_intervention_cache: dict[str, tuple[str, str]]` 存储 base64 编码图片（每张 500KB-2MB），无大小限制、无 TTL 淘汰。如果 interrupt 未被 resume（用户关闭应用、网络中断），缓存条目永不清理。在多并发用户场景下可导致服务进程 OOM。

## Findings

- `backend/src/constellate/tools/experiential.py:25` — 无界 dict 缓存
- 仅在 happy path（用户响应后）通过 `pop()` 清理
- LangGraph Cloud 多 worker 部署时缓存不跨进程，resume 路由到不同 worker 导致 cache miss

## Proposed Solutions

### Option A: TTLCache（推荐）
使用 `cachetools.TTLCache(maxsize=32, ttl=1800)` 替代裸 dict。
- Pros: 自动淘汰，有大小上限
- Cons: 新增依赖 cachetools
- Effort: Small
- Risk: Low

### Option B: LRU + 手动清理
使用 `functools.lru_cache` 或 `OrderedDict` + maxsize。
- Pros: 无新依赖
- Cons: 无 TTL，需手动管理
- Effort: Small
- Risk: Low

## Acceptance Criteria

- [ ] 缓存有 maxsize 上限
- [ ] 超时条目自动淘汰
- [ ] 并发 50 用户不触发 OOM

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Performance Oracle + Security Sentinel |
