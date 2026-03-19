# -*- coding: utf-8 -*-
import db_helper

# 1. 天草市WORKSTYLE重複確認
sql1 = """SELECT category1, COUNT(*) as row_count, SUM(count) as total_count
FROM job_seeker_data
WHERE job_type = '看護師' AND municipality = '天草市' AND row_type = 'WORKSTYLE_DISTRIBUTION'
GROUP BY category1"""
df1 = db_helper.query_df(sql1)
print('=== 天草市 WORKSTYLE_DISTRIBUTION ===')
print(df1.to_string())

# 2. 看護師SUMMARY重複確認
sql2 = """SELECT municipality, COUNT(*) as dup_count
FROM job_seeker_data
WHERE job_type = '看護師' AND row_type = 'SUMMARY'
GROUP BY municipality HAVING COUNT(*) > 1 LIMIT 20"""
df2 = db_helper.query_df(sql2)
print('\n=== 看護師 SUMMARY重複 ===')
print(df2.to_string() if len(df2) > 0 else '重複なし')

# 3. 全職種SUMMARY確認
sql3 = """SELECT job_type, COUNT(*) as summary_count, COUNT(DISTINCT municipality) as unique_muni
FROM job_seeker_data WHERE row_type = 'SUMMARY' GROUP BY job_type"""
df3 = db_helper.query_df(sql3)
print('\n=== 全職種 SUMMARY ===')
print(df3.to_string())
