<!-- ABOUTME: Voliti Eval 模块说明文档 -->
<!-- ABOUTME: 描述当前评估真相源、场景矩阵、混合评分架构与运行方式 -->

# Voliti Eval

## 定位

Voliti Eval 用于系统评估 Coach Agent 是否符合当前产品语义、运行时契约与教练行为要求。模块继续保留 `lite` / `full` / `compare` 的 CLI 外壳，但内部评分架构已经重建为：

- **Deterministic Graders**：使用代码直接校验 A2UI、Witness Card、Store、onboarding 产物、Goal/Chapter 对齐与记忆协议。
- **Behavior Judge**：仅对教练行为维度进行 LLM 判分，不再承担协议合法性校验。
- **Artifacts Layer**：每个 seed 运行后保留 transcript、tool call log、store before、store after 与 store diff，作为报告与 Judge 的共同证据链。

评估模块的唯一真相源来自当前产品运行时，而不是 eval 内部复制的历史概念。核心来源如下：

- 持久化与路径契约：`backend/src/voliti/store_contract.py`
- A2UI 与 fan-out 契约：`backend/src/voliti/a2ui.py`、`backend/src/voliti/tools/fan_out.py`
- Witness Card 契约：`backend/src/voliti/tools/experiential.py`
- Coach / onboarding 语义：`backend/prompts/coach_system.j2`、`backend/prompts/onboarding.j2`
- 产品与用户研究：`docs/01_Product_Foundation.md`、`docs/07_User_Research.md`

## 架构

```text
Seed YAML
  -> Runner
  -> Auditor（受约束的场景执行器）
  -> CoachClient（LangGraph SDK）
  -> Coach Agent

运行结果
  -> Transcript
  -> Tool Call Log
  -> Store Before / After / Diff
  -> Deterministic Graders
  -> Behavior Judge
  -> ScoreCard
  -> HTML Report / Comparison Report
```

### Auditor

Auditor 不再扮演泛化陪聊用户，而是执行 seed 中定义的受约束策略。每个 seed 必须声明：

- `entry_mode`：`new | resume | re_entry | coaching`
- `auditor_policy`
- `expected_artifacts`
- `judge_dimensions`

`auditor_policy` 固定包含：

- `latent_facts`
- `reveal_rules`
- `a2ui_plan`
- `challenge_rules`
- `stop_rules`

Auditor 默认遵循以下原则：

- 不替 Coach 补作业
- 只有被问到时才透露受限信息
- A2UI 优先执行 seed 计划
- A2UI 若未返回有效结构化结果，最多本地重试一次，仍失败则直接判定 seed 失败

### Judge

Judge 只读取行为相关维度，输入固定为四段：

1. `Transcript`
2. `Tool Summary`
3. `Store Diff Summary`
4. `Relevant Final Files`

Judge 明确禁止依据以下旧概念评分：

- `dashboardConfig.current_value`
- `chapter.identity_statement`
- quick path 必须创建首个 LifeSign
- `JourneyAnalysisMiddleware` 等已移除语义

## 统一维度库

当前评估只有一套主维度库，共 15 个维度。`lite` 与 `full` 的差异只体现在 seed 覆盖面，而不是使用不同 rubric。

### 硬契约 / 治理维度

- `contract_a2ui`
- `contract_witness_card`
- `contract_store_schema`
- `contract_onboarding_artifacts`
- `contract_goal_chapter_alignment`
- `contract_memory_protocol`

### 教练行为维度

- `coach_state_before_strategy`
- `coach_recovery_framing`
- `coach_identity_language`
- `coach_continuity_memory_surfacing`
- `coach_lifesign_management`
- `coach_forward_marker_prevention`
- `coach_intervention_dosage`
- `coach_action_transparency`
- `coach_safety_and_grounded_guidance`

### 判分边界

Deterministic graders 负责：

- A2UI payload / response 合法性
- `compose_witness_card(...)` 参数契约
- Store 路径、JSON 结构与旧字段拦截
- onboarding quick / full / re-entry 最小产物
- Goal / Chapter / 3 个 Process Goal / `dashboardConfig.support_metrics` 的 1:1 对齐
- profile 与 coach memory 的职责边界

