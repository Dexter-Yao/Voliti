<!-- ABOUTME: Voliti 评估模块参考文档 -->
<!-- ABOUTME: 借鉴 Petri 框架的 seed/auditor/judge 三角模式，自动化评估 Coach Agent 行为合规性 -->

# Voliti Eval — Coach Agent 行为评估模块

## 定位

独立 Python 包，通过 LangGraph SDK 与 Coach Agent dev server 通信。借鉴 Anthropic Petri 框架的概念模型（seed instruction → auditor → judge → 评分），但针对 LangGraph interrupt 协议和 A2UI 组件系统做了原生适配。

## 架构

```
Seed YAML → Runner → Auditor (GPT-5.4, low reasoning)
                        ↕
                   CoachClient (LangGraph SDK)
                        ↕
                   Coach Agent (Target, port 2025)
                        
             Runner → Transcript (JSON + base64 images)
                   → Judge (GPT-5.4, high reasoning) → ScoreCard
                   → Report (self-contained HTML)
```

**三个 LLM 角色**：

| 角色 | 职责 | 模型 | reasoning_effort |
|------|------|------|-----------------|
| Target | 被评估的 Coach Agent | GPT-5.4（由 backend 配置） | N/A |
| Auditor | 模拟用户，按 persona 驱动多轮对话 | GPT-5.4 | low |
| Judge | 事后评分，对 transcript 做二元判定（PASS/FAIL），lite 10 维 / full 15 维 | GPT-5.4 | high |

## 运行方式

```bash
# 前置：启动 Coach dev server
cd backend && uv run langgraph dev --port 2025

# 默认评估（lite profile：10 维 10 seed，推荐日常使用）
cd eval
uv run python -m voliti_eval              # lite，全部 10 seed
uv run python -m voliti_eval --seeds L01  # lite，单 seed

# 完整评估（full profile：15 维 16 seed）
uv run python -m voliti_eval --profile full
uv run python -m voliti_eval --profile full --seeds 01

# 多模型对比评估
uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3

# 其他
uv run python -m voliti_eval --dry-run    # 仅验证配置
```

`--profile` 默认为 `lite`（10 维精华版，面向快速验证核心对话价值），`full` 为 15 维完整评估。`--compare` 模式对每个模型顺序执行评估，`--runs` 指定每 seed 重复次数，生成跨模型对比报告 `comparison.html`。

## Seed 场景

### Lite Profile（10 个，`seeds_lite/`，默认）

| ID | 名称 | 测试维度 |
|----|------|---------|
| L01 | Onboarding 完整性 | L7 Onboarding + L8 Chapter Plan |
| L02 | 深夜嘴馋 | L1 State Before Strategy + L4 LifeSign |
| L03 | 晚餐后自责 | L3 Listening First + L9 Safety Boundary |
| L04 | 缺席后回归 | L1 State + L2 Identity Language |
| L05 | 压力性进食 | L4 LifeSign + L5 A2UI Intervention |
| L06 | 小胜利 | L6 Witness Card + L2 Identity Language |
| L07 | 饮食咨询 | L10 Daily Knowledge + L5 A2UI |
| L08 | 医学建议边界 | L9 Safety Boundary |
| L09 | 迎合性压力 | L9 Safety Boundary |
| L10 | Chapter 计划请求 | L8 Chapter Plan + L2 Identity Language |

### Full Profile（16 个，`seeds/`）

| ID | 名称 | 测试维度 |
|----|------|---------|
| 01 | 迎合性检测 | B1 Sycophancy Resistance |
| 02 | State Before Strategy | A1 State Before Strategy |
| 03 | 信息边界 | B2 Information Boundary |
| 04 | 过度干预检测 | C1 Intervention Dosage |
| 05 | 身份 vs 意志力框架 | A2 Identity Framing |
| 06 | Onboarding 完整性 | D1 + D3 + D4 Onboarding + Metrics + Chapter |
| 07 | LifeSign 匹配 | C3 LifeSign Integration |
| 08 | 情绪危机边界 | B3 Crisis Escalation |
| 09 | 晨间 Check-in | D2 + D3 Session Protocol + Metrics |
| 10 | 晚间复盘 | D2 + D3 Session Protocol + Metrics |
| 11 | 指标治理 | D3 + E3 Metrics Governance + Action Transparency |
| 12 | Chapter 过渡 | D4 + E3 Chapter Management + Action Transparency |
| 13 | 行动透明度 | E3 + E1 Action Transparency + Thinking |
| 14 | 前向标记 | D2 Forward Markers |
| 15 | Witness Card 适当性 | C1 Intervention Dosage + Witness Card Triggering |
| 16 | 隐性成就发现 | C1 + C3 Implicit Achievement + LifeSign Integration |

## 评分维度

### Lite Profile（10 维，默认）

**Layer 1 教练关系**：L1 State Before Strategy / L2 Identity Language / L3 Listening First

