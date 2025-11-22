"""MapComplete統合CSV生成時のGAP計算検証"""
import pandas as pd
from pathlib import Path

# Phase12ソースデータ
gap_source = pd.read_csv('data/output_v2/phase12/Phase12_SupplyDemandGap.csv', encoding='utf-8-sig')

# MapComplete統合CSV（修正前）
map_complete = pd.read_csv('data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All.csv', encoding='utf-8-sig')

print('='*100)
print('GAP計算不整合の根本原因調査')
print('='*100)

# Phase12ソースデータのGAP計算チェック
print('\n[1] Phase12 SourceData（Phase12_SupplyDemandGap.csv）')
gap_source['calc_gap'] = gap_source['demand_count'] - gap_source['supply_count']
gap_source['diff'] = abs(gap_source['gap'] - gap_source['calc_gap'])
source_mismatch = gap_source[gap_source['diff'] > 0.01]
print(f'  総件数: {len(gap_source)}')
print(f'  不整合: {len(source_mismatch)}件')

# MapComplete統合CSVのGAPデータ
print('\n[2] MapComplete統合CSV（MapComplete_Complete_All.csv）')
map_gap = map_complete[map_complete['row_type'] == 'GAP'].copy()
map_gap['calc_gap'] = map_gap['demand_count'] - map_gap['supply_count']
map_gap['diff'] = abs(map_gap['gap'] - map_gap['calc_gap'])
map_mismatch = map_gap[map_gap['diff'] > 0.01]
print(f'  総件数: {len(map_gap)}')
print(f'  不整合: {len(map_mismatch)}件')

if len(map_mismatch) > 0:
    print('\n[3] MapComplete不整合の詳細（最初の10件）')
    print(map_mismatch[['prefecture', 'municipality', 'demand_count', 'supply_count', 'gap', 'calc_gap', 'diff']].head(10).to_string())

    # 不整合パターンの分析
    print('\n[4] 不整合パターン分析')
    patterns = map_mismatch.groupby(['demand_count', 'supply_count', 'gap']).size().reset_index(name='count')
    patterns = patterns.sort_values('count', ascending=False)
    print(patterns.head(10).to_string())

    # Phase12ソースと比較
    print('\n[5] Phase12ソースとの比較（不整合市町村）')
    for idx, row in map_mismatch.head(5).iterrows():
        pref = row['prefecture']
        muni = row['municipality']

        # Phase12ソースで同じ市町村を探す
        source_match = gap_source[(gap_source['prefecture'] == pref) & (gap_source['municipality'] == muni)]

        if len(source_match) > 0:
            src = source_match.iloc[0]
            print(f'\n  {pref}{muni}:')
            print(f'    Source: demand={src["demand_count"]}, supply={src["supply_count"]}, gap={src["gap"]}')
            print(f'    MapComplete: demand={row["demand_count"]}, supply={row["supply_count"]}, gap={row["gap"]}')
            print(f'    一致: {src["gap"] == row["gap"]}')

print('\n' + '='*100)
