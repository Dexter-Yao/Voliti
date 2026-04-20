# 01 · Plan Skill 学术调研报告

<!-- ABOUTME: Plan Skill 设计的学术理论依据与循证建议 -->
<!-- ABOUTME: 覆盖行为改变理论、减脂周期化、营养训练指南、权威机构立场、反面教训五个维度 -->

> **文档类型**:学术调研(READ-ONLY)
> **调研范围**:行为改变理论 / 减脂周期化 / 营养训练指南 / 权威机构立场 / 反面教训
> **产出日期**:2026-04-19
> **服务对象**:Plan Skill(分阶段减脂方案生成)SKILL.md 设计

---

## 一、行为改变核心理论

### 1.1 跨理论模型(TTM)—— Prochaska & DiClemente

**理论概述**

跨理论模型(Transtheoretical Model, TTM)由 Prochaska 与 DiClemente 在 1983 年提出,1992 年系统化(Prochaska, DiClemente & Norcross, *Health Psychology*, 1992)。该模型将行为改变定义为五阶段过程:

| 阶段 | 英文 | 特征 | 典型标志 |
|------|------|------|---------|
| 前思考期 | Precontemplation | 无意向改变 | "减脂不是我的问题" |
| 思考期 | Contemplation | 有意向,未行动 | "我知道该减,但……" |
| 准备期 | Preparation | 计划 30 天内行动 | "我在找方法" |
| 行动期 | Action | 过去 6 个月内有可观察改变 | 已建立饮食/运动习惯 |
| 维持期 | Maintenance | 行为改变持续 ≥6 个月 | 防止复发,巩固身份认同 |

**减脂干预证据**

一项巴西初级医疗系统随机对照试验(Lopes & Desidério Nogueira, *BMC Public Health*, 2020, PMC7216547)将 TTM 应用于体重管理咨询,历时 6 个月,结果显示干预组(基于 TTM 的每月个体咨询)显著改善饮食行为,但证据质量受偏倚风险与精确度不足的限制——长期超过 1 年的效果仍不稳定。

系统综述(Hashemzadeh et al., *Nutrients*, 2019)确认:TTM 对饮食和运动改变的短中期干预有效,但证据强度不允许得出强结论。

**→ 对 Plan Skill 的映射**:
- Plan Skill 服务的用户处于"准备期 → 行动期"的过渡点,而非前思考期
- Plan 的语气与结构应面向"已有动机"的用户,不需要动机激励,直接进入"如何做"
- 三段式 phases(适应 → 主攻 → 维持)与 TTM 阶段次序高度对齐:Phase 1 = Action Entry(建立节奏);Phase 2 = Action Deepening(深化行为);Phase 3 = Maintenance(防止复发)
- phases 建议设为 3 段而非 2 段或 4 段,原因正是 TTM 三主要行为阶段结构

---

### 1.2 目标设定理论(Goal Setting Theory)—— Locke & Latham

**理论基础**

Locke(1968)与 Latham(1975)系统化提出目标设定理论(Goal Setting Theory, GST),核心命题:**具体且有挑战性的目标(specific + challenging goals)比模糊目标("尽力而为")产生显著更高绩效**。

关键研究发现(Locke & Latham, *American Psychologist*, 2002):
- 设定困难目标的参与者,绩效比设定最容易目标的参与者高出 **250%**
- 目标效果被五个调节因素放大:承诺(commitment)、反馈(feedback)、任务复杂度、能力、情境约束

**过程目标 vs. 结果目标的区分**

Locke & Latham 2006(*Current Directions in Psychological Science*, 15(5), 265-268)明确区分:
- **结果目标(Outcome Goal)**:减 10 斤——聚焦最终结果
- **过程目标(Process Goal)**:每天摄入 1600-1800 kcal,每周训练 3 次——聚焦可控行为

研究发现,在复杂任务(如减脂)中,**仅设定结果目标会导致"隧道视野"**,缺乏技能习得路径;过程目标则更有利于能力建构与长期坚持。

美国减肥项目的社区队列研究(Burke et al., *Obesity*, 2025, PMC11897847)表明:行为目标依从性每提升 10%,6 个月末体重损失量增加 0.8-1.2 kg(p<0.001)。

目标设定与体重损失的社区研究(Collins et al., *JMIR*, 2023, PMC10357317)显示:eHealth 平台中**设定个人化目标的用户 6 个月末体重损失显著高于非设定目标用户**(控制协变量后)。

**→ 对 Plan Skill 的映射**:
- Plan 必须同时包含结果目标(`target`:减多少/多久)和过程目标(`process_goals`:3 个具体行为目标)
- 过程目标应是可测量且具体的行为——如"每周 3 次力量训练,每次 ≥30 分钟",而非"多运动"
- 每个 process_goal 应附带可测量的 `days_met / days_expected` 跟踪维度,正是 GST"反馈循环"的操作化
- 结果目标应具体但不宜过于激进(参考下文"减脂速率"建议的安全上限)

---

### 1.3 执行意图(Implementation Intentions)—— Gollwitzer

**理论基础**

