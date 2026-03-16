"""
Layer C: セグメンテーション（k-meansクラスタリング）

16次元特徴量ベクトルを構築し、職種別 × 雇用形態別にMiniBatchKMeansでクラスタリングする。
結果は geocoded_postings.db に3テーブルとして格納する。

出力テーブル:
  - layer_c_clusters:          各求人のクラスタ割当（employment_type別）
  - layer_c_cluster_profiles:  クラスタプロファイル要約（employment_type別）
  - layer_c_region_heatmap:    セグメント×地域ヒートマップ（employment_type別）

雇用形態別分離: 全体/正職員/パートの3セグメントで独立にクラスタリング

使用法:
  python compute_layer_c.py
  python compute_layer_c.py --db-path path/to/geocoded_postings.db
"""

import argparse
import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import RobustScaler

# --------------------------------------------------------------------------- #
# 定数
# --------------------------------------------------------------------------- #
DB_PATH_DEFAULT = (
    r"C:\Users\fuji1\AppData\Local\Temp\rust-dashboard-deploy"
    r"\data\geocoded_postings.db"
)

# 雇用形態セグメント
EMPLOYMENT_TYPES = ["全体", "正職員", "パート・バイト"]

RANDOM_STATE = 42
K_CANDIDATES = [3, 4, 5, 6, 7]
SILHOUETTE_THRESHOLD_MIN = 0.10   # シルエットスコアの絶対閾値（これ未満はk=4にフォールバック）
MIN_POSTINGS_FOR_CLUSTERING = 100  # これ未満の職種はクラスタリングをスキップ
PCA_COMPONENTS = 4                 # has_*フラグのPCA圧縮次元数
HOURLY_TO_MONTHLY = 173            # 時給→月給変換係数（月間所定労働時間）

# 特徴量の英語名→日本語ラベルマッピング（動的特徴量数に対応）
FEATURE_LABEL_MAP = {
    "salary_min_normalized": "給与水準",
    "salary_range_ratio": "給与レンジ幅",
    "text_entropy": "テキスト情報量",
    "kanji_ratio": "漢字比率",
    "benefits_score": "福利厚生スコア",
    "content_richness_score": "求人充実度",
    "annual_holidays_numeric": "年間休日数",
    "has_salary_range": "給与レンジ有",
    "has_holidays_specified": "休日記載有",
    "is_fulltime": "正職員",
    "is_monthly_salary": "月給制",
    "pca_0": "福利PCA1",
    "pca_1": "福利PCA2",
    "pca_2": "福利PCA3",
    "pca_3": "福利PCA4",
}


# --------------------------------------------------------------------------- #
# ユーティリティ
# --------------------------------------------------------------------------- #
def log(msg: str) -> None:
    """タイムスタンプ付きログ出力"""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def holidays_to_category_score(val: int) -> int:
    """年間休日の数値をカテゴリスコアに変換する。"""
    if val <= 0:
        return 0
    if val >= 120:
        return 4
    if val >= 105:
        return 3
    if val >= 96:
        return 2
    return 1


def holidays_to_category_label(val: int) -> str:
    """年間休日の数値をカテゴリラベルに変換する。"""
    if val <= 0:
        return "記載なし"
    if val >= 120:
        return "120+"
    if val >= 105:
        return "105-119"
    if val >= 96:
        return "96-104"
    return "<96"


# --------------------------------------------------------------------------- #
# DB スキーマ操作 - employment_type カラム追加
# --------------------------------------------------------------------------- #
def get_has_flag_columns(conn: sqlite3.Connection) -> list[str]:
    """postingsテーブルから has_* カラム名を動的に取得する。"""
    cur = conn.execute("PRAGMA table_info(postings)")
    cols = cur.fetchall()
    has_cols = [c[1] for c in cols if c[1].startswith("has_")]
    log(f"  has_*フラグカラム: {len(has_cols)}個 検出")
    return has_cols


