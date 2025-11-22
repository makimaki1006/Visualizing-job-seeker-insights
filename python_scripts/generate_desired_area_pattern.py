# -*- coding: utf-8 -*-
"""DESIRED_AREA_PATTERN生成スクリプト

併願パターン分析: 同一求職者が複数の希望地を持つ場合の組み合わせパターンを分析
"""
import pandas as pd
import sys
import io
from pathlib import Path
from itertools import combinations
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
    pref_match = re.match(r'^(.+?県|.+?府|.+?都|.+?道)', location)
    if not pref_match:
        return None, None

    prefecture = pref_match.group(1)
    municipality_part = location[len(prefecture):]

    # 郡を含む場合の処理
    if '郡' in municipality_part:
        parts = municipality_part.split('郡')
        municipality = parts[1] if len(parts) > 1 else municipality_part
    else:
        municipality = municipality_part

    return prefecture, municipality


def generate_desired_area_pattern():
    """DESIRED_AREA_PATTERNデータ生成"""
    print("\n" + "=" * 60)
    print("DESIRED_AREA_PATTERN生成開始")
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

    # applicant_idでグループ化して希望地リスト（都道府県+市区町村のペア）を作成
    applicant_areas = df_desired.groupby('applicant_id').apply(
        lambda x: list(zip(x['desired_prefecture'], x['desired_municipality']))
    ).to_dict()

    # 複数希望地を持つ求職者のみ抽出
    multi_area_applicants = {k: v for k, v in applicant_areas.items() if len(v) >= 2}
    print(f"  [INFO] 複数希望地あり: {len(multi_area_applicants)}人")

    # 併願パターン生成
    pattern_rows = []
    excluded_count_pref = 0  # 除外された求職者数（5都道府県以上）
    excluded_count_total = 0  # 除外された求職者数（40件以上）

    for applicant_id, desired_areas in multi_area_applicants.items():
        # 求職者情報取得
        applicant_info = df_applicants[df_applicants['applicant_id'] == applicant_id]
        if applicant_info.empty:
            continue

        age_group = applicant_info.iloc[0]['age_group']
        gender = applicant_info.iloc[0]['gender']
        residence_pref = applicant_info.iloc[0]['residence_prefecture']
        residence_muni = applicant_info.iloc[0]['residence_municipality']

        # 重複を除外してユニークな希望地のみ（NaNを除外）
        # desired_areasは(prefecture, municipality)のタプルのリスト
        unique_areas = [area for area in set(desired_areas)
                       if pd.notna(area[0]) and pd.notna(area[1])]

        # 2地域未満の場合はスキップ
        if len(unique_areas) < 2:
            continue

        # 外れ値フィルタリング1: 40件以上の希望地を持つ求職者は除外
        if len(unique_areas) >= 40:
            excluded_count_total += 1
            continue

        # 外れ値フィルタリング2: 5つ以上の異なる都道府県を持つ求職者は除外
        unique_prefectures = set(area[0] for area in unique_areas)
        if len(unique_prefectures) >= 5:
            excluded_count_pref += 1
            continue

        # 2地域の組み合わせを生成
        for (pref1, muni1), (pref2, muni2) in combinations(sorted(unique_areas), 2):
            # 都道府県と市区町村は既にPhase1データから取得済み
            if not pref1 or not pref2:
                continue

            # パターンとして記録（主希望地をarea1として）
            pattern_rows.append({
                'prefecture': pref1,
                'municipality': muni1,
                'co_desired_prefecture': pref2,
                'co_desired_municipality': muni2,
                'age_group': age_group,
                'gender': gender,
                'residence_prefecture': residence_pref,
                'residence_municipality': residence_muni
            })

    print(f"  [INFO] 併願パターン展開: {len(pattern_rows)}件")
    print(f"  [INFO] 外れ値除外:")
    print(f"    - 40件以上の希望地: {excluded_count_total}人")
    print(f"    - 5都道府県以上: {excluded_count_pref}人")
    print(f"    - 合計除外: {excluded_count_total + excluded_count_pref}人")
    print(f"  [INFO] 有効求職者: {len(multi_area_applicants) - excluded_count_total - excluded_count_pref}人")

    # DataFrameに変換
    df_patterns = pd.DataFrame(pattern_rows)

    # グループ化してカウント
    grouped = df_patterns.groupby([
        'prefecture', 'municipality',
        'co_desired_prefecture', 'co_desired_municipality',
        'age_group', 'gender'
    ]).size().reset_index(name='count')

    print(f"  [INFO] グループ化後: {len(grouped)}行")

    # row_type追加
    grouped['row_type'] = 'DESIRED_AREA_PATTERN'

    # カラム順序調整
    result = grouped[[
        'row_type', 'prefecture', 'municipality',
        'co_desired_prefecture', 'co_desired_municipality',
        'age_group', 'gender', 'count'
    ]]

    # 保存
    output_dir = Path('data/output_v2/desired_area_pattern')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'DesiredAreaPattern.csv'
    result.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n[SAVE] {output_file}")
    print(f"  [OK] {len(result)}行保存")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"総行数: {len(result)}")
    print(f"ユニーク主希望地数: {result['prefecture'].nunique()}都道府県")
    print(f"ユニーク併願地数: {result['co_desired_prefecture'].nunique()}都道府県")

    # 都道府県間併願パターンTOP10
    print("\n都道府県間併願パターンTOP10:")
    pref_patterns = result.groupby(['prefecture', 'co_desired_prefecture'])['count'].sum().sort_values(ascending=False).head(10)
    for i, ((pref1, pref2), count) in enumerate(pref_patterns.items(), 1):
        print(f"  {i:2d}. {pref1} ⇄ {pref2}: {count:,}件")

    # 最も併願されている市区町村TOP10
    print("\n併願先TOP10:")
    co_desired_top = result.groupby(['co_desired_prefecture', 'co_desired_municipality'])['count'].sum().sort_values(ascending=False).head(10)
    for i, ((pref, muni), count) in enumerate(co_desired_top.items(), 1):
        print(f"  {i:2d}. {pref}{muni}: {count:,}件")

    print("\n" + "=" * 60)
    print("✅ DESIRED_AREA_PATTERN生成完了")
    print("=" * 60)

    return result


if __name__ == '__main__':
    result = generate_desired_area_pattern()
