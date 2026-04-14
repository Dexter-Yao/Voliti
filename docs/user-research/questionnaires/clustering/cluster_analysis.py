# ABOUTME: 问卷数据聚类分析脚本（修正版 v2）
# ABOUTME: Gower + Average 层次聚类（主）+ K-Prototypes（参考），已通过方法论 review

import numpy as np
import pandas as pd
import gower
from kmodes.kprototypes import KPrototypes
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score, adjusted_rand_score

BASE_DIR = "/Users/dexter/DexterOS/products/Voliti/docs/user-research/questionnaires"
df = pd.read_csv(f"{BASE_DIR}/cleaned/survey_merged.csv")

# 排除非目标（Q1=D 已稳定，仅 1 人）
df = df[df["intentional_adjustment"] != "D.以前做过，已经比较稳定了"].copy()
df = df.reset_index(drop=True)

# ================================================================
# 一、特征精选（8 个核心行为特征）
# ================================================================
# 选择标准：语义区分力强 + 覆盖核心维度 + 无高缺失率
# n/features = 85/8 ≈ 10.6:1，满足 ≥10:1 经验阈值

q6_map = {
    "A.经常发生（一周好几次）": 4, "B.时不时会有（一周1-2次）": 3,
    "C.偶尔（一个月几次）": 2, "D.很少": 1,
}
q7_map = {
    "A.几乎没影响——不太在意，很快就过去了": 1,
    "B.短暂懊恼——有点后悔，但第二天基本能调整回来": 2,
    'C.当天放大——"既然已经破功了，今天就算了"，当天彻底放开': 3,
    "D.难以恢复——会低落一阵子，或者中断后很难重新捡起来": 4,
}
d_map = {"没遇到": 0, "几乎没影响": 1, "有些影响，能调整回来": 2,
         "影响很大，基本失控": 3, "彻底打乱节奏": 4}
# Q9 私教体验：(跳过) 出现在已被删除的无效问卷中，当前数据集不含此值
# 保留映射作为安全兜底，语义等同"没试过"
q9_coach_map = {"没试过": 0, "试过，没什么用": 1, "试过，有一点用": 2,
                "试过，确实有帮助": 3, "(跳过)": 0}
q11_map = {"A.没花过钱": 0, "B.数百元": 1, "C.一千到三千（不含）": 2,
           "D.三千到一万": 3, "E.一万以上": 4}

cluster_df = pd.DataFrame(index=df.index)

# 数值特征（6 个）
cluster_df["q6_gap_freq"] = df["intention_gap_frequency"].map(q6_map).astype(float)
cluster_df["q7_lapse"] = df["post_lapse_reaction"].map(q7_map).astype(float)
# Q5 干扰均值（聚类用综合指标，画像环节逐项展开解读）
cluster_df["q5_disruption_avg"] = df[
    ["disruption_work_pressure", "disruption_social_dining",
     "disruption_travel", "disruption_emotional"]
].map(lambda v: d_map.get(v, np.nan)).mean(axis=1)
cluster_df["q9_coach_exp"] = df["support_private_coach"].map(q9_coach_map).astype(float)
cluster_df["q11_spending"] = df["annual_spending"].map(q11_map).astype(float)
# 工具多样性（多选合并为计数，避免 7 列二值膨胀）
cluster_df["tool_diversity"] = df["tools_used"].apply(
    lambda v: len([x for x in str(v).split("┋") if x.strip()]) if pd.notna(v) and str(v).strip() not in ("(跳过)", "(空)", "") else 0
).astype(float)

# 类别特征（2 个）
cluster_df["q1_status"] = df["intentional_adjustment"].map({
    "A.是的，我现在正在做": "active",
    "B.试过，但目前没有在坚持": "stopped",
    "C.断断续续地在做，时有时无": "on_off",
}).astype(object)
cluster_df["q8_pref"] = df["preferred_approach"].map({
    "A.习惯自己默默做，不太需要别人参与": "solo",
    "B.希望有人支持，但想私密地进行": "private",
    "C.和身边的人一起做": "social",
    "D.公开做，社交监督对自己有用": "public",
}).astype(object)

num_cols = ["q6_gap_freq", "q7_lapse", "q5_disruption_avg",
            "q9_coach_exp", "q11_spending", "tool_diversity"]
cat_cols = ["q1_status", "q8_pref"]

# 验证 tool_diversity 计数
print("=== tool_diversity 抽样验证 ===")
for i in [0, 1, 2]:
    raw = df.loc[i, "tools_used"]
    computed = cluster_df.loc[i, "tool_diversity"]
    print(f"  [{i}] raw='{str(raw)[:50]}' → diversity={computed}")
print()

print(f"特征矩阵: {cluster_df.shape[0]} 行 × {cluster_df.shape[1]} 列 (数值 {len(num_cols)} + 类别 {len(cat_cols)})")
print(f"样本/特征比: {len(cluster_df) / cluster_df.shape[1]:.1f}:1")

