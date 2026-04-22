# PlanDocument 字段详规

读这份文档，当你要 `create_plan` 或做一个涉及多字段的 `revise_plan`——你需要在脑海里构建一份完整的 PlanDocument，而不是仅改一两个字段。字段命名、校验规则、跨字段约束都在这里。

## 整体结构

一个 PlanDocument 是一份嵌套的 JSON 文档：

```json
{
  "plan_id": "plan_2026_03_21_weight_loss",
  "status": "active",
  "version": 1,
  "predecessor_version": null,
  "supersedes_plan_id": null,
  "change_summary": null,

  "target_summary": "两个月减 10 斤",
  "overall_narrative": "两个月前体重回到一个我自己都不认识的数字，我想用两个月看看能不能把它掰回来。",
  "started_at": "2026-03-21T00:00:00+08:00",
  "planned_end_at": "2026-05-16T23:59:59+08:00",
  "created_at": "...",
  "revised_at": "...",

  "target": {
    "metric": "weight_kg",
    "baseline": 70.0,
    "goal_value": 65.0,
    "duration_weeks": 8,
    "rate_kg_per_week": 0.625
  },

  "chapters": [
    { "chapter_index": 1, "name": "...", ... },
    { "chapter_index": 2, "name": "...", ... }
  ],

  "linked_lifesigns": [
    { "id": "ls_latenight_craving", "name": "深夜食欲", "relevant_chapters": [1, 2] }
  ],
  "linked_markers": [
    { "id": "mk_trip", "name": "出差", "date": "2026-04-02", "impacts_chapter": 2, "note": "保底即可" }
  ],

  "current_week": null
}
```

## 顶层字段

- `plan_id` — 稳定标识，一次 `create_plan` 设定后不再变。命名约定 `plan_<YYYY>_<MM>_<DD>_<slug>`，slug 描述性不超过三个英文单词。
- `status` — `active` / `completed` / `paused` / `archived`。`create_plan` 时强制 `active`（系统覆盖）；`revise_plan` 可改 `status`，改到 `completed` 或 `archived` 意味着该 Plan 的生命周期结束。
- `version` — 从 1 递增。`create_plan` 强制 1；`revise_plan` 遇到结构性字段变更自动 `version++`；状态性字段变更（仅 `current_week`）不变 version。
- `predecessor_version` — 上一个 version 号。`create_plan` 强制 null；`revise_plan` 结构性修订时自动设为旧 version。
- `supersedes_plan_id` — 指向被替换的上一个 Plan 的 `plan_id`（不是 version）。这是跨 Plan 血缘字段，由显式 successor flow 维护；不要把它当成 `revise_plan` patch 字段。
- `change_summary` — 本次 `revise_plan` 的一句话说明。独立使用（只改 `change_summary`）会被拒；必须伴随实质字段变化。
- `target_summary` — 一句话概括这次 Plan 想到达的状态（如"两个月减 10 斤"、"三个月回到 60 公斤"）。用户可见。
- `overall_narrative` — 用户自己表达的动机叙事，10-800 字。这不是由 Coach 写的描述，是用户的话。保存用户的原话比修辞更重要。
- `started_at` / `planned_end_at` — 带时区的 ISO-8601 datetime。`planned_end_at` 必须晚于最后一章的 `end_date`（跨字段约束 #3）。

## target（TargetRecord）

```json
{
  "metric": "weight_kg",
  "baseline": 70.0,
  "goal_value": 65.0,
  "duration_weeks": 8,
  "rate_kg_per_week": 0.625
}
```

- `metric` — 目前仅支持 `weight_kg`，字段为 str 留出未来扩展（腰围、体脂率）。
- `baseline` / `goal_value` — 体重区间。未必非要跌，维持期也合法（`goal_value == baseline`）。
- `duration_weeks` — 2 到 26 之间。极端短（<2 周）不够形成习惯，极端长（>26 周）应拆为多个 Plan。
- `rate_kg_per_week` — 上限硬性 1.0 kg/周（Pydantic 层拒绝超出）。健康阈值的详细依据见 `numeric-guidelines.md`。用户要求 >1 kg/周时，你的职责是解释风险后协商下来，而不是直接写进 Plan。

