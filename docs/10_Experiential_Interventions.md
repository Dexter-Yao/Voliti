# 体验式干预手段应用方案

本文件给出四种体验式干预手段（未来自我对话、场景预演、隐喻协作、认知重构）在 Voliti 中的落地架构。**定位为架构说明与边界文档**；实施细节以各 skill 的 `SKILL.md` 为唯一事实源，学术依据见 `docs/experiential-interventions/`。目标读者是实施者（Coach 维护、前端开发、eval 扩展）。

## 1. 架构一览

| 组件 | 位置 | 职能 |
|---|---|---|
| Skill 定义 | `backend/skills/coach/<kind>/SKILL.md` | 四份独立 skill；trigger、guardrails、A2UI Composition；LLM 直接消费 |
| Skill 深度参考 | `backend/skills/coach/<kind>/references/theory.md` | 从 `docs/experiential-interventions/` 物理复制；`test_skills_sync.py` 字节级校验 |
| Skill 专用工具 | `backend/skills/coach/<kind>/tool.py` | 每份 skill 一个 `fan_out_<kind>` 工具；`surface` / `intervention_kind` / `layout="full"` 由代码硬编码 |
| 动态加载 | `backend/src/voliti/agent.py::_load_intervention_tools` | 启动时扫描 `COACH_SKILLS_ROOT/*/tool.py`，发现的 `TOOL` 自动合入 `COACH_TOOLS` |
| SkillsGate | `backend/src/voliti/middleware/skills_gate.py` | 仅在 coaching session 注入 SKILL.md description；onboarding 跳过 |
| Backend 只读路由 | `CompositeBackend /skills/coach/` | Coach 对该路径只读；用于懒加载 references |
| A2UI 分派键 | `A2UIPayload.metadata["surface"]` + `["intervention_kind"]` | 由工具代码写入；前端据此选择全屏 Layout；详见 `docs/05_Runtime_Contracts.md § 8.5` |
| 前端视觉外壳 | `frontend-web/src/components/a2ui/intervention/` | `InterventionShell` + 四种 Layout；详见 `DESIGN.md § A2UI 渲染 / Intervention 模式` |

## 2. 核心设计原则

1. **代码承担可代码化** —— metadata（surface / intervention_kind / layout）由每个 `tool.py` 硬编码注入；Coach 只决策"用哪种干预"。Coach 工具签名不暴露 metadata / layout 参数。
2. **Skill 自包含** —— `SKILL.md` + `references/` + `tool.py` 共驻一个目录；新增第五种 intervention 只需建目录，`agent.py` 零改动。
3. **唯一事实源** —— `SKILL.md` 是 LLM 直接消费的源文件（不是文档复制品）；本文件不复述 SKILL.md 全文。
4. **前端零解析** —— 四种 Layout 仅基于 component kind 做槽位分派，不检查内容字符串。例外：scenario 的 `"IF X → THEN Y?"` chip 是极窄模式 + 不匹配即回退普通 text，不脆弱。
5. **弹性保持** —— 通用 `fan_out` 不动，继续服务 daily_checkin / daily_review 等非干预场景；`A2UIPayload.metadata` 保持 `dict[str, str]` 类型以允许未来扩展上下文键。

## 3. 四种手法索引

以下列表为概览；详细 trigger / guardrails / component sequence 见各 `SKILL.md`。

| Kind | 中文名 | SKILL.md | 前端 Layout | 开场信号 |
|---|---|---|---|---|
| `future-self-dialogue` | 和未来自我对话 | `backend/skills/coach/future-self-dialogue/SKILL.md` | `FutureSelfLayout`（三栏状态格式塔） | 动机迷雾、Chapter transition、identity drift |
| `scenario-rehearsal` | 场景预演 | `backend/skills/coach/scenario-rehearsal/SKILL.md` | `ScenarioLayout`（推演对话流） | 用户提及 2-14 天内具体事件、Forward Marker 临近 |
| `metaphor-collaboration` | 隐喻协作 | `backend/skills/coach/metaphor-collaboration/SKILL.md` | `MetaphorLayout`（景深镜头） | 用户自发使用隐喻描述状态 |
| `cognitive-reframing` | 认知重构 | `backend/skills/coach/cognitive-reframing/SKILL.md` | `ReframingLayout`（上层对比 + 下层解读） | 用户刚失控并用 catastrophizing 语言自责 |

### Coach 入口节（保持现状）

Coach 系统提示词 `coach_system.j2 § 3.5` 承载：State Before Strategy、当多个 skill 匹配时如何挑选、Hard stops、Rhythm（每 session 最多一次）。这些是 Coach 自律准则；**运行时无强制拦截**，eval 覆盖作为第二道防线。

## 4. A2UI 契约（引用）

完整 metadata 分派键与写入责任见 `docs/05_Runtime_Contracts.md § 8.5`。本节仅列要点：

- **分派键（工具代码硬编码，Coach 不写）**：
  - `surface="intervention"` —— 前端识别全屏 overlay 分支
  - `intervention_kind=<4 值之一>` —— 前端分派到对应 Layout
  - `layout="full"` —— 全屏 overlay（非 Sheet）