# ================================================================
# 二、Gower 距离矩阵（不做预标准化，Gower 内部自行归一化）
# ================================================================
# Review 结论：MinMaxScaler + Gower = 无意义的预处理，Gower 内部已做 range 归一化
gower_dist = gower.gower_matrix(cluster_df)
np.fill_diagonal(gower_dist, 0)

triu = gower_dist[np.triu_indices_from(gower_dist, k=1)]
print(f"\nGower 距离: 均值={triu.mean():.3f}, 标准差={triu.std():.3f}, CV={triu.std()/triu.mean():.2f}")

# ================================================================
# 三、层次聚类（主方法）— Average Linkage + Gower
# ================================================================
print()
print("=" * 70)
print("  层次聚类 (Average Linkage + Gower)")
print("=" * 70)

condensed = squareform(gower_dist)
Z = linkage(condensed, method="average")

# Silhouette 扫描 + 簇大小
print()
best_k = 2
best_sil = -1
for k in range(2, 7):
    labels = fcluster(Z, t=k, criterion="maxclust") - 1
    sil = silhouette_score(gower_dist, labels, metric="precomputed")
    sizes = sorted([int((labels == c).sum()) for c in range(k)], reverse=True)
    marker = ""
    if min(sizes) <= 2:
        marker = " ← 含单例簇，可能是离群值分离"
    print(f"  K={k}: silhouette={sil:.3f}, 簇大小={sizes}{marker}")
    # 只在无单例簇时更新最优
    if sil > best_sil and min(sizes) > 2:
        best_sil = sil
        best_k = k

# 如果所有 K 都有单例，退回最大 silhouette
if best_sil == -1:
    for k in range(2, 7):
        labels = fcluster(Z, t=k, criterion="maxclust") - 1
        sil = silhouette_score(gower_dist, labels, metric="precomputed")
        if sil > best_sil:
            best_sil = sil
            best_k = k

print(f"\n  选定 K={best_k} (silhouette={best_sil:.3f})")
labels_hier = fcluster(Z, t=best_k, criterion="maxclust") - 1
df["cluster_hier"] = labels_hier

# Dendrogram 数据输出（截断前 20 层，用于辅助判断）
print()
print("=== Dendrogram 截断视图（最后 15 次合并）===")
print(f"{'步骤':>4} {'簇1':>6} {'簇2':>6} {'距离':>8} {'合并后大小':>10}")
n = len(Z)
for i in range(max(0, n - 15), n):
    print(f"  {i+1:>3}  {int(Z[i,0]):>6}  {int(Z[i,1]):>6}  {Z[i,2]:>8.4f}  {int(Z[i,3]):>10}")

# ================================================================
# 四、K-Prototypes（参考，非独立验证）
# ================================================================
print()
print("=" * 70)
print("  K-Prototypes（参考）")
print("=" * 70)

cat_indices = [cluster_df.columns.get_loc(c) for c in cat_cols]
X_arr = cluster_df.values

best_kp_sil = -1
best_kp_labels = None
best_gamma = 0.5

for gamma in [0.3, 0.5, 0.7, 1.0]:
    for seed in range(15):
        kp = KPrototypes(n_clusters=best_k, init="Huang", n_init=1,
                         gamma=gamma, random_state=seed, verbose=0)
        labels = kp.fit_predict(X_arr, categorical=cat_indices)
        sil = silhouette_score(gower_dist, labels, metric="precomputed")
        if sil > best_kp_sil:
            best_kp_sil = sil
            best_kp_labels = labels
            best_gamma = gamma

df["cluster_kp"] = best_kp_labels

# ARI 是唯一有效的跨方法一致性指标（与距离度量无关）
ari_methods = adjusted_rand_score(df["cluster_hier"], df["cluster_kp"])
print(f"  K={best_k}, gamma={best_gamma}, silhouette(参考)={best_kp_sil:.3f}")
print(f"  ARI (层次 vs K-Prototypes): {ari_methods:.3f}")
print(f"  (ARI > 0.5 = 高度一致, 0.3-0.5 = 中等, < 0.3 = 低一致性)")

# ================================================================
# 五、聚类画像（使用层次聚类结果）
# ================================================================
print()
print("=" * 70)
print(f"  聚类画像（K={best_k}，层次聚类）")
print("=" * 70)

# 先验分层
# F 项归属：C001/C014/P012 → 多次（基于逐人行为判断，已与 Dexter 确认）
f_to_multi = {"C001", "C014", "P012"}
def assign_quadrant(row):
    rid, q2, q1 = row["respondent_id"], row["attempt_history"], row["intentional_adjustment"]
    is_active = q1 == "A.是的，我现在正在做"
    if q2 == "F.3年以上，1-5次":
        is_multi = rid in f_to_multi
    elif q2 in ["A.不到1年，1-2次", "C.1-3年，1-2次"]:
        is_multi = False
    else:
        is_multi = True
    if is_active and not is_multi: return "起步行动者"
    if is_active and is_multi: return "反复行动者"
    if not is_active and not is_multi: return "轻度脱轨"
    return "重度脱轨"

