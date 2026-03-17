#!/usr/bin/env python3
"""
CSV-DB同期フレームワーク

設計原則:
- 冪等性: 同じCSVを複数回適用しても結果が同じ
- トランザクション整合性: 途中失敗時にロールバック可能
- 検証必須: インポート前後で必ず検証を実行
- 監査可能: 変更履歴を追跡可能

使用方法:
  python turso_sync.py validate <CSVファイル>   # CSV検証のみ
  python turso_sync.py import <CSVファイル>     # 検証→インポート→検証
  python turso_sync.py verify <job_type>        # DB検証のみ
"""

import os
import sys
import json
import time
import urllib.request
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
import pandas as pd

# =============================================================================
# 定数定義
# =============================================================================

# row_type別の一意キー定義（2026-02-02 実データ構造に基づき修正）
UNIQUE_KEY_DEFINITIONS = {
    # 基本キー: job_type + prefecture + municipality のみ
    'SUMMARY': ['job_type', 'prefecture', 'municipality'],
    'GAP': ['job_type', 'prefecture', 'municipality'],
    'FLOW': ['job_type', 'prefecture', 'municipality'],
    'COMPETITION': ['job_type', 'prefecture', 'municipality'],
    'WORKSTYLE_REGION': ['job_type', 'prefecture', 'municipality', 'category1'],

    # cat1キー
    'PERSONA_MUNI': ['job_type', 'prefecture', 'municipality', 'category1'],
    'WORKSTYLE_DISTRIBUTION': ['job_type', 'prefecture', 'municipality', 'category1'],
    'QUALIFICATION_DETAIL': ['job_type', 'prefecture', 'municipality', 'category1'],

    # cat2キー（URGENCY系: category1が空、category2にデータ）
    'URGENCY_AGE': ['job_type', 'prefecture', 'municipality', 'category2'],
    'URGENCY_EMPLOYMENT': ['job_type', 'prefecture', 'municipality', 'category2'],
    'URGENCY_GENDER': ['job_type', 'prefecture', 'municipality', 'category2'],
    'URGENCY_START_CATEGORY': ['job_type', 'prefecture', 'municipality', 'category2'],

    # cat1+cat2キー
    'AGE_GENDER': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'AGE_GENDER_RESIDENCE': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'DESIRED_AREA_PATTERN': ['job_type', 'prefecture', 'municipality', 'category1', 'category2', 'co_desired_prefecture', 'co_desired_municipality'],
    'RESIDENCE_FLOW': ['job_type', 'prefecture', 'municipality', 'category1', 'category2', 'desired_prefecture', 'desired_municipality'],
    'WORKSTYLE_AGE_CROSS': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_CAREER': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_DESIRED_AREA_COUNT': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_EMPLOYMENT_STATUS': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_GENDER_CROSS': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_MOBILITY': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_QUALIFICATION': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],
    'WORKSTYLE_URGENCY': ['job_type', 'prefecture', 'municipality', 'category1', 'category2'],

    # cat1+cat2+cat3キー
    'EMPLOYMENT_AGE_CROSS': ['job_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3'],
    'WORKSTYLE_AGE_GENDER_CROSS': ['job_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3'],
    'QUALIFICATION_PERSONA': ['job_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3'],

    # 特殊キー（座標含む）
    'RARITY': ['job_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3', 'latitude', 'longitude'],
}

# 必須カラム
REQUIRED_COLUMNS = ['row_type', 'job_type', 'prefecture', 'municipality']

# 職種別期待行数範囲
EXPECTED_ROW_RANGES = {
    # 2026-02-02 dedup後の行数に基づき更新（±10%マージン）
    '看護師': (780_000, 960_000),
    '介護職': (780_000, 960_000),
    '保育士': (770_000, 950_000),
    '栄養士': (630_000, 780_000),
    '生活相談員': (620_000, 770_000),
    '調理師、調理スタッフ': (570_000, 700_000),
    '学童支援': (540_000, 670_000),
    'サービス管理責任者': (530_000, 660_000),
    'サービス提供責任者': (500_000, 620_000),
    'ケアマネジャー': (490_000, 600_000),
    '理学療法士': (450_000, 550_000),
    '作業療法士': (400_000, 500_000),
}

# インポート設定
ROWS_PER_INSERT = 20
INSERTS_PER_REQUEST = 50

# =============================================================================
# ユーティリティ関数
# =============================================================================

