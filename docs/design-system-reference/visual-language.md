<!-- ABOUTME: Starpath Protocol 视觉语言完整规范，整合色彩、排版、间距、组件与交互原则 -->
<!-- ABOUTME: 人类参考文档，写新组件或审查现有组件时以此为标准 -->

# Visual Language — Starpath Protocol

## 一、色彩系统

### 核心色彩

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-obsidian` | `#1A1816` | 主文字、主按钮背景、强调元素 |
| `--color-parchment` | `#F5F1EB` | 页面背景、面板背景、主按钮文字 |
| `--color-warm-dark` | `#2A2520` | Map 页暗色主题背景（教练洞察卡片全屏模式） |

### 功能色彩

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-risk-red` | `#8B3A3A` | 仅用于系统级风险标记，**禁止**用于行为评判 |
| `--color-aligned` | `#8A9A8A` | 对齐状态指示，低饱和冷绿灰 |
| `--color-aligned-cool` | `#8AACB8` | 图片生成专用，对齐状态冷蓝（图片生成 prompt 中的星光色） |

### 透明度变体

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-obsidian-10` | `rgba(26, 24, 22, 0.10)` | 细分割线、输入框边框、滑块轨道 |
| `--color-obsidian-15` | `rgba(26, 24, 22, 0.15)` | 周分隔线（稍粗，暗示时间周期） |
| `--color-obsidian-20` | `rgba(26, 24, 22, 0.20)` | 扇出面板顶部细线、Map 卡片边框 |
| `--color-obsidian-40` | `rgba(26, 24, 22, 0.40)` | 次要标签、时间戳、占位符文字 |

### 禁止色彩

- **禁止**：医疗蓝（任何 #0000FF 系列的蓝色）
- **禁止**：激励橙（#FF6B00 系列）
- **禁止**：鲜艳绿（#00FF00 系列，游戏化感）
- **禁止**：纯黑 #000000（用 obsidian 替代）
- **禁止**：纯白 #FFFFFF（用 parchment 替代）

---

## 二、排版系统

### 字体栈

| Token | 字体 | 用途 | 关键词 |
|-------|------|------|--------|
| `--font-serif` | `'Noto Serif SC', serif` | 叙事层 | Coach 消息、Journal 条目文本、教练洞察文案、Map 卡片文案 |
| `--font-sans` | `'Inter', sans-serif` | 界面层 | 用户消息、输入框、按钮文案、数据摘要、页面正文 |
| `--font-mono` | `'IBM Plex Mono', monospace` | 信号层 | 底部标签栏、时间戳、数值指标（kcal、状态分数）、数据标签 |

### 尺寸系统

| Token | 值 | 用途 |
|-------|-----|------|
| `--font-size-xs` | `12px` | 等宽标签、时间戳、数据单位、灰色次要信息 |
| `--font-size-sm` | `14px` | 界面操作文字、数据摘要、按钮文案 |
| `--font-size-base` | `16px` | 主要正文、Coach 消息正文 |
| `--font-size-lg` | `18px` | 扇出面板标题、Journal 重要条目 |
| `--font-size-xl` | `24px` | Map 页身份宣言、空状态提示标题 |

### 字间距

| Token | 值 | 用途 |
|-------|-----|------|
| `--letter-spacing-tabbar` | `2px` | 底部标签栏（COACH / MAP / JOURNAL，Signal Tower 风格） |

### 排版规则

- **行高**：正文 1.6，标题 1.3，数据标签 1.0
- **标签**：等宽体 12px，大写（`text-transform: uppercase`），40% 灰色
- **数值**：等宽体或无衬线体，14-16px，obsidian 色
- **Coach 消息**：衬线体，16px，1.6 行高，左对齐无气泡
- **用户消息**：无衬线体，14-16px，右对齐无气泡

---

## 三、间距系统

| Token | 值 | 典型用途 |
|-------|-----|---------|
| `--spacing-xs` | `4px` | 标签内部间距、图标与文字的微间距 |
| `--spacing-sm` | `8px` | 组件内部元素间距（如滑块标签与轨道） |
| `--spacing-md` | `16px` | 主要内容区域间距、卡片内边距 |
| `--spacing-lg` | `24px` | 卡片间距、主要区块间距 |
| `--spacing-xl` | `32px` | 页面级大留白、模块间隔 |

---

## 四、布局约束

### 固定尺寸

| Token | 值 | 位置 |
|-------|-----|------|
| `--tab-bar-height` | `44px` | 底部标签栏高度 |
| `--input-bar-height` | `48px` | Coach 页输入栏高度 |

### 扇出面板尺寸

| Token | 值 | 场景 |
|-------|-----|------|
| `--fanout-half` | `50vh` | 饮食确认卡片、状态签到卡片、Protocol Prompt Card |
| `--fanout-three-quarter` | `75vh` | 应对计划卡片、模式识别卡片 |
| `--fanout-full` | `100vh` | 趋势可视化、每日总结、身份回顾、图片全屏展示 |

### Map 卡片

| 约束 | 值 |
|------|-----|
| 图片宽高比 | `3:4`（竖向） |
| 图片宽度 | 占卡片宽度 80% 居中 |
| 卡片内边距 | 16px |
| 卡片间距 | 24px |

---

## 五、边框与分割线

| Token | 值 | 用途 |
|-------|-----|------|
| `--border-separator` | `1px solid rgba(26,24,22,0.10)` | 通用分割线（组件内、扇出面板底部按钮上方） |
| `--border-separator-week` | `2px solid rgba(26,24,22,0.15)` | Journal 页周一和月初的时间分隔线 |
| `--border-card` | `1px solid rgba(26,24,22,0.20)` | Map 页教练洞察卡片边框 |

**规则**：
- 无阴影（`box-shadow: none`）
- 无浮层效果（无 `z-index` 叠加视觉）
- 面板边界只用线性分割

---

## 六、动画与过渡

| Token | 值 | 用途 |
|-------|-----|------|
| `--transition-interaction` | `150ms ease` | 按钮 hover、选项按钮选中状态切换 |
| `--transition-standard` | `200ms ease` | 通用状态变化（如按钮 disabled 状态） |
| `--fanout-duration` | `300ms ease-out` | 扇出面板从底部滑入 |

**规则**：
- 无庆祝动画（confetti、bounce、scale-up）
- 无持续循环动画（loading pulse 仅用于真实等待状态）
- 过渡应克制，用户不应"注意到"动画，只感受到流畅

---

## 七、主要组件规范

### ObsidianPill（主交互按钮）

```
背景：--color-obsidian
文字：--color-parchment
圆角：999px（全圆角）
内边距：8px 16px
字体：--font-sans，14px，500
Hover：opacity 0.85
Disabled：opacity 0.4
```

### BottomTabBar（底部标签栏）

```
高度：44px
字体：--font-mono，12px，字间距 2px，大写
当前页签：--color-obsidian + 下方 2px 短下划线
非当前：40% 灰色
背景：--color-parchment（与页面同色）
顶部：1px 细线分隔（obsidian 10%）
三等分布局，无分隔线
```

### FanOutPanel（扇出面板）

```
动画：从底部滑入，300ms ease-out
背景：半透明 --color-parchment
顶部：1px 细线（obsidian 20%）
无阴影，无圆角
标题：--font-serif，18px
数据标签：--font-mono，12px，灰色
数据值：--font-sans，16px，obsidian
操作按钮：ObsidianPill
```

### ChatMessage（对话消息）

```
Coach（左对齐）：
  字体：--font-serif，16px，1.6 行高
  颜色：--color-obsidian
  无气泡背景

