# ABOUTME: 减脂行为调查第二期数据清洗与分析脚本
# ABOUTME: 输入原始 CSV，输出清洗后 CSV 与 Markdown 分析报告

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
from collections import Counter

# ─── 路径配置 ──────────────────────────────────────────────────────────────────
RAW_CSV = "/Users/dexter/DexterOS/products/Voliti/docs/user-research/questionnaires/raw/减脂行为与日常习惯调查-第二期-results.csv"
OUT_DIR = "/Users/dexter/DexterOS/products/Voliti/docs/user-research/questionnaires/v2"
CLEANED_CSV = os.path.join(OUT_DIR, "survey_v2_cleaned.csv")
REPORT_MD = os.path.join(OUT_DIR, "analysis_report.md")

os.makedirs(OUT_DIR, exist_ok=True)

# ─── 1. 读取数据 ────────────────────────────────────────────────────────────────
df_raw = pd.read_csv(RAW_CSV, encoding="utf-8-sig")
total_raw = len(df_raw)
print(f"原始行数: {total_raw}")

# ─── 2. 数据清洗 ────────────────────────────────────────────────────────────────

# 2a. 答题时长过短（< 60 秒，疑似机器作答）
df_raw["答题时长_sec"] = pd.to_numeric(df_raw["答题时长"], errors="coerce")
spam_time = df_raw["答题时长_sec"] < 60
print(f"时长 <60s 的行: {spam_time.sum()}")

# 2b. 开放题垃圾内容检测（金融广告、无关通用模板）
SPAM_PATTERNS = [
    r"天天盈",
    r"转入转出.*到账速度",
    r"理财.*零钱",
    r"活期",
    r"2026年中奋斗",
    r"奋斗小目标",
    r"远离无用社交",
    r"精简生活.*沉淀内心",
]

def is_spam_text(text: str) -> bool:
    if not isinstance(text, str) or text.strip() == "":
        return False
    for pat in SPAM_PATTERNS:
        if re.search(pat, text):
            return True
    return False

# 检查开放题三列
open_cols = [
    df_raw.columns[66],  # Q23/Q27 教练经历 (版本A)
    df_raw.columns[69],  # Q26 失控经历
    df_raw.columns[70],  # Q27 教练经历 (版本B)
]
spam_open = df_raw[open_cols].apply(lambda col: col.map(is_spam_text)).any(axis=1)
print(f"开放题含垃圾内容的行: {spam_open.sum()}")

# 2c. 清洗数据结果列（平台标记）
wash_col = "清洗数据结果"
if wash_col in df_raw.columns:
    platform_invalid = df_raw[wash_col].astype(str).str.contains("无效", na=False)
    print(f"平台标记无效的行: {platform_invalid.sum()}")
else:
    platform_invalid = pd.Series(False, index=df_raw.index)

# 2d. 智能清洗无效概率（≥0.7 视为高风险）
prob_col = "智能清洗数据无效概率"
if prob_col in df_raw.columns:
    df_raw["_invalid_prob"] = pd.to_numeric(df_raw[prob_col], errors="coerce")
    high_risk = df_raw["_invalid_prob"] >= 0.7
    print(f"智能清洗高风险 (≥0.7) 的行: {high_risk.sum()}")
else:
    high_risk = pd.Series(False, index=df_raw.index)

# 2e. Q1=D 或 E（非目标用户：从未认真尝试 / 对减脂没兴趣）
q1_col = df_raw.columns[4]
non_target = df_raw[q1_col].astype(str).str.strip().str.startswith(("D.", "E."))
print(f"Q1=D或E（非目标用户）: {non_target.sum()}")

# 综合过滤条件
invalid_mask = spam_time | spam_open | platform_invalid | high_risk | non_target
df_invalid = df_raw[invalid_mask].copy()
df = df_raw[~invalid_mask].copy()

print(f"\n清洗摘要:")
print(f"  原始回收: {total_raw}")
print(f"  时长<60s: {spam_time.sum()}")
print(f"  开放题垃圾: {spam_open.sum()}")
print(f"  平台标记无效: {platform_invalid.sum()}")
print(f"  智能清洗高风险: {high_risk.sum()}")
print(f"  Q1=D/E 非目标: {non_target.sum()}")
print(f"  (以上可能重叠)")
print(f"  剔除总计: {invalid_mask.sum()}")
print(f"  有效样本: {len(df)}")

