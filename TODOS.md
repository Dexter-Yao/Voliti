# TODOS

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

## P3: 智能签到提醒（已合并至时间感知设计）
- **What:** ~~Coach 根据用户习惯自动调整签到提醒时间~~ → 已升级为"智能签到进化"，纳入时间感知设计 P1 scope
- **Why:** 原 P3 项已被 CEO Review 2026-04-07 cherry-pick ceremony 升级为时间感知的自然组成部分
- **Context:** 不再作为独立 TODO，见 `docs/2026-04-07-temporal-awareness-design.md` 第九章 P1
- **Source:** 原 /plan-ceo-review 2026-04-06 → 升级 /plan-ceo-review 2026-04-07
