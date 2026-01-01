# -*- coding: utf-8 -*-
"""
人材地図データ整合性検証スクリプト

検証項目:
1. SUMMARYのapplicant_countとAGE_GENDERの合計が一致するか
2. 全47都道府県でデータが存在するか
3. municipality=NULL/空のデータの扱いが適切か
4. 年齢層の定義が一貫しているか
5. 性別データの欠損パターン
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
    # URLをHTTPS形式に変換
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

def print_section(title: str):
    """セクションタイトルを出力"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    print("=" * 70)
    print("  人材地図データ整合性検証")
    print("=" * 70)
    print(f"\nTurso URL: {TURSO_DATABASE_URL[:50]}...")

    # ========================================
    # 検証1: テーブル構造の確認
    # ========================================
    print_section("1. テーブル構造の確認")

    sql = """
    SELECT name FROM sqlite_master
    WHERE type='table'
    ORDER BY name
    """
    result = turso_query(sql)
    tables = parse_turso_response(result)
    print("テーブル一覧:")
    for t in tables:
        print(f"  - {t['name']}")

    # ========================================
    # 検証2: 全47都道府県でデータが存在するか
    # ========================================
    print_section("2. 都道府県データの確認")

    sql = """
    SELECT DISTINCT prefecture
    FROM mapcomplete
    WHERE row_type = 'SUMMARY'
    ORDER BY prefecture
    """
    result = turso_query(sql)
    prefs = parse_turso_response(result)
    print(f"都道府県数: {len(prefs)}")

    if len(prefs) < 47:
        print("\n[警告] 47都道府県未満です")
        pref_names = [p['prefecture'] for p in prefs]
        all_prefs = [
            '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
            '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
            '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
            '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
        missing = [p for p in all_prefs if p not in pref_names]
        print(f"欠落している都道府県: {missing}")
    else:
        print("[OK] 47都道府県すべてのデータが存在します")

    # ========================================
    # 検証3: municipality=NULL/空のデータの扱い
    # ========================================
    print_section("3. 市区町村データの確認（NULL/空のパターン）")

    sql = """
    SELECT
        row_type,
        COUNT(*) as count,
        SUM(CASE WHEN municipality IS NULL THEN 1 ELSE 0 END) as null_count,
        SUM(CASE WHEN municipality = '' THEN 1 ELSE 0 END) as empty_count,
        SUM(CASE WHEN municipality IS NOT NULL AND municipality != '' THEN 1 ELSE 0 END) as valid_count
    FROM mapcomplete
    GROUP BY row_type
    ORDER BY row_type
    """
    result = turso_query(sql)
    rows = parse_turso_response(result)
    print("\nrow_type別の市区町村データ:")
    print(f"{'row_type':<20} {'総数':>10} {'NULL':>10} {'空文字':>10} {'有効':>10}")
    print("-" * 60)
    for row in rows:
        print(f"{row['row_type']:<20} {row['count']:>10} {row['null_count']:>10} {row['empty_count']:>10} {row['valid_count']:>10}")

    # ========================================
    # 検証4: SUMMARYとAGE_GENDERの整合性
    # ========================================
    print_section("4. SUMMARYとAGE_GENDERの整合性検証")

    # まずサンプルとして5つの市区町村で検証
    sql = """
    SELECT prefecture, municipality
    FROM mapcomplete
    WHERE row_type = 'SUMMARY'
      AND municipality IS NOT NULL
      AND municipality != ''
    LIMIT 10
    """
    result = turso_query(sql)
    sample_munis = parse_turso_response(result)

    print("\nサンプル市区町村での検証:")
    print(f"{'都道府県':<12} {'市区町村':<15} {'SUMMARY':>10} {'AGE_GENDER':>12} {'差分':>8} {'結果':>8}")
    print("-" * 75)

    mismatch_count = 0
    for muni in sample_munis:
        pref = muni['prefecture']
        city = muni['municipality']

        # SUMMARY の applicant_count を取得
        sql_summary = f"""
        SELECT applicant_count
        FROM mapcomplete
        WHERE row_type = 'SUMMARY'
          AND prefecture = '{pref}'
          AND municipality = '{city}'
        """
        result_summary = turso_query(sql_summary)
        summary_rows = parse_turso_response(result_summary)
        summary_count = int(summary_rows[0]['applicant_count']) if summary_rows else 0

        # AGE_GENDER の count 合計を取得
        sql_age_gender = f"""
        SELECT SUM(CAST(count AS INTEGER)) as total
        FROM mapcomplete
        WHERE row_type = 'AGE_GENDER'
          AND prefecture = '{pref}'
          AND municipality = '{city}'
        """
        result_ag = turso_query(sql_age_gender)
        ag_rows = parse_turso_response(result_ag)
        ag_total = int(ag_rows[0]['total']) if ag_rows and ag_rows[0]['total'] else 0

        diff = summary_count - ag_total
        status = "OK" if diff == 0 else "NG"
        if diff != 0:
            mismatch_count += 1

        print(f"{pref:<12} {city:<15} {summary_count:>10} {ag_total:>12} {diff:>8} {status:>8}")

    if mismatch_count > 0:
        print(f"\n[警告] {mismatch_count}件の不整合が検出されました")
    else:
        print("\n[OK] サンプル市区町村でのデータ整合性は問題ありません")

    # 全体での不整合チェック
    print("\n全市区町村での整合性チェック:")
    sql = """
    WITH summary_data AS (
        SELECT prefecture, municipality, CAST(applicant_count AS INTEGER) as summary_count
        FROM mapcomplete
        WHERE row_type = 'SUMMARY'
          AND municipality IS NOT NULL
          AND municipality != ''
    ),
    age_gender_data AS (
        SELECT prefecture, municipality, SUM(CAST(count AS INTEGER)) as ag_total
        FROM mapcomplete
        WHERE row_type = 'AGE_GENDER'
          AND municipality IS NOT NULL
          AND municipality != ''
        GROUP BY prefecture, municipality
    )
    SELECT
        COUNT(*) as total_munis,
        SUM(CASE WHEN s.summary_count = a.ag_total THEN 1 ELSE 0 END) as match_count,
        SUM(CASE WHEN s.summary_count != a.ag_total THEN 1 ELSE 0 END) as mismatch_count
    FROM summary_data s
    LEFT JOIN age_gender_data a ON s.prefecture = a.prefecture AND s.municipality = a.municipality
    """
    result = turso_query(sql)
    integrity_check = parse_turso_response(result)
    if integrity_check:
        row = integrity_check[0]
        print(f"  総市区町村数: {row['total_munis']}")
        print(f"  一致: {row['match_count']}")
        print(f"  不一致: {row['mismatch_count']}")
        if row['mismatch_count'] and int(row['mismatch_count']) > 0:
            print("\n[詳細] 不一致の市区町村（上位10件）:")
            sql_detail = """
            WITH summary_data AS (
                SELECT prefecture, municipality, CAST(applicant_count AS INTEGER) as summary_count
                FROM mapcomplete
                WHERE row_type = 'SUMMARY'
                  AND municipality IS NOT NULL
                  AND municipality != ''
            ),
            age_gender_data AS (
                SELECT prefecture, municipality, SUM(CAST(count AS INTEGER)) as ag_total
                FROM mapcomplete
                WHERE row_type = 'AGE_GENDER'
                  AND municipality IS NOT NULL
                  AND municipality != ''
                GROUP BY prefecture, municipality
            )
            SELECT s.prefecture, s.municipality, s.summary_count, COALESCE(a.ag_total, 0) as ag_total,
                   s.summary_count - COALESCE(a.ag_total, 0) as diff
            FROM summary_data s
            LEFT JOIN age_gender_data a ON s.prefecture = a.prefecture AND s.municipality = a.municipality
            WHERE s.summary_count != COALESCE(a.ag_total, 0)
            ORDER BY ABS(s.summary_count - COALESCE(a.ag_total, 0)) DESC
            LIMIT 10
            """
            result_detail = turso_query(sql_detail)
            detail_rows = parse_turso_response(result_detail)
            for r in detail_rows:
                print(f"    {r['prefecture']} {r['municipality']}: SUMMARY={r['summary_count']}, AGE_GENDER={r['ag_total']}, 差分={r['diff']}")

    # ========================================
    # 検証5: 年齢層の定義確認
    # ========================================
    print_section("5. 年齢層の定義確認")

    sql = """
    SELECT DISTINCT age_group, COUNT(*) as count
    FROM mapcomplete
    WHERE row_type = 'AGE_GENDER'
      AND age_group IS NOT NULL
    GROUP BY age_group
    ORDER BY age_group
    """
    result = turso_query(sql)
    age_groups = parse_turso_response(result)
    print("\n定義されている年齢層:")
    for ag in age_groups:
        print(f"  - {ag['age_group']}: {ag['count']}件")

    expected_ages = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
    actual_ages = [ag['age_group'] for ag in age_groups]
    missing_ages = [a for a in expected_ages if a not in actual_ages]
    extra_ages = [a for a in actual_ages if a not in expected_ages]

    if missing_ages:
        print(f"\n[警告] 欠落している年齢層: {missing_ages}")
    if extra_ages:
        print(f"\n[情報] 追加の年齢層: {extra_ages}")
    if not missing_ages and not extra_ages:
        print("\n[OK] 年齢層の定義は期待通りです")

    # ========================================
    # 検証6: 性別データの欠損パターン
    # ========================================
    print_section("6. 性別データの欠損パターン")

    sql = """
    SELECT gender, COUNT(*) as count
    FROM mapcomplete
    WHERE row_type = 'AGE_GENDER'
    GROUP BY gender
    ORDER BY gender
    """
    result = turso_query(sql)
    genders = parse_turso_response(result)
    print("\n性別の分布:")
    for g in genders:
        gender_label = g['gender'] if g['gender'] else "(NULL/空)"
        print(f"  - {gender_label}: {g['count']}件")

    # 性別が欠損している市区町村を確認
    sql = """
    SELECT prefecture, municipality, age_group, count
    FROM mapcomplete
    WHERE row_type = 'AGE_GENDER'
      AND (gender IS NULL OR gender = '')
    LIMIT 10
    """
    result = turso_query(sql)
    null_gender = parse_turso_response(result)
    if null_gender:
        print(f"\n[警告] 性別が欠損しているレコード（上位10件）:")
        for r in null_gender:
            print(f"  {r['prefecture']} {r['municipality']} {r['age_group']}: {r['count']}件")
    else:
        print("\n[OK] 性別の欠損データはありません")

    # ========================================
    # 検証7: row_type別のデータ件数
    # ========================================
    print_section("7. row_type別データサマリー")

    sql = """
    SELECT row_type, COUNT(*) as count
    FROM mapcomplete
    GROUP BY row_type
    ORDER BY count DESC
    """
    result = turso_query(sql)
    row_types = parse_turso_response(result)
    print("\nrow_type別件数:")
    for rt in row_types:
        print(f"  - {rt['row_type']}: {rt['count']:,}件")

    # ========================================
    # 検証完了
    # ========================================
    print_section("検証完了")
    print("\n検証が完了しました。上記の結果を確認してください。")

if __name__ == "__main__":
    main()
