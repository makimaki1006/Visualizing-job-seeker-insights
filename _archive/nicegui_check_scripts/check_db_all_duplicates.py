# -*- coding: utf-8 -*-
"""DB 全職種×主要row_type 重複確認"""
import db_helper

print("=== DB 全職種 重複確認 ===")
print()

# 主要row_type（UIで使用されるもの）
row_types = [
    'SUMMARY',
    'AGE_GENDER',
    'WORKSTYLE_DISTRIBUTION',
    'PERSONA_MUNI',
    'GAP',
    'COMPETITION',
    'FLOW',
]

for rt in row_types:
    print(f"--- {rt} ---")

    sql = f"""
    SELECT job_type,
           COUNT(*) as total,
           COUNT(DISTINCT prefecture || '/' || municipality) as unique_keys
    FROM job_seeker_data
    WHERE row_type = '{rt}'
    GROUP BY job_type
    ORDER BY job_type
    """

    df = db_helper.query_df(sql)
    if len(df) == 0:
        print("  データなし")
        continue

    df['total'] = df['total'].astype(int)
    df['unique_keys'] = df['unique_keys'].astype(int)
    df['ratio'] = df['total'] / df['unique_keys']
    df['status'] = df['ratio'].apply(lambda x: 'DUP' if x > 1.1 else 'OK')

    for _, row in df.iterrows():
        print(f"  {row['status']} {row['job_type']}: {row['total']}/{row['unique_keys']} = {row['ratio']:.2f}")

    print()

print("=== 確認完了 ===")
