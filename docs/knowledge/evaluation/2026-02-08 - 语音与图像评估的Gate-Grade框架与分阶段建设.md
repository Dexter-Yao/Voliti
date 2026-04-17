---
type: source
author: OpenAI Cookbook Team
published: 2025
source_url: https://cookbook.openai.com/examples/realtime_eval_guide
topics:
  - voice evaluation
  - image evaluation
  - multimodal evaluation
  - Gate-Grade framework
  - Crawl-Walk-Run framework
created: 2026-03-01
updated: 2026-04-05
status: active
canonical: false
---

# 语音与图像评估的Gate-Grade框架与分阶段建设

## 一句话简介

OpenAI 两篇 Cookbook 实战指南分别针对语音/实时交互和图像生成/编辑场景，提供了从评估架构到具体评分标准的完整实践方法，核心洞察是多模态评估必须处理传统文本评估不存在的维度冲突。

## Takeaway

1. **语音评估有两个独立轴**：内容正确 ≠ 听起来正确，两者必须分别评估
2. **Crawl/Walk/Run 是语音评估的正确渐进路径**：从合成单轮开始，每次只增加一个复杂度维度——系统不能 crawl 就不要尝试 run
3. **转录不是真实值**：基于转录的评估会同时产生假通过和假失败，1-5% 的音频人工审计是必要补充
4. **图像评估的核心是 Gate + Grade**：先用 Pass/Fail 门控守住不可商量的正确性，再用 0-5 分级评估质量——此框架可泛化到所有需要区分"必须正确"和"最好优质"的评估场景
5. **品牌安全需要更严格的阈值**：Logo 编辑中 near-miss（接近正确）就是失败，从 ≥3 提升到 ≥4 反映了不同场景对错误的容忍度差异
6. **模态转换让困难判断变得可处理**：OCR 提取、裁剪局部检查将视觉判断转为文本/结构化数据
7. **Negative cases 是数据集中最容易遗漏也最关键的部分**：98% 准确率的升级检测因缺少"不应升级"案例而在生产中全面失败

---

## 摘要

### 一、语音与实时交互评估

#### 双轴评估模型

语音系统有两个独立的评估轴（OpenAI, 2025）：

- **内容质量（Content Quality）**：正确性、工具选择、指令遵循
- **音频质量（Audio Quality）**：自然度、韵律、发音、噪声下的稳定性

> "A response can be 'right' and still sound broken."（OpenAI, 2025）

两个轴是独立的：一个回答内容完全正确但音频断续、韵律不自然，对用户来说仍是失败体验。反之亦然。

#### Crawl/Walk/Run 渐进框架

一个象限结构，沿两个轴递增复杂度（OpenAI, 2025）：

| | 单轮 | 多轮 |
|---|---|---|
| **合成音频** | **Crawl**（最快迭代） | **Run**（测试鲁棒性） |
| **噪声/真实音频** | **Walk**（测试感知） | 手动端到端测试 |

- **Crawl（合成+单轮）**：最快迭代周期，聚焦路由和策略逻辑
- **Walk（噪声+单轮）**：订单号、姓名、地址在噪声音频上容易出错
- **Run（合成+多轮）**：完整工作流加工具 mock，测试上下文保持和状态管理

> "If your system cannot crawl, it will not run."（OpenAI, 2025）

#### 转录 ≠ 真实值

> "In realtime API, the ground truth for 'what the user said' is the actual audio signal."（OpenAI, 2025）

两类评估假象（OpenAI, 2025）：

- **假失败（False Fail）**：ASR 漏掉一个数字；模型实际听对了；LLM 评分器基于错误转录判定失败
- **假通过（False Pass）**：音频被截断；模型猜对了答案；真实问题被掩盖

缓解策略：通过 prompt 迭代和模型选择改善转录质量；在噪声转录（而非干净文本）上校准评分器；抽检约 1-5% 会话进行端到端音频审计。

#### 三构建块

**构建块 1：数据集**：从 10-50 个"黄金"种子用例开始，覆盖不能失败的核心流程。必须包含 negative cases——一个团队将升级检测优化到 98% 离线准确率，但上线后几乎对所有请求都触发升级，因缺少"不应升级"案例。三类数据集：回归套件 / 滚动发现集（生产中的新失败）/ 保留集。