- **Coach 工具签名**：每个 `fan_out_<kind>(components=[...])` 只接 components 一个参数
- **构造侧断言**：`A2UIPayload.metadata` 未做键级运行时校验；分派键正确性由工具代码保证，由 `test_intervention_tools.py` 字节级验证
- **上下文键（预留扩展，当前无工具写入路径）**：`trigger_reason` / `user_state` 等

## 5. 落地清单索引

本次落地已完成的代码与文档改动见 commit 记录。下列清单仅作定位：

### 5.1 后端

- `backend/skills/coach/<kind>/tool.py`（4 份）—— metadata 硬编码 + `_fan_out_core` 复用
- `backend/src/voliti/tools/fan_out.py` —— 抽取 `_fan_out_core` 辅助函数；通用 `fan_out` 签名不变
- `backend/src/voliti/agent.py::_load_intervention_tools` —— 动态加载四工具
- `backend/src/voliti/a2ui.py` —— `A2UIPayload.metadata` docstring 说明三类语义键
- `backend/tests/test_intervention_tools.py` —— 23 项单测覆盖 metadata 硬编码、动态加载、响应处理、组件校验
- `backend/tests/test_skills_sync.py` —— theory.md 与真相源字节级校验
- SKILL.md 的 A2UI Composition 节 —— 指明 Coach 调用哪个专用工具 + 组件序列约束

### 5.2 前端

- `frontend-web/src/components/a2ui/intervention/` —— `InterventionShell` + `SignatureStrip` + 四个 `*Layout.tsx` + `slot-mapping.ts`
- `frontend-web/src/components/a2ui/A2UIDrawer.tsx` —— `surface="intervention"` 走全屏 overlay 分支
- `frontend-web/src/app/globals.css` —— intervention 专属 CSS 变量（backdrop / ribbon / clamp 字号锚点）
- `frontend-web/src/components/a2ui/intervention/slot-mapping.test.ts` —— 24 项纯函数测试
- 详细视觉规格：`DESIGN.md § Web 端适配 § A2UI 渲染（Web 适配）§ Intervention 模式`

### 5.3 Eval

- `eval/seeds/17-20_*.yaml` —— 四种 intervention 各一个触发场景；full 集 16 → 20；lite 集保持 10

### 5.4 文档

- `docs/05_Runtime_Contracts.md § 8.5` —— A2UI Metadata 语义键表
- `DESIGN.md § A2UI 渲染 / Intervention 模式` —— 共享外壳 + 四 Layout 视觉规格 + 字号最小值表
- 本文件 —— 架构与边界索引
- `AGENTS.md` / `CLAUDE.md` —— 变更记录条目

## 6. 风险与回滚

| 风险 | 缓解 |
|---|---|
| SkillsGateMiddleware 注入 token 预算上涨 | 监测生产 token 用量；必要时收紧 SKILL.md description 长度 |
| Coach 过度调用干预（"教育化"失陪伴感）| Rhythm + Hard stops 作为 prompt 约束；eval seeds 17-20 为第二道防线 |
| Skill 加载失败（tool.py 语法错误等）| `_load_intervention_tools` 捕获异常并 warning，不阻断 Coach 启动 |
| 东方传统引用被用户理解为"学术对等" | SKILL.md guardrails 禁止向用户提及任何理论名；分册 theory.md 内部标注"借鉴性对应" |
| Witness Card 与 intervention metadata 同 dict 共存 | `surface` 四取值封闭集；Witness Card composer 必写 `surface="witness-card"`；前端按 surface 值分派 |
| 真相源与 backend 复制品 drift | `test_skills_sync.py` CI 字节级校验；任何修改两边同步 |

**回滚层级**：

- **仅前端**：`A2UIDrawer` 移除 intervention 分支，回到统一 Sheet。后端 metadata 与 SKILL.md 保留，不影响服务。
- **专用工具撤回**：删除四个 `tool.py` + `agent.py::_load_intervention_tools`；`COACH_TOOLS` 恢复 `[fan_out, add_forward_marker]`；SKILL.md 仍可由 SkillsGateMiddleware 加载（可独立保留或同步撤回）。
- **Eval 撤回**：删除 4 个新 seed 文件。

所有改动不涉及 Store 迁移与数据契约破坏；回滚成本低。

## 7. 后续工作

- 端到端 QA：四种 intervention 在真实 Coach 对话中的触发、全屏 overlay 渲染、签名条不重叠、响应式降级（含 Reframing &lt;880px）
- eval 扩展：考虑给四个 intervention seed 各配一个专项 grader（判定触发正确性 + metadata + 组件序列合规）
- 上下文键写入路径：若需要观测 `trigger_reason` / `user_state` 等，评估是否为通用 `fan_out` 加 metadata 参数或走 LangSmith trace metadata
- 移动端（&lt;768px）的 intervention 专门设计 —— 当前仅桌面目标
