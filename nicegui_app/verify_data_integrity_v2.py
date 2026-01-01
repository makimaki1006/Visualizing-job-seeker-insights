# -*- coding: utf-8 -*-
"""
人材地図データ整合性検証スクリプト v2

テーブル構造を確認して適切に検証する
"""

import os
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

# .envを読み込む
load_dotenv(Path(__file__).parent / ".env")

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

def turso_query(sql: str) -> dict:
    """Turso HTTP APIでSQLを実行"""
    url = TURSO_DATABASE_URL.replace("libsql://", "https://")

    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "requests": [
            {"type": "execute", "stmt": {"sql": sql}},
            {"type": "close"}
        ]
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{url}/v2/pipeline", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

def parse_turso_response(result: dict) -> list:
    """Tursoレスポンスをリスト形式に変換"""
    if "results" not in result or len(result["results"]) == 0:
        return []

    response_data = result["results"][0].get("response", {})
    result_data = response_data.get("result", {})
    cols = result_data.get("cols", [])
    rows = result_data.get("rows", [])

    parsed = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(cols):
            col_name = col.get("name", f"col{i}")
            cell = row[i]
            if cell.get("type") == "integer":
                row_dict[col_name] = cell.get("value")
            elif cell.get("type") == "text":
                row_dict[col_name] = cell.get("value")
            elif cell.get("type") == "null":
                row_dict[col_name] = None
            else:
                row_dict[col_name] = cell.get("value")
        parsed.append(row_dict)

    return parsed

def main():
    print("=" * 70)
    print("  DATA INTEGRITY VERIFICATION")
    print("=" * 70)

    # 1. テーブル一覧を取得
    print("\n[1] Table list:")
    sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    result = turso_query(sql)
    tables = parse_turso_response(result)
    for t in tables:
        print(f"  - {t['name']}")

    # 2. job_seeker_dataテーブルのカラム構造を確認
    print("\n[2] job_seeker_data table structure:")
    sql = "PRAGMA table_info(job_seeker_data)"
    result = turso_query(sql)
    columns = parse_turso_response(result)
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")

    col_names = [c['name'] for c in columns]

    # 3. row_type カラムがあるか確認
    if 'row_type' in col_names:
        print("\n[3] row_type distribution:")
        sql = "SELECT row_type, COUNT(*) as cnt FROM job_seeker_data GROUP BY row_type ORDER BY cnt DESC"
        result = turso_query(sql)
        row_types = parse_turso_response(result)
        for rt in row_types:
            cnt_val = int(rt['cnt']) if rt['cnt'] else 0
            print(f"  - {rt['row_type']}: {cnt_val:,} rows")
    else:
        print("\n[3] row_type column not found. Checking total rows:")
        sql = "SELECT COUNT(*) as cnt FROM job_seeker_data"
        result = turso_query(sql)
        total = parse_turso_response(result)
        print(f"  Total rows: {total[0]['cnt']:,}")

    # 4. 都道府県カラムを確認
    pref_col = None
    for c in ['prefecture', 'pref', 'desired_prefecture']:
        if c in col_names:
            pref_col = c
            break

    if pref_col:
        print(f"\n[4] Prefecture column: {pref_col}")
        sql = f"SELECT DISTINCT {pref_col} as pref FROM job_seeker_data WHERE {pref_col} IS NOT NULL ORDER BY {pref_col}"
        result = turso_query(sql)
        prefs = parse_turso_response(result)
        print(f"  Unique prefectures: {len(prefs)}")
        if len(prefs) <= 50:
            for p in prefs:
                print(f"    - {p['pref']}")
    else:
        print("\n[4] Prefecture column not found in:", col_names)

    # 5. サンプルデータを取得
    print("\n[5] Sample data (first 5 rows):")
    sql = "SELECT * FROM job_seeker_data LIMIT 5"
    result = turso_query(sql)
    samples = parse_turso_response(result)
    for i, s in enumerate(samples):
        print(f"\n  Row {i+1}:")
        for k, v in s.items():
            val_str = str(v)[:50] if v else "(null)"
            print(f"    {k}: {val_str}")

    # 6. 市区町村カラムを確認
    muni_col = None
    for c in ['municipality', 'muni', 'desired_municipality', 'city']:
        if c in col_names:
            muni_col = c
            break

    if muni_col:
        print(f"\n[6] Municipality column: {muni_col}")
        sql = f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN {muni_col} IS NULL THEN 1 ELSE 0 END) as null_cnt,
            SUM(CASE WHEN {muni_col} = '' THEN 1 ELSE 0 END) as empty_cnt,
            SUM(CASE WHEN {muni_col} IS NOT NULL AND {muni_col} != '' THEN 1 ELSE 0 END) as valid_cnt
        FROM job_seeker_data
        """
        result = turso_query(sql)
        muni_stats = parse_turso_response(result)
        if muni_stats:
            s = muni_stats[0]
            print(f"  Total: {s['total']}")
            print(f"  NULL: {s['null_cnt']}")
            print(f"  Empty: {s['empty_cnt']}")
            print(f"  Valid: {s['valid_cnt']}")

    # 7. 年齢・性別カラムを確認
    age_col = None
    gender_col = None
    for c in ['age_group', 'age', 'age_range']:
        if c in col_names:
            age_col = c
            break
    for c in ['gender', 'sex']:
        if c in col_names:
            gender_col = c
            break

    if age_col:
        print(f"\n[7] Age column: {age_col}")
        sql = f"SELECT {age_col} as age, COUNT(*) as cnt FROM job_seeker_data WHERE {age_col} IS NOT NULL GROUP BY {age_col} ORDER BY {age_col}"
        result = turso_query(sql)
        ages = parse_turso_response(result)
        for a in ages:
            cnt_val = int(a['cnt']) if a['cnt'] else 0
            print(f"  - {a['age']}: {cnt_val:,}")

    if gender_col:
        print(f"\n[8] Gender column: {gender_col}")
        sql = f"SELECT {gender_col} as gender, COUNT(*) as cnt FROM job_seeker_data GROUP BY {gender_col}"
        result = turso_query(sql)
        genders = parse_turso_response(result)
        for g in genders:
            label = g['gender'] if g['gender'] else "(NULL)"
            cnt_val = int(g['cnt']) if g['cnt'] else 0
            print(f"  - {label}: {cnt_val:,}")

    # 8. applicant_countカラムを確認
    if 'applicant_count' in col_names:
        print(f"\n[9] applicant_count statistics:")
        sql = """
        SELECT
            SUM(CAST(applicant_count AS INTEGER)) as total_applicants,
            AVG(CAST(applicant_count AS REAL)) as avg_applicants,
            MAX(CAST(applicant_count AS INTEGER)) as max_applicants,
            MIN(CAST(applicant_count AS INTEGER)) as min_applicants
        FROM job_seeker_data
        WHERE applicant_count IS NOT NULL
        """
        result = turso_query(sql)
        stats = parse_turso_response(result)
        if stats:
            s = stats[0]
            print(f"  Total: {s['total_applicants']}")
            print(f"  Average: {s['avg_applicants']:.2f}")
            print(f"  Max: {s['max_applicants']}")
            print(f"  Min: {s['min_applicants']}")

    print("\n" + "=" * 70)
    print("  VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