Gollwitzer(1999, *American Psychologist*, 54(7), 493-503)提出执行意图(Implementation Intentions)概念:以"如果情境 X 出现,我将执行行为 Y"(if-then)格式预先规划行为,可显著提升目标达成率。

**元分析证据**

- Gollwitzer & Sheeran(2006)在 *Advances in Experimental Social Psychology*(38, 69-119)对 **94 项独立研究进行元分析**,执行意图的效应量为中到大(**d = 0.65**),对行为依从性的提升具有实质意义
- Aarts et al.(2024)更大规模综合分析(**642 项独立测试**)显示效应量 d 区间 0.27-0.66,在认知/情感/行为输出上均有效(*European Review of Social Psychology*, 2024)
- 在饮食健康、运动坚持等"明知该做但经常做不到"的领域,效果尤为突出

**减脂/健康行为的具体应用**

Meta 分析(Sheeran & Orbell, *British Journal of Social Psychology*, 2000)确认:if-then 格式对目标意图的执行率平均提升约 **28 个百分点**。

**→ 对 Plan Skill 的映射**:
- `contingency`(失控应对规则)和 `known_risks`(预案引用)正是执行意图的产品化实现
- 格式建议:每条 contingency 应明确包含"触发条件"(if:今晚有商务餐)+ "执行指令"(then:主菜选蛋白质为主,不点主食,酒精控制在 1 杯以内)
- LifeSign 系统已经按此逻辑运作,Plan Skill 的 contingency 字段应与 LifeSign 格式保持一致,避免重复
- 执行意图效果在"高动机 + 预先排练"条件下最大——这意味着 Plan Skill 在生成 contingency 时应引导用户脑演一遍场景(场景预演 Skill 协作机会)

---

### 1.4 习惯环(Habit Loop)—— Duhigg / Clear / Lally

**理论框架**

Duhigg(2012, *The Power of Habit*)将习惯定义为"线索—惯例—奖励"(Cue-Routine-Reward)三环结构。Clear(2018, *Atomic Habits*)进一步区分为四步:线索—渴望—响应—奖励。

关键实验发现:**线索的具体化是习惯形成的关键操纵变量**。线索可以是时间、地点、前置行为、情绪状态或他人。

**习惯形成周期的实证**

Lally 等(2010, *European Journal of Social Psychology*, 40, 998-1009)追踪 96 名参与者建立新健康行为的自动化程度,发现:
- 习惯达到最大自动化程度的平均时间:**66 天**
- 个体差异范围:**18-254 天**
- 漏掉一次机会**不显著影响**最终习惯形成
- 更简单的行为形成更快,复杂行为需要更长时间

**→ 对 Plan Skill 的映射**:
- `daily_rhythm`(统一规范)的设计应围绕**清晰的线索(cue)结构**,不仅规定"吃什么",还规定"什么时机吃"(线索)
- Phase 时长建议**最少 3 周、最长 8 周**,理由:低于 18 天习惯尚未稳定;超过 8 周进入长维持期,应升阶为新 Phase
- Phase 1(适应期)特别关键,对应 Lally 数据中"习惯形成最不稳定的前 21 天"——此阶段 daily_rhythm 应尽量简单,减少认知负荷
- Plan 在 daily_rhythm 中不应只写目标值,应写**触发点**("睡前 1 小时记录当日饮食")

---

### 1.5 自我决定理论(SDT)—— Deci & Ryan

**理论基础**

Deci & Ryan(2000, *Psychological Inquiry*, 11, 227-268)提出自我决定理论(Self-Determination Theory, SDT),主张人类有三种基本心理需求:
- **自主性(Autonomy)**:行为发自内在意志,而非外部压力
- **胜任感(Competence)**:感到自己有能力完成任务
- **关联感(Relatedness)**:感到与他人有意义的连接

**减脂/健康行为的证据**

SDT 在医疗减重项目中的应用研究(Williams et al., *Journal of Personality and Social Psychology*, 1998)表明:**更自主地进行行为改变的参与者,长期依从性显著更高**——在饮食改变和运动参与两个维度均得到验证。

罗彻斯特大学研究中心(URMC)综述指出:当社会环境同时支持三种心理需求时,用户更可能进行自主自我调节,从而持续改变。

**认知评价理论(CET)的子命题**:外部奖励(如积分、排行榜)若被用户解读为"控制性",将降低内在动机;若被解读为"信息性"(你进步了),则不影响甚至正向加强内在动机。

**→ 对 Plan Skill 的映射**:
- Plan 应以**"共建"方式生成**,而非系统单方面下发——与 SDT 自主性需求契合
- 关键操作:Plan Skill 不应直接输出完整方案,而应先呈现选项,让用户参与决策("这两个方案,你觉得哪个更接近你实际能做到的?")
- 胜任感设计:Phase 1 应设置相对容易达成的 process_goals,建立早期成功体验,再逐渐升阶
- 禁止元素:points 积累、streak 计数、任何形式的排行——这些被 CET 和 SDT 定性为"控制性奖励",损害长期内在动机

---

## 二、减脂 / 体重管理方案的周期化

### 2.1 周期化训练的理论起源与跨域应用