# 保存清洗后数据
df.to_csv(CLEANED_CSV, encoding="utf-8-sig", index=False)
print(f"\n清洗后 CSV 已保存: {CLEANED_CSV}")

# ─── 辅助函数 ───────────────────────────────────────────────────────────────────

def extract_letter(series: pd.Series) -> pd.Series:
    """从形如 'A.【xxx】...' 的字符串中提取首字母"""
    return series.astype(str).str.strip().str.extract(r'^([A-Z])\.', expand=False)

def freq_table(series: pd.Series, label_map: dict = None) -> pd.DataFrame:
    """单选题频率表"""
    counts = series.value_counts(dropna=True)
    pct = (counts / counts.sum() * 100).round(1)
    df_out = pd.DataFrame({"选项": counts.index, "频次": counts.values, "占比%": pct.values})
    if label_map:
        df_out["说明"] = df_out["选项"].map(label_map)
    return df_out.reset_index(drop=True)

def borda_score(df_sub: pd.DataFrame, option_names: list) -> pd.DataFrame:
    """
    计算 Borda 分数。
    df_sub: 每列为一个选项，每行为一条回答，值为该选项的排名数字（1=最高）。
    N 个选项时，排名第 1 得 N 分，排名第 2 得 N-1 分，以此类推。
    空值/非数字不计入。
    """
    n = len(option_names)
    records = []
    for col_name, opt_name in zip(df_sub.columns, option_names):
        ranks = pd.to_numeric(df_sub[col_name], errors="coerce").dropna()
        ranks = ranks[ranks.between(1, n)]
        scores = n + 1 - ranks  # rank 1 → N 分，rank N → 1 分
        records.append({
            "选项": opt_name,
            "平均Borda分": round(scores.mean(), 2) if len(scores) > 0 else np.nan,
            "有效填写数": len(scores),
        })
    result = pd.DataFrame(records).sort_values("平均Borda分", ascending=False).reset_index(drop=True)
    return result

def df_to_md_table(df: pd.DataFrame, indent: str = "") -> str:
    """DataFrame 转 Markdown 表格"""
    lines = []
    lines.append(indent + "| " + " | ".join(str(c) for c in df.columns) + " |")
    lines.append(indent + "| " + " | ".join(["---"] * len(df.columns)) + " |")
    for _, row in df.iterrows():
        lines.append(indent + "| " + " | ".join(str(v) for v in row.values) + " |")
    return "\n".join(lines)

def crosstab_md(df: pd.DataFrame, col_a: pd.Series, col_b: pd.Series,
                row_label: str, col_label: str) -> str:
    ct = pd.crosstab(col_a, col_b, margins=True, margins_name="合计")
    ct.index.name = f"{row_label} \\ {col_label}"
    return df_to_md_table(ct.reset_index())

# ─── 3. 变量提取 ────────────────────────────────────────────────────────────────

# 单选题
Q1  = extract_letter(df.iloc[:, 4])
Q2  = extract_letter(df.iloc[:, 5])
Q3  = extract_letter(df.iloc[:, 6])
Q4  = extract_letter(df.iloc[:, 7])
Q5  = extract_letter(df.iloc[:, 9])
Q6  = extract_letter(df.iloc[:, 10])
Q9  = extract_letter(df.iloc[:, 23])
Q11 = extract_letter(df.iloc[:, 32])
Q12 = extract_letter(df.iloc[:, 33])
Q16 = extract_letter(df.iloc[:, 52])
Q17 = extract_letter(df.iloc[:, 53])
Q18 = extract_letter(df.iloc[:, 54])
Q19 = extract_letter(df.iloc[:, 55])
Q21 = extract_letter(df.iloc[:, 64])
Q22 = extract_letter(df.iloc[:, 65])
Q25 = extract_letter(df.iloc[:, 68])

# 排名题
Q7_cols  = df.iloc[:, 11:17]
Q8_cols  = df.iloc[:, 17:23]
Q10_cols = df.iloc[:, 25:32]
Q13_cols = df.iloc[:, 34:39]
Q14_cols = df.iloc[:, 40:45]
Q15_cols = df.iloc[:, 46:52]

