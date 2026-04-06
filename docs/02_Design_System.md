<!-- ABOUTME: Voliti 设计系统规范（Starpath Protocol v2），定义视觉语言、信息层级、关键组件与交互原则 -->
<!-- ABOUTME: 所有界面设计与交互实现应遵循本文档的风格约束与节奏设计 -->
<!-- ABOUTME: 本文档为设计理念与交互原则参考。精确的 tokens、色值、组件规格见项目根目录 DESIGN.md -->

# Voliti 设计系统 – Starpath Protocol v2

## 一、设计哲学

Voliti 的视觉与交互建立在两个原则之上：

1. **Identity First**：界面强化"成为那种人"的连续性，而非数字评判。
2. **Map Over Metrics**：用户走在路径上，而不是被仪表盘监控。

## 二、视觉语言

核心风格：**Obsidian & Parchment + Copper（Refined Industrial）**

色彩体系：

- **背景**：温暖羊皮纸色（#F4F0E8）
- **主色**：深黑曜石（#1A1816）
- **信号色**：铜色（#B87333）—— LifeSign/预案、北极星标签、趋势活跃柱
- **对齐状态**：低饱和冷色（#8A9A8A）
- **风险标记**：深红（#8B3A3A）—— 系统级风险，禁止用于行为评判

排版层级：

- **叙事层**（Serif）：LXGW WenKai —— Coach 消息、身份宣言、指标数值
- **界面层**（Sans）：DM Sans —— 用户消息、按钮、输入框、事件摘要
- **信号层**（Mono）：JetBrains Mono —— 时间戳、数据标签、Tab 栏、Section 标题

视觉原则：

- 高对比
- 大留白
- 线性分割
- 少容器化
- 零圆角容器（仅 pill 999px）
- 无奖励动画、无激励色彩

## 三、信息层级结构

Voliti 界面采用 **2-Tab 架构（COACH + MIRROR）**，承载四个信息层：

1. **Coach Layer（交互层）**：用户的主要停留空间。通过对话和扇出组件动态呈现信息。
2. **Horizon Layer（身份层）**：展示长期趋势、一致性指数与身份演化。
3. **Path Layer（行为层）**：以事件流与时间戳呈现行为节点与风险区。
4. **Journal Layer（叙事层）**：结构性反思与数据追踪。

页签映射：

| 页签 | 承载的信息层 | 职责 | 关键功能 |
|------|------------|------|---------|
| COACH | Coach Layer（主）+ 按需扇出其余三层 | 对话、扇出组件、Agent 主导的交互 | 实时对话、状态签到、饮食确认、预案触发 |
| MIRROR | Horizon Layer + Path Layer + Journal Layer | 指标概览与事件历史 | 北极星指标、支持性指标、LifeSign 摘要、事件流过滤 |

**MIRROR 页面结构（从上到下）**：
- **Chapter Context**：篇章编号、天数、身份宣言、目标摘要
- **North Star Metric**：北极星指标、7日趋势、Delta、查看全部记录
- **Support Metrics**：3 列等宽支持性指标（由 Coach 在 Onboarding 确定）
- **LifeSign 摘要**：激活的预案总数、成功次数、失败次数
- **Event Stream + Filter**：动态标签过滤、事件列表

Coach 扇出半 UI 是 Coach Layer 的核心机制——Coach 根据用户状态和交互需要，从预定义组件目录中选择组件，在对话区域上方以半屏或全屏面板呈现。用户随时可返回对话。

## 四、关键组件

### 4.1 全局通用组件

跨页签通用的视觉构件与交互模式：

- **StarpathTabBar**：2-Tab（COACH/MIRROR），Mono 12px uppercase，活跃态底部线（copper）
- **StarpathDivider**：线性分割（1px obsidian-10 标准、2px obsidian-15 周分隔、区块级 padding 16px）
- **StarpathTypography**：三层字体（.starpathSerif / .starpathSans / .starpathMono）
- **Obsidian Pill**：主交互按钮，全圆角黑色胶囊（999px），用于所有交互

### 4.2 COACH Tab 组件

**ChatMessage**：
- Coach 消息：Serif 16px，左对齐，无背景，右侧留 48px
- 用户消息：Sans 14px，右对齐，obsidian-05 背景，12px 圆角，内容自适应宽度，左侧留 64px

