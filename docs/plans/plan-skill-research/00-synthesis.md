# 00 · Plan Skill 凝练架构文档

<!-- ABOUTME: Plan Skill 设计决策汇总 + 架构图 + 字段清单 + 实施路径 -->
<!-- ABOUTME: 基于 6 路调研产出(01-06) + 主线 15 轮决策对话收敛而成 -->

> **状态**:决策收敛,待 Dexter 审阅
> **产出日期**:2026-04-20
> **依据**:`01-academic.md` / `02-benchmark.md` / `03-knowledge-base.md` / `04-voliti-internal.md` / `05-skill-authoring.md` / `06-tech-arch.md` + 主线对话决策
> **下游**:本文通过后,进入实施路径第一步(Store 结构重组),再制定 Plan Skill 具体内容

---

## 一、14 项决策汇总

| # | 议题 | 决定 | 理由 / 出处 |
|---|------|------|----------|
| 1 | Plan 本质 | **完整嵌套对象** | 比"原子堆 + 视图"更符合用户心智,MVP 简单 |
| 2 | 存储格式 | **Markdown + 内嵌 JSON** | LLM 原生读写友好;叙事段与结构段解耦;git diff 友好;与 Voliti 现有 md 文档风格一致 |
| 3 | 写入校验 | **fail-closed 严格拒写** | Coach 写入后立刻反馈合法性,防幻觉;校验失败硬错误返回 Coach |
| 4 | 字段命名 | **语义化优先** | LLM 字段自解释,写错概率低;对读者优势 > token 劣势 |
| 5 | 失控应对机制 | **LifeSign 独立保留** | 不做 Plan 的用户也能用;与 Plan 解耦;Plan 通过引用关联 |
| 6 | `contingency` 字段 | **取消** | 失控应对完全交 LifeSign,Plan 只承担正向方案 |
| 7 | 外部事件(Marker) | **独立保留,Plan 引用** | 与 LifeSign 对称;支撑 Coach 时间感知(Briefing 每日注入);不绑 Plan |
| 8 | Goal / Chapter | **Plan 完全吸收** | 废弃 `/goal/` + `/chapter/` 独立路径;Plan.md 内"整体意图"章 = Goal,"阶段"各章 = Chapter |
| 9 | Pulse / 本周状态 | **嵌在 Plan.md 章节** | 结构一体化;版本化自然随 Plan 快照;Coach 用 `edit_file` 编辑 |
| 10 | 版本化 | **仅重大变动留版本** | target 改 / Chapter 重划 → archive;小编辑就地改 |
| 11 | 触发时机 | **Coach 综合判断** | 六维画像充分 + 情绪稳定 → Coach 主动提议;用户主动请求也可 |
| 12 | 共建 UX | **六维检查 → 稍补 → 起草 → 反馈**;**全屏页面复用 onboarding 视觉**,但不放入 onboarding 流 | 繁简度由 Coach 判断;解耦"方案制定"与"入门流程" |
| 13 | 写入接口 | **通用 `edit_file` + 路径 hook** | 不新增 tool 表面,middleware 识别 `/plan/*.md` 自动触发校验 |
| 14 | Pulse 数据来源 | **嵌入 Plan.md,Coach 写**(Computing 层兜底派生未采纳) | 见决策 9,简化为 Coach 唯一写者 |

---

## 二、四层骨架(数据分解)

