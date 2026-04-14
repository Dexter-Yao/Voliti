# Design System — Voliti (Starpath Protocol v2)

> 设计哲学与交互原则见 [`docs/02_Design_Philosophy.md`](docs/02_Design_Philosophy.md)。
> 产品定位与理论基础见 [`docs/01_Product_Foundation.md`](docs/01_Product_Foundation.md)。
> 机器可读 tokens 见 [`docs/design-system/design-tokens.json`](docs/design-system/design-tokens.json)。

## 产品上下文
- **产品定义：** AI 减脂领导力教练，训练用户在真实生活场景中的决策能力
- **目标用户：** 理性、上进的知识工作者/管理者。信息储备充足，但压力/疲劳/社交持续打断节奏
- **支持语言：** 中文、英文
- **产品类型：** iOS 原生 App（SwiftUI）+ Web 端 MVP（Next.js），三栏可折叠布局

## 美学方向

**方向：** Refined Industrial
**调性：** 沉稳的策略顾问，不是健身教练。有品味的工具，不是温柔的安慰。
**装饰级别：** Minimal — 排版和留白承担全部视觉任务
**情绪关键词：** 克制、精准、温度、力量

**核心原则（继承 v1）：**
- 高对比
- 大留白
- 线性分割
- 少容器化
- 零圆角容器（仅 pill 999px）
- 无奖励动画、无激励色彩

**差异化要素：**
- Copper 信号色在关键时刻出现，是 Coach 的视觉签名
- 楷体叙事层（LXGW WenKai）区别于通用宋体，增加书写温度
- Mono 信号层视觉权重提升，承担身份区分和数据标签任务

## 排版

### 三层字体语义

| 层 | 角色 | 字体 | 用途 |
|----|------|------|------|
| 叙事层 Serif | Coach 的声音 | LXGW WenKai | Coach 消息、身份宣言、日期标签、指标数值 |
| 界面层 Sans | 用户的声音 | DM Sans | 用户消息、按钮、输入框、事件摘要 |
| 信号层 Mono | 系统的声音 | JetBrains Mono | 时间戳、数据标签、Tab 栏、Section 标题、指标单位 |

### 字号层级

| Token | 值 | 用途 |
|-------|-----|------|
| xs | 12px | Mono 标签、时间戳、数据单位 |
| sm | 14px | Sans 正文、按钮文案、事件行文字 |
| base | 16px | Serif 正文、Coach 消息 |
| lg | 18px | Section 标题 |
| xl | 24px | 身份宣言、指标数值 |
| 2xl | 36px | 北极星指标数值 |

### 行高

| 类型 | 值 |
|------|-----|
| body (Serif) | 1.6 |
| heading | 1.3 |
| data (Mono) | 1.0 |

### 字间距

| 场景 | 值 |
|------|-----|
| Tab 栏、Section 标题（Mono uppercase） | 2px |
| 其他 | 0 |

## 色彩

### 核心色板

| Token | Hex | 用途 |
|-------|-----|------|
| obsidian | #1A1816 | 主文字、主按钮背景、强调元素 |
| parchment | #F4F0E8 | 页面背景、面板背景、主按钮文字 |
| copper | #B87333 | 信号色：LifeSign/预案标题、IF/THEN 标记、北极星标签、趋势图活跃柱、Coach 消息左边界（可选） |
| aligned | #8A9A8A | 对齐状态指示、正向趋势 delta |
| risk-red | #8B3A3A | 系统级风险标记，禁止用于行为评判 |

### 透明度变体

| Token | 值 | 用途 |
|-------|-----|------|
| obsidian-05 | 5% | 用户消息背景面板 |
| obsidian-10 | 10% | 细分割线、输入框边框、非活跃趋势柱 |
| obsidian-15 | 15% | 周分隔线 |
| obsidian-20 | 20% | 卡片边框、扇出面板顶线 |
| obsidian-40 | 40% | 次要标签、时间戳、占位符文字 |
| copper-40 | 40% | 趋势图活跃柱 |

### 禁止色

