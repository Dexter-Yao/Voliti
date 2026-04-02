---
status: pending
priority: p2
issue_id: "005"
tags: [code-review, security, backend]
dependencies: []
---

# Jinja2 PromptRegistry 未使用 SandboxedEnvironment

## Problem Statement

`PromptRegistry` 使用标准 `Environment` 而非 `SandboxedEnvironment`。当前模板均为开发者编写的磁盘文件，风险低。但如果未来 `PromptRegistry.get()` 的 kwargs 中混入用户输入，可导致 SSTI（服务端模板注入）执行任意 Python 代码。`StrictUndefined` 仅防止未定义变量，不提供沙箱。

## Findings

- `backend/src/voliti/config/prompts.py:21-25` — `Environment(loader=FileSystemLoader(...))`

## Proposed Solutions

### Option A: 替换为 SandboxedEnvironment（推荐）
```python
from jinja2.sandbox import SandboxedEnvironment
cls._env = SandboxedEnvironment(...)
```
- Effort: 1 行改动
- Risk: None（对合法模板无影响）

## Acceptance Criteria

- [ ] 使用 SandboxedEnvironment
- [ ] 所有现有模板正常渲染
- [ ] 测试通过

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Security Sentinel Agent |
