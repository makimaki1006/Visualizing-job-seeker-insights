"""GAP計算不整合を修正"""
import pandas as pd
from pathlib import Path

print('='*100)
print('GAP計算不整合修正')
print('='*100)

base_dir = Path('data/output_v2')
map_complete_path = base_dir / 'mapcomplete_complete_sheets' / 'MapComplete_Complete_All_FIXED.csv'
df = pd.read_csv(map_complete_path, encoding='utf-8-sig')

print(f'\n総行数: {len(df)}行')

# GAP row_typeのみ抽出
gap_rows = df[df['row_type'] == 'GAP'].copy()
print(f'GAP行数: {len(gap_rows)}行')

# GAP計算の整合性チェック
gap_rows['calculated_gap'] = gap_rows['demand_count'] - gap_rows['supply_count']
gap_rows['gap_diff'] = abs(gap_rows['gap'] - gap_rows['calculated_gap'])

mismatches_before = gap_rows[gap_rows['gap_diff'] > 0.01]
print(f'\n修正前の不整合: {len(mismatches_before)}行')

if len(mismatches_before) > 0:
    print('\n不整合の詳細（最初の10件）:')
    print(mismatches_before[['prefecture', 'municipality', 'demand_count', 'supply_count', 'gap', 'calculated_gap']].head(10).to_string())

    # GAP列を正しく再計算
    df.loc[df['row_type'] == 'GAP', 'gap'] = df.loc[df['row_type'] == 'GAP', 'demand_count'] - df.loc[df['row_type'] == 'GAP', 'supply_count']

    print(f'\n[OK] GAP列を再計算しました（demand_count - supply_count）')

    # 修正後の整合性チェック
    gap_rows_after = df[df['row_type'] == 'GAP'].copy()
    gap_rows_after['calculated_gap'] = gap_rows_after['demand_count'] - gap_rows_after['supply_count']
    gap_rows_after['gap_diff'] = abs(gap_rows_after['gap'] - gap_rows_after['calculated_gap'])
    mismatches_after = gap_rows_after[gap_rows_after['gap_diff'] > 0.01]

    print(f'修正後の不整合: {len(mismatches_after)}行')

    # 保存
    output_path = base_dir / 'mapcomplete_complete_sheets' / 'MapComplete_Complete_All_FIXED_V2.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f'\n修正版を保存: {output_path}')

else:
    print('\n[OK] すべてのGAP計算が正しいです（修正不要）')

print('='*100)
