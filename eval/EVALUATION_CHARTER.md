<!-- ABOUTME: Voliti Eval 评估宪章 -->
<!-- ABOUTME: 统一约束维度设计、Judge 职责、seed 设计与放行口径 -->

# Voliti Evaluation Charter

## 目标

Voliti Eval 的职责不是惩罚某条理想路径，而是判断：

1. 用户是否得到了当前时刻真正需要的帮助
2. 运行时契约是否稳定
3. 其余细节是否值得记录为诊断或人工复核项

评估体系默认采用三条通道：

- **User Gate**：真正影响用户体验与模型核心行为的硬门槛
- **Runtime Contract Gate**：会导致运行时或协议层真实错误的硬门槛
- **Diagnostics + Manual Appendix**：自动诊断细节与人工审核附录，不阻断放行

## 六个设计问题

每个自动评估项在进入体系前，都必须能通过以下六个问题：

1. 用户是否真的会在意这个结果？
2. 它评估的是结果，还是在惩罚某条特定路径？
3. 它是否只评模型真正拥有的行为或文本，而不是 UI、实现细节或 reviewer 偏好？
4. 它是否能从 transcript 或 artifacts 中被稳定观察，而不是靠主观脑补？
5. 它是否允许多个合理好解，而不是只允许一种标准答案？
6. 如果它本质上是审美、细腻度、策略偏好或非文本质量，它是否应该退出硬 gate，转为 diagnostic 或 manual appendix？

任何无法清晰回答上述问题的维度，都不应进入正式 gate。

## 方法论锚点

本宪章长期遵循以下方法论主线：

- **评估结果，不评路径**  
  只要用户获得了需要的帮助，就不因为未采用某条 reviewer 偏好的中间路径而扣分。

- **Prompt 的本质是信息配置，而不是魔法措辞**  
  Judge 不因没有复述某句理想措辞而扣分，除非场景本身明确要求 exact wording。

- **有效 context 是能推动行动的 context**  
  记忆、continuity 与 profile 的价值，不在于“记起更多”，而在于是否帮助用户当前向前。

- **Skill 承载的是判断，不是模板文本**  
  intervention eval 只评模型生成文本与运行时契约，不把 skill 内建的 UI 呈现细节误当成模型行为。

- **信任来自证据、控制权与清晰边界**  
  报告必须给出 transcript、tool calls、store diff 与 prompts，且人工审核项必须与正式 gate 分离。

## Judge Charter

Judge 的职责固定如下：

- 只评分模型拥有的、用户可感知的行为与文本
- 默认评估“是否帮助用户向前”，而不是“是否最像 rubric 作者”
- 明确允许多个合理好解
- intervention 场景只评模型生成文本，不评 UI 呈现、布局与视觉层级

Judge 明确禁止：

- 因未采用某个 preferred intermediate step 而扣分
- 因未复述某句 reviewer 偏好的理想措辞而扣分
- 因风格不够像某位 reviewer 偏好而扣分
- 因 skill 内建的 UI 结构与布局细节而扣分

Judge 只在以下三类场景允许把 exact wording 当作硬要求：

1. 法律、安全或医疗边界
2. 明确的 runtime contract
3. 产品真实要求逐字引用的技术协议场景

## Assessability Boundary

评估模块必须先判断“能否稳定判断”，再决定是否自动评分。

### 可自动 gate

- 运行时契约
- onboarding 最小产物
- intervention 专用工具选择与 metadata
- 具体、即时、可从 transcript / payload 稳定观察的文本行为
  - 例如 `if_then_quality`
  - 例如 `reframe_text_fit`

### 可自动 diagnostic

- exact wording 是否更贴近用户原话
- 源域连续性
- 干预剂量
- store / memory / witness 的结构性健康度

这些信息有价值，但默认不阻断放行。

### 仅人工复核

- 开放式 reflective intervention 的深层帮助感
- Future Self 对话是否真正让用户更靠近未来身份
- Metaphor Collaboration 是否真正形成有帮助的隐喻协作
- UI / 布局 / 视觉 / 语气审美
- 长期效果或跨时间真实帮助

若某项无法在当前 transcript、tool calls、store diff 与最终文件中稳定判断，就不得被强行放进正式 gate，也不得用 RAG 补判。

## Seed Charter

每个 seed 都必须显式声明：

- `user_outcome`
- `allowed_good_variants`
- `manual_review_checks`

解释如下：

- `user_outcome`
  这个场景真正想验证的用户结果是什么

- `allowed_good_variants`
  哪些不同但合理的好解应该被自动接受

- `manual_review_checks`
  哪些内容应该进入人工附录，而不是自动 gate

`scoring_focus.primary` 只能包含 gate 维度。  
`scoring_focus.secondary` 只能包含 diagnostic 维度。  
任何冲突都必须在 `--dry-run` 阶段直接失败。

## Auditor Charter

Auditor 的职责不是“演得更像用户”，而是守住 seed 的测试边界。

Auditor 必须：

- 不主动引入会改变评估对象的新维度
- 不主动制造第二套成功路径
- 只在 seed 允许的 `allowed_good_variants` 内自然展开
- 若 seed 测某个特定框架，只能深化该框架，不得横跳到另一套问题定义
- 不能因为工具触发就结束，必须以 `user_outcome` 是否达成为终点

## 报告 Charter

单模型报告的固定顺序为：

1. `User Gate Summary`
2. `Runtime Contract Summary`
3. `Diagnostics Summary`
4. `Seed Detail`
5. `Manual Review Appendix`

其中：

- 正式放行只看 User Gate 与 Runtime Contract Gate
- Diagnostics 只提供诊断，不阻断
- Manual Appendix 只承接人工复核，不参与 pass/fail
- 无法完成评估或运行报错统一记为 `BLOCKED`
- 未被当前 seed 评估的通道统一显示为 `N/A`
- 刻意退出自动评估的内容统一显示为 `Manual Follow-up`

每个 seed 的详情必须提供：

- 结果摘要
- 为什么过 / 为什么没过
- 核心证据 turn
- Diagnostic findings
- Manual review appendix
- 折叠材料：Auditor prompt、Judge prompt、seed policy、完整 transcript、tool calls、store diff

## 发布前口径

发布前默认运行方式为：

```bash
cd eval && uv run python -m voliti_eval --profile full --runs 3
```

解释如下：

- 单次运行通过率用于日常开发反馈
- `pass^k` 用于观察多次运行中 gate 的韧性
- flake 信息必须显式展示
- 所有 gate failure 与高波动 seed 都必须人工阅读 transcript

## 变更纪律

若之后要新增、删除或降级某个维度，必须同时更新：

1. 本 Charter
2. `dimensions.py`
3. 相关 seed
4. Judge prompt 或 deterministic grader
5. 报告呈现

任何只改其中一处的做法，都视为不完整变更。
