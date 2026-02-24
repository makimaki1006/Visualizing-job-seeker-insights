#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gap_detailsを分類して既存classifiedに追加するスクリプト

20260221版classified + gap_details分類結果 → 20260224版classified
dedupはDB builder側に任せる（法人名+アクセスの緩いキーでは正社員/パートを誤削除するため）
"""

import sys
import time
from pathlib import Path
from datetime import datetime

import pandas as pd

from job_medley_analyzer import analyze_dataframe
from segment_classifier import classify_dataframe
from job_posting_parser import DASHBOARD_JOB_TYPES, map_job_type, is_dashboard_job_type

# ディレクトリ
SCRAPING_DIR = Path(r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング")
CLASSIFIED_DIR = Path(__file__).parent / "data" / "classified"

# gap_detailsに含まれるCSVカラム → classifiedに必要なカラムのマッピング
CSV_NAME_MAP = {
    "看護師/准看護師": "看護師・准看護師",
    "介護職/ヘルパー": "介護職・ヘルパー",
    "管理栄養士/栄養士": "管理栄養士・栄養士",
    "調理師/調理スタッフ": "調理師・調理スタッフ",
    "栄養士/栄養士": "管理栄養士・栄養士",
}

# classifiedの出力カラム（classify_all_job_types.pyと同じ）
OUTPUT_COLUMNS = [
    "prefecture", "municipality", "facility_name", "service_type", "facility_scale",
    "salary_min", "salary_max", "salary_type", "salary_detail", "employment_type",
    "headline", "job_description", "requirements", "welcome_requirements", "benefits",
    "working_hours", "holidays", "education_training", "access",
    "special_holidays", "selection_process", "staff_composition",
    "annual_holidays", "tags", "benefits_score", "content_richness_score",
    "tier1_experience", "tier1_career_stage", "tier1_lifestyle", "tier1_appeal", "tier1_urgency",
    "tier2_experience", "tier2_career_stage", "tier2_lifestyle", "tier2_appeal", "tier2_urgency",
    "tier2_combined", "tier3_id", "tier3_label", "tier3_label_short",
    "tier3_label_proposal", "tier3_match_score",
    "jd_categories", "jd_primary_task", "jd_tone", "jd_detail_level",
    "age_20s_score", "age_30s_score", "age_40s_score", "age_50s_score", "age_60s_score",
    "age_decade_primary", "age_decade_all",
    "gender_female_score", "gender_male_score", "gender_signal",
    "lifecycle_stages", "lifecycle_primary",
    "exp_qual_segment", "is_inexperienced", "requires_qualification",
    "wh_shift_type", "wh_start_hour", "wh_end_hour",
    "wh_start_band", "wh_end_band", "wh_break_minutes", "wh_overtime", "wh_has_night",
    "hol_pattern", "hol_weekday_off", "hol_special",
]


def classify_gap_details(gap_csv: Path) -> pd.DataFrame:
    """gap_details CSVを分類してDataFrameとして返す"""
    df = pd.read_csv(gap_csv, encoding="utf-8-sig", low_memory=False)
    df = df.dropna(how="all")
    if len(df) == 0:
        return pd.DataFrame()

    # analyze + classify
    df_analyzed = analyze_dataframe(df)
    df_classified = classify_dataframe(df_analyzed)

    # 必要カラムのみ
    available = [c for c in OUTPUT_COLUMNS if c in df_classified.columns]
    return df_classified[available]


def main():
    t_start = time.time()
    today = datetime.now().strftime("%Y%m%d")

    # gap_details一覧
    gap_files = sorted(SCRAPING_DIR.glob("gap_details_*_20260223.csv"))
    print(f"gap_details: {len(gap_files)}ファイル")

    total_gap_rows = 0
    total_merged = 0
    processed = 0

    for gap_csv in gap_files:
        # ファイル名からソース職種を抽出
        name = gap_csv.stem  # gap_details_介護職・ヘルパー_20260223
        parts = name.split("_")
        source_name = "_".join(parts[2:-1])  # 日付部分を除去

        # ダッシュボード対象チェック
        if not is_dashboard_job_type(source_name):
            print(f"  [スキップ] {source_name}: ダッシュボード対象外")
            continue

        # 既存classified（20260221版）
        existing_classified = None
        for f in sorted(CLASSIFIED_DIR.glob(f"classified_{source_name}_*.csv"), reverse=True):
            # 20260224版とsampleファイルを除外
            if "20260224" not in f.name and "sample" not in f.name:
                existing_classified = f
                break

        if existing_classified is None:
            print(f"  [スキップ] {source_name}: 既存classified不在")
            continue

        print(f"\n{'='*60}")
        print(f"処理: {source_name}")
        print(f"  既存: {existing_classified.name}")
        print(f"  gap:  {gap_csv.name}")

        # gap_detailsの行数チェック
        gap_df_raw = pd.read_csv(gap_csv, encoding="utf-8-sig", low_memory=False)
        gap_rows = len(gap_df_raw.dropna(how="all"))
        print(f"  gap行数: {gap_rows:,}")

        if gap_rows == 0:
            print(f"  → gap空、スキップ")
            continue

        # gap_detailsを分類
        t0 = time.time()
        gap_classified = classify_gap_details(gap_csv)
        print(f"  分類完了: {len(gap_classified):,}行 ({time.time()-t0:.1f}s)")
        total_gap_rows += len(gap_classified)

        # 既存classifiedを読み込み
        df_existing = pd.read_csv(existing_classified, encoding="utf-8-sig", low_memory=False)
        print(f"  既存行数: {len(df_existing):,}")

        # 結合（dedupなし - DB builder側で処理）
        df_merged = pd.concat([df_existing, gap_classified], ignore_index=True)
        total_merged += len(df_merged)

        # 出力
        output_path = CLASSIFIED_DIR / f"classified_{source_name}_{today}.csv"
        df_merged.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"  出力: {output_path.name} ({len(df_merged):,}行)")
        processed += 1

    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"完了: {processed}職種処理")
    print(f"  追加gap行数: {total_gap_rows:,}")
    print(f"  合計行数: {total_merged:,}")
    print(f"  処理時間: {elapsed:.1f}秒")


if __name__ == "__main__":
    main()
