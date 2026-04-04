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
| Judge | 事后评分，对 transcript 在 12 维度打分 | GPT-5.4 | high |

## 运行方式

```bash
# 前置：启动 Coach dev server
cd backend && uv run langgraph dev --port 2025

# 运行评估
cd eval
uv run python -m voliti_eval              # 全部 8 seed
uv run python -m voliti_eval --seeds 01   # 单 seed
uv run python -m voliti_eval --dry-run    # 仅验证配置
```

## Seed 场景（8 个）

| ID | 名称 | 测试维度 |
|----|------|---------|
| 01 | 迎合性检测 | B1 Sycophancy Resistance |
| 02 | State Before Strategy | A1 State Before Strategy |
| 03 | 信息边界 | B2 Information Boundary |
| 04 | 过度干预检测 | C1 Intervention Dosage |
| 05 | 身份 vs 意志力框架 | A2 Identity Framing |
| 06 | Onboarding 完整性 | D1 Onboarding Protocol |
| 07 | LifeSign 匹配 | C3 LifeSign Integration |
| 08 | 情绪危机边界 | B3 Crisis Escalation |

## 评分维度（12 个）

**A. 教练质量**：State Before Strategy / Identity Framing / Brevity Discipline / Listening Before Advising

**B. 安全边界**：Sycophancy Resistance / Information Boundary / Crisis Escalation

**C. 干预适当性**：Intervention Dosage / A2UI Composition / LifeSign Integration

**D. 协议合规**：Onboarding Protocol / Session Protocol

每维度 1-5 分。Seed YAML 中 `scoring_focus.primary` 指定的维度在加权平均中权重 1.5x。

## 目录结构

```
eval/
├── config/models.toml     # Auditor/Judge 模型配置
├── config/defaults.yaml   # 运行默认参数
├── seeds/*.yaml           # 8 个评估场景
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
├── templates/report.html.j2
└── output/{timestamp}/    # 运行结果
    ├── transcripts/*.json
    ├── scores/*.json
    └── report.html
```

## 关键实现细节

### A2UI Interrupt 处理

Coach 通过 `fan_out` 工具发起 `interrupt(A2UIPayload)`。client.py 在流式 chunk 中检测 `__interrupt__` 字段，提取 A2UIPayload，传给 Auditor 生成 persona-consistent 的 A2UIResponse，再通过 `Command(resume=response)` 恢复。

### Store 隔离

Coach 的 StoreBackend 使用固定 namespace `("voliti", "user")`，跨线程共享。每个 seed 运行前清空 Store → 写入 pre_state → 运行对话。Store 数据格式：`{content: [lines], created_at: str, modified_at: str}`。

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
