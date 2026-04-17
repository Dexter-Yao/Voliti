---
type: source
author: Charlie Guo
published: 2026-02-11
source_url: https://developers.openai.com/blog/skills-shell-tips
topics:
  - "[[skills]]"
  - "[[shell]]"
  - "[[compaction]]"
  - "[[long-running agents]]"
  - "[[agentic AI]]"
created: 2026-04-10
updated: 2026-04-10
---

# OpenAI长程Agent的Skills、Shell、Compaction协同

## 一句话简介

这篇文章说明 OpenAI 如何把长程 Agent 的三类核心能力拆成 [[skills]]、[[shell]] 与 [[compaction]]：前者负责把稳定流程打包成可重用手册，中间负责让模型在真实计算环境中执行命令和产出文件，最后负责让长任务在上下文增长后仍能持续运行。

## Takeaway

1. 对长程 Agent 而言，真正可复用的基础设施不是“大而全的 system prompt”，而是 `skills = procedure`、`shell = execution`、`compaction = continuity` 这三层分工。
2. 文中的 [[shell]] 不是抽象“工具调用”概念，而是一台可操作的终端环境。模型可以像初级工程师一样在其中安装依赖、运行脚本、读写文件并留下 artifact，因此“能不能执行”与“能不能回答”是两件不同的事。
3. 一旦 Agent 进入生产环境，关键问题立刻变成流程路由、上下文续航、artifact 边界与网络安全，而不是单轮提示词写得多漂亮。

---

## 摘要

### 文章要解决的问题

文章的出发点是：AI 正从单轮问答走向长时间运行的 Agent，这类 Agent 不只是回答一个问题，而是要持续读取资料、处理数据、修改文件、生成交付物。作者认为，当任务长度和复杂度上升后，纯 prompt 方式很快会暴露三个问题：流程容易漂移、执行能力不足、上下文会耗尽。因此，OpenAI 将长程 Agent 的关键能力拆成三个原语：[[skills]]、[[shell]] 与 [[compaction]]。

### Skills：把稳定流程从 prompt 中拆出来

文章把 [[skills]] 定义为“模型按需加载的 procedures”。一个 skill 不是一句提示词，而是一组文件加上 `SKILL.md` 清单，其中写明触发条件、工作步骤、边界、模板和示例。平台会先把 skill 的 `name`、`description` 和 `path` 暴露给模型，模型再基于这些元信息决定要不要调用它；只有决定调用时，才真正读取 `SKILL.md`。

作者的核心主张是：skill 的 description 不应写成宣传文案，而应写成路由逻辑。它至少要回答三个问题：什么时候该用、什么时候不该用、成功输出长什么样。文中还特别强调负面示例与边界条件，因为多个 skill 并存时，模型很容易误触发。Glean 的经验是，skills 刚接入时触发准确率曾下降约 20%，后来通过补充“不要在什么情况下调用”与边界案例，才把触发效果拉回去。

文章还反复强调，应把模板和 worked examples 放进 skill，而不是塞进系统提示词。原因很直接：这些内容只有在 skill 真被调用时才会装入上下文，平时不会为无关请求消耗 token。这让 skill 变成一种“按需加载的工作手册”，既保留示例密度，又避免 system prompt 变成难维护的巨型文档。

### Shell：让模型真正进入可执行环境

这里的 [[shell]]，如果用非计算机背景更容易理解的说法，可以把它当成“文字版的电脑操作台”或“命令行工作台”。普通聊天模型只能描述“应该怎么做”；而 shell 让模型进入一个真实的终端环境，可以直接下命令、安装程序、运行脚本、读写文件，并把产出留在磁盘里。也就是说，模型不再只是“给建议”，而是开始“动手做事”。

对没有技术背景的读者，`terminal` 或 `shell` 可以理解成一种不用鼠标点图标、而是通过输入命令操作电脑的界面。人在这个界面里可以让电脑执行明确动作，比如下载依赖、处理一批文件、调用 API、生成报告。文章要强调的是：一旦模型接入 shell，它获得的不是“多一个回答问题的知识点”，而是“多了一台可被指挥的执行环境”。因此，shell 是执行层（execution），不是推理层的简单延伸。

作者把 shell 分成两种运行方式。第一种是 OpenAI 托管的 hosted container，也就是 OpenAI 帮你准备好隔离的计算环境；第二种是 local shell mode，由开发者自己在本地机器上执行同样语义的 shell 调用。两者的重要共同点是：模型面对的是相同的工具抽象，所以工作流可以先在本地快速迭代，再迁移到托管环境获得更稳定、更可复现的执行结果。

文章给了几个很具体的 shell 使用原则。第一，要把 `/mnt/data` 视为 artifact 的交接边界：报告、清洗后的数据、电子表格等最终产物都应写到这里，方便后续检索、审阅和传递。作者给出的心智模型很简洁：

> "tools write to disk, models reason over disk"

第二，要理解 shell 让 Agent 具备了真正的“做事”能力，因此安全边界必须同步收紧。网络访问不应默认大开，而应只对当前任务最少量放行。第三，本地与云端最好共享同一套 API 语义，这样工作流本身不会因运行位置变化而重写。

### Compaction：让长任务不停线