**Matveyev 周期化(Periodization)**

前苏联生理学家 Matveyev(1964, *Problem of Periodization of Athletic Training*)在分析 1952、1956 年奥运会苏联运动员数据后,系统化提出训练周期化模型,将训练组织为:

| 层级 | 名称 | 时间跨度 | 特征 |
|------|------|---------|------|
| 宏循环 | Macrocycle | 12 个月 | 整体年度目标 |
| 中循环 | Mesocycle | 3-4 个月 | 阶段主题(准备/竞赛/恢复) |
| 微循环 | Microcycle | 1-4 周 | 每周具体安排 |

理论基础依赖 Selye 的**一般适应综合征(GAS)**与**特异性适应需求(SAID)原则**:压力 → 适应 → 超量补偿。

**跨域应用于减脂**:周期化逻辑在减脂中体现为:不同阶段采用不同强度(热量赤字深度)、不同侧重(适应/攻坚/维持),而非全程单一高赤字。NASM 运动学文献明确将此逻辑延伸至体重管理方案设计。

**→ 对 Plan Skill 的映射**:
- Plan 的三段 phases 本质是 Mesocycle 结构在减脂领域的应用
- Phase 1(4-6 周)= 准备期:建立饮食/运动习惯,赤字较小,降低退出风险
- Phase 2(4-8 周)= 主攻期:最大赤字(但不超过安全上限),最优脂肪流失
- Phase 3(≥4 周)= 维持/过渡期:赤字收窄,建立长期可持续行为模式

---

### 2.2 "适应—主攻—维持"三段式临床证据

**体重管理行为干预的分段依据**

NICE NG246 临床指南(英国, 2024)在行为干预结构建议中,将体重管理划分为不同密度的支持阶段:初始强化阶段 → 过渡阶段 → 维持阶段。USPSTF(美国, 2018)要求强化行为干预具备结构化多阶段特征(≥12 次会话/年),正是阶段化支持的标准化体现。

循序渐进的干预设计在多项 RCT 中得到验证:
- Omada Health 计划(医疗 DPP 认证)采用 16 周强化 + 长期维持的两阶段结构
- Noom 采用 16-24 周的分阶段心理-行为课程模型

共同逻辑:**先建立行为,再强化减脂,最后转入维持**——这正是减脂不可跳过"适应期"的理由。

---

### 2.3 平台期(Weight Loss Plateau)的成因与应对

**代谢适应(Metabolic Adaptation)**

减脂过程中,基础代谢率(BMR)会随体重降低而下降,但其下降幅度**超出体重变化的预期幅度**,即存在"超量代谢抑制"(adaptive thermogenesis)。

StatPearls 综述(Sarwan & Rehman, NCBI NBK576400)指出平台期两大机制:
1. **代谢适应**:瘦素(leptin)降低、甲状腺素减少、交感神经抑制 → 基础代谢下降
2. **依从性漂移(Adherence Drift)**:实际摄入逐渐上升、实际消耗逐渐下降,但用户对此缺乏感知

超过 **80% 的减脂者最终体重反弹**(StatPearls, NBK592402),反弹率与平台期处理策略直接相关。

**应对策略的循证依据**

- **Diet Break(饮食间歇期)**:MATADOR 研究(Byrne et al., *International Journal of Obesity*, 2017)最具代表性(见下节)
- **重新评估依从性**:平台期优先排查实际摄入与消耗,而非进一步削减热量
- **训练变化**:引入新刺激(抗阻训练强度提升、NEAT 增加)

**→ 对 Plan Skill 的映射**:
- Plan 应在每阶段末内置"平台期预案"——不是主动触发失控应对,而是告知用户"第 X 周可能出现体重停滞,这是正常生理响应"
- contingency 中应包括平台期应对规则:核查实际饮食依从性,而非加大赤字
- known_risks 字段可引用"代谢适应"作为预注册风险

---

### 2.4 Diet Break / Refeed Protocol 的循证依据

**MATADOR 研究(关键证据)**

Byrne 等(*International Journal of Obesity*, 2017, PMC5803575)开展的 MATADOR(Minimising Adaptive Thermogenesis And Deactivating Obesity Rebound)随机对照试验,51 名男性肥胖者:
- 对照组(CON):16 周连续热量限制(摄入 = 维持量的 67%)
- 干预组(INT):8 × 2 周限制 + 7 × 2 周能量平衡轮替(共 30 周总时长)

**关键发现**:
- INT 组脂肪减少量显著更大(**12.3 kg vs 8.0 kg, p<0.01**)
- 去脂体重损失两组相近
- 调整体成分变化后,INT 组代谢适应抑制幅度显著低于 CON 组(-360 vs -749 kJ/day, p<0.05)

**系统综述更新**

Jéquier Gygax 等(2024, 发表于 *BMJ Open*, PMC10088065 已引用相关证据):间歇性热量限制在依从性和代谢适应衰减方面优于连续限制,但需要更长总时程。

