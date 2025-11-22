# -*- coding: utf-8 -*-
"""RESIDENCE_FLOW生成スクリプト

居住地→希望地の人材フロー分析
"""
import pandas as pd
import sys
import io
from pathlib import Path
import re

# Windows環境での絵文字出力対応
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (ValueError, AttributeError):
    # stdout already configured or not available
    pass


def extract_prefecture_municipality(location):
    """都道府県と市区町村を分離"""
    if pd.isna(location):
        return None, None

    pref_match = re.match(r'^(.+?県|.+?府|.+?都|.+?道)', str(location))
    if not pref_match:
        return None, None

    prefecture = pref_match.group(1)
    municipality_part = str(location)[len(prefecture):]

    # 郡を含む場合の処理
    if '郡' in municipality_part:
        parts = municipality_part.split('郡')
        municipality = parts[1] if len(parts) > 1 else municipality_part
    else:
        municipality = municipality_part

    return prefecture, municipality


def generate_residence_flow():
    """RESIDENCE_FLOWデータ生成"""
    print("\n" + "=" * 60)
    print("RESIDENCE_FLOW生成開始")
    print("=" * 60)

    # Phase1データ読み込み
    applicants_path = Path('data/output_v2/phase1/Phase1_Applicants.csv')
    desired_work_path = Path('data/output_v2/phase1/Phase1_DesiredWork.csv')

    print(f"\n[LOAD] {applicants_path}")
    df_applicants = pd.read_csv(applicants_path, encoding='utf-8-sig')
    print(f"  [OK] {len(df_applicants)}行読み込み")

    print(f"\n[LOAD] {desired_work_path}")
    df_desired = pd.read_csv(desired_work_path, encoding='utf-8-sig')
    print(f"  [OK] {len(df_desired)}行読み込み")

    # 求職者情報とマージ
    df_merged = df_desired.merge(
        df_applicants[['applicant_id', 'age_group', 'gender',
                       'residence_prefecture', 'residence_municipality']],
        on='applicant_id',
        how='left'
    )

    print(f"  [INFO] マージ後: {len(df_merged)}行")

    # フロー行生成
    flow_rows = []

    for _, row in df_merged.iterrows():
        # 希望地が存在しない場合はスキップ
        if pd.isna(row['desired_municipality']):
            continue

        # 希望地の都道府県・市区町村を分離
        desired_pref, desired_muni = extract_prefecture_municipality(row['desired_municipality'])

        if not desired_pref or not desired_muni:
            continue

        flow_rows.append({
            'residence_prefecture': row['residence_prefecture'],
            'residence_municipality': row['residence_municipality'],
            'desired_prefecture': desired_pref,
            'desired_municipality': desired_muni,
            'age_group': row['age_group'],
            'gender': row['gender']
        })

    print(f"  [INFO] フロー展開: {len(flow_rows)}件")

    # DataFrameに変換
    df_flows = pd.DataFrame(flow_rows)

    # グループ化してカウント
    grouped = df_flows.groupby([
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender'
    ]).size().reset_index(name='count')

    print(f"  [INFO] グループ化後: {len(grouped)}行")

    # row_type追加
    grouped['row_type'] = 'RESIDENCE_FLOW'

    # カラム順序調整
    result = grouped[[
        'row_type',
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender', 'count'
    ]]

    # 保存
    output_dir = Path('data/output_v2/residence_flow')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'ResidenceFlow.csv'
    result.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n[SAVE] {output_file}")
    print(f"  [OK] {len(result)}行保存")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"総行数: {len(result)}")
    print(f"居住都道府県数: {result['residence_prefecture'].nunique()}")
    print(f"希望都道府県数: {result['desired_prefecture'].nunique()}")

    # 都道府県間フローTOP10
    print("\n都道府県間フローTOP10:")
    pref_flows = result.groupby(['residence_prefecture', 'desired_prefecture'])['count'].sum().sort_values(ascending=False).head(10)
    for i, ((res_pref, des_pref), count) in enumerate(pref_flows.items(), 1):
        arrow = "→" if res_pref != des_pref else "⟲"
        print(f"  {i:2d}. {res_pref} {arrow} {des_pref}: {count:,}件")

    # 流入TOP10（最も人材が流入している市区町村）
    print("\n流入TOP10:")
    inflow_top = result.groupby(['desired_prefecture', 'desired_municipality'])['count'].sum().sort_values(ascending=False).head(10)
    for i, ((pref, muni), count) in enumerate(inflow_top.items(), 1):
        print(f"  {i:2d}. {pref}{muni}: {count:,}件")

    # 流出TOP10（最も人材が流出している市区町村）
    print("\n流出TOP10:")
    outflow_top = result.groupby(['residence_prefecture', 'residence_municipality'])['count'].sum().sort_values(ascending=False).head(10)
    for i, ((pref, muni), count) in enumerate(outflow_top.items(), 1):
        print(f"  {i:2d}. {pref}{muni}: {count:,}件")

    print("\n" + "=" * 60)
    print("✅ RESIDENCE_FLOW生成完了")
    print("=" * 60)

    return result


if __name__ == '__main__':
    result = generate_residence_flow()