Q7_opts  = ["自己做饭", "食堂", "外卖", "外出就餐", "家人做饭", "便利食品"]
Q8_opts  = ["自己做饭", "食堂", "外卖", "外出就餐", "家人做饭", "便利食品"]
Q10_opts = ["个性化", "专业性", "记忆力", "态度", "可执行", "交流风格", "不确定"]
Q13_opts = ["手机App", "微信小程序", "手机网页", "电脑网页", "其他"]
Q14_opts = ["手机App", "微信小程序", "手机网页", "电脑网页", "其他"]
Q15_opts = ["社交媒体", "搜索引擎", "问AI", "问身边人", "专业人士", "不太找"]

# 多选题 Q20
Q20_cols = df.iloc[:, 56:64]
Q20_opts = ["小红书", "抖音", "微信公众号/视频号", "B站", "知乎", "微博", "其他", "其他_填空"]

# 开放题
Q23_col = df.iloc[:, 66]  # 版本A教练经历
Q24_col = df.iloc[:, 67]  # 版本A微信号
Q26_col = df.iloc[:, 69]  # 失控经历
Q27_col = df.iloc[:, 70]  # 版本B教练经历
Q28_col = df.iloc[:, 71]  # 版本B微信号

# ─── 4. 标签映射 ────────────────────────────────────────────────────────────────

Q1_labels  = {"A": "正在执行", "B": "断断续续", "C": "已暂停/放弃", "D": "从未认真尝试", "E": "对减脂无兴趣"}
Q2_labels  = {"A": "短期少次(<1年,1-2次)", "B": "短期多次(<1年,3次+)", "C": "中期少次(1-3年,1-2次)", "D": "中期多次(1-3年,3次+)", "E": "长期(3年+)"}
Q3_labels  = {"A": "成功维持", "B": "有效但反弹", "C": "轻微改善", "D": "几乎无效", "E": "未能坚持"}
Q4_labels  = {"A": "方案难执行", "B": "节奏被打乱", "C": "缺乏动力/意志力", "D": "效果不明显", "E": "其他"}
Q5_labels  = {"A": "跟过专业人士", "B": "跟过身边人", "C": "跟过网上方法", "D": "无外部指导"}
Q6_labels  = {"A": "详细计划", "B": "大致方向", "C": "直接行动", "D": "观望等待", "E": "其他"}
Q9_labels  = {"A": "从未用过", "B": "只聊工作", "C": "聊过但没用", "D": "聊过且有用", "E": "深度使用"}
Q11_labels = {"A": "独居", "B": "与伴侣/家人同住", "C": "合租", "D": "其他"}
Q12_labels = {"A": "高频(6次+/天)", "B": "中频(3-5次/天)", "C": "场景触发即可", "D": "低频(每周几次)", "E": "不需要推送"}
Q16_labels = {"A": "未花钱", "B": "数百元", "C": "一千至三千", "D": "三千至一万", "E": "一万以上"}
Q17_labels = {"A": "男", "B": "女", "C": "其他/不愿透露"}
Q18_labels = {"A": "18-24岁", "B": "25-30岁", "C": "31-40岁", "D": "41岁以上"}
Q19_labels = {"A": "一线(北上广深)", "B": "新一线", "C": "二线及以下"}
Q21_labels = {"A": "正常体重", "B": "中等基数(5-15斤)", "C": "较大基数(15-30斤)", "D": "大基数(30斤+)", "E": "其他"}
Q22_labels = {str(i): f"{i}分" for i in range(1, 11)}
Q25_labels = {
    "A": "INTJ", "B": "INTP", "C": "ENTJ", "D": "ENTP",
    "E": "INFJ", "F": "INFP", "G": "ENFJ", "H": "ENFP",
    "I": "ISTJ", "J": "ISTP", "K": "ESTJ", "L": "ESTP",
    "M": "ISFJ", "N": "ISFP", "O": "ESFJ", "P": "ESFP",
    "Q": "不知道/不参与"
}

# ─── 5. 频率分析 ────────────────────────────────────────────────────────────────