**→ 对 Plan Skill 的映射**:
- Plan 的 Phase 之间可以内置"恢复窗口"(1-2 周),热量提升至维持水平,对应 MATADOR 的"能量平衡块"
- 恢复窗口不等于"计划外放纵",应有明确的热量目标(维持量,不低于基础代谢)
- contingency 中应包括:持续 2 周以上体重无变化 → 启动 1 周 diet break,再重新评估

---

### 2.5 减脂速率的推荐安全范围

**主流机构建议**

| 机构 | 推荐每周减重速率 | 来源 |
|------|----------------|------|
| NIH(美国) | 0.5-1 kg/周 | NHLBI 临床指南 |
| ACSM(2009) | 不超过体重的 1%/周 | Position Stand, PMID 19127177 |
| NICE(英国, NG246) | 0.5-1 kg/周 | 行为干预部分 |
| 中国营养学会(2022) | 0.5-1 kg/周,个体化调整 | 膳食指南 2022 |

**肌肉保留的速率限制**

Helms 等研究(综合引用自 ISSN)显示:抗阻训练者将减脂速率控制在体重的 **0.5%/周以内**时,肌肉保留效果显著优于更快速率。过快减脂(>1 kg/周)在蛋白质摄入不足时,去脂体重(FFM)损失比例显著上升。

**→ 对 Plan Skill 的映射**:
- Plan 在生成时应验证用户目标的速率合理性:`(target_kg / duration_weeks)` 应在 0.4-0.9 kg/周区间
- 若用户目标超过 1 kg/周,应向用户说明风险并调整目标(肌肉损失、营养不足、难以维持),而非直接拒绝
- `daily_calorie_range` 的下限设计应防止摄入低于基础代谢(BMR)——这是绝对底线

---

## 三、营养与训练实务指南

### 3.1 蛋白质摄入 —— ISSN 立场声明

**核心推荐范围**

国际运动营养学会(ISSN)立场声明(Jäger et al., *Journal of the International Society of Sports Nutrition*, 2017, PMC5477153):

| 人群 | 推荐蛋白质摄入(每公斤体重) |
|------|--------------------------|
| 一般运动人群(维持) | 1.4-2.0 g/kg/天 |
| 抗阻训练者(减脂期) | 2.3-3.1 g/kg/天(以维持肌肉量) |
| 极高摄入(探索性) | >3.0 g/kg/天(仍安全,但额外收益边际递减) |

**减脂期肌肉保留的证据**

ISSN 立场声明明确:"Higher protein intakes (2.3-3.1 g/kg/d) may be needed to maximize the retention of lean body mass in resistance-trained subjects during hypocaloric periods."

中国营养学会(CNS)膳食指南 2022:中国普通成人日均蛋白质摄入建议约 **1 g/kg/天**,65 岁以上建议 **1.2 g/kg/天**;高质量蛋白质(动物蛋白 + 大豆蛋白)应占总摄入的 **50% 以上**。

**→ 对 Plan Skill 的映射**:
- `daily_protein_grams_range` 字段应基于用户体重与运动程度动态计算
- 减脂初学者(无系统训练):1.4-1.8 g/kg/天
- 有力量训练计划的用户:1.8-2.4 g/kg/天(对中国用户而言,此范围已高于 CNS 标准,需要说明理由)
- Phase 1(适应期)蛋白质目标可略保守,Phase 2(主攻期)提升至上限
- 蛋白质范围应以具体克数呈现(如"每日 100-120g 蛋白质"),不要仅呈现比例,降低用户理解门槛

---

### 3.2 热量赤字 —— 推荐范围与计算基础

**NIH 标准建议**

NHLBI 临床指南(1998, 至今仍是权威参照):
> "A caloric deficit of 500-1,000 kcal/d is an integral part of any weight loss program aimed at achieving a safe rate of 0.5-1 kg/week."

固定 500-1000 kcal 赤字是历史最常用方案,但更精准的做法是按**体重比例设定赤字**:
- 实际 RCT 数据显示,500 kcal 赤字在研究环境中普遍难以精确执行
- ACSM(2009 Position Stand)建议:通过饮食赤字 + 运动消耗共同实现目标赤字,单纯饮食减少不超过 750 kcal/天(以防止基础代谢适应过强)

**赤字安全底线**

NIH 指南设定最低摄入量保护:
- 女性:≥ 1,200 kcal/天
- 男性:≥ 1,500 kcal/天

低于此值可能引起营养缺乏和肌肉加速分解。

**→ 对 Plan Skill 的映射**:
- `daily_calorie_range` 计算路径:估算总日能量消耗(TDEE)→ 设定赤字(Phase 1: -300 至 -400 kcal;Phase 2: -400 至 -600 kcal)→ 校验不低于性别对应最低值
- 赤字应作为范围(如 350-500 kcal/天),而非精确单一值,留给用户一定弹性
- Phase 1 赤字故意设置较小(-300 kcal),目的是建立习惯,而非最大化减脂速率

---

### 3.3 训练频次 —— 减脂阶段的最低有效剂量

**抗阻训练**

ACSM 力量训练指南(*Medicine & Science in Sports & Exercise*, 2009, Position Stand):
> "Progressive resistance exercise on **2 or 3 nonconsecutive days per week**, involving 8-10 muscle groups per session."

