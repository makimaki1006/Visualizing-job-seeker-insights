# -*- coding: utf-8 -*-
"""データ問題の詳細調査"""
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import main
import db_helper

def check_all_data_issues():
    print("=" * 80)
    print("NiceGUI データ問題 詳細調査")
    print("=" * 80)

    # テスト対象: 東京都千代田区（データが豊富なはず）
    test_pref = "東京都"
    test_muni = "千代田区"

    # 1. ペルソナ分析データ
    print(f"\n[1] ペルソナ分析（{test_pref} {test_muni}）:")
    print("-" * 60)

    # AGE_GENDER_RESIDENCEデータ確認
    try:
        age_res_df = main.query_turso(
            f"SELECT COUNT(*) as cnt FROM job_seeker_data "
            f"WHERE row_type = 'AGE_GENDER_RESIDENCE' "
            f"AND prefecture = '{test_pref}' AND municipality = '{test_muni}'"
        )
        print(f"  AGE_GENDER_RESIDENCE ({test_muni}): {age_res_df['cnt'].iloc[0]} rows")
    except Exception as e:
        print(f"  AGE_GENDER_RESIDENCE error: {e}")

    # get_persona_market_share 関数テスト
    persona_data = db_helper.get_persona_market_share(test_pref, test_muni)
    print(f"  get_persona_market_share(): {len(persona_data)} items")
    if persona_data:
        print(f"    Sample: {persona_data[:2]}")

    # 2. 資格詳細データ
    print(f"\n[2] 資格詳細（{test_pref} {test_muni}）:")
    print("-" * 60)

    try:
        qual_df = main.query_turso(
            f"SELECT COUNT(*) as cnt FROM job_seeker_data "
            f"WHERE row_type = 'QUALIFICATION_DETAIL' "
            f"AND prefecture = '{test_pref}' AND municipality = '{test_muni}'"
        )
        print(f"  QUALIFICATION_DETAIL ({test_muni}): {qual_df['cnt'].iloc[0]} rows")
    except Exception as e:
        print(f"  QUALIFICATION_DETAIL error: {e}")

    try:
        qual_p_df = main.query_turso(
            f"SELECT COUNT(*) as cnt FROM job_seeker_data "
            f"WHERE row_type = 'QUALIFICATION_PERSONA' "
            f"AND prefecture = '{test_pref}' AND municipality = '{test_muni}'"
        )
        print(f"  QUALIFICATION_PERSONA ({test_muni}): {qual_p_df['cnt'].iloc[0]} rows")
    except Exception as e:
        print(f"  QUALIFICATION_PERSONA error: {e}")

    # 3. GAPデータ（需給バランス）
    print(f"\n[3] 需給バランス:")
    print("-" * 60)

    try:
        # 東京都のGAP
        gap_tokyo = main.query_turso(
            f"SELECT COUNT(*) as cnt FROM job_seeker_data "
            f"WHERE row_type = 'GAP' AND prefecture = '{test_pref}'"
        )
        print(f"  GAP ({test_pref}): {gap_tokyo['cnt'].iloc[0]} rows")

        # 岩手県のGAP
        gap_iwate = main.query_turso(
            f"SELECT COUNT(*) as cnt FROM job_seeker_data "
            f"WHERE row_type = 'GAP' AND prefecture = '岩手県'"
        )
        print(f"  GAP (岩手県): {gap_iwate['cnt'].iloc[0]} rows")

        # 全国のGAP都道府県分布
        gap_prefs = main.query_turso(
            "SELECT prefecture, COUNT(*) as cnt FROM job_seeker_data "
            "WHERE row_type = 'GAP' GROUP BY prefecture ORDER BY cnt DESC LIMIT 10"
        )
        print(f"  GAP Top 10 prefectures:")
        for _, row in gap_prefs.iterrows():
            print(f"    {row['prefecture']}: {row['cnt']}")
    except Exception as e:
        print(f"  GAP error: {e}")

    # 4. 地域サマリー（female_ratio, top_age_ratio）
    print(f"\n[4] 地域サマリー（SUMMARY行のカラム）:")
    print("-" * 60)

    df = main._clean_dataframe(main.load_data())
    chiyoda = df[(df["prefecture"] == test_pref) & (df["municipality"] == test_muni)]
    if len(chiyoda) > 0:
        row = chiyoda.iloc[0]
        for col in ["female_ratio", "male_ratio", "top_age_ratio", "avg_desired_areas"]:
            val = row.get(col, "N/A")
            status = "OK" if pd.notna(val) and val != 0 else "NG (NaN or 0)"
            print(f"  {col}: {val} [{status}]")

    # 5. 全都道府県でfemale_ratioを確認
    print(f"\n[5] female_ratio の全体状況:")
    print("-" * 60)
    if "female_ratio" in df.columns:
        non_null = df["female_ratio"].notna().sum()
        non_zero = (df["female_ratio"] != 0).sum() if non_null > 0 else 0
        print(f"  全{len(df)}行中:")
        print(f"    non-null: {non_null} ({non_null/len(df)*100:.1f}%)")
        print(f"    non-zero: {non_zero}")
    else:
        print("  female_ratio column NOT FOUND")

    # 6. 年齢別分布（AGE_GENDER）のUI連携確認
    print(f"\n[6] 年齢別分布（AGE_GENDER）:")
    print("-" * 60)
    try:
        age_df = main.query_turso(
            f"SELECT category1, category2, SUM(CAST(count AS INTEGER)) as total "
            f"FROM job_seeker_data "
            f"WHERE row_type = 'AGE_GENDER' "
            f"AND prefecture = '{test_pref}' AND municipality = '{test_muni}' "
            f"GROUP BY category1, category2"
        )
        print(f"  AGE_GENDER ({test_muni}): {len(age_df)} groups")
        for _, row in age_df.iterrows():
            print(f"    {row['category1']} {row['category2']}: {row['total']}")
    except Exception as e:
        print(f"  AGE_GENDER error: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_all_data_issues()
