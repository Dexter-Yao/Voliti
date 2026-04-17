# ABOUTME: Wave-2 问卷数据清洗脚本
# ABOUTME: 读取原始 CSV，执行 5 层过滤、列重命名、"其他"选项归并，输出清洗后 CSV

import pandas as pd
import numpy as np
import re

RAW_CSV = "raw/wave-2_减脂行为与日常习惯调查-第二期-results.csv"
OUT_CSV = "wave-2_survey_cleaned.csv"

# ─── 1. 读取 ─────────────────────────────────────────────────────────────────

df = pd.read_csv(RAW_CSV, encoding="utf-8-sig")
print(f"原始行数: {len(df)}")

# ─── 2. 数据清洗（5 层过滤） ──────────────────────────────────────────────────

# 2a. 答题时长 < 60 秒
df["_dur"] = pd.to_numeric(df["答题时长"], errors="coerce")
mask_time = df["_dur"] < 60

# 2b. 开放题垃圾内容
SPAM_RE = [
    r"天天盈", r"转入转出.*到账速度", r"理财.*零钱", r"活期",
    r"2026年中奋斗", r"奋斗小目标", r"远离无用社交", r"精简生活.*沉淀内心",
]

def is_spam(text):
    if not isinstance(text, str) or text.strip() == "":
        return False
    return any(re.search(p, text) for p in SPAM_RE)

open_cols = [df.columns[66], df.columns[69], df.columns[70]]
mask_spam = df[open_cols].apply(lambda c: c.map(is_spam)).any(axis=1)

# 2c. 平台标记无效
mask_platform = df.get("清洗数据结果", pd.Series("", index=df.index)).astype(str).str.contains("无效", na=False)

# 2d. 智能清洗无效概率 >= 0.7
prob = pd.to_numeric(df.get("智能清洗数据无效概率", pd.Series(dtype=float)), errors="coerce")
mask_risk = prob >= 0.7

# 2e. Q1 = D 或 E（非目标）
mask_nontarget = df.iloc[:, 4].astype(str).str.strip().str.startswith(("D.", "E."))

invalid = mask_time | mask_spam | mask_platform | mask_risk | mask_nontarget
print(f"剔除: 时长<60s={mask_time.sum()}, 垃圾={mask_spam.sum()}, "
      f"平台无效={mask_platform.sum()}, 高风险={mask_risk.sum()}, "
      f"非目标={mask_nontarget.sum()}, 总计(去重)={invalid.sum()}")

df = df[~invalid].copy()
print(f"有效样本: {len(df)}")

# ─── 3. 提取字母辅助函数 ─────────────────────────────────────────────────────

def letter(series):
    return series.astype(str).str.strip().str.extract(r"^([A-Z])\.", expand=False)

# ─── 4. 构建清洗后 DataFrame ──────────────────────────────────────────────────

out = pd.DataFrame()

# 元数据
out["respondent_id"] = df.iloc[:, 0].values
out["duration_sec"] = df["_dur"].values

# 单选题（提取字母代码）
out["q1_status"] = letter(df.iloc[:, 4]).values
out["q2_duration"] = letter(df.iloc[:, 5]).values
out["q3_best_result"] = letter(df.iloc[:, 6]).values

# Q4: 处理 F.其他 → NaN
q4_raw = letter(df.iloc[:, 7])
q4_raw = q4_raw.where(q4_raw != "F")  # F.其他 → NaN
out["q4_failure_reason"] = q4_raw.values

out["q5_guidance"] = letter(df.iloc[:, 9]).values
out["q6_planning"] = letter(df.iloc[:, 10]).values

# Q7 排序题：饮食方式频率
food_names = ["自己做饭", "食堂", "外卖", "外出就餐", "家人做饭", "便利食品"]
for i, name in enumerate(food_names):
    out[f"q7_food_rank_{name}"] = pd.to_numeric(df.iloc[:, 11 + i], errors="coerce").values

# Q8 排序题：饮食方式负面影响
for i, name in enumerate(food_names):
    out[f"q8_impact_rank_{name}"] = pd.to_numeric(df.iloc[:, 17 + i], errors="coerce").values

# Q9 AI 使用
out["q9_ai_usage"] = letter(df.iloc[:, 23]).values

# Q10 排序题：AI 信任因素
trust_names = ["个性化", "专业性", "记忆力", "态度", "可执行", "交流风格", "不确定"]
for i, name in enumerate(trust_names):
    out[f"q10_trust_rank_{name}"] = pd.to_numeric(df.iloc[:, 25 + i], errors="coerce").values

# Q11 居住
out["q11_living"] = letter(df.iloc[:, 32]).values

# Q12 通知偏好
out["q12_notification"] = letter(df.iloc[:, 33]).values

# Q13 健康产品形态排序（仅 A-D，删除 E.其他）
health_form_names = ["手机App", "微信小程序", "手机网页", "电脑网页"]
for i, name in enumerate(health_form_names):
    out[f"q13_health_form_rank_{name}"] = pd.to_numeric(df.iloc[:, 34 + i], errors="coerce").values

