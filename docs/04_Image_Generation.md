<!-- ABOUTME: Witness Card 图片生成技术指南，定义 API 参数、Subagent 架构、统一视觉体系与 Prompt 工程实践 -->
<!-- ABOUTME: 产品定位与触发逻辑见 01_Product_Foundation.md 4.1 节"见证系统" -->

# Witness Card 图片生成技术指南

**前置阅读**：`/docs/01_Product_Foundation.md` 4.1 节（教练干预体系 + 见证系统）、第六节（Guardrail）

本文档聚焦技术实现层：如何用 Azure OpenAI gpt-image-1.5 生成 Witness Card 中的场景图片。关于**见证系统的产品定位**、**触发逻辑**、**干预与见证的分离**，请参考 01_Product_Foundation.md。

## 一、产品定位与技术约束

Witness Card 是用户旅程中里程碑时刻的纪念卡片。图片是卡片的一部分，不独立存在。

**关键约束**：
- 图片不承载文字——文字在卡片框架的独立区域呈现
- 图片服务于"见证"（这个时刻值得被记住），不服务于"干预"（帮用户改变行为）
- 同一用户的所有 Witness Card 图片在视觉上必须属于同一体系
- 图片必须基于用户的具体场景和经历，不使用通用意象

## 二、模型与 API 参数

| 参数 | 值 |
|------|-----|
| 部署名 | `gpt-image-1.5` |
| API 端点 | Azure AI Foundry（`AZURE_OPENAI_ENDPOINT`）|
| API 版本 | `2025-03-01-preview` |
| 支持尺寸 | `1024x1024`、`1024x1536`、`1536x1024` |
| 质量等级 | `high`（生产环境）|
| 输出格式 | `png`（支持 `jpeg`、`webp`）|
| 返回格式 | 始终返回 base64 数据（无 URL）|

### 尺寸映射

Witness Card 图片区域为固定比例，由卡片框架模板决定：

| 原 aspect_ratio | 映射到 size | 说明 |
|-----------------|------------|------|
| `3:4` | `1024x1536` | 竖版（默认）|
| `4:3` | `1536x1024` | 横版 |
| `1:1` | `1024x1024` | 正方形 |

## 三、Subagent 架构

图片生成由 Witness Card Composer Subagent 执行。

```
Coach Agent (Supervisor)
│
│  1. Coach 判断里程碑时刻 → 决定生成 Witness Card
│  2. Coach 构造 delegation：成就描述、用户上下文、情感基调
│
├── Witness Card Composer Subagent
│   ├── 解析 Coach delegation
│   ├── 选择色温方向（暖色 / 冷色）
│   ├── 组装图片 prompt（场景 + 风格 + 技术 + 约束）
│   ├── 撰写卡片文字（Coach 语气的个性化叙事）
│   └── 调用 compose_witness_card tool
│       ├── Azure OpenAI gpt-image-1.5 生成图片
│       ├── 组装 Witness Card（框架 + 图片 + 文字 + 元数据）
│       └── interrupt() → FanOutPanel → 用户收下/拒绝
```

## 四、统一视觉体系

所有 Witness Card 图片共享同一视觉体系，Coach 在体系内选择色温方向。

### 不变元素（品牌一致性）

- 插画/水墨/水彩风格，非写实渲染
- 纸张质感（handmade paper texture）
- 大面积留白（≥40%）
- 避免真人面孔（使用剪影、抽象形态、环境细节）
- 去饱和、柔和色调
- 无游戏化元素（无徽章、爆炸、五角星）

### 可变元素（Coach 决定）

**色温轴**：Coach 根据里程碑的情感基调选择方向。

**暖色调**（成长、温柔、被看见的时刻）：
```
暖色羊皮纸背景（#F5F1EB），深黑曜石（#1A1A1A）作主体，
水彩渲染，有机笔触。温暖、个人化、安静的骄傲感。
```

**冷色调**（突破、力量、掌控的时刻）：
```
暖黑背景（#2A2520），低饱和冷蓝（#8AACB8）作点缀，
水墨渲染，精确线条。冷静、客观、内在力量感。
```

## 五、Prompt 组装

每个图片 prompt 由四个模块组装：`[SCENE] + [STYLE] + [TECHNICAL] + [NEGATIVE]`。

### [SCENE] — 用户场景（Subagent 根据 delegation 构造）

场景必须基于用户的**具体经历**，不使用通用意象。

好的场景："A kitchen table at dawn, a bowl of simple congee with side dishes, morning light on chopsticks"（来自用户"我今天早上自己做了早餐"的成就）

差的场景："A person achieving their goals in a beautiful setting"（通用、无锚点）