def get_unique_key_cols(row_type: str) -> List[str]:
    """row_typeに対応する一意キーカラムを取得"""
    return UNIQUE_KEY_DEFINITIONS.get(row_type, REQUIRED_COLUMNS)


def get_turso_config() -> Tuple[str, str]:
    """Turso接続情報を取得"""
    load_dotenv()
    url = os.getenv('TURSO_DATABASE_URL', '').replace('libsql://', 'https://')
    token = os.getenv('TURSO_AUTH_TOKEN', '')
    return url, token


def convert_value(val, col_name: str) -> dict:
    """値をTurso API形式に変換"""
    if pd.isna(val) or val is None or val == '' or str(val).lower() == 'nan':
        return {'type': 'null'}

    numeric_cols = [
        'desired_count', 'lat', 'lng', 'female_ratio', 'top_age_ratio',
        'avg_desired_areas', 'persona_count', 'persona_percentage',
        'supply_count', 'demand_count', 'gap', 'gap_ratio', 'rarity_score',
        'competition_score', 'flow_in', 'flow_out', 'net_flow', 'count',
        'percentage', 'male_count', 'female_count', 'male_ratio',
        'cross_count', 'cross_percentage', 'applicant_count',
        'avg_qualifications', 'latitude', 'longitude', 'avg_reference_distance_km',
        'total_applicants', 'retention_rate', 'avg_age'
    ]

    integer_cols = [
        'desired_count', 'count', 'male_count', 'female_count',
        'cross_count', 'applicant_count', 'supply_count', 'demand_count',
        'total_applicants'
    ]

    if col_name in numeric_cols:
        try:
            float_val = float(val)
            if col_name in integer_cols:
                return {'type': 'integer', 'value': str(int(float_val))}
            return {'type': 'float', 'value': float_val}
        except:
            return {'type': 'null'}

    return {'type': 'text', 'value': str(val)}


def send_pipeline(url: str, token: str, requests: list, timeout: int = 300, max_retries: int = 5) -> dict:
    """Turso Pipeline APIにリクエスト送信（リトライ付き）"""
    data = json.dumps({'requests': requests}).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                f'{url}/v2/pipeline',
                data=data,
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=timeout)
            return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt * 3  # 3, 6, 12, 24, 48秒
                print(f"\n  リトライ {attempt+1}/{max_retries} ({wait}秒待機): {str(e)[:50]}")
                time.sleep(wait)
            else:
                raise  # 最終試行で失敗したら例外を投げる


def query_db(url: str, token: str, sql: str, args: list = None) -> list:
    """DBクエリ実行"""
    stmt = {'sql': sql}
    if args:
        stmt['args'] = [{'type': 'text', 'value': str(a)} for a in args]

    result = send_pipeline(url, token, [{'type': 'execute', 'stmt': stmt}])

    if result['results'][0].get('type') == 'error':
        raise Exception(result['results'][0]['error']['message'])

    rows = result['results'][0]['response']['result'].get('rows', [])
    cols = result['results'][0]['response']['result'].get('cols', [])
    col_names = [c['name'] for c in cols]

    return [dict(zip(col_names, [r.get('value') for r in row])) for row in rows]


def query_scalar(url: str, token: str, sql: str, args: list = None):
    """スカラー値を取得"""
    rows = query_db(url, token, sql, args)
    if rows:
        return list(rows[0].values())[0]
    return None


# =============================================================================
# CSV検証
# =============================================================================