用户（右对齐）：
  字体：--font-sans，14-16px
  颜色：--color-obsidian
  无气泡背景

消息间距：16px
时间戳：仅在 > 30 分钟间隔时显示，--font-mono 12px，40% 灰色，居中
```

### MapCard（教练洞察卡片）

```
背景：半透明 --color-parchment
边框：1px obsidian 20%
内边距：16px
图片：3:4 比例，卡片宽 80%，居中
文案：--font-serif，16px，obsidian，图片下方 16px 间距
时间戳：--font-mono，12px，灰色，右下角
卡片间距：24px
```

### JournalEntry（Journal 条目）

```
日期头：--font-serif，16px，带星期
时间戳：--font-mono，12px，灰色
事件类型：--font-sans，14px，obsidian
数据摘要：--font-mono，12px，灰色
标签：方括号包裹 [在家]，行内排列
条目间：1px 细线（obsidian 10%）
逆时间序（最近在上）
```

---

## 八、禁止列表

以下所有项均被明确排除，原因见 `rationale/design-intent.md`：

**视觉**：
- 过度渐变
- 激励式色彩（橙、鲜绿、亮蓝）
- 医疗蓝
- 圆角卡片容器作为通用信息容器
- 阴影或浮层效果
- 红色用于行为评判

**界面元素**：
- 进度条
- 完成百分比
- 徽章/成就图标
- 连续打卡天数计数
- 庆祝动画
- 打卡按钮

**语言**：
- "偏航"、"脱轨"、"回到正轨"
- 鼓励式感叹号
- "你没有记录今天的饮食"
- 任何暗示"你做错了"的表达

---

## 变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-03-08 | 初始创建：从 doc/02_Design_System.md 和 doc/04_UI_Specification.md 整合并规范化 |
