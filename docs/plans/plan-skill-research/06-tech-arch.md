# Plan Skill 技术实现架构调研

本文档为 Plan Skill 落地提供技术骨架级建议，覆盖计算层、编辑工具、A2UI 共建模式、传输缓存、测试范式与 middleware 协作六个维度。所有建议以现有代码结构为基点，避免新增冗余抽象；字段名与函数名保持英文以与 `backend/src/voliti/` 既有风格一致。

关键参考：

- 契约校验层：`backend/src/voliti/contracts/__init__.py`、`backend/src/voliti/store_contract.py`
- A2UI 协议：`backend/src/voliti/a2ui.py`
- Coach 工厂：`backend/src/voliti/agent.py`
- 计算类模块现样板：`backend/src/voliti/briefing.py`
- 日终 Pipeline：`backend/src/voliti/pipeline/day_end.py`
- 前端聚合端点：`frontend-web/src/app/api/me/coach-context/route.ts`
- Mirror 契约：`frontend-web/src/lib/mirror-contract.ts`
- Skill 范式：`backend/skills/coach/future-self-dialogue/tool.py`、`backend/skills/coach/witness-card/tool.py`
- Store 契约测试：`backend/tests/test_store_contract.py`

---

## 一、Computing 层模块结构

### 1.1 目录组织

新增 `backend/src/voliti/derivations/` 子包，与 `contracts/`（校验）和 `briefing.py`（既有计算）并列。不引入聚合式 `compute/` 目录，避免将未来不确定的派生逻辑统一抽象。

```
backend/src/voliti/derivations/
├── __init__.py           # 对外仅导出顶层入口 compute_plan_view
├── plan_view.py          # 入口函数 + 组装逻辑
├── plan_clock.py         # 日期相关纯函数（days_left / phase_at / week_window）
└── plan_projection.py    # PlanRecord + 旁路数据 → PlanViewRecord 的字段投影
```

划分理由：

- `plan_clock.py` 是日期代数，不依赖任何 Pydantic 模型；最易单测，最可复用。
- `plan_projection.py` 是"契约模型 → 视图模型"的纯映射层；消费 `PlanRecord`、`day_summary`、`MarkersRecord`，产出 `PlanViewRecord`。
- `plan_view.py` 是协调者：从输入选择性调用上述两层，输出给调用方。不做 I/O。

### 1.2 入口函数签名

`plan_view.py` 的入口函数接收已校验的 Pydantic 记录，不直接接触 Store 或 LangGraph runtime：

```python
# ABOUTME: Plan 视图派生入口 — 纯函数，不做 I/O
# ABOUTME: 输入为已校验的契约模型与旁路数据，输出前端直接渲染的 PlanViewRecord

from datetime import date
from voliti.contracts import (
    PlanRecord,           # 新增：Plan Skill 契约模型
    PlanViewRecord,       # 新增：前端投影模型
    MarkersRecord,
)

def compute_plan_view(
    *,
    plan: PlanRecord,
    today: date,
    markers: MarkersRecord | None = None,
    day_summaries: dict[str, str] | None = None,  # date_str -> raw markdown
    lifesigns: list[dict] | None = None,
) -> PlanViewRecord:
    """根据当日上下文派生 Plan 面板视图。

    关键派生点：
    - current_phase_index：依据 today 与 phases 的日期窗口定位
    - days_left_in_phase / days_elapsed：phase_clock 算出
    - week_progress：从 plan.current_week.metrics 直接取，不再聚合 day_summary
    - risk_window：交叉 markers（未来 7 天）与 current_phase
    """
```

### 1.3 纯函数与 LangGraph context 的解耦

参考 `briefing.py` 的做法（L25 / L46 / L60 / L127 等系列 `compute_*` / `extract_*`）：

1. **纯函数优先**：`plan_clock.py` 与 `plan_projection.py` 内所有函数仅接收参数、返回值，不读 `get_config()`、不读 `store`。
2. **数据加载在外层**：Store 读取与 Pydantic 校验由调用方（API route、middleware、工具）完成，将已校验的记录传入 `compute_plan_view`。
3. **时间注入**：`today` 显式作为参数，与 `briefing.py` 的 `now: datetime | None = None` 模式一致，便于测试。

