# 天级 Thread 重组方案

> 状态：待审 | 作者：Dexter + Claude | 日期：2026-04-12

## 目标

以**天级 Thread 分割**为锚点，重组 Voliti 后端的 middleware 栈、数据流和 Coach 系统提示词，实现：

1. Context 负担可控——每天 thread 天然有限长度，降低 SummarizationMW 触发频率
2. Fresh Start 效应——过去一天不可变动，用户每天面对干净的起点
3. 日终 Pipeline 天然时机——封存 thread 后用小模型提取结构化事件、生成摘要
4. Coach 系统提示词精简——删除可由默认 middleware 或架构保证覆盖的指令

## 核心设计理念

按优先级递减：

1. 可通过架构设计完成的 → 架构设计
2. 可通过硬编码实现的 → 硬编码
3. 可通过默认 DeepAgent Middleware 定制的 → 不增加新模块
4. 可通过小模型独立进程实现的 → 离线 pipeline

**核心目标：将大模型 Coach 的负担降到最低，使其充分发挥能力服务用户。**

---

## 一、天级 Thread 分割

### 1.1 生命周期

```
用户发消息
    │
    ▼
查找该用户今日 active thread
（POST /threads/search, metadata: {user_id, segment_date: today, segment_status: "active"}）
    │
    ├── 存在 → 继续对话（同 thread）
    │
    └── 不存在 → 创建新 thread
            metadata: {
              user_id,
              segment_date: "2026-04-13",      // YYYY-MM-DD
              segment_status: "active",
              session_type: "coaching" | "onboarding",
              timezone: "Asia/Shanghai"         // 来自用户 profile
            }
            │
            ▼
        加载 Store memory（MemoryMW 自动完成）
        注入 briefing（SessionContextMW）
        开始对话

═══════════════ 零点（day_boundary） ═══════════════

前端：00:00 后不再允许发送新消息
     （如果 Coach 有未完成的响应，仍可完成输出）
     用户下一条消息 → 自动进入新 thread

日终 Pipeline（cron 定时任务）：
    1. PATCH thread metadata → segment_status: "sealed"
    2. 小模型提取结构化事件 → ledger
    3. 小模型生成日摘要 → /user/day_summary/{YYYY-MM-DD}.md
    4. 脚本计算 briefing 数据 → /user/derived/briefing.md
```

### 1.2 时区处理

- 时区绑定到用户手机设置，通过前端在 onboarding 或首次登录时推断，存入 `/user/profile/context.md`
- `segment_date` 使用用户本地日期（非 UTC），确保"今天"对用户有直觉意义
- 日终 Pipeline 按用户时区计算零点，触发封存

### 1.3 密封（Sealing）机制

**前端层**（主要防线）：
- 零点后前端 disable 输入框，显示"新的一天开始了"过渡提示
- 点击已封存的历史 thread → 只读查看模式
- 实现难度低——前端比对当前时间与 `segment_date` 即可

**后端层**（辅助保障）：
- Thread metadata 中 `segment_status: "sealed"` 标记
- 无 LangGraph 原生只读锁，但无 API 凭据的外部方无法接入 thread
- 如需强制执行，可在 LangGraph 的 auth handler 中加入 segment_status 检查

### 1.4 前端变更

现有基础（已实现）：
- `ensureTodayThread()` — 按天创建/复用 thread
- 历史面板按日期分组 — `groupThreadsByDate()`
- Thread metadata 存储 `date` 字段

需要新增：
- 零点后 disable 输入 + 过渡提示 UI
- 已封存 thread 的只读查看模式
- （可选）日历面板组件——Timeline Markers 和方案可视化

### 1.5 对现有工具的影响

**`retrieve_conversation_archive` 工具可删除**。替代方案：
- Coach 需要回顾过往 → 用 `read_file` 读 `/user/day_summary/{YYYY-MM-DD}.md`
- 日摘要由日终 pipeline 自动生成，天然是 summary-first 模式
- 不再需要 `ConversationArchiveAccessLayer`、`ConversationRetrievalEngine` 等组件

---

## 二、Middleware 栈重组

### 2.1 目标栈

