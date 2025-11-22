# -*- coding: utf-8 -*-
"""PERSONA_MUNI行数確認スクリプト"""
import pandas as pd
import sys
import io

# Windows環境での絵文字出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# CSV読み込み
df = pd.read_csv('data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv',
                 encoding='utf-8-sig', low_memory=False)

# PERSONA_MUNI行抽出
persona_muni = df[df['row_type'] == 'PERSONA_MUNI']

print(f"総行数: {len(df)}")
print(f"PERSONA_MUNI: {len(persona_muni)}行")
print()
print("Row type分布:")

rt_counts = df['row_type'].value_counts()
for rt, count in rt_counts.items():
    print(f"  {rt}: {count}行")