def single_freq(series, label_map, question_label):
    letters = series.dropna()
    counts = letters.value_counts()
    rows = []
    for letter, label in label_map.items():
        cnt = counts.get(letter, 0)
        rows.append({"选项": f"{letter}", "说明": label, "频次": cnt, "占比%": round(cnt / len(letters) * 100, 1) if len(letters) > 0 else 0})
    return pd.DataFrame(rows)

Q1_freq  = single_freq(Q1,  Q1_labels,  "Q1")
Q2_freq  = single_freq(Q2,  Q2_labels,  "Q2")
Q3_freq  = single_freq(Q3,  Q3_labels,  "Q3")
Q4_freq  = single_freq(Q4,  Q4_labels,  "Q4")
Q5_freq  = single_freq(Q5,  Q5_labels,  "Q5")
Q6_freq  = single_freq(Q6,  Q6_labels,  "Q6")
Q9_freq  = single_freq(Q9,  Q9_labels,  "Q9")
Q11_freq = single_freq(Q11, Q11_labels, "Q11")
Q12_freq = single_freq(Q12, Q12_labels, "Q12")
Q16_freq = single_freq(Q16, Q16_labels, "Q16")
Q17_freq = single_freq(Q17, Q17_labels, "Q17")
Q18_freq = single_freq(Q18, Q18_labels, "Q18")
Q19_freq = single_freq(Q19, Q19_labels, "Q19")
Q21_freq = single_freq(Q21, Q21_labels, "Q21")
Q25_freq = single_freq(Q25, Q25_labels, "Q25")

# Q22 意愿强度（数字选项）
Q22_raw = df.iloc[:, 65].astype(str).str.extract(r'(\d+)')[0]
Q22_numeric = pd.to_numeric(Q22_raw, errors="coerce")
Q22_mean = Q22_numeric.mean()
Q22_median = Q22_numeric.median()
Q22_counts = Q22_numeric.value_counts().sort_index()

# ─── 6. Borda 排序 ──────────────────────────────────────────────────────────────

Q7_borda  = borda_score(Q7_cols,  Q7_opts)
Q8_borda  = borda_score(Q8_cols,  Q8_opts)
Q10_borda = borda_score(Q10_cols, Q10_opts)
Q13_borda = borda_score(Q13_cols, Q13_opts)
Q14_borda = borda_score(Q14_cols, Q14_opts)
Q15_borda = borda_score(Q15_cols, Q15_opts)

# ─── 7. 多选题 Q20 ──────────────────────────────────────────────────────────────

Q20_counts = {}
platform_col_names = ["小红书", "抖音", "微信公众号/视频号", "B站", "知乎", "微博", "其他"]
for i, name in enumerate(platform_col_names):
    col = df.iloc[:, 56 + i]
    Q20_counts[name] = col.astype(str).str.strip().ne("").sum() - (col.astype(str).str.strip() == "nan").sum()

# 修正：非空且非nan才算选择
def count_nonempty(col):
    return col.apply(lambda x: isinstance(x, str) and x.strip() not in ("", "nan")).sum()

Q20_result = {}
for i, name in enumerate(platform_col_names):
    col = df.iloc[:, 56 + i]
    Q20_result[name] = count_nonempty(col)

Q20_df = pd.DataFrame([
    {"平台": k, "选择人数": v, "占比%": round(v / len(df) * 100, 1)}
    for k, v in sorted(Q20_result.items(), key=lambda x: -x[1])
])

# ─── 8. 开放题 ──────────────────────────────────────────────────────────────────

def nonempty_texts(col: pd.Series) -> list:
    return [str(x).strip() for x in col if isinstance(x, str) and x.strip() not in ("", "nan")]

Q23_texts = nonempty_texts(Q23_col)
Q27_texts = nonempty_texts(Q27_col)
coach_texts_all = Q23_texts + Q27_texts

Q26_texts = nonempty_texts(Q26_col)

Q24_texts = nonempty_texts(Q24_col)
Q28_texts = nonempty_texts(Q28_col)
contact_all = list(set(Q24_texts + Q28_texts))
# 去除明显无效（长度太短、非微信号格式）
contact_valid = [x for x in contact_all if len(x.strip()) >= 4]

def sample_quotes(texts: list, n: int = 5) -> list:
    # 过滤垃圾内容后抽样
    clean = [t for t in texts if not is_spam_text(t) and len(t) > 5]
    return clean[:n]

