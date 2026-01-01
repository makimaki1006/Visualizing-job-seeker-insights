# -*- coding: utf-8 -*-
"""
人材地図データ整合性検証スクリプト v4
詳細問題調査
"""

import os
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Windows用コンソール出力設定
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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
    with httpx.Client(timeout=60.0) as client:
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
            elif cell.get("type") == "float":
                row_dict[col_name] = cell.get("value")
            elif cell.get("type") == "null":
                row_dict[col_name] = None
            else:
                row_dict[col_name] = cell.get("value")
        parsed.append(row_dict)
    return parsed

def safe_int(val):
    if val is None:
        return 0
    try:
        return int(float(val))
    except:
        return 0

def main():
    print("=" * 70)
    print("  DETAILED ISSUE INVESTIGATION")
    print("=" * 70)

    # ========================================
    # 問題1: AGE_GENDER の category1/category2 の関係
    # ========================================
    print("\n[Issue 1] AGE_GENDER structure investigation:")
    print("  Checking category1 and category2 values...")

    sql = """
    SELECT category1, category2, COUNT(*) as cnt
    FROM job_seeker_data
    WHERE row_type = 'AGE_GENDER'
    GROUP BY category1, category2
    ORDER BY category1, category2
    """
    result = turso_query(sql)
    rows = parse_turso_response(result)

    print(f"\n  {'category1':<12} {'category2':<12} {'Count':>10}")
    print("  " + "-" * 40)
    for r in rows:
        c1 = r['category1'] if r['category1'] else "(null)"
        c2 = r['category2'] if r['category2'] else "(null)"
        cnt = safe_int(r['cnt'])
        print(f"  {c1:<12} {c2:<12} {cnt:>10}")

    print("\n  [Analysis] category1 contains age groups, category2 contains gender")

    # ========================================
    # 問題2: 性別カウント不整合の詳細
    # ========================================
    print("\n[Issue 2] SUMMARY gender count mismatch details:")

    sql = """
    SELECT
        prefecture,
        municipality,
        CAST(applicant_count AS INTEGER) as applicant_count,
        CAST(male_count AS INTEGER) as male_count,
        CAST(female_count AS INTEGER) as female_count,
        CAST(male_count AS INTEGER) + CAST(female_count AS INTEGER) as sum_gender,
        CAST(applicant_count AS INTEGER) - (CAST(male_count AS INTEGER) + CAST(female_count AS INTEGER)) as diff
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND CAST(male_count AS INTEGER) + CAST(female_count AS INTEGER) != CAST(applicant_count AS INTEGER)
    ORDER BY diff DESC
    LIMIT 15
    """
    result = turso_query(sql)
    mismatches = parse_turso_response(result)

    if mismatches:
        print(f"\n  {'Prefecture':<12} {'Municipality':<15} {'Applicant':>10} {'Male':>8} {'Female':>8} {'Sum':>8} {'Diff':>6}")
        print("  " + "-" * 75)
        for m in mismatches:
            pref = m['prefecture'] if m['prefecture'] else "(null)"
            muni = m['municipality'] if m['municipality'] else "(null)"
            app = safe_int(m['applicant_count'])
            male = safe_int(m['male_count'])
            female = safe_int(m['female_count'])
            sum_g = safe_int(m['sum_gender'])
            diff = safe_int(m['diff'])
            print(f"  {pref:<12} {muni:<15} {app:>10} {male:>8} {female:>8} {sum_g:>8} {diff:>6}")

        # この差分は「不明」性別か？
        print("\n  [Analysis] The difference likely represents 'unknown/unspecified' gender")
    else:
        print("  No mismatches found")

    # ========================================
    # 問題3: municipality=NULL のレコード詳細
    # ========================================
    print("\n[Issue 3] NULL municipality records in SUMMARY:")

    sql = """
    SELECT prefecture, municipality, CAST(applicant_count AS INTEGER) as applicant_count
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND municipality IS NULL
    ORDER BY applicant_count DESC
    LIMIT 10
    """
    result = turso_query(sql)
    null_muni = parse_turso_response(result)

    if null_muni:
        print(f"  Found {len(null_muni)} SUMMARY records with NULL municipality (showing top 10)")
        for m in null_muni:
            pref = m['prefecture'] if m['prefecture'] else "(null)"
            app = safe_int(m['applicant_count'])
            print(f"    - {pref}: {app:,} applicants")
    else:
        print("  No NULL municipality in SUMMARY")

    # ========================================
    # 問題4: AGE_GENDERでの「不明」年齢/性別
    # ========================================
    print("\n[Issue 4] 'Unknown' values in AGE_GENDER:")

    sql = """
    SELECT prefecture, municipality, category1, category2, CAST(count AS INTEGER) as cnt
    FROM job_seeker_data
    WHERE row_type = 'AGE_GENDER'
      AND (category1 = '不明' OR category2 = '不明')
    LIMIT 20
    """
    result = turso_query(sql)
    unknown = parse_turso_response(result)

    if unknown:
        print(f"  Found records with 'unknown' category (showing max 20):")
        for u in unknown:
            pref = u['prefecture'] if u['prefecture'] else "(null)"
            muni = u['municipality'] if u['municipality'] else "(null)"
            c1 = u['category1'] if u['category1'] else "(null)"
            c2 = u['category2'] if u['category2'] else "(null)"
            cnt = safe_int(u['cnt'])
            print(f"    - {pref} {muni}: {c1}/{c2} = {cnt}")
    else:
        print("  No 'unknown' values found")

    # ========================================
    # 問題5: 各都道府県の市区町村数確認
    # ========================================
    print("\n[Issue 5] Municipality count per prefecture (SUMMARY):")

    sql = """
    SELECT prefecture, COUNT(*) as muni_count
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND municipality IS NOT NULL
      AND municipality != ''
    GROUP BY prefecture
    ORDER BY muni_count DESC
    LIMIT 10
    """
    result = turso_query(sql)
    pref_counts = parse_turso_response(result)

    print("\n  Top 10 prefectures by municipality count:")
    for p in pref_counts:
        pref = p['prefecture'] if p['prefecture'] else "(null)"
        cnt = safe_int(p['muni_count'])
        print(f"    - {pref}: {cnt} municipalities")

    # 最少も表示
    sql2 = """
    SELECT prefecture, COUNT(*) as muni_count
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND municipality IS NOT NULL
      AND municipality != ''
    GROUP BY prefecture
    ORDER BY muni_count ASC
    LIMIT 5
    """
    result2 = turso_query(sql2)
    pref_counts2 = parse_turso_response(result2)

    print("\n  Bottom 5 prefectures by municipality count:")
    for p in pref_counts2:
        pref = p['prefecture'] if p['prefecture'] else "(null)"
        cnt = safe_int(p['muni_count'])
        print(f"    - {pref}: {cnt} municipalities")

    # ========================================
    # 問題6: AGE_GENDER と AGE_GENDER_RESIDENCE の関係
    # ========================================
    print("\n[Issue 6] AGE_GENDER vs AGE_GENDER_RESIDENCE comparison:")

    sql = """
    SELECT
        'AGE_GENDER' as row_type,
        COUNT(DISTINCT prefecture || '/' || municipality) as unique_locations,
        COUNT(*) as total_rows
    FROM job_seeker_data
    WHERE row_type = 'AGE_GENDER'
    UNION ALL
    SELECT
        'AGE_GENDER_RESIDENCE' as row_type,
        COUNT(DISTINCT prefecture || '/' || municipality) as unique_locations,
        COUNT(*) as total_rows
    FROM job_seeker_data
    WHERE row_type = 'AGE_GENDER_RESIDENCE'
    """
    result = turso_query(sql)
    comparison = parse_turso_response(result)

    print(f"\n  {'row_type':<25} {'Unique Locations':>20} {'Total Rows':>15}")
    print("  " + "-" * 60)
    for c in comparison:
        rt = c['row_type']
        locs = safe_int(c['unique_locations'])
        rows = safe_int(c['total_rows'])
        print(f"  {rt:<25} {locs:>20} {rows:>15}")

    # ========================================
    # 完了
    # ========================================
    print("\n" + "=" * 70)
    print("  INVESTIGATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