```
╔═══════════════════════════════════════════════════════════════╗
║  ①  整体目标  ·  Plan 顶部叙事 + target JSON                  ║
║      "两个月减 10 斤"                                         ║
╚══════════════════════════╤════════════════════════════════════╝
                           │ 分解为序列
                           ▼
╔═══════════════════════════════════════════════════════════════╗
║  ②  阶段(chapter)·  Plan.md 各 Chapter 章节                  ║
║                                                               ║
║   立起早餐 ──→ 训练成锚(当前)──→ 焊进日常                      ║
║   第 1-2 周    第 3-6 周          第 7-8 周                   ║
║                                                               ║
║   每章包含:                                                  ║
║    · milestone                    定性目标                    ║
║    · process_goals[3]             本章三个可追踪目标           ║
║    · daily_rhythm                 统一规范(用餐/训练/作息)     ║
║    · daily_calorie_range          热量区间                    ║
║    · daily_protein_grams_range    蛋白区间                    ║
║    · weekly_training_count        周训练次数                  ║
║    · why_this_chapter             为什么(info tooltip 源)     ║
╚══════════════════════════╤════════════════════════════════════╝
                           │ 当前 Chapter 的 process_goals
                           │ 进入"本周状态"章节追踪
                           ▼
╔═══════════════════════════════════════════════════════════════╗
║  ③  本周状态(pulse)·  Plan.md 独立章节                        ║
║                                                               ║
║   week_index · updated_at · source                           ║
║   goals_status[] · highlights · concerns                     ║
║                                                               ║
║   Coach 每次对话后 edit_file 更新这一章;无对话则保持          ║
║   前端据 updated_at 显示 freshness                           ║
╚══════════════════════════▲════════════════════════════════════╝
                           │ Coach 从日级信息汇总
                           │
╔══════════════════════════╧════════════════════════════════════╗
║  ④  每日原始  ·  /day_summary/{YYYY-MM-DD}.md(独立)         ║
║                                                               ║
║   用户当日会话 + 关键事件 + 身心状态                         ║
║   不在 Plan.md 内                                             ║
╚═══════════════════════════════════════════════════════════════╝

  ┌─── 两个独立协作机制 ─────────────────────────────────────┐
  │                                                          │
  │  LifeSign(/lifesigns/*.md)· 失控 if-then 预案            │
  │    跨 Plan 长期有效;Plan 通过 linked_lifesigns 引用      │
  │                                                          │
  │  Marker(/markers/*.md)· 外部事件日程                     │
  │    跨 Plan 长期有效;Plan 通过 linked_markers 引用        │
  │    Briefing 每日注入 Coach 上下文(时间感知)             │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
```

---

## 三、系统架构(端到端数据管道)

```
┌───────────────────────────────────────────────────────────────────┐
│  ①  Coach 输出层                                                 │
│  ───────────────────────────────────────────────────────────────  │
│  Coach 通过通用 edit_file / write_file 写 Plan.md                │
│  (不引入专用 plan_edit tool)                                     │
└───────────────────────────────┬───────────────────────────────────┘
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  ②  路径 hook + 校验层                                           │
│  ───────────────────────────────────────────────────────────────  │
│  PlanWriteMiddleware                                              │
│   · 路径匹配: /plan/*.md                                          │
│   · 解析: parse_markdown_with_json_blocks()                       │
│   · 校验: PlanDocument.model_validate()(Pydantic)                │
│   · 失败: 拒写 + 结构化错误 fail-closed 返回 Coach               │
│   · 成功: 写入 Store                                              │
└───────────────────────────────┬───────────────────────────────────┘
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  ③  存储层                                                       │
│  ───────────────────────────────────────────────────────────────  │
│  /plan/current.md                      当前 Plan                  │
│  /plan/archive/{plan_id}_v{n}.md       重大变动后归档            │
│  /lifesigns/{id}.md                    失控 if-then 预案(独立)  │
│  /markers/{id}.md                      外部事件(独立)           │
│  /day_summary/{date}.md                每日原始(独立)           │
└───────────────────────────────┬───────────────────────────────────┘
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  ④  计算层 · derivations/plan_view.py                            │
│  ───────────────────────────────────────────────────────────────  │
│  纯函数 · compute_plan_view(PlanDocument, today, markers,        │
│                              lifesigns) → PlanViewRecord          │
│                                                                   │
│  只做日期驱动派生:                                               │
│   · active_chapter_index / days_left                             │
│   · map_state.flag_ratio / events brightness                     │
│   · linked_lifesigns / linked_markers 展开为面板信息             │
│                                                                   │
│  不做指标聚合 —— goals_status 由 Coach 写 Pulse 章节             │
└───────────────────────────────┬───────────────────────────────────┘
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  ⑤  前端 · Mirror / PlanPanel.tsx                                │
│  ───────────────────────────────────────────────────────────────  │
│  直接消费 PlanViewRecord,零计算,零业务逻辑                      │
└───────────────────────────────────────────────────────────────────┘
```

---

## 四、Plan.md 完整结构示例

> 使用 mock 用户"两个月减 10 斤"场景,当前第 27 天、第 4 周、第 2 阶段"训练成锚"。

````markdown
---
plan_id: plan_2026_02_21_weight_loss
status: active
version: 3
target_summary: 两个月减 10 斤
started_at: 2026-02-21
planned_end_at: 2026-04-17
created_at: 2026-02-21T09:15:00+08:00
revised_at: 2026-04-20T07:32:00+08:00
---