```
DeepAgent 默认栈                   说明
──────────────────────────────    ──────────────────────────────
TodoListMiddleware                 Coach 不使用 write_todos，但无法移除
                                   → prompt 中指示忽略（成本约 300 tokens/call）
MemoryMiddleware ← memory=[       
  "/user/coach/AGENTS.md",         教练长期记忆
  "/user/profile/context.md",      用户画像
  "/user/lifesigns.md",            LifeSign（≤6 条，内联）
]                                  
FilesystemMiddleware               标准文件工具，Coach 操作 Store 的核心通道
SubAgentMiddleware ← [             
  witness_card_composer             保留
]                                 
SummarizationMiddleware            天级 thread 后负担显著降低
AnthropicPromptCachingMiddleware   Azure OpenAI 下为 NO-OP，保留无害
PatchToolCallsMiddleware           修复畸形 tool call
──────────────────────────────
Voliti 自定义栈
──────────────────────────────
SessionContextMiddleware ← NEW     合并 SessionType + Briefing（见 2.3）
──────────────────────────────

删除：
  ✗ MemoryLifecycleMiddleware     → 写入守卫下沉到 CompositeBackend 白名单
  ✗ JourneyAnalysisMiddleware     → 脚本替代 + SessionContextMW briefing 注入
  ✗ SessionTypeMiddleware          → 合并进 SessionContextMW
```

### 2.2 写入白名单（替代 MemoryLifecycleMiddleware）

在 `CompositeBackend` 的 `/user/*` 路由层实现路径白名单：

```python
_WRITABLE_PATH_PREFIXES = frozenset({
    "/user/coach/AGENTS.md",
    "/user/profile/context.md",
    "/user/profile/dashboardConfig",
    "/user/chapter/",
    "/user/lifesigns.md",
    "/user/timeline-calendar.md",
    "/user/plan/",
    "/user/coping_plans",     # 保留兼容，逐步迁移到 lifesigns.md
})
```

写入请求的路径不在白名单内 → 返回错误。比 middleware guard 更底层、更不可绕过。

### 2.3 SessionContextMiddleware（新，替代 SessionType + JourneyAnalysis）

继承 `PromptInjectionMiddleware` 基类，合并所有"会话开始时的上下文注入"：

```python
class SessionContextMiddleware(PromptInjectionMiddleware):
    """统一的会话上下文注入 middleware。

    职责：
    1. Onboarding 检测 + prompt 注入（原 SessionTypeMW）
    2. Briefing 注入（替代原 JourneyAnalysisMW）
    """

    def should_inject(self) -> bool:
        return True  # 始终注入（onboarding 或 briefing）

    def get_prompt(self) -> str:
        session_type = get_session_type()
        parts = []

        if session_type == "onboarding":
            parts.append(_ONBOARDING_PROMPT)
        else:
            # Coaching session: 注入预计算的 briefing
            briefing = self._load_briefing()
            if briefing:
                parts.append(briefing)

        return "\n\n".join(parts)

    def _load_briefing(self) -> str | None:
        """从 Store 读取预计算的 briefing 文件。"""
        # 读取 /user/derived/briefing.md
        # 由日终 pipeline 或定时脚本预生成
        # fail-open: 读取失败返回 None
        ...
```

Briefing 内容由脚本预计算（见第六节），不在 middleware 内调用 LLM。

### 2.4 MemoryMW 路径调整

当前 4 路径：
```
/user/coach/AGENTS.md
/user/profile/context.md
/user/coping_plans_index.md      ← 删除（LifeSign 内联到 lifesigns.md）
/user/timeline/markers.json      ← 删除（改为 timeline-calendar.md，按需读取）
```

新 3 路径：
```
/user/coach/AGENTS.md            教练长期记忆
/user/profile/context.md         用户画像 + 指标配置
/user/lifesigns.md               LifeSign（≤6 条，≤100 字/条）
```

减少 1 个自动加载文件 = 每次 model call 减少 context 开销。Timeline 和方案信息由 Coach 按需 `read_file`。

---

## 三、LifeSign 简化

### 3.1 新格式

从 JSON 结构化文件（`/user/coping_plans/{id}.json` + `/user/coping_plans_index.md`）简化为单一 markdown 文件：