2022 年系统综述与元分析(Lopez et al., *Obesity Reviews*, PMC9285060, 114 项试验, 4,184 名参与者):抗阻训练 + 热量限制联合干预是改善体脂率和脂肪量效果最显著的方案(体脂率 ES = -3.8%, 体脂量 ES = -5.3 kg)。

**有氧训练**

ACSM 2009 Position Stand(PMID 19127177):
- 防止体重增加:150-250 分钟/周中等强度有氧
- 产生适度体重损失(约 2-3 kg):>150 分钟/周
- 产生临床显著体重损失(5-7.5 kg):>225-420 分钟/周

**→ 对 Plan Skill 的映射**:
- `weekly_training_count` 最小值建议 **2 次**(对应 ACSM 力量训练最低有效频次)
- 对于完全未运动用户,Phase 1 建议 2 次/周,Phase 2 升为 3 次/周,Phase 3 维持或个体化
- 训练类型不需要极度精细——Plan Skill 只定义频次与基本类型(力量/有氧),具体动作交给 Coach 对话
- 如用户有时间约束,有氧可通过日常步行(NEAT 活动)补充,无需额外训练课

---

### 3.4 睡眠与减脂 —— 因果链证据

**关键研究:Nedeltcheva 等(2010)**

Nedeltcheva, Kilkus, Imperial, Schoeller & Penev, *Annals of Internal Medicine*, 153(7), 435-441, 2010(PMC2951287):
- 10 名超重成人,交叉实验,14 天热量限制 + 8.5 小时 vs 5.5 小时睡眠
- **睡眠减少使减脂比例降低 55%**(脂肪损失:8.5h 组 1.4 kg vs 5.5h 组 0.6 kg)
- **去脂体重损失增加 60%**(5.5h 组反而多损失肌肉 1.5 vs 2.4 kg)
- 伴随增强的神经内分泌适应和饥饿感上升

**Papatriantafyllou 等系统综述(2022)**(*Nutrients*, 14(8), 1549, PMC9031614):
- 睡眠不足(≤6 小时)导致每日额外摄入 **200-500 kcal**(通过增加夜间零食,以高脂高糖食物为主)
- 瘦素(leptin)降低 + 生长素释放肽(ghrelin)升高 → 饥饿感上升、饱腹感下降
- 肥胖风险与睡眠不足(≤7 小时)的关联已被大型流行病学研究确认

**Tasali 等(2022)**(*JAMA Internal Medicine*):延长睡眠时间干预研究,睡眠延长后能量摄入显著下降(约 270 kcal/天),体重轻微改善。

**→ 对 Plan Skill 的映射**:
- `daily_rhythm` 应将"睡眠目标"纳入规范,建议 **7-9 小时**作为标准范围
- 睡眠不达标应与当日营养/运动目标解耦——不因睡眠差就追加补偿训练
- contingency 中可新增:连续 3 天睡眠 <6 小时 → 当日训练强度降级、热量目标放宽 100-150 kcal(预防补偿性暴食)

---

## 四、权威机构指南摘要

### 4.1 NICE(英国国家卫生与临床优化研究所)—— NG246(2024)

**发布背景**:NG246(*Overweight and Obesity Management*, 2024)整合并替代此前多份肥胖相关 NICE 指南,是当前英国体重管理临床实践的最权威综合性文件。

**核心结构转变**:
- 从层级式转诊体系转向**"以个体为核心的整合式服务"**
- 强调个性化评估而非统一阶梯治疗
- 三类服务层次:通用服务(健康促进/初级保健)→ 行为干预服务 → 专科服务

**行为干预关键建议**:
- 鼓励目标设定(goal-setting)与自我监测(self-monitoring)以追踪进展
- 多成分行为干预(饮食咨询 + 运动 + 行为治疗联合)优于单一干预
- 避免评判性语言,强调非体重指标的健康结果

**→ 对 Plan Skill 的映射**:
- Plan 生成后应包含非体重指标(如精力、睡眠质量、体能)作为辅助追踪,与 NICE 方向一致
- Plan 语言应无评判——数值范围而非精确值,避免"你必须"式指令

---

### 4.2 USPSTF(美国预防服务工作组)—— 2018 B 级推荐

**核心推荐**:
> 对 BMI ≥30 的成人,建议**提供或转介至强化多成分行为干预**(B 级推荐,即净收益中等)。

**强化多成分行为干预的定义**:
- 第 1 年至少 12 次会话(含个体 + 小组)
- 覆盖:健康饮食选择辅导 + 运动增加 + 行为治疗(目标设定、自我监测、问题解决)

**证据强度**:
- 强化干预可产生**临床显著的体重改善**
- 行为干预本身几乎无副作用(noninvasive, no significant harms reported)

**→ 对 Plan Skill 的映射**:
- "12 次以上结构化接触"的密度要求印证 Voliti 的每日 Coach 接入逻辑(Plan 作为每次接触的结构骨架)
- Plan 应是支持"自我监测"的工具,而非替代用户判断的系统——`process_goals` 的 `days_met` 跟踪正是自我监测的操作化

---

