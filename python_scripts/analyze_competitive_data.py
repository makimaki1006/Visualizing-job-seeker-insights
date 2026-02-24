"""
求人データ競合分析スクリプト

ローカルSQLite DB (local_competitive.db) を読み込み、以下の分析を実行:
1. 施設形態3層分類 (facility_type_mapping.json)
2. 給与分析 (salary_analysis.json)
3. 地域クラスタリング (prefecture_clusters.json)
"""

import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# パス設定
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "nicegui_app" / "data" / "local_competitive.db"
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "analysis_results"


# =============================================================================
# 施設形態3層分類の定義
# =============================================================================

# 大カテゴリのキーマッピング
MAJOR_CATEGORY_KEYS = {
    "介護・福祉事業所": "kaigo_fukushi",
    "美容・サロン・ジム": "beauty_salon",
    "薬局・ドラッグストア": "pharmacy",
    "代替医療・リラクゼーション": "alternative_medicine",
    "病院・クリニック": "hospital_clinic",
    "歯科診療所・技工所": "dental",
    "訪問看護ステーション": "home_nursing",
    "その他（企業・学校等）": "other_corporate",
    "保育園・幼稚園": "nursery_kindergarten",
}

# 機能グループ定義: {大カテゴリキー: {グループキー: {"label": str, "sub_elements": [str]}}}
FUNCTIONAL_GROUPS = {
    "kaigo_fukushi": {
        "tsusho": {
            "label": "通所系",
            "sub_elements": ["通所介護・デイサービス", "通所リハ・デイケア"],
        },
        "nyusho": {
            "label": "入所系",
            "sub_elements": [
                "特別養護老人ホーム",
                "介護付き有料老人ホーム",
                "住宅型有料老人ホーム",
                "グループホーム",
                "介護老人保健施設",
                "サービス付き高齢者向け住宅",
                "軽費老人ホーム",
                "ショートステイ",
            ],
        },
        "houmon": {
            "label": "訪問系",
            "sub_elements": [
                "訪問介護",
                "訪問入浴",
                "定期巡回・随時対応サービス",
                "介護タクシー",
            ],
        },
        "jido_fukushi": {
            "label": "児童福祉系",
            "sub_elements": [
                "放課後等デイサービス",
                "障害児相談支援",
            ],
        },
        "shogai_fukushi": {
            "label": "障害福祉系",
            "sub_elements": [
                "障害者支援",
                "就労継続支援B型",
                "就労継続支援A型",
                "就労移行支援",
                "計画相談支援",
                "特定相談支援",
                "一般相談支援",
                "地域定着支援",
                "地域移行支援",
            ],
        },
        "kyotaku_chiiki": {
            "label": "居宅・地域支援系",
            "sub_elements": [
                "居宅介護支援事業所",
                "小規模多機能型居宅介護",
                "地域包括支援センター",
                "福祉用具貸与/販売",
            ],
        },
    },
    "beauty_salon": {
        "hair": {
            "label": "ヘア系",
            "sub_elements": ["美容院・ヘアサロン", "理容室"],
        },
        "eye_nail": {
            "label": "アイ・ネイル系",
            "sub_elements": ["まつげ・アイラッシュサロン", "ネイルサロン"],
        },
        "esthetic": {
            "label": "エステ・フィットネス系",
            "sub_elements": ["美容・エステサロン", "スポーツ・フィットネスクラブ"],
        },
    },
    "pharmacy": {
        "chozai": {
            "label": "調剤系",
            "sub_elements": ["調剤薬局", "調剤併設型", "院内調剤", "漢方"],
        },
        "retail": {
            "label": "小売・在宅系",
            "sub_elements": ["ドラッグストア", "OTC販売", "在宅サービス"],
        },
    },
    "alternative_medicine": {
        "seikotsuin": {
            "label": "接骨・整体系",
            "sub_elements": ["整骨院・接骨院", "整体院", "外傷処置"],
        },
        "shinkyu": {
            "label": "鍼灸・美容鍼系",
            "sub_elements": ["鍼灸院", "美容鍼"],
        },
        "rehabilitation": {
            "label": "リハビリ・運動療法系",
            "sub_elements": ["運動療法", "リハビリ", "機能訓練"],
        },
        "houmon_chiryo": {
            "label": "訪問・リラクゼーション系",
            "sub_elements": ["訪問治療院", "リラクゼーション", "介護支援"],
        },
    },
    "dental": {
        "general": {
            "label": "一般歯科系",
            "sub_elements": [
                "一般歯科",
                "小児歯科",
                "歯周治療",
                "口腔外科",
                "訪問歯科",
                "入れ歯・補綴",
            ],
        },
        "aesthetic": {
            "label": "審美・矯正系",
            "sub_elements": [
                "審美歯科",
                "ホワイトニング",
                "矯正歯科",
                "インプラント",
                "デンタルエステ",
                "予防歯科",
            ],
        },
        "lab": {
            "label": "技工系",
            "sub_elements": ["歯科技工所"],
        },
    },
    "home_nursing": {
        "houmon_kango": {
            "label": "訪問看護・リハビリ",
            "sub_elements": ["訪問看護", "訪問リハビリ"],
        },
    },
    "other_corporate": {
        "corporate_school": {
            "label": "企業・学校",
            "sub_elements": ["企業", "学校"],
        },
    },
    "nursery_kindergarten": {
        "ninka": {
            "label": "認可・認証系",
            "sub_elements": [
                "認証・認可保育所",
                "認定こども園",
                "認可外保育所",
                "小規模保育園",
            ],
        },
        "youchien_gakudo": {
            "label": "幼稚園・学童系",
            "sub_elements": [
                "幼稚園",
                "学童保育・放課後児童クラブ",
                "幼児教室",
            ],
        },
    },
    "hospital_clinic": {},
}