这样做的直接好处：单元测试不需要 mock `BaseStore`，只需构造 `PlanRecord` 实例；而与 `coach-context/route.ts` 的对接是"API route 完成 Store 读取 → 校验 → 调 Python 派生模块？"——由于前端是 TypeScript，此处需要做选择（见第四节）。

### 1.4 异常处理与 fallback

沿用现有项目"读取端 fail-closed、派生端 fail-graceful"的分工：

| 场景 | 处理策略 | 理由 |
|------|----------|------|
| `PlanRecord` 本身校验失败 | 由 `store_read_validated` 抛 `InvalidStoreValueError`，**不进入 compute** | 契约破损是 Coach 的责任，要显式暴露 |
| `today` 早于 `plan.start_date` | 返回 `PlanViewRecord(state="pending_start", ...)` | Plan 已创建但未到启动日，前端显示"将于 X 月 X 日开始" |
| `today` 晚于 `plan.target_date` | 返回 `PlanViewRecord(state="awaiting_review", ...)` | Plan 到期等待复盘 |
| `phases` 列表为空 | 返回 `PlanViewRecord(state="skeleton", phases=[], ...)` | 只有目标没有阶段：初始草案状态 |
| `current_week` 缺失 | 派生层不报错；`current_week` 视图字段返回 `None`，UI 显示占位 | Coach 尚未首次汇总本周状态属正常流程中态 |
| `markers` 为 `None` 或解析失败 | `risk_window=[]`，不影响主视图 | 参考 `extract_upcoming_markers` 的 try/except 模式 |

`PlanViewRecord` 应包含一个 `state: Literal["pending_start", "active", "awaiting_review", "skeleton"]` 字段，让前端不需要自行解释边界态。

---

## 二、编辑工具集

三类编辑操作在 LangGraph + DeepAgents 体系下应以 `@tool` 装饰器表达，而不是 middleware hook。middleware hook 适合"每次请求都要发生"的行为（prompt 注入、上下文加载），而编辑行为需要 LLM 主动触发且有校验反馈回路——与 `add_forward_marker`、`issue_witness_card` 同属"工具"层。

### 2.1 三类工具的技术形态

#### A. 细粒度字段编辑（`update_current_week` / `set_goal_status`）

复用 `add_forward_marker` 的"读 → 合并 → 校验写"三步模式（`backend/src/voliti/tools/marker.py` L27-84）：

```python
# backend/skills/coach/plan/tool_update_current_week.py（示意）
from typing import Annotated, Any
from langchain_core.tools import InjectedToolArg, tool
from langgraph.store.base import BaseStore

from voliti.contracts import PlanRecord
from voliti.store_contract import (
    PLAN_CURRENT_KEY,                # 新增常量
    resolve_user_namespace,
    store_read_validated,
    store_write_validated,
    unwrap_file_value,
)

@tool
def update_current_week(
    field: str,
    value: str,
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Update a single field inside plan.current_week.

    Allowed fields are declared in PlanRecord.current_week schema; unknown fields
    return a coach-actionable error message without writing Store.
    """
    namespace = resolve_user_namespace(config)
    item = store.get(namespace, PLAN_CURRENT_KEY)
    plan = store_read_validated(item.value if item else None, PlanRecord, PLAN_CURRENT_KEY)
    if plan is None:
        return "Plan 不存在，请先调用 generate_plan 建立初始草案。"

    current = plan.current_week.model_dump()
    current[field] = value  # Pydantic 下一步会校验
    new_plan = plan.model_copy(update={"current_week": current})

    ok, err = store_write_validated(
        store, namespace, PLAN_CURRENT_KEY,
        new_plan.model_dump(mode="json"),
        PlanRecord,
    )
    return "current_week 已更新" if ok else err
```

#### B. 阶段调整（`tweak_phase`）

结构同 A，但针对 `plan.phases[index]`。关键点：传入 `phase_index` 时先检查边界，越界直接返回中文错误（不写 Store）：

```python
if not 0 <= phase_index < len(plan.phases):
    return f"phase_index 越界：当前 plan 仅有 {len(plan.phases)} 个阶段。"
```

#### C. 整体重建（`generate_plan`）

