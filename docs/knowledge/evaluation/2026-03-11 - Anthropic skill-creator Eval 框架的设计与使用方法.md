---
type: source
author: Anthropic
published: 2026-03-03
source_url: https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
topics:
  - skills
  - evaluation
  - Claude Code
  - LLM
  - agent
created: 2026-03-11
updated: 2026-03-11
status: active
canonical: false
---

# Anthropic skill-creator Eval 框架的设计与使用方法

## 一句话简介

Anthropic 于 2026 年 3 月在官方 skill-creator 中内置了完整的 Eval 测试框架，将软件单元测试范式引入 Skill 开发，使开发者能通过结构化测试用例和 with-skill/baseline 并行对比，量化验证 Skill 是否真正有效。

## Takeaway

1. **消除"感觉有效"与"实际有效"的混淆是此次更新的核心价值**：没有 Eval，Skill 的每次迭代依赖直觉判断；有了 Eval 框架，每次修改都能以 pass rate 量化验证效果，与 OpenAI Cookbook 提出的"以证据链替代感觉"原则完全一致。
2. **同步运行 with-skill 和 baseline 是框架设计的强制要求**：官方文档明确规定必须在同一轮（same turn）并行启动两组子代理，先跑 with-skill 再补 baseline 会引入时间差，影响对比有效性。
3. **Eval 框架不适用于主观类技能**：写作风格、设计质量等依赖人类判断的 Skill，官方建议以人工定性评审为主，不强制设计断言式测试。

---

## 摘要

### 背景与设计动机

Anthropic 在 2025 年 10 月推出 Agent Skills 后，Skill 开发者面临一个长期未解决的问题：无法可靠地验证一个 Skill 在模型更新后是否仍然正确执行，触发率是否稳定，以及某次修改是否真正带来了改进而非退化。此前官方指南建议的"测试方法"本质上是人工运行若干查询并凭直觉打分，存在显著的主观性。

2026 年 3 月的更新将 skill-creator 从"写指令的工具"升级为包含测试与迭代循环的完整开发环境，使 Skill 开发从感性迭代转向可验证的工程实践。

### 两类 Skill 的战略分类

官方文档对 Skill 提出了两类战略分类，直接影响开发者对投资方向的判断：

**Capability Uplift Skills**（能力补足类）：补足当前模型不擅长的功能，例如 PDF 处理、PowerPoint 生成、结构化数据提取。这类 Skill 有"退休日期"（retirement date）——随底层模型原生能力提升，这类 Skill 会被取代，需定期通过 Benchmark 验证其是否仍有价值。

**Encoded Preferences / Workflow Skills**（编码偏好类）：固化组织特定的业务规则、工作流程和操作偏好，例如代码审查规范、NDA 检查清单、特定格式的报告模板。这类 Skill 随模型改进价值递增——模型越强，执行嵌入式规则越可靠，不存在被原生能力淘汰的风险。

### Eval 循环的完整流程

完整的 Eval 循环由五个阶段组成，形成一个可重复的迭代环：

#### 阶段一：写测试用例（不含断言）

