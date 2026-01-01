#!/usr/bin/env python3
"""Check category values in database"""

from db_helper import query_df

# row_typeごとのcategory1, category2の値を確認
df = query_df('''
    SELECT row_type, category1, category2, COUNT(*) as cnt
    FROM job_seeker_data
    GROUP BY row_type, category1, category2
    ORDER BY row_type, cnt DESC
    LIMIT 100
''')

print('=== row_type別 category1/category2 の値 ===')
current_type = None
for _, row in df.iterrows():
    if current_type != row['row_type']:
        current_type = row['row_type']
        print(f'\n【{current_type}】')
    print(f"  {row['category1']} | {row['category2']} ({row['cnt']}件)")
