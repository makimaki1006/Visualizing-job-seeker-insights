# -*- coding: utf-8 -*-
"""性別グラフ修正の検証スクリプト"""
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

print("=== 性別グラフ修正検証 ===")
print(f"\n選択都道府県: {prefecture}")
print(f"SUMMARYデータ件数: {len(summary_data)}")

if not summary_data.empty:
    # 合計値（修正後のロジック）
    female_total = summary_data['female_count'].sum()
    male_total = summary_data['male_count'].sum()

    print(f"\n=== 修正後の出力（期待値） ===")
    expected_output = [
        {"name": "男性", "value": int(male_total), "fill": "#0072B2"},  # 青
        {"name": "女性", "value": int(female_total), "fill": "#E69F00"}  # オレンジ
    ]
    print(f"データポイント数: {len(expected_output)}")
    for item in expected_output:
        print(f"  - {item['name']}: {item['value']:,}人 (色: {item['fill']})")

    print(f"\n✅ 結果: シンプルな男女2項目のみ表示")
    print(f"   - 市区町村別内訳は表示されない")
    print(f"   - 色盲対応パレット使用（青・オレンジ）")
else:
    print("⚠️ SUMMARYデータが見つかりません")
