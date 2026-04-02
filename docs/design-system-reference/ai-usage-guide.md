<!-- ABOUTME: Starpath Protocol AI 使用指引，供 Claude/Cursor 等 AI 工具生成前端代码和图片时参考 -->
<!-- ABOUTME: 使用本设计系统前必读此文，了解文件优先级和常见违规模式 -->

# AI Usage Guide — Starpath Protocol

本文档面向 Claude、Cursor 等 AI 代码生成工具。在为 Voliti 生成前端代码、CSS、组件或 Gemini 图片 prompt 之前，先读此文。

---

## 一、文件优先级

按以下顺序读取上下文：

```
1. machine/design-tokens.json     ← 所有具体数值和 CSS 变量
2. machine/component-rules.json   ← 组件渲染规则和禁止项
3. rationale/design-language.md   ← 5 个判断标准（用于验证生成结果）
4. rationale/design-intent.md     ← 战略例外说明（避免"修复"刻意设计）
```

生成图片 prompt 时额外读取：

```
5. machine/image-prompt-tokens.json   ← 色彩、风格模块、模板参数
6. doc/05_Image_Generation.md        ← 完整 prompt 模板（含具体变量占位符）
```

---

## 二、生成新组件时的检查清单

生成任何新组件或修改现有组件后，对照以下 5 条逐一验证：

**1. 克制（Restrained）**
- [ ] 没有进度条、徽章、完成动画
- [ ] 每个界面只有一个主要行动点
- [ ] 空状态不用大量引导文字填充

**2. 导向（Navigational）**
- [ ] 没有使用"偏航"、"脱轨"、"完成度 X%"等表达
- [ ] 差异用中性色或路径语言表达，不用红绿色编码"好坏天"

**3. 连续（Continuous）**
- [ ] 没有连续天数计数或"今天未记录"的空白占位
- [ ] 成功完成没有明确的庆祝视觉（无 ✓ 动画、无徽章）

**4. 精准（Precise）**
- [ ] Coach 消息数据先行，结构在前
- [ ] 没有鼓励式感叹号或模糊表达
- [ ] 数据标签用等宽体（mono），数值用无衬线体（sans）分层区分

**5. 非评判（Non-judgmental）**
- [ ] 没有红色用于行为数据标记
- [ ] 没有"你吃多了"或"今天没控制住"这类措辞
- [ ] 空状态不暗示用户有未完成的义务

---

## 三、CSS 生成规则

### 必须使用 CSS 变量，不硬编码数值

```css
/* 正确 */
color: var(--color-obsidian);
font-size: var(--font-size-sm);
gap: var(--spacing-md);

/* 错误 */
color: #1A1816;
font-size: 14px;
gap: 16px;
```

### 字体选择规则

```css
/* 叙事内容（Coach 消息、Journal 文本、教练洞察）*/
font-family: var(--font-serif);

/* 界面内容（按钮、输入框、用户消息）*/
font-family: var(--font-sans);

/* 数据/信号（时间戳、数值、标签、底部标签栏）*/
font-family: var(--font-mono);
```

### 禁止的 CSS 属性组合

```css
/* 禁止：带颜色的 box-shadow */
box-shadow: 0 4px 12px rgba(0, 0, 255, 0.1);

/* 禁止：渐变背景 */
background: linear-gradient(to bottom, #xxx, #yyy);

/* 禁止：除 999px 以外的大圆角用于容器 */
border-radius: 16px; /* ← 用于按钮可以，用于信息容器禁止 */

/* 禁止：进度条类元素 */
.progress-bar { ... }
.completion-ring { ... }
```

---

## 四、生成图片 prompt 的流程

1. 从 `machine/image-prompt-tokens.json` 读取 `templates` 中对应的模板 ID
2. 从 `style_modules` 中选择 `STYLE_parchment` 或 `STYLE_warm_dark`（根据情感基调）
3. 将用户上下文填入模板的 `variables`，**直接使用用户原话中的隐喻**
4. 组装：`[SCENE 变量填充] + [STYLE 模块] + [TECHNICAL 模块] + [NEGATIVE 模块]`
5. 检查 `global_constraints`，确认无违反
6. 在 prompt 末尾添加 aspect_ratio 参数

**重要**：不要翻译或改写用户的隐喻表达。如用户说"感觉被洪流冲着走"，在 `metaphor_scene` 中保留"洪流"的意象，不要替换为通用的"压力"描述。

---

## 五、常见违规模式（AI 最容易生成的不对齐结果）

以下是 AI 工具在生成 Voliti 界面时最常见的错误，每条均附有正确替代：

| 错误模式 | 原因 | 正确替代 |
|---------|------|---------|
| 添加进度圆环或条形图 | 默认的"完成度"可视化 | 文字趋势描述或线图（点状，无填充区域） |
| 空状态显示"你还没有记录今天的数据" | 默认空状态文案 | "Coach 会在关键时刻为你生成洞察" 或 空白留白 |
| 用绿色标记"好天"、红色标记"坏天" | 默认的正负色彩编码 | 中性路径宽度变化或色彩饱和度差异 |
| Coach 消息末尾加感叹号 | 激励式语气习惯 | 句号或无结束符，数据陈述 |
| 按钮组带有 hover 时颜色变化到彩色 | 默认 hover 交互 | opacity 0.85（仅透明度变化） |
| 添加 loading 骨架屏 | 默认加载体验 | 保持空白，等待真实内容 |
| 使用 emoji 作为图标 | 默认图标方案 | 纯文字或极简 SVG 线条图标 |
| Journal 缺席日显示灰色占位行 | 默认列表完整性习惯 | 直接跳过，不显示缺席日 |
| Map 卡片使用大圆角（16px+） | 默认现代 UI 卡片风格 | border-radius: 0，用边框线分隔 |
| 图片 prompt 包含真人面孔描述 | 默认写实风格 | "abstract silhouette"、"shadow"、"environmental detail" |

---

## 六、战略例外不可"修复"

`rationale/design-intent.md` 第三节记录了刻意违反 UX 最优化原则的设计。这些不是 bug：

- **时间戳不持续显示** → 不要添加"显示全部时间戳"的选项
- **Journal 缺席日不显示** → 不要添加"查看未记录的日期"功能
- **没有总卡路里数字** → 不要添加"今日合计"字段
- **Coach 消息无气泡** → 不要添加气泡背景色改善"区分度"
- **没有打卡成功动画** → 不要在"记录完成"时添加任何庆祝动效

如果你认为某项违规是需要修复的设计缺陷，先查阅 `rationale/design-intent.md`。如确实不在战略例外列表中，再提出修改建议。

---

## 变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-03-08 | 初始创建：文件优先级、组件检查清单、CSS 规则、图片 prompt 流程、常见违规模式与战略例外说明 |