df["quadrant"] = df.apply(assign_quadrant, axis=1)

q8_map_full = {
    "A.习惯自己默默做，不太需要别人参与": "solo",
    "B.希望有人支持，但想私密地进行": "private",
    "C.和身边的人一起做": "social",
    "D.公开做，社交监督对自己有用": "public",
}

for c in range(best_k):
    sub = df[df["cluster_hier"] == c]
    print(f"\n--- 簇 {c} ({len(sub)} 人) ---")

    # Demographics
    print(f"  性别: {sub['gender'].value_counts().to_dict()}")
    print(f"  年龄: {sub['age_group'].value_counts().to_dict()}")
    print(f"  工作节奏: {sub['work_rhythm'].str[:15].value_counts().to_dict()}")
    print(f"  CEIBS: {sub['is_ceibs'].sum()}/{len(sub)} ({sub['is_ceibs'].mean()*100:.0f}%)")
    print(f"  留联系方式: {sub['has_contact'].sum()}/{len(sub)} ({sub['has_contact'].mean()*100:.0f}%)")

    # Q1 状态
    q1s = {"A.是的，我现在正在做": "正在做", "B.试过，但目前没有在坚持": "没坚持",
           "C.断断续续地在做，时有时无": "断断续续"}
    print(f"  Q1: {sub['intentional_adjustment'].map(q1s).value_counts().to_dict()}")

    # Q2 尝试历史
    print(f"  Q2: {sub['attempt_history'].str[:12].value_counts().to_dict()}")

    # 先验分层
    print(f"  先验分层: {sub['quadrant'].value_counts().to_dict()}")

    # 核心行为指标
    print(f"  Q6 意图差距均分: {sub['intention_gap_frequency'].map(q6_map).mean():.2f}")
    print(f"  Q7 失控严重度均分: {sub['post_lapse_reaction'].map(q7_map).mean():.2f}")

    # Q5 逐项（聚类用均值，画像逐项展开）
    d_labels = ["工作", "社交", "外出", "情绪"]
    d_raw_cols = ["disruption_work_pressure", "disruption_social_dining",
                  "disruption_travel", "disruption_emotional"]
    d_scores = [sub[dc].map(d_map).mean() for dc in d_raw_cols]
    print(f"  Q5 干扰: {' / '.join(f'{l}={s:.1f}' for l, s in zip(d_labels, d_scores))} (总={sum(d_scores):.1f})")

    # Q5 高影响率
    for dc, dl in zip(d_raw_cols, d_labels):
        high = sub[dc].isin(["影响很大，基本失控", "彻底打乱节奏"]).mean()
        print(f"    {dl} 高影响率: {high*100:.0f}%")

    # Q8
    print(f"  Q8 偏好: {sub['preferred_approach'].map(q8_map_full).value_counts().to_dict()}")
    private_rate = sub["preferred_approach"].isin([
        "A.习惯自己默默做，不太需要别人参与", "B.希望有人支持，但想私密地进行"
    ]).mean()
    print(f"  私密偏好率: {private_rate*100:.0f}%")

    # Q9 各项
    support_cols = ["support_self_only", "support_family_friends", "support_online_community",
                    "support_private_coach", "support_social_checkin"]
    support_labels = ["靠自己", "家人朋友", "线上社群", "私教一对一", "社交打卡"]
    for sc, sl in zip(support_cols, support_labels):
        tried = sub[sc].isin(["试过，确实有帮助", "试过，有一点用", "试过，没什么用"]).sum()
        helpful = (sub[sc] == "试过，确实有帮助").sum()
        print(f"    Q9 {sl}: 试过{tried}/{len(sub)}, 有帮助{helpful}")

    # Q11
    print(f"  Q11 花费: {sub['annual_spending'].value_counts().to_dict()}")
    has_spend = (sub["annual_spending"] != "A.没花过钱").mean()
    print(f"  有花费率: {has_spend*100:.0f}%")

    # 工具多样性
    print(f"  工具多样性均值: {cluster_df.loc[sub.index, 'tool_diversity'].mean():.1f}")

# ================================================================
# 六、聚类 vs 先验分层
# ================================================================
print()
print("=" * 70)
print("  聚类 vs 先验分层交叉表")
print("=" * 70)
ct = pd.crosstab(df["cluster_hier"], df["quadrant"])
print(ct.to_string())
ari_quad = adjusted_rand_score(df["cluster_hier"], df["quadrant"])
print(f"\nARI (聚类 vs 先验分层): {ari_quad:.3f}")

# 保存
df.to_csv(f"{BASE_DIR}/clustering/clustered_data.csv", index=False, encoding="utf-8-sig")
print(f"\n聚类结果已保存: clustering/clustered_data.csv")