**场景构造原则**：
- 从用户的原话中提取具体物件、地点、时间
- 用叙事式段落描述，不用关键词列表
- 场景只占画面的 40-60%，其余留白
- 人物用剪影或背影，不画面部

### [STYLE] — 根据色温选择（见第四节）

### [TECHNICAL]
```
Medium format film aesthetic with subtle organic grain.
Natural side lighting, soft and diffused.
Non-photorealistic rendering. Illustration and painting style throughout.
```

### [NEGATIVE]
```
This image must not contain: photorealistic rendering, colorful or vibrant palettes,
busy compositions, excessive gradients, motivational graphics, medical blue,
bright green/yellow/orange, rounded containers, drop shadows, glossy effects,
gamification elements (badges, stars, explosions), fitness influencer photography,
stock photo people, cartoon or emoji style, high saturation, 3D effects, watermarks,
realistic human faces, text overlays, typography, words or letters.
Keep the palette desaturated and muted.
```

注意：[NEGATIVE] 中新增了 `text overlays, typography, words or letters`，因为 Witness Card 的文字在卡片框架中独立呈现，图片本身不嵌入文字。

## 六、Prompt 工程注意事项

1. **叙事式描述**优于关键词列表——按 场景→主体→细节→约束 组织
2. **颜色双重锚定**——hex 代码 + 描述性语言：`"warm parchment (#F5F1EB, like aged cream paper)"`
3. **显式要求留白**——"The scene occupies the lower 40% of the canvas, upper 60% is empty parchment"
4. **正面描述优先**——关键约束写成正面描述融入 Style，负面约束作兜底
5. **非写实强化**——反复强调 "illustration"、"painting"、"non-photorealistic rendering"
6. **用户语言优先**——将用户原话中的隐喻、物件直接嵌入 prompt
7. **避免真人面孔**——明确写 "silhouette figure" 或 "abstract form"
8. **不嵌入文字**——图片不含任何文字，文字在卡片框架中独立处理
9. **情绪色温匹配**——温暖/成长时刻用羊皮纸底，力量/突破时刻用暖黑底
10. **场景克制**——减少叙事细节量以保证留白。描述 3-5 个关键物件即可，不要铺满画面

## 七、Witness Card 卡片结构

```
┌─────────────────────────────┐
│  [Voliti 品牌标识]     [日期] │
│                              │
│  ┌────────────────────────┐  │
│  │                        │  │
│  │    AI 生成的场景图片    │  │
│  │    （无文字叠加）       │  │
│  │                        │  │
│  └────────────────────────┘  │
│                              │
│  "连续21天，你每天早上都选择  │
│   了先喝水再看手机。"        │
│                              │
│  ── 你的第一个 Chapter 完成  │
│                              │
│            [用户名]          │
└─────────────────────────────┘
```

**框架元素**：
- 品牌标识（Voliti logo / wordmark）
- 日期（里程碑发生的日期）
- 图片区域（AI 生成，无文字）
- 文字区域（Coach 撰写的个性化叙事，独立排版）
- 成就标题（简短的里程碑描述）
- 用户名

文字由 Intervention Composer Subagent 与图片同时生成，确保文字与图片在情感和内容上协调。

## 八、与旧系统的区别

| 维度 | 旧系统（教练干预图像） | 新系统（Witness Card） |
|------|---------------------|---------------------|
| 定位 | 干预工具（帮用户改变行为） | 纪念品（见证用户的成就） |
| 触发 | Coach 判断"文字不够用" | Coach 判断"这是里程碑时刻" |
| 图片类型 | 5 种固定模板（future_self 等） | 基于用户具体场景自由生成 |
| 文字处理 | 叠加在图片上 | 在卡片框架中独立呈现 |
| 风格 | Warm/Cool 两套不同体系 | 统一体系内的色温轴变化 |
| 留存价值 | 一次性（看完即走） | 永久收藏、反复回看 |

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-09 | 初始创建：模型参数、Subagent 架构、模块化 prompt 体系、6 个数据可视化测试 prompt |
| 2026-02-09 | 架构重定位：图像生成从数据可视化转向教练干预工具；替换全部 6 个模板为 5 个教练干预模板 |
| 2026-02-09 | 文档重新定位为技术实现指南；删除理论基础章节（移至 01_Product_Foundation.md）|
| 2026-04-01 | 图片生成模型从 Gemini 3 Pro Image 迁移至 Azure OpenAI gpt-image-1.5 |
| 2026-04-07 | 全面重构：从"教练干预 Prompt 模板库"转为"Witness Card 图片生成技术指南"；图片不再承载干预功能，仅用于里程碑见证；移除 5 种固定干预模板和部署表；新增统一视觉体系（品牌一致性 + 色温轴）；图片不再嵌入文字（文字在卡片框架独立呈现）；新增卡片结构定义；新增场景构造原则和留白策略 |