**文件**：`/user/lifesigns.md`

```markdown
# LifeSign

1. 下班后压力大想吃零食 → 泡茶 + 阳台 3 分钟
2. 周末聚餐吃太多 → 提前吃轻食垫底、优先蛋白质
3. 出差酒店没运动条件 → 房间 15 分钟拉伸
```

### 3.2 规则

- 最多 6 条
- 每条不超过 100 字（触发场景 → 应对策略）
- 由 MemoryMW 自动加载到 Coach context
- Coach 用 `edit_file` 直接编辑
- 不需要专门的工具——文件就是接口
- 不跟踪成功率（成功/失败信号由 Coach 在对话中自然观察，写入 AGENTS.md）

### 3.3 迁移

现有 `/user/coping_plans/{id}.json` + `/user/coping_plans_index.md` 数据一次性转换为 `/user/lifesigns.md` 格式。迁移脚本在日终 pipeline 中执行一次。

---

## 四、Timeline Calendar

### 4.1 文件格式

**文件**：`/user/timeline-calendar.md`

```markdown
# Timeline Calendar
Timezone: Asia/Shanghai

## 2026-04-12 (Sat)
- 朋友聚餐 19:00 [HIGH] → LifeSign #2

## 2026-04-15 (Tue)
- 出差北京（3 天）[MED] → LifeSign #3
- 团队晚餐 [MED]

## 2026-04-18 (Fri)
- 回程

## 2026-04-28 (Mon)
- 体检 [INFO]
```

### 4.2 设计特征

1. **人类可读 + 机器可解析**：markdown 格式，日期为 section header，前端用正则提取
2. **Coach 感知今天**：Coach 通过系统 prompt 中的时间戳知道今天日期，对照 calendar 自行判断"这周"
3. **不自动加载到 context**：从 MemoryMW 路径中移除。Coach 需要时用 `read_file` 按需读取
4. **Coach 直接编辑**：用 `edit_file` 添加/修改/删除条目。复用 FilesystemMW 标准工具
5. **关联 LifeSign**：通过 `→ LifeSign #N` 引用，Coach 在对话中提醒用户相关应对策略
6. **日终 Pipeline 清理**：已过去的条目由脚本自动删除，保持文件精简

### 4.3 Context 中的索引

SessionContextMW 的 briefing 中包含未来 7 天的 calendar 摘要：

```
## 近期日程
- 4/15 出差北京 [MED]
- 4/28 体检

完整日历：/user/timeline-calendar.md（需要时 read_file）
```

这样 Coach 在多数对话中不需要读取完整 calendar，只有当用户提及日程相关话题时才按需加载。

---

## 五、Coach 系统提示词精简

### 5.1 删除/简化的内容

经审计，coach_system.j2（401 行）中以下部分与默认 middleware 重叠或可被架构保证替代：

| 行号范围 | 内容 | 处理 |
|----------|------|------|
| 140-144 | "以下文件已自动加载，不要重新读取" | **删除**。MemoryMW 已保证加载，`<agent_memory>` 标签已明示 |
| 93-100 | `retrieve_conversation_archive` 工具说明 | **删除**。工具本身被删除，Coach 用 `read_file` 读日摘要 |
| 175-213 | Event Recording 详细 schema | **大幅简化**。事件提取移到日终 pipeline，Coach 不再直接写 ledger |
| 215-238 | Forward Markers schema（timeline/markers.json） | **替换**。改为 timeline-calendar.md 的简要说明 |
| 355-385 | LifeSign 完整 JSON schema + 索引格式 | **简化**。改为 lifesigns.md 的简要说明（≤6 条、≤100 字） |
| 244-264 | 数据架构目录树 | **更新**。反映新的文件结构 |

### 5.2 新增/保留的内容