**构建块 2：评分器层叠**：确定性评分器（工具调用验证、JSON 合法性）→ LLM 评分器（细微信号——正确性、指令遵循、恰当性）→ 音频评分器（静默时长、重叠检测、中断处理）。

**构建块 3：评估工具（Eval Harness）**：唯一职责是"make runs comparable"（使运行可比较）。单轮回放：保持完全相同的音频字节、预处理、VAD 配置；多轮：固定并版本化模拟器 prompt，确定性 mock 工具。

#### 关键洞察

投入评估的团队发布到生产的速度快 5-10 倍。手动审查仍不可替代——自动化低估轮换失败、韵律问题、转录不匹配。一家公司每天花约 3 小时听录音，发现了自动化遗漏的问题。

### 二、多模态图像评估

#### Gate + Grade 评分体系

两层评分结构（OpenAI, 2025）：

- **Gate（门控，Pass/Fail）**：不可商量的正确性——指令遵循、文字渲染准确性。任何 Gate 失败即整体失败
- **Grade（分级，0-5 分）**：质量维度——布局层次、风格品牌契合、视觉质量。所有 Grade ≥3 方可通过

策略：先 Gate 后 Grade——在正确性失败得到控制之前，不必关注质量优化。

> "A good vision eval does NOT score 'a pretty picture.' It scores whether the model is reliable for a specific workflow."（OpenAI, 2025）

#### 四场景评估标准

**场景 1：UI Mockup 生成**
- Gate：指令遵循、图内文字渲染
- Grade（0-5）：布局与层次、UI 可操作性渲染
- 通过标准：所有 Gate 通过 + 所有 Grade ≥3

**场景 2：营销图（传单/海报）**
- Gate：指令遵循、文字渲染准确性（精确拼写、标点、大小写）
- Grade（0-5）：布局与层次、风格与品牌契合、视觉质量
- 备选：OCR 提取文字，与要求文字集合比对

**场景 3：虚拟试穿（图像编辑）**
- Grade（0-5）：面部相似度、服装保真度、体型保持
- 通过标准：任何指标 ≤2 即失败，所有指标 ≥3 方可通过

**场景 4：Logo 编辑**
- Gate（0-5，高门槛）：编辑意图正确性、非目标不变性、字符与风格完整性
- 通过标准：所有指标必须 ≥4（严格阈值）

> "Logo editing is a precision task. Small errors matter. Near-misses are failures."（OpenAI, 2025）

品牌安全场景使用比一般场景更严格的阈值——从 ≥3 提升到 ≥4。

#### 图像评估的五个额外挑战

与文本评估相比，图像评估面临（OpenAI, 2025）：

1. **多维正确性**——硬约束（精确文字、数量、位置）与软约束（审美质量、品牌契合）混合
2. **保留约束**——编辑工作流要求近乎完美的非目标不变性
3. **空间推理**——必须判断布局、层次、编辑是否在边界内
4. **伪影检测**——细微扭曲（融化物体、断裂的手、文字涂抹）破坏可用性
5. **模态转换**——将视觉判断转为可处理的文本（OCR 提取、裁剪局部检查）

#### 模态转换技巧

当直接视觉判断困难时，将图像转换为可处理的文本形式（OpenAI, 2025）：

- **OCR 提取**：从生成的营销图中提取文字，与要求的文字集合比对
- **裁剪局部**：使用 Code Interpreter 裁剪特定区域进行近距离检查
- **结构化 JSON 输出**：让视觉模型以结构化格式输出判断，便于程序化处理

---

## 参考链接

- [OpenAI Cookbook: Realtime Eval Guide](https://cookbook.openai.com/examples/realtime_eval_guide)
  - 作者：OpenAI Cookbook Team
  - 发布日期：2025

- [OpenAI Cookbook: Image Evals](https://cookbook.openai.com/examples/multimodal/image_evals)
  - 作者：OpenAI Cookbook Team
  - 发布日期：2025

## 相关笔记

- [[2026-02-14 - LLM输出一致性与召回率最大化]]（补充多模态评估中的稳定性与召回率问题）
- [[Topic - LLM 评估体系]]（纳入多模态评估主题入口）