### 4.3 AHA(美国心脏协会)—— 2021 饮食指南科学声明

**发布**:*Circulation*, 2021(PMID 34724806)

**与减脂方案直接相关的建议**:
- 能量摄入与消耗平衡,配合每周 **≥150 分钟中等强度有氧或 75 分钟高强度有氧**
- 以食物模式(dietary pattern)而非单一营养素为单位制定建议
- 限制添加糖(与体重增加、2 型糖尿病、心血管病风险直接关联)
- 优选液态植物油,限制饱和脂肪

**→ 对 Plan Skill 的映射**:
- `daily_rhythm` 中的饮食规范应以"食物类型优先级"表述(优先蔬菜/蛋白质,控制精制碳水/添加糖),而非精确宏量克数——与 AHA 以食物模式为核心的理念一致

---

### 4.4 ACSM(美国运动医学会)—— 运动处方

**核心立场**:
- **减重目标**:>250 分钟/周有氧运动,产生临床显著减重(约 5-7.5 kg)
- **体重维持**:>250 分钟/周
- **防止体重增加**:150-250 分钟/周
- **抗阻训练**:2-3 次/周,非连续日,每次 8-10 肌群,2-4 组 × 8-12 次

**重要说明**:ACSM 明确"抗阻训练本身不产生显著体重减少,但增加去脂体重、减少脂肪量,并与心血管代谢健康改善相关"——即抗阻训练的价值在于体成分改善,而非数字下降。

**→ 对 Plan Skill 的映射**:
- Plan 中向用户解释训练价值时,应强调"体成分改善 + 代谢健康"而非"秤上数字"
- `weekly_training_count` 最小值 = 2(ACSM 抗阻训练底线),建议值 = 3(结合有氧与力量)

---

### 4.5 中国营养学会 / 中华医学会 —— 中国人群特定建议

**中国居民膳食指南(2022, 中国营养学会)**:

| 指标 | 建议值 |
|------|--------|
| 成人蛋白质日摄入(普通) | 约 1.0 g/kg/天 |
| 65 岁以上 | 约 1.2 g/kg/天 |
| 高质量蛋白质比例 | >50% 总蛋白质 |
| 运动频率 | ≥5 天/周中等强度, ≥150 分钟/周 |
| 每日步数 | 6,000-10,000 步(具体活动量补充) |

**超重/肥胖医学营养治疗指南(中华医学会, 2021, PMID 36173217)**:
- 医学营养治疗是肥胖全病程基础干预,贯穿任何阶段
- 推荐低热量饮食(LCD:1000-1500 kcal/天)作为基础热量方案,而非超低热量饮食(VLCD, <800 kcal)
- 蛋白质推荐占总热量的 15-25%(大体重人群向 25% 靠近)

**中国人群体成分特征注意**:
- 中国人在相同 BMI 下体脂率和内脏脂肪比例高于西方参照值
- 健康 BMI 上限(对中国人群)为 23.9(vs 西方 24.9)

**→ 对 Plan Skill 的映射**:
- 蛋白质目标对中国普通用户应设在 1.2-1.8 g/kg/天(高于 CNS 基准,低于 ISSN 力量运动员建议),兼顾本土合理性与减脂保肌需求
- 热量下限参考中华医学会 1000 kcal(但实际执行中不应低于 1200 kcal 以确保营养完整性)
- 日常活动目标可以步数量化(6000-10000 步),作为训练以外的 NEAT 补充

---

## 五、反面教训 —— 应规避的设计陷阱

### 5.1 Streak(连续天数)游戏化的副作用

**理论机制:过度理由化效应(Overjustification Effect)**

Deci & Ryan 认知评价理论(CET)与 Lepper 等(1973)经典研究表明:**对原本具有内在价值的行为施加外部奖励(积分/徽章/streak),若被用户感知为"控制性",将侵蚀内在动机**。

Decision Lab 分析("Streak Creep: The Perils of Too Much Gamification")总结:
- Streak 特性在初期(1-2 周)显著提升参与度
- 但随时间推移,用户开始为"保 streak"而非"真正想改变"而行动
- 一旦 streak 断裂,容易引发弃用("反正已经 0 了")

ADHD 用户与神经多样性群体研究(Klarity Health, 2024):streak 特性对 ADHD 用户造成额外焦虑、回避与最终弃用。

**游戏化教育领域证据**

Frontiers in Education(2024):"ghost effect"研究——游戏化可能产生"表演性参与"(perfunctory engagement),不产生真正的认知或行为改变;Springer(2023)元分析:游戏化提升学生自主性和关联感,但对胜任感影响有限,且可能侵蚀内在动机。

**→ 对 Plan Skill 的映射**:
- Plan 不得包含任何 streak 计数、连续达标天数、"N 天连续完成"等语言
- `days_met / days_expected` 字段用于结构化评估(是否在轨),不转化为用户可见的"连续天数"展示
- 阶段切换不应以"连续达标"为条件,而应以"整体轨迹在合理区间内"为标准

---

### 5.2 全有全无思维(All-or-Nothing Thinking)与失控螺旋

**临床证据:弃权违规效应(Abstinence Violation Effect, AVE)**

