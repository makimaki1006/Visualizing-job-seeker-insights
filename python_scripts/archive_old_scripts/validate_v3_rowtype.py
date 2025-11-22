# -*- coding: utf-8 -*-
"""V3 CSV row_type検証スクリプト

不要なrow_typeが削除され、新しいrow_typeが追加されたことを確認します。
"""
import pandas as pd
import sys
import io
from pathlib import Path

# Windows環境での絵文字出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "=" * 60)
print("V3 CSV row_type検証")
print("=" * 60)

# V3 CSV読み込み
csv_path = Path('data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv')
print(f"\n[LOAD] {csv_path}")

df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
print(f"  [OK] {len(df)}行読み込み")

# row_type別件数
print("\n" + "=" * 60)
print("row_type別件数")
print("=" * 60)

row_type_counts = df['row_type'].value_counts().sort_values(ascending=False)
total_rows = len(df)

for row_type, count in row_type_counts.items():
    percentage = (count / total_rows * 100)
    print(f"{row_type:30s}: {count:5d}行 ({percentage:5.2f}%)")

print(f"\n{'総計':30s}: {total_rows:5d}行")

# 削除対象row_typeチェック
print("\n" + "=" * 60)
print("削除対象row_typeチェック")
print("=" * 60)

removed_types = ['RARITY', 'URGENCY_AGE', 'URGENCY_EMPLOYMENT', 'FLOW', 'COMPETITION']
all_removed = True

for row_type in removed_types:
    count = len(df[df['row_type'] == row_type])
    if count > 0:
        print(f"  ❌ {row_type}: {count}行（削除失敗）")
        all_removed = False
    else:
        print(f"  ✅ {row_type}: 0行（削除成功）")

if all_removed:
    print("\n✅ すべての不要row_typeが正常に削除されました")
else:
    print("\n❌ 一部のrow_typeが残っています")

# 新規追加row_typeチェック
print("\n" + "=" * 60)
print("新規追加row_typeチェック（今後追加予定）")
print("=" * 60)

new_types = ['PERSONA_MUNI', 'QUALIFICATION_DETAIL', 'DESIRED_AREA_PATTERN',
             'RESIDENCE_FLOW', 'MOBILITY_PATTERN']

for row_type in new_types:
    count = len(df[df['row_type'] == row_type])
    if count > 0:
        print(f"  ✅ {row_type}: {count}行（既に追加済み）")
    else:
        print(f"  ⏳ {row_type}: 0行（未追加）")

print("\n" + "=" * 60)
print("検証完了")
print("=" * 60)
