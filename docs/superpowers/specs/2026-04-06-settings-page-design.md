# Settings 页设计规格

## 概述

为 Voliti iOS App 增加设置页面，包含：用户信息展示、持续 Onboarding 采集入口、偏好设置、重置功能、账户占位。设置页遵循 Starpath Protocol v2 设计系统，保持克制。

## 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 入口位置 | Toolbar leading 齿轮图标 | 始终可触达，toolbar 背景透明融入 parchment |
| Onboarding 会话 | 独立 thread，不与日常 coaching 共享 | 用户心智模型清晰，数据通过 Store 跨 thread 同步 |
| Coach 模式感知 | `configurable.session_mode` 传入后端 | LangGraph 原生机制，无临时补丁 |
| 缺失项标记 | 不做 | 信息采集开放式，无完整列表 |
| 登录/注册 | 预留占位，不实现 | 当前阶段不需要账户系统 |
| 删除账户 | 预留占位，不实现 | 依赖账户系统 |

## 信息架构

```
Settings (Form + NavigationStack)
├── Section: 我的信息
│   ├── Coach 已掌握的 profile 信息（只读 key-value 列表）
│   └── "继续了解我" CTA → 打开 Onboarding 采集会话
├── Section: 显示与交互
│   ├── 思考过程默认展开 (Toggle)
│   ├── 语言 (Picker: 跟随系统 / 中文 / English)
│   ├── 签到提醒 (Toggle)
│   └── 签到提醒时间 (DatePicker, 仅时间)
├── Section: 账户
│   └── 登录 / 注册（整行变淡 obsidian-20，右侧"即将推出"，不可点击）
├── Section: 数据与隐私
│   ├── 重置所有数据 (destructive)
│   └── 删除账户（整行变淡 obsidian-20，右侧"即将推出"，不可点击）
└── Section: 关于
    ├── 版本号
    └── 隐私政策 / 使用条款（外链）
```

## 组件设计

### 1. 入口：Settings 按钮

- **位置：** MirrorView 和 CoachView 的 `ToolbarItem(placement: .topBarLeading)`
- **图标：** SF Symbol `gearshape`，obsidian-40，14pt
- **Toolbar 样式：** `.navigationBarTitleDisplayMode(.inline)` + 空标题 + `.toolbarBackground(.hidden, for: .navigationBar)`
- **交互：** 点击 push 到 SettingsView

### 2. SettingsView

- **容器：** `Form` + `Section` 分组
- **背景：** parchment
- **Section header：** Mono 10px，obsidian-40，uppercase，letter-spacing 2px
- **行内标签：** Sans 14px
- **行内只读值：** Serif 16px
- **破坏性按钮：** Sans 14px，risk-red
- **圆角：** 0（Section 容器零圆角）
- **分隔线：** obsidian-10

### 3. "我的信息"区域

**数据来源：** `StoreSyncService` 从 LangGraph Store `/voliti/user/profile/context` 读取。

**展示格式：**
- key-value 列表，Mono 标签 + Serif 值
- 信息为空时该行不显示（不标记缺失，不暗示完整性）
- 无编辑功能（Coach 是唯一数据入口）
- Profile 字段由 Coach 动态写入，无固定 schema。前端从 Store 读取 context 内容后，按字段出现顺序展示。常见字段如 `name`（称呼）、`goal`（目标）等的中文标签映射在 ProfileInfoSection 中维护一个 static dict，未知字段直接显示原始 key。

**CTA 按钮：**
- "继续了解我"
- Sans 14px，obsidian-10 边框，Capsule 圆角（有意对比：Form 行零圆角，CTA 按钮以 Capsule 形式作为功能性引导点，延续 DESIGN.md 中 Pill 按钮的设计语言）
- 点击 → fullScreenCover 打开 Onboarding 采集会话

### 4. 重置功能

