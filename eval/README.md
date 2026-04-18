<!-- ABOUTME: Voliti Eval 运行文档 -->
<!-- ABOUTME: 说明评估模块的运行方式、输出结构与与 Charter 的关系 -->

# Voliti Eval

## 定位

Voliti Eval 用于评估 Coach Agent 是否在当前产品语义下：

1. 给了用户真正需要的帮助
2. 保持了运行时契约稳定
3. 把其余细节收口为 diagnostics 或人工复核项

本目录的设计锚点在：

- [EVALUATION_CHARTER.md](/Users/dexter/DexterOS/products/Voliti/eval/EVALUATION_CHARTER.md)

README 只负责运行与维护说明，不再承载评分哲学本身。

## 真相源

Eval 不复制产品历史概念。当前唯一真相源来自运行时本体：

- 持久化与路径契约：`backend/src/voliti/store_contract.py`
- A2UI 与 fan-out 契约：`backend/src/voliti/a2ui.py`、`backend/src/voliti/tools/fan_out.py`
- Witness Card 契约：`backend/src/voliti/tools/experiential.py`
- Coach / onboarding 语义：`backend/prompts/coach_system.j2`、`backend/prompts/onboarding.j2`
- 产品与用户研究：`docs/01_Product_Foundation.md`、`docs/07_User_Research.md`

## 当前评分架构

```text
Seed YAML
  -> Auditor（受约束场景执行器）
  -> CoachClient（LangGraph SDK）
  -> Transcript / Tool Calls / Store Before / After / Diff
  -> Deterministic Graders
  -> Judge
  -> ScoreCard
  -> HTML Report
```

### 三条评分通道

- **User Gate**
  真正影响用户体验与模型核心行为的硬门槛

- **Runtime Contract Gate**
  会导致运行时或协议层真实错误的硬门槛

- **Diagnostics + Manual Appendix**
  自动诊断细节与人工审核附录，不阻断放行

### Deterministic vs Judge

Deterministic 负责：

- A2UI 契约
- onboarding 产物最小集
- intervention 专用工具选择与 metadata
- scene anchor / reframe verdict 组件契约
- 其余 store / memory / goal-chapter / witness 的诊断性校验

Judge 负责：

- 只评分模型拥有的、用户可感知的行为与文本
- 允许多个合理好解
- intervention 场景只评模型生成文本，不评 UI 呈现与布局
- 不把无法稳定判断的“深层帮助感”强行变成正式 gate

以下内容刻意不做自动 gate，统一进入 `Manual Follow-up`：

- Future Self 对话是否真正有帮助
- Metaphor Collaboration 是否真正形成有帮助的隐喻协作
- UI / 布局 / 视觉 / 语气审美

这些部分不会通过 RAG 或额外检索被强行补判，而是直接进入人工复核。

## 维度通道

### User Gate

- `coach_state_before_strategy`
- `coach_recovery_framing`
- `coach_continuity_memory_surfacing`
- `coach_lifesign_management`
- `coach_forward_marker_prevention`
- `coach_action_transparency`
- `coach_safety_and_grounded_guidance`
- `if_then_quality`
- `reframe_text_fit`

### Runtime Contract Gate

- `contract_a2ui`
- `contract_onboarding_artifacts`
- `intervention_kind_selection`
- `intervention_metadata_correctness`
- `intervention_scene_anchor_present`
- `reframe_verdict_component_present`

### Diagnostics

- `coach_identity_language`
- `coach_intervention_dosage`
- `metaphor_verbatim_preservation`
- `source_domain_integrity`
- `reframe_verbatim_quote`
- `contract_store_schema`
- `contract_memory_protocol`
- `contract_goal_chapter_alignment`
- `contract_witness_card`

## Seed 结构

每个 seed 现在必须显式声明：

- `user_outcome`
- `allowed_good_variants`
- `manual_review_checks`
- `auditor_policy`
- `expected_artifacts`
- `judge_dimensions`
- `scoring_focus.primary`
- `scoring_focus.secondary`

约束如下：

- `primary` 只能放 gate 维度
- `secondary` 只能放 diagnostic 维度
- `judge_dimensions` 只能放 Judge 负责的文本 / 行为维度
- 任一冲突都必须在 `--dry-run` 阶段失败

## 场景矩阵

### Lite（10）

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

### Full（20）

`full = lite 10 + 扩展 10`

11. `11_onboarding_reentry_gap_fill`
12. `12_claimed_vs_revealed_memory_write`
13. `13_lifesign_revision_after_failure`
14. `14_chapter_transition_and_identity_review`
15. `15_holiday_restart_fatigue`
16. `16_a2ui_reject_skip_resilience`
17. `17_future_self_dialogue_trigger`
18. `18_scenario_rehearsal_trigger`
19. `19_metaphor_collaboration_trigger`
20. `20_cognitive_reframing_trigger`

## 运行方式

```bash
# 前置：启动 backend dev server
cd backend && uv run langgraph dev --port 2025

# 默认 lite
cd eval
uv run python -m voliti_eval

# 指定 seed
uv run python -m voliti_eval --seeds L01
uv run python -m voliti_eval --seeds L01,14

# full = lite 10 + 扩展 10
uv run python -m voliti_eval --profile full

# 单模型稳定性审计
uv run python -m voliti_eval --profile full --runs 3

# 多模型对比
uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3 --profile full

# 仅验证配置
uv run python -m voliti_eval --dry-run
uv run python -m voliti_eval --dry-run --profile full
```

## 输出结构

单模型运行会输出：

- `report.html`
- `run_*/transcripts/*.json` 与 `run_*/scores/*.json`（当 `--runs > 1`）
- `transcripts/*.json` 与 `scores/*.json`（当 `--runs = 1`）

多模型对比额外输出：

- `comparison.html`

## 报告阅读顺序

单模型报告固定顺序为：

1. `Execution Blockers`
2. `User Gate Summary`
3. `Runtime Contract Summary`
4. `Diagnostics Summary`
5. `Seed Detail`
6. `Manual Review Appendix`

其中：

- 正式放行只看 User Gate 与 Runtime Contract Gate
- Diagnostics 只看诊断，不阻断
- Manual Appendix 只承接人工复核，不参与 pass/fail
- `BLOCKED` 表示运行或评分过程中出现阻断，本次正式 gate 直接不通过
- `N/A` 表示该通道本次未被评估，不等于失败
- `Manual Follow-up` 表示这部分刻意不做自动评估，需要人工复核

每个 seed 详情会包含：

- 结果摘要
- Latest run detail
- What was intentionally not auto-scored
- 为什么过 / 为什么没过
- 核心证据 turn
- Diagnostic findings
- Manual review appendix
- 折叠项：Auditor prompt、Judge prompt、seed policy、完整 transcript、tool calls、store diff、relevant final files

## 发布前建议口径

```bash
cd backend && uv run python -m pytest
cd eval && uv run python -m pytest
cd frontend-web && pnpm build
cd eval && uv run python -m voliti_eval --profile full --runs 3
cd eval && uv run python -m voliti_eval --compare --models coach,coach_qwen --runs 3 --profile full
```

执行后必须人工阅读：

- 最新 `report.html`
- 最新 `comparison.html`
- 所有 gate failure 的 transcript
- 所有 flaky seed 的 transcript

## 目录结构

```text
eval/
├── config/
├── seeds/                # 扩展 10 个场景
├── seeds_lite/           # lite 10 个场景
├── src/voliti_eval/
├── templates/
├── tests/
├── EVALUATION_CHARTER.md
└── README.md
```
