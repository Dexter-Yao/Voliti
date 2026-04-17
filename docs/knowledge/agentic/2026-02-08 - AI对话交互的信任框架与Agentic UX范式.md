---
type: source
author: IBM Design；Botpress；UX Magazine；Microsoft Design；Wharton（Puntoni, McKinlay, Meincke, Terwiesch et al.）
published: 2022-2026
source_url: https://www.ibm.com/design/ai/conversation/
topics:
  - conversation design
  - agentic UX
  - human-AI interaction
  - model routing
  - trust framework
created: 2026-03-01
updated: 2026-04-10
status: active
canonical: false
---

# AI对话交互的信任框架与Agentic UX范式

## 一句话简介

从对话设计基础到 Agentic UX 范式、情境风格决策、信任与稳定性框架、长期参与衰减应对、以及模型路由运营策略的综合设计指南；跨越 2022-2026 年多个权威来源，记录了 AI 交互设计从「让 Bot 说话」到「让 Agent 与人协作」的范式转变。补入 Karri Saarinen 关于 Linear 的一线判断后，这篇笔记的核心焦点进一步收敛为：AI 产品的可靠性感首先是界面设计问题，而不是模型问题。

## Takeaway

1. **AI 产品的“滑”主要是界面失职，不是模型失职**：当系统何时行动、是否可中止、由谁负责都未被界面明确表达时，用户会把模型的可变性直接感知为“不可靠”。
2. **稳定性是多维度问题**：不是让 AI 变得可预测，而是在可变性周围建立视觉、行为、推理、控制与责任归属的稳定锚点。
3. **Agent 必须在产品中原生出现，而不是以外挂形态出现**：身份披露、动作位置、状态表达、审计痕迹都应使用与人类协作者一致的界面语法。
4. **信任靠“证据”与“控制权”共同建立**：展示成功案例比解释技术原理有效 5 倍（+22.1%），但对 agent 场景而言，`stop/pause/review` 与责任显示同样是信任前提。
5. **长期参与必然衰减**，记忆连续性（连续性→信任→敞开→深化）是重要缓解手段；而在执行型 Agent 场景中，清晰的委托与可追责结构是另一条并行主线。

---

## 摘要

### 对话设计基础

AI 对话的原子结构由三层构成（IBM, 2022）：Topics（话题上下文）→ Exchanges（信息交换）→ Utterances（个体话语）。贯穿所有对话设计的三条主线：

- **Preferred Responses**：每次交互中用户都有隐含期望的回应类型，最大化首选回应并开发令人满意的非首选回应
- **Relevancy**：Bot 必须是有状态和上下文感知的——"最令人兴奋的是当我们感觉 bot '理解'了我们"
- **Repair**：犯错可以，但犯错时不能不相关——"It's okay for the bot to be wrong, but it's not okay for it to be wrong and irrelevant"

**2026 年 Botpress 提炼的 8 条设计原则**（Botpress, 2026）：以用户为中心（研究实际需求非假设行为）；清晰的意图识别（预判同一请求的多种表达方式）；结构化与引导（提供 2-3 个选项而非开放式提示）；一致性与清晰（统一语调、术语、格式）；错误处理与恢复（不归咎用户地引导回正轨）；自然流与轮换（将消息拆分为可消化片段）；多模态与无障碍；一致的个性与品牌声音。

**对话修复六类策略**（IBM / Wharton, 2022-2025）：Confirmation（确认理解）→ Information（补充信息）→ Solve（直接解决）→ Social（社交回应）→ Ask（追问澄清）→ Disclosure（坦诚系统局限）。核心是解释系统能/不能理解什么，引导用户自我修复而非让用户感到受挫。

### Human-like vs Machine-like 情境决策

**核心原则**：用户的情绪状态和任务性质决定风格选择，而非 chatbot 自身偏好。（Puntoni et al., 2024-2025）

#### 选择 Human-like 的情境

| 情境 | 为什么有效 | 效果量 |
|------|-----------|--------|
| 传递好消息（贷款批准、录用通知） | 共情放大正面体验 | 公司评价 +8.1% |
| 低压力情感任务（日常关怀、鼓励） | 社交临场感提升满意度 | 满意度 +18.4% |
| 需要用户感觉被倾听的场景 | 感叹词（"hmm"、"oh"）创造被倾听感 | +17.5% |
| 希望引导用户道德行为 | 共情、感谢等特征降低不道德倾向 | 不道德行为 -18.5% |

#### 选择 Machine-like 的情境