**操作范围（按执行顺序）：**
1. 将 `onboardingComplete` 设为 false（最先执行，确保中断安全）
2. 调用后端 Store 清除 API（清除 `/voliti/user/` 下所有数据）
3. 清除所有 SwiftData 数据（BehaviorEvent、DashboardConfig、Chapter、LifeSignPlan、InterventionCard、ChatMessage）
4. 重置 `voliti_thread_id` 和 `voliti_onboarding_thread_id`（新 thread 将在下次 Onboarding 自动创建）
5. 清除其他 @AppStorage 值

**执行顺序设计理由：** 先设 `onboardingComplete = false`，即使后续步骤被中断（App 被杀），最坏情况是 App 重启后进入 Onboarding，旧数据会在下次 sync 时被新数据覆盖。

**后端 Store 清除 API（新增）：**
- **依赖验证：** 本接口依赖 LangGraph Cloud 批量删除能力，实施前须通过官方文档确认可用性；如不存在批量删除，需改为逐键删除方案（遍历已知 namespace 逐个删除）。
- Endpoint: `DELETE /store/items?prefix=/voliti/user/`（或等效的 LangGraph Store 批量删除机制）
- 清除范���：`/voliti/user/profile/`、`/voliti/user/chapter/`、`/voliti/user/ledger/`、`/voliti/user/coping_plans/`
- 需要在 `LangGraphAPI` 中新增 `clearUserStore()` 方法
- 如果 Store 清除 API 调用失败（网络错误），显示警告但继续本地清除，不阻塞重置流程

**交互流程：**
1. 点击"重置所有数据"
2. `confirmationDialog` 弹出
   - 标题："此操作将永久删除所有对话历史、行为记录和教练配置，无法恢复。"
   - 破坏性按钮："确认重置"（`role: .destructive`）
   - Cancel 由系统自动添加
3. 显示 loading indicator（ProgressView overlay）
4. 执行重置（按上述顺序）
5. dismiss SettingsView，延迟 0.3 秒后触发 Onboarding fullScreenCover

## Onboarding 采集会话

### Thread 架构

```
┌─────────────────────────────────────────────────┐
│               LangGraph Store                    │
│  /voliti/user/profile/context                    │
│  /voliti/user/profile/dashboardConfig            │
│  /voliti/user/chapter/current                    │
│  /voliti/user/ledger/*                           │
├──────────────────────┬──────────────────────────┤
│   Coaching Thread    │   Onboarding Thread      │
│   (voliti_thread_id) │ (voliti_onboarding_      │
│                      │          thread_id)       │
│   日常 coaching 对话  │   Profile 采集对话        │
│   session_mode:      │   session_mode:           │
│     "coaching"       │     "onboarding"          │
└──────────────────────┴──────────────────────────┘
         ▲ 读取 Store              ▲ 写入 Store
         │                         │
         └───── 共享同一份用户数据 ──┘
```

两个 thread 共享同一个 LangGraph Store。Onboarding thread 采集的信息写入 Store，Coaching thread 下次对话自动读取。

### Thread 管理

**APIConfiguration 扩展：**
```swift
// 现有
static var threadID: String?  // key: "voliti_thread_id"

// 新增
static var onboardingThreadID: String?  // key: "voliti_onboarding_thread_id"
```

**LangGraphAPI 扩展：**
```swift
// createThread 支持 metadata
func createThread(metadata: [String: String] = [:]) async throws -> String

// ensureOnboardingThread 管理独立 thread
func ensureOnboardingThread() async throws -> String

// streamRun 支持 session_mode
func streamRun(threadID: String, message: String, imageData: Data? = nil,
               sessionMode: String = "coaching") throws -> AsyncStream<SSEEvent>
```

`streamRun` 在 request body 中传递 `config.configurable.session_mode`：
```json
{
  "assistant_id": "coach",
  "input": { "messages": [...] },
  "config": {
    "configurable": {
      "session_mode": "onboarding"
    }
  },
  "stream_mode": ["messages", "values"],
  "stream_subgraphs": true
}
```

### Coach Prompt 适配

