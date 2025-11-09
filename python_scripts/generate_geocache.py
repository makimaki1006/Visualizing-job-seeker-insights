"""
geocache.json生成スクリプト
実データから必要な市区町村を抽出し、座標を生成
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict

# データパス
csv_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251027_180947.csv"
geocache_path = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\output_v2\geocache.json")

print("=" * 80)
print("geocache.json生成スクリプト")
print("=" * 80)
print()

# 既存のgeocache読み込み
existing_geocache = {}
if geocache_path.exists():
    with open(geocache_path, 'r', encoding='utf-8') as f:
        existing_geocache = json.load(f)
    print(f"既存geocache: {len(existing_geocache)}件")
else:
    print("既存geocacheなし（新規作成）")

# CSVデータ読み込み
df = pd.read_csv(csv_path, encoding='utf-8-sig')
print(f"データ件数: {len(df)}件")
print()

# locationカラムから市区町村を抽出
from data_normalizer import DataNormalizer
normalizer = DataNormalizer()

unique_locations = set()

# 居住地から抽出
for location in df['location'].dropna():
    parsed = normalizer.parse_location(location)
    if parsed['prefecture'] and parsed['municipality']:
        key = f"{parsed['prefecture']}{parsed['municipality']}"
        unique_locations.add((parsed['prefecture'], parsed['municipality'], key))

# 希望勤務地から抽出
for desired_area in df['desired_area'].dropna():
    areas = normalizer.parse_desired_area(desired_area)
    for area in areas:
        if area['prefecture'] and area['municipality']:
            key = f"{area['prefecture']}{area['municipality']}"
            unique_locations.add((area['prefecture'], area['municipality'], key))

print(f"ユニーク地域数: {len(unique_locations)}箇所")
print()

# 都道府県別の中心座標（簡易版）
prefecture_center_coords = {
    '北海道': {'lat': 43.064301, 'lng': 141.346874},
    '青森県': {'lat': 40.824308, 'lng': 140.739998},
    '岩手県': {'lat': 39.703531, 'lng': 141.152667},
    '宮城県': {'lat': 38.268837, 'lng': 140.872101},
    '秋田県': {'lat': 39.718614, 'lng': 140.102364},
    '山形県': {'lat': 38.240436, 'lng': 140.363633},
    '福島県': {'lat': 37.750299, 'lng': 140.467551},
    '茨城県': {'lat': 36.341811, 'lng': 140.446793},
    '栃木県': {'lat': 36.565725, 'lng': 139.883565},
    '群馬県': {'lat': 36.390668, 'lng': 139.060406},
    '埼玉県': {'lat': 35.856999, 'lng': 139.648849},
    '千葉県': {'lat': 35.605057, 'lng': 140.123306},
    '東京都': {'lat': 35.689488, 'lng': 139.691706},
    '神奈川県': {'lat': 35.447507, 'lng': 139.642345},
    '新潟県': {'lat': 37.902552, 'lng': 139.023095},
    '富山県': {'lat': 36.695291, 'lng': 137.211338},
    '石川県': {'lat': 36.594682, 'lng': 136.625573},
    '福井県': {'lat': 36.065178, 'lng': 136.221527},
    '山梨県': {'lat': 35.664158, 'lng': 138.568449},
    '長野県': {'lat': 36.651299, 'lng': 138.181239},
    '岐阜県': {'lat': 35.391227, 'lng': 136.722291},
    '静岡県': {'lat': 34.976987, 'lng': 138.383084},
    '愛知県': {'lat': 35.180188, 'lng': 136.906565},
    '三重県': {'lat': 34.730283, 'lng': 136.508588},
    '滋賀県': {'lat': 35.004531, 'lng': 135.868605},
    '京都府': {'lat': 35.021247, 'lng': 135.755597},
    '大阪府': {'lat': 34.686297, 'lng': 135.519661},
    '兵庫県': {'lat': 34.691269, 'lng': 135.183071},
    '奈良県': {'lat': 34.685334, 'lng': 135.805},
    '和歌山県': {'lat': 34.226034, 'lng': 135.167509},
    '鳥取県': {'lat': 35.503868, 'lng': 134.237736},
    '島根県': {'lat': 35.472295, 'lng': 133.050568},
    '岡山県': {'lat': 34.661751, 'lng': 133.934406},
    '広島県': {'lat': 34.396642, 'lng': 132.459622},
    '山口県': {'lat': 34.185956, 'lng': 131.470649},
    '徳島県': {'lat': 34.065718, 'lng': 134.559297},
    '香川県': {'lat': 34.340149, 'lng': 134.043444},
    '愛媛県': {'lat': 33.841649, 'lng': 132.765681},
    '高知県': {'lat': 33.559706, 'lng': 133.531079},
    '福岡県': {'lat': 33.606576, 'lng': 130.418297},
    '佐賀県': {'lat': 33.249442, 'lng': 130.299794},
    '長崎県': {'lat': 32.744839, 'lng': 129.873756},
    '熊本県': {'lat': 32.789827, 'lng': 130.741667},
    '大分県': {'lat': 33.238172, 'lng': 131.612619},
    '宮崎県': {'lat': 31.911096, 'lng': 131.423855},
    '鹿児島県': {'lat': 31.560146, 'lng': 130.557978},
    '沖縄県': {'lat': 26.212401, 'lng': 127.680932}
}

# 市区町村レベルの座標オフセット（簡易版）
# 実際のプロダクションではGoogle Maps APIを使用すべき
def generate_municipality_offset(index: int) -> tuple:
    """
    市区町村ごとのオフセットを生成（簡易版）
    indexに基づいて少しずつずらす
    """
    offset_lat = (index % 10 - 5) * 0.01  # -0.05 ~ +0.05度
    offset_lng = ((index // 10) % 10 - 5) * 0.01
    return (offset_lat, offset_lng)

# geocache生成
new_geocache = existing_geocache.copy()
added_count = 0
skipped_count = 0

for index, (pref, muni, key) in enumerate(sorted(unique_locations)):
    # すでにキャッシュにある場合はスキップ
    if key in new_geocache:
        skipped_count += 1
        continue

    # 都道府県の中心座標を取得
    if pref in prefecture_center_coords:
        base_coords = prefecture_center_coords[pref]
        offset_lat, offset_lng = generate_municipality_offset(index)

        new_geocache[key] = {
            'lat': round(base_coords['lat'] + offset_lat, 6),
            'lng': round(base_coords['lng'] + offset_lng, 6),
            'prefecture': pref,
            'municipality': muni
        }
        added_count += 1
    else:
        print(f"  [警告] 未知の都道府県: {pref}")

print(f"結果:")
print(f"  既存: {len(existing_geocache)}件")
print(f"  追加: {added_count}件")
print(f"  スキップ: {skipped_count}件")
print(f"  合計: {len(new_geocache)}件")
print()

# geocache保存
geocache_path.parent.mkdir(parents=True, exist_ok=True)
with open(geocache_path, 'w', encoding='utf-8') as f:
    json.dump(new_geocache, f, ensure_ascii=False, indent=2)

print(f"[OK] geocache.json保存完了: {geocache_path}")
print()

# カバレッジ確認
total_locations = len(unique_locations)
cached_locations = sum(1 for _, _, key in unique_locations if key in new_geocache)
coverage = cached_locations / total_locations * 100 if total_locations > 0 else 0

print(f"カバレッジ: {coverage:.1f}% ({cached_locations}/{total_locations})")

if coverage < 100:
    uncached = [key for _, _, key in unique_locations if key not in new_geocache]
    print(f"\n[警告] 未キャッシュ地域: {len(uncached)}箇所")
    if len(uncached) <= 10:
        for key in uncached:
            print(f"  - {key}")

print()
print("=" * 80)
print("完了")
print("=" * 80)
