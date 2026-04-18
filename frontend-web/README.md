<!-- ABOUTME: Voliti Web 试用端运行说明 -->
<!-- ABOUTME: 供邀请制试用阶段使用，说明环境变量、启动方式、发布门槛与常见故障 -->

# Voliti Web

Voliti Web 是当前邀请制试用阶段的唯一正式客户端。目标不是公开 beta，而是支撑 5-20 位受邀用户的稳定试用。

## 试用定位

- 面向受邀用户，不面向公开注册。
- 以桌面浏览器为主。
- 第一轮不做外部主动通知；核心是让用户打开应用时即可进入当前最相关的教练上下文。

## 必要环境变量

将 [`.env.example`](/Users/dexter/DexterOS/products/Voliti/frontend-web/.env.example) 复制为 `.env.local`，至少补齐以下变量：

- `NEXT_PUBLIC_API_URL`：前端访问 LangGraph 的代理地址。默认 `/api`。
- `NEXT_PUBLIC_ASSISTANT_ID`：当前 assistant ID。默认 `coach`。
- `LANGGRAPH_API_URL`：服务端直连 LangGraph 的地址。
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

邀请制试用相关变量：

- `NEXT_PUBLIC_ALLOW_SELF_SIGNUP=false`
- `VOLITI_ALLOW_SELF_SIGNUP=false`
- `NEXT_PUBLIC_TRIAL_CONTACT`
- `VOLITI_TRIAL_CONTACT`

说明：

- 默认关闭自助注册，登录页会展示邀请制提示。
- `VOLITI_*` 用于服务端动作判断；`NEXT_PUBLIC_*` 用于前端文案呈现。

## 本地启动

1. 启动 backend：

```bash
cd backend
uv run langgraph dev --port 2025
```

2. 启动 Web：

```bash
cd frontend-web
pnpm install
pnpm dev
```

3. 打开 `http://localhost:3000/login`

## 工程验证

Web 自身基线：

```bash
cd frontend-web
pnpm test
pnpm build
```

完整发布前门槛：

```bash
./scripts/pilot_release_gate.sh
```

该脚本会按固定顺序执行：

1. `backend` 测试
2. `eval` 测试
3. `frontend-web` 测试
4. `frontend-web` 构建
5. `eval --profile full`
6. `eval --compare --models coach,coach_qwen --runs 3 --profile full`

脚本完成后，仍需人工阅读 `eval/output` 中最新报告。

## 邀请制试用约束

- 账号由人工发放。
- 当前不承诺公开注册流程、邮件提醒、浏览器通知与自助支持。
- 当前支持的故障反馈方式应由 `NEXT_PUBLIC_TRIAL_CONTACT` 明示。

## 常见故障

### 登录后仍无法进入应用

优先检查：

- Supabase URL / Anon Key 是否正确。
- middleware 是否成功刷新 session。
- 浏览器是否阻止了站点 cookie。

### 页面提示无法连接教练服务

优先检查：

- `LANGGRAPH_API_URL` 是否可达。
- backend 是否已在 `:2025` 启动。
- `/api` 代理是否返回 401 或 500。

### Mirror 显示无法读取

该面板现在通过服务端路由按已登录用户身份读取 Store。优先检查：

- 当前账号是否已完成 onboarding。
- LangGraph Store 中是否存在 `profile / goal / chapter / dashboardConfig`。
- `/api/me/coach-context` 是否返回错误。

### 语音转写失败

优先检查：

- `DASHSCOPE_API_KEY` 是否已配置到服务端环境。
- 录音文件是否超出大小限制。
- 当前用户是否处于已登录状态。

## 当前发布标准

邀请制试用前，以下条件必须同时满足：

- `backend` 全绿
- `eval` 全绿
- `frontend-web` 全绿
- `eval full` 通过
- `compare` 通过

如果 `compare` 显示主模型在 must-pass 维度上不稳定，即使前端可用，也不进入试用。