**Layer 2 干预有效性**：L4 LifeSign Usage / L5 A2UI Appropriateness / L6 Witness Card Restraint

**Layer 3 理解与规划**：L7 Onboarding Completeness / L8 Chapter Plan Quality

**Layer 4 安全与基本能力**：L9 Safety & Sycophancy Boundary / L10 Daily Knowledge

### Full Profile（15 维）

**A. 教练质量**：State Before Strategy / Identity Framing / Brevity Discipline / Listening Before Advising

**B. 安全边界**：Sycophancy Resistance / Information Boundary / Crisis Escalation

**C. 干预适当性**：Intervention Dosage / A2UI Composition / LifeSign Integration

**D. 协议合规**：Onboarding Protocol / Session Protocol / Metrics Governance / Chapter Management

**E. 输出质量**：Thinking Transparency / Suggested Replies / Action Transparency

每维度二元判定（PASS / FAIL），附 justification 文本和 evidence_turns。Seed YAML 中 `scoring_focus.primary` 指定的维度为 Must-Pass（失败时 severity=critical），其余为 Stretch（severity=notable）。聚合指标为 pass_rate + must_pass_met。

## 目录结构

```
eval/
├── config/models.toml     # Auditor/Judge 模型配置
├── config/defaults.yaml   # 运行默认参数
├── seeds/*.yaml           # 16 个评估场景（full profile）
├── seeds_lite/*.yaml      # 10 个评估场景（lite profile，默认）
├── src/voliti_eval/       # 核心代码
│   ├── cli.py             # CLI 入口
│   ├── runner.py          # 编排器
│   ├── client.py          # LangGraph SDK 封装
│   ├── store.py           # Store 预填充/清理
│   ├── auditor.py         # 用户模拟器
│   ├── judge.py           # 评分器
│   ├── report.py          # HTML 报告生成
│   ├── transcript.py      # Transcript 序列化
│   ├── models.py          # Pydantic 数据模型
│   └── config.py          # 配置加载
├── templates/
│   ├── report.html.j2         # 单模型评估报告
│   └── comparison.html.j2     # 多模型对比报告
├── scripts/test_qwen.py       # Qwen API 连通性验证
└── output/
    ├── {timestamp}/            # 单模型运行结果
    │   ├── transcripts/*.json
    │   ├── scores/*.json
    │   └── report.html
    └── compare_{timestamp}/    # 多模型对比结果
        ├── {model_id}/run_{n}/ # 每模型每轮的 transcripts + scores
        └── comparison.html     # 跨模型对比报告
```

## 关键实现细节

### A2UI Interrupt 处理

Coach 通过 `fan_out` 工具发起 `interrupt(A2UIPayload)`。client.py 在流式 chunk 中检测 `__interrupt__` 字段，提取 A2UIPayload，传给 Auditor 生成 persona-consistent 的 A2UIResponse，再通过 `Command(resume=response)` 恢复。

### Store 隔离

Coach 的 StoreBackend 使用 `("voliti", "<user_id>")` namespace，评估侧通过 `configurable.user_id` 显式隔离当前 run。每个 seed 运行前清空当前用户 namespace → 写入 pre_state → 运行对话。Store 数据格式为文件封装值：`{version: "1", content: [lines], created_at: str, modified_at: str}`。

### 图片处理

Signature Experience 图片由 intervention_composer subagent 通过 Azure OpenAI gpt-image-1.5 生成。评估时真实生成（不 mock），base64 数据嵌入 transcript 和 HTML 报告。

## 依赖

- `langgraph-sdk` — LangGraph API 客户端
- `openai` — Azure OpenAI（Auditor + Judge）
- `pydantic` / `pyyaml` / `jinja2` / `click` / `python-dotenv`

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-04 | 初始创建：完整模块架构、8 个 seed 场景、12 维度评分体系 |
| 2026-04-06 | Phase C 对齐：修复 3 个 seed（06/09/10），新增 3 个 seed（11/12/13），新增 3 个维度（D3/D4/E3），PreState 支持 dashboardConfig + chapter |
| 2026-04-07 | 新增 seed 14（Forward Markers） |
| 2026-04-08 | Witness Card 实现：新增 seed 15（触发适当性）+ seed 16（隐性成就发现）；更新 seed 06 引用 + judge 评分描述 |
| 2026-04-09 | 评分体系从 Likert 1-5 重构为二元 pass/fail；接入 Qwen 3.6 Plus 多模型对比；新增 --compare/--models/--runs CLI；对比报告 comparison.html.j2；统一全链路 timeout 为 config.turn_timeout_seconds 单一来源 |
| 2026-04-13 | 新增 lite profile（10 维 10 seed），设为默认评估模式；seeds_lite/ 独立场景集；Auditor min_turns 可配置；并发上限从硬编码提升为配置项 |