# ─── 9. 关键交叉分析 ────────────────────────────────────────────────────────────

# Q1 × Q2 四象限
# 行动中: Q1=A/B；非行动中: Q1=C
# 少次: Q2=A/C；多次: Q2=B/D/E
Q1_action = Q1.map(lambda x: "行动中(A/B)" if x in ("A","B") else ("非行动中(C)" if x == "C" else "其他"))
Q2_freq_grp = Q2.map(lambda x: "少次(1-2次)" if x in ("A","C") else ("多次(3次+)" if x in ("B","D","E") else "其他"))
ct_q1q2 = pd.crosstab(Q1_action, Q2_freq_grp, margins=True, margins_name="合计")

# Q3 × Q4 效果历史 × 归因
ct_q3q4 = pd.crosstab(Q3, Q4, margins=True, margins_name="合计")

# Q5 × Q3 指导性 × 效果
ct_q5q3 = pd.crosstab(Q5, Q3, margins=True, margins_name="合计")

# Q9 × Q21 AI使用 × 体重状况
ct_q9q21 = pd.crosstab(Q9, Q21, margins=True, margins_name="合计")

# Q12 × Q22 通知偏好 × 意愿强度（均值）
Q22_int = Q22_numeric.fillna(0).astype(int).astype(str).replace("0", np.nan)
# 用均值展示
_q12_valid = Q12[Q12.isin(Q12_labels.keys())]
_q22_valid = Q22_numeric[Q12.isin(Q12_labels.keys())]
q12_q22_mean = pd.DataFrame({
    "Q12通知偏好": _q12_valid,
    "Q22意愿强度": _q22_valid
}).groupby("Q12通知偏好")["Q22意愿强度"].agg(["mean", "count"]).round(2)
q12_q22_mean.columns = ["意愿均值", "人数"]
q12_q22_mean.index = q12_q22_mean.index.map(lambda x: f"{x}({Q12_labels.get(x, x)})")

# ─── 10. 种子用户候选分析 ────────────────────────────────────────────────────────

seed_df = df[
    (Q22_numeric >= 7) &
    (Q1.isin(["A", "B"])) &
    (Q3.isin(["A", "B", "C"]))
].copy()

seed_contacts_q24 = nonempty_texts(df.loc[seed_df.index].iloc[:, 67])
seed_contacts_q28 = nonempty_texts(df.loc[seed_df.index].iloc[:, 71])
seed_contacts = list(set(seed_contacts_q24 + seed_contacts_q28))

# ─── 11. 报告生成 ────────────────────────────────────────────────────────────────

lines = []

def h1(text): lines.append(f"\n# {text}\n")
def h2(text): lines.append(f"\n## {text}\n")
def h3(text): lines.append(f"\n### {text}\n")
def p(text):  lines.append(f"{text}\n")
def table(df_): lines.append(df_to_md_table(df_) + "\n")

