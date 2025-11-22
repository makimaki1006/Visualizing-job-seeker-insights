# -*- coding: utf-8 -*-
"""MOBILITY_PATTERN生成スクリプト

移動パターン分析: 地元希望・近隣移動・中距離移動・遠距離移動を分類
"""
import pandas as pd
import sys
import io
import json
import math
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


def haversine_distance(lat1, lon1, lat2, lon2):
    """2点間の距離をkm単位で計算（Haversine公式）"""
    R = 6371  # 地球の半径（km）

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def classify_mobility_type(residence_full, desired_full, distance):
    """移動タイプを分類"""
    # 同一市区町村
    if residence_full == desired_full:
        return '地元希望'

    # 都道府県を抽出
    res_pref, _ = extract_prefecture_municipality(residence_full)
    des_pref, _ = extract_prefecture_municipality(desired_full)

    # 都道府県が異なる場合は遠距離
    if res_pref != des_pref:
        return '遠距離移動'

    # 同一都道府県内の場合は距離で分類
    if distance < 30:
        return '近隣移動'
    elif distance < 80:
        return '中距離移動'
    else:
        return '遠距離移動'


def generate_mobility_pattern():
    """MOBILITY_PATTERNデータ生成"""
    print("\n" + "=" * 60)
    print("MOBILITY_PATTERN生成開始")
    print("=" * 60)

    # Geocache読み込み
    geocache_path = Path('data/output_v2/geocache.json')
    print(f"\n[LOAD] {geocache_path}")
    with open(geocache_path, 'r', encoding='utf-8') as f:
        geocache = json.load(f)
    print(f"  [OK] {len(geocache)}件読み込み")

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
        df_applicants[['applicant_id', 'age_group', 'gender', 'employment_status',
                       'residence_prefecture', 'residence_municipality']],
        on='applicant_id',
        how='left'
    )

    print(f"  [INFO] マージ後: {len(df_merged)}行")

    # 移動パターン行生成
    pattern_rows = []
    missing_geocode = set()

    for _, row in df_merged.iterrows():
        # 希望地が存在しない場合はスキップ
        if pd.isna(row['desired_municipality']):
            continue

        # フル市区町村名
        residence_full = f"{row['residence_prefecture']}{row['residence_municipality']}"

        # 希望地の都道府県・市区町村を分離
        # desired_prefectureカラム優先、欠損時はフォールバック
        desired_pref = row.get('desired_prefecture')
        if pd.isna(desired_pref) or not desired_pref:
            # フォールバック: 正規表現で抽出
            desired_pref, desired_muni = extract_prefecture_municipality(row['desired_municipality'])
        else:
            # prefectureカラムがある場合、市区町村部分のみ抽出
            _, desired_muni = extract_prefecture_municipality(row['desired_municipality'])

        if not desired_pref or not desired_muni:
            continue

        desired_full = f"{desired_pref}{desired_muni}"

        # 座標取得
        res_coord = geocache.get(residence_full)
        des_coord = geocache.get(desired_full)

        # 距離計算
        if res_coord and des_coord:
            distance = haversine_distance(
                res_coord['lat'], res_coord['lng'],
                des_coord['lat'], des_coord['lng']
            )
        else:
            # 座標が見つからない場合はNone（後で分類時にフォールバック）
            distance = None
            if not res_coord:
                missing_geocode.add(residence_full)
            if not des_coord:
                missing_geocode.add(desired_full)

        # 移動タイプ分類
        if distance is None:
            # 座標がない場合は都道府県ベースで分類
            res_pref = row['residence_prefecture']
            if res_pref != desired_pref:
                mobility_type = '遠距離移動'
            elif residence_full == desired_full:
                mobility_type = '地元希望'
            else:
                mobility_type = '近隣移動'  # デフォルト
        else:
            mobility_type = classify_mobility_type(residence_full, desired_full, distance)

        pattern_rows.append({
            'residence_prefecture': row['residence_prefecture'],
            'residence_municipality': row['residence_municipality'],
            'desired_prefecture': desired_pref,
            'desired_municipality': desired_muni,
            'age_group': row['age_group'],
            'gender': row['gender'],
            'employment_status': row['employment_status'],
            'mobility_type': mobility_type,
            'reference_distance_km': round(distance, 1) if distance is not None else None
        })

    print(f"  [INFO] 移動パターン展開: {len(pattern_rows)}件")
    if missing_geocode:
        print(f"  [WARN] ジオコード未登録: {len(missing_geocode)}件")

    # DataFrameに変換
    df_patterns = pd.DataFrame(pattern_rows)

    # グループ化してカウント（参照距離の平均も計算）
    grouped = df_patterns.groupby([
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender', 'employment_status', 'mobility_type'
    ]).agg({
        'reference_distance_km': 'mean'
    }).reset_index()
    grouped = grouped.rename(columns={'reference_distance_km': 'avg_reference_distance_km'})

    # カウントを追加
    grouped['count'] = df_patterns.groupby([
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender', 'employment_status', 'mobility_type'
    ]).size().values

    print(f"  [INFO] グループ化後: {len(grouped)}行")

    # row_type追加
    grouped['row_type'] = 'MOBILITY_PATTERN'

    # カラム順序調整
    result = grouped[[
        'row_type',
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender', 'employment_status',
        'mobility_type', 'avg_reference_distance_km', 'count'
    ]]

    # 保存
    output_dir = Path('data/output_v2/mobility_pattern')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / 'MobilityPattern.csv'
    result.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"\n[SAVE] {output_file}")
    print(f"  [OK] {len(result)}行保存")

    # 統計情報
    print("\n" + "=" * 60)
    print("統計情報")
    print("=" * 60)
    print(f"総行数: {len(result)}")

    print("\n移動タイプ分布:")
    mobility_dist = result.groupby('mobility_type')['count'].sum().sort_values(ascending=False)
    for mobility_type, count in mobility_dist.items():
        print(f"  {mobility_type}: {count:,}件")

    print("\n移動タイプ別平均距離:")
    avg_distances = result.groupby('mobility_type')['avg_reference_distance_km'].mean()
    for mobility_type, avg_dist in avg_distances.items():
        if pd.notna(avg_dist):
            print(f"  {mobility_type}: {avg_dist:.1f}km")

    print("\n年齢層別移動タイプ:")
    age_mobility = result.groupby(['age_group', 'mobility_type'])['count'].sum().unstack(fill_value=0)
    print(age_mobility.to_string())

    print("\n" + "=" * 60)
    print("✅ MOBILITY_PATTERN生成完了")
    print("=" * 60)

    return result


if __name__ == '__main__':
    result = generate_mobility_pattern()