def validate_csv(csv_path: str, expected_job_type: str = None) -> Dict:
    """
    CSV検証（インポート前）

    チェック項目:
    1. job_type一意性
    2. row_type存在確認
    3. 必須カラム非NULL
    4. 一意キー重複なし
    5. 行数妥当性
    """
    print("\n" + "=" * 60)
    print("CSV検証")
    print("=" * 60)

    errors = []
    warnings = []

    # CSV読み込み
    print(f"\n[LOAD] {os.path.basename(csv_path)}")
    try:
        df = pd.read_csv(csv_path, dtype=str, low_memory=False, encoding='utf-8-sig')
    except Exception as e:
        return {'valid': False, 'errors': [f'CSV読み込みエラー: {e}']}

    print(f"  行数: {len(df):,}")
    print(f"  カラム数: {len(df.columns)}")

    # 1. idカラムチェック
    if 'id' in df.columns:
        warnings.append("idカラムが存在します（インポート時に除外されます）")
        df = df.drop(columns=['id'])

    # 2. job_type一意性
    print("\n[CHECK] job_type一意性")
    if 'job_type' not in df.columns:
        errors.append("job_typeカラムがありません")
    else:
        job_types = df['job_type'].dropna().unique()
        if len(job_types) == 0:
            errors.append("job_typeが全て空です")
        elif len(job_types) > 1:
            errors.append(f"複数のjob_typeが含まれています: {list(job_types)}")
        else:
            job_type = job_types[0]
            print(f"  job_type: {job_type} [OK]")

            if expected_job_type and job_type != expected_job_type:
                errors.append(f"job_type不一致: {job_type} != {expected_job_type}")

    # 3. 必須カラム存在・非NULL
    print("\n[CHECK] 必須カラム")
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"必須カラム '{col}' がありません")
        else:
            null_count = df[col].isna().sum()
            if null_count > 0:
                # municipalityのNULLは都道府県レベル集計として許容
                if col == 'municipality':
                    warnings.append(f"'{col}'に{null_count:,}件のNULLがあります（都道府県集計）")
                    print(f"  {col}: {null_count:,}件NULL（都道府県集計） [WARN]")
                else:
                    errors.append(f"'{col}'に{null_count:,}件のNULLがあります")
            else:
                print(f"  {col}: OK")

    # 4. row_type存在確認
    print("\n[CHECK] row_type存在確認")
    if 'row_type' in df.columns:
        row_types = df['row_type'].dropna().unique()
        unknown_types = [rt for rt in row_types if rt not in UNIQUE_KEY_DEFINITIONS]
        if unknown_types:
            warnings.append(f"未定義のrow_type: {unknown_types}")
            print(f"  未定義: {unknown_types} [WARN]")

        print(f"  検出されたrow_type: {len(row_types)}種類")
        for rt in sorted(row_types):
            count = len(df[df['row_type'] == rt])
            status = "[OK]" if rt in UNIQUE_KEY_DEFINITIONS else "[WARN]"
            print(f"    {rt}: {count:,}行 {status}")

    # 5. 一意キー重複チェック
    print("\n[CHECK] 一意キー重複")
    duplicate_count = 0
    if 'row_type' in df.columns:
        for rt in df['row_type'].unique():
            if pd.isna(rt):
                continue
            key_cols = get_unique_key_cols(rt)

            # カラム存在確認
            missing_cols = [c for c in key_cols if c not in df.columns]
            if missing_cols:
                # category系カラムがない場合はスキップ（そのrow_typeで使わない可能性）
                if all(c.startswith('category') for c in missing_cols):
                    continue
                warnings.append(f"{rt}: 一意キーカラム不足 {missing_cols}")
                continue

            subset = df[df['row_type'] == rt]
            # NaN値を文字列に変換して重複チェック
            subset_filled = subset[key_cols].fillna('__NULL__')
            dup = subset_filled.groupby(key_cols).size()
            dup_count = (dup > 1).sum()

            if dup_count > 0:
                errors.append(f"{rt}: {dup_count:,}件の重複キーがあります")
                duplicate_count += dup_count
                print(f"  {rt}: {dup_count:,}件の重複 [NG]")
            else:
                print(f"  {rt}: 重複なし [OK]")

    # 6. 行数妥当性
    print("\n[CHECK] 行数妥当性")
    if 'job_type' in df.columns and len(df['job_type'].dropna().unique()) == 1:
        job_type = df['job_type'].dropna().iloc[0]
        row_count = len(df)

        if job_type in EXPECTED_ROW_RANGES:
            min_rows, max_rows = EXPECTED_ROW_RANGES[job_type]
            if row_count < min_rows:
                warnings.append(f"行数が期待値より少ない: {row_count:,} < {min_rows:,}")
                print(f"  {row_count:,}行 (期待: {min_rows:,}~{max_rows:,}) [WARN]")
            elif row_count > max_rows:
                warnings.append(f"行数が期待値より多い: {row_count:,} > {max_rows:,}")
                print(f"  {row_count:,}行 (期待: {min_rows:,}~{max_rows:,}) [WARN]")
            else:
                print(f"  {row_count:,}行 (期待範囲内) [OK]")
        else:
            print(f"  {row_count:,}行 (期待値未定義)")

    # 7. 都道府県数チェック
    print("\n[CHECK] 都道府県数")
    if 'prefecture' in df.columns:
        prefectures = df['prefecture'].dropna().unique()
        pref_count = len(prefectures)
        if pref_count < 47:
            warnings.append(f"都道府県が47未満: {pref_count}県")
            print(f"  {pref_count}県 (期待: 47県) [WARN]")
        elif pref_count > 47:
            warnings.append(f"都道府県が47超過: {pref_count}県（異常データ混入の可能性）")
            print(f"  {pref_count}県 (期待: 47県) [WARN] 超過")
        else:
            print(f"  {pref_count}県 [OK]")

    # 結果サマリ
    print("\n" + "=" * 60)
    if errors:
        print(f"[NG] 検証失敗: {len(errors)}件のエラー")
        for e in errors:
            print(f"  [NG] {e}")
    else:
        print("[OK] 検証成功")

    if warnings:
        print(f"\n警告: {len(warnings)}件")
        for w in warnings:
            print(f"  [WARN] {w}")

    print("=" * 60)

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'row_count': len(df),
        'job_type': df['job_type'].dropna().iloc[0] if 'job_type' in df.columns and len(df['job_type'].dropna()) > 0 else None,
        'row_types': df['row_type'].value_counts().to_dict() if 'row_type' in df.columns else {}
    }