AVE 由 Marlatt & Gordon(1985)首次描述于成瘾治疗领域,随后被应用于饮食行为和减脂依从性研究。

Grilo & Shiffman(*Addictive Behaviors*, 1994, ScienceDirect)的超低热量饮食(VLCD)研究(76 名患者, 11 周随访):
- 41/76 患者报告了至少一次饮食违规
- 对违规行为做出"性格归因"(AVE 高)的患者,最终减重量显著低于做出"情境归因"的患者
- **"AVE 程度解释了超出初始肥胖程度之外的显著额外体重变化方差"**

Psychology Tools 资料库(*All-or-Nothing Thinking*):全有全无思维使用户将部分失败视为完全失败,触发"反正已经破了就算了"的补偿行为,加剧失控螺旋。

用户研究印证(Voliti docs/07_User_Research.md):55% 的反复尝试者一次失控即演变为 2-3 天崩溃,这正是 AVE 的产品层表现。

**→ 对 Plan Skill 的映射**:
- Plan 的 contingency 设计应**明确拒绝补偿式规则**("今天超了 400 卡,明天减少 400 卡")——这类规则强化 AVE
- 失控后的首要任务:复原认知资源(cognitive-reframing 干预接入),而非立即重新执行计划
- Phase 转场不应因一次失控而重置计时——连续性是习惯形成的关键,短暂中断不等于阶段失败
- 语言设计:Plan 中不出现"你必须每天达标"式表述,改为"这一周大部分天达标即为在轨"

---

### 5.3 过度精细化饮食记录与饮食失调风险

**关键研究:MyFitnessPal 与饮食失调**

Troscianko & Wade(*Eating Behaviors*, 2017, PMC5700836, PMID 28843591)研究 105 名饮食失调确诊患者:
- **约 75% 曾使用 MyFitnessPal**
- **73% 认为该应用助长了其饮食失调**
- **30% 认为该应用"非常显著地"促成了其饮食失调**

Ridolfi 等(*Eating Behaviors*, 2021, PMID 34543856)研究卡路里追踪应用使用动机:
- 以体重控制/体型为动机使用者,更可能报告:食物先占(food preoccupation)、全有全无思维、食物焦虑、补偿行为
- 以健康/疾病预防为动机使用者:上述风险均较低

Ozier 等(*PMC*, 2021, PMC8485346)定性研究八大负面结果主题:
> 数字固着、刚性饮食、强迫性执行、应用依赖、极端情绪、负面消息驱动、过度竞争、高度自我要求感

**重要细分证据**

Christoph 等(*Journal of Academy of Nutrition and Dietetics*, 2021):饮食失调低风险的大学生样本中,1 个月 MFP 使用**不显著增加饮食失调风险**——表明个体脆弱性是关键调节变量,精细记录本身不一定有害,有害的是将数字与自我价值绑定。

**→ 对 Plan Skill 的映射**:
- Plan 的营养目标以**范围而非精确值**呈现(1600-1800 kcal,而非"1724 kcal")
- Plan 不要求克级精度的食物记录——鼓励"份量目标"(一份拳头大的蛋白质,两份蔬菜)作为替代
- `daily_calorie_range` 字段名本身已体现"范围"概念,写入时宽度至少 200 kcal
- Plan 生成后应显式说明"这是参考范围,不是精确指令",去除完美执行的隐性期待

---

## → 对 Plan Skill 字段设计的综合建议

以下将上述全部研究证据直接映射到 Plan Skill 的核心字段决策:

### phases 数量:建议 3 段

**依据**:
- TTM 三主要行为阶段(Action Entry → Action Deepening → Maintenance)与三段式最为自然对齐
- MATADOR 研究证明间歇式结构(攻坚期 + 恢复期轮替)优于单一连续减脂
- Matveyev 周期化的中循环结构在运动科学中验证了"准备-竞争-恢复"三段范式
- 4 段以上会使用户对"在哪个阶段"产生认知负担;2 段无法体现"适应期"的特殊性

**建议时长**:
- Phase 1(适应期):3-5 周(覆盖 Lally 习惯形成最不稳定的前 18-21 天,赤字保守)
- Phase 2(主攻期):4-8 周(最大赤字窗口,MATADOR 表明 8 周左右是连续限制的合理上限)
- Phase 3(维持/稳固期):≥4 周(至少覆盖一轮习惯检验周期)

---

### process_goals 数量:精确 3 个

**依据**:
- Locke-Latham 目标设定理论:目标数量过多(>3-4 个)导致注意力分散,每个目标的依从性均下降
- Voliti 现有架构已固定 Chapter = 3 个 process_goals,Plan Skill 的 process_goals 字段应与此保持一致,不创造额外摩擦
- 三维度建议:① 饮食热量/蛋白质管理 ② 运动行为 ③ 睡眠/压力管理(对应 SDT 胜任感的递进建构)

---

### contingency 格式:严格 if-then

