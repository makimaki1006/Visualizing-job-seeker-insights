# -*- coding: utf-8 -*-
"""各タブ・各グラフのrow_type使用状況分析"""
import pandas as pd
import re
from pathlib import Path

# V3 CSV読み込み
df = pd.read_csv('MapComplete_Complete_All_FIXED.csv', encoding='utf-8-sig', low_memory=False)

# row_type別行数
print("=" * 80)
print("V3 CSV row_type別行数")
print("=" * 80)
print(df['row_type'].value_counts().to_string())
print(f"\n総行数: {len(df)}行\n")

# mapcomplete_dashboard.pyからrow_type使用状況を抽出
dashboard_file = Path('mapcomplete_dashboard/mapcomplete_dashboard.py')
content = dashboard_file.read_text(encoding='utf-8')

# row_type使用箇所を抽出
row_type_pattern = r"df\['row_type'\] == '([A-Z_]+)'"
matches = re.findall(row_type_pattern, content)

print("=" * 80)
print("コード内でのrow_type使用回数")
print("=" * 80)
from collections import Counter
usage_counter = Counter(matches)
for row_type, count in usage_counter.most_common():
    print(f"{row_type}: {count}回使用")

print()

# 関数名とrow_typeのマッピング抽出
print("=" * 80)
print("各グラフ計算関数のrow_type使用")
print("=" * 80)

# @rx.var関数名とその中で使われるrow_typeを抽出
function_pattern = r'@rx\.var.*?\n\s+def\s+(\w+)\(self\).*?:\s*\n(.*?)(?=\n\s+@rx\.var|\n\s+def\s+\w+|\nclass\s|\Z)'
functions = re.findall(function_pattern, content, re.DOTALL)

function_usage = {}
for func_name, func_body in functions:
    # この関数内で使用されているrow_typeを抽出
    row_types_in_func = re.findall(row_type_pattern, func_body)
    if row_types_in_func:
        function_usage[func_name] = row_types_in_func

# 関数名でソートして表示
for func_name in sorted(function_usage.keys()):
    row_types = function_usage[func_name]
    print(f"\n{func_name}():")
    for rt in row_types:
        row_count = len(df[df['row_type'] == rt])
        print(f"  - {rt}: {row_count:,}行")

print()

# 未使用row_typeの検出
print("=" * 80)
print("未使用または低使用率のrow_type")
print("=" * 80)
all_row_types = set(df['row_type'].unique())
used_row_types = set(matches)
unused_row_types = all_row_types - used_row_types

if unused_row_types:
    print("\n❌ 完全未使用:")
    for rt in sorted(unused_row_types):
        row_count = len(df[df['row_type'] == rt])
        print(f"  - {rt}: {row_count:,}行（完全未使用）")
else:
    print("\n全row_typeが使用されています")

# 使用回数が少ないrow_type
print("\n⚠️ 低使用率（使用回数1-2回）:")
for row_type, count in usage_counter.most_common():
    if count <= 2:
        row_count = len(df[df['row_type'] == row_type])
        print(f"  - {row_type}: {count}回使用、{row_count:,}行")

print()

# 各タブの推定（タブ名コメントから推測）
print("=" * 80)
print("タブ構造分析（推定）")
print("=" * 80)

# タブ関連のコメントやラベルを探す
tab_pattern = r'(?:タブ|Tab|概要|年齢|性別|ペルソナ|緊急度|希少|需給|競合|キャリア)'
tab_matches = re.findall(tab_pattern, content)

print(f"\n見つかったタブ関連キーワード: {len(tab_matches)}個")
print(f"  - {', '.join(set(tab_matches))}")

print("\n" + "=" * 80)
print("分析完了")
print("=" * 80)
