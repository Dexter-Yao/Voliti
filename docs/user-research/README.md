# 用户研究

## 目录结构

```
user-research/
├── interviews/                          — 访谈记录（每人一份）
│   └── 2026-04-06-P01.md               — P01 直接访谈（男，30岁，知识工作者）
├── questionnaires/                      — 问卷调查
│   ├── raw/                             — 原始 Excel + Word 文件
│   ├── cleaned/                         — 清洗后数据集 + 分析报告
│   └── clustering/                      — 聚类分析脚本与结果
├── 01-user-research-synthesis.md        — 定性研究主报告（访谈 + 社媒）
├── 02-xiaohongshu-findings.md           — 小红书采集原始记录
├── 03-xiaohongshu-insights.md           — 小红书综合洞察
├── 04-reddit-findings.md                — Reddit 采集原始记录
├── 05-reddit-insights.md                — Reddit 综合洞察
├── README.md                            — 本文件
└── insights.md                          — 跨访谈洞察汇总（访谈 8 人以上后创建）
```

**综合报告入口：** [`docs/07_User_Research.md`](../07_User_Research.md)（融合定性与定量研究结论，约 1000 字）

## 阅读路径

**产品决策 / 快速了解**：读 [`docs/07_User_Research.md`](../07_User_Research.md)（综合报告）

**定性研究详细报告**：读 `01-user-research-synthesis.md`

内含：执行摘要、用户画像、行为细分、旅程地图、竞品分析、关键洞察、产品建议、待验证假设。

**深入某平台的原始数据**：
- 小红书 Profile 分析 → `02-xiaohongshu-findings.md`
- Reddit 原帖逐条分析 → `04-reddit-findings.md`

**平台级洞察（比主报告更详细）**：
- 小红书 → `03-xiaohongshu-insights.md`
- Reddit → `05-reddit-insights.md`

## 置信度说明

所有文件使用统一标注：

| 标注 | 含义 |
|------|------|
| `[直接观察]` | 研究者直接浏览页面所得，原始数据，可溯源 |
| `[分析推断]` | 基于观察数据的作者解读，含主观判断，不等同于用户原话 |
| `[二手引用，未直接核实]` | 来自其他文章或报告的转引，原始来源未直接核实 |
| `[估算，非实测]` | 基于现有数据的主观估计，非来自调查或统计 |

## 文件体系

| 文件 | 类型 | 内容摘要 |
|------|------|---------|
| `01-user-research-synthesis.md` | **★ 主报告** | 画像、行为细分、旅程、竞品、洞察、产品建议 |
| `02-xiaohongshu-findings.md` | 原始记录 | U01/U02/U03 用户Profile深度分析、搜索结果概览 |
| `03-xiaohongshu-insights.md` | 平台洞察 | 5大洞察、S-PDCA痛点、与P01对比 |
| `04-reddit-findings.md` | 原始记录 | R01-R10/C01-C04/F01/P01-P02逐帖分析 |
| `05-reddit-insights.md` | 平台洞察 | 5类失败模式、8大洞察含Reddit独有维度 |

## 访谈记录格式

每份访谈记录使用统一模板，文件命名：`{日期}-{编号}.md`，例如 `2026-04-06-P01.md`。

| 字段 | 说明 |
|------|------|
| 参与者编号 | P01, P02... |
| 渠道来源 | 如何认识/接触到的 |
| 基本画像 | 年龄段、性别、职业、地域 |
| 减脂阶段 | 刚开始/中途/反弹过/长期维持 |
| 当前方案 | 用什么工具/方法 |
| 花费 | 时间/金钱投入 |
| 最大卡点 | 用原话记录 |
| 尝试过的解决方案 | 以及为什么没用 |
| 意外发现 | 没预料到的信息 |
| 与 S-PDCA 的关联 | 痛点落在哪个环节 |

## 分析方法

当访谈积累到 8 人以上时，进行 PMF 信号分析：

1. 痛点是否收敛（3+ 人描述相似卡点）
2. 现有方案满意度
3. 付费意愿与历史
4. S-PDCA 假设验证情况
