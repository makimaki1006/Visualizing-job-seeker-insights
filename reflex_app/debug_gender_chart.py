# -*- coding: utf-8 -*-
"""性別構成グラフのデバッグスクリプト"""
import db_helper
import pandas as pd

# データ取得
df = db_helper.get_all_data()

# 都道府県選択（例: 群馬県）
prefecture = '群馬県'

# SUMMARYデータをフィルタ
summary_data = df[
    (df['row_type'] == 'SUMMARY') &
    (df['prefecture'] == prefecture)
]

print("=== 性別構成グラフ データ確認 ===")
print(f"\n選択都道府県: {prefecture}")
print(f"SUMMARYデータ件数: {len(summary_data)}")

if not summary_data.empty:
    print("\n=== SUMMARY行の詳細 ===")
    print(summary_data[['prefecture', 'municipality', 'female_count', 'male_count']].to_string())

    # 合計値
    female_total = summary_data['female_count'].sum()
    male_total = summary_data['male_count'].sum()

    print(f"\n=== 集計結果 ===")
    print(f"女性合計: {female_total:,}")
    print(f"男性合計: {male_total:,}")
    print(f"総計: {female_total + male_total:,}")

    # グラフデータ形式
    print(f"\n=== グラフデータ（期待値） ===")
    chart_data = [
        {"name": "女性", "value": int(female_total)},
        {"name": "男性", "value": int(male_total)}
    ]
    print(chart_data)
else:
    print("⚠️ SUMMARYデータが見つかりません")

# 念のため、他のrow_typeも確認
print(f"\n=== {prefecture}の全row_type分布 ===")
pref_data = df[df['prefecture'] == prefecture]
print(pref_data['row_type'].value_counts())