# 两个月减 10 斤

## 整体意图

为什么要做这件事(Coach 根据六维画像与用户共建的叙事段):
两个月前体重回到一个我自己都不认识的数字,我想用两个月看看能不能把它
掰回来,不是因为数字,是因为我没有背叛自己。

```json
{
  "metric": "weight_kg",
  "baseline": 70.0,
  "goal_value": 65.0,
  "duration_weeks": 8,
  "rate_kg_per_week": 0.625
}
```

---

## 阶段一 · 立起早餐

**时间**:第 1 – 2 周(2026-02-21 → 2026-03-06)
**里程碑**:早餐蛋白达标 5/7 持续两周

**为什么这个阶段**:你过去早餐习惯最不稳定,建立这个锚点比追求减重
速度更重要。前两周不追求体重变化,只追求早餐节奏立住。

```json
{
  "chapter_index": 1,
  "name": "立起早餐",
  "start_date": "2026-02-21",
  "end_date": "2026-03-06",
  "milestone": "早餐蛋白达标 5/7 持续两周",
  "process_goals": [
    {
      "name": "早餐蛋白 25 克以上",
      "weekly_target_days": 5,
      "weekly_total_days": 7,
      "how_to_measure": "Coach 每日对话后评估,综合蛋白种类与份量",
      "examples": [
        "一杯牛奶 + 一个鸡蛋 + 一片火腿",
        "希腊酸奶 + 一把坚果",
        "两个鸡蛋 + 一片全麦吐司"
      ]
    }
  ],
  "daily_rhythm": {
    "meals":    { "value": "三餐 · 蛋白分散", "tooltip": "早中晚各 25 克左右,分散比单餐集中更稳血糖" },
    "training": { "value": "每周两次",       "tooltip": "适应期量小,优先让身体接受训练节奏" },
    "sleep":    { "value": "十一点半",       "tooltip": "上床时间,目标入睡 12 点前" }
  },
  "daily_calorie_range": [1500, 1800],
  "daily_protein_grams_range": [90, 110],
  "weekly_training_count": 2
}
```

---

## 阶段二 · 训练成锚 · 当前

**时间**:第 3 – 6 周(2026-03-07 → 2026-04-03)
**里程碑**:再减 3 公斤,训练变成日常

**为什么这个阶段**:早餐已经立住了,这四周的真正任务不是减重本身,
而是让每周三次训练从"心情"变成"不用挣扎的惯性"。-3kg 是附带结果。

```json
{
  "chapter_index": 2,
  "name": "训练成锚",
  "start_date": "2026-03-07",
  "end_date": "2026-04-03",
  "milestone": "再减 3 公斤,训练变成日常",
  "process_goals": [
    {
      "name": "早餐蛋白 25 克以上",
      "weekly_target_days": 5,
      "weekly_total_days": 7,
      "how_to_measure": "沿用阶段一",
      "examples": ["延续上阶段"]
    },
    {
      "name": "每周三次训练",
      "weekly_target_days": 3,
      "weekly_total_days": 3,
      "how_to_measure": "训练日可弹性,不拘固定哪天;若体力差可降为 20 分钟快走 + 核心,仍计一次",
      "examples": ["周一 / 三 / 五 力量训练", "出差时用自重训练"]
    },
    {
      "name": "晚上十一点半前上床",
      "weekly_target_days": 5,
      "weekly_total_days": 7,
      "how_to_measure": "上床时间,非入睡时间;连续 2 天晚睡则次日训练降档",
      "examples": []
    }
  ],
  "daily_rhythm": {
    "meals":    { "value": "三餐 · 蛋白分散", "tooltip": "沿用" },
    "training": { "value": "每周三次",        "tooltip": "力量优先,每次 30-45 分钟" },
    "sleep":    { "value": "十一点半",        "tooltip": "连续 2 天晚睡 → 次日训练降档" }
  },
  "daily_calorie_range": [1400, 1700],
  "daily_protein_grams_range": [100, 120],
  "weekly_training_count": 3
}
```

---

## 阶段三 · 焊进日常

**时间**:第 7 – 8 周(2026-04-04 → 2026-04-17)
**里程碑**:前两章建立的节奏,经历差旅 / 生日 / 节日的最后压力测试还守得住

**为什么这个阶段**:减下来是一回事,能保住是另一回事。这两周主动测试
节奏的抗压能力——如果压力下节奏还在,这个模式就算焊住了。