lines.append("<!-- ABOUTME: 减脂行为与日常习惯调查第二期分析报告 -->")
lines.append("<!-- ABOUTME: 自动生成，勿手动修改数据部分 -->")
lines.append("")
h1("减脂行为与日常习惯调查（第二期）数据分析报告")
p(f"**生成日期：** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
p(f"**数据来源：** 减脂行为与日常习惯调查-第二期（问卷星）")
p("")

# ── 第一节：数据概览 ──────────────────────────────────────────────────────────────
h2("一、数据概览")

# 清洗明细
clean_detail = {
    "原始回收总量": total_raw,
    "答题时长<60秒（疑似机器）": int(spam_time.sum()),
    "开放题含垃圾/广告内容": int(spam_open.sum()),
    "平台标记无效": int(platform_invalid.sum()),
    "智能清洗高风险（≥0.7）": int(high_risk.sum()),
    "Q1=D/E（非目标用户）": int(non_target.sum()),
    "累计剔除（去重后）": int(invalid_mask.sum()),
    "最终有效样本": len(df),
}

h3("1.1 样本清洗摘要")
clean_df = pd.DataFrame([{"指标": k, "数值": v} for k, v in clean_detail.items()])
table(clean_df)
p(f"> 注：各剔除原因存在重叠，累计剔除为去重后数字。最终有效样本 **{len(df)}** 份，有效率 **{round(len(df)/total_raw*100, 1)}%**。")

h3("1.2 地理分布（省级 Top10）")
if "地理位置省" in df.columns:
    prov_cnt = df["地理位置省"].value_counts().head(10)
    prov_df = pd.DataFrame({"省份": prov_cnt.index, "人数": prov_cnt.values, "占比%": (prov_cnt.values / len(df) * 100).round(1)})
    table(prov_df)

h3("1.3 答题时长分布")
time_stats = df["答题时长_sec"].describe().round(1)
time_df = pd.DataFrame({"统计量": time_stats.index, "秒数": time_stats.values})
table(time_df)

# ── 第二节：用户分层 ──────────────────────────────────────────────────────────────
h2("二、用户分层（Q1 × Q2 四象限）")
h3("2.1 Q1 当前减脂状态")
table(Q1_freq)

h3("2.2 Q2 尝试时长×次数")
table(Q2_freq)

h3("2.3 Q1 × Q2 四象限矩阵")
p("行动力（Q1）× 尝试深度（Q2）交叉分析：")
table(ct_q1q2.reset_index())

p("**解读：**")
try:
    active_heavy = ct_q1q2.loc["行动中(A/B)", "多次(3次+)"] if "行动中(A/B)" in ct_q1q2.index and "多次(3次+)" in ct_q1q2.columns else 0
    active_light = ct_q1q2.loc["行动中(A/B)", "少次(1-2次)"] if "行动中(A/B)" in ct_q1q2.index and "少次(1-2次)" in ct_q1q2.columns else 0
    inactive_heavy = ct_q1q2.loc["非行动中(C)", "多次(3次+)"] if "非行动中(C)" in ct_q1q2.index and "多次(3次+)" in ct_q1q2.columns else 0
    inactive_light = ct_q1q2.loc["非行动中(C)", "少次(1-2次)"] if "非行动中(C)" in ct_q1q2.index and "少次(1-2次)" in ct_q1q2.columns else 0
    p(f"- **高价值核心用户**（行动中×多次尝试）：{active_heavy} 人 ——  有减脂行动且经验丰富，对方案优化需求最强")
    p(f"- **新入局用户**（行动中×少次尝试）：{active_light} 人 ——  初次或少次尝试，需要引导建立正确预期")
    p(f"- **反复失败用户**（非行动中×多次尝试）：{inactive_heavy} 人 ——  尝试过多次但当前已放弃，再激活难度较大")
    p(f"- **观望用户**（非行动中×少次尝试）：{inactive_light} 人 ——  参与度低，短期难以转化")
except Exception as e:
    p(f"（四象限数据读取异常：{e}）")

# ── 第三节：减脂效果与归因 ────────────────────────────────────────────────────────
h2("三、减脂效果与归因（Q3、Q4）")
h3("3.1 Q3 最佳减脂效果")
table(Q3_freq)

h3("3.2 Q4 失败/未达预期主要原因")
table(Q4_freq)

h3("3.3 Q3 × Q4 效果历史与归因交叉")
table(ct_q3q4.reset_index())
p("**解读：** 成功维持与有效但反弹的人群，在归因上是否有显著差异，可作为行为干预设计的参考依据。")

# ── 第四节：外部指导与计划行为 ────────────────────────────────────────────────────
h2("四、外部指导与计划行为（Q5、Q6）")
h3("4.1 Q5 接受外部指导类型")
table(Q5_freq)

h3("4.2 Q6 开始减脂时的准备方式")
table(Q6_freq)

h3("4.3 Q5（指导类型）× Q3（效果）交叉")
table(ct_q5q3.reset_index())

# ── 第五节：饮食环境 ──────────────────────────────────────────────────────────────
h2("五、饮食环境（Q7 频率排序、Q8 负面影响排序）")
h3("5.1 Q7 日常饮食方式 Borda 排序（频率从高到低）")
table(Q7_borda)
p("> Borda 分越高，表示该饮食方式在样本中整体频率排名越靠前。")

h3("5.2 Q8 饮食方式对体重管理负面影响 Borda 排序")
table(Q8_borda)
p("> Borda 分越高，表示该饮食方式被认为对体重管理的负面影响越大。")

# ── 第六节：AI 使用与信任 ────────────────────────────────────────────────────────
h2("六、AI 使用与信任（Q9、Q10）")
h3("6.1 Q9 AI 聊天工具使用情况")
table(Q9_freq)

h3("6.2 Q9 × Q21 AI 使用 × 体重状况交叉")
table(ct_q9q21.reset_index())

h3("6.3 Q10 影响 AI 信任感的因素 Borda 排序")
table(Q10_borda)
p("> Borda 分越高，该因素对用户 AI 信任感的影响权重越大。")

# ── 第七节：产品偏好 ──────────────────────────────────────────────────────────────
h2("七、产品偏好（Q12 通知偏好、Q13/Q14 产品形态）")
h3("7.1 Q12 推送通知偏好")
table(Q12_freq)

h3("7.2 Q12 通知偏好 × Q22 意愿强度（均值）")
table(q12_q22_mean.reset_index())

h3("7.3 Q11 居住情况")
table(Q11_freq)

h3("7.4 Q13 健康管理产品形态偏好 Borda 排序")
table(Q13_borda)

h3("7.5 Q14 AI 聊天机器人产品形态偏好 Borda 排序")
table(Q14_borda)

# ── 第八节：信息来源与社交平台 ───────────────────────────────────────────────────
h2("八、信息来源与社交平台（Q15、Q20）")
h3("8.1 Q15 减脂信息获取渠道 Borda 排序")
table(Q15_borda)

h3("8.2 Q20 日常内容平台使用情况（多选）")
table(Q20_df)
p(f"> 基于有效样本 {len(df)} 人，占比为选择该平台的人数占比。")

# ── 第九节：人口统计 ──────────────────────────────────────────────────────────────
h2("九、人口统计画像（Q16-Q19、Q21、Q22、Q25）")
h3("9.1 Q17 性别分布")
table(Q17_freq)

h3("9.2 Q18 年龄段分布")
table(Q18_freq)

h3("9.3 Q19 城市层级分布")
table(Q19_freq)

h3("9.4 Q16 过去一年减脂花费")
table(Q16_freq)

h3("9.5 Q21 当前体重状况")
table(Q21_freq)

h3("9.6 Q22 减脂意愿强度（1-10）")
p(f"- **均值：** {Q22_mean:.2f}　　**中位数：** {Q22_median:.1f}")
q22_dist = pd.DataFrame({
    "分数": Q22_counts.index.astype(int).astype(str),
    "人数": Q22_counts.values.astype(int).astype(str),
    "占比%": (Q22_counts.values / Q22_counts.sum() * 100).round(1).astype(str)
})
table(q22_dist)

h3("9.7 Q25 MBTI 类型分布")
mbti_valid = Q25_freq[Q25_freq["频次"] > 0].sort_values("频次", ascending=False)
table(mbti_valid)

# ── 第十节：开放题摘要 ────────────────────────────────────────────────────────────
h2("十、开放题摘要")

h3("10.1 Q23/Q27 教练/指导跟进经历（有效回答）")
p(f"**版本A（Q23）有效回答：** {len(Q23_texts)} 条　　**版本B（Q27）有效回答：** {len(Q27_texts)} 条　　**合并去重：** {len(set(coach_texts_all))} 条")
p("\n**代表性引用（前5条，已过滤垃圾内容）：**\n")
for i, q in enumerate(sample_quotes(coach_texts_all, 5), 1):
    p(f"> {i}. {q[:200]}")

h3("10.2 Q26 失控饮食经历（有效回答）")
p(f"**有效回答：** {len(Q26_texts)} 条")
p("\n**代表性引用（前5条）：**\n")
for i, q in enumerate(sample_quotes(Q26_texts, 5), 1):
    p(f"> {i}. {q[:200]}")

h3("10.3 Q24/Q28 种子用户联系方式")
p(f"- Q24（版本A）留下联系方式：**{len(Q24_texts)}** 人")
p(f"- Q28（版本B）留下联系方式：**{len(Q28_texts)}** 人")
p(f"- 合并去重有效联系方式：**{len(contact_valid)}** 条")

# ── 第十一节：关键交叉分析 ────────────────────────────────────────────────────────
h2("十一、关键交叉分析汇总")

h3("11.1 Q3（效果历史）× Q4（归因）")
p("见第三节 3.3，此处补充说明：")
try:
    # 计算成功维持中归因分布
    q3a_mask = Q3 == "A"
    if q3a_mask.sum() > 0:
        q4_given_q3a = Q4[q3a_mask].value_counts()
        p(f"**成功维持（A）组（{q3a_mask.sum()}人）中主要归因：**")
        for letter, cnt in q4_given_q3a.items():
            p(f"  - {letter}（{Q4_labels.get(letter, letter)}）：{cnt} 人")
except Exception:
    pass

h3("11.2 Q9（AI使用程度）× Q21（体重状况）")
p("见第六节 6.2。深度 AI 使用者（D/E）的体重状况分布，可反映目标用户 AI 接受度。")

h3("11.3 Q12（通知偏好）× Q22（意愿强度）")
p("见第七节 7.2。意愿强度越高的用户，对推送通知的接受度是否更高，是产品运营策略的参考依据。")

# 补充：意愿强度高（≥8）用户的通知偏好分布
high_will = Q22_numeric >= 8
q12_high_will = Q12[high_will & Q12.isin(Q12_labels.keys())].value_counts()
hw_total = q12_high_will.sum()
p(f"\n**意愿强度 ≥8 分的用户（{int(high_will.sum())}人，其中通知偏好有效填写 {hw_total} 人）通知偏好分布：**")
for letter, cnt in q12_high_will.items():
    p(f"  - {letter}（{Q12_labels.get(letter, letter)}）：{cnt} 人（{round(cnt/hw_total*100, 1)}%）")

# ── 第十二节：种子用户候选 ────────────────────────────────────────────────────────
h2("十二、种子用户候选")

h3("12.1 筛选标准")
p("以下条件**同时满足**视为高价值种子用户候选：")
p("- Q22 意愿强度 ≥ 7 分")
p("- Q1 = A（正在执行）或 B（断断续续）")
p("- Q3 = A、B 或 C（有减脂尝试且有一定效果）")

h3("12.2 候选人数统计")
p(f"**符合条件的候选用户：** {len(seed_df)} 人")
p(f"**其中留下联系方式的：** {len(seed_contacts)} 人")

if len(seed_df) > 0:
    h3("12.3 候选用户特征画像")

    # 性别
    seed_q17 = extract_letter(seed_df.iloc[:, 53]).value_counts()
    p("**性别分布：**")
    for k, v in seed_q17.items():
        p(f"  - {k}（{Q17_labels.get(k, k)}）：{v} 人")

    # 年龄
    seed_q18 = extract_letter(seed_df.iloc[:, 54]).value_counts()
    p("**年龄段：**")
    for k, v in seed_q18.items():
        p(f"  - {k}（{Q18_labels.get(k, k)}）：{v} 人")

    # 体重状况
    seed_q21 = extract_letter(seed_df.iloc[:, 64]).value_counts()
    p("**体重状况：**")
    for k, v in seed_q21.items():
        p(f"  - {k}（{Q21_labels.get(k, k)}）：{v} 人")

    # 意愿均值
    seed_will = pd.to_numeric(seed_df.iloc[:, 65].astype(str).str.extract(r'(\d+)')[0], errors="coerce")
    p(f"**意愿强度均值：** {seed_will.mean():.2f}（整体样本均值 {Q22_mean:.2f}）")

    # AI 使用
    seed_q9 = extract_letter(seed_df.iloc[:, 23]).value_counts()
    p("**AI 使用情况：**")
    for k, v in seed_q9.items():
        p(f"  - {k}（{Q9_labels.get(k, k)}）：{v} 人")

h3("12.4 联系方式可用性说明")
p("联系方式原始数据已存入清洗后 CSV，报告中不展示具体号码以保护用户隐私。")
p("招募建议：优先联系意愿强度 ≥ 8、Q1=A（正在执行）的用户，其产品体验质量和反馈价值最高。")

# ── 尾注 ─────────────────────────────────────────────────────────────────────────
lines.append("\n---\n")
lines.append(f"*本报告由自动化分析脚本生成，生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。*")
lines.append(f"*有效样本量：{len(df)}；数据文件：`survey_v2_cleaned.csv`。*")

# 写入报告
with open(REPORT_MD, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n报告已保存: {REPORT_MD}")
print(f"报告行数: {len(lines)}")