# 切り詰め名から正規名への正規化マップ（DBに「…」で切れたデータがある）
TRUNCATED_TO_CANONICAL = {
    "居宅介護支援事業所…": "居宅介護支援事業所",
    "特別養護老…": "特別養護老人ホーム",
    "定期巡回・随時…": "定期巡回・随時対応サービス",
    "サービス付…": "サービス付き高齢者向け住宅",
    "放課後等デイサービ…": "放課後等デイサービス",
    "サービス付き高…": "サービス付き高齢者向け住宅",
    "地域移行支援…": "地域移行支援",
    "軽費老人…": "軽費老人ホーム",
    "訪問…": "訪問介護",
    "就労継続支援B型…": "就労継続支援B型",
    "福祉用具貸与…": "福祉用具貸与/販売",
    "居宅介護支援事…": "居宅介護支援事業所",
    "障害児…": "障害児相談支援",
    "就…": "就労移行支援",
    "放課後等デイサービス…": "放課後等デイサービス",
    "放課後等デイサー…": "放課後等デイサービス",
    "…": "",
    "放課後等デ…": "放課後等デイサービス",
    "小規模多機能型居宅…": "小規模多機能型居宅介護",
    "小規模多機…": "小規模多機能型居宅介護",
    "特…": "特別養護老人ホーム",
    "地域包括支援セン…": "地域包括支援センター",
    "ショ…": "ショートステイ",
    "地域移…": "地域移行支援",
}


