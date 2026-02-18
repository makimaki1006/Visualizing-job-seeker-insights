#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全17職種のスクレイピングCSVを分類してclassified CSVを出力する

analyze_dataframe() → classify_dataframe() の2段パイプラインで
Tier1/Tier2/Tier3 + タグ + テキスト特徴を付与したCSVを生成する。
出力CSVは aggregate_segments.py の入力として利用する。

使用例:
    python classify_all_job_types.py
    python classify_all_job_types.py --job_type "看護師・准看護師"
    python classify_all_job_types.py --output_dir data/classified

実行後:
    python aggregate_segments.py \
        --input "data/classified/classified_*.csv" \
        --output "../rust_dashboard/data/segment_summary.db"
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from job_medley_analyzer import analyze_dataframe
from segment_classifier import classify_dataframe
from job_posting_parser import (
    DASHBOARD_JOB_TYPES,
    JOB_TYPE_MAPPING,
    is_dashboard_job_type,
    map_job_type,
)

# スクレイピングCSV格納ディレクトリ
SCRAPING_DIR = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング_2026_02_15"
)

# 出力ディレクトリ
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "data" / "classified"


def find_all_csvs(job_type: str = None) -> list[tuple[Path, str]]:
    """ダッシュボード対象17職種のCSVを検索

    Returns:
        [(csv_path, db_job_type), ...]
    """
    results = []
    all_csvs = sorted(SCRAPING_DIR.glob("job_urls_*_details_output.csv"))

    for csv_path in all_csvs:
        source = csv_path.stem.replace("job_urls_", "").replace("_details_output", "")

        if not is_dashboard_job_type(source):
            continue

        db_name = map_job_type(source)

        if job_type and job_type not in source and job_type != db_name:
            continue

        results.append((csv_path, source))

    return results


def classify_csv(csv_path: Path, source_job_type: str, output_dir: Path) -> dict:
    """1つのCSVを分類してclassified CSVとして出力

    Returns:
        処理結果のサマリーdict
    """
    t0 = time.time()
    print(f"\n{'='*60}")
    print(f"処理: {csv_path.name}")
    print(f"ソース職種: {source_job_type}")

    # CSV読み込み
    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
    df = df.dropna(how="all")
    initial_rows = len(df)
    print(f"行数: {initial_rows:,}")

    # Step 1: 属性抽出（カラムマッピング + タグ + スコア）
    print("  Step 1: analyze_dataframe ...")
    t1 = time.time()
    df_analyzed = analyze_dataframe(df)
    print(f"  → {time.time() - t1:.1f}s")

    # Step 2: 3層分類（Tier1/Tier2/Tier3）
    print("  Step 2: classify_dataframe ...")
    t2 = time.time()
    df_classified = classify_dataframe(df_analyzed)
    print(f"  → {time.time() - t2:.1f}s")

    # 出力ファイル名: classified_{ソース職種}_{日付}.csv
    today = datetime.now().strftime("%Y%m%d")
    output_name = f"classified_{source_job_type}_{today}.csv"
    output_path = output_dir / output_name

    # 出力カラム選定（aggregate_segments.pyで必要なカラム）
    output_columns = [
        # 地域情報
        "prefecture", "municipality",
        # 施設情報
        "facility_name", "service_type", "facility_scale",
        # 給与情報
        "salary_min", "salary_max", "salary_type", "salary_detail",
        "employment_type",
        # テキスト情報（text_features用）
        "headline", "job_description", "requirements",
        "welcome_requirements", "benefits", "working_hours",
        "holidays", "education_training", "access",
        "special_holidays", "selection_process",
        "staff_composition",
        # 属性
        "annual_holidays", "tags", "benefits_score",
        "content_richness_score",
        # Tier1 分類結果
        "tier1_experience", "tier1_career_stage",
        "tier1_lifestyle", "tier1_appeal", "tier1_urgency",
        # Tier2 ラベル
        "tier2_experience", "tier2_career_stage",
        "tier2_lifestyle", "tier2_appeal", "tier2_urgency",
        "tier2_combined",
        # Tier3
        "tier3_id", "tier3_label", "tier3_label_short",
        "tier3_label_proposal", "tier3_match_score",
        # 仕事内容分析 (v1.2)
        "jd_categories", "jd_primary_task", "jd_tone", "jd_detail_level",
        # 年代セグメント (v2.0)
        "age_20s_score", "age_30s_score", "age_40s_score",
        "age_50s_score", "age_60s_score",
        "age_decade_primary", "age_decade_all",
        # 性別・ライフステージ (v2.0)
        "gender_female_score", "gender_male_score", "gender_signal",
        "lifecycle_stages", "lifecycle_primary",
        # 未経験×資格 (v2.0)
        "exp_qual_segment", "is_inexperienced", "requires_qualification",
        # 勤務時間帯 (v2.1)
        "wh_shift_type", "wh_start_hour", "wh_end_hour",
        "wh_start_band", "wh_end_band", "wh_break_minutes",
        "wh_overtime", "wh_has_night",
    ]

    # 存在するカラムのみ選択
    available = [c for c in output_columns if c in df_classified.columns]
    missing = [c for c in output_columns if c not in df_classified.columns]
    if missing:
        print(f"  [INFO] 不足カラム（スキップ）: {missing[:5]}...")

    df_out = df_classified[available]
    df_out.to_csv(output_path, index=False, encoding="utf-8-sig")

    elapsed = time.time() - t0
    print(f"  出力: {output_path.name} ({len(df_out):,}行, {elapsed:.1f}s)")

    # 分類結果サマリー
    summary = {
        "source": source_job_type,
        "db_job_type": map_job_type(source_job_type),
        "rows": len(df_out),
        "output": output_path,
        "elapsed": elapsed,
    }

    # Tier1分布（軸A）
    if "tier1_experience" in df_out.columns:
        dist = df_out["tier1_experience"].value_counts().head(3)
        summary["top_tier1_A"] = ", ".join(f"{k}({v:,})" for k, v in dist.items())

    return summary