Behavior Judge 负责：

- 对话是否先看状态再给策略
- 恢复是否采用“继续而非重来”的框架
- 是否使用 identity 语言
- 是否自然调取 profile / briefing / chapter / recent history 的连续性
- 是否优先匹配 / 修订已有 LifeSign
- 是否使用 forward marker 进行前瞻预防
- 干预剂量是否恰当
- 写入数据时是否解释了动作
- 是否保持 grounded guidance 与边界感

## 场景矩阵

### Lite（10 个，默认日常回归）

1. `L01_onboarding_quick_minimum_dataset`
2. `L02_onboarding_full_personal_system`
3. `L03_return_after_lapse_48h`
4. `L04_work_stress_lifesign_match`
5. `L05_return_after_absence_with_memory`
6. `L06_forward_marker_prevention`
7. `L07_chapter_scaffold_request`
8. `L08_implicit_achievement_witness`
9. `L09_boundary_mixed_case`
10. `L10_grounded_daily_guidance`

### Full（16 个）

`full` 语义为：**lite 10 个基础场景 + 6 个扩展场景**。

扩展场景如下：

11. `11_onboarding_reentry_gap_fill`
12. `12_claimed_vs_revealed_memory_write`
13. `13_lifesign_revision_after_failure`
14. `14_chapter_transition_and_identity_review`
15. `15_holiday_restart_fatigue`
16. `16_a2ui_reject_skip_resilience`

## 运行方式

```bash
# 前置：启动 backend dev server
cd backend && uv run langgraph dev --port 2025

# 默认 lite
cd eval
uv run python -m voliti_eval

# 指定单个或多个 seed
uv run python -m voliti_eval --seeds L01
uv run python -m voliti_eval --seeds L01,14

# full = lite 10 + 扩展 6
uv run python -m voliti_eval --profile full

# 多模型对比
uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3

# 仅做配置验证
uv run python -m voliti_eval --dry-run
uv run python -m voliti_eval --dry-run --profile full
```

## 输出内容

每次运行都会输出：

- `transcripts/*.json`
- `scores/*.json`
- `report.html`

多模型对比还会输出：

- `comparison.html`

单模型报告首页按“契约失败 / 行为失败”分区展示，并在 seed 详情中提供：

- 每个维度的 `score_source`
- `tool_calls`
- `store_diff`
- `relevant_final_files`
- transcript 证据

对比报告提供两条主轴：

- 硬契约通过率
- 行为维度通过率

## 目录结构

```text
eval/
├── config/
│   ├── defaults.yaml
│   └── models.toml
├── seeds/                # full 扩展 6 个场景
├── seeds_lite/           # lite 10 个场景
├── src/voliti_eval/
│   ├── auditor.py
│   ├── backend_contracts.py
│   ├── cli.py
│   ├── client.py
│   ├── config.py
│   ├── graders.py
│   ├── judge.py
│   ├── models.py
│   ├── report.py
│   ├── runner.py
│   ├── store.py
│   └── transcript.py
├── templates/
│   ├── comparison.html.j2
│   └── report.html.j2
└── tests/
```

## 设计约束

- 不在 eval 内复制 backend 的路径常量、枚举或 A2UI / Witness Card 契约
- quick onboarding 的硬要求是“最小数据集完整并可进入 coaching”，不是“必须先创建 LifeSign”
- Witness Card 失败不得阻塞 onboarding 完成，但若 seed 声明 `witness_required=true`，则必须在 deterministic grader 中显式失败
- 本轮评估只对齐当前 Web / backend 语义，不为历史 iOS 语义保留兼容维度

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-17 | 评分架构重建为 deterministic + behavior judge + artifacts 三层；统一 15 维主维度库；重写 lite/full 场景矩阵；报告改为契约失败 / 行为失败双视角；`full` 语义更新为 lite 10 + 扩展 6 |
