# ABOUTME: 问卷数据清洗与合并脚本
# ABOUTME: 将 CEIBS 校友版和公开版问卷合并为统一 dataset，含排序题 Borda 赋分

import json
import re

import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent

# --- 读取原始数据 ---
df_ceibs = pd.read_excel(BASE / "raw/357373063_按文本_减脂行为与日常习惯调查_40_40.xlsx")
df_public = pd.read_excel(BASE / "raw/357398068_按文本_减脂行为与日常习惯调查（公开版）_52_51.xlsx")

# --- 列名映射（按位置，两份结构完全一致） ---
COLUMN_MAP = {
    0: "respondent_id",
    1: "submitted_at",
    2: "duration",
    # 3: 来源 → DROP
    # 4: 来源详情 → DROP
    # 5: 来自IP → DROP
    6: "intentional_adjustment",
    7: "attempt_history",
    8: "motivation_drivers_rank",
    9: "restart_hesitation_rank",
    10: "disruption_work_pressure",
    11: "disruption_social_dining",
    12: "disruption_travel",
    13: "disruption_emotional",
    14: "intention_gap_frequency",
    15: "intention_gap_reasons_rank",
    16: "post_lapse_reaction",
    17: "preferred_approach",
    18: "support_self_only",
    19: "support_family_friends",
    20: "support_online_community",
    21: "support_private_coach",
    22: "support_social_checkin",
    23: "coach_effectiveness_reason",
    24: "tools_used",
    25: "annual_spending",
    26: "intention_gap_story",
    27: "longest_method",
    28: "one_line_takeaway",
    29: "gender",
    30: "age_group",
    31: "work_rhythm",
    32: "contact_info",
}

DROP_INDICES = {3, 4, 5}

# 无效受访者
# 原始序号 21, 32: 整卷跳过
# 原始序号 11: 所有维度选极端值，疑似快速勾选（95秒完成，Q5 四项全选"彻底打乱"）
INVALID_IDS_CEIBS = {11, 21, 32}  # 原始序号

# --- 排序题选项定义 ---
# Q3: 推动力（4 选项）
MOTIVATION_OPTIONS = {
    "A": "self_dissatisfaction",
    "B": "health_signal",
    "C": "specific_occasion",
    "D": "peer_influence",
}

# Q4: 重新开始犹豫来源（5 选项，公开版比 CEIBS 多 E）
HESITATION_OPTIONS = {
    "A": "psychological_barrier",
    "B": "conditions_not_ready",
    "C": "lack_of_direction",
    "D": "lack_of_urgency",
    "E": "past_failure_distrust",
}

# Q6b: "知道不该但还是做了"原因（4 选项）
INTENTION_GAP_OPTIONS = {
    "A": "physical_need",
    "B": "emotion_or_habit",
    "C": "social_situation",
    "D": "schedule_disruption",
}


def parse_rank_to_scores(raw_value: str, options: dict[str, str]) -> dict[str, float | None]:
    """将排序题原始文本解析为 Borda 赋分。

    示例输入: "A.自我不满...→B.健康信号...→D.身边人..."
    N = len(options)，排第 1 名得 N 分，第 2 名得 N-1 分，依此类推。
    未被排名的选项返回 NaN。
    """
    result = {v: None for v in options.values()}

    if pd.isna(raw_value) or str(raw_value).strip() in ("(跳过)", "(空)", ""):
        return result

    items = str(raw_value).split("→")
    n_total = len(options)

    for rank_pos, item in enumerate(items):
        item = item.strip()
        letter_match = re.match(r"^([A-Z])\.", item)
        if letter_match:
            letter = letter_match.group(1)
            if letter in options:
                score = n_total - rank_pos
                result[options[letter]] = score

    return result


def expand_rank_column(df: pd.DataFrame, col: str, prefix: str, options: dict[str, str]) -> pd.DataFrame:
    """将一列排序题原始文本展开为多列 Borda 得分。"""
    scores = df[col].apply(lambda v: parse_rank_to_scores(v, options))
    score_df = pd.DataFrame(scores.tolist(), index=df.index)
    score_df.columns = [f"{prefix}_{c}" for c in score_df.columns]
    df = pd.concat([df, score_df], axis=1)
    df = df.drop(columns=[col])
    return df


def clean(df: pd.DataFrame, is_ceibs: bool) -> pd.DataFrame:
    """清洗单份问卷数据。"""
    # 删除无效受访者
    if is_ceibs:
        df = df[~df.iloc[:, 0].isin(INVALID_IDS_CEIBS)].copy()

    # 按位置重命名，删除不需要的列
    cols_to_keep = []
    new_names = []
    for i, col in enumerate(df.columns):
        if i in DROP_INDICES:
            continue
        if i in COLUMN_MAP:
            cols_to_keep.append(col)
            new_names.append(COLUMN_MAP[i])

    result = df[cols_to_keep].copy()
    result.columns = new_names

    # 新增字段
    result["is_ceibs"] = is_ceibs
    result["has_contact"] = result["contact_info"].apply(
        lambda v: pd.notna(v) and str(v).strip() not in ("", "(跳过)", "(空)")
    )

    # 展开排序题为 Borda 得分列
    result = expand_rank_column(result, "motivation_drivers_rank", "motivation", MOTIVATION_OPTIONS)
    result = expand_rank_column(result, "restart_hesitation_rank", "hesitation", HESITATION_OPTIONS)
    result = expand_rank_column(result, "intention_gap_reasons_rank", "intention_gap", INTENTION_GAP_OPTIONS)

    return result


df_ceibs_clean = clean(df_ceibs, is_ceibs=True)
df_public_clean = clean(df_public, is_ceibs=False)

# --- 合并 ---
merged = pd.concat([df_ceibs_clean, df_public_clean], ignore_index=True)

# 重新编排 respondent_id（删除无效数据后连续编号）
merged["respondent_id"] = [f"C{i:03d}" if row["is_ceibs"] else f"P{i:03d}"
                           for i, row in zip(
                               merged.groupby("is_ceibs").cumcount() + 1,
                               merged.to_dict("records"))]

# --- 输出 ---
output_path = BASE / "cleaned" / "survey_merged.csv"
merged.to_csv(output_path, index=False, encoding="utf-8-sig")

# 输出 codebook（选项代码 → 描述映射）
codebook = {
    "motivation_options": {f"motivation_{v}": f"{k}. {v}" for k, v in MOTIVATION_OPTIONS.items()},
    "hesitation_options": {f"hesitation_{v}": f"{k}. {v}" for k, v in HESITATION_OPTIONS.items()},
    "intention_gap_options": {f"intention_gap_{v}": f"{k}. {v}" for k, v in INTENTION_GAP_OPTIONS.items()},
    "scoring_rule": "Borda: rank 1 = N points, rank 2 = N-1, ..., unranked = NaN",
}
codebook_path = BASE / "cleaned" / "codebook.json"
with open(codebook_path, "w", encoding="utf-8") as f:
    json.dump(codebook, f, ensure_ascii=False, indent=2)

# --- 摘要 ---
print(f"CEIBS: {(merged['is_ceibs'] == True).sum()} 行")
print(f"公开版: {(merged['is_ceibs'] == False).sum()} 行")
print(f"合并后: {len(merged)} 行, {len(merged.columns)} 列")
print(f"留联系方式: {merged['has_contact'].sum()} 人")
print(f"输出: {output_path}")
print(f"Codebook: {codebook_path}")
print()
print("列名:")
for c in merged.columns:
    print(f"  {c}")