def drop_and_create_tables(conn: sqlite3.Connection) -> None:
    """出力テーブルを削除して再作成する（冪等性確保）。"""
    conn.execute("DROP TABLE IF EXISTS layer_c_clusters")
    conn.execute("DROP TABLE IF EXISTS layer_c_cluster_profiles")
    conn.execute("DROP TABLE IF EXISTS layer_c_region_heatmap")

    conn.execute("""
        CREATE TABLE layer_c_clusters (
            posting_id         INTEGER NOT NULL,
            job_type           TEXT NOT NULL,
            employment_type    TEXT NOT NULL DEFAULT '全体',
            cluster_id         INTEGER NOT NULL,
            cluster_label      TEXT NOT NULL,
            distance_to_center REAL NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE layer_c_cluster_profiles (
            job_type              TEXT NOT NULL,
            employment_type       TEXT NOT NULL DEFAULT '全体',
            cluster_id            INTEGER NOT NULL,
            cluster_label         TEXT NOT NULL,
            size                  INTEGER NOT NULL,
            size_pct              REAL NOT NULL,
            salary_min_mean       REAL,
            salary_min_median     REAL,
            text_entropy_mean     REAL,
            benefits_score_mean   REAL,
            content_richness_mean REAL,
            fulltime_pct          REAL,
            has_salary_range_pct  REAL,
            top_benefits          TEXT,
            dominant_employment   TEXT,
            feature_means         TEXT,
            description           TEXT,
            PRIMARY KEY (job_type, employment_type, cluster_id)
        )
    """)

    conn.execute("""
        CREATE TABLE layer_c_region_heatmap (
            job_type        TEXT NOT NULL,
            employment_type TEXT NOT NULL DEFAULT '全体',
            prefecture      TEXT NOT NULL,
            cluster_id      INTEGER NOT NULL,
            cluster_label   TEXT NOT NULL,
            count           INTEGER NOT NULL,
            pct             REAL NOT NULL,
            national_pct    REAL NOT NULL,
            deviation       REAL NOT NULL
        )
    """)

    conn.commit()
    log("出力テーブル3個を作成完了（employment_type対応）")


def create_indexes(conn: sqlite3.Connection) -> None:
    """パフォーマンス向上のためインデックスを作成する。"""
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lc_clusters_posting "
        "ON layer_c_clusters(posting_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lc_clusters_jt_emp "
        "ON layer_c_clusters(job_type, employment_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lc_profiles_jt_emp "
        "ON layer_c_cluster_profiles(job_type, employment_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_lc_heatmap_jt_emp_pref "
        "ON layer_c_region_heatmap(job_type, employment_type, prefecture)"
    )
    conn.commit()
    log("インデックス作成完了")


# --------------------------------------------------------------------------- #
# 特徴量構築
# --------------------------------------------------------------------------- #
def load_job_type_data(
    conn: sqlite3.Connection,
    job_type: str,
    has_cols: list[str],
    employment_type: str = "全体",
) -> pd.DataFrame:
    """指定職種・雇用形態のデータをDataFrameとして読み込む。"""
    has_col_sql = ", ".join(f'"{c}"' for c in has_cols)

    emp_where = ""
    params: tuple = (job_type,)
    if employment_type != "全体":
        emp_where = " AND employment_type = ?"
        params = (job_type, employment_type)

    query = f"""
        SELECT
            id,
            job_type,
            prefecture,
            municipality,
            employment_type,
            salary_type,
            salary_min,
            salary_max,
            text_entropy,
            kanji_ratio,
            benefits_score,
            content_richness_score,
            annual_holidays,
            {has_col_sql}
        FROM postings
        WHERE job_type = ?{emp_where}
    """
    df = pd.read_sql_query(query, conn, params=params)
    return df


def impute_missing_values(df: pd.DataFrame, job_type: str) -> pd.DataFrame:
    """欠損値を補完する。"""
    # salary_min: salary_type別中央値
    for st in df["salary_type"].unique():
        if not st:
            continue
        mask = (df["salary_min"] <= 0) & (df["salary_type"] == st)
        if mask.any():
            median_val = df.loc[
                (df["salary_min"] > 0) & (df["salary_type"] == st),
                "salary_min",
            ].median()
            if pd.notna(median_val) and median_val > 0:
                df.loc[mask, "salary_min"] = median_val

    # salary_type自体が空の場合
    mask_empty_st = (df["salary_min"] <= 0) & (
        (df["salary_type"] == "") | df["salary_type"].isna()
    )
    if mask_empty_st.any():
        median_monthly = df.loc[
            (df["salary_min"] > 0) & (df["salary_type"] == "月給"),
            "salary_min",
        ].median()
        if pd.notna(median_monthly) and median_monthly > 0:
            df.loc[mask_empty_st, "salary_min"] = median_monthly

    # text_entropy: 職種別中央値
    mask_te = df["text_entropy"] <= 0
    if mask_te.any():
        median_te = df.loc[df["text_entropy"] > 0, "text_entropy"].median()
        if pd.notna(median_te):
            df.loc[mask_te, "text_entropy"] = median_te

    # content_richness_score: 職種別中央値
    mask_cr = df["content_richness_score"] <= 0
    if mask_cr.any():
        median_cr = df.loc[
            df["content_richness_score"] > 0, "content_richness_score"
        ].median()
        if pd.notna(median_cr):
            df.loc[mask_cr, "content_richness_score"] = median_cr
        else:
            df.loc[mask_cr, "content_richness_score"] = 0

    # benefits_score: 0で補完
    df["benefits_score"] = df["benefits_score"].fillna(0)

    return df