与 `issue_witness_card`（`backend/skills/coach/witness-card/tool.py` L143）同类：输入结构化参数，工具内部做骨架生成（可以纯 Python，也可以借助轻量模型），最后写入 Store 并返回状态码。

```python
@tool(args_schema=GeneratePlanInput)
def generate_plan(
    target: str,
    horizon_days: int,
    phase_count: int,
    profile_snapshot_ref: str,  # 指向 /profile/context.md 的版本标识，而非整段传入
    *,
    store: Annotated[BaseStore, InjectedToolArg],
    config: Annotated[dict[str, Any], InjectedToolArg],
) -> str:
    """Create or replace the user's Plan with a fresh skeleton."""
```

`GeneratePlanInput` 用 Pydantic `BaseModel` 做入参校验，与 `WitnessCardInput` 的 `args_schema=WitnessCardInput` 做法对齐。

### 2.2 Store 写入的原子性

LangGraph Store 单个 key 的 `put` 是原子的，但"读 → 合并 → 写"序列不是。MVP 阶段的可行路径：

1. **单 key 写入**：Plan 落在 `/user/plan/current.json` 单个 JSON 文件内。所有三类工具都是"整文件重写"，天然避免字段级并发冲突。
2. **避免跨会话并发**：Coach 在一个会话内是顺序调用工具的，冲突窗口只存在于"Coach 写入 ↔ 日终 Pipeline 写入"之间；按 `day_end.py` 的锁窗口设计（日终只在用户 thread 封存后才写）基本不会同时发生。
3. **未来扩展**：如果需要真正的乐观并发，可以在 `PlanRecord` 加 `version: int` 字段，写入时 `Optimistic If-Match`。当前不建议引入。

### 2.3 确保所有工具经过校验层

这是 Store 契约层的核心价值主张。具体做法：

- **禁止裸 `store.put`**：Plan 相关所有工具一律走 `store_write_validated`（`store_contract.py` L118）。
- **禁止裸 `json.loads`**：读取一律走 `store_read_validated`（`store_contract.py` L142）。
- **在 `agent.py` 中注册**：Plan 工具也通过 `_load_skill_tools()`（`agent.py` L35）自动发现，只要在 `backend/skills/coach/plan/` 下放 `tool.py` 并导出 `TOOL = ...` 即可。
- **测试守门**：在 `backend/tests/test_plan_tools.py` 加一条测试扫描所有 plan 工具源码，断言不出现 `store.put(` 或 `json.loads(` 的裸调用（参考 `test_store_contract.py` 既有的测试风格，扫描源文件）。

---

## 三、A2UI 共建模式比较

Plan 生成是 Coach 与用户的长链路共建。结合既有 A2UI 组件（`a2ui.py` 定义的 8 种原语：text / image / protocol_prompt / slider / text_input / number_input / select / multi_select）与 onboarding Path A 的 wizard 范式，下面给出 4 个方案的结构化对比。

### 3.1 方案 A：多步 Wizard（onboarding Path A 复刻）

**结构**：Coach 连续发起 6-8 次 `fan_out`，每次一个目标维度（目标 → 阶段 → process goal → 首周 → LifeSign → 确认）。

**引用基准**：`backend/prompts/onboarding.j2` L83-L92（Path A 流程）。

**优点**：
- 每步可见、可拒绝、可回退，契合 MLP 的"用户掌控"价值。
- 复用度最高：onboarding 已完整实现同类范式，代码几乎零额外。
- 中断恢复容易：每步都是独立 interrupt，状态在 Store 上。

**缺点**：
- 6-8 轮交互偏长；老用户（已完成 onboarding）重复感强。
- Coach 需要维护"我正在 Plan 生成第 N 步"的心智模型（可通过 prompt 模板中的明确节点列表解决）。

### 3.2 方案 B：自由对话挖掘后隐式落盘

**结构**：Coach 与用户自然对话 10-15 轮，期间不显式出 UI；Coach 在合适时机调用 `generate_plan` 工具，将对话中挖掘的结构一次写入。

**优点**：
- 最贴近"教练感"，降低问卷感。
- 不依赖 A2UI，技术路径最短。

**缺点**：
- 用户没有直观的"计划成型中"反馈，容易在第 7-8 轮放弃。
- 落盘质量完全依赖 LLM 对自由对话的结构化能力，风险高。
- 与"让用户感到被看见"价值冲突不大，但与"差异化"价值（行为教练的透明度）冲突。