| 内容 | 理由 |
|------|------|
| Identity & Mission（25-31 行） | Voliti 特有，保留 |
| Voice（37-43 行） | 保留 |
| Boundaries — Layer 1 扩展 | **更新**：Layer 1 新增"根据用户环境和动机制定具体饮食与运动计划" |
| Coaching Framework（S-PDCA）| 保留 |
| fan_out / witness_card 工具说明 | 保留（Voliti 特有） |
| Semantic Memory Boundary | **简化**。只需列出可写路径，删除 candidate signal / archive 分类 |
| Metrics Governance | 保留（Voliti 特有领域知识） |
| Chapter Management | 保留 |
| Session Protocol | 保留 |
| "不要使用 write_todos 工具" | **新增**。缓解 TodoListMW 的 token 浪费 |
| 日摘要读取方式说明 | **新增**。替代 retrieve_conversation_archive 说明 |

### 5.3 Boundary Layer 1 扩展

当前 Layer 1（Open）：
> 卡路里估算、宏量营养指导、行为模式识别、meal planning

扩展为：
> 卡路里估算、宏量营养指导、行为模式识别、meal planning、**根据用户环境（场景、社交、时间）和动机制定具体的饮食与运动执行计划**

这使 Coach 可以在 Layer 1 范围内给出实操级别的建议（"出差期间建议每天午餐选择蛋白质优先的简餐"），而不仅是原则性指导。计划必须贴合用户的实际情境——游泳、独处、出差等不同环境下的计划完全不同。

### 5.4 预估精简效果

| 指标 | 当前 | 精简后 | 变化 |
|------|------|--------|------|
| coach_system.j2 行数 | ~401 | ~250 | -38% |
| 系统 prompt tokens（估） | ~3500 | ~2200 | -37% |
| 自动加载文件数 | 4 | 3 | -25% |
| 自定义 middleware | 3 | 1 | -67% |
| Coach 工具总数 | ~10 | ~8 | -20% |

---

## 六、Briefing 机制（替代 JourneyAnalysis）

### 6.1 数据源

由定时脚本（非 Coach LLM）计算以下信号：

```python
briefing_data = {
    "days_since_last_session": 3,           # 距上次会话天数
    "total_sessions_this_week": 4,          # 本周会话数
    "recent_check_in_streak": 7,            # 连续打卡天数
    "upcoming_markers_7d": [                # 未来 7 天 calendar 事件
        {"date": "4/15", "desc": "出差北京", "risk": "MED"},
    ],
    "lifesign_recent_mentions": {           # 近期 LifeSign 提及情况
        "#1 下班压力": "3 次提及 / 本周",
        "#3 出差运动": "0 次提及",
    },
    "north_star_trend": "72.3kg → 71.8kg (7d, -0.5)",  # 北极星趋势
    "notable_events": [                     # 显著事件
        "连续 7 天打卡",
        "3 天前因聚餐超标",
    ],
}
```

### 6.2 Briefing 文件

**文件**：`/user/derived/briefing.md`

由脚本生成固定格式文本，SessionContextMW 在每次会话开始时注入：

```markdown
## Coach Briefing (auto-generated, 2026-04-13)

距上次会话：3 天
本周会话数：4 次
连续打卡：7 天

北极星趋势：72.3kg → 71.8kg (7d, -0.5kg)

近期日程：
- 4/15 出差北京 [MED]

LifeSign 活跃度：
- #1 下班压力：本周 3 次提及
- #3 出差运动：未提及（提前提醒出差应对）

值得关注：
- 连续 7 天打卡——考虑 Witness Card
- 3 天前聚餐超标——关注恢复节奏

完整日历：read_file /user/timeline-calendar.md
```

### 6.3 脚本执行策略

| 频率 | 触发 | 计算内容 |
|------|------|----------|
| 每天零点 | 日终 Pipeline（cron） | 封存 thread、提取事件、生成日摘要、更新 briefing |
| 用户首次发消息 | 应用层检查 | 如果 briefing 已过期（>24h），触发增量更新 |

脚本不调用大模型——所有计算都是确定性的（日期差、计数、趋势计算）。日摘要生成是唯一使用小模型的步骤。

---

## 七、日终 Pipeline

### 7.1 触发时机

用户时区的零点（从 profile 读取 timezone）。使用 cron 或 LangGraph 的定时触发机制。

### 7.2 执行步骤

