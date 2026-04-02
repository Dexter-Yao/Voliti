---
status: pending
priority: p3
issue_id: "015"
tags: [code-review, security, deployment]
dependencies: ["001"]
---

# Dockerfile dev 命令 + HTTP 明文 + ThreadID 存 UserDefaults

## Problem Statement

三个部署相关安全加固项：
1. Dockerfile CMD 使用 `langgraph dev`（开发服务器），应为生产命令
2. Info.plist 允许本地 HTTP 明文，生产 baseURL 使用 `http://localhost:2024`
3. Thread ID 存 UserDefaults（未加密），是访问对话历史的唯一凭证

## Findings

- `backend/Dockerfile:32` — `CMD ["uv", "run", "langgraph", "dev", ...]`
- `frontend-ios/Voliti/Info.plist:33-37` — `NSAllowsLocalNetworking: true`
- `frontend-ios/Voliti/Core/Network/APIConfiguration.swift:15` — `http://localhost:2024`
- `APIConfiguration.swift:21-24` — `UserDefaults.standard` 存 threadID

## Proposed Solutions

### Option A: 逐项加固
1. Dockerfile 改为 `langgraph up` 或 LangGraph Cloud 部署
2. Release 配置移除 NSAllowsLocalNetworking，baseURL 改 https
3. Thread ID 迁移至 iOS Keychain
- Effort: Medium
- Risk: Low

## Acceptance Criteria

- [ ] 生产 Dockerfile 不用 dev 命令
- [ ] Release build 强制 HTTPS
- [ ] Thread ID 安全存储

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Security Sentinel Agent |