## chapters（list[ChapterRecord]，1-6 章）

每章字段：

- `chapter_index` — 1 到 6，必须从 1 开始严格递增（跨字段约束 #2）。
- `name` — 2-20 字，用户可见的阶段名。
- `why_this_chapter` — 4-400 字，这一章为什么对用户重要。前端作为 tooltip 显示；写给用户看，不写给 Coach 内部看。
- `start_date` / `end_date` — ISO-8601 date。相邻章节必须按自然日连续：`chapters[i+1].start_date == chapters[i].end_date + 1 day`（跨字段约束 #1）。
- `milestone` — 4-200 字，这一章结束时用户能看到的可判断的状态。
- `process_goals` — 1 到 4 个。每个 Process Goal:
  - `name`（2-60 字）、`why_this_goal`（可选，≤200）、`weekly_target_days`（1-7）、`weekly_total_days`（1-7，默认 7）、`how_to_measure`（4-240）、`examples`（最多 6 条）
- `daily_rhythm` — 三个维度 `meals` / `training` / `sleep`，每个含 `value`（1-40 字）与 `tooltip`（4-200 字）。
- `daily_calorie_range` — `[下限, 上限]`，下限不低于基础代谢底线（详见 `numeric-guidelines.md`）。
- `daily_protein_grams_range` — `[下限, 上限]`，按用户实际体重计算。
- `weekly_training_count` — 0 到 7。0 合法（用户无法训练的阶段）但慎用。
- `previous_chapter_id` / `revision_of` — 可选，跨版本血缘追溯。

## linked_lifesigns / linked_markers

两者都是**引用列表**，不重复存储 LifeSign 或 Marker 的正文。

```json
{ "id": "ls_latenight_craving", "name": "深夜食欲", "relevant_chapters": [1, 2, 3] }
{ "id": "mk_trip", "name": "出差", "date": "2026-04-02", "impacts_chapter": 2, "note": "保底即可" }
```

- `relevant_chapters` / `impacts_chapter` 引用的 `chapter_index` 必须在 `chapters` 范围内（跨字段约束 #5、#6）。
- `id` 可能指向一个已不存在的 LifeSign / Marker（比如用户删掉了）；派生层会 try-skip 跳过缺失项，不会让整个 Plan 失败。

## current_week（CurrentWeekRecord，可选）

```json
{
  "updated_at": "2026-04-13T07:32:00+08:00",
  "source": "coach_inferred",
  "goals_status": [
    { "goal_name": "每周三次训练", "days_met": 2, "days_expected": 3 }
  ],
  "highlights": "周二训练比计划多做了 15 分钟",
  "concerns": "周六深夜又吃了一顿"
}
```

- `create_plan` 时通常为 `null`，第一次 `set_goal_status` 调用会自动初始化空壳。
- `goals_status[].goal_name` 必须在任一 Chapter 的 `process_goals[*].name` 中出现（跨字段约束 #4）。
- `week_index` 和 `active_chapter_index` **不在这里存储**——它们由派生层从 `today` 和 Plan 的日期字段计算。写 Plan 时不要去加这些字段。

## 跨字段约束（Pydantic `@model_validator` 守护）

| # | 约束 | 失败时错误消息定位 |
|---|------|------------------|
| 1 | 相邻 chapters 首尾相连 | chapters[i].end_date |
| 2 | chapter_index 从 1 严格递增 | chapters[*].chapter_index |
| 3 | planned_end_at ≥ 最后一章 end_date | planned_end_at |
| 4 | current_week.goals_status[*].goal_name ∈ 某 chapter process_goals | current_week.goals_status[*].goal_name |
| 5 | linked_lifesigns[*].relevant_chapters 在 chapter 范围内 | linked_lifesigns[i].relevant_chapters |
| 6 | linked_markers[*].impacts_chapter 在 chapter 范围内 | linked_markers[i].impacts_chapter |

Tool 返回的中文错误消息已格式化好"字段路径 + 问题描述 + 修复建议"三要素——那是给你修正文档的线索，不是给用户看的。
