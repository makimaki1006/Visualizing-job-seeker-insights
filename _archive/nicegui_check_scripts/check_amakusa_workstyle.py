# -*- coding: utf-8 -*-
"""天草市の看護師 雇用形態データを詳細確認"""
import db_helper

print("=== 天草市 看護師 雇用形態データ確認 ===")
print()

# 1. WORKSTYLE_DISTRIBUTION の全データ
sql1 = """
SELECT id, prefecture, municipality, category1, count, total_applicants, percentage
FROM job_seeker_data
WHERE job_type = '看護師'
  AND municipality = '天草市'
  AND row_type = 'WORKSTYLE_DISTRIBUTION'
ORDER BY count DESC
"""

df1 = db_helper.query_df(sql1)
print("WORKSTYLE_DISTRIBUTION (雇用形態分布):")
print(df1.to_string())
print()

# 2. 重複チェック
sql2 = """
SELECT category1, COUNT(*) as row_count, SUM(count) as total_count
FROM job_seeker_data
WHERE job_type = '看護師'
  AND municipality = '天草市'
  AND row_type = 'WORKSTYLE_DISTRIBUTION'
GROUP BY category1
ORDER BY total_count DESC
"""

df2 = db_helper.query_df(sql2)
print("category1別の集計:")
print(df2.to_string())
print()

# 3. 他の市区町村と比較（正常なデータとの比較）
sql3 = """
SELECT municipality, category1, count, total_applicants
FROM job_seeker_data
WHERE job_type = '看護師'
  AND prefecture = '熊本県'
  AND row_type = 'WORKSTYLE_DISTRIBUTION'
  AND category1 = '正職員'
ORDER BY count DESC
LIMIT 10
"""

df3 = db_helper.query_df(sql3)
print("熊本県の他の市区町村（正職員）と比較:")
print(df3.to_string())

print()
print("=== 確認完了 ===")
