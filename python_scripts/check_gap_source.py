"""Phase12ソースCSVのGAP計算整合性チェック"""
import pandas as pd
from pathlib import Path

# Phase12ソースデータ読み込み
df = pd.read_csv('data/output_v2/phase12/Phase12_SupplyDemandGap.csv', encoding='utf-8-sig')

print('='*80)
print('Phase12 SupplyDemandGap.csv GAP計算整合性チェック')
print('='*80)

# GAP計算の整合性チェック
df['calculated_gap'] = df['demand_count'] - df['supply_count']
df['gap_diff'] = abs(df['gap'] - df['calculated_gap'])

mismatches = df[df['gap_diff'] > 0.01]

print(f'\n総レコード数: {len(df)}')
print(f'不整合レコード数: {len(mismatches)}')

if len(mismatches) > 0:
    print('\n不整合の詳細:')
    print(mismatches[['prefecture', 'municipality', 'demand_count', 'supply_count', 'gap', 'calculated_gap', 'gap_diff']].to_string())
else:
    print('\n✅ すべてのGAP計算が正しいです（demand_count - supply_count = gap）')

print('\n' + '='*80)