def build_feature_matrix(
    df: pd.DataFrame,
    has_cols: list[str],
    pca_model: PCA | None = None,
    employment_type: str = "全体",
) -> tuple[np.ndarray, PCA, list[str]]:
    """特徴量行列を構築する。

    employment_type が "全体" 以外の場合、is_fulltime と is_monthly_salary は
    分散がほぼゼロになるため特徴量から除外する。
    """
    n = len(df)

    # 雇用形態別セグメントでは is_fulltime / is_monthly_salary を除外
    exclude_emp_features = (employment_type != "全体")

    # --- 連続特徴量 (7) ---
    salary_normalized = df["salary_min"].values.astype(np.float64).copy()
    is_hourly = (df["salary_type"] == "時給").values
    salary_normalized[is_hourly] *= HOURLY_TO_MONTHLY

    s_min = df["salary_min"].values.astype(np.float64)
    s_max = df["salary_max"].values.astype(np.float64)
    salary_range_ratio = np.zeros(n, dtype=np.float64)
    valid_range = (s_max > 0) & (s_min > 0)
    salary_range_ratio[valid_range] = (
        (s_max[valid_range] - s_min[valid_range]) / s_min[valid_range]
    )
    salary_range_ratio = np.clip(salary_range_ratio, 0.0, 5.0)

    text_entropy = df["text_entropy"].values.astype(np.float64)
    kanji_ratio = df["kanji_ratio"].values.astype(np.float64)
    benefits_score = df["benefits_score"].values.astype(np.float64)
    content_richness = df["content_richness_score"].values.astype(np.float64)

    hol_values = df["annual_holidays"].values.astype(np.float64)
    hol_valid = hol_values[hol_values > 0]
    hol_median = float(np.median(hol_valid)) if len(hol_valid) > 0 else 110.0
    annual_holidays_num = hol_values.copy()
    annual_holidays_num[annual_holidays_num <= 0] = hol_median

    # --- バイナリ特徴量 ---
    has_salary_range = (s_max > 0).astype(np.float64)
    has_holidays = (hol_values > 0).astype(np.float64)

    # --- PCA圧縮 has_*フラグ (4) ---
    has_matrix = df[has_cols].values.astype(np.float64)
    has_matrix = np.nan_to_num(has_matrix, nan=0.0)

    if pca_model is None:
        pca_model = PCA(n_components=PCA_COMPONENTS, random_state=RANDOM_STATE)
        pca_components = pca_model.fit_transform(has_matrix)
    else:
        pca_components = pca_model.transform(has_matrix)

    # 特徴量スタックとカラム名リストを動的に構築
    feature_arrays = [
        salary_normalized,      # 0
        salary_range_ratio,     # 1
        text_entropy,           # 2
        kanji_ratio,            # 3
        benefits_score,         # 4
        content_richness,       # 5
        annual_holidays_num,    # 6
        has_salary_range,       # 7
        has_holidays,           # 8
    ]
    feature_names = [
        "salary_min_normalized",
        "salary_range_ratio",
        "text_entropy",
        "kanji_ratio",
        "benefits_score",
        "content_richness_score",
        "annual_holidays_numeric",
        "has_salary_range",
        "has_holidays_specified",
    ]

    if not exclude_emp_features:
        # 全体セグメントのみ is_fulltime / is_monthly_salary を含める
        is_fulltime = (df["employment_type"] == "正職員").values.astype(np.float64)
        is_monthly = (df["salary_type"] == "月給").values.astype(np.float64)
        feature_arrays.extend([is_fulltime, is_monthly])
        feature_names.extend(["is_fulltime", "is_monthly_salary"])
    else:
        log(f"  雇用形態別セグメント: is_fulltime, is_monthly_salary を除外")

    # PCA成分を追加
    feature_arrays.append(pca_components)
    feature_names.extend([f"pca_{i}" for i in range(PCA_COMPONENTS)])

    features = np.column_stack(feature_arrays)

    return features, pca_model, feature_names