### 3.3 方案 C：完整草案 + 整体批改

**结构**：Coach 挖掘 3-4 轮后，调用 `generate_plan` 生成完整草案，以单个 `layout="full"` A2UI 面板（含多个 `text` 展示 phase + `multi_select` 选择要调整的部分 + `text_input` 收集修改意见）呈现，用户可整体确认或批注。

**引用基准**：`backend/skills/coach/future-self-dialogue/tool.py` 的 `layout="full"` 全屏模式（L15），以及 `a2ui.py` 的 `layout: Literal["half", "three-quarter", "full"]`（L137）。

**优点**：
- 一次性呈现完整计划，用户建立整体感。
- 修改意图显式，Coach 收到的信号清晰。

**缺点**：
- 单个面板信息密度高；8 原语的表现力受限，复杂层级结构（phases × process_goals）在 A2UI 上呈现困难——可能需要退化成大段 `text` 组件，用户编辑颗粒粗。
- 一次交互承载过多决策，用户可能草率点"确认"。

### 3.4 方案 D：混合（推荐）

**结构**：
1. **Phase 1 — 摸底对话（1-2 轮，自由对话）**：Coach 识别用户是"有具体方向"还是"还在摸索"。
2. **Phase 2 — 结构化提议（1 次 wizard 式 fan_out）**：一次性呈现 `text`（草案目标 + 建议阶段数）+ `select`（确认粒度：方向对/要换/微调）+ `text_input`（如选"微调"则填修改点）。此处使用 `layout="three-quarter"`。
3. **Phase 3 — 阶段级细化（仅"要换"或"微调"路径，1-2 次 fan_out）**：按用户反馈增量调整，每次只改一个阶段或一个 process_goal。
4. **Phase 4 — 最终确认（1 次 fan_out）**：`protocol_prompt`（观察链："我为你规划了 X 周、Y 个阶段，主线是 Z"）+ `select`（接受 / 再改一次 / 全盘重来）。

**技术实现**：
- 不需要新的 A2UI 原语。
- Plan skill 目录下放 `tool_propose_plan_draft`、`tool_confirm_plan` 两个专用工具（仿照 `future-self-dialogue/tool.py` 硬编码 metadata 的模式），Coach 在对应阶段调用。
- `metadata` 字段写入 `surface="coaching"`、可加自定义观测键 `plan_stage=draft|refine|confirm`（当前 `metadata: dict[str, str]` 弹性已支持，见 `a2ui.py` L138-L155）。

**优点**：
- 对老用户（Path B/C 进入）最短 3 次交互即可完成。
- 对新用户可退化到接近方案 A 的体验，但更"教练化"而非"问卷化"。
- 每步仍可中断、可 reject，继承现有 A2UI response 契约。

**缺点**：
- prompt 规则比方案 A 复杂，需要在 Plan skill 的 `SKILL.md` 中清晰定义阶段切换条件。

### 3.5 推荐

**采用方案 D。核心判断：Plan 不是 onboarding 的延伸，是 onboarding 之后的首个合作产物。**

- Plan 生成发生在用户已完成 onboarding、Coach 已有 profile/goal/chapter 的前提下。若此时再走 6-8 轮 wizard（方案 A），用户会感觉"刚做完一份问卷，又要做一份"——这与产品定位的"AI 减脂私密行为教练"冲突。
- 方案 B 的结构化风险过高，不值得。
- 方案 C 的全屏信息密度是 A2UI 8 原语难以承载的。
- 方案 D 在最短路径上尊重用户已输入的信息（Phase 1 + Phase 2），在复杂路径上仍保有控制权（Phase 3 细化）。

---

## 四、PlanViewRecord 传输与缓存策略

### 4.1 核心问题：计算层放在哪里

Computing 层有两种放置选择：

| 选择 | 描述 | 适用性 |
|------|------|--------|
| **后端 Python** | `derivations/plan_view.py` 作为独立模块；由 `coach-context/route.ts` 从 LangGraph SDK 取 PlanRecord 后，要么在后端再暴露一个派生端点，要么把派生逻辑镜像到前端 TypeScript | 与现有 `briefing.py` 风格一致 |
| **前端 TypeScript** | 仅在 `mirror-contract.ts` 中实现投影，类似 `parseCopingPlans` 与 `buildMirrorDataFromStoreValues` | 与现有 Mirror 数据流一致 |