在 Skill 草稿完成后，准备 2–3 个真实用户会发出的测试提示，保存至 `evals/evals.json`。此阶段不写断言——断言在运行进行中并行草拟：

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "用户的实际任务提示",
      "expected_output": "期望结果的描述",
      "files": []
    }
  ]
}
```

#### 阶段二：并行启动 with-skill 和 baseline 两组子代理

官方文档的强制要求：必须在同一轮（same turn）同时启动两组子代理，不允许先运行 with-skill 再补充 baseline。

- **With-skill 组**：加载目标 Skill，输出保存至 `<workspace>/iteration-N/eval-ID/with_skill/outputs/`
- **Baseline 组**（按场景选择）：
  - 新建 Skill 时：不加载任何 Skill，保存至 `without_skill/outputs/`
  - 改进已有 Skill 时：加载旧版本快照（先执行 `cp -r <skill-path> <workspace>/skill-snapshot/`），保存至 `old_skill/outputs/`

每个测试目录同时写入 `eval_metadata.json`，断言字段初始为空数组。

#### 阶段三：运行进行中草拟断言

等待子代理运行期间，草拟每个测试用例的断言并向用户解释。好的断言具备两个特征：客观可验证，且名称在报告中直接可读（名称描述要清晰到让读者一眼理解它在检验什么）。

支持的断言类型：

| 类型 | 说明 |
|------|------|
| `regex` | 正则匹配，验证特定模式存在于输出中 |
| `negative_regex` | 验证不希望出现的模式确实缺失 |
| `inclusion` | 验证特定文本包含于输出中 |
| `skill_not_called` | 验证不应触发的场景确实未触发（负例控制） |

复杂逻辑验证推荐 Model-as-a-Grader；结构性检查使用 regex。官方明确指出：主观类技能（写作风格、设计质量）不强制断言，以人工定性评审为主。

#### 阶段四：捕获计时数据

每个子代理完成时，任务通知中包含 `total_tokens` 和 `duration_ms`，必须立即保存至对应目录的 `timing.json`。官方文档明确指出："这是唯一能捕获该数据的时机"——不在通知到达时处理，数据将永久丢失。

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

#### 阶段五：评分、聚合与启动 Viewer

**评分（grading）**：生成每个运行目录的 `grading.json`。字段名必须严格使用 `text`、`passed`、`evidence`——Viewer 依赖这三个精确字段名，使用 `name`/`met`/`details` 等变体会导致 Viewer 无法正确渲染。

**聚合（benchmark）**：

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

生成 `benchmark.json` 和 `benchmark.md`，包含 with-skill 与 baseline 的 pass rate、耗时、token 用量对比（含均值 ± 标准差与 delta）。

**Analyst pass**：聚合后需进行一轮模式识别分析，重点识别：无判别力的断言（无论有无 Skill 均通过）、高方差的 eval（可能存在 flakiness）、时间与 token 的权衡点。

**启动 HTML Viewer**：

```bash
nohup python <skill-creator-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
```

Headless / 无显示环境使用 `--static <output_path>` 生成静态 HTML 文件；用户提交评审后生成 `feedback.json`（下载后复制到 workspace 目录供下次迭代使用）。

Viewer 包含两个 Tab：
- **Outputs Tab**：逐个 eval 展示提示 + 输出文件（内联渲染）+ 上次迭代对比（可折叠）+ 断言评分（可折叠）+ 用户反馈文本框
- **Benchmark Tab**：各配置 pass rate、耗时、token 汇总，含 per-eval 明细与 analyst 分析

### Trigger Tuning（触发器自动调优）

独立于 Eval 循环之外，用于优化 Skill description 的触发准确率。触发准确率指 Skill 在应触发时确实被加载的比例——description 写得过于模糊或过于狭窄都会导致触发失准。

流程：
1. 测试集按 60% / 40% 拆分为训练集与保留测试集
2. 每个查询运行 3 次，评估当前 description 的触发稳定性
3. 基于失败案例自动提出 description 改写建议
4. 在训练集和测试集上重新评估，最多迭代 5 轮
5. 生成最终 HTML 对比报告

官方数据：在 Anthropic 公开技能样本中，6 个里有 5 个经 Trigger Tuning 后触发准确率有所提升。

### 改进循环的两条核心原则

官方文档对改进（Improve）阶段给出两条明确指引：

> "从具体反馈中泛化。你们在反复迭代少数样本，因为这样更快。但如果 Skill 只对这些样本有效，它就没有价值。与其做精细的过拟合式修改，不如尝试不同的比喻和工作模式——代价低，可能有意外收获。"

> "保持 prompt 精简。阅读运行轨迹而不只是最终输出——如果 Skill 让模型做了大量无效工作，把造成这种情况的部分删掉。"

---

## 参考链接

- [skill-creator SKILL.md — anthropics/skills](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
  - 作者：Anthropic
  - 发布日期：2026-03-03

## 相关笔记

- [[2026-03-10 - 以 Skills 为核心的领域 AI 产品形态]]（Eval 机制是 Skill 产品护城河五层系统的第四层；本笔记提供该层的具体工程实现细节）
- [[2026-02-15 - OpenAI Cookbook Eval驱动系统设计方法论]]（「证据链替代感觉」是两套系统的共同哲学基础；OpenAI Cookbook 侧重通用 LLM 应用评估，本笔记聚焦 Skill 层的专项 Eval 实现）
- [[2026-02-08 - Agentic系统设计与评估驱动开发]]（「先写 Eval，再写 Agent」是 Agentic 工程的首要原则；skill-creator Eval 框架是这一原则在 Skill 开发场景中的具体落地）