文章把 [[compaction]] 定义为长任务的连续性机制。随着对话越做越长，上下文窗口一定会逼近极限；如果没有压缩机制，Agent 迟早会丢失前文、重启流程，或因上下文溢出直接中断。为此，Responses API 提供两种处理方式：一种是 server-side compaction，在上下文超过阈值时自动压缩；另一种是独立的 `/responses/compact` endpoint，给开发者显式控制压缩时机。

作者的立场很明确：compaction 不应该被当作“快撑不住时的补救手段”，而应被视为长程工作流的默认原语。文中的建议是，把 container reuse、`previous_response_id` 和 compaction 一起纳入最初设计，而不是后期打补丁。原因在于，长程 Agent 很少能靠一次性提示稳定完成工作；只有把连续性视作系统能力，才可能减少“重新开始”的行为。

### 三者为何要一起设计

文章最重要的判断之一，是三者不是可替换关系，而是分工关系。[[skills]] 负责把流程、守则、模板、示例稳定下来；[[shell]] 负责让模型真的运行命令、处理文件、产出 artifact；[[compaction]] 负责让整个过程在多轮、多步骤、多文件的长链条里不崩。

作者认为，如果没有 skill，prompt 会越来越像“意大利面”一样纠缠；如果没有 shell，模型再聪明也只能停留在建议层，无法真正执行；如果没有 compaction，再好的流程也跑不长。三者一起使用时，才会形成“可复用流程 + 真实执行 + 长程续航”的闭环。

### 十条操作建议的实际含义

文章的十条 tips 可以整理成四组更容易记忆的原则。

第一组是“让 skill 更容易被正确调用”。包括把 description 写成路由条件、补充负面示例、把模板和示例放进 skill 内部。核心目的都是减少误触发和 prompt 膨胀。

第二组是“从一开始就按长任务设计”。包括复用 container、传递 `previous_response_id`、默认启用 compaction。这里体现的是一种长程工程观：不要假设一次调用就能完成复杂任务，要假设任务会跨多个步骤持续推进。

第三组是“把生产边界写清楚”。这包括在需要确定性时直接告诉模型：

> "Use the `<skill name>` skill."

还包括把 `/mnt/data` 作为统一交付边界，以及把网络访问拆成组织级 allowlist 与请求级 allowlist 两层。作者特别提醒：skills 和 networking 组合在一起时，数据外泄风险显著上升，所以必须把允许访问的域名范围收得很窄。

第四组是“让认证信息不进入模型上下文”。如果某个允许访问的域名需要鉴权，文章建议使用 `domain_secrets`。模型只会看到类似 `$API_KEY` 的占位符，真正密钥由外部系统在发往已批准域名时注入。这样可以降低凭证泄露风险。

### 三种 build pattern

文章最后给出三种组合模式。

Pattern A 是最基础的“安装依赖 -> 获取数据 -> 写出 artifact”。这说明 hosted shell 的最低价值并不是“更聪明”，而是能稳定地产出一个可交付文件，例如报告或清洗后的数据。

Pattern B 是“skills + shell” 的重复性工作流。适合那些已经验证过一次，但随着 prompt 漂移会逐渐失真的任务，例如表格分析、数据清洗加总结、标准化报告生成。这里 skill 的作用是把做法固定住，让 shell 每次按同一套流程干活。

Pattern C 更偏企业场景。文章提到 Glean 的实测案例：面向 Salesforce 的某个 skill 把 eval accuracy 从 73% 提升到 85%，同时把 time-to-first-token 降低 18.1%。作者借这个例子想说明，skill 在企业里可以逐步变成“活的 SOP”，随着组织演进不断更新，并由 Agent 稳定执行。

### 文章的总体结论

文章最后把三者的关系压缩成一句很清楚的分工：用 [[skills]] 编码 how，用 [[shell]] 完成 do，用 [[compaction]] 保持长流程的连贯性。开发上建议先从本地开始，便于快速迭代和调试；等流程稳定后，再迁移到托管 container 获取隔离性、可复现性和部署一致性。与此同时，网络开放范围要始终保持最小化，并配合 allowlist 与 `domain_secrets` 控制风险。

---

## 参考链接

- [Shell + Skills + Compaction: Tips for long-running agents that do real work](https://developers.openai.com/blog/skills-shell-tips)
  - 作者：Charlie Guo
  - 发布日期：2026-02-11

## 相关笔记

- [[2026-02-08 - 长时间运行Agent的上下文管理与弹性设计]]（Anthropic 对长程 Agent 的 compaction、结构化记忆与弹性恢复给出平行参照，能和本文形成对读）
- [[2026-03-09 - OpenAI Harness Engineering Agent优先工程实验全景]]（从工程组织与环境设计视角解释 OpenAI 为什么把 Agent 基础设施做成可组合原语）
- [[2026-03-10 - 以 Skills 为核心的领域 AI 产品形态]]（把本文对 skills 的工程定义推进到产品层，解释 skill 为什么会成为领域 AI 的能力载体）
- [[2026-03-16 - Context Layer的两种形态可编码知识与执行涌现知识]]（把本文中的 skills、shell 与 compaction 视作 context 进入执行系统时的分层原语）
- [[2026-04-01 - 打造 AI Agent 员工的操作方法论]]（把本文的 skills、shell、shared state 与安全边界进一步转译为可部署的数字员工操作方法）