| 情境 | 为什么有效 | 效果量 |
|------|-----------|--------|
| 传递坏消息（拒绝、超预期价格） | 去人格化减少对"信使"的负面归因 | 接受概率 2.6x |
| 敏感信息收集（医疗/财务数据） | 无评判感降低自我审查 | 信息披露 +11.5% |
| 用户处于愤怒状态 | 类人风格反而激化情绪 | 满意度差距 +23.4% |
| 高压力/时间紧迫（航班改签） | 用户要效率不要寒暄 | 满意度 +15.7% |
| 尴尬产品购买 | 减少社交压力 | 交互意愿 +11.2% |
| 需要专业信任的建议 | 低萌度/专业感头像提升可信度 | 遵从建议 +23.5% |
| 易出错的自动化任务 | 类人风格下出错品牌伤害更大 | 品牌伤害 -25.4% |

**必须避免 Human-like 的场景**：高权威情境（抑制提问）、程序性/法律任务、潜意识陷阱（第一人称/表情符号/类人名字制造不切实际期待）。

**动态适应**：最佳系统实时分析用户情绪并调整风格，共同基线偏好为 Engagement + Serviceability + Decency。（Wharton, 2026）

**关键实现数据**：感叹词 → 被倾听感 +17.5%；快速响应 = 信任 +6.1%；不可避免的延迟必须解释原因；主动通知 68% 消费者品牌感知转正，但时机是关键。

### 从 Chatbot 到 Agentic AI：范式转变与新模式

> "Designers are now confronted with a question that didn't previously exist: are we designing screens for users, or are we designing intelligence that acts for them?" — UX Magazine

| 传统 Chatbot | Agentic AI (2026) |
|-------------|-------------------|
| 同步请求-响应 | 异步迭代工作流 |
| 人类操作、Bot 执行 | 人类验证、Agent 自主探索 |
| 固定脚本流程 | 渐进式信心呈现 |
| 功能性交互 | 协作式真相发现 |

**Agentic UX 四模式**（UX Magazine, 2025）：异步迭代工作流、证据收集模式（Agent 先提供建议性观察供用户接受/拒绝）、渐进式信心披露（低确定性→中确定性→高确定性假说）、Human-in-the-Loop（人类作为验证者而非操作者）。

**关键安全机制**：Start/Stop/Pause 控制（防止"魔法师学徒"失控）、高风险建议的审批工作流、成本透明与行动预览。

**Microsoft Agent 设计三维框架**（Microsoft Design, 2025）：Space（"Connecting, Not Collapsing"——连接事件知识人，后台不可见但行动始终可见可控）；Time（记忆系统连接过去，从静态通知转向主动发起）；Core（"Embrace Uncertainty While Establishing Trust"——承认 Agent 不确定性是预期内的，使确定性水平和推理可见）。

**Linear 的六条 Agent Interaction Guidelines**（Karri Saarinen, 2026）把上述范式进一步落到产品表层语法上：

1. Agent 必须明确披露自己是 Agent，避免被误认作人类；
2. Agent 必须原生 inhabits the platform，使用与人类一致的动作模式与视觉语言；
3. Agent 被调用后必须立即反馈，先建立心理闭环，再等待结果；
4. Agent 必须公开其内部状态，让人知道它在思考、等待、执行还是完成；
5. Agent 必须尊重 disengage 请求，被叫停后应立即停下；
6. Agent 不能承担责任，责任归属于授权它行动的人类。

这组六原则的重要性在于，它把“Agentic UX”从泛泛的协作体验问题，推进为**身份、状态、控制权与责任分配**四个具体界面层对象。

### 稳定性与信任：在 AI 可变性中建立锚点

生成式 AI 的核心矛盾：同一输入每次产生不同输出（generative variability），与传统设计"consistent and predictable"原则直接冲突。IBM 的回应是发明 **Consistency Anchors**，到 2026 年结合 Linear 等产品实践后，可视为五维框架：（IBM, 2022-2026；Saarinen, 2026）

- **视觉稳定** — 明确的颜色/字体/布局规则；AI Label 组件作为跨产品统一 AI 识别标志
- **行为稳定** — Agent 状态始终对用户可见；行动始终可见可控
- **推理稳定** — Case File 模式维护持久推理链，用户可审计；渐进式信心披露镜像人类侦探工作方式
- **控制稳定** — Start/Stop/Pause 控制；高风险审批工作流；Revert to AI 组件级回退
- **责任稳定** — 委托关系、授权人、执行者与结果归属必须可见；不能让 Agent 成为“做了事但没人负责”的界面黑箱

核心策略：**不是让 AI 变得可预测，而是在可变性周围建立稳定的锚点。**

**信任建设**（Wharton, 2025）：

