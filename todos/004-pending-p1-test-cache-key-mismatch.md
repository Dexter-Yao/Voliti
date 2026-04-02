---
status: done
priority: p1
issue_id: "004"
tags: [code-review, bug, backend, testing]
dependencies: []
---

# test_experiential.py 缓存 key 使用 hash() 与生产代码 hashlib.sha256 不匹配

## Problem Statement

测试 fixture `_prefill_cache` 使用 `hash(TEST_PROMPT)` 计算缓存 key（返回 int），但生产代码 `experiential.py:90` 使用 `hashlib.sha256(prompt.encode()).hexdigest()`（返回 hex 字符串）。二者永远不匹配。测试仅因 mock 了 `interrupt` 而通过，fixture 的预填充意图完全失效。

## Findings

- `backend/tests/test_experiential.py:21` — `cache_key = hash(TEST_PROMPT)`
- `backend/src/voliti/tools/experiential.py:90` — `cache_key = hashlib.sha256(prompt.encode()).hexdigest()`
- 类型不匹配：int vs str

## Proposed Solutions

### Option A: 修复 fixture（推荐）
```python
import hashlib
cache_key = hashlib.sha256(TEST_PROMPT.encode()).hexdigest()
```
- Effort: 1 行
- Risk: None

## Acceptance Criteria

- [ ] fixture 使用与生产代码相同的 hash 逻辑
- [ ] 测试通过且 cache hit 生效

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Kieran Python Reviewer |
