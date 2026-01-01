#!/usr/bin/env python3
"""各row_typeのデータ構造を調査するスクリプト"""
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helper import query_df

def investigate_row_types():
    """各row_typeのカラム構造と代表的な値を調査"""

    # 調査対象のrow_types
    row_types = [
        'SUMMARY',
        'RESIDENCE_FLOW',
        'AGE_GENDER',
        'PERSONA_MUNI',
        'QUALIFICATION_DETAIL',
        'COMPETITION',
        'WORKSTYLE_DISTRIBUTION',
        'WORKSTYLE_AGE_CROSS',
        'URGENCY_GENDER',
        'URGENCY_START_CATEGORY',
        'WORKSTYLE_MOBILITY',
        'DESIRED_AREA_PATTERN',
    ]

    for row_type in row_types:
        print(f"\n{'='*60}")
        print(f"row_type: {row_type}")
        print('='*60)

        sql = f"SELECT * FROM job_seeker_data WHERE row_type = '{row_type}' LIMIT 3"
        df = query_df(sql)

        if df.empty:
            print("  [データなし]")
            continue

        print(f"  件数: {len(df)} (LIMIT 3)")

        # 主要カラムの値を確認
        key_cols = ['prefecture', 'municipality', 'category1', 'category2', 'category3',
                    'desired_prefecture', 'desired_municipality', 'count']

        for col in key_cols:
            if col in df.columns:
                sample_values = df[col].dropna().unique()[:3].tolist()
                print(f"  {col}: {sample_values}")

        # レコード数も取得
        count_sql = f"SELECT COUNT(*) as cnt FROM job_seeker_data WHERE row_type = '{row_type}'"
        count_df = query_df(count_sql)
        if not count_df.empty:
            total = count_df.iloc[0]['cnt']
            print(f"  総レコード数: {total}")

if __name__ == "__main__":
    investigate_row_types()