**建议：后端 Python + 前端复刻派生（只读）**。

- Python 侧是**派生真相**：所有 eval、测试、日终 Pipeline（如果未来需要快照）共享同一套纯函数。
- 前端侧维持当前"读 Store → 在 `mirror-contract.ts` 投影"的轻量模式，但把投影逻辑从分散字段拼装升级为 "解析 PlanRecord → 派生 PlanViewRecord"；派生函数与 Python 保持 1:1 字段对应（就像 `mirror-contract.ts` L4-79 的 interface 与 Pydantic 模型保持镜像一样）。
- 为防止双端漂移：两端共用 `tests/contracts/fixtures/` 下的 fixture（参考 `tests/contracts/fixtures/store/goal_current.value.json`），给 Python 和 TypeScript 各一套"相同输入 → 相同输出"的对照测试。

### 4.2 触发时机

沿用现在 `coach-context/route.ts` 的 `Cache-Control: no-store` + 前端按事件刷新的模式，不引入新的 SSE 事件类型：

1. **首次加载**：进入应用时 `fetchCoachContext` 一并取回 `planView`（新增字段）。
2. **Coach 工具调用完成后**：A2UI resume 返回后，前端 `store-sync.ts` 再调一次 `/api/me/coach-context`。既有 `EventStream`（`MirrorPanel.tsx` L49 / L328）在工具调用结束时已触发 Mirror 刷新，Plan 视图可挂在同一刷新周期内。
3. **每日刷新（日期推进）**：前端在 `Date.now()` 跨日时触发一次重新派生。由于派生是纯函数，不需要额外的 SSE；在 Mirror 面板挂一个 `setInterval(_, 60*1000)` 检查 `new Date().toDateString()` 是否变化即可（低频，成本可忽略）。
4. **中长期**：如果未来需要主动推送（例如 Coach 静默修改 Plan 后希望前端立即反映），复用 LangGraph 的 thread update 事件流；当前 MVP 不做。

### 4.3 缓存层级

| 层级 | 存储 | 生命周期 |
|------|------|----------|
| **权威层** | `/user/plan/current.json`（Store） | 直到下次工具写入 |
| **派生层** | `compute_plan_view()` 纯函数输出 | 每次请求重算（~ 毫秒级，不需要缓存） |
| **前端层** | React state (`useState` in MirrorPanel) | 组件生命周期 |

不建议做派生结果的持久化缓存。纯函数的成本是日期比较 + 数组过滤，远低于 Store 一次读操作；缓存反而引入失效策略问题。

---

## 五、测试范式

### 5.1 纯函数 Computing 层（pytest）

参考 `backend/tests/test_briefing.py` L23-L67 的模式：每个 `compute_*` / `extract_*` 函数对应一个 `TestX` 类，内部用 `datetime(...)` 构造 `now` 注入。

```python
# backend/tests/test_plan_view.py
class TestPhaseAt:
    def test_returns_none_before_start(self) -> None:
        plan = _make_plan(start="2026-05-01", phases=[...])
        today = date(2026, 4, 20)
        assert phase_at(plan, today) is None

    def test_returns_current_phase_index(self) -> None:
        ...

class TestComputePlanView:
    def test_pending_start_state(self) -> None:
        view = compute_plan_view(plan=_make_plan(start="2099-01-01"), today=date.today())
        assert view.state == "pending_start"
```

**Fixture 组织**：

- **契约模型 fixture**：扩展 `tests/contracts/fixtures/store/`，新增 `plan_current.value.json`（骨架）、`plan_mid_phase.value.json`（中期态）、`plan_awaiting_review.value.json`（尾期态）。参考 `goal_current.value.json` 的格式——都是 `make_file_value` 封装过的 `{"version": "1", "content": [...]}` 结构。
- **视图快照 fixture**：新增 `tests/contracts/fixtures/plan_view/` 放 `{input.json, today.txt, expected_view.json}` 三元组，供 Python + TypeScript 共享。
- **fixture 同步参数化**：在 `test_store_contract.py`（L41-L46 的 `_load_fixture` 工具）已有 fixture-driven 测试模式；Plan 侧直接复用。