# --------------------------------------------------------------------------- #
# クラスタリング
# --------------------------------------------------------------------------- #
def find_optimal_k(
    X_scaled: np.ndarray,
    k_candidates: list[int],
) -> tuple[int, dict[int, float]]:
    """シルエットスコアに基づいて最適なkを決定する。"""
    scores: dict[int, float] = {}
    best_k = 4
    best_score = -1.0

    n_samples = len(X_scaled)
    sample_size = min(n_samples, 10000)

    for k in k_candidates:
        if k >= n_samples:
            continue
        kmeans = MiniBatchKMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            batch_size=min(1024, n_samples),
            n_init=3,
        )
        labels = kmeans.fit_predict(X_scaled)

        if len(set(labels)) < 2:
            scores[k] = -1.0
            continue

        if n_samples > sample_size:
            rng = np.random.RandomState(RANDOM_STATE)
            idx = rng.choice(n_samples, sample_size, replace=False)
            score = silhouette_score(X_scaled[idx], labels[idx])
        else:
            score = silhouette_score(X_scaled, labels)

        scores[k] = score
        if score > best_score:
            best_score = score
            best_k = k

    # 絶対閾値でフォールバック判定（best_score が低すぎる場合 k=4 にリセット）
    if best_score < SILHOUETTE_THRESHOLD_MIN:
        log(f"  警告: 最高シルエットスコア {best_score:.3f} < 閾値 {SILHOUETTE_THRESHOLD_MIN}")
        best_k = 4

    return best_k, scores


def auto_label_cluster(
    center: np.ndarray,
    feature_names: list[str],
    global_means: np.ndarray,
    global_stds: np.ndarray,
) -> tuple[str, str]:
    """クラスタ中心のプロファイルから自動ラベルと説明文を生成する。"""
    deviations = np.zeros(len(center))
    for i in range(len(center)):
        if global_stds[i] > 1e-9:
            deviations[i] = (center[i] - global_means[i]) / global_stds[i]
        else:
            deviations[i] = 0.0

    label_parts = []
    desc_parts = []

    sorted_idx = np.argsort(np.abs(deviations))[::-1]

    for rank, idx in enumerate(sorted_idx):
        if rank >= 3:
            break
        dev = deviations[idx]
        abs_dev = abs(dev)
        name_en = feature_names[idx]
        name_jp = FEATURE_LABEL_MAP.get(name_en, name_en)

        if abs_dev < 0.3:
            continue

        if name_en == "salary_min_normalized":
            if dev > 0.5:
                label_parts.append("高給与")
                desc_parts.append(f"給与水準が平均より高い(+{dev:.1f}σ)")
            elif dev < -0.5:
                label_parts.append("低給与")
                desc_parts.append(f"給与水準が平均より低い({dev:.1f}σ)")
        elif name_en == "benefits_score":
            if dev > 0.5:
                label_parts.append("高福利厚生")
                desc_parts.append(f"福利厚生スコアが高い(+{dev:.1f}σ)")
            elif dev < -0.5:
                label_parts.append("基本待遇")
                desc_parts.append(f"福利厚生スコアが低い({dev:.1f}σ)")
        elif name_en == "content_richness_score":
            if dev > 0.5:
                label_parts.append("情報充実")
                desc_parts.append(f"求人情報の充実度が高い(+{dev:.1f}σ)")
            elif dev < -0.5:
                label_parts.append("簡素掲載")
                desc_parts.append(f"求人情報の充実度が低い({dev:.1f}σ)")
        elif name_en == "is_fulltime":
            if dev > 0.5:
                label_parts.append("正職員中心")
                desc_parts.append(f"正職員比率が高い(+{dev:.1f}σ)")
            elif dev < -0.5:
                label_parts.append("非常勤中心")
                desc_parts.append(f"パート・非常勤比率が高い({dev:.1f}σ)")
        elif name_en == "is_monthly_salary":
            if dev > 0.5:
                label_parts.append("月給制")
                desc_parts.append(f"月給制が多い(+{dev:.1f}σ)")
            elif dev < -0.5:
                label_parts.append("時給制")
                desc_parts.append(f"時給制が多い({dev:.1f}σ)")
        elif name_en == "text_entropy":
            if dev > 0.5:
                desc_parts.append(f"テキスト情報量が多い(+{dev:.1f}σ)")
            elif dev < -0.5:
                desc_parts.append(f"テキスト情報量が少ない({dev:.1f}σ)")
        elif name_en == "annual_holidays_numeric":
            if dev > 0.5:
                label_parts.append("休日充実")
                desc_parts.append(f"年間休日数が多い(+{dev:.1f}σ)")
            elif dev < -0.5:
                label_parts.append("休日少")
                desc_parts.append(f"年間休日数が少ない({dev:.1f}σ)")
        elif name_en == "salary_range_ratio":
            if dev > 0.5:
                desc_parts.append(f"給与レンジが広い(+{dev:.1f}σ)")
            elif dev < -0.5:
                desc_parts.append(f"給与レンジが狭いまたは固定({dev:.1f}σ)")
        elif name_en == "has_salary_range":
            if dev < -0.5:
                label_parts.append("給与固定")
                desc_parts.append("給与レンジ記載なしが多い")
        elif name_en == "has_holidays_specified":
            if dev < -0.5:
                label_parts.append("休日未記載")
                desc_parts.append("年間休日の記載なしが多い")

    if not label_parts:
        label = "標準型"
        description = "全体平均に近い標準的な求人群"
    else:
        seen = set()
        unique_parts = []
        for p in label_parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        label = "・".join(unique_parts[:3])
        description = "。".join(desc_parts) if desc_parts else label

    return label, description


