# -*- coding: utf-8 -*-
import db_helper

sql = """SELECT row_type, COUNT(*) as cnt
FROM job_seeker_data
WHERE job_type='看護師' AND municipality='天草市'
GROUP BY row_type
ORDER BY cnt DESC"""

df = db_helper.query_df(sql)
print(df.to_string())
