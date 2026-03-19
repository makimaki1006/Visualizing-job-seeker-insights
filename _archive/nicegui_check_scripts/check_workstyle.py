#!/usr/bin/env python3
"""WORKSTYLEデータの状態確認"""
import os
from dotenv import load_dotenv
import urllib.request
import json

load_dotenv()
url = os.getenv('TURSO_DATABASE_URL', '').replace('libsql://', 'https://')
token = os.getenv('TURSO_AUTH_TOKEN', '')

sql = """
SELECT row_type, job_type, COUNT(*) as cnt
FROM job_seeker_data
WHERE row_type LIKE 'WORKSTYLE%'
GROUP BY row_type, job_type
ORDER BY row_type, job_type
"""

req = urllib.request.Request(
    f'{url}/v2/pipeline',
    data=json.dumps({'requests': [{'type': 'execute', 'stmt': {'sql': sql}}]}).encode(),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=60)
result = json.loads(resp.read().decode())

print('WORKSTYLE data by row_type and job_type:')
print('-' * 60)
try:
    rows = result['results'][0]['response']['result']['rows']
    for row in rows:
        rt = row[0].get('value', 'NULL') if isinstance(row[0], dict) else row[0]
        jt = row[1].get('value', 'NULL') if isinstance(row[1], dict) else row[1]
        cnt = int(row[2].get('value', 0) if isinstance(row[2], dict) else row[2])
        print(f'  {rt:40} | {jt:15} | {cnt:,}')
except Exception as e:
    print(f'Error: {e}')
    print(f'Result: {json.dumps(result, indent=2)[:1000]}')