```
步骤 1：封存 Thread
  PATCH /threads/{id} metadata: {segment_status: "sealed", sealed_at: ISO8601}

步骤 2：生成日摘要
  读取 thread 完整历史 → 小模型（GPT-5.4-Nano）生成摘要
  写入 /user/day_summary/{YYYY-MM-DD}.md
  格式：3-5 个要点 + 关键数据变动 + 情绪基调

步骤 3：提取结构化事件（可选，视需求启用）
  小模型从对话中提取：体重记录、饮食观察、运动记录、情绪状态
  写入 /user/ledger/{YYYY-MM-DD}.json
  格式：数组 [{kind, evidence, metrics, ...}]

步骤 4：更新 Briefing
  确定性脚本计算：
  - 距上次会话天数
  - 打卡连续性
  - 北极星趋势（从 ledger 或 day_summary 提取）
  - 未来 7 天 calendar 事件
  - LifeSign 活跃度
  写入 /user/derived/briefing.md

步骤 5：Calendar 清理
  删除 timeline-calendar.md 中已过去的条目
```

### 7.3 Fail-Open 设计

Pipeline 任一步骤失败不阻塞后续步骤。失败记录写入 `/user/observability/pipeline-errors.log`。Coach 在没有 briefing 的情况下仍能正常工作——只是少了一层上下文。

---

## 八、Coach 写入机制

### 8.1 Coach 可写路径

| 路径 | 内容 | 写入频率 |
|------|------|----------|
| `/user/coach/AGENTS.md` | 教练长期记忆 | 每次对话（MemoryMW 指导） |
| `/user/profile/context.md` | 用户画像 + 基本信息 | 低频（信息变更时） |
| `/user/profile/dashboardConfig` | 北极星 + 支撑指标配置 | 极低频（配置变更） |
| `/user/chapter/current.json` | 当前身份阶段 | 低频（Chapter 转换时） |
| `/user/chapter/archive/{id}.json` | 归档 Chapter | 低频 |
| `/user/lifesigns.md` | LifeSign（≤6 条） | 低频 |
| `/user/timeline-calendar.md` | 日程事件 | 中频（对话中发现新事件） |

### 8.2 当天数据（体重等）

在天级 thread 架构下，当天的体重、饮食等数据自然存在于对话 context 中。Coach **不需要在对话中将当天数据写入文件**——数据就在 thread 的消息里。

日终 pipeline 的小模型负责从 thread 历史中提取结构化数据并写入持久化存储。

**例外**：如果用户上午称了体重并希望立即在 Mirror 面板看到更新，Coach 需要写入 Store。此时 Coach 用 `edit_file` 更新 `/user/profile/context.md` 中的最新体重字段即可。这不需要专门的工具——FilesystemMW 的标准 `edit_file` 足够。

### 8.3 Mirror 面板数据源

Mirror 面板当前从 Store 读取 Chapter、指标配置、LifeSign 等数据。在新架构下：

| 面板区域 | 数据源 | 更新时机 |
|----------|--------|----------|
| Chapter | `/user/chapter/current.json` | Coach 写入时即时更新 |
| 北极星指标 | `/user/profile/context.md` 或 `dashboardConfig` | Coach 写入时即时更新 |
| 支撑指标 | 同上 | 同上 |
| LifeSign | `/user/lifesigns.md` | Coach 写入时即时更新 |
| Timeline | `/user/timeline-calendar.md` | Coach 写入 + 日终清理 |

前端刷新 Mirror 面板时从 Store 读取最新数据。无需额外 API。

---

## 九、数据迁移

### 9.1 迁移清单

| 现有数据 | 目标 | 策略 |
|----------|------|------|
| `/user/coping_plans/{id}.json` | `/user/lifesigns.md` | 一次性脚本转换 |
| `/user/coping_plans_index.md` | `/user/lifesigns.md` | 合并到上述 |
| `/user/timeline/markers.json` | `/user/timeline-calendar.md` | 一次性脚本转换 |
| `/user/derived/last_journey_analysis.json` | 删除 | 不再需要 |
| `/user/derived/pattern_index.md` | 评估保留价值 | 可能合并到 AGENTS.md |

### 9.2 迁移顺序

1. 先部署新 middleware 栈（兼容旧数据路径）
2. 运行迁移脚本
3. 更新 Coach 系统 prompt
4. 删除旧代码路径

