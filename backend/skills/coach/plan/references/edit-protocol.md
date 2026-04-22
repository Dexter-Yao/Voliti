# Edit Protocol · revise_plan 的合并语义与共建话术

读这份文档，当你准备调 `revise_plan`——无论是调一个小字段（`change_summary` 加一句）还是做结构性修订（换一个 Process Goal、调整 Chapter 边界、换 target）。这里讲的是：patch 的合并语义长什么样；什么样的修改会被系统当成"结构性"而归档新版本；以及和用户协商修订时的几个行之有效的模式。

## PlanPatch 的合并规则

`revise_plan(patch)` 接受的 `patch` 是一个部分字段的 `PlanPatch`——只列你想改的字段，不列的字段保留原值。

### 顶层字段

这几个字段传了就替换，不传就保留：

- `status` / `change_summary` / `target_summary` / `overall_narrative` / `planned_end_at`
- `target`（整体替换 TargetRecord）
- `linked_lifesigns` / `linked_markers`（整体替换——不是追加）

注意 `linked_*` 的整体替换语义：如果 Plan 现有 `linked_lifesigns: [ls_A, ls_B]`，你传 `linked_lifesigns: [ls_C]`，结果是 `[ls_C]` 而不是 `[ls_A, ls_B, ls_C]`。想追加时，先在对话里确认用户意图（是"新增"还是"只保留这个"），再传完整的新列表。

### chapters 的定位合并

`patch.chapters` 字段的语义和其他字段不同：它是 `list[ChapterPatch]`，按 `chapter_index` 作为定位键逐章合并，而不是整体替换。

举例：Plan 现有 3 个 Chapter（index 1/2/3）。你想把 Chapter 2 的 `weekly_training_count` 从 3 改成 2：

```json
{
  "chapters": [
    { "chapter_index": 2, "weekly_training_count": 2 }
  ]
}
```

合并结果：Chapter 1 和 Chapter 3 原样保留，Chapter 2 只有 `weekly_training_count` 变化，其他字段保留原值。

`ChapterPatch` 的 `chapter_index` 是必填定位键；其余字段都可选，传了就覆盖该字段。

**不允许**在 `patch.chapters` 里引入新的 `chapter_index`（指向一个不存在的 chapter）——这会被拒绝。想**新增 chapter** 时，传完整的 `chapters` 数组（包含所有已有 chapter 的全部字段 + 新 chapter），但这相当于整体重写 chapters，用起来繁重。新增 chapter 的更常见做法：和用户对话确认后重构当前 Plan，或者在下一个 Plan 开启时纳入新结构。

## 结构性 vs 状态性

系统根据 patch 里出现的字段判断是否归档新版本：

**结构性字段**（任一出现即归档，`version++`）：
- `target` / `chapters` / `linked_lifesigns` / `linked_markers` / `status`

**状态性字段**（不归档，`version` 不变）：
- `target_summary` / `overall_narrative` / `planned_end_at` / `change_summary` / `revised_at`

注意 `change_summary` 单独存在会被拒——它必须伴随实质字段变化一起提交。

状态性修订直接改 `/user/plan/current.json`。结构性修订先写 `/user/plan/archive/{plan_id}_v{new}.json`，再更新 `/user/plan/current.json`（archive-first 半事务）。归档失败会自愈（下次 tool 调用发现 current 落后 archive，自动重写 current）——这是底层机制，你不需要管。

## 何时开启下一段新方案

两种情况：

- **旧 Plan 完成了，开启新 Plan**：走显式 successor flow，由 `create_successor_plan(document, previous_plan_id, user_confirmed, confirmation_text)` 创建新 Plan，并在新 Plan 上写入 `supersedes_plan_id`。
- **旧 Plan 没完成但方向变了**：如果这是跨 Plan 切换，仍然走 successor flow；如果只是当前 Plan 内重排章节、目标或 linked references，则仍是 `revise_plan`。

不要用 `supersedes_plan_id` 来做"这个 Plan 的第二个版本"——那是 `revise_plan` 的 `version++`。`supersedes_plan_id` 代表一个 Plan 生命周期结束、另一个 Plan 的开始。

## 几种常见修订的话术与 patch 对照

下面每一种都有"对话中你怎么说"和"随后的 patch 长什么样"。目的是让你的协商和提交对齐——用户听到的变化应该和 patch 里的变化是一回事。

### 修订 1：换掉一个 Process Goal

*对话中*：

> "这周你说早餐蛋白目标做得不错，但你自己觉得'每周三次训练'上周两次都没做到，而且这种状态已经持续三周了——是训练强度不对，还是时间根本排不进去？"
>
> *（用户说时间排不进去）*
>
> "那我们把这一章的训练目标降到每周两次，但把训练质量稍微提一提——不是次数问题，是每次是不是真的到了强度。你觉得怎么样？"