# Q14 AI 产品形态排序（仅 A-D，删除 E.其他）
for i, name in enumerate(health_form_names):
    out[f"q14_ai_form_rank_{name}"] = pd.to_numeric(df.iloc[:, 40 + i], errors="coerce").values

# Q15 信息来源排序
info_names = ["社交媒体", "搜索引擎", "问AI", "问身边人", "专业人士", "不太找"]
for i, name in enumerate(info_names):
    out[f"q15_info_rank_{name}"] = pd.to_numeric(df.iloc[:, 46 + i], errors="coerce").values

# Q16-Q19 人口统计
out["q16_spending"] = letter(df.iloc[:, 52]).values
out["q17_gender"] = letter(df.iloc[:, 53]).values
out["q18_age"] = letter(df.iloc[:, 54]).values
out["q19_city"] = letter(df.iloc[:, 55]).values

# Q20 内容平台（布尔列，删除"其他"）
platform_names = ["小红书", "抖音", "微信公众号_视频号", "B站", "知乎", "微博"]
for i, name in enumerate(platform_names):
    col_val = df.iloc[:, 56 + i].astype(str).str.strip()
    out[f"q20_platform_{name}"] = (~col_val.isin(["", "nan"])).astype(int).values

# Q21 体重状况
out["q21_weight_status"] = letter(df.iloc[:, 64]).values

# Q22 意愿强度（数值）
out["q22_willingness"] = pd.to_numeric(df.iloc[:, 65], errors="coerce").values

# Q25 MBTI
mbti_raw = df.iloc[:, 68].astype(str).str.strip()
# 提取 MBTI 四字母类型或标记为 "未知"
def parse_mbti(val):
    if not isinstance(val, str) or val in ("", "nan"):
        return np.nan
    m = re.search(r"([A-Z])\.", val)
    if m:
        letter_code = m.group(1)
        if letter_code == "Q":
            return "未知"
        # Map letter to MBTI type
        mbti_map = {
            "A": "INTJ", "B": "INTP", "C": "ENTJ", "D": "ENTP",
            "E": "INFJ", "F": "INFP", "G": "ENFJ", "H": "ENFP",
            "I": "ISTJ", "J": "ISFJ", "K": "ESTJ", "L": "ESFJ",
            "M": "ISTP", "N": "ISFP", "O": "ESTP", "P": "ESFP",
        }
        return mbti_map.get(letter_code, val)
    return val

out["q25_mbti"] = [parse_mbti(v) for v in mbti_raw.values]

# ─── 5. 合并重复的开放题（Q23+Q27, Q24+Q28） ─────────────────────────────────

def merge_open(col_a, col_b, label_a="【回答A】", label_b="【回答B】"):
    """合并两列开放题回答，用明确标签区分来源。"""
    results = []
    for a_val, b_val in zip(col_a, col_b):
        a = str(a_val).strip() if pd.notna(a_val) else ""
        b = str(b_val).strip() if pd.notna(b_val) else ""
        # 过滤无意义回答
        if a in ("", "nan", "无", "没有", "没有过"):
            a = ""
        if b in ("", "nan", "无", "没有", "没有过", "1"):
            b = ""
        if a and b:
            if a == b:
                results.append(a)
            else:
                results.append(f"{label_a}{a}\n{label_b}{b}")
        elif a:
            results.append(a)
        elif b:
            results.append(b)
        else:
            results.append("")
    return results

out["open_coaching"] = merge_open(
    df.iloc[:, 66].values, df.iloc[:, 70].values,
    label_a="【回答A】", label_b="【回答B】"
)

# Q26 失控场景（单列，无需合并）
q26_vals = df.iloc[:, 69].astype(str).str.strip()
out["open_critical_moment"] = q26_vals.where(~q26_vals.isin(["", "nan", "无"])).values

# 联系方式合并（Q24+Q28）
def merge_contact(col_a, col_b):
    results = []
    for a_val, b_val in zip(col_a, col_b):
        a = str(a_val).strip() if pd.notna(a_val) else ""
        b = str(b_val).strip() if pd.notna(b_val) else ""
        if a in ("", "nan", "无"):
            a = ""
        if b in ("", "nan", "无"):
            b = ""
        if a and b:
            if a == b:
                results.append(a)
            else:
                # 两个不同的联系方式，都保留
                results.append(f"{a} / {b}")
        elif a:
            results.append(a)
        elif b:
            results.append(b)
        else:
            results.append("")
    return results

out["contact_info"] = merge_contact(df.iloc[:, 67].values, df.iloc[:, 71].values)

# 地理位置
out["geo_province"] = df.iloc[:, 76].values if len(df.columns) > 76 else ""
out["geo_city"] = df.iloc[:, 77].values if len(df.columns) > 77 else ""

# ─── 6. 保存 ─────────────────────────────────────────────────────────────────

out.to_csv(OUT_CSV, encoding="utf-8-sig", index=False)
print(f"\n清洗后 CSV: {OUT_CSV}")
print(f"行数: {len(out)}, 列数: {len(out.columns)}")
print(f"\n列名列表:")
for i, c in enumerate(out.columns):
    print(f"  {i:3d}: {c}")