### 5.2 编辑工具 integration test

参考 `backend/tests/test_fan_out.py`（`@patch("voliti.tools.fan_out.interrupt")`）和 `test_day_end_pipeline.py`（`AsyncMock`）的风格：

```python
# backend/tests/test_plan_tools.py
class TestUpdateCurrentWeek:
    def test_writes_validated_plan(self) -> None:
        store = InMemoryStore()
        namespace = ("voliti", "user_test_001")
        store.put(namespace, PLAN_CURRENT_KEY, make_file_value(_canonical_plan_json()))

        result = update_current_week.invoke(
            {"field": "meal_log_days", "value": "5"},
            config={"configurable": {"user_id": "user_test_001"}},
            store=store,
        )
        assert "current_week 已更新" in result

        item = store.get(namespace, PLAN_CURRENT_KEY)
        plan = store_read_validated(item.value, PlanRecord, PLAN_CURRENT_KEY)
        assert plan.current_week.meal_log_days == 5

    def test_rejects_unknown_field(self) -> None:
        ...  # 返回中文错误，不写 Store
```

关键覆盖点：

- 校验层 fail-closed 生效（不合法输入不写 Store）
- 并发场景：同一 namespace 下两次 `update_current_week` 调用的最终状态正确
- 越界/缺失场景：phase_index 越界、plan 不存在时的行为

### 5.3 End-to-end 骨架

扩展 `tests/contracts/run_onboarding_completion_e2e.py` 的思路（启动本地 LangGraph dev server → 真实 Store API），新增一个 `run_plan_lifecycle_e2e.py`：

```
Step 1: 走一遍 onboarding (复用现有 e2e 工具)
Step 2: 向 thread 发消息触发 Coach 调用 generate_plan
Step 3: 断言 /user/plan/current.json 存在且 PlanRecord 校验通过
Step 4: 模拟 7 天后（伪造 today），调用 /api/me/coach-context 断言 planView.state == "active"
Step 5: 触发 Coach 调用 update_current_week
Step 6: 断言 planView.current_week 字段更新
Step 7: 跳到 target_date 之后，断言 planView.state == "awaiting_review"
```

Step 4 和 Step 7 的"伪造 today"是 e2e 的难点；建议在 `compute_plan_view` 入参 `today` 上保持显式，让 e2e 直接调派生函数而不经 HTTP（或在 API route 上加 dev-only 的 `?today=YYYY-MM-DD` 覆盖；仅开发环境允许，生产环境断开，参考 `backend/src/voliti/config/` 的环境变量注入模式）。

---

## 六、Middleware 协作

### 6.1 MemoryMW（DeepAgent 原生）加载路径

DeepAgent 的 `MemoryMiddleware` 按 `_build_coach_memory_paths`（`agent.py` L90-L100）指定的路径列表预加载文件到 session state，注入到 system prompt。Plan 相关路径需要加入：

- 新增 `/user/plan/current.json` 到 coaching session 的 `memory_paths`
- 不加到 onboarding session（onboarding 完成前没有 Plan）

具体位置：`backend/src/voliti/session_type.py` 的 `SessionProfile.memory_paths`（从现有 `profile_context.md` / `chapter/current.json` 等扩展）。

### 6.2 BriefingMW 感知 Plan 变动

`BriefingMiddleware`（`backend/src/voliti/middleware/briefing.py`）只负责注入预计算的 briefing 文件，**不应**在请求链路上做 Plan 派生。派生工作由两个位置负责：

1. **日终 Pipeline**：`compute_and_write_briefing`（`briefing.py` L256-L330）已读取 `goal` 和 `chapter` 并做 `extract_goal_chapter_summary`。Plan 引入后，扩展此函数读 `/user/plan/current.json`，调用新函数 `extract_plan_highlight(plan_content, today)`（放在 `briefing.py` 或 `derivations/` 下均可；建议放 `derivations/plan_projection.py` 然后 `briefing.py` 调用它，保持派生逻辑单源）。
2. **前端 coach-context API**：每次请求调 `compute_plan_view` 即时派生。

