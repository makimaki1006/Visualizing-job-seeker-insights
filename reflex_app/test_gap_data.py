# -*- coding: utf-8 -*-
"""需給バランスタブのデータ検証スクリプト"""
import pandas as pd

# V3 CSV読み込み
df = pd.read_csv('MapComplete_Complete_All_FIXED.csv', encoding='utf-8-sig', low_memory=False)

# 京都府でフィルタリング（例）
prefecture = '京都府'
filtered = df[df['prefecture'] == prefecture]

print(f"=== 需給バランスタブデータ検証 ===\n")
print(f"選択都道府県: {prefecture}")
print(f"全行数: {len(filtered)}")

# GAP行をフィルタ
gap_df = filtered[filtered['row_type'] == 'GAP']

print(f"\n=== GAPデータ ===")
print(f"GAP行数: {len(gap_df)}")

if not gap_df.empty:
    # gap_compare_data のテスト
    demand = gap_df['demand_count'].sum()
    supply = gap_df['supply_count'].sum()

    print(f"\n=== gap_compare_data（需要 vs 供給）===")
    print(f"需要合計: {int(demand):,}")
    print(f"供給合計: {int(supply):,}")

    # gap_balance_data のテスト
    gap_value = gap_df['gap'].sum()

    print(f"\n=== gap_balance_data（バランス）===")
    print(f"不足分（gap）: {int(gap_value):,}")
    print(f"供給: {int(supply):,}")

    # cross_supply_demand_region_data のテスト
    print(f"\n=== cross_supply_demand_region_data（地域別）===")

    # 市町村別にグループ化
    for municipality in gap_df['municipality'].dropna().unique()[:5]:  # 最初の5件
        muni_data = gap_df[gap_df['municipality'] == municipality]

        if not muni_data.empty:
            supply_muni = int(muni_data['supply_count'].sum())
            demand_muni = int(muni_data['demand_count'].sum())
            gap_muni = int(muni_data['gap'].sum())

            print(f"{municipality}: 需要={demand_muni:,}, 供給={supply_muni:,}, Gap={gap_muni:,}")

    # NaN municipalityの確認
    nan_count = gap_df['municipality'].isna().sum()
    print(f"\nNaN municipality行数: {nan_count}")

else:
    print("\n⚠️ GAPデータが見つかりません")

# 他のrow_type分布も確認
print(f"\n=== {prefecture}の全row_type分布 ===")
print(filtered['row_type'].value_counts())
