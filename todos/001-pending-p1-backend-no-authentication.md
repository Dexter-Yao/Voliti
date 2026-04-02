---
status: done
priority: p1
issue_id: "001"
tags: [code-review, security]
dependencies: []
---

# 后端 API 无认证机制

## Problem Statement

LangGraph 后端所有 API 端点完全无认证。任何发现后端 URL 的人可以：创建 thread、发送消息（消耗 LLM token）、恢复 interrupt、触发 Gemini 图片生成。iOS 客户端的所有请求（createThread、buildStreamRequest、buildResumeRequest）均不携带任何认证头。

## Findings

- `frontend-ios/Voliti/Core/Network/LangGraphAPI.swift` — 所有 HTTP 请求无 auth header
- `frontend-ios/Voliti/Core/Network/APIConfiguration.swift` — 无 API key 配置
- 后端无任何中间件或认证检查

## Proposed Solutions

### Option A: LangGraph Cloud x-api-key（推荐）
LangGraph Cloud 原生支持 `x-api-key` header。在 iOS 端 APIConfiguration 添加 API key，所有请求携带 `x-api-key` header。
- Pros: 最小改动，平台原生支持
- Cons: 单一 key，无 per-user 隔离
- Effort: Small
- Risk: Low

### Option B: JWT Token 认证
实现用户注册/登录，签发 JWT，后端校验。
- Pros: per-user 隔离，可扩展
- Cons: 工程量大，MLP 阶段可能过度
- Effort: Large
- Risk: Medium

## Recommended Action

已实施 Option A。

## Technical Details

- Affected files: `LangGraphAPI.swift`, `APIConfiguration.swift`
- iOS Keychain 存储 API key（勿用 UserDefaults）

## Acceptance Criteria

- [ ] 所有后端 API 请求携带认证信息
- [ ] 无认证请求返回 401
- [ ] API key 安全存储（iOS Keychain）

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-03-20 | 全库审查发现 | Security Sentinel Agent |
| 2026-04-01 | Option A 实施：APIConfiguration 添加 apiKey 属性，LangGraphAPI 所有请求附加 x-api-key header | 本地 dev server 无需 key，Cloud 部署时通过环境变量或 Info.plist 配置 |

## Resources

- LangGraph Cloud 认证文档
