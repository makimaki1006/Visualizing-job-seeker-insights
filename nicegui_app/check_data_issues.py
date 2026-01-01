# -*- coding: utf-8 -*-
"""
NiceGUIダッシュボードのデータ問題を調査するスクリプト
"""
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import main
import db_helper

def check_all_issues():
    """全ての問題を調査"""
    print("=" * 80)
    print("NiceGUIダッシュボード データ問題調査")
    print("=" * 80)

    # 1. メインデータ（SUMMARY）を取得
    df = main._clean_dataframe(main.load_data())
    print(f"\n[1] メインデータ（SUMMARY行）: {len(df):,} rows")
    print(f"    Columns: {len(df.columns)} columns")

    # 2. row_typeの種類を確認（全データ）
    print("\n[2] データベース内のrow_type分布:")
    try:
        all_data = main.query_turso("SELECT row_type, COUNT(*) as cnt FROM job_seeker_data GROUP BY row_type")
        for _, row in all_data.iterrows():
            print(f"    {row['row_type']}: {row['cnt']:,} rows")
    except Exception as e:
        print(f"    Error: {e}")

    # 3. 岩手県のデータを確認
    print("\n[3] 岩手県のデータ確認:")
    iwate_df = df[df["prefecture"] == "岩手県"]
    print(f"    岩手県 SUMMARY行: {len(iwate_df):,} rows")
    if len(iwate_df) > 0:
        munis = iwate_df["municipality"].unique().tolist()
        print(f"    市区町村: {munis[:10]}...")
        if "盛岡市" in munis:
            morioka = iwate_df[iwate_df["municipality"] == "盛岡市"]
            print(f"    盛岡市 rows: {len(morioka)}")

    # 4. GAP データを確認
    print("\n[4] GAP（需給バランス）データ確認:")
    gap_df = main.load_gap_data()
    print(f"    GAP rows total: {len(gap_df):,}")
    if len(gap_df) > 0:
        iwate_gap = gap_df[gap_df["prefecture"] == "岩手県"] if "prefecture" in gap_df.columns else pd.DataFrame()
        print(f"    岩手県 GAP rows: {len(iwate_gap)}")
        if len(iwate_gap) > 0:
            print(f"    岩手県 GAP columns with data:")
            for col in ["demand_count", "supply_count", "gap", "demand_supply_ratio"]:
                if col in iwate_gap.columns:
                    non_null = iwate_gap[col].notna().sum()
                    print(f"      {col}: {non_null} non-null values")

    # 5. PERSONA データを確認
    print("\n[5] PERSONA データ確認:")
    try:
        persona_df = main.query_turso("SELECT * FROM job_seeker_data WHERE row_type = 'PERSONA' LIMIT 10")
        print(f"    PERSONA rows: {len(persona_df)}")
        if len(persona_df) > 0:
            print(f"    PERSONA columns: {list(persona_df.columns)[:10]}...")
    except Exception as e:
        print(f"    Error: {e}")

    # 6. 資格データを確認
    print("\n[6] 資格データ確認:")
    try:
        qual_df = main.query_turso("SELECT DISTINCT category1 FROM job_seeker_data WHERE row_type = 'QUALIFICATION' LIMIT 20")
        print(f"    QUALIFICATION distinct categories: {len(qual_df)}")
        if len(qual_df) > 0:
            print(f"    Categories: {qual_df['category1'].tolist()[:10]}...")
    except Exception as e:
        print(f"    QUALIFICATION row_type: Error - {e}")

    # 7. SUMMARYの重要カラムの欠損確認
    print("\n[7] SUMMARY行の重要カラム欠損状況:")
    important_cols = [
        "avg_age", "male_count", "female_count", "applicant_count",
        "avg_desired_areas", "avg_mobility_score", "avg_urgency_score",
        "avg_qualifications", "top_age_ratio", "female_ratio", "male_ratio"
    ]
    for col in important_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            pct = non_null / len(df) * 100 if len(df) > 0 else 0
            status = "OK" if pct > 90 else "WARN" if pct > 50 else "NG"
            print(f"    {col}: {non_null:,}/{len(df):,} ({pct:.1f}%) [{status}]")
        else:
            print(f"    {col}: NOT FOUND [NG]")

    # 8. AGE_GENDER データ（年齢別分布用）
    print("\n[8] AGE_GENDER データ確認:")
    try:
        age_df = main.query_turso("SELECT * FROM job_seeker_data WHERE row_type = 'AGE_GENDER' LIMIT 10")
        print(f"    AGE_GENDER rows: {len(age_df)}")
        if len(age_df) > 0:
            print(f"    Columns: {list(age_df.columns)[:10]}...")
            if "category1" in age_df.columns:
                print(f"    category1 values: {age_df['category1'].unique().tolist()}")
    except Exception as e:
        print(f"    Error: {e}")

    # 9. 盛岡市のデータ詳細
    print("\n[9] 盛岡市の詳細データ:")
    if len(iwate_df) > 0:
        morioka_df = iwate_df[iwate_df["municipality"] == "盛岡市"]
        if len(morioka_df) > 0:
            for col in ["applicant_count", "male_count", "female_count", "avg_age",
                       "female_ratio", "top_age_ratio", "avg_qualifications"]:
                if col in morioka_df.columns:
                    val = morioka_df[col].iloc[0]
                    print(f"    {col}: {val}")

    # 10. db_helper.get_municipality_stats の結果確認
    print("\n[10] db_helper.get_municipality_stats('岩手県', '盛岡市'):")
    stats = db_helper.get_municipality_stats("岩手県", "盛岡市")
    for key, val in stats.items():
        print(f"    {key}: {val}")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    check_all_issues()