*患者确认后，patch*：

```json
{
  "chapters": [
    {
      "chapter_index": 2,
      "process_goals": [
        { "name": "早餐蛋白 25 克以上", "weekly_target_days": 5, "how_to_measure": "...", "examples": [...] },
        { "name": "每周两次高强度训练", "weekly_target_days": 2, "how_to_measure": "每次训练达到自觉 RPE 7 以上", "examples": [...] }
      ],
      "weekly_training_count": 2
    }
  ],
  "change_summary": "将 Chapter 2 训练目标从每周三次降为每周两次，强调单次强度"
}
```

这是结构性修订（`chapters` 字段出现）。`version++`。

注意 `process_goals` 是整体替换该 chapter 的 goals 列表——所以你必须传完整的 goals 列表（包括没改的"早餐蛋白 25 克以上"）。

### 修订 2：提前结束当前 Chapter

用户比预期更快达到了 milestone：

*对话*：

> "看起来你其实已经把这一章的事情做稳了——milestone 要求的两周 5/7 你在过去三周都做到了。是不是可以提前进入下一章？我们原本 end_date 是 4 月底，可以提前到这周日。"

*patch*：

```json
{
  "chapters": [
    { "chapter_index": 1, "end_date": "2026-04-19" },
    { "chapter_index": 2, "start_date": "2026-04-20" }
  ],
  "change_summary": "Chapter 1 提前结束（milestone 已稳定达成），Chapter 2 提前开始"
}
```

必须同时改 Chapter 1 的 `end_date` 和 Chapter 2 的 `start_date`（跨字段约束 #1：下一章必须从上一章结束后的次日开始）。只改一边 Pydantic 会拒。

### 修订 3：调整 Target

用户原本的目标不合理（过快或过慢），在对话中达成了新目标：

*对话*：

> "原本 8 周减 10 斤——每周 0.625 公斤——这个目标我们走了两周，但按你现在的生活节奏，我观察下来这个速度对你来说是有代价的（睡眠、情绪压力）。你考虑一下把时间放宽到 10 周？目标还是 10 斤，但每周 0.5 公斤——这个速度你应该不用刻意牺牲睡眠。"

*patch*：

```json
{
  "target": {
    "metric": "weight_kg",
    "baseline": 70.0,
    "goal_value": 65.0,
    "duration_weeks": 10,
    "rate_kg_per_week": 0.5
  },
  "planned_end_at": "2026-06-01T23:59:59+08:00",
  "change_summary": "将减脂周期从 8 周延长到 10 周，速率从 0.625 kg/周降到 0.5 kg/周"
}
```

结构性修订（`target` 字段出现）。Pydantic 会校验 `planned_end_at >= 最后一章 end_date`——如果最后一章的 end_date 超过了新的 `planned_end_at`，同一个 patch 里也要调整 chapters。

### 修订 4：更新 `overall_narrative` 或 `target_summary`

用户的表达方式变了，或他们用更精确的话重述了自己：

*对话*：

> "你刚才那句'我就是不想再像去年冬天那样'——比我们当时写的 narrative 更准确。要不要我把它写进 Plan？"

*patch*：

```json
{
  "overall_narrative": "我就是不想再像去年冬天那样，体重一个月涨了五斤自己都没察觉。想用两个月看看能不能把节奏重新拉住。",
  "change_summary": "更新 narrative 为用户本次对话中更精确的表达"
}
```

这是状态性修订（`version` 不变，就地改）。

### 修订 5：结束当前 Plan（不开新 Plan）

用户想暂停：

*对话*：

> "你说想先停一段时间——没问题。我把当前 Plan 设为 paused。它里面的东西都留着，哪天你想回来我们可以从这里继续，或者直接做一个新的。"

*patch*：

```json
{
  "status": "paused",
  "change_summary": "用户主动暂停"
}
```

结构性（`status` 字段出现）。

## 几个不该做的

- **不该一次 patch 里捆绑多个不相关的修订**。用户如果问"我想换训练节奏"，不要顺便把 Target 也改了——哪怕你觉得应该一起改。下一轮再做。一次 patch 一个意图，`change_summary` 写得清楚。
- **不该在 `change_summary` 里写给自己看的东西**（"根据用户上周 concerns 推断训练频率过高"）。`change_summary` 是 Plan 的版本注释，下次自己或别的 Coach 看到这条记录时需要读得懂——写"将训练频次从 3 降为 2"比"根据推断调整"更有用。
- **不该在用户没同意前提交结构性修订**。状态性修订（`set_goal_status` / `update_week_narrative`）可以在对话后自主写——那是你读取的状态。结构性修订应该和用户明确对齐过再提交。