---

## 十、暂缓事项

### 10.1 方案工具（Action Plan）

**状态**：设计中，暂缓实现。完成天级 thread + middleware 精简后再评估。

**已有的设计思考**：
- 方案是 Chapter（identity_statement + goal）的执行层
- 核心指标关联：Chapter + 北极星 + 3 支撑指标
- 方案结构：总体指南 + 多维度天/周/月计划
- 需要动态调整机制（执行反馈）
- 实现方式：文件读写（`/user/plan/current.md`），不需要专门工具
- 方案与 Timeline Calendar 结合——特定天的计划需关联当天日程
- 可能需要前端日历面板（在支撑指标下方、ledger 面板上方）

**暂缓原因**：
- 方案粒度（天/周/月）需要基于真实用户行为确定
- Coach 能否在 Layer 1 边界内提供足够具体的计划，需要先扩展 Boundary 后观察
- 动态调整机制的复杂度需要评估

**重新评估时机**：天级 thread + Boundary Layer 1 扩展完成后，观察 Coach 自然行为 2 周。

### 10.2 SummarizationMW 模型配置

**状态**：待确认 DeepAgent API。

SummarizationMW 默认使用主模型（GPT-5.4）做压缩。理想方案是配置为 GPT-5.4-Nano。需确认 `create_deep_agent` 是否支持为 SummarizationMW 指定独立模型。

天级 thread 架构下 SummarizationMW 触发频率大幅降低（单天对话长度有限），优先级下调。

---

## 十一、实施顺序

```
阶段 1：基础（无破坏性变更）
├── 1a. Coach prompt 精简（删除重叠内容、Boundary Layer 1 扩展）
├── 1b. LifeSign 简化（新建 lifesigns.md 格式 + 迁移脚本）
└── 1c. Timeline Calendar 文件设计（新建 timeline-calendar.md + 迁移脚本）

阶段 2：Middleware 重组
├── 2a. 创建 SessionContextMiddleware（合并 SessionType + Briefing 注入）
├── 2b. 写入白名单下沉到 CompositeBackend
├── 2c. 删除 MemoryLifecycleMiddleware + JourneyAnalysisMiddleware
├── 2d. 更新 MemoryMW 路径（4 → 3）
└── 2e. 删除 retrieve_conversation_archive 工具及相关代码

阶段 3：日终 Pipeline
├── 3a. Thread 封存逻辑（PATCH metadata）
├── 3b. 日摘要生成（小模型）
├── 3c. Briefing 计算脚本
└── 3d. Calendar 清理脚本

阶段 4：前端对齐
├── 4a. 零点后 disable 输入 + 过渡提示
├── 4b. 已封存 thread 只读模式
└── 4c. Mirror 面板数据源更新

阶段 5：清理
├── 5a. 删除 ConversationArchiveAccessLayer / ConversationRetrievalEngine
├── 5b. 删除旧 LifeSign / Forward Markers 相关代码
├── 5c. 更新 docs/05_Runtime_Contracts.md
└── 5d. 更新 CLAUDE.md / AGENTS.md
```

---

## 十二、验证计划

| 验证项 | 方法 | 通过标准 |
|--------|------|----------|
| 天级 thread 创建/复用 | 手动测试 | 同一天多次对话使用同一 thread |
| Thread 封存 | 手动触发日终 pipeline | metadata.segment_status = "sealed" |
| Coach 不读已封存 thread | 观察 Coach 行为 | Coach 使用 day_summary 而非直接读 thread |
| Briefing 注入 | 检查 LangSmith trace | system prompt 中包含 briefing 段落 |
| LifeSign 编辑 | 对话中要求修改 LifeSign | Coach 用 edit_file 正确编辑 lifesigns.md |
| Calendar 编辑 | 对话中提及未来事件 | Coach 用 edit_file 正确更新 calendar |
| 写入白名单 | 尝试写入非白名单路径 | 返回错误 |
| prompt 精简效果 | 比对 LangSmith trace | tokens 减少 ≥30% |
| `pnpm build` | CI | 前端构建通过 |
| `uv run python -m pytest` | CI | 后端测试通过 |
