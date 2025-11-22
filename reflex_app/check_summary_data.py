# -*- coding: utf-8 -*-
import db_helper
import pandas as pd

df = db_helper.get_filtered_data('群馬県', '伊勢崎市')
summary = df[df['row_type'] == 'SUMMARY']

print('=== SUMMARY データ詳細 ===')
print(f'行数: {len(summary)}')

if len(summary) > 0:
    row = summary.iloc[0]
    print(f'\napplicant_count: {row["applicant_count"]}')
    print(f'avg_age: {row["avg_age"]}')
    print(f'male_count: {row["male_count"]}')
    print(f'female_count: {row["female_count"]}')
    print(f'female_ratio: {row["female_ratio"]}')
    print(f'male_ratio: {row["male_ratio"]}')

    print('\n=== 非NaNカラム一覧 ===')
    for col in summary.columns:
        val = row[col]
        if pd.notna(val) and val != '':
            print(f'{col}: {val}')