def main():
    parser = argparse.ArgumentParser(description="全17職種のCSVを分類")
    parser.add_argument("--job_type", type=str, default=None,
                        help="特定職種のみ処理（例: 看護師・准看護師）")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="出力ディレクトリ")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 対象CSV検索
    csvs = find_all_csvs(args.job_type)
    if not csvs:
        print("[ERROR] 対象CSVが見つかりません")
        print(f"  検索ディレクトリ: {SCRAPING_DIR}")
        sys.exit(1)

    print(f"対象: {len(csvs)}ファイル")
    print(f"出力: {output_dir}")
    for csv_path, source in csvs:
        print(f"  {csv_path.name} → {map_job_type(source)}")

    # 分類実行
    t_total = time.time()
    results = []
    for csv_path, source in csvs:
        try:
            result = classify_csv(csv_path, source, output_dir)
            results.append(result)
        except Exception as e:
            print(f"\n  [ERROR] {csv_path.name}: {e}")
            import traceback
            traceback.print_exc()

    # 最終サマリー
    print(f"\n{'='*60}")
    print("[最終サマリー]")
    print(f"{'='*60}")
    total_rows = 0
    print(f"  {'職種':<28} {'行数':>10} {'時間':>8}")
    print(f"  {'-'*28} {'-'*10} {'-'*8}")
    for r in results:
        print(f"  {r['source']:<28} {r['rows']:>10,} {r['elapsed']:>7.1f}s")
        total_rows += r["rows"]

    elapsed_total = time.time() - t_total
    print(f"  {'-'*28} {'-'*10} {'-'*8}")
    print(f"  {'合計':<28} {total_rows:>10,} {elapsed_total:>7.1f}s")
    print(f"\n出力ディレクトリ: {output_dir}")
    print(f"生成ファイル数: {len(results)}")

    # aggregate_segments.py 用のコマンド例
    print(f"\n--- 次のステップ ---")
    print(f"python aggregate_segments.py \\")
    input_args = " \\\n  ".join(
        f'  --input "{r["output"]}"' for r in results
    )
    print(input_args)
    print(f'  --output "../rust_dashboard/data/segment_summary.db"')


if __name__ == "__main__":
    main()