# --------------------------------------------------------------------------- #
# 職種別クラスタリング（雇用形態対応）
# --------------------------------------------------------------------------- #
def cluster_job_type(
    conn: sqlite3.Connection,
    job_type: str,
    has_cols: list[str],
    employment_type: str = "全体",
) -> dict:
    """単一職種・雇用形態のクラスタリングを実行し結果をDBに書き込む。

    Returns:
        結果サマリ辞書
    """
    log(f"--- 職種: {job_type} [{employment_type}] ---")

    # データ読み込み
    t0 = time.time()
    df = load_job_type_data(conn, job_type, has_cols, employment_type)
    n_total = len(df)
    log(f"  データ読み込み: {n_total:,}件 ({time.time()-t0:.1f}s)")

    # 件数チェック
    if n_total < MIN_POSTINGS_FOR_CLUSTERING:
        log(f"  件数不足({n_total} < {MIN_POSTINGS_FOR_CLUSTERING}) → "
            f"全件クラスタ0に割当")
        rows = [
            (int(row["id"]), job_type, employment_type, 0, "件数不足", 0.0)
            for _, row in df.iterrows()
        ]
        conn.executemany(
            "INSERT INTO layer_c_clusters VALUES (?, ?, ?, ?, ?, ?)", rows
        )
        conn.execute(
            "INSERT INTO layer_c_cluster_profiles VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job_type, employment_type, 0, "件数不足", n_total, 100.0,
                None, None, None, None, None, None, None,
                "[]", "", "{}", "件数不足のためクラスタリング未実施",
            ),
        )
        conn.commit()
        return {"job_type": job_type, "employment_type": employment_type,
                "n": n_total, "k": 0, "status": "skipped"}

    # 欠損値補完
    df = impute_missing_values(df, job_type)

    # 特徴量行列構築
    t1 = time.time()
    features_raw, pca_model, feature_names = build_feature_matrix(
        df, has_cols, employment_type=employment_type
    )
    log(f"  特徴量構築: {features_raw.shape} ({time.time()-t1:.1f}s)")

    # NaN/Inf チェック
    nan_mask = ~np.isfinite(features_raw)
    if nan_mask.any():
        nan_counts = nan_mask.sum(axis=0)
        for i, cnt in enumerate(nan_counts):
            if cnt > 0:
                log(f"  警告: {feature_names[i]} に {cnt}個のNaN/Inf → 0で補完")
        features_raw = np.nan_to_num(features_raw, nan=0.0, posinf=0.0, neginf=0.0)

    # スケーリング
    scaler = RobustScaler()
    features_scaled = scaler.fit_transform(features_raw)

    # 最適k探索
    t2 = time.time()
    best_k, sil_scores = find_optimal_k(features_scaled, K_CANDIDATES)
    sil_str = ", ".join(f"k={k}: {s:.3f}" for k, s in sorted(sil_scores.items()))
    log(f"  シルエットスコア: {sil_str}")
    log(f"  最適k: {best_k} ({time.time()-t2:.1f}s)")

    # 本番クラスタリング
    t3 = time.time()
    kmeans = MiniBatchKMeans(
        n_clusters=best_k,
        random_state=RANDOM_STATE,
        batch_size=min(1024, n_total),
        n_init=10,
    )
    labels = kmeans.fit_predict(features_scaled)

    # クラスタ中心への距離
    distances = np.zeros(n_total)
    for i in range(n_total):
        center = kmeans.cluster_centers_[labels[i]]
        distances[i] = float(np.linalg.norm(features_scaled[i] - center))

    log(f"  クラスタリング完了 ({time.time()-t3:.1f}s)")

    # --- グローバル統計（ラベル生成用） ---
    global_means = features_raw.mean(axis=0)
    global_stds = features_raw.std(axis=0)

    # クラスタ中心を元のスケールに逆変換
    centers_original = scaler.inverse_transform(kmeans.cluster_centers_)

    # --- ラベル生成 ---
    cluster_labels_map: dict[int, str] = {}
    cluster_desc_map: dict[int, str] = {}
    for cid in range(best_k):
        label, desc = auto_label_cluster(
            centers_original[cid], feature_names, global_means, global_stds
        )
        # 同じラベルの重複を防ぐ
        if label in cluster_labels_map.values():
            devs = np.zeros(len(centers_original[cid]))
            for fi in range(len(centers_original[cid])):
                if global_stds[fi] > 1e-9:
                    devs[fi] = (
                        (centers_original[cid][fi] - global_means[fi])
                        / global_stds[fi]
                    )
            sorted_fi = np.argsort(np.abs(devs))[::-1]
            suffix_added = False
            for fi in sorted_fi:
                dev = devs[fi]
                abs_dev = abs(dev)
                if abs_dev < 0.2:
                    continue
                fn = feature_names[fi]
                suffix_map = {
                    "salary_min_normalized": "高給与" if dev > 0 else "低給与",
                    "benefits_score": "高福利" if dev > 0 else "基本待遇",
                    "content_richness_score": "情報充実" if dev > 0 else "簡素",
                    "is_fulltime": "正職員" if dev > 0 else "非常勤",
                    "is_monthly_salary": "月給" if dev > 0 else "時給",
                    "text_entropy": "詳細記載" if dev > 0 else "簡潔",
                    "annual_holidays_numeric": "休日多" if dev > 0 else "休日少",
                    "has_salary_range": "レンジ有" if dev > 0 else "固定給",
                    "has_holidays_specified": "休日記載" if dev > 0 else "休日不明",
                }
                suffix = suffix_map.get(fn, "")
                if suffix and suffix not in label:
                    new_label = f"{label}・{suffix}"
                    if new_label not in cluster_labels_map.values():
                        label = new_label
                        suffix_added = True
                        break
            if not suffix_added:
                label = f"{label}[{cid}]"
        cluster_labels_map[cid] = label
        cluster_desc_map[cid] = desc

    log(f"  ラベル: {cluster_labels_map}")

    # --- layer_c_clusters 書き込み ---
    t4 = time.time()
    cluster_rows = []
    for i in range(n_total):
        cluster_rows.append((
            int(df.iloc[i]["id"]),
            job_type,
            employment_type,
            int(labels[i]),
            cluster_labels_map[int(labels[i])],
            round(float(distances[i]), 4),
        ))

    conn.executemany(
        "INSERT INTO layer_c_clusters VALUES (?, ?, ?, ?, ?, ?)",
        cluster_rows,
    )
    log(f"  layer_c_clusters: {len(cluster_rows):,}件挿入 ({time.time()-t4:.1f}s)")

    # --- layer_c_cluster_profiles 書き込み ---
    t5 = time.time()
    for cid in range(best_k):
        mask = labels == cid
        cluster_df = df.loc[mask]
        cluster_features = features_raw[mask]
        c_size = int(mask.sum())
        c_pct = round(c_size / n_total * 100, 2)

        sal_vals = cluster_df["salary_min"].values
        sal_valid = sal_vals[sal_vals > 0]
        sal_mean = float(np.mean(sal_valid)) if len(sal_valid) > 0 else None
        sal_median = float(np.median(sal_valid)) if len(sal_valid) > 0 else None

        te_vals = cluster_df["text_entropy"].values
        te_valid = te_vals[te_vals > 0]
        te_mean = float(np.mean(te_valid)) if len(te_valid) > 0 else None

        bs_mean = float(cluster_df["benefits_score"].mean())
        cr_mean = float(cluster_df["content_richness_score"].mean())

        ft_pct = round(
            (cluster_df["employment_type"] == "正職員").mean() * 100, 2
        )
        sr_pct = round(
            (cluster_df["salary_max"] > 0).mean() * 100, 2
        )

        benefit_rates = {}
        for hc in has_cols:
            rate = cluster_df[hc].mean()
            display_name = hc.replace("has_", "")
            benefit_rates[display_name] = round(rate * 100, 1)
        top5 = sorted(benefit_rates.items(), key=lambda x: -x[1])[:5]
        top_benefits_json = json.dumps(
            [{"name": name, "pct": pct} for name, pct in top5],
            ensure_ascii=False,
        )

        emp_counts = Counter(cluster_df["employment_type"].dropna().values)
        dominant_emp = emp_counts.most_common(1)[0][0] if emp_counts else ""

        feature_means_dict = {}
        cluster_feature_mean = cluster_features.mean(axis=0)
        for fi, fn in enumerate(feature_names):
            feature_means_dict[fn] = round(float(cluster_feature_mean[fi]), 4)
        feature_means_json = json.dumps(feature_means_dict, ensure_ascii=False)

        conn.execute(
            "INSERT INTO layer_c_cluster_profiles VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job_type,
                employment_type,
                cid,
                cluster_labels_map[cid],
                c_size,
                c_pct,
                round(sal_mean, 0) if sal_mean is not None else None,
                round(sal_median, 0) if sal_median is not None else None,
                round(te_mean, 3) if te_mean is not None else None,
                round(bs_mean, 2),
                round(cr_mean, 2),
                ft_pct,
                sr_pct,
                top_benefits_json,
                dominant_emp,
                feature_means_json,
                cluster_desc_map[cid],
            ),
        )
    log(f"  layer_c_cluster_profiles: {best_k}件挿入 ({time.time()-t5:.1f}s)")

    # --- layer_c_region_heatmap 書き込み ---
    t6 = time.time()

    national_dist: dict[int, float] = {}
    for cid in range(best_k):
        national_dist[cid] = round((labels == cid).sum() / n_total * 100, 2)

    heatmap_rows = []
    prefectures = df["prefecture"].unique()
    for pref in prefectures:
        pref_mask = df["prefecture"].values == pref
        pref_labels = labels[pref_mask]
        pref_total = len(pref_labels)
        if pref_total == 0:
            continue
        for cid in range(best_k):
            c_count = int((pref_labels == cid).sum())
            c_pct = round(c_count / pref_total * 100, 2)
            n_pct = national_dist[cid]
            deviation = round(c_pct - n_pct, 2)
            heatmap_rows.append((
                job_type,
                employment_type,
                pref,
                cid,
                cluster_labels_map[cid],
                c_count,
                c_pct,
                n_pct,
                deviation,
            ))

    conn.executemany(
        "INSERT INTO layer_c_region_heatmap VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        heatmap_rows,
    )
    log(f"  layer_c_region_heatmap: {len(heatmap_rows):,}件挿入 "
        f"({time.time()-t6:.1f}s)")

    conn.commit()

    result = {
        "job_type": job_type,
        "employment_type": employment_type,
        "n": n_total,
        "k": best_k,
        "silhouette_scores": sil_scores,
        "cluster_sizes": {
            cluster_labels_map[cid]: int((labels == cid).sum())
            for cid in range(best_k)
        },
        "status": "completed",
    }
    return result