```json
{
  "chapter_index": 3,
  "name": "焊进日常",
  "start_date": "2026-04-04",
  "end_date": "2026-04-17",
  "milestone": "压力测试下节奏守住即毕业",
  "process_goals": [
    {
      "name": "早餐蛋白 25 克以上",
      "weekly_target_days": 5,
      "weekly_total_days": 7
    },
    {
      "name": "每周两次训练(保底)",
      "weekly_target_days": 2,
      "weekly_total_days": 3
    },
    {
      "name": "晚上十一点半前上床",
      "weekly_target_days": 4,
      "weekly_total_days": 7
    }
  ],
  "daily_rhythm": {
    "meals":    { "value": "三餐 · 蛋白分散", "tooltip": "沿用" },
    "training": { "value": "每周两到三次",   "tooltip": "压力下保底即可" },
    "sleep":    { "value": "十一点半",        "tooltip": "沿用" }
  },
  "daily_calorie_range": [1500, 1800],
  "daily_protein_grams_range": [90, 110],
  "weekly_training_count": 2
}
```

---

## 已知风险(引用 /lifesigns/)

```json
{
  "linked_lifesigns": [
    {
      "id": "ls_latenight_craving",
      "name": "深夜食欲",
      "relevant_chapters": [1, 2, 3]
    },
    {
      "id": "ls_weekend_drift",
      "name": "周末漂移",
      "relevant_chapters": [2, 3]
    },
    {
      "id": "ls_emotional_eating",
      "name": "情绪进食",
      "relevant_chapters": [1, 2, 3]
    }
  ]
}
```

---

## 已知外部事件(引用 /markers/)

```json
{
  "linked_markers": [
    {
      "id": "mk_2026_03_01_trip",
      "name": "出差",
      "date": "2026-03-01",
      "impacts_chapter": 2,
      "note": "三天出差,保底即可,不追求新进展"
    },
    {
      "id": "mk_2026_03_15_birthday",
      "name": "生日",
      "date": "2026-03-15",
      "impacts_chapter": 2
    },
    {
      "id": "mk_2026_04_02_holiday",
      "name": "节日",
      "date": "2026-04-02",
      "impacts_chapter": 3
    }
  ]
}
```

---

## 本周状态

**本周 index**:4 (第 3 阶段第 2 周)
**更新于**:2026-04-20 今晨
**来源**:coach_inferred

**亮点**:周二训练比计划多做了 15 分钟,状态回暖明显
**担心**:周六深夜又吃了一顿,是本阶段第二次触发 LS-003

```json
{
  "week_index": 4,
  "active_chapter_index": 2,
  "updated_at": "2026-04-20T07:32:00+08:00",
  "source": "coach_inferred",
  "goals_status": [
    { "goal_name": "早餐蛋白 25 克以上",    "days_met": 3, "days_expected": 5 },
    { "goal_name": "每周三次训练",          "days_met": 2, "days_expected": 3 },
    { "goal_name": "晚上十一点半前上床",    "days_met": 4, "days_expected": 7 }
  ],
  "highlights": "周二训练比计划多做了 15 分钟,状态回暖明显",
  "concerns": "周六深夜又吃了一顿,是本阶段第二次触发 LS-003"
}
```
````

---

## 五、Pydantic 模型(校验层)骨架

文件位置:`backend/src/voliti/contracts/plan.py`(新增,与现有 `__init__.py` 并列)。