这样 BriefingMW 自身代码零改动，只是 briefing 文件的内容会包含 Plan 高亮（"本周重点：X / 距离阶段结束：Y 天"）。

### 6.3 SkillsGate 注入时机

`SkillsGateMiddleware`（`backend/src/voliti/middleware/skills_gate.py` L37-L55）目前按 session_type 过滤。Plan skill 的注入规则：

| session | onboarding_complete | 是否注入 Plan skill |
|---------|--------------------|--------------------|
| onboarding | - | 否 |
| coaching | false | 否（还没 profile，Coach 无从生成 Plan） |
| coaching | true | 是 |

当前 `SkillsGateMiddleware` 只按 `session_type` 做 on/off，不做细粒度 skill 级过滤。两种实现路径：

**选项 A（侵入小）**：在 `backend/skills/coach/plan/SKILL.md` 的 `description` 中通过 prompt 约束（例如 "Only invoke when `/profile/context.md` contains `onboarding_complete: true`"）。Coach 自律。优点：零代码改动；缺点：依赖 LLM 遵守。

**选项 B（硬约束）**：在 `SkillsGateMiddleware` 中扩展，按文件内容再过滤一次要注入的 skill。需要在 `should_inject` 变成 `list_injected_skills`。侵入大但更稳妥。

**建议**：MVP 阶段走选项 A；在 eval 中加一条"onboarding 未完成时 Coach 不得调 generate_plan"的 seed；若 eval 不稳定再升级到选项 B。

### 6.4 顺序约束

`_build_coach_middleware`（`agent.py` L103-L121）的 middleware 栈是：

```
StripDeepAgentDefaultsMiddleware
  → SessionTypeMiddleware
  → SkillsGateMiddleware（依赖 SessionType）
  → BriefingMiddleware
```

Plan skill 不需要新增 middleware；所有逻辑通过：

1. 扩展 `SessionProfile.memory_paths`（让 Coach 能读到 Plan）
2. 在 `backend/skills/coach/plan/` 放 SKILL.md + tool.py（动态加载）
3. 扩展 `briefing.py` 的 Plan 高亮

三点局部改动完成，不打破既有 middleware 契约。

---

## 附：关键决策摘要

1. **Computing 层为独立子包 `derivations/`，入口 `compute_plan_view` 纯函数，不 I/O；双端共享 fixture 但各自实现（Python 为派生真相，TypeScript 镜像）。**
2. **三类编辑工具一律以 `@tool` 表达，通过 `backend/skills/coach/plan/tool.py` 自动加载（复用 `agent.py::_load_skill_tools` 既有机制），不新增 middleware hook。**
3. **A2UI 共建采用方案 D（混合）：摸底对话 + 结构化提议 + 增量细化 + 最终确认，最短路径 3 次 fan_out；不引入新 A2UI 原语。**
4. **Store 写入原子性靠"Plan 单 JSON 文件 + 全量覆盖写"实现；所有写路径强制走 `store_write_validated`，读路径走 `store_read_validated`；以测试扫描源码方式守门。**
5. **PlanViewRecord 每请求重算，不做派生缓存；SkillsGate 的 Plan skill 启用在 MVP 阶段靠 prompt 自律（选项 A），以 eval 兜底。**

相关文件绝对路径：

- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/contracts/__init__.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/store_contract.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/a2ui.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/agent.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/briefing.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/pipeline/day_end.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/tools/fan_out.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/tools/marker.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/middleware/briefing.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/src/voliti/middleware/skills_gate.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/skills/coach/future-self-dialogue/tool.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/skills/coach/witness-card/tool.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/tests/test_store_contract.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/tests/test_fan_out.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/tests/test_briefing.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/tests/test_day_end_pipeline.py`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/backend/prompts/onboarding.j2`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/frontend-web/src/app/api/me/coach-context/route.ts`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/frontend-web/src/lib/mirror-contract.ts`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/frontend-web/src/lib/store-sync.ts`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/frontend-web/src/components/mirror/MirrorPanel.tsx`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/tests/contracts/fixtures/store/goal_current.value.json`
- `/Users/dexter/DexterOS/products/Voliti/.claude/worktrees/recursing-blackwell-760d6e/tests/contracts/run_onboarding_completion_e2e.py`