| 杠杆 | 效果 | 核心机制 |
|------|------|----------|
| 展示准确性证据（成功案例） | +22.1% | 用户信"有效结果"不信"技术原理" |
| 快速响应 | +6.1% | 速度 = 能力 |
| 标注"持续学习" | 选择率 55% vs 43% | AI 显得可积累经验 |
| 展示优于人类的性能 | +37.2% | 差异化定位 |

**AI Disclosure 悖论**：告知用户在与 AI 对话会侵蚀信任，但监管要求披露。设计平衡：坦诚但不前置，强调"AI + 人类协作"。

**Overtrust 风险**：LLM 流畅性降低警惕；新领域中错误答案可能获得比正确答案更高信任。应对：主动表达不确定性。

**Uncanny Valley**：诡异感来源是期待与失误的不一致，而非不够像人。应创造独特特征而非追求完美类人。

**提升使用率的五大心理障碍**（Wharton, 2025）：感知不透明、无情感、僵硬、自主性威胁、非人类本质。应对：展示优于人类的性能（+37.2%）；混入小众推荐使建议"感觉个性化"；对非技术用户强调变革性而非技术细节（+31%）。

### 长期参与衰减与应对

所有纵向研究（3-12 周）一致观察到兴奋度和频率下降。这不是设计缺陷，而是用户与任何非人类系统互动的固有模式。

**缓解策略**：三层记忆系统（会话内 / 跨会话 / 关键摘要）创造连续性 → **连续性 → 信任 → 敞开 → 深化**。

**定位策略**：突出 AI 独特优势（24/7、无评判），定位为辅导工具而非友谊替代品。

### 模型路由与非 LLM 路径

设计良好的系统将 60–80% 请求路由到更小模型或非 LLM 路径（多个生产系统交叉印证）：

- RouteLLM（UC Berkeley, 2024）：实现 GPT-4 质量的 95%，但仅 26% 请求使用 GPT-4
- Anthropic 分层：Haiku 85% + Haiku 4.5 10% + Sonnet 5% → 平均 ~$0.40/1M vs 全用 Sonnet 的 $3/1M，省 87%
- Stripe：多阶段 fine-tuned 小模型 + vLLM 迁移，推理成本降 73%

**三种路由方式**：规则路由（if-then，适合流程明确场景）、分类器路由（轻量 ML 判断复杂度，适合语义模糊）、级联路由（先小模型处理，不达标再升级，适合成本敏感）。生产中最常见是规则做第一道过滤，分类器处理边缘情况。

**非 LLM 路径分类**：正则/规则提取（几乎零成本）、语义缓存（31% 查询可命中历史，5-20ms）、传统 ML 分类器（毫秒级）、数据库查询（FAQ/产品信息）、模板填充（通知消息）。

**实际成本降幅**：最低限度 30–50%，典型优化 60–70%，精细优化 75–85%，极致优化 85–98%。

---

## 参考链接

- [IBM AI Conversation Design](https://www.ibm.com/design/ai/conversation/)
  - 作者：IBM Design
  - 发布日期：2022

- [Botpress: Conversation Design](https://botpress.com/blog/conversation-design)
  - 作者：Botpress
  - 发布日期：2026

- [UX Magazine: Secrets of Agentic UX](https://uxmag.com/articles/secrets-of-agentic-ux-emerging-design-patterns-for-human-interaction-with-ai-agents)
  - 作者：UX Magazine
  - 发布日期：2025

- [Microsoft Design: UX Design for Agents](https://microsoft.design/articles/ux-design-for-agents)
  - 作者：Microsoft Design
  - 发布日期：2025

- [Wharton Blueprint: Effective AI Chatbots](https://ai.wharton.upenn.edu/wp-content/uploads/2025/05/Wharton-Blueprint-Effective-AI-Chatbots.pdf)
  - 作者：Puntoni, McKinlay, Meincke, Terwiesch et al.（Wharton）
  - 发布日期：2024-2025

- Karri Saarinen, "How to Design for Human-agent Interaction", Every
  - 作者：Karri Saarinen
  - 发布日期：N/A

- [RouteLLM (LMSYS)](https://lmsys.org/blog/2024-07-01-routellm/)
  - 作者：UC Berkeley / LMSYS
  - 发布日期：2024-07

## 相关笔记

- [[2026-04-10 - ChatGPT App 协同设计中的 The Third Body]]（补充在 [[ChatGPT Apps]] 中把模型作为第三参与者纳入界面与状态系统的产品化经验）
- [[2026-03-07 - OpenAI 广告策略演变与用户信任危机]]（补充助手信任被商业化行为侵蚀的案例）
- [[Topic - Agentic AI 系统构建]]（纳入 Agent 交互与用户信任的主题入口）
