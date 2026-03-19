# -*- coding: utf-8 -*-
"""DB 全職種の存在確認（軽量版）"""
import db_helper

print("=== DB 職種別 行数確認 ===")
print()

# 職種別の総行数のみ
sql1 = """
SELECT job_type, COUNT(*) as cnt
FROM job_seeker_data
GROUP BY job_type
ORDER BY job_type
"""

df1 = db_helper.query_df(sql1)
print("職種別総行数:")
print(df1.to_string())
print()

# WORKSTYLE_DISTRIBUTIONだけ確認
sql2 = """
SELECT job_type, COUNT(*) as cnt
FROM job_seeker_data
WHERE row_type = 'WORKSTYLE_DISTRIBUTION'
GROUP BY job_type
ORDER BY job_type
"""

df2 = db_helper.query_df(sql2)
print("WORKSTYLE_DISTRIBUTION行数:")
print(df2.to_string())

print()
print("=== 確認完了 ===")