**后端 `agent.py`：** 从 `configurable.session_mode` 读取模式，传递给 prompt 模板。

**`coach_system.j2` 新增条件段落：**

```jinja2
{% if session_mode == "onboarding" %}
<!-- ═══════════════════════════════════════════════════════════════════ -->
<!-- SESSION MODE: Onboarding / Profile Collection                      -->
<!-- ═══════════════════════════════════════════════════════════════════ -->

This is a profile collection session, not a regular coaching session. Your focus:
- Actively and naturally collect personal information to build the user's profile
- Ask about goals, lifestyle patterns, constraints, preferences, and context
- Write collected information to the user's profile via Store operations
- If the user initiates regular coaching conversation (reporting meals, asking for advice, discussing struggles), gently redirect: suggest they return to the main coaching session for that topic
{% endif %}
```

当 `session_mode` 未设置或为 `"coaching"` 时，此段落不渲染，Coach 行为不受影响。

### 视觉区分

Onboarding 采集界面与正常 Coach 对话的视觉差异：

| 属性 | 正常 Coach | Onboarding 采集 |
|------|-----------|----------------|
| 呈现方式 | Tab 内 | fullScreenCover |
| 底色 | parchment (#F4F0E8) | 微暖偏移 (#F4EDE3) |
| 顶部指示 | 无 | copper 渐变呼吸线 |
| Tab 栏 | 可见 | 不可见 |
| 退出方式 | 切换 Tab | 右上角关闭按钮 |

**Copper 渐变呼吸线：**
- 位置：屏幕顶部
- 尺寸：1px 高，约 60% 屏幕宽，居中
- 颜色：copper → transparent 渐变
- 动画：低频缓慢呼吸，目标视觉强度约 10-30% opacity，具体参数实施阶段根据实际效果确认
- 语义：Coach 存在感的"签名"，表示 Coach 正在主动感知

**退出机制：**
- 右上角关闭按钮：SF Symbol `xmark`，obsidian-40
- Coach 判断采集完毕后可通过对话自然结束

### 进入方式

**首次启动（现有流程改造）：**
1. `onboardingComplete == false` → fullScreenCover 打开 OnboardingView
2. OnboardingView 使用 `onboardingThreadID`（而非 `threadID`）
3. 视觉走 Onboarding 采集样式（微暖底色 + copper 呼吸线）
4. 完成后设置 `onboardingComplete = true`，Tab 栏滑入

**设置页"继续了解我"：**
1. 点击 → fullScreenCover 打开 OnboardingView（`isReEntry: true`）
2. 复用同一个 `onboardingThreadID`（Coach 能看到之前的采集历史）
3. `isReEntry = true` 时跳过 Step 1-2（称呼 + Future Self），直接进入对话模式
4. Coach 通过 Store 感知已有 profile，针对性补充采集

**`isReEntry` 判定：** OnboardingView 接受 `isReEntry: Bool` 参数。完整 Step 序列为 Step 1（称呼）→ Step 2（Future Self）→ Step 3+（自由对话）。首次启动 `isReEntry = false` 从 Step 1 开始；设置页"继续了解我"时 `isReEntry = true` 直接进入 Step 3+ 对话模式，跳过 Step 1-2。判定来源是调用方传入，不依赖 Store 或 thread 状态推断。

## 偏好设置

| 偏好 | 控件 | 默认值 | @AppStorage Key | 类型 |
|------|------|--------|----------------|------|
| 思考过程默认展开 | Toggle | false | `showThinkingExpanded` | Bool |
| 语言 | Picker | "system" | `preferredLanguage` | String |
| 签到提醒 | Toggle | true | `checkinReminderEnabled` | Bool |
| 签到提醒时间 | DatePicker (时间) | 08:00 | `checkinReminderTime` | Double (TimeInterval) |

**签到提醒时间存��：** 使用 `Double`（`TimeInterval`，从午夜起的秒数）而非字符串，避免时区/DST 解析歧义。默认值为 28800.0（08:00）。

**签到提醒权限流程：** 当 `checkinReminderEnabled` 被设为 `true` 时：
1. 请求 UNUserNotificationCenter 授权
2. 授权通过 → 注册本地通知
3. 授权被拒 → Toggle 自动恢复 `false`，显示内联说明："需��开启通知权限"+ 按钮跳转系统设置
4. 偏好变更后立即重建/取消已注册的本地通知

**语言 Picker 选项：**
- 跟随系统（"system"）
- 中文（"zh"）
- English（"en"）

语言偏好通过 `config.configurable.preferred_language` 传递给后端（与 `session_mode` 并列）：
```json
{
  "config": {
    "configurable": {
      "session_mode": "coaching",
      "preferred_language": "zh"
    }
  }
}
```
当前仅影响 Coach 对话语言，不影响 UI 静态文案（Localization 基础设施不在范围内）。

## 文件结构

```
frontend-ios/Voliti/
├── Features/
│   └── Settings/                          (NEW)
│       ├── SettingsView.swift             — 设置主页 Form
│       ├── ProfileInfoSection.swift       — "我的信息" 只读展示
│       └── ResetService.swift             — 重置逻辑（清除 SwiftData + AppStorage + Store）
├── Core/
│   └── Network/
│       ├── APIConfiguration.swift         — 新增 onboardingThreadID
│       └── LangGraphAPI.swift             — createThread(metadata:), streamRun(sessionMode:), clearUserStore()
├── Features/
│   ├── Onboarding/
│   │   └── OnboardingView.swift           — 改用 onboardingThreadID + 视觉区分
│   ├── Coach/
│   │   └── CoachView.swift                — toolbar 新增设置按钮
│   └── Mirror/
│       └── MirrorView.swift               — toolbar 新增设置按钮

backend/
├── prompts/
│   └── coach_system.j2                    — 新增 onboarding mode 条件段落
└── src/voliti/
    └── agent.py                           — 读取 session_mode，传递给 prompt
```

## 不在范围内

- 登录/注册实现（仅 UI 占位）
- 删除账户实现（依赖账户系统）
- 通知推送后端（签到提醒仅本地 UNUserNotificationCenter）
- 语言切换的 Localization 基础设施（当前仅传递偏好给 Coach）
- Onboarding 采集视觉的动画微调（实施阶段根据实际效果调整）

## DESIGN.md 更新

需要更新的 DESIGN.md 内容：
1. 组件清单新增 SettingsView、ProfileInfoSection
2. Onboarding 段落：更新为独立 thread 架构，删除"共享 thread_id"描述
3. 新增 Settings 页视觉规格段落
4. 新增 Onboarding 采集模式视觉段落（微暖底色 + copper 呼吸线）

## 实施注意事项（CEO + Codex Review 发现）

1. **重置执行顺序：** 先 `onboardingComplete = false` → Store 清除 API → SwiftData 删除 → thread ID 重置 → 其他 AppStorage。中断安全。
2. **重置后 UI 过渡：** dismiss SettingsView → 延迟 0.3 秒 → ContentView 检测 onboardingComplete=false → fullScreenCover 触发。
3. **后端验证项（实施前确认）：**
   - LangGraph `POST /threads` 是否接受 `metadata` 字段
   - `config.configurable.session_mode` 如何传递到 Jinja2 模板渲染上下文
   - LangGraph Store 是否有批量删除 API（`DELETE /store/items` 或等效机制）
4. **签到提醒闭环：** 偏好变更后需要立即重建/取消本地 UNNotification。检查通知授权状态，未授权时引导用户到系统设置。时间存储使用 DateComponents 而非字符串，避免时区/DST 问题。
5. **SwiftUI Form 零圆角：** 需要自定义 `listRowBackground` 和 Section styling 来覆盖 iOS 默认圆角。实施前先做 prototype 确认可行性。
6. **Profile 加载状态：** SettingsView `onAppear` 读取 Store，加载期间显示 ProgressView 或 placeholder。非响应式，不做实时更新。
