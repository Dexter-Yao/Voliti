<!-- ABOUTME: Gemini 3 Global Hackathon 获奖策略，定义差异化定位、评分映射与技术展示路径 -->
<!-- ABOUTME: 基于竞品分析与评审标准制定，指导 demo 开发与提交材料准备 -->

# Gemini 3 Hackathon 获奖策略

## 一、评分标准与得分策略

| 标准 | 权重 | 评审关注点 | Voliti 得分策略 |
|------|------|-----------|---------------------|
| Technical Execution | 40% | Gemini 3 深度集成、代码质量、功能完整性 | 多模态管线（视觉理解 → 文本推理 → 图像生成）贯穿单次交互 |
| Innovation / Wow Factor | 30% | 问题重构、独特方案、惊喜感 | "Coach 即界面"——Agent 不只回复文字，还主动生成视觉体验 |
| Potential Impact | 20% | 真实问题、目标市场规模、可扩展性 | 3000 万+知识工作者面临"知行不一"，减脂仅是行为对齐 OS 的第一个场景 |
| Presentation / Demo | 10% | 问题定义清晰、demo 有效、技术说明到位 | 3 分钟内完整展示 S-PDCA 流程中 Gemini 3 的五种能力 |

## 二、必须避开的陷阱

黑客松明确 discourage 以下项目类型：
- **Generic nutrition chatbot** → Voliti 必须展示远超聊天的能力
- **Prompt-only wrapper** → 需要 robust 多 Agent 系统
- **Simple vision analyzer** → 食物识别只是基线，需要更深的情境/行为理解
- **Baseline RAG** → Gemini 3 的 1M token context 使简单检索成为 table stakes
- **Medical advice** → 不生成医疗或心理健康诊断建议

## 三、往届获奖项目规律

分析 2024 Gemini API Developer Competition 获奖项目（Jayu、Vite Vere、Outdraw AI、Gaze Link、ViddyScribe 等），提炼共性：

1. **真实的人类问题**——不是生造痛点，而是特定人群的具体困境
2. **多个 Gemini 能力协同工作**——不是 single-capability demo
3. **清晰的 before/after 叙事**——没有你的方案，用户的生活是怎样的
4. **特定的目标人群**——越具体越好，"所有想减肥的人"太泛
5. **生产级 UX**——打磨过的体验，不是原型感

## 四、差异化定位

### 核心叙事

Voliti 不是在跟减肥 App 竞争。它是将 Leadership Coaching 方法论应用于人类行为的系统。"减脂"是第一个验证场景，本质是在构建**行为对齐操作系统**。

### 与预期竞品的区分

| 他们做的 | 我们做的 |
|---------|---------|
| 回答营养问题 | 维持跨天的推理连续性 |
| 追踪卡路里 | 构建身份一致性 |
| 推荐菜谱 | 解码行为阻抗模式 |
| 展示仪表盘 | 生成个人星座旅程地图 |
| 扫描食物标签 | 理解行为的情境触发条件 |
| 逐条交互 | 长期运行的 Agentic 教练关系 |

### 黑客松 Track 映射

Voliti 最契合 **Marathon Agent** track（跨天自主推理）+ **Creative Autopilot** track（多模态内容生成），但不局限于单一 track。

## 五、Gemini 3 技术展示矩阵

需要在 demo 中清晰展示以下 Gemini 3 独有/核心能力：

| Gemini 3 能力 | 集成方式 | Demo 展示时刻 |
|--------------|---------|-------------|
| **Thinking Process** | Coach 分析行为模式时使用高思考级别 | 展示 Coach 的推理链——"我注意到你连续三天在晚间高压时选择高热量食物" |
| **Thought Signatures** | 跨会话保持教练推理连续性 | "三天前我们讨论过的压力饮食模式，今天再次出现了" |
| **Agentic Vision** | 食物照片分析 + 视觉标注（bounding boxes） | 用户上传食物照片 → Gemini 标注识别区域，推断情境 |
| **Nano Banana Pro** | 教练干预中生成个性化视觉图像（未来自我可视化、场景预演、隐喻图像化） | Coach 识别行为模式后主动生成个性化图像辅助用户理解——不是数据可视化，而是教练工具 |
| **混合文图输出** | 单次 API 调用同时返回教练分析 + 个性化干预图像 | 模式分析场景：文字洞察 + 基于用户隐喻语言的图像同步呈现 |
| **1M Token Context** | 读取完整行为账本进行模式分析 | 加载 21 天数据，即时识别跨周期规律 |

## 六、提交材料规划

### 200 字描述（英文）

核心要点：
- Problem: Knowledge workers face intent-action misalignment, not information gaps
- Solution: Leadership Coach using S-PDCA methodology
- Gemini 3 Integration: Agentic Vision (food photo with evidence annotation), Thought Signatures (multi-day coaching continuity), Thinking Levels (adaptive reasoning depth per S-PDCA phase), Nano Banana Pro (constellation map generation), 1M context (full behavior history pattern analysis)
- Impact: 30M+ knowledge workers, extensible to sleep/exercise/focus

### 3 分钟 Demo 结构

| 时段 | 内容 | Gemini 3 能力 |
|------|------|-------------|
| 0:00-0:25 | Hook：为什么聪明人总做不到显而易见的事？ | — |
| 0:25-0:50 | Voliti 的不同：不是 diet tracker，是 Leadership Coach | — |
| 0:50-1:20 | 食物照片 → 视觉标注 + 情境推断 | Agentic Vision |
| 1:20-1:50 | Coach 记忆三天前的讨论 + 模式识别 | Thought Signatures + 1M Context |
| 1:50-2:05 | Coach 生成体验式干预图像（隐喻图像化） | Nano Banana Pro + 混合文图输出 |
| 2:05-2:20 | Map 页：目标+进度+卡片归档，演示删除卡片 | A2UI 复用 + Store 持久化 |
| 2:20-2:45 | 展示完整架构图 + 扩展性 | Thinking Levels |
| 2:45-3:00 | Call to action：demo 链接 + 代码仓库 | — |

## 七、风险规避

1. **医疗声明风险**：定位为"Leadership Development"而非"Health Management"
2. **API 限制**：demo 视频预录，避免现场 API 超限
3. **代码质量**：public repo 需 README、架构图、Gemini 3 集成说明
4. **时区**：截止 Feb 9 5pm PST = Feb 10 9am CST

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-09 | 初始创建：评分策略、差异化定位、技术展示矩阵、提交材料规划 |
| 2026-02-09 | Nano Banana Pro 展示策略从数据可视化调整为教练干预图像生成；Demo 结构同步更新 |
| 2026-02-09 | Demo 结构更新：Map 页面重设计为卡片归档视图，演示时长调整为 2:05-2:20，增加删除卡片操作展示 |