# --------------------------------------------------------------------------- #
# メイン処理
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Layer C: 求人セグメンテーション（k-meansクラスタリング、雇用形態別分離対応）"
    )
    parser.add_argument(
        "--db-path",
        default=DB_PATH_DEFAULT,
        help="geocoded_postings.db のパス",
    )
    parser.add_argument(
        "--job-type",
        nargs="+",
        default=None,
        metavar="JT",
        help="対象職種（複数指定可）例: --job-type 介護職 看護師",
    )
    parser.add_argument(
        "--employment-type",
        default=None,
        choices=EMPLOYMENT_TYPES,
        help="特定の雇用形態のみ処理する場合に指定（デフォルト: 全セグメント）",
    )
    args, _ = parser.parse_known_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"エラー: DBファイルが見つかりません: {db_path}", file=sys.stderr)
        sys.exit(1)

    log(f"DB: {db_path}")
    log(f"DB size: {db_path.stat().st_size / 1024 / 1024:.1f} MB")

    # 雇用形態セグメント
    emp_types = [args.employment_type] if args.employment_type else EMPLOYMENT_TYPES
    log(f"雇用形態セグメント: {emp_types}")

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")

    try:
        has_cols = get_has_flag_columns(conn)
        if len(has_cols) == 0:
            log("エラー: has_*カラムが見つかりません")
            sys.exit(1)

        # 職種一覧取得
        if args.job_type:
            job_types = args.job_type  # リスト
        else:
            rows = conn.execute(
                "SELECT job_type, COUNT(*) as cnt "
                "FROM postings "
                "GROUP BY job_type "
                "ORDER BY cnt DESC"
            ).fetchall()
            job_types = [r[0] for r in rows]

        log(f"対象職種: {len(job_types)}種")
        for jt in job_types:
            log(f"  - {jt}")

        # テーブル初期化
        if args.job_type is None and args.employment_type is None:
            drop_and_create_tables(conn)
        else:
            existing = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='layer_c_clusters'"
            ).fetchone()
            if existing is None:
                drop_and_create_tables(conn)
            else:
                # 該当データだけ削除して再投入
                for tbl in [
                    "layer_c_clusters",
                    "layer_c_cluster_profiles",
                    "layer_c_region_heatmap",
                ]:
                    if args.job_type and args.employment_type:
                        for jt in job_types:
                            conn.execute(
                                f"DELETE FROM {tbl} WHERE job_type = ? AND employment_type = ?",
                                (jt, args.employment_type),
                            )
                    elif args.job_type:
                        for jt in job_types:
                            conn.execute(
                                f"DELETE FROM {tbl} WHERE job_type = ?",
                                (jt,),
                            )
                    elif args.employment_type:
                        conn.execute(
                            f"DELETE FROM {tbl} WHERE employment_type = ?",
                            (args.employment_type,),
                        )
                conn.commit()
                log(f"既存データ削除完了")

        # 職種 × 雇用形態 のクラスタリング
        t_all = time.time()
        results = []
        total_combos = len(job_types) * len(emp_types)
        combo_idx = 0

        for emp_type in emp_types:
            log(f"\n{'='*40} 雇用形態: {emp_type} {'='*40}")
            for jt in job_types:
                combo_idx += 1
                log(f"\n[{combo_idx}/{total_combos}] 処理開始")
                result = cluster_job_type(conn, jt, has_cols, emp_type)
                results.append(result)
                log(f"  完了: k={result['k']}, {result['status']}")

        # インデックス作成
        create_indexes(conn)

        # サマリ出力
        elapsed = time.time() - t_all
        log(f"\n{'='*60}")
        log(f"全処理完了: {elapsed:.1f}秒")
        log(f"{'='*60}")

        total_postings = 0
        for r in results:
            total_postings += r["n"]
            status_mark = "OK" if r["status"] == "completed" else "SKIP"
            sil_best = ""
            if "silhouette_scores" in r and r["silhouette_scores"]:
                best_s = max(r["silhouette_scores"].values())
                sil_best = f" (sil={best_s:.3f})"
            log(
                f"  [{status_mark}] {r['job_type']} [{r['employment_type']}]: "
                f"{r['n']:,}件 → k={r['k']}{sil_best}"
            )
            if r.get("cluster_sizes"):
                for label, size in r["cluster_sizes"].items():
                    pct = size / r["n"] * 100
                    log(f"         {label}: {size:,}件 ({pct:.1f}%)")

        log(f"\n合計: {total_postings:,}件処理")

        # 検証クエリ
        log("\n=== 検証 ===")
        for tbl in [
            "layer_c_clusters",
            "layer_c_cluster_profiles",
            "layer_c_region_heatmap",
        ]:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            log(f"  {tbl}: {cnt:,}件")

        # 雇用形態別行数
        log("\n  雇用形態別行数:")
        for tbl in ["layer_c_clusters", "layer_c_cluster_profiles", "layer_c_region_heatmap"]:
            rows = conn.execute(
                f"SELECT employment_type, COUNT(*) FROM {tbl} GROUP BY employment_type"
            ).fetchall()
            for emp, cnt in rows:
                log(f"    {tbl} [{emp}]: {cnt:,}")

        # 「全体」セグメントでの整合性チェック
        postings_count = conn.execute(
            "SELECT COUNT(*) FROM postings"
        ).fetchone()[0]
        clusters_total = conn.execute(
            "SELECT COUNT(*) FROM layer_c_clusters WHERE employment_type = '全体'"
        ).fetchone()[0]
        if postings_count == clusters_total:
            log(f"  整合性OK（全体）: postings={postings_count:,} == "
                f"clusters={clusters_total:,}")
        else:
            log(f"  警告（全体）: postings={postings_count:,} != "
                f"clusters={clusters_total:,}")
            missing = conn.execute(
                "SELECT COUNT(*) FROM postings p "
                "LEFT JOIN layer_c_clusters c ON p.id = c.posting_id "
                "AND c.employment_type = '全体' "
                "WHERE c.posting_id IS NULL"
            ).fetchone()[0]
            log(f"  未割当: {missing:,}件")

    finally:
        conn.close()

    log("\n処理完了")


if __name__ == "__main__":
    main()
