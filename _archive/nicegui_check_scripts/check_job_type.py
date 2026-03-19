#!/usr/bin/env python3
"""全row_typeのjob_type状態確認"""
import os
from dotenv import load_dotenv
import urllib.request
import json

load_dotenv()
url = os.getenv('TURSO_DATABASE_URL', '').replace('libsql://', 'https://')
token = os.getenv('TURSO_AUTH_TOKEN', '')

sql = '''
SELECT row_type, job_type, COUNT(*) as cnt
FROM job_seeker_data
GROUP BY row_type, job_type
ORDER BY row_type, job_type
'''
req = urllib.request.Request(
    f'{url}/v2/pipeline',
    data=json.dumps({'requests': [{'type': 'execute', 'stmt': {'sql': sql}}]}).encode(),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=120)
result = json.loads(resp.read().decode())

print('Turso job_type status by row_type:')
print('-' * 70)
for row in result['results'][0]['response']['result']['rows']:
    rt = row[0].get('value', 'NULL') if isinstance(row[0], dict) else row[0]
    jt_obj = row[1]
    if isinstance(jt_obj, dict):
        jt = jt_obj.get('value', 'NULL') if jt_obj.get('type') != 'null' else 'NULL'
    else:
        jt = str(jt_obj) if jt_obj else 'NULL'
    cnt = int(row[2].get('value', 0) if isinstance(row[2], dict) else row[2])
    print(f'{rt:35} | job_type={jt:15} | {cnt:,}')
