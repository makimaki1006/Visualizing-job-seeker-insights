# -*- coding: utf-8 -*-
"""DB 正しいキーでの重複確認"""
import db_helper

print("=== DB 正しいキーでの重複確認 ===")
print()

# WORKSTYLE_DISTRIBUTION: prefecture + municipality + category1
print("--- WORKSTYLE_DISTRIBUTION (pref+muni+category1) ---")
sql1 = """
SELECT job_type,
       COUNT(*) as total,
       COUNT(DISTINCT prefecture || '/' || municipality || '/' || category1) as unique_keys
FROM job_seeker_data
WHERE row_type = 'WORKSTYLE_DISTRIBUTION'
GROUP BY job_type
ORDER BY job_type
"""
df1 = db_helper.query_df(sql1)
if len(df1) > 0:
    df1['total'] = df1['total'].astype(int)
    df1['unique_keys'] = df1['unique_keys'].astype(int)
    df1['ratio'] = df1['total'] / df1['unique_keys']
    for _, row in df1.iterrows():
        status = 'DUP' if row['ratio'] > 1.1 else 'OK'
        print(f"  {status} {row['job_type']}: {row['total']}/{row['unique_keys']} = {row['ratio']:.2f}")
print()

# AGE_GENDER: prefecture + municipality + category1 + category2
print("--- AGE_GENDER (pref+muni+cat1+cat2) ---")
sql2 = """
SELECT job_type,
       COUNT(*) as total,
       COUNT(DISTINCT prefecture || '/' || municipality || '/' || COALESCE(category1,'') || '/' || COALESCE(category2,'')) as unique_keys
FROM job_seeker_data
WHERE row_type = 'AGE_GENDER'
GROUP BY job_type
ORDER BY job_type
"""
df2 = db_helper.query_df(sql2)
if len(df2) > 0:
    df2['total'] = df2['total'].astype(int)
    df2['unique_keys'] = df2['unique_keys'].astype(int)
    df2['ratio'] = df2['total'] / df2['unique_keys']
    for _, row in df2.iterrows():
        status = 'DUP' if row['ratio'] > 1.1 else 'OK'
        print(f"  {status} {row['job_type']}: {row['total']}/{row['unique_keys']} = {row['ratio']:.2f}")
print()

# SUMMARY: prefecture + municipality
print("--- SUMMARY (pref+muni) ---")
sql3 = """
SELECT job_type,
       COUNT(*) as total,
       COUNT(DISTINCT prefecture || '/' || municipality) as unique_keys
FROM job_seeker_data
WHERE row_type = 'SUMMARY'
GROUP BY job_type
ORDER BY job_type
"""
df3 = db_helper.query_df(sql3)
if len(df3) > 0:
    df3['total'] = df3['total'].astype(int)
    df3['unique_keys'] = df3['unique_keys'].astype(int)
    df3['ratio'] = df3['total'] / df3['unique_keys']
    for _, row in df3.iterrows():
        status = 'DUP' if row['ratio'] > 1.1 else 'OK'
        print(f"  {status} {row['job_type']}: {row['total']}/{row['unique_keys']} = {row['ratio']:.2f}")

print()
print("=== 確認完了 ===")
