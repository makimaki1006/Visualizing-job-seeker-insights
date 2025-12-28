# -*- coding: utf-8 -*-
"""RESIDENCE_FLOW生成スクリプト

居住地→希望地の人材フロー分析
※ v2.0: MOBILITY_PATTERNを統合（mobility_type, avg_reference_distance_km追加）
※ v2.1: 距離統計カラム追加（median, min, max, std, q25, q75）
※ v2.2: 新規地域自動検出・geocache自動更新機能追加
"""
import pandas as pd
import numpy as np
import sys
import io
import json
import math
import time
import urllib.request
from pathlib import Path
import re
from scipy import stats
from urllib.parse import quote

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


# =============================================================
# Geocache自動更新モジュール（Geolonia API連携）
# =============================================================

def fetch_json_from_geolonia(url, retries=3):
    """Geolonia APIからJSONを取得（リトライあり）"""
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    return None


def get_municipality_coordinate(pref_name, muni_name):
    """市区町村の代表座標をGeolonia APIから取得（町丁目データの平均）"""
    url = f"https://geolonia.github.io/japanese-addresses/api/ja/{quote(pref_name)}/{quote(muni_name)}.json"

    try:
        data = fetch_json_from_geolonia(url)
        if not data:
            return None

        lats = []
        lngs = []
        for item in data:
            if isinstance(item, dict):
                lat = item.get('lat')
                lng = item.get('lng')
                if lat is not None and lng is not None:
                    try:
                        lats.append(float(lat))
                        lngs.append(float(lng))
                    except (ValueError, TypeError):
                        pass

        if lats and lngs:
            return {
                'lat': round(sum(lats) / len(lats), 4),
                'lng': round(sum(lngs) / len(lngs), 4)
            }
        return None
    except Exception:
        return None


def update_geocache_for_missing(missing_locations, geocache, geocache_path):
    """未登録地域をGeolonia APIから取得してgeocacheを更新

    Args:
        missing_locations: 未登録地域名のセット（例: {'東京都新宿区', '大阪府大阪市'}）
        geocache: 現在のgeocache辞書
        geocache_path: geocache.jsonのパス

    Returns:
        (updated_count, failed_list): 更新件数と失敗リスト
    """
    if not missing_locations:
        return 0, []

    print(f"\n[GEOCACHE] 新規地域検出: {len(missing_locations)}件")
    print("[GEOCACHE] Geolonia APIから座標取得中...")

    updated_count = 0
    failed_list = []

    for location in missing_locations:
        # 都道府県と市区町村を分離
        pref, muni = extract_prefecture_municipality(location)
        if not pref or not muni:
            failed_list.append(location)
            continue

        # Geolonia APIから座標取得
        coord = get_municipality_coordinate(pref, muni)

        if coord:
            geocache[location] = coord
            updated_count += 1
            print(f"  [ADD] {location}: lat={coord['lat']}, lng={coord['lng']}")
        else:
            failed_list.append(location)

        # レート制限対策
        time.sleep(0.2)

    # geocache保存
    if updated_count > 0:
        with open(geocache_path, 'w', encoding='utf-8') as f:
            json.dump(geocache, f, ensure_ascii=False, indent=2)
        print(f"\n[GEOCACHE] 更新完了: {updated_count}件追加 -> {geocache_path}")

    if failed_list:
        print(f"[GEOCACHE] 取得失敗: {len(failed_list)}件")
        for loc in failed_list[:5]:
            print(f"  - {loc}")
        if len(failed_list) > 5:
            print(f"  ... 他{len(failed_list) - 5}件")

    return updated_count, failed_list


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


