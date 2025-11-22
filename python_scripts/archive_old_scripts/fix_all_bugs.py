"""全バグ一括修正スクリプト"""
import pandas as pd
from pathlib import Path

print('='*100)
print('MapComplete統合CSV 全バグ一括修正')
print('='*100)

base_dir = Path('data/output_v2')
map_complete_path = base_dir / 'mapcomplete_complete_sheets' / 'MapComplete_Complete_All.csv'
df = pd.read_csv(map_complete_path, encoding='utf-8-sig')

print(f'\n修正前: {len(df)}行')

# BUG 1: PERSONA重複削除（全都道府県に複製されているものを1都道府県のみに）
print('\n[BUG 1] PERSONA重複削除')
persona_rows = df[df['row_type'] == 'PERSONA']
print(f'  修正前: {len(persona_rows)}行')

# 最初の都道府県（京都府）のみに残す
if len(persona_rows) > 0:
    first_pref = persona_rows['prefecture'].iloc[0]
    # PERSONA以外の行 + 京都府のPERSONAのみ
    df = pd.concat([
        df[df['row_type'] != 'PERSONA'],
        persona_rows[persona_rows['prefecture'] == first_pref]
    ])
    print(f'  修正後: {len(df[df["row_type"] == "PERSONA"])}行（{first_pref}のみ）')

# BUG 2: AGE_GENDER NaNmunicipality処理
print('\n[BUG 2] AGE_GENDER NaN municipality処理')
age_gender_nan = df[(df['row_type'] == 'AGE_GENDER') & (df['municipality'].isna())]
print(f'  NaN municipality: {len(age_gender_nan)}行')
# NaNを空文字列に変換
df.loc[(df['row_type'] == 'AGE_GENDER') & (df['municipality'].isna()), 'municipality'] = ''
print(f'  修正後: {len(df[(df["row_type"] == "AGE_GENDER") & (df["municipality"] == "")])}行（空文字列に変換）')

# BUG 3: GAP欠落都道府県の確認（ソースデータ側の問題なので、ここでは確認のみ）
print('\n[BUG 3] GAP欠落都道府県確認')
gap_prefs = df[df['row_type'] == 'GAP']['prefecture'].unique()
print(f'  GAP都道府県数: {len(gap_prefs)}/47')
# Phase12のソースデータを確認
gap_source = pd.read_csv(base_dir / 'phase12' / 'Phase12_SupplyDemandGap.csv', encoding='utf-8-sig')
gap_source_prefs = gap_source['prefecture'].unique()
print(f'  ソースデータ都道府県数: {len(gap_source_prefs)}')

# 欠落している都道府県を特定
missing_prefs = set(gap_source_prefs) - set(gap_prefs)
if missing_prefs:
    print(f'  欠落都道府県: {missing_prefs}')
    # これらを追加（ソースデータから）
    for pref in missing_prefs:
        pref_data = gap_source[gap_source['prefecture'] == pref]
        for _, row in pref_data.iterrows():
            df = pd.concat([df, pd.DataFrame([{
                'row_type': 'GAP',
                'prefecture': pref,
                'municipality': row.get('municipality', ''),
                'category1': '',
                'category2': '',
                'category3': '',
                'demand_count': row.get('demand_count', 0),
                'supply_count': row.get('supply_count', 0),
                'gap': row.get('gap', 0),
                'demand_supply_ratio': row.get('demand_supply_ratio', None),
                'latitude': row.get('latitude', None),
                'longitude': row.get('longitude', None)
            }])], ignore_index=True)
    print(f'  追加後: {len(df[df["row_type"] == "GAP"])}行')

# BUG 4: RARITY重複削除
print('\n[BUG 4] RARITY重複削除')
rarity_before = len(df[df['row_type'] == 'RARITY'])
df = df.drop_duplicates(subset=['row_type', 'prefecture', 'municipality', 'category1', 'category2'], keep='first')
rarity_after = len(df[df['row_type'] == 'RARITY'])
print(f'  修正前: {rarity_before}行 → 修正後: {rarity_after}行（削除: {rarity_before - rarity_after}行）')

# BUG 5: 数値データ異常値の処理
print('\n[BUG 5] 数値データ異常値処理')

# gap列の負の値を0に
negative_gap = (df['gap'] < 0).sum()
if negative_gap > 0:
    df.loc[df['gap'] < 0, 'gap'] = 0
    print(f'  gap列負の値: {negative_gap}件 → 0に修正')

# count列のNaNを確認（これは仕様の可能性があるので、0に置き換えるかは要検討）
count_nan = df['count'].isna().sum()
print(f'  count列NaN: {count_nan}件（維持、0埋めは不適切）')

print(f'\n修正後: {len(df)}行')
print(f'行数差分: {len(df) - pd.read_csv(map_complete_path, encoding="utf-8-sig").shape[0]}')

# 修正版を保存
output_path = base_dir / 'mapcomplete_complete_sheets' / 'MapComplete_Complete_All_FIXED.csv'
df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f'\n修正版を保存: {output_path}')
print('='*100)
