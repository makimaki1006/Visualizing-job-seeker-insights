# -*- coding: utf-8 -*-
"""V3 CSVデータ活用状況分析スクリプト"""
import pandas as pd

# V3 CSV読み込み
df = pd.read_csv('MapComplete_Complete_All_FIXED.csv', encoding='utf-8-sig', low_memory=False)

print("=" * 80)
print("V3 CSVデータ活用状況分析")
print("=" * 80)

# 1. 全カラムリスト
print(f"\n【1】全カラム一覧（{len(df.columns)}個）")
print("=" * 80)
for i, col in enumerate(df.columns, 1):
    non_null = df[col].notna().sum()
    pct = (non_null / len(df)) * 100
    print(f"{i:2d}. {col:30s} - データあり: {non_null:6,}行 ({pct:5.1f}%)")

# 2. row_type別データ分布
print(f"\n【2】row_type別データ分布")
print("=" * 80)
row_type_counts = df['row_type'].value_counts()
for rt, count in row_type_counts.items():
    pct = (count / len(df)) * 100
    print(f"{rt:25s}: {count:5,}行 ({pct:5.1f}%)")

print(f"\n総行数: {len(df):,}行")

# 3. 各row_typeで利用可能な主要カラム
print(f"\n【3】各row_typeで利用可能な主要カラム")
print("=" * 80)

for rt in row_type_counts.index:
    rt_df = df[df['row_type'] == rt]
    print(f"\n■ {rt} ({len(rt_df):,}行)")

    # 50%以上データがあるカラムのみ表示
    useful_cols = []
    for col in df.columns:
        if col == 'row_type':
            continue
        non_null = rt_df[col].notna().sum()
        pct = (non_null / len(rt_df)) * 100
        if pct >= 50:
            useful_cols.append((col, non_null, pct))

    # データあり率でソート
    useful_cols.sort(key=lambda x: x[2], reverse=True)

    for col, non_null, pct in useful_cols[:15]:  # 上位15個
        print(f"  - {col:30s}: {non_null:6,}行 ({pct:5.1f}%)")

# 4. 現在未使用のカラム候補
print(f"\n【4】活用可能性が高い未使用カラム候補")
print("=" * 80)

# 現在のダッシュボードで使用されている主要カラム
used_cols = [
    'row_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3',
    'count', 'male_count', 'female_count', 'demand_count', 'supply_count', 'gap',
    'avg_age', 'inflow', 'outflow', 'net_flow'
]

print("\n■ データが豊富だが未活用のカラム:")
for col in df.columns:
    if col in used_cols:
        continue

    non_null = df[col].notna().sum()
    pct = (non_null / len(df)) * 100

    # 50%以上データがあるカラム
    if pct >= 50:
        print(f"  - {col:30s}: {non_null:6,}行 ({pct:5.1f}%) ← 未活用")

# 5. 具体的な活用提案
print(f"\n【5】具体的な可視化提案")
print("=" * 80)

print("""
■ 提案1: 資格・スキル分析パネル
  - avg_qualifications（平均資格数）
  - avg_qualification_count（平均資格カウント）
  - national_license_rate（国家資格保有率）
  - has_national_license（国家資格保有フラグ）
  → グラフ: 資格保有率ヒートマップ、資格数分布ヒストグラム

■ 提案2: 市場シェア・競合分析パネル
  - market_share_pct（市場シェア%）
  - total_applicants（総申請者数）
  - demand_supply_ratio（需給比率）
  → グラフ: 市場シェアランキング、需給比率散布図

■ 提案3: 緊急度・モチベーション分析パネル
  - avg_urgency_score（平均緊急度スコア）
  - avg_mobility_score（平均移動許容度スコア）
  → グラフ: 緊急度×移動許容度マトリクス、緊急度分布ヒートマップ

■ 提案4: 年齢・性別・就業状況詳細分析
  - avg_age（平均年齢）
  - male_ratio（男性比率）
  - female_ratio（女性比率）
  - employment_rate（就業率）
  - top_employment_ratio（トップ就業状況比率）
  → グラフ: 年齢×性別×就業状況3D散布図

■ 提案5: 地理的分析（座標活用）
  - latitude（緯度）
  - longitude（経度）
  → グラフ: 実際の地図プロット（Plotly Mapbox）

■ 提案6: 希少性スコアリング
  - rarity_score（希少性スコア）
  - top_age_ratio（トップ年齢比率）
  → グラフ: 希少性スコアTop 20ランキング
""")

print("\n" + "=" * 80)
print("分析完了")
print("=" * 80)
