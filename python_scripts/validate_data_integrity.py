"""MapComplete統合CSVデータ妥当性検証スクリプト（Ultrathink 20段階深掘り）"""
import pandas as pd
import json

def stage4_age_gender_investigation():
    """Stage 4: AGE_GENDER不一致調査"""
    print('='*100)
    print('[BUG 2] AGE_GENDER: Kyoto missing 7 rows')
    print('='*100)

    df_age_source = pd.read_csv('data/output_v2/phase7/Phase7_AgeGenderCrossAnalysis.csv', encoding='utf-8-sig')
    df_age_map = pd.read_csv('data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All.csv', encoding='utf-8-sig')
    df_age_map = df_age_map[df_age_map['row_type'] == 'AGE_GENDER']

    # 京都府のデータを詳細比較
    kyoto_source = df_age_source[df_age_source['prefecture'] == '京都府']
    kyoto_map = df_age_map[df_age_map['prefecture'] == '京都府']

    print(f'Kyoto - Source: {len(kyoto_source)} rows | Map: {len(kyoto_map)} rows')
    print(f'Source columns: {list(kyoto_source.columns)}')

    # municipality列の比較
    source_munis = set(kyoto_source['municipality'].unique())
    map_munis = set(kyoto_map['municipality'].unique())

    missing_munis = source_munis - map_munis
    extra_munis = map_munis - source_munis

    if missing_munis:
        print(f'\nMissing municipalities in Map: {len(missing_munis)} municipalities')
        for muni in list(missing_munis)[:5]:
            print(f'  - {muni}')
    if extra_munis:
        print(f'Extra municipalities in Map: {len(extra_munis)} municipalities')

    # 各市町村の行数比較
    print(f'\nMunicipality row count comparison (showing mismatches):')
    source_muni_counts = kyoto_source.groupby('municipality').size()
    map_muni_counts = kyoto_map.groupby('municipality').size()

    mismatch_count = 0
    for muni in source_muni_counts.index:
        source_count = source_muni_counts.get(muni, 0)
        map_count = map_muni_counts.get(muni, 0)
        if source_count != map_count:
            print(f'  {muni}: Source {source_count} vs Map {map_count} (diff: {source_count - map_count})')
            mismatch_count += 1

    print(f'\nTotal municipalities with mismatches: {mismatch_count}')

    return {
        'source_rows': len(kyoto_source),
        'map_rows': len(kyoto_map),
        'missing_munis': len(missing_munis),
        'mismatch_count': mismatch_count
    }

def stage5_gap_investigation():
    """Stage 5: GAP欠落調査"""
    print('\n' + '='*100)
    print('[BUG 3] GAP: 3 prefectures missing data')
    print('='*100)

    df_gap_source = pd.read_csv('data/output_v2/phase12/Phase12_SupplyDemandGap.csv', encoding='utf-8-sig')
    df_gap_map = pd.read_csv('data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All.csv', encoding='utf-8-sig')
    df_gap_map = df_gap_map[df_gap_map['row_type'] == 'GAP']

    print(f'Source: {len(df_gap_source)} rows in {df_gap_source["prefecture"].nunique()} prefectures')
    print(f'Map: {len(df_gap_map)} rows in {df_gap_map["prefecture"].nunique()} prefectures')

    # 欠落した都道府県を特定
    source_prefs = set(df_gap_source['prefecture'].unique())
    map_prefs = set(df_gap_map['prefecture'].unique())

    missing_prefs = source_prefs - map_prefs

    if missing_prefs:
        print(f'\nMissing prefectures in Map: {missing_prefs}')
        for pref in missing_prefs:
            pref_data = df_gap_source[df_gap_source['prefecture'] == pref]
            print(f'  {pref}: {len(pref_data)} rows missing')
            print(f'    Municipalities: {list(pref_data["municipality"].unique())}')

    return {
        'source_prefs': len(source_prefs),
        'map_prefs': len(map_prefs),
        'missing_prefs': list(missing_prefs)
    }

def main():
    """メイン実行"""
    results = {}

    # Stage 4: AGE_GENDER
    results['stage4_age_gender'] = stage4_age_gender_investigation()

    # Stage 5: GAP
    results['stage5_gap'] = stage5_gap_investigation()

    # 結果をJSON保存
    with open('data/output_v2/mapcomplete_complete_sheets/validation_stage4_5.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('\n' + '='*100)
    print('Stage 4-5 validation results saved to: validation_stage4_5.json')
    print('='*100)

if __name__ == '__main__':
    main()