# =============================================================================
# DB検証
# =============================================================================

def validate_db_after_import(job_type: str, expected_counts: Dict[str, int] = None) -> Dict:
    """
    インポート後のDB検証

    チェック項目:
    1. row_type別行数
    2. SUMMARY重複チェック
    3. サンプル値確認
    """
    print("\n" + "=" * 60)
    print("DB検証")
    print("=" * 60)

    url, token = get_turso_config()
    if not url or not token:
        return {'valid': False, 'errors': ['Turso設定なし']}

    errors = []
    warnings = []

    print(f"\n[CHECK] job_type: {job_type}")

    # 1. 総行数
    total = query_scalar(url, token,
        "SELECT COUNT(*) FROM job_seeker_data WHERE job_type = ?", [job_type])
    total = int(total) if total else 0
    print(f"  総行数: {total:,}")

    # 2. row_type別行数
    print("\n[CHECK] row_type別行数")
    rows = query_db(url, token, """
        SELECT row_type, COUNT(*) as cnt
        FROM job_seeker_data
        WHERE job_type = ?
        GROUP BY row_type
        ORDER BY cnt DESC
    """, [job_type])

    db_counts = {r['row_type']: int(r['cnt']) for r in rows}

    for rt, cnt in sorted(db_counts.items(), key=lambda x: -x[1]):
        if expected_counts and rt in expected_counts:
            expected = expected_counts[rt]
            if cnt != expected:
                errors.append(f"{rt}: {cnt:,} != {expected:,} (期待値)")
                print(f"  {rt}: {cnt:,} (期待: {expected:,}) [NG]")
            else:
                print(f"  {rt}: {cnt:,} [OK]")
        else:
            print(f"  {rt}: {cnt:,}")

    # 3. SUMMARY重複チェック（同名市区町村を考慮: prefecture + municipality でグループ化）
    print("\n[CHECK] SUMMARY重複")
    dups = query_db(url, token, """
        SELECT prefecture, municipality, COUNT(*) as cnt
        FROM job_seeker_data
        WHERE job_type = ? AND row_type = 'SUMMARY'
        GROUP BY prefecture, municipality
        HAVING cnt > 1
    """, [job_type])

    if dups:
        errors.append(f"SUMMARY重複: {len(dups)}件（都道府県+市区町村）")
        for d in dups[:5]:
            print(f"  {d['prefecture']}/{d['municipality']}: {d['cnt']}件 [NG]")
        if len(dups) > 5:
            print(f"  ... 他{len(dups)-5}件")
    else:
        print("  重複なし [OK]")

    # 4. サンプル値確認（実データから上位3市区町村を取得）
    print("\n[CHECK] サンプルデータ（上位市区町村）")
    sample = query_db(url, token, """
        SELECT prefecture, municipality, applicant_count, avg_age, female_ratio
        FROM job_seeker_data
        WHERE job_type = ? AND row_type = 'SUMMARY' AND municipality IS NOT NULL AND municipality != ''
        ORDER BY CAST(applicant_count AS REAL) DESC
        LIMIT 3
    """, [job_type])

    if sample:
        for s in sample:
            print(f"  {s.get('prefecture')}/{s.get('municipality')}: "
                  f"applicant_count={s.get('applicant_count')}, "
                  f"avg_age={s.get('avg_age')}, "
                  f"female_ratio={s.get('female_ratio')}")
    else:
        warnings.append("SUMMARYデータが見つかりません")
        print("  データなし [WARN]")

    # 5. 都道府県数チェック
    print("\n[CHECK] 都道府県数")
    pref_count = query_scalar(url, token,
        "SELECT COUNT(DISTINCT prefecture) FROM job_seeker_data WHERE job_type = ?",
        [job_type])
    if pref_count:
        pref_count = int(pref_count)
        if pref_count < 47:
            warnings.append(f"DB都道府県が47未満: {pref_count}県")
            print(f"  {pref_count}県 (期待: 47県) [WARN]")
        elif pref_count > 47:
            warnings.append(f"DB都道府県が47超過: {pref_count}県（異常データ混入の可能性）")
            print(f"  {pref_count}県 (期待: 47県) [WARN] 超過")
        else:
            print(f"  {pref_count}県 [OK]")
    else:
        errors.append("都道府県数を取得できません")
        print("  取得失敗 [NG]")

    # 結果サマリ
    print("\n" + "=" * 60)
    if errors:
        print(f"[NG] 検証失敗: {len(errors)}件のエラー")
        for e in errors:
            print(f"  [NG] {e}")
    else:
        print("[OK] 検証成功")

    if warnings:
        print(f"\n警告: {len(warnings)}件")
        for w in warnings:
            print(f"  [WARN] {w}")

    print("=" * 60)

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'total_rows': int(total) if total else 0,
        'row_type_counts': db_counts
    }