- 医疗蓝 (#0000FF 系)
- 激励橙 (#FF6B00 系)
- 亮绿 (#00FF00 系)
- 纯黑 (#000000)
- 纯白 (#FFFFFF)
- 紫色/靛蓝渐变

## 间距

| Token | 值 | 用途 |
|-------|-----|------|
| xs | 4px | 标签内部、图标微间距 |
| sm | 8px | 组件内部元素间距 |
| md | 16px | 主内容区域间距、卡片内边距 |
| lg | 24px | 卡片间距、区块间距 |
| xl | 32px | 页面级留白、模块间隔 |

间距基于 4px 网格，不允许非 4 整数倍的值。

## 布局

### Tab 栏（BottomTabBar）

- 2 个 Tab：COACH / MIRROR
- 字体：Mono 12px uppercase，letter-spacing 2px
- 活跃态：obsidian + 2px 底部线（24px 宽）
- 非活跃：obsidian-40
- 背景：parchment
- 顶部边框：1px solid obsidian-10
- 禁止：图标、emoji、活跃态背景填充、Tab 间分隔线

### 分隔线（StarpathDivider）

| 类型 | 规格 |
|------|------|
| 标准 | 1px · obsidian-10 |
| 周边界 | 2px · obsidian-15 |
| 区块分隔 | 1px · obsidian-10 · 水平 padding 16px |

### 圆角规则

| 元素 | 圆角 |
|------|------|
| 容器、卡片 | 0（零圆角） |
| Pill 按钮、Filter 标签 | 999px (Capsule) |
| 用户消息面板 | 12px |
| 输入框 | 4px |
| 图片缩略图 | 4px |

### Touch Target

所有可交互元素最小 44×44pt。视觉尺寸可以小于 44pt，但 contentShape 必须 ≥ 44pt。

## COACH Tab — 聊天界面

### 消息样式

| 角色 | 字体 | 对齐 | 背景 | 边距 |
|------|------|------|------|------|
| Coach | Serif 16px | 左 | 无 | 右侧留 48px |
| 用户 | Sans 14px | 右 | obsidian-05 · 12px 圆角 | 左侧留 64px · 背景宽度适配内容 |

**用户消息背景宽度适配内容长度，不使用固定宽度。**

### IF/THEN 标记

- 字体：Mono 13px
- 颜色：copper
- 用于 LifeSign 预案展示

### 时间戳规则

| 消息间隔 | 显示方式 | 格式 |
|---------|---------|------|
| < 5 min | 不显示，消息合组 | — |
| 5 ~ 30 min | 居中时间 | 09:12 |
| 30 min ~ 当天 | 居中，带上午/下午 | 下午 3:20 / 3:20 PM |
| 跨天 < 7 天 | 居中，相对日 + 时间 | 昨天 15:20 / Yesterday 15:20 |
| ≥ 7 天 | 居中，日期 + 时间 | 3月28日 09:00 / Mar 28 09:00 |

- 字体：Mono 11px · obsidian-40 · 居中
- 需要实现为独立的时间戳组件

## Onboarding — 全屏对话

### 设计意图

Onboarding 是 Coach 的独白时刻。视觉上把 Coach 升格为前景，把界面降格为背景。用户感受到的是"一位教练在关注我"，而不是"一个表单要我填"。

### 布局

- 全屏覆盖（fullScreenCover），无 Tab 栏，无导航栏
- 背景：onboardingWarm (#F4EDE3，比 parchment 微暖偏移)
- 顶部 copper 渐变呼吸线（1px，60% 屏宽居中，opacity 0.1-0.3 缓慢循环）
- 内容垂直居中偏上（top 30% 留白）
- 左右 padding：spacingXL (32px)

### 两个视觉阶段

| 阶段 | Coach 消息 | 用户回复 | InputBar |
|------|-----------|---------|----------|
| 居中模式（Step 1-2） | Serif 18px · 居中 | Quick Reply pills（垂直排列） | 隐藏 |
| 对话模式（Step 3+） | Serif 16px · 左对齐 | 自由输入 + 语音 | 显示 |

过渡动画：300ms ease-out（Starpath fanout token）

### Coach 标识

- "VOLITI COACH" — Mono 12px · copper · uppercase · letter-spacing 2px
- 位于屏幕垂直 30% 处，居中
- 仅在 Step 1 显示，后续消息流中不重复

### Quick Reply pills

- 垂直排列，居中对齐
- Sans 14px · obsidian-10 边框 · Capsule 圆角
- 间距 spacingSM (8px)
- 底部 padding spacingXL (32px)
- 最后一个选项触发 InputBar 出现（"让我想想" / "我想说说"）

### 语音输入

InputBar 和 Quick Reply 区域均支持语音按钮（麦克风图标，语音转文字后作为文本输入）。

### 三步对话内容

**Step 1：称呼**
```
ZH: "你好。
     我是你的教练，将陪你走接下来这段旅程。
     怎么称呼你？"

EN: "Hi there.
     I'm your coach, and I'll be walking this next stretch of the road with you.
     What should I call you?"
```
回复方式：文本输入框 + 语音
语言选择：跟随 @AppStorage("preferredLanguage")，默认跟随系统

**Step 2：Future Self（场景）**
```
"[名字]，闭上眼想一下 —
 你最享受的自己是什么样的？"
```
Quick Reply: "精力充沛，从容不迫" / "穿上喜欢的衣服，很自信" / "能掌控自己的节奏" / "让我想想"

**Step 3：State（当前距离）**
```
"那现在呢 —
 你觉得离那个状态有多远？"
```
Quick Reply: "差一点点" / "有距离，但方向清楚" / "挺远的，不知道从哪开始"

三步完成后，Coach 自主判断是否发送 fan_out 结构化表单深入采集，或直接完成 Onboarding。

### Onboarding 完成过渡

1. Coach 完成 profile / dashboardConfig / chapter 写入
2. 触发 `future_self` ceremony image（A2UI 全屏面板）
3. StoreSyncService.syncAll() 确认数据到位
4. Tab 栏从底部滑入（300ms ease-out）

### 独立会话

Onboarding 使用独立的 `onboardingThreadID`，与日常 coaching 的 `threadID` 分离。两个 thread 共享同一 LangGraph Store（profile、dashboardConfig 等自动同步）。对话历史不混合。

### 采集模式 re-entry

设置页"继续了解我"可重新进入 Onboarding 采集界面（`isReEntry: true`），跳过 Step 1-2，直接进入对话模式。Coach 通过 `configurable.session_mode = "onboarding"` 感知当前为采集模式。

## MIRROR Tab — 展示层

### 页面结构（从上到下）

```
┌─────────────────────────────────┐
│ Chapter Context                 │
│ 篇章 3 · Day 14                │
│ "在压力下保持清晰选择的人"        │  ← Serif 24px
│ 目标：12 周 75kg → 70kg          │  ← Sans 14px obsidian-40
├─────────────────────────────────┤
│ ★ 北极星 / NORTH STAR           │  ← Mono copper
│ 72.3 KG  ↓ 0.4 本周             │  ← Serif 36px + Mono delta
│ [■ ■ ■ ■ ■ ■ ■] 7日趋势         │  ← 可点击
│ 查看全部记录 ›                   │
├─────────────────────────────────┤
│ 支持性指标（3 列等宽）            │
│ 今日摄入 | 今日状态 | 本周一致性   │
│ 1,420    | 7/10    | 5/7        │
├─────────────────────────────────┤
│ LIFESIGN / 预案                  │  ← Mono copper
│ 3 预案 · 激活 5 成功 4  ›         │
├─────────────────────────────────┤
│ 日志 Filter（动态标签）           │
│ [全部 12] [饮食 5] [体重 3] ...  │  ← 有记录才显示
│ 事件流...                        │
└─────────────────────────────────┘
```

### 北极星指标

- 标签：Mono 10px · copper · uppercase · ★ 前缀
- 数值：Serif 36px
- 单位：Mono 12px · obsidian-40
- Delta：Mono 12px · aligned（正向）/ risk-red（负向）
- 7日趋势：直接在数值下方，柱状图，高度 40px
  - reported 柱：obsidian-10（非活跃）/ copper（今日/选中）
  - estimated 柱：同色但 opacity 0.4，视觉传达"推断值"
  - 今日柱：copper
  - hover/tap 状态：copper-40
  - 日期标签：Mono 9px · obsidian-40
  - "查看全部记录 ›"：Mono 10px · obsidian-40 · 右对齐

### 支持性指标

- 固定 3 个，由 Coach 在 Onboarding 确定
- 等宽三列，border-left 分隔（第一列无左边框）
- 标签：Mono 10px · obsidian-40 · uppercase
- 数值：Serif 20px
- 副标签：Mono 10px · obsidian-40

### LifeSign 摘要卡片

- 标题：Mono 12px · copper · uppercase · "LIFESIGN"（EN）/ "预案"（ZH）
- 统计：Sans 14px
- Chevron：12px · obsidian-40 · 右对齐
- 点击进入 LifeSign 列表

### 事件流 Filter

- 动态标签：只显示有记录的事件类型
- 每个标签显示计数（Mono 10px）
- 零记录的事件类型不渲染
- Pill 样式：Sans 13px · Capsule · obsidian-10 边框
- 活跃态：obsidian 背景 · parchment 文字

### 空状态设计

| 场景 | 北极星区域 | 支持指标 | 趋势图 |
|------|-----------|---------|--------|
| 完全空（新用户） | 破折号 "—" + "待设定" | 破折号 | 虚线框 + "与 Coach 对话后开始记录" |
| 部分数据（有对话无北极星记录） | 指标名已显示 + 破折号 + 单位 | 有数据的显示，无数据的破折号 | 虚线框 + "记录第一次[指标]后显示趋势" |
| 有数据但不足 7 天 | 正常显示 | 正常显示 | 已有天数的柱子 + 其余位置空白（不用占位柱） |

## 界面语言规范

| 概念 | 中文 | English | 备注 |
|------|------|---------|------|
| LifeSign | 预案 | LifeSign | 中文用直觉表达，英文保留品牌词 |
| Milestone | 时刻 | Moment | 值得记住的瞬间 |
| Event Stream | 日志 | Log | 用户可见名称 |
| State Check-in | 状态签到 | Check-in | |
| Chapter | 篇章 | Chapter | |
| North Star | 北极星 | North Star | 界面上用 ★ 符号 |
| Dashboard | （不显示标题） | （no title） | 指标区域直接呈现 |

## Settings 页

### 入口

- 齿轮图标（gearshape SF Symbol）· obsidian-40 · 14pt
- 位于 CoachView 和 MirrorView 的 toolbar leading 侧
- Toolbar 背景透明融入 parchment

### 布局

- Form + Section 分组，背景 parchment
- Section header：Mono 10px · obsidian-40 · uppercase · letter-spacing 2px
- 行内标签：Sans 14px
- 行内只读值：Serif 16px
- 破坏性按钮：Sans 14px · risk-red
- "即将推出"占位行：整行 obsidian-20（标签 + 文字），不可点击
- CTA "继续了解我"：Sans 14px · obsidian-10 边框 · Capsule 圆角

## 动效

| Token | 值 | 用途 |
|-------|-----|------|
| interaction | 150ms ease | 按钮 hover、选项切换 |
| standard | 200ms ease | 通用状态变化 |
| fanout | 300ms ease-out | 扇出面板滑入 |

### 禁止动效
- 庆祝/纸屑动画
- 完成时弹跳
- 成就放大
- 持续脉冲（仅加载状态允许）

## 组件清单

| 组件 | 位置 | 关键规则 |
|------|------|---------|
| StarpathTabBar | 全局 | 2-Tab · Mono · border-top |
| StarpathDivider | 全局 | 可配置 opacity + thickness |
| StarpathTypography | 全局 | .starpathSerif / .starpathSans / .starpathMono |
| TimestampSeparator | Coach | 时间戳组件，按间隔规则显示 |
| ChatMessage | Coach | Coach/User 双样式 |
| FilterBar | Mirror | 动态标签 + 计数 |
| NorthStarMetric | Mirror | 36px 数值 + 趋势图 |
| SupportMetric | Mirror | 3 列等宽 |
| LifeSignSummaryCard | Mirror | Copper 标题 + 统计 + Chevron |
| EventRow | Mirror | 类型标签 + 时间 + 摘要 |
| SettingsView | Settings | Form · Starpath 零圆角 · 5 Section |
| ProfileInfoSection | Settings | Store profile 只读 KV 展示 |
| CopperBreathingLine | Onboarding | 顶部 copper 渐变呼吸线 |

## Web 端适配

### 平台定位

Web 端是 iOS 的补充验证渠道，不是替代。核心设计语言（Starpath Protocol v2）跨平台保持一致，以下仅记录 Web 特有的适配规格。

### 布局：三栏可折叠

```
┌──────────┬───────────────────────────┬──────────────────┐
│ 对话历史  │         Coach 对话         │   Mirror 面板    │
│ (可折叠)  │          (始终)           │   (可折叠)       │
│  15-25%  │     ← 自动填充 →          │    15-30%        │
└──────────┴───────────────────────────┴──────────────────┘
```

- 分隔线：2px obsidian-10 竖线，hover 变 copper，`cursor: col-resize`
- 折叠态：只显示 icon 按钮（左：汉堡菜单，右：网格图标），宽度 36px
- 尺寸持久化：`localStorage` 自动保存

### 响应式断点

| 断点 | 布局 |
|------|------|
| < 768px（移动） | 两侧折叠，左侧覆盖层（overlay + backdrop）展开，右侧底部抽屉展开 |
| ≥ 768px（桌面） | 三栏全部可见可拖拽 |

### 交互状态（Web 特有）

iOS 只有 tap/no-tap。Web 端需要完整的交互状态链：

| 组件 | Default | Hover | Active | Focus | Disabled |
|------|---------|-------|--------|-------|----------|
| Pill 按钮 | obsidian-20 边框 | obsidian 背景 · parchment 文字 | 同 hover | 2px copper outline | obsidian-10 边框 · obsidian-40 文字 |
| 主按钮 (btn-primary) | obsidian 背景 | opacity 0.9 | opacity 0.8 | 2px copper outline | obsidian-40 背景 |
| 次按钮 (btn-secondary) | obsidian-10 边框 | obsidian-05 背景 | obsidian-10 背景 | 2px copper outline | obsidian-10 边框 · obsidian-40 文字 |
| 输入框 | obsidian-10 边框 | 同 default | 同 default | copper 边框 | obsidian-05 背景 |
| Thread 项 | 透明 | obsidian-05 背景 | obsidian-10 背景 | — | — |
| Coach 消息 👍/👎 | 隐藏 | 显示 obsidian-40 | copper | — | — |
| 拖拽手柄 | obsidian-10 竖线 | copper 竖线 | copper 竖线 3px | — | — |
| 链接 | copper · 无下划线 | copper · 下划线 | — | 2px copper outline | — |

### 光标样式

| 元素 | 光标 |
|------|------|
| 拖拽手柄 | `col-resize` |
| 可点击按钮/Pill | `pointer` |
| 输入框 | `text` |
| Coach 消息文本 | `default`（可选中复制） |
| 不可交互区域 | `default` |

### 滚动条

```css
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--obsidian-10); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--obsidian-20); }
```

### 键盘导航

| 快捷键 | 功能 |
|--------|------|
| Enter | 发送消息 |
| Shift+Enter | 消息换行 |
| Escape | 关闭 A2UI 抽屉 / 折叠侧边栏 |

### 字体加载策略

- LXGW WenKai：`next/font/local`，自托管 WOFF2，`font-display: swap`
- DM Sans / JetBrains Mono：Google Fonts，`font-display: swap`
- Fallback 链：`LXGW WenKai` → `KaiTi` → `STKaiti` → `serif`
- 图标库：Lucide React（替代 iOS SF Symbols）

### A2UI 抽屉（Web 适配）

- 形态：底部抽屉（shadcn Sheet），`max-width: 480px`，居中
- 背景遮罩：`rgba(26, 24, 22, 0.4)`
- 尺寸映射：`half` → 50vh, `three-quarter` → 75vh, `full` → 100vh
- 关闭手势：Escape 键、点击遮罩
- 容错：网络失败时显示横幅 + 重试，无法 resume 时发送带 `_network_failure` 标记的 fallback resume

### Web 特有组件

| 组件 | 位置 | 关键规则 |
|------|------|---------|
| ResizableLayout | 全局 | 三栏 PanelGroup + 两个 PanelResizeHandle |
| HistorySidebar | 左侧栏 | 按天分组 · 今天 copper 标题 · Chapter 分界线 |
| DragHandle | 分隔线 | 2px obsidian-10 · hover copper · col-resize |
| FeedbackButton | 右下浮动 | 固定定位 · obsidian-20 边框 · hover obsidian 背景 |
| MessageFeedback | Coach 消息 | hover 显示 👍/👎 · 点击 copper · LangSmith API |

### 线框图索引

| 文件 | 内容 |
|------|------|
| `~/.gstack/projects/Dexter-Yao-Voliti/designs/voliti-web-mvp-20260412/finalized.html` | 3 种方案对比（A/B/C） |
| `~/.gstack/projects/Dexter-Yao-Voliti/designs/voliti-web-mvp-20260412/option-b-plus.html` | 方案 B+（选定）：三栏展开/折叠/移动端/Thread 架构 |

---

## 待办事项

| 编号 | 事项 | 优先级 | 状态 |
|------|------|--------|------|
| TODO-1 | 北极星指标 + 支持性指标的 Coach 治理机制（Onboarding 设定 + 对话中调整） | 高 | 待做 |
| TODO-2 | Chapter / 身份宣言的设定和更新机制 | 高 | 待做 |
| TODO-3 | 趋势图点击查看历史记录的交互详设 | 中 | 待做 |
| TODO-4 | Filter 标签动态生成的数据结构适配 | 中 | 已完成 |
| TODO-5 | TimestampSeparator 组件实现 | 中 | 已完成 |
| TODO-6 | 用户消息背景宽度适配内容的 SwiftUI 实现 | 中 | 已完成 |
| TODO-7 | LXGW WenKai / DM Sans / JetBrains Mono 字体文件集成到 Xcode 项目 | 高 | 已完成 |
| TODO-8 | design-tokens.json 更新对齐 v2 | 中 | 已完成 |
| TODO-9 | component-rules.json 更新对齐 v2 | 中 | 已完成 |

---

## 设计稿索引

| 文件 | 内容 |
|------|------|
| `~/.gstack/projects/Voliti/designs/starpath-v2-mockups/starpath-v2-variant-A.html` | Variant A: Noto Serif SC + Inter + IBM Plex Mono |
| `~/.gstack/projects/Voliti/designs/starpath-v2-mockups/starpath-v2-variant-B.html` | Variant B: LXGW WenKai + DM Sans + JetBrains Mono (选定) |
| `~/.gstack/projects/Voliti/designs/starpath-v2-mockups/starpath-v2-variant-C.html` | Variant C: Source Serif 4 + Geist + Geist Mono |
| `~/.gstack/projects/Voliti/designs/starpath-v2-mockups/starpath-v2-chat-variants.html` | 聊天界面 3 种方案对比 (中英双语) |
| `~/.gstack/projects/Voliti/designs/starpath-v2-mockups/starpath-v2-chat-final.html` | 聊天界面最终方案 + 时间戳规则 + 命名约定 (中英双语) |
| `~/.gstack/projects/Voliti/designs/starpath-v2-mockups/starpath-v2-mirror-metrics.html` | MIRROR 指标体系重组 + 空状态设计 (中英双语) |
| `~/.gstack/projects/Voliti/designs/design-audit-20260406/starpath-protocol-audit.md` | Starpath v1 源码审计报告 |

---

## 决策记录

| 日期 | 决策 | 理由 |
|------|------|------|
| 2026-04-06 | Starpath v1 → v2 进化（非替换） | 竞品研究确认"策略顾问"定位是品类空隙，核心原则正确 |
| 2026-04-06 | Parchment #F5F1EB → #F4F0E8 | 微暖偏移，与 Claude App 拉开距离 |
| 2026-04-06 | 新增 Copper #B87333 信号色 | LifeSign/预案 是核心差异化，需要视觉签名 |
| 2026-04-06 | Serif: Noto Serif SC → LXGW WenKai | 楷体比宋体更有辨识度和书写温度 |
| 2026-04-06 | Sans: system → DM Sans | 几何感强，比 Inter 更干净 |
| 2026-04-06 | Mono: system → JetBrains Mono | 数据呈现更有力量，信号层权重提升 |
| 2026-04-06 | 聊天 Style 1 Refined | 用户消息圆角面板（内容适配宽度），Coach 无背景 |
| 2026-04-06 | 里程碑 → 时刻 (Moment) | 减少认知负荷 |
| 2026-04-06 | LifeSign → 预案 (中文) | 用户直觉可理解 |
| 2026-04-06 | 北极星指标 1 + 支持性指标 3 | 固定层级，Coach 治理 |
| 2026-04-06 | Filter 标签动态化 | 零记录不显示，减少噪音 |
| 2026-04-06 | 时间戳 5 级规则 | 参考微信/iMessage/WhatsApp 实践 |
| 2026-04-12 | Web 端适配章节加入 DESIGN.md | Web MVP 验证需要跨平台设计一致性 |
| 2026-04-12 | 三栏可折叠布局（替代 iOS 2-Tab） | Web 端利用宽屏优势，对话 + Mirror 并排 |
| 2026-04-12 | 响应式断点 768px（移动/桌面两档） | MVP 阶段简化，避免过度断点 |
| 2026-04-12 | A2UI 底部抽屉 max-width 480px | 桌面端居中避免过宽，手机端全宽 |
| 2026-04-12 | Web 交互状态表（hover/focus/active/disabled） | iOS 无 hover，Web 必须定义 |