**TimestampSeparator**：
- 按消息间隔显示时间戳（5 级规则）：< 5min（无）、5~30min（09:12）、30min~当天（下午 3:20）、跨天 < 7天（昨天 15:20）、≥ 7天（3月28日 09:00）
- 样式：Mono 11px obsidian-40 居中

**ThinkingCard**：
- 默认折叠，点击展开
- 左边框 2px solid obsidian-10，文字 Sans 13px obsidian-40

**SuggestedReplies**：
- 水平滚动 Pill 样式，Sans 13px obsidian-10 边框，Capsule 圆角

**其他扇出组件**：
- 趋势卡片：可视化摄入区间、体重变化等趋势数据
- LifeSign 预案卡片：IF/THEN 标记（Mono 13px copper），预案选项
- 状态签到卡片：用于 State 阶段快速采集当前身体/情绪状态
- Protocol Prompt Card：State 微干预与决策引导，风格简洁克制

### 4.3 MIRROR Tab 组件

**NorthStarMetric**：
- 标签：Mono 10px copper uppercase ★ 前缀
- 数值：Serif 36px obsidian
- 单位：Mono 12px obsidian-40
- Delta：Mono 12px aligned（正向）/ risk-red（负向）
- 7日趋势：柱状图（高度 40px），非活跃柱 obsidian-10，今日柱 copper，日期标签 Mono 9px

**SupportMetric**：
- 固定 3 个，等宽三列，border-left 分隔（第一列无左边框）
- 标签：Mono 10px obsidian-40 uppercase
- 数值：Serif 20px obsidian
- 副标签：Mono 10px obsidian-40

**LifeSignSummaryCard**：
- 标题：Mono 12px copper uppercase "LIFESIGN" / "预案"
- 统计：Sans 14px（激活数、成功数、失败数）
- Chevron：12px obsidian-40 右对齐，点击进入完整列表

**FilterBar**：
- 动态标签：只显示有记录的事件类型
- Pill 样式：Sans 13px Capsule obsidian-10 边框
- 活跃态：obsidian 背景 parchment 文字
- 每个标签显示计数（Mono 10px）

**EventRow**：
- 类型标签 + 时间戳 + 事件摘要
- Serif 16px 正文，支持 Coach 轻量注解

## 五、交互原则

- 冷静、精准、非评判式语言
- 优先呈现结构信息，再提供叙事
- 干预频率克制
- 不使用鼓励式动画或奖励机制

系统像一位沉稳的策略顾问，而非健身教练。

## 六、节奏设计

- 行为后即时轻反馈
- 每日晚间结构复盘
- 每周趋势总结
- 每月身份回顾

各节奏点与 Coach 交互机制的对应：

| 节奏 | Coach 交互方式 |
|------|---------------|
| 行为后即时轻反馈 | 对话回复 + 可扇出饮食确认卡片或状态确认 |
| 每日晚间结构复盘 | 扇出当日总结组件（半屏或全屏） |
| 每周趋势总结 | 扇出趋势可视化 + MIRROR 页签 Coach 注解 |
| 每月身份回顾 | 扇出身份演化回顾 |

强调连续性，而非即时成就。

Voliti 的视觉与交互目标不是"激励"，而是营造一个让身份缓慢演化的空间。它让用户感觉自己不是被管理，而是在书写一条长期路径。

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-08 | 按文档规范整理格式；添加 ABOUTME 标识与变更记录；统一标题层级与列表样式 |
| 2026-02-08 | 信息层级增加 Coach Layer 与三页签映射；组件章节重构为基础视觉元素 + Coach 扇出组件目录；节奏设计补充 Coach 交互方式映射；视觉语言补充扇出面板约束 |
| 2026-02-12 | Map页设计定位更新：从"Horizon Layer + Path Layer"转为"Coach卡片归档（Chapter元数据 + 体验式干预卡片列表）"；删除Alignment Path Bar组件；信息呈现类组件调整（删除AI生成图片，新增应对计划卡片）；品牌更名：Aligner → Voliti, Wayfarer's Protocol → Starpath Protocol |
| 2026-04-06 | Starpath v2 进化对齐：3-Tab → 2-Tab 架构（COACH + MIRROR），色彩升级（Parchment #F4F0E8、新增 Copper #B87333），排版层级三分（LXGW WenKai / DM Sans / JetBrains Mono），组件库重构（新增 NorthStarMetric / SupportMetric / LifeSignSummaryCard / TimestampSeparator / FilterBar），MIRROR 页面取代 Map + Journal 的归档职能 |