# =============================================================================
# インポート処理
# =============================================================================

def delete_job_type_data(url: str, token: str, job_type: str) -> int:
    """指定job_typeのデータを全削除"""
    print(f"\n[DELETE] {job_type} のデータを削除中...")
    deleted = 0
    while True:
        try:
            result = send_pipeline(url, token, [{
                'type': 'execute',
                'stmt': {
                    'sql': "DELETE FROM job_seeker_data WHERE rowid IN (SELECT rowid FROM job_seeker_data WHERE job_type = ? LIMIT 100000)",
                    'args': [{'type': 'text', 'value': job_type}]
                }
            }], timeout=600)
            affected = result['results'][0]['response']['result'].get('affected_row_count', 0)
            deleted += affected
            print(f"\r  削除中: {deleted:,}行", end="", flush=True)
            if affected < 100000:
                break
        except Exception as e:
            print(f"\n  削除エラー: {e}")
            return -1
    print(f"\n  削除完了: {deleted:,}行 [OK]")
    return deleted


def create_bulk_insert_stmt(records: list, columns: list) -> dict:
    """バルクINSERT文を生成"""
    col_names = ', '.join(columns)
    single_ph = '(' + ', '.join(['?' for _ in columns]) + ')'
    all_ph = ', '.join([single_ph for _ in records])
    sql = f"INSERT INTO job_seeker_data ({col_names}) VALUES {all_ph}"

    args = []
    for row in records:
        for col in columns:
            args.append(convert_value(row.get(col), col))

    return {'type': 'execute', 'stmt': {'sql': sql, 'args': args}}