def get_connection() -> sqlite3.Connection:
    """SQLiteデータベース接続を取得"""
    if not DB_PATH.exists():
        print(f"エラー: DB not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(str(DB_PATH))


# =============================================================================
# 機能1: 施設形態3層分類
# =============================================================================


def _build_sub_element_index() -> dict:
    """サブ要素 → {major, group} の逆引きインデックスを構築"""
    index = {}
    for major_key, groups in FUNCTIONAL_GROUPS.items():
        for group_key, group_def in groups.items():
            for elem in group_def["sub_elements"]:
                index[elem] = {"major": major_key, "group": group_key}
    return index


def _normalize_sub_element(raw: str) -> str:
    """切り詰め名を正規名に正規化"""
    return TRUNCATED_TO_CANONICAL.get(raw, raw)


def analyze_facility_types(conn: sqlite3.Connection) -> dict:
    """施設形態3層分類を生成"""
    print("=== 施設形態3層分類の構築 ===")

    cur = conn.cursor()
    cur.execute(
        "SELECT facility_type, count(*) as cnt FROM job_postings "
        "GROUP BY facility_type ORDER BY cnt DESC"
    )
    rows = cur.fetchall()

    # 大カテゴリ別件数集計
    major_counts = Counter()
    # raw_to_major マッピング
    raw_to_major = {}
    # サブ要素別件数（正規化後）
    sub_element_counts = defaultdict(lambda: defaultdict(int))

    for ft_raw, cnt in rows:
        if not ft_raw or ft_raw.strip() == "":
            major_label = "病院・クリニック"
            major_key = MAJOR_CATEGORY_KEYS[major_label]
            major_counts[major_label] += cnt
            raw_to_major[""] = major_key
            continue

        parts = ft_raw.split(" ", 1)
        major_label = parts[0]
        major_key = MAJOR_CATEGORY_KEYS.get(major_label)
        if major_key is None:
            print(f"  警告: 未知の大カテゴリ '{major_label}' (件数: {cnt})")
            continue

        major_counts[major_label] += cnt
        raw_to_major[ft_raw] = major_key

        if len(parts) > 1:
            # カンマ区切りのサブカテゴリを分解
            subs = [s.strip() for s in parts[1].split("、")]
            for sub in subs:
                normalized = _normalize_sub_element(sub)
                if normalized:
                    sub_element_counts[major_key][normalized] += cnt

    # サブ要素インデックス構築
    sub_element_index = _build_sub_element_index()

    # major_categories 配列を構築
    major_categories = []
    for label, key in MAJOR_CATEGORY_KEYS.items():
        count = major_counts.get(label, 0)
        groups_def = FUNCTIONAL_GROUPS.get(key, {})
        functional_groups = []
        for group_key, group_def in groups_def.items():
            group_count = sum(
                sub_element_counts[key].get(elem, 0)
                for elem in group_def["sub_elements"]
            )
            sub_elements_with_count = []
            for elem in group_def["sub_elements"]:
                elem_count = sub_element_counts[key].get(elem, 0)
                sub_elements_with_count.append({"name": elem, "count": elem_count})
            functional_groups.append(
                {
                    "key": group_key,
                    "label": group_def["label"],
                    "count": group_count,
                    "sub_elements": sub_elements_with_count,
                }
            )
        major_categories.append(
            {
                "key": key,
                "label": label,
                "count": count,
                "functional_groups": functional_groups,
            }
        )

    # カウント降順でソート
    major_categories.sort(key=lambda x: x["count"], reverse=True)

    # 未分類サブ要素チェック
    all_defined_subs = set(sub_element_index.keys())
    all_found_subs = set()
    for key_subs in sub_element_counts.values():
        all_found_subs.update(key_subs.keys())
    unclassified = all_found_subs - all_defined_subs
    if unclassified:
        print(f"  未分類サブ要素: {unclassified}")

    result = {
        "major_categories": major_categories,
        "sub_element_index": sub_element_index,
        "raw_to_major": raw_to_major,
        "total_records": sum(major_counts.values()),
        "unique_facility_types": len(rows),
    }

    print(f"  大カテゴリ: {len(major_categories)}種")
    print(f"  機能グループ: {sum(len(mc['functional_groups']) for mc in major_categories)}種")
    print(f"  サブ要素: {len(sub_element_index)}種")
    print(f"  総レコード: {result['total_records']:,}")
    return result


# =============================================================================
# 機能2: 給与分析
# =============================================================================


def _load_salary_dataframe(conn: sqlite3.Connection) -> pd.DataFrame:
    """給与分析用のDataFrameを読み込み、外れ値をフィルタ"""
    query = """
    SELECT job_type, prefecture, employment_type, facility_type,
           salary_min, salary_max, salary_type, inexperienced_ok,
           annual_holidays, expected_annual_income
    FROM job_postings
    WHERE salary_min IS NOT NULL AND salary_min > 0
    """
    df = pd.read_sql_query(query, conn)

    original_len = len(df)
    # 外れ値フィルタ
    df = df[df["salary_min"] >= 50000]
    df = df[(df["salary_max"].isna()) | (df["salary_max"] <= 2000000)]
    df = df[(df["annual_holidays"].isna()) | (df["annual_holidays"] <= 365)]

    filtered_len = len(df)
    print(f"  外れ値フィルタ: {original_len:,} -> {filtered_len:,} ({original_len - filtered_len:,}件除外)")

    # 大カテゴリ付与
    df["major_category"] = df["facility_type"].apply(_extract_major_category)
    return df


def _extract_major_category(ft: str) -> str:
    """facility_type文字列から大カテゴリラベルを抽出"""
    if not ft or pd.isna(ft) or ft.strip() == "":
        return "病院・クリニック"
    parts = ft.split(" ", 1)
    return parts[0]


def _salary_stats(series: pd.Series) -> dict:
    """給与系列の基本統計量を計算"""
    if len(series) == 0:
        return {"count": 0, "mean": 0, "median": 0, "q25": 0, "q75": 0, "std": 0}
    return {
        "count": int(len(series)),
        "mean": int(series.mean()),
        "median": int(series.median()),
        "q25": int(series.quantile(0.25)),
        "q75": int(series.quantile(0.75)),
        "std": int(series.std()) if len(series) > 1 else 0,
    }


def analyze_salary(conn: sqlite3.Connection) -> dict:
    """給与分析を実行"""
    print("\n=== 給与分析 ===")
    df = _load_salary_dataframe(conn)

    # (1) 職種×雇用形態の給与統計
    print("  職種×雇用形態 集計中...")
    job_emp_stats = {}
    for (job_type, emp_type), group in df.groupby(["job_type", "employment_type"]):
        if not emp_type:
            continue
        key = f"{job_type}|{emp_type}"
        job_emp_stats[key] = {
            "job_type": job_type,
            "employment_type": emp_type,
            "salary_min": _salary_stats(group["salary_min"]),
        }
        valid_max = group["salary_max"].dropna()
        if len(valid_max) > 0:
            job_emp_stats[key]["salary_max"] = _salary_stats(valid_max)

    # (2) 職種×都道府県の給与統計（正社員のみ）
    print("  職種×都道府県 集計中...")
    seishoku = df[df["employment_type"] == "正社員"]
    job_pref_stats = {}
    for (job_type, pref), group in seishoku.groupby(["job_type", "prefecture"]):
        key = f"{job_type}|{pref}"
        job_pref_stats[key] = {
            "job_type": job_type,
            "prefecture": pref,
            "salary_min": _salary_stats(group["salary_min"]),
            "count": int(len(group)),
        }

    # (3) 未経験OK vs 経験者の待遇差
    print("  未経験OK vs 経験者 集計中...")
    inexperience_stats = {}
    for job_type, group in df.groupby("job_type"):
        inex_ok = group[group["inexperienced_ok"] == 1]
        inex_no = group[group["inexperienced_ok"] == 0]
        diff_mean = 0
        if len(inex_ok) > 0 and len(inex_no) > 0:
            diff_mean = int(inex_no["salary_min"].mean() - inex_ok["salary_min"].mean())
        inexperience_stats[job_type] = {
            "inexperienced_ok": {
                "count": int(len(inex_ok)),
                "salary_min": _salary_stats(inex_ok["salary_min"]) if len(inex_ok) > 0 else _salary_stats(pd.Series(dtype=float)),
            },
            "experienced_only": {
                "count": int(len(inex_no)),
                "salary_min": _salary_stats(inex_no["salary_min"]) if len(inex_no) > 0 else _salary_stats(pd.Series(dtype=float)),
            },
            "salary_gap": diff_mean,
        }

    # (4) 施設形態(大カテゴリ)別給与水準
    print("  施設形態別給与水準 集計中...")
    facility_salary = {}
    for major_cat, group in df.groupby("major_category"):
        facility_salary[major_cat] = {
            "count": int(len(group)),
            "salary_min": _salary_stats(group["salary_min"]),
        }
        # 雇用形態別内訳
        emp_breakdown = {}
        for emp_type, emp_group in group.groupby("employment_type"):
            if not emp_type:
                continue
            emp_breakdown[emp_type] = {
                "count": int(len(emp_group)),
                "salary_min": _salary_stats(emp_group["salary_min"]),
            }
        facility_salary[major_cat]["by_employment_type"] = emp_breakdown

    result = {
        "job_employment_type_stats": job_emp_stats,
        "job_prefecture_stats": job_pref_stats,
        "inexperience_comparison": inexperience_stats,
        "facility_category_salary": facility_salary,
        "filter_criteria": {
            "salary_min_threshold": 50000,
            "salary_max_threshold": 2000000,
            "annual_holidays_threshold": 365,
        },
        "total_analyzed_records": int(len(df)),
    }

    print(f"  職種×雇用形態: {len(job_emp_stats)}パターン")
    print(f"  職種×都道府県: {len(job_pref_stats)}パターン")
    print(f"  未経験比較: {len(inexperience_stats)}職種")
    print(f"  施設形態別: {len(facility_salary)}カテゴリ")
    return result


# =============================================================================
# 機能3: 地域クラスタリング
# =============================================================================


def analyze_prefecture_clusters(conn: sqlite3.Connection) -> dict:
    """K-Meansで都道府県をクラスタリング"""
    print("\n=== 地域クラスタリング ===")

    query = """
    SELECT prefecture, job_type, employment_type, facility_type,
           salary_min, salary_max
    FROM job_postings
    WHERE salary_min IS NOT NULL AND salary_min >= 50000
      AND (salary_max IS NULL OR salary_max <= 2000000)
    """
    df = pd.read_sql_query(query, conn)
    df["major_category"] = df["facility_type"].apply(_extract_major_category)

    # 特徴量を都道府県ごとに集計
    print("  特徴量構築中...")
    features = []
    prefectures = sorted(df["prefecture"].unique())

    for pref in prefectures:
        pref_df = pref_df_raw = df[df["prefecture"] == pref]
        n = len(pref_df)
        if n < 10:
            continue

        # 求人密度（件数）
        job_count = n

        # 平均給与（salary_min）
        avg_salary = pref_df["salary_min"].mean()

        # 正社員比率
        seishoku_ratio = len(pref_df[pref_df["employment_type"] == "正社員"]) / n

        # 未経験OK率（NULLでないもの対象）
        # ここではDB全体からinexperienced_okを取得する必要がある
        # 簡略化: salary_minフィルタ済みデータから集計

        # 施設形態分布（主要5カテゴリの比率）
        major_counts = pref_df["major_category"].value_counts(normalize=True)
        kaigo_ratio = major_counts.get("介護・福祉事業所", 0)
        hospital_ratio = major_counts.get("病院・クリニック", 0)
        beauty_ratio = major_counts.get("美容・サロン・ジム", 0)
        pharmacy_ratio = major_counts.get("薬局・ドラッグストア", 0)
        dental_ratio = major_counts.get("歯科診療所・技工所", 0)

        # 雇用形態多様性（パート比率）
        part_ratio = len(pref_df[pref_df["employment_type"] == "パート・バイト"]) / n

        features.append(
            {
                "prefecture": pref,
                "job_count": job_count,
                "avg_salary": avg_salary,
                "seishoku_ratio": seishoku_ratio,
                "part_ratio": part_ratio,
                "kaigo_ratio": kaigo_ratio,
                "hospital_ratio": hospital_ratio,
                "beauty_ratio": beauty_ratio,
                "pharmacy_ratio": pharmacy_ratio,
                "dental_ratio": dental_ratio,
            }
        )

    feat_df = pd.DataFrame(features)
    pref_names = feat_df["prefecture"].tolist()
    feature_cols = [
        "job_count",
        "avg_salary",
        "seishoku_ratio",
        "part_ratio",
        "kaigo_ratio",
        "hospital_ratio",
        "beauty_ratio",
        "pharmacy_ratio",
        "dental_ratio",
    ]
    X = feat_df[feature_cols].values

    # 標準化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 最適k選択（シルエットスコア）
    print("  最適クラスタ数選定中...")
    from sklearn.metrics import silhouette_score

    best_k = 4
    best_score = -1
    k_scores = {}
    for k in range(3, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        k_scores[k] = round(float(score), 4)
        print(f"    k={k}: silhouette={score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k

    print(f"  最適k = {best_k} (silhouette={best_score:.4f})")

    # 最適kでクラスタリング実行
    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    # クラスタ別の都道府県リストと特性
    clusters = defaultdict(list)
    for i, pref in enumerate(pref_names):
        clusters[int(labels[i])].append(
            {
                "prefecture": pref,
                "features": {col: round(float(feat_df.iloc[i][col]), 2) for col in feature_cols},
            }
        )

    # クラスタ中心の特性を解釈
    cluster_summaries = {}
    centers_original = scaler.inverse_transform(km.cluster_centers_)
    for cluster_id in range(best_k):
        center = centers_original[cluster_id]
        center_dict = {col: round(float(center[j]), 2) for j, col in enumerate(feature_cols)}
        members = [m["prefecture"] for m in clusters[cluster_id]]

        # 特性ラベル自動付与
        label = _interpret_cluster(center_dict, centers_original, feature_cols)

        cluster_summaries[str(cluster_id)] = {
            "label": label,
            "center": center_dict,
            "prefectures": members,
            "size": len(members),
        }

    result = {
        "optimal_k": best_k,
        "silhouette_scores": k_scores,
        "best_silhouette": round(float(best_score), 4),
        "feature_columns": feature_cols,
        "clusters": cluster_summaries,
        "total_prefectures": len(pref_names),
    }

    for cid, summary in cluster_summaries.items():
        print(f"  クラスタ{cid} ({summary['label']}): {summary['size']}県 - {', '.join(summary['prefectures'][:5])}...")

    return result


def _interpret_cluster(center: dict, all_centers: np.ndarray, cols: list) -> str:
    """クラスタ中心の特性からラベルを生成"""
    labels = []

    # 求人数が多いか少ないか
    avg_count = np.mean(all_centers[:, cols.index("job_count")])
    if center["job_count"] > avg_count * 1.5:
        labels.append("大都市圏")
    elif center["job_count"] < avg_count * 0.5:
        labels.append("地方")

    # 給与水準
    avg_salary = np.mean(all_centers[:, cols.index("avg_salary")])
    if center["avg_salary"] > avg_salary * 1.05:
        labels.append("高給与")
    elif center["avg_salary"] < avg_salary * 0.95:
        labels.append("低給与")

    # 介護比率
    avg_kaigo = np.mean(all_centers[:, cols.index("kaigo_ratio")])
    if center["kaigo_ratio"] > avg_kaigo * 1.2:
        labels.append("介護中心")

    if not labels:
        labels.append("標準型")

    return "・".join(labels)


# =============================================================================
# メイン実行
# =============================================================================


def main():
    """メインエントリポイント"""
    sys.stdout.reconfigure(encoding="utf-8")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"DB: {DB_PATH}")
    print(f"出力先: {OUTPUT_DIR}")
    print()

    conn = get_connection()

    try:
        # (1) 施設形態3層分類
        facility_mapping = analyze_facility_types(conn)
        output_path = OUTPUT_DIR / "facility_type_mapping.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(facility_mapping, f, ensure_ascii=False, indent=2)
        print(f"  -> {output_path}")

        # (2) 給与分析
        salary_analysis = analyze_salary(conn)
        output_path = OUTPUT_DIR / "salary_analysis.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(salary_analysis, f, ensure_ascii=False, indent=2)
        print(f"  -> {output_path}")

        # (3) 地域クラスタリング
        clusters = analyze_prefecture_clusters(conn)
        output_path = OUTPUT_DIR / "prefecture_clusters.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(clusters, f, ensure_ascii=False, indent=2)
        print(f"  -> {output_path}")

        print("\n=== 全分析完了 ===")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