def generate_residence_flow():
    """RESIDENCE_FLOWデータ生成（MOBILITY_PATTERN統合版）"""
    print("\n" + "=" * 60)
    print("RESIDENCE_FLOW生成開始（MOBILITY_PATTERN統合版）")
    print("=" * 60)

    # Geocache読み込み（距離計算用）
    geocache_path = Path('data/output_v2/geocache.json')
    geocache = {}
    if geocache_path.exists():
        print(f"\n[LOAD] {geocache_path}")
        with open(geocache_path, 'r', encoding='utf-8') as f:
            geocache = json.load(f)
        print(f"  [OK] {len(geocache)}件読み込み")
    else:
        print(f"\n[WARN] {geocache_path} が見つかりません。距離計算はスキップされます。")

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

    # フロー行生成（距離・移動タイプ計算を含む）
    flow_rows = []
    skipped_count = 0
    missing_geocode = set()

    for _, row in df_merged.iterrows():
        # 必須フィールドの確認
        desired_pref = row.get('desired_prefecture')
        desired_muni = row.get('desired_municipality')
        residence_pref = row.get('residence_prefecture')
        residence_muni = row.get('residence_municipality')

        # 必須フィールドがNaNの場合はスキップ
        if pd.isna(desired_pref) or pd.isna(desired_muni):
            skipped_count += 1
            continue
        if pd.isna(residence_pref) or pd.isna(residence_muni):
            skipped_count += 1
            continue

        # フル市区町村名
        residence_full = f"{residence_pref}{residence_muni}"
        desired_full = f"{desired_pref}{desired_muni}"

        # 距離計算
        res_coord = geocache.get(residence_full)
        des_coord = geocache.get(desired_full)

        if res_coord and des_coord:
            distance = haversine_distance(
                res_coord['lat'], res_coord['lng'],
                des_coord['lat'], des_coord['lng']
            )
        else:
            distance = None
            if not res_coord:
                missing_geocode.add(residence_full)
            if not des_coord:
                missing_geocode.add(desired_full)

        # 移動タイプ分類
        if distance is None:
            # 座標がない場合は都道府県ベースで分類
            if residence_pref != desired_pref:
                mobility_type = '遠距離移動'
            elif residence_full == desired_full:
                mobility_type = '地元希望'
            else:
                mobility_type = '近隣移動'  # デフォルト
        else:
            mobility_type = classify_mobility_type(residence_full, desired_full, distance)

        flow_rows.append({
            'residence_prefecture': residence_pref,
            'residence_municipality': residence_muni,
            'desired_prefecture': desired_pref,
            'desired_municipality': desired_muni,
            'age_group': row['age_group'],
            'gender': row['gender'],
            'mobility_type': mobility_type,
            'reference_distance_km': round(distance, 1) if distance is not None else None
        })

    print(f"  [INFO] スキップ: {skipped_count}件")

    # 新規地域があればgeocacheを自動更新
    if missing_geocode:
        print(f"  [WARN] ジオコード未登録: {len(missing_geocode)}件")
        updated_count, failed = update_geocache_for_missing(missing_geocode, geocache, geocache_path)

        # geocache更新後、再計算が必要な行をリトライ
        if updated_count > 0:
            print(f"\n[RETRY] geocache更新後の再計算中...")
            retry_count = 0
            for row in flow_rows:
                if row['reference_distance_km'] is None:
                    res_full = f"{row['residence_prefecture']}{row['residence_municipality']}"
                    des_full = f"{row['desired_prefecture']}{row['desired_municipality']}"
                    res_coord = geocache.get(res_full)
                    des_coord = geocache.get(des_full)

                    if res_coord and des_coord:
                        distance = haversine_distance(
                            res_coord['lat'], res_coord['lng'],
                            des_coord['lat'], des_coord['lng']
                        )
                        row['reference_distance_km'] = round(distance, 1)
                        row['mobility_type'] = classify_mobility_type(res_full, des_full, distance)
                        retry_count += 1

            print(f"  [OK] {retry_count}件の距離を再計算")

    print(f"  [INFO] フロー展開: {len(flow_rows)}件")

    # DataFrameに変換
    df_flows = pd.DataFrame(flow_rows)

    # グループ化してカウント（距離統計と移動タイプの最頻値も計算）
    def get_dominant_mobility_type(g):
        """最頻値の移動タイプを取得"""
        return g.value_counts().idxmax()

    def calc_mode_distance(g):
        """距離の最頻値を計算（10km単位で丸めてから最頻値）"""
        valid = g.dropna()
        if valid.empty:
            return None
        # 10km単位で丸めて最頻値を計算
        rounded = (valid / 10).round() * 10
        mode_result = stats.mode(rounded, keepdims=True)
        return mode_result.mode[0] if len(mode_result.mode) > 0 else None

    def calc_percentile(g, percentile):
        """パーセンタイル計算"""
        valid = g.dropna()
        if valid.empty:
            return None
        return np.percentile(valid, percentile)

    # グループ化キー
    group_keys = [
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender'
    ]

    # グループ化と集約
    grouped = df_flows.groupby(group_keys).agg({
        'reference_distance_km': [
            ('avg_distance_km', 'mean'),           # 平均
            ('median_distance_km', 'median'),      # 中央値
            ('min_distance_km', 'min'),            # 最小値
            ('max_distance_km', 'max'),            # 最大値
            ('std_distance_km', 'std'),            # 標準偏差
            ('q25_distance_km', lambda x: calc_percentile(x, 25)),  # 25パーセンタイル
            ('q75_distance_km', lambda x: calc_percentile(x, 75)),  # 75パーセンタイル
            ('mode_distance_km', calc_mode_distance)  # 最頻値（10km単位）
        ],
        'mobility_type': [
            ('mobility_type', get_dominant_mobility_type)
        ]
    })

    # MultiIndexカラムをフラットに
    grouped.columns = [col[1] if col[1] else col[0] for col in grouped.columns]
    grouped = grouped.reset_index()

    # カウントを追加
    count_series = df_flows.groupby(group_keys).size()
    grouped['count'] = count_series.values

    # 小数点丸め
    distance_cols = ['avg_distance_km', 'median_distance_km', 'min_distance_km',
                     'max_distance_km', 'std_distance_km', 'q25_distance_km',
                     'q75_distance_km', 'mode_distance_km']
    for col in distance_cols:
        if col in grouped.columns:
            grouped[col] = grouped[col].round(1)

    print(f"  [INFO] グループ化後: {len(grouped)}行")

    # row_type追加
    grouped['row_type'] = 'RESIDENCE_FLOW'

    # カラム名の互換性維持（avg_reference_distance_km）
    grouped = grouped.rename(columns={'avg_distance_km': 'avg_reference_distance_km'})

    # カラム順序調整（統計カラム追加）
    result = grouped[[
        'row_type',
        'residence_prefecture', 'residence_municipality',
        'desired_prefecture', 'desired_municipality',
        'age_group', 'gender', 'count',
        'mobility_type',
        'avg_reference_distance_km',   # 平均（互換性維持）
        'median_distance_km',           # 中央値
        'mode_distance_km',             # 最頻値（10km単位）
        'min_distance_km',              # 最小値
        'max_distance_km',              # 最大値
        'std_distance_km',              # 標準偏差
        'q25_distance_km',              # 25パーセンタイル
        'q75_distance_km'               # 75パーセンタイル
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

    # 移動タイプ分布（新規追加）
    print("\n移動タイプ分布:")
    mobility_dist = result.groupby('mobility_type')['count'].sum().sort_values(ascending=False)
    for mobility_type, count in mobility_dist.items():
        print(f"  {mobility_type}: {count:,}件")

    # 移動タイプ別平均距離（新規追加）
    print("\n移動タイプ別平均距離:")
    avg_distances = result.groupby('mobility_type')['avg_reference_distance_km'].mean()
    for mobility_type, avg_dist in avg_distances.items():
        if pd.notna(avg_dist):
            print(f"  {mobility_type}: {avg_dist:.1f}km")

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
    print("RESIDENCE_FLOW生成完了（MOBILITY_PATTERN統合版）")
    print("=" * 60)

    return result


if __name__ == '__main__':
    result = generate_residence_flow()