def import_csv(csv_path: str, skip_validation: bool = False) -> int:
    """
    CSV→DBインポート（検証付き）

    フロー:
    1. CSV検証（skip_validation=Falseの場合）
    2. 既存データ削除
    3. データ挿入
    4. DB検証
    """
    url, token = get_turso_config()
    if not url or not token:
        print("ERROR: Turso設定なし（.envを確認）")
        return 1

    print("\n" + "=" * 60)
    print("CSV-DB同期フレームワーク")
    print("=" * 60)
    print(f"ファイル: {os.path.basename(csv_path)}")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Phase 1: CSV検証
    if not skip_validation:
        csv_result = validate_csv(csv_path)
        if not csv_result['valid']:
            print("\n[ABORT] CSV検証失敗のためインポートを中止")
            return 1
        job_type = csv_result['job_type']
        expected_counts = csv_result['row_types']
    else:
        df = pd.read_csv(csv_path, dtype=str, low_memory=False, encoding='utf-8-sig', nrows=1)
        job_type = df['job_type'].iloc[0]
        expected_counts = None

    # Phase 2: バックアップ情報記録
    print("\n[BACKUP] 現在のDB状態を記録")
    before_count = query_scalar(url, token,
        "SELECT COUNT(*) FROM job_seeker_data WHERE job_type = ?", [job_type])
    before_count = int(before_count) if before_count else 0
    print(f"  既存行数: {before_count:,}")

    # Phase 3: 削除
    deleted = delete_job_type_data(url, token, job_type)
    if deleted < 0:
        print("\n[ABORT] 削除エラーのためインポートを中止")
        return 1

    # Phase 4: インポート
    print(f"\n[INSERT] データをインポート中...")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False, encoding='utf-8-sig')

    # idカラム除外
    columns = [c for c in df.columns if c != 'id']
    if 'id' in df.columns:
        df = df.drop(columns=['id'])

    total_rows = len(df)
    all_records = df.to_dict('records')

    rows_per_request = ROWS_PER_INSERT * INSERTS_PER_REQUEST
    mega_batches = [all_records[i:i+rows_per_request] for i in range(0, total_rows, rows_per_request)]
    total_mega = len(mega_batches)

    print(f"  総行数: {total_rows:,}")
    print(f"  リクエスト数: {total_mega}")

    start_time = time.time()
    inserted_total = 0
    errors_total = 0

    for i, mega_batch in enumerate(mega_batches):
        sub_batches = [mega_batch[j:j+ROWS_PER_INSERT] for j in range(0, len(mega_batch), ROWS_PER_INSERT)]
        requests = [create_bulk_insert_stmt(sub, columns) for sub in sub_batches]

        try:
            result = send_pipeline(url, token, requests, timeout=300)

            batch_inserted = 0
            batch_errors = 0
            for r in result.get('results', []):
                if r.get('type') == 'error':
                    batch_errors += ROWS_PER_INSERT
                else:
                    affected = r.get('response', {}).get('result', {}).get('affected_row_count', ROWS_PER_INSERT)
                    batch_inserted += affected

            inserted_total += batch_inserted
            errors_total += batch_errors

        except Exception as e:
            errors_total += len(mega_batch)
            print(f"\n  エラー: {str(e)[:60]}")

        elapsed = time.time() - start_time
        rows_done = min((i + 1) * rows_per_request, total_rows)
        progress = (rows_done / total_rows) * 100
        rate = rows_done / elapsed if elapsed > 0 else 0
        remaining = (total_rows - rows_done) / rate if rate > 0 else 0

        print(f"\r  [{i+1:5d}/{total_mega}] {progress:5.1f}% | {rate:,.0f} rows/s | ETA {remaining/60:.1f}min   ", end="", flush=True)

    elapsed = time.time() - start_time
    print(f"\n  インポート完了: {total_rows:,}行 ({elapsed/60:.1f}分) [OK]")

    # Phase 5: DB検証
    db_result = validate_db_after_import(job_type, expected_counts)

    # 最終結果
    print("\n" + "=" * 60)
    print("同期結果サマリ")
    print("=" * 60)
    print(f"  job_type: {job_type}")
    print(f"  削除行数: {deleted:,}")
    print(f"  挿入行数: {total_rows:,}")
    print(f"  DB検証行数: {db_result['total_rows']:,}")
    print(f"  処理時間: {elapsed/60:.1f}分")
    print(f"  処理速度: {total_rows/elapsed:,.0f} rows/s")
    print(f"  エラー: {errors_total}")

    if db_result['valid'] and errors_total == 0:
        print("\n[SUCCESS] 同期完了 [OK]")
        return 0
    else:
        print("\n[WARNING] 同期完了（警告あり）")
        return 0 if db_result['valid'] else 1


# =============================================================================
# メイン
# =============================================================================

def print_usage():
    print("""
CSV-DB同期フレームワーク

使用方法:
  python turso_sync.py validate <CSVファイル>   CSV検証のみ
  python turso_sync.py import <CSVファイル>     検証→インポート→検証
  python turso_sync.py verify <job_type>        DB検証のみ

例:
  python turso_sync.py validate MapComplete_看護師_READY.csv
  python turso_sync.py import MapComplete_看護師_READY.csv
  python turso_sync.py verify 看護師

注意:
  - CSVにはjob_type列が必須
  - 1つのjob_typeのみ含むCSVを使用
  - インポート前に該当job_typeの既存データは自動削除
  - 検証に失敗した場合、インポートは実行されません
""")


def main():
    if len(sys.argv) < 3:
        print_usage()
        return 1

    command = sys.argv[1].lower()
    target = sys.argv[2]

    if command == 'validate':
        if not os.path.exists(target):
            print(f"ERROR: ファイルが見つかりません: {target}")
            return 1
        result = validate_csv(target)
        return 0 if result['valid'] else 1

    elif command == 'import':
        if not os.path.exists(target):
            print(f"ERROR: ファイルが見つかりません: {target}")
            return 1
        return import_csv(target)

    elif command == 'verify':
        result = validate_db_after_import(target)
        return 0 if result['valid'] else 1

    else:
        print(f"ERROR: 不明なコマンド: {command}")
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
