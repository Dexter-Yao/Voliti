# TODOS

## P2: Witness Card 图片生成等待体验优化
- **What:** 两阶段策略——先即时呈送文字卡片（Coach 叙事 + 成就标题 + 品牌框架），后台生成图片完成后异步更新卡片
- **Why:** 当前 gpt-image-1.5 生成需 ~57 秒，虽然 Coach 文字先流式输出缓解了等待感，但生产化后用户体验仍有优化空间
- **Pros:** 用户看到文字时就能决定收下/拒绝，图片是 bonus；消除感知等待
- **Cons:** 工程复杂度高（需要异步更新已呈送的 A2UI 卡片，或第二次 interrupt，或 Store 回写 + 前端监听）
- **Context:** CEO Review 2026-04-07 评估后 Defer。当前同步流程（subagent 阻塞 ~57s）对里程碑时刻可接受（每 Chapter 仅 3-5 张），因为 Coach 文字在委托前已流式输出，用户阅读时图片同时生成
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** Witness Card P1 实现
- **Source:** /plan-ceo-review 2026-04-07, cherry-pick ceremony deferred

## P2: Coach 自我反思日志
- **What:** 每次会话结束后 Coach 写简短内部反思（"今天用户情绪低落，我尝试了 X 策略，效果待观察"）
- **Why:** 为 JourneyAnalysisMiddleware 提供更丰富的分析材料，让 Coach 的长期记忆更有深度
- **Pros:** 提升模式识别质量，Coach 的干预策略可跨会话学习
- **Cons:** 增加每次会话的 token 消耗，核心价值待验证
- **Context:** 时间感知设计中 cherry-pick ceremony deferred。反思内容写入 Coach memory，格式与现有 AGENTS.md 一致
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** 时间感知 P0/P1 基础完成
- **Source:** /plan-ceo-review 2026-04-07, cherry-pick ceremony deferred

## P2: Push 通知节制规则
- **What:** Push 通知上线时的 Day 1 安全约束：每天推送上限、禁发时间窗口（深夜/清晨）、用户静音级别、人格一致性检验指标
- **Why:** 缺少硬阈值可能导致首次上线即出现通知疲劳，反噬留存与情绪安全
- **Pros:** 防止 Push 成为用户负担，保持 Coach 信任关系
- **Cons:** 限制了 Coach 主动干预的灵活度
- **Context:** Codex Outside Voice 在 CEO Review 中发现。Push 是设计文档的 P2 模块，节制规则是其 Day 1 要求
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** Push 通知基础设施（P2）
- **Source:** /plan-ceo-review 2026-04-07, Codex outside voice

## P2: 端到端干预质量评估
- **What:** 在 Petri eval 中测试 Coach 在有/无长期视角摘要时的干预质量差异
- **Why:** JourneyAnalysisMiddleware 的最终价值体现在 Coach 干预质量，需要端到端验证
- **Pros:** 直接衡量功能的用户价值，而非中间产物
- **Cons:** 依赖足够的测试数据和评估维度设计
- **Context:** 本轮先做 MW 产出质量单元测试，端到端评估作为后续验证
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** JourneyAnalysisMiddleware 实现（P1）
- **Source:** /plan-ceo-review 2026-04-07

## P2: 可执行契约包
- **What:** 为 Store / A2UI / session contract 增加机器可读定义、golden fixtures 与最小 contract tests
- **Why:** 当前仓库仍处于 MVP 阶段，协议可能继续演化，本轮整改先以文档和实现收口为主；待协议趋稳后，再用机器校验降低再次漂移风险
- **Pros:** 协议一旦稳定，可快速建立跨端护栏，减少“每端各自理解”导致的回归
- **Cons:** 当前阶段过早固化可能放大后续协议调整成本
- **Context:** 2026-04-09 仓库一致性整改 CEO Review 中，Dexter 明确选择 defer。当前判断是先完成契约收口、一次性迁移/清理旧测试数据，再决定何时固化成可执行契约包
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** 仓库一致性整改 Phase 0/1 完成，协议基本稳定
- **Source:** /plan-ceo-review 2026-04-09, repository remediation cherry-pick ceremony

## P2: Mirror 日志区日期锚点跳转
- **What:** 为 Mirror 日志区增加“跳到某一天 / 某个月份”的快速定位能力
- **Why:** 当前方案允许较大时间范围浏览，但仍以滚动和按天折叠为主；当日志跨度变大后，定位特定时间段会逐步变慢
- **Pros:** 提升长范围日志浏览效率，减少纯滚动查找成本
- **Cons:** 会增加日志区交互复杂度，若过早实现容易把当前轻量浏览器做重
- **Context:** `codex/mirror-reliability` 的 Mirror 收口方案已明确支持日志区日期范围，但本次只做稳定浏览，不做额外定位控件
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** 当前 Mirror 日志范围浏览稳定落地，并观察真实用户是否出现长范围查找需求
- **Source:** /plan-eng-review 2026-04-11, mirror-reliability

## P2: Mirror 与 Journal 的长期职责边界
- **What:** 明确 Mirror 与 Journal 是否应长期统一为单一事件浏览体系，或继续保持不同职责下的共享底座
- **Why:** 当前实现继续复用 `EventRow` 是正确的最小路径，但若长期缺少边界定义，两个页面的事件展示逻辑容易逐步分叉
- **Pros:** 为未来事件展示演进提供清晰入口，减少 Mirror 与 Journal 各自生长造成的重复逻辑
- **Cons:** 该问题短期不直接提升用户价值，过早处理会把本次稳定性收口扩成结构重构
- **Context:** `codex/mirror-reliability` 分支本次明确不做 Journal/Mirror 重构，只做 Mirror 稳定性收口与最小复用
- **Effort:** M (human) → S (CC+gstack)
- **Priority:** P2
- **Depends on:** 当前 Mirror 收口完成并验证实际使用模式后，再判断是否值得统一
- **Source:** /plan-eng-review 2026-04-11, mirror-reliability

## P3: "你不是一个人"时刻
- **What:** Onboarding 场景认领后 Coach 回应"这是 XX% 用户都会遇到的场景，你不是一个人"
- **Why:** 调研数据显示"孤独感/陪伴需求"是跨平台一致痛点，正常化可在 Onboarding 建立信任
- **Pros:** 早期建立情感连接，降低用户的"个人缺陷"感知
- **Cons:** 百分比数据必须基于真实调研，不可编造
- **Context:** 需要更多访谈数据支撑具体百分比。现有调研中"知行分离"和"孤独感"跨平台一致，但精确比例未量化
- **Effort:** S (human) → S (CC+gstack)
- **Priority:** P3
- **Depends on:** Onboarding 场景认领功能完成（P1）+ 更多用户调研数据
- **Source:** /plan-ceo-review 2026-04-07, cherry-pick ceremony deferred

## P3: 智能签到提醒（已合并至时间感知实现）
- **What:** ~~Coach 根据用户习惯自动调整签到提醒时间~~ → 已升级为"智能签到进化"，纳入时间感知 P1 scope 并已实现
- **Why:** 原 P3 项已被 CEO Review 2026-04-07 升级为时间感知的自然组成部分
- **Context:** 不再作为独立 TODO。前瞻标记驱动 Check-in 内容调整已在 `coach_system.j2` 中实现
- **Source:** 原 /plan-ceo-review 2026-04-06 → 升级 /plan-ceo-review 2026-04-07
