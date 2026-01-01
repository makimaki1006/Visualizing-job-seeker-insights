# -*- coding: utf-8 -*-
"""
人材地図データ整合性検証スクリプト v3
UTF-8対応版 + 詳細整合性検証
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
    """安全にint変換"""
    if val is None:
        return 0
    try:
        return int(float(val))
    except:
        return 0

def safe_float(val):
    """安全にfloat変換"""
    if val is None:
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

def main():
    print("=" * 70)
    print("  DATA INTEGRITY VERIFICATION v3")
    print("=" * 70)

    # ========================================
    # 1. row_type 分布の確認
    # ========================================
    print("\n[1] row_type distribution:")
    sql = "SELECT row_type, COUNT(*) as cnt FROM job_seeker_data GROUP BY row_type ORDER BY cnt DESC"
    result = turso_query(sql)
    row_types = parse_turso_response(result)
    for rt in row_types:
        cnt = safe_int(rt['cnt'])
        print(f"  - {rt['row_type']}: {cnt:,}")

    # ========================================
    # 2. 都道府県の確認（47都道府県すべて存在するか）
    # ========================================
    print("\n[2] Prefecture check (47 prefectures):")
    sql = """
    SELECT DISTINCT prefecture
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
    ORDER BY prefecture
    """
    result = turso_query(sql)
    prefs = parse_turso_response(result)
    pref_list = [p['prefecture'] for p in prefs]
    print(f"  Found {len(pref_list)} unique prefectures in SUMMARY")

    # 47都道府県リスト
    ALL_PREFS = [
        '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
        '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
        '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
        '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
        '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
        '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
        '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
    ]

    missing = [p for p in ALL_PREFS if p not in pref_list]
    if missing:
        print(f"  [WARNING] Missing prefectures: {missing}")
    else:
        print("  [OK] All 47 prefectures exist in SUMMARY")

    # 追加の都道府県（想定外）
    extra = [p for p in pref_list if p not in ALL_PREFS and p]
    if extra:
        print(f"  [INFO] Extra prefectures found: {extra}")

    # ========================================
    # 3. SUMMARY と AGE_GENDER の整合性検証
    # ========================================
    print("\n[3] SUMMARY vs AGE_GENDER consistency check:")

    # 全体の整合性をCTEで確認
    sql = """
    WITH summary_data AS (
        SELECT
            prefecture,
            municipality,
            CAST(applicant_count AS INTEGER) as summary_count,
            CAST(male_count AS INTEGER) as summary_male,
            CAST(female_count AS INTEGER) as summary_female
        FROM job_seeker_data
        WHERE row_type = 'SUMMARY'
          AND municipality IS NOT NULL
          AND municipality != ''
    ),
    age_gender_agg AS (
        SELECT
            prefecture,
            municipality,
            SUM(CAST(count AS INTEGER)) as ag_total,
            SUM(CASE WHEN category1 = '男性' THEN CAST(count AS INTEGER) ELSE 0 END) as ag_male,
            SUM(CASE WHEN category1 = '女性' THEN CAST(count AS INTEGER) ELSE 0 END) as ag_female
        FROM job_seeker_data
        WHERE row_type = 'AGE_GENDER'
          AND municipality IS NOT NULL
          AND municipality != ''
        GROUP BY prefecture, municipality
    )
    SELECT
        COUNT(*) as total_municipalities,
        SUM(CASE WHEN s.summary_count = COALESCE(a.ag_total, 0) THEN 1 ELSE 0 END) as exact_match,
        SUM(CASE WHEN s.summary_count != COALESCE(a.ag_total, 0) THEN 1 ELSE 0 END) as mismatch,
        SUM(CASE WHEN a.ag_total IS NULL THEN 1 ELSE 0 END) as missing_age_gender
    FROM summary_data s
    LEFT JOIN age_gender_agg a ON s.prefecture = a.prefecture AND s.municipality = a.municipality
    """
    result = turso_query(sql)
    stats = parse_turso_response(result)
    if stats:
        s = stats[0]
        print(f"  Total municipalities in SUMMARY: {safe_int(s['total_municipalities'])}")
        print(f"  Exact match (SUMMARY == AGE_GENDER sum): {safe_int(s['exact_match'])}")
        print(f"  Mismatch: {safe_int(s['mismatch'])}")
        print(f"  Missing AGE_GENDER data: {safe_int(s['missing_age_gender'])}")

        mismatch_cnt = safe_int(s['mismatch'])
        if mismatch_cnt > 0:
            print(f"\n  [WARNING] {mismatch_cnt} municipalities have data mismatch!")

            # 不整合の詳細を表示
            sql2 = """
            WITH summary_data AS (
                SELECT
                    prefecture,
                    municipality,
                    CAST(applicant_count AS INTEGER) as summary_count
                FROM job_seeker_data
                WHERE row_type = 'SUMMARY'
                  AND municipality IS NOT NULL
                  AND municipality != ''
            ),
            age_gender_agg AS (
                SELECT
                    prefecture,
                    municipality,
                    SUM(CAST(count AS INTEGER)) as ag_total
                FROM job_seeker_data
                WHERE row_type = 'AGE_GENDER'
                  AND municipality IS NOT NULL
                  AND municipality != ''
                GROUP BY prefecture, municipality
            )
            SELECT
                s.prefecture,
                s.municipality,
                s.summary_count,
                COALESCE(a.ag_total, 0) as ag_total,
                s.summary_count - COALESCE(a.ag_total, 0) as diff
            FROM summary_data s
            LEFT JOIN age_gender_agg a ON s.prefecture = a.prefecture AND s.municipality = a.municipality
            WHERE s.summary_count != COALESCE(a.ag_total, 0)
            ORDER BY ABS(s.summary_count - COALESCE(a.ag_total, 0)) DESC
            LIMIT 15
            """
            result2 = turso_query(sql2)
            mismatches = parse_turso_response(result2)
            print("\n  Top 15 mismatches (by absolute difference):")
            print(f"  {'Prefecture':<12} {'Municipality':<15} {'SUMMARY':>10} {'AGE_GENDER':>12} {'Diff':>8}")
            print("  " + "-" * 60)
            for m in mismatches:
                pref = m['prefecture'] if m['prefecture'] else "(null)"
                muni = m['municipality'] if m['municipality'] else "(null)"
                sc = safe_int(m['summary_count'])
                ag = safe_int(m['ag_total'])
                diff = safe_int(m['diff'])
                print(f"  {pref:<12} {muni:<15} {sc:>10} {ag:>12} {diff:>8}")
        else:
            print("\n  [OK] All municipalities have consistent data!")

    # ========================================
    # 4. AGE_GENDER の年齢層定義確認
    # ========================================
    print("\n[4] Age group definitions in AGE_GENDER:")
    sql = """
    SELECT category2 as age_group, COUNT(*) as cnt
    FROM job_seeker_data
    WHERE row_type = 'AGE_GENDER'
      AND category2 IS NOT NULL
    GROUP BY category2
    ORDER BY category2
    """
    result = turso_query(sql)
    age_groups = parse_turso_response(result)

    expected_ages = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
    actual_ages = [a['age_group'] for a in age_groups]

    for ag in age_groups:
        cnt = safe_int(ag['cnt'])
        status = "OK" if ag['age_group'] in expected_ages else "EXTRA"
        print(f"  - {ag['age_group']}: {cnt:,} ({status})")

    missing_ages = [a for a in expected_ages if a not in actual_ages]
    if missing_ages:
        print(f"\n  [WARNING] Missing age groups: {missing_ages}")
    else:
        print("\n  [OK] All expected age groups exist")

    # ========================================
    # 5. 性別データの欠損パターン
    # ========================================
    print("\n[5] Gender data in AGE_GENDER:")
    sql = """
    SELECT
        category1 as gender,
        COUNT(*) as cnt
    FROM job_seeker_data
    WHERE row_type = 'AGE_GENDER'
    GROUP BY category1
    ORDER BY category1
    """
    result = turso_query(sql)
    genders = parse_turso_response(result)

    for g in genders:
        label = g['gender'] if g['gender'] else "(NULL/empty)"
        cnt = safe_int(g['cnt'])
        print(f"  - {label}: {cnt:,}")

    # NULL/空の性別がある場合は警告
    null_gender = [g for g in genders if not g['gender']]
    if null_gender:
        print("\n  [WARNING] Records with NULL/empty gender exist")

    # ========================================
    # 6. municipality NULL/空 の分布
    # ========================================
    print("\n[6] Municipality NULL/empty distribution:")
    sql = """
    SELECT
        row_type,
        COUNT(*) as total,
        SUM(CASE WHEN municipality IS NULL THEN 1 ELSE 0 END) as null_cnt,
        SUM(CASE WHEN municipality = '' THEN 1 ELSE 0 END) as empty_cnt
    FROM job_seeker_data
    GROUP BY row_type
    HAVING null_cnt > 0 OR empty_cnt > 0
    ORDER BY null_cnt DESC
    """
    result = turso_query(sql)
    null_stats = parse_turso_response(result)

    if null_stats:
        print(f"  {'row_type':<30} {'Total':>10} {'NULL':>10} {'Empty':>10}")
        print("  " + "-" * 60)
        for s in null_stats:
            rt = s['row_type'] if s['row_type'] else "(null)"
            total = safe_int(s['total'])
            null_cnt = safe_int(s['null_cnt'])
            empty_cnt = safe_int(s['empty_cnt'])
            print(f"  {rt:<30} {total:>10} {null_cnt:>10} {empty_cnt:>10}")
    else:
        print("  [OK] No NULL/empty municipality values")

    # ========================================
    # 7. サンプル整合性チェック（5都道府県の主要市区町村）
    # ========================================
    print("\n[7] Sample integrity check (specific municipalities):")

    # 東京都の市区町村をサンプル
    sql = """
    SELECT prefecture, municipality
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND prefecture LIKE '%東京%'
      AND municipality IS NOT NULL
      AND municipality != ''
    ORDER BY applicant_count DESC
    LIMIT 5
    """
    result = turso_query(sql)
    tokyo_samples = parse_turso_response(result)

    # 大阪府の市区町村
    sql = """
    SELECT prefecture, municipality
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND prefecture LIKE '%大阪%'
      AND municipality IS NOT NULL
      AND municipality != ''
    ORDER BY applicant_count DESC
    LIMIT 5
    """
    result = turso_query(sql)
    osaka_samples = parse_turso_response(result)

    samples = tokyo_samples + osaka_samples

    print(f"\n  Checking {len(samples)} municipalities...")
    print(f"  {'Prefecture':<12} {'Municipality':<15} {'SUMMARY':>10} {'AGE_GENDER':>12} {'Match':>8}")
    print("  " + "-" * 60)

    all_match = True
    for s in samples:
        pref = s['prefecture']
        muni = s['municipality']

        # SUMMARY
        sql_s = f"""
        SELECT CAST(applicant_count AS INTEGER) as cnt
        FROM job_seeker_data
        WHERE row_type = 'SUMMARY'
          AND prefecture = '{pref}'
          AND municipality = '{muni}'
        """
        result_s = turso_query(sql_s)
        summary_rows = parse_turso_response(result_s)
        summary_cnt = safe_int(summary_rows[0]['cnt']) if summary_rows else 0

        # AGE_GENDER合計
        sql_ag = f"""
        SELECT SUM(CAST(count AS INTEGER)) as total
        FROM job_seeker_data
        WHERE row_type = 'AGE_GENDER'
          AND prefecture = '{pref}'
          AND municipality = '{muni}'
        """
        result_ag = turso_query(sql_ag)
        ag_rows = parse_turso_response(result_ag)
        ag_total = safe_int(ag_rows[0]['total']) if ag_rows and ag_rows[0]['total'] else 0

        match = "OK" if summary_cnt == ag_total else "NG"
        if match == "NG":
            all_match = False

        print(f"  {pref:<12} {muni:<15} {summary_cnt:>10} {ag_total:>12} {match:>8}")

    if all_match:
        print("\n  [OK] All sampled municipalities have consistent data")
    else:
        print("\n  [WARNING] Some municipalities have inconsistent data")

    # ========================================
    # 8. SUMMARYの male_count + female_count = applicant_count 確認
    # ========================================
    print("\n[8] SUMMARY male_count + female_count vs applicant_count:")
    sql = """
    SELECT
        COUNT(*) as total,
        SUM(CASE
            WHEN CAST(male_count AS INTEGER) + CAST(female_count AS INTEGER) = CAST(applicant_count AS INTEGER)
            THEN 1 ELSE 0 END) as match_cnt,
        SUM(CASE
            WHEN CAST(male_count AS INTEGER) + CAST(female_count AS INTEGER) != CAST(applicant_count AS INTEGER)
            THEN 1 ELSE 0 END) as mismatch_cnt
    FROM job_seeker_data
    WHERE row_type = 'SUMMARY'
      AND male_count IS NOT NULL
      AND female_count IS NOT NULL
    """
    result = turso_query(sql)
    gender_stats = parse_turso_response(result)
    if gender_stats:
        s = gender_stats[0]
        print(f"  Total SUMMARY rows with gender data: {safe_int(s['total'])}")
        print(f"  male + female = applicant_count: {safe_int(s['match_cnt'])}")
        print(f"  Mismatch: {safe_int(s['mismatch_cnt'])}")

        if safe_int(s['mismatch_cnt']) > 0:
            print("\n  [WARNING] Some SUMMARY rows have gender count mismatch!")
        else:
            print("\n  [OK] All SUMMARY rows have consistent gender counts")

    # ========================================
    # 完了
    # ========================================
    print("\n" + "=" * 70)
    print("  VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
