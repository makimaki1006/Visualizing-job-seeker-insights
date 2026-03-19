# -*- coding: utf-8 -*-
"""DB 全職種 WORKSTYLE_DISTRIBUTION 重複確認"""
import db_helper

print("=== DB 全職種 WORKSTYLE_DISTRIBUTION 重複確認 ===")
print()

# 職種別の重複状況
sql = """
SELECT
    job_type,
    COUNT(*) as total_rows,
    COUNT(DISTINCT prefecture || '/' || municipality || '/' || category1) as unique_keys
FROM job_seeker_data
WHERE row_type = 'WORKSTYLE_DISTRIBUTION'
GROUP BY job_type
ORDER BY job_type
"""

df = db_helper.query_df(sql)
df['total_rows'] = df['total_rows'].astype(int)
df['unique_keys'] = df['unique_keys'].astype(int)
df['dup_ratio'] = df['total_rows'] / df['unique_keys']
print(df.to_string())
print()

# 重複の具体例
sql2 = """
SELECT job_type, prefecture, municipality, category1, COUNT(*) as cnt
FROM job_seeker_data
WHERE row_type = 'WORKSTYLE_DISTRIBUTION'
GROUP BY job_type, prefecture, municipality, category1
HAVING COUNT(*) > 1
LIMIT 20
"""

df2 = db_helper.query_df(sql2)
print("重複例（上位20件）:")
print(df2.to_string())

print()
print("=== 確認完了 ===")
