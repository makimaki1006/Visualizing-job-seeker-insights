#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MunicipalityFlowEdges.csvのデータ調査
"""

import pandas as pd
from pathlib import Path

def debug_flow_data():
    """フローデータのデバッグ"""

    input_file = Path("data/output_v2/phase6/MunicipalityFlowEdges.csv")

    print("[INFO] データ読み込み中...")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"[OK] 総行数: {len(df)}")

    print("\n[INFO] カラム情報:")
    print(df.info())

    print("\n[INFO] 欠損値チェック:")
    missing = df.isnull().sum()
    print(missing[missing > 0])

    # groupbyで使用するカラムの欠損値
    groupby_cols = ['origin', 'destination', 'origin_pref', 'origin_muni', 'destination_pref', 'destination_muni']

    print(f"\n[INFO] groupby対象カラムの欠損値:")
    for col in groupby_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            print(f"  {col}: {null_count}件")

    # 欠損値を含む行をフィルター
    has_null = df[groupby_cols].isnull().any(axis=1)
    null_rows = df[has_null]

    print(f"\n[INFO] groupby対象カラムに欠損値を含む行数: {len(null_rows)}")

    if len(null_rows) > 0:
        print("\n[INFO] 欠損値を含む行のサンプル（最初の5行）:")
        print(null_rows.head().to_string())

    # 欠損値を除外してgroupby
    print("\n[INFO] 欠損値を除外してgroupby実行...")
    df_clean = df.dropna(subset=groupby_cols)
    print(f"[OK] 欠損値除外後の行数: {len(df_clean)}")

    agg = df_clean.groupby(groupby_cols).agg({
        'applicant_id': 'count',
        'age': 'mean',
        'gender': lambda x: x.mode()[0] if len(x.mode()) > 0 else '不明'
    }).reset_index()

    agg.rename(columns={
        'applicant_id': 'flow_count',
        'age': 'avg_age',
        'gender': 'gender_mode'
    }, inplace=True)

    print(f"[OK] 集約後の行数: {len(agg)}")
    print(f"[OK] 総flow_count: {agg['flow_count'].sum()}")

    # 整合性チェック
    if len(df_clean) == agg['flow_count'].sum():
        print("[SUCCESS] 欠損値除外後のデータは整合性があります")
    else:
        print(f"[ERROR] まだ不一致があります（差分: {abs(len(df_clean) - agg['flow_count'].sum())}）")

if __name__ == '__main__':
    debug_flow_data()