```python
# ABOUTME: Plan Skill 校验层 · PlanDocument 与嵌套模型
# ABOUTME: 与 /plan/*.md 中 YAML frontmatter + 内嵌 JSON code blocks 一一对应

from pydantic import BaseModel, Field
from typing import Literal


class ProcessGoalRecord(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    weekly_target_days: int = Field(ge=1, le=7)
    weekly_total_days: int = Field(ge=1, le=7, default=7)
    how_to_measure: str = Field(min_length=4, max_length=240)
    examples: list[str] = Field(default_factory=list, max_length=6)


class RhythmItem(BaseModel):
    value: str = Field(min_length=1, max_length=40)
    tooltip: str = Field(min_length=4, max_length=200)


class DailyRhythm(BaseModel):
    meals: RhythmItem
    training: RhythmItem
    sleep: RhythmItem


class ChapterRecord(BaseModel):
    chapter_index: int = Field(ge=1, le=6)
    name: str = Field(min_length=2, max_length=20)
    start_date: str  # ISO-8601
    end_date: str
    milestone: str = Field(min_length=4, max_length=200)
    process_goals: list[ProcessGoalRecord] = Field(min_length=1, max_length=4)
    daily_rhythm: DailyRhythm
    daily_calorie_range: tuple[int, int]
    daily_protein_grams_range: tuple[int, int]
    weekly_training_count: int = Field(ge=0, le=7)


class TargetRecord(BaseModel):
    metric: str
    baseline: float
    goal_value: float
    duration_weeks: int = Field(ge=2, le=26)
    rate_kg_per_week: float = Field(ge=0.1, le=1.5)  # 安全阈值


class LinkedLifeSign(BaseModel):
    id: str
    name: str
    relevant_chapters: list[int]


class LinkedMarker(BaseModel):
    id: str
    name: str
    date: str
    impacts_chapter: int
    note: str | None = None


class GoalStatus(BaseModel):
    goal_name: str
    days_met: int = Field(ge=0, le=7)
    days_expected: int = Field(ge=1, le=7)


class PulseRecord(BaseModel):
    week_index: int = Field(ge=1)
    active_chapter_index: int = Field(ge=1, le=6)
    updated_at: str
    source: Literal["coach_inferred", "user_reported"]
    goals_status: list[GoalStatus]
    highlights: str | None = None
    concerns: str | None = None


class PlanDocument(BaseModel):
    # 来自 YAML frontmatter
    plan_id: str
    status: Literal["active", "completed", "paused", "archived"]
    version: int = Field(ge=1)
    target_summary: str
    started_at: str
    planned_end_at: str
    created_at: str
    revised_at: str

    # 来自 markdown body 内的 JSON blocks
    target: TargetRecord
    chapters: list[ChapterRecord] = Field(min_length=2, max_length=4)
    linked_lifesigns: list[LinkedLifeSign] = Field(default_factory=list)
    linked_markers: list[LinkedMarker] = Field(default_factory=list)
    pulse: PulseRecord | None = None  # 新 Plan 首次无 pulse
```

---

## 六、计算层派生(`derivations/plan_view.py`)

```python
# ABOUTME: Plan Skill 计算层 · PlanDocument → PlanViewRecord 纯函数
# ABOUTME: 仅做日期驱动派生,不做指标聚合(指标由 Coach 写 Pulse 承担)

def compute_plan_view(
    plan: PlanDocument,
    today: date,
    markers: dict[str, MarkerRecord],    # 从 /markers/ 展开
    lifesigns: dict[str, LifeSignRecord],  # 从 /lifesigns/ 展开
    locale: str = "zh-CN",
) -> PlanViewRecord:
    ...
```

**关键派生字段**:

| 字段 | 公式 |
|------|------|
| `day_progress` | `(today - plan.started_at, plan.planned_end_at - plan.started_at)` |
| `active_chapter_index` | `find i where chapters[i].start ≤ today ≤ chapters[i].end` |
| `days_left` | `chapters[active].end_date - today` |
| `map_state.flag_ratio` | `(today - plan.start) / (plan.end - plan.start)` |
| `map_state.events[i].brightness` | `clamp(1 - |event.date - today| / 30, 0.25, 1.0)` |
| `week_view[]` | 直接读 `pulse.goals_status`(不重新聚合) |
| `week_freshness.level` | `"fresh" if now-pulse.updated_at < 1d else "stale" if < 3d else "very_stale"` |
| `day_template[]` | `chapters[active].daily_rhythm` 格式化为三列 |
| `watch_list[]` | merge(`linked_lifesigns` + `linked_markers` 本周窗口) |

---

## 七、写入 hook 技术点

**PlanWriteMiddleware**(新增):

```python
# ABOUTME: 拦截对 /plan/*.md 的写入,解析 + 校验 + fail-closed
# ABOUTME: 符合决策 3(严格拒写)+ 决策 13(通用 edit_file + hook)

class PlanWriteMiddleware:
    def before_edit_file(self, path: str, new_content: str) -> None:
        if not path.startswith("/plan/") or not path.endswith(".md"):
            return
        try:
            doc = parse_plan_markdown(new_content)  # YAML + JSON blocks → dict
            PlanDocument.model_validate(doc)        # Pydantic 校验
        except (ParseError, ValidationError) as e:
            raise PlanValidationError(
                message="Plan 校验未通过,未写入。" + format_error_for_coach(e),
                details=e,
            )
```

