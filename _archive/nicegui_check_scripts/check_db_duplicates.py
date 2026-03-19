# -*- coding: utf-8 -*-
"""DBの重複状態を確認するスクリプト

Claude.md遵守: DBへの書き込みは行わない（SELECTのみ）
"""
import db_helper

print("=== DB SUMMARY重複確認 ===")
print()

# 1. 職種別SUMMARY重複
sql1 = """
SELECT
    job_type,
    COUNT(*) as summary_count,
    COUNT(DISTINCT prefecture || '/' || municipality) as unique_pref_muni,
    COUNT(DISTINCT municipality) as unique_muni
FROM job_seeker_data
WHERE row_type = 'SUMMARY'
GROUP BY job_type
ORDER BY job_type
"""

df1 = db_helper.query_df(sql1)
print("職種別SUMMARY行数:")
print(df1.to_string())
print()

# 2. 重複している市区町村の詳細（prefecture+municipality基準）
sql2 = """
SELECT job_type, prefecture, municipality, COUNT(*) as cnt
FROM job_seeker_data
WHERE row_type = 'SUMMARY'
GROUP BY job_type, prefecture, municipality
HAVING COUNT(*) > 1
ORDER BY cnt DESC
LIMIT 30
"""

df2 = db_helper.query_df(sql2)
print("重複SUMMARY（prefecture+municipality基準）:")
if len(df2) > 0:
    print(df2.to_string())
else:
    print("  重複なし")
print()

# 3. municipalityのみで重複（同名異市の検出）
sql3 = """
SELECT job_type, municipality, COUNT(DISTINCT prefecture) as pref_count, COUNT(*) as total_rows
FROM job_seeker_data
WHERE row_type = 'SUMMARY'
GROUP BY job_type, municipality
HAVING COUNT(DISTINCT prefecture) > 1
LIMIT 20
"""

df3 = db_helper.query_df(sql3)
print("同名異市（同じmunicipality名で複数都道府県）:")
if len(df3) > 0:
    print(df3.to_string())
else:
    print("  なし")
print()

# 4. 特定市区町村の詳細（伊達市、府中市）
sql4 = """
SELECT job_type, prefecture, municipality, applicant_count
FROM job_seeker_data
WHERE row_type = 'SUMMARY'
  AND (municipality = '伊達市' OR municipality = '府中市')
ORDER BY municipality, prefecture
"""

df4 = db_helper.query_df(sql4)
print("伊達市・府中市の詳細:")
if len(df4) > 0:
    print(df4.to_string())
else:
    print("  データなし")

print()
print("=== 確認完了 ===")