**依据**:
- Gollwitzer & Sheeran(2006)元分析:d = 0.65 效应量来源之一正是"if-then 格式 vs 仅 goal intention"的对比
- 效果在"高动机 + 预先规划"条件下最大——Plan Skill 生成的 contingency 应在用户高动机时(Onboarding / Phase 开始)就预设
- 每条 contingency 应包含:**触发条件(If: 情境描述)+ 具体响应(Then: 行为指令)**
- 不应写成建议性语言("你可以考虑……"),而是陈述性指令("这种情况下, [具体做法]")

---

### daily_calorie_range 宽度:≥200 kcal

**依据**:
- 避免过度精细化记录的饮食失调风险(Troscianko 2017, Ridolfi 2021)
- NIH 赤字区间本身就是范围(500-1000 kcal),对应每日摄入的弹性空间
- 范围宽度不宜超过 400 kcal(避免"随便吃也合规"的误解)

---

### daily_protein_grams_range 计算基础

**依据**:
- ISSN(2017):减脂期抗阻训练者 2.3-3.1 g/kg,一般运动者 1.4-2.0 g/kg
- CNS(2022):中国普通成人约 1.0 g/kg(底线参考,非减脂期特定建议)
- 实用建议区间(Voliti 用户画像, 25-40 岁, 轻度至中度运动):**1.4-2.0 g/kg/天**,以用户实际体重(非目标体重)计算

---

### weekly_training_count 最小值:2

**依据**:
- ACSM Position Stand(2009):抗阻训练 2-3 次/周(非连续日)是改善体成分的有效最低剂量
- 低于 2 次/周,抗阻训练刺激不足以维持肌肉量
- 建议 Phase 2 提升至 3 次/周,Phase 3 维持 2-3 次/周(个体化)

---

### 睡眠目标:纳入 daily_rhythm,建议 7-9 小时

**依据**:
- Nedeltcheva 等(2010, *Annals of Internal Medicine*):睡眠不足将减脂效率降低 55%,且增加 60% 去脂体重损失——影响与热量赤字管理同等量级
- Papatriantafyllou 等(2022):睡眠不足每日额外摄入 200-500 kcal,抵消大部分人为的热量赤字努力
- 睡眠是最低成本、最高回报的减脂辅助因素,应在 daily_rhythm 中明确设定

---

### 平台期预案:Phase 之间内置"恢复窗口"

**依据**:
- MATADOR(2017):2 周间歇性能量平衡期显著减少代谢适应(-360 vs -749 kJ/day 代谢抑制)并产生更大总脂肪损失
- 建议在 Phase 1→2 和 Phase 2→3 过渡时各设置 **1-2 周恢复窗口**(热量目标提升至维持水平)
- 恢复窗口应在 Plan 生成时就向用户预告,而非在平台期出现后"临时补救"(符合 Implementation Intentions 的提前规划精神)

---

## 参考文献与来源

- Stages of Change Theory · StatPearls · NCBI Bookshelf (NBK556005)
- Transtheoretical model stages of change for dietary and physical exercise modification in weight loss · PMC10088065
- The transtheoretical model is an effective weight management intervention: a randomized controlled trial · PMC7216547
- New Directions in Goal-Setting Theory · Locke & Latham (2006)
- The Association Between Goal Setting and Weight Loss · PMC10357317
- Adherence to self-monitoring and behavioral goals · PMC11897847
- Implementation Intentions and Goal Achievement: A Meta-Analysis · Gollwitzer & Sheeran (2006)
- The When and How of Planning: Meta-Analysis of 642 Tests · European Review of Social Psychology (2024)
- How long does it take to form a habit? · Lally et al. (2010)
- Self-Determination Theory and the Facilitation of Intrinsic Motivation · Deci & Ryan (2000)
- Intermittent energy restriction improves weight loss efficiency: the MATADOR study · PMC5803575
- Effects of intermittent dieting with break periods on body composition: systematic review · PubMed 38193357
- ACSM Position Stand: Appropriate physical activity intervention strategies for weight loss · PubMed 19127177
- ISSN Position Stand: Protein and exercise · PMC5477153
- Insufficient sleep undermines dietary efforts to reduce adiposity · Nedeltcheva et al. (2010) · PMC2951287
- Sleep Deprivation: Effects on Weight Loss and Weight Loss Maintenance · PMC9031614
- NICE Overweight and Obesity Management NG246
- USPSTF Weight Loss Behavioral Interventions Recommendation
- 2021 AHA Dietary Guidance to Improve Cardiovascular Health · Circulation
- Chinese Dietary Guidelines 2022 · Chinese CDC
- Guidelines for medical nutrition treatment of overweight/obesity in China (2021) · PubMed 36173217
- My Fitness Pal Calorie Tracker Usage in the Eating Disorders · PMC5700836
- The abstinence violation effect and very low calorie diet success · ScienceDirect
- Streak Creep: The Perils of Too Much Gamification · The Decision Lab
- Management of Weight Loss Plateau · StatPearls · NCBI NBK576400
- Resistance training effectiveness on body composition: meta-analysis 2022 · PMC9285060

---

## 变更记录

| 日期 | 内容 |
|------|------|
| 2026-04-19 | 初始创建:覆盖行为改变理论、减脂周期化、营养训练、权威指南、反面教训五个维度 |