**错误消息设计原则**(给 Coach 读的):
- 明确指出哪个字段不合法
- 给出期望格式示例
- 保留原文错误信息(行号 / 字段名)
- 避免"重新生成整个 Plan"建议——Coach 应能局部修复

示例错误消息:
```
Plan 校验未通过,未写入。
问题:阶段二 chapter_index = 2 的 process_goals 少于最少要求。
字段:chapters[1].process_goals
期望:1-4 条 ProcessGoalRecord
实际:0 条
建议:补充至少 1 条 process_goals 后重新调用 edit_file
```

---

## 八、独立机制 · LifeSign 与 Marker 的协作

### LifeSign(`/lifesigns/{id}.md`)
- 文件格式:同样 Markdown + 内嵌 JSON(本文档不展开结构;属"LifeSign 本身的重构",另外工作)
- Plan 通过 `linked_lifesigns[].id` 引用
- Computing 层展开:`linked_lifesigns` → 完整 LifeSign 对象 → `plan_view.watch_list` 预案条目
- 跨 Plan 有效:Plan 归档 / 新建 Plan,LifeSign 不受影响

### Marker(`/markers/{id}.md`)
- 文件格式:Markdown + 内嵌 JSON(单事件)
- Plan 通过 `linked_markers[].id` 引用
- Briefing 每日注入 Coach 上下文:"接下来 7 天有什么事件"——Coach 时间感知来源
- Computing 层展开:`linked_markers` → 完整 Marker 对象 → `plan_view.map_state.events[]` 与 `plan_view.watch_list` 事件条目
- 跨 Plan 有效:同 LifeSign

---

## 九、待实施前的小议题(不阻塞架构确认)

这些议题在写代码前再决策即可,本文档不锁死:

1. **`/goal/current.md` + `/chapter/current.md` 废弃的迁移路径**:是否写一次性迁移脚本?或者新用户启用 Plan / 老用户保持原路径?
2. **现有 `dashboardConfig` 与 Plan 的关系**:是 Plan 内化为字段 / 仍独立?
3. **Briefing 中 Plan 片段的展示格式**:纯文字摘要 / 结构化(active_chapter + goals_status 本周)?
4. **版本 diff 呈现**:archive 中 v1 vs v2 如何给用户/Coach 看?
5. **LifeSign 本身的重构**:本文不涉,作为独立工作项
6. **首次生成 Plan 时的 A2UI fan_out 具体组件**:等进入 Plan Skill 内容设计环节决定

---

## 十、实施路径(建议)

**Phase A · 数据结构基础**(当前讨论后首先实施)

1. 新增 `backend/src/voliti/contracts/plan.py` 写 Pydantic 模型
2. 新增 `backend/src/voliti/plan_parser.py` 写 Markdown 解析器
3. 新增 `backend/src/voliti/middleware/plan_write.py` 写入 hook
4. 新增 `backend/src/voliti/derivations/plan_view.py` 计算层
5. 新增 fixture `tests/contracts/fixtures/store/plan_current.value.md`
6. 写 unit tests:解析 + 校验正负向 + 计算派生

**Phase B · Coach 协作**(数据结构稳定后)

1. 编写 `backend/skills/coach/plan/SKILL.md`(Plan Skill 正文)
2. references:`plan-structure.md`(md+json 规范) / `phase-templates.md`(模板) / `numeric-guidelines.md`(数值依据,映射 `01-academic.md`) / `edit-protocol.md`(协商话术)
3. 触发逻辑:六维画像检查 + 时机判断写入 SKILL.md
4. eval seeds 补充:Plan 生成 / Pulse 更新 / 失控后重生成三类场景

**Phase C · 前端呈现**(Coach 可用后)

1. `frontend-web/app/mirror/PlanPanel.tsx` 消费 PlanViewRecord
2. Plan 生成全屏 overlay(复用 onboarding 视觉)
3. info icon tooltip 系统落地(已在 mockup 验证)

**Phase D · 老概念废弃**(灰度)

1. 新用户启用 Plan 路径
2. 老用户 Goal/Chapter 保持可读兼容一段时间
3. 适当时机做一次迁移,废弃 `/goal/` + `/chapter/`

---

## 变更记录

| 日期 | 内容 |
|------|------|
| 2026-04-20 | 初始创建:14 项决策汇总 + 四层骨架 + 系统架构 + Plan.md 示例 + 契约模型骨架 + 实施路径 |
