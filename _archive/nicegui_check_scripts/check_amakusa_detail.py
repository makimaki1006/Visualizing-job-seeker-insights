# -*- coding: utf-8 -*-
"""天草市の看護師データを詳細確認"""
import db_helper

print("=== 天草市 看護師 全データ確認 ===")
print()

# 1. 全row_typeの天草市データ
sql1 = """
SELECT row_type, COUNT(*) as cnt
FROM job_seeker_data
WHERE job_type = '看護師' AND municipality = '天草市'
GROUP BY row_type
ORDER BY cnt DESC
"""

df1 = db_helper.query_df(sql1)
print("天草市・看護師のrow_type別行数:")
print(df1.to_string())
print()

# 2. SUMMARYの詳細
sql2 = """
SELECT id, prefecture, municipality, applicant_count, latitude, longitude
FROM job_seeker_data
WHERE job_type = '看護師' AND municipality = '天草市' AND row_type = 'SUMMARY'
"""

df2 = db_helper.query_df(sql2)
print("天草市・看護師・SUMMARYの全行:")
print(df2.to_string())
print()

# 3. 熊本県の他の市区町村でSUMMARY重複があるか
sql3 = """
SELECT municipality, COUNT(*) as cnt
FROM job_seeker_data
WHERE job_type = '看護師' AND prefecture = '熊本県' AND row_type = 'SUMMARY'
GROUP BY municipality
HAVING COUNT(*) > 1
"""

df3 = db_helper.query_df(sql3)
print("熊本県・看護師でSUMMARY重複がある市区町村:")
if len(df3) > 0:
    print(df3.to_string())
else:
    print("  なし")
print()

# 4. 天草市の全職種SUMMARY
sql4 = """
SELECT job_type, COUNT(*) as cnt, SUM(applicant_count) as total_applicants
FROM job_seeker_data
WHERE municipality = '天草市' AND row_type = 'SUMMARY'
GROUP BY job_type
"""

df4 = db_helper.query_df(sql4)
print("天草市・全職種のSUMMARY:")
print(df4.to_string())

print()
print("=== 確認完了 ===")
