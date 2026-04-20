# 02 · 业界产品基准调研

> 范围:Noom / Second Nature / Lark / Omada / Weight Watchers / MyFitnessPal / Lose It! / Apple Fitness+ / Whoop / Oura / Fitbit Premium / Zepp / 薄荷健康 / Keep / Zero / Peloton
> 视角:同类产品如何让用户理解自己的分阶段方案、每周任务、每日节奏;哪些值得借鉴,哪些陷阱要避开。

## 一、关键发现摘要

1. **阶段语言分化** · 国际产品多用 Phase / Month / Week 结构化显示;中国产品多用模糊的"阶段"概念与渐进式解锁。Voliti 的 Phase + LifeSign 模型在设计上已超越主流做法。
2. **每周任务呈现关键差异** · Noom / Lark 采用"周主题 + 每日小课"模式;Omada 用进度圆环与医学化指标;Weight Watchers 用点数预算制——但**都未能清晰呈现"为什么是这个目标"**。Voliti 的 `process_goals` + `why_this_goal` 设计具有差异优势。
3. **失控应对是行业空白** · 现有产品在失控后多数要么推荐"重新开始",要么"继续记录";**真正的"非评判复原流程"几乎没有产品做**。这是 Voliti 最大的差异化机会。
4. **游戏化两极分化** · Keep / Weight Watchers / Fitbit 强依赖 streak / badge / 排行榜;Oura / Second Nature / Lark 等行为教练型产品明确避开,改用"进度可见性"和"状态感知"。Voliti 的"无打卡、无评判"定位与后者对齐。
5. **视觉呈现密集度** · 国际产品倾向"简化首屏 → 可选展开"(Whoop 主屏只显 Recovery / Strain / Sleep);中国产品倾向"一屏多维度"。Voliti 四块板布局(目标 + timeline / 阶段卡 / 周进度 / 日节奏)在 Refined Industrial 美学下可避免密集感。

---

## 二、值得借鉴的做法

### 1. 清晰的 Phase 语言与可视化 timeline
> 参考:Noom / Omada

山河水墨 timeline 的概念有意义,但需改进语言清晰度——不用"第 1-3 阶段",改用叙事化分组("立起早餐 → 训练成锚 → 焊进日常"的路径我们已采用)。

### 2. 周主题 + 每日微动作
> 参考:Lark / Second Nature

"每周一个核心教学主题 + 数条微动作"模式。Voliti 的 `process_goals` 应配套"本周为什么这个目标"的 2-3 句 `why_this_goal` 陈述——让用户读一眼就懂"这周不是一个任务清单,是在做一件事"。

### 3. State-First Interface
> 参考:Whoop / Oura

首屏不是"你完成了什么",而是"你今天的状态是什么"。Whoop 的 Recovery / Strain / Sleep 三指标启发了 Voliti 的 S-PDCA(State → Plan → Do)递进。

### 4. 色值编码的进度可视化
> 参考:Zero / Oura

多维度颜色编码避免单一指标的枯燥,同时保留一扫而过的可读性。Voliti 的 copper / obsidian / parchment 系统可用于区分"计划状态 / 执行状态 / 复原状态"。

### 5. 周反思而非周统计
> 参考:MyFitnessPal / Fitbit

"周总结"机制值得借鉴,但应改成**"周反思"而非"周统计"**——数字再详细,不如一句话的洞察。Voliti 的 `current_week.highlights` / `current_week.concerns` 字段正是此意图。

---

## 三、必须避开的陷阱

### 1. Streak-based 游戏化
> 反面教材:Keep / Weight Watchers / Fitbit

连续天数与成就勋章设计在心理学上已被证实会加重失败后的羞耻感。Voliti 的"无打卡、无 streak"决策已写入设计系统硬约束。

### 2. 首屏信息过载
> 反面教材:薄荷健康 / Keep

初屏同时显示 5+ 维度(体重 / 热量 / 蛋白 / 训练计划 / 社区任务),用户陷入"不知道看哪个"的无措。Voliti 的四块板布局已规避。

### 3. "线性 Phase 推进"的呈现感
> 反面教材:Noom

Noom 虽在官方讲四个阶段,但用户实际体验是"一直在同一个 app 里,怎么突然变了"——没有仪式感。Voliti 应在 Chapter 切换时增加明确的过渡。

### 4. 把 Why 藏在数字后面
> 反面教材:Omada / Weight Watchers

Omada 给"目标体重 X"但不解释"为什么现在应该是 X 而不是 Y";Weight Watchers 给 Points 但不讲"为什么这份量对你对"。Voliti 的 `why_this_phase` + `why_this_goal` 直接补齐这个心理缺口。

### 5. 通用的"失控后"流程
> 反面教材:大多数产品

多数产品"失控后"的流程是"继续记录、看趋势、再来一遍",等同于"重新开始"。Voliti 的失控应对应强调**"这次失控与上次失控的区别是什么"**,才能跳出循环。

---

## 四、对 Voliti Plan Skill 的具体设计建议

### 阶段呈现
- 不用"月数"或"数字序号",用**叙事化节点**(已采用:立起早餐 / 训练成锚 / 焊进日常)
- 山河水墨 timeline 上明确标出"当前在这里"的物理指针(已采用:copper 铜色旗)
- 每个 Phase 切换时应有明确过渡感,配合 Chapter 切换仪式

### 每周目标
- 文本只显 1-3 个 Process Goals(不超 3 个,否则重回"决策瘫痪")
- 每个 Goal 后配"这周为什么选这个"的 caption(对应 `why_this_goal` + info tooltip)
- 进度用 **bar** 或圆环均可,关键是色值对比 clean(obsidian 底 + copper fill)
- **不显示连续天数**,改显"完成 pattern"(如"本周完成 5/7 天",不是"连续 5 天")

### 每日节奏
- 不是"每日计划表",而是"今日相对于全周的位置"
- 显示当日建议 1-2 项微动作,而非完整规范
- 失控时不要藏起来——改成"本周偏离计划的情况"的中性呈现(没有红色 X、没有羞辱)

### 失控应对(最关键)
- Mirror 面板上为"打破一致性"的日子设计专门的视觉处理
- 点击进入时,不是"重新设定目标",而是进入"48-72 小时恢复工作流"
- 第一句话必须是"这很正常。让我们看看这次发生了什么" / "回来了——跟我说说这段"
- **禁用**"你的纪录断了 / 连续被打破 / 请重新开始"类语言

---

## 五、参考来源

| 产品 | 调研入口 |
|---|---|
| Noom | noom.com/blog/weight-management/noom-cost/ |
| Omada Health | omadahealth.com/frequently-asked-questions |
| Weight Watchers | weightwatchers.com/us/how-it-works/points-program |
| MyFitnessPal | support.myfitnesspal.com (Weekly Digest) |
| Keep | finance.sina.com.cn (AI Coach Kaka 发布) |
| Second Nature | secondnature.io/us |
| Lark | lark.com/resources/larks-coach-and-the-evolution-of-food-logging-meal-planning |
| Zero | screensdesign.com/showcase/zero-fasting-health-tracker |
| Fitbit Premium | blog.fitbit.com (Fitbit Dashboard Updated) |
| Whoop | whoop.com/us/en/thelocker/how-does-whoop-recovery-work-101 |
| Zepp Health | Xiaomi Mi Fit (play.google.com) |
| 游戏化陷阱综述 | trophy.so/blog/fitness-gamification-examples |
| 仪表板设计最佳实践 | thinkitive.com/blog/best-practices-in-healthcare-dashboard-design |
