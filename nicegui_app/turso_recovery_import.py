#!/usr/bin/env python3
"""
Tursoリカバリインポートスクリプト

コンテンツベースの重複検出を使用して、欠落行のみをインポートします。
"""

import os
import sys
import json
import time
import hashlib
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import pandas as pd

# 設定
BATCH_SIZE = 5000
ROWS_PER_INSERT = 100
MAX_WORKERS = 4
REQUEST_TIMEOUT = 300
MAX_RETRIES = 3

# ハッシュ対象フィールド（ユニーク性の高い組み合わせ - 集計データの複合キー）
HASH_FIELDS = [
    'row_type', 'prefecture', 'municipality',
    'category1', 'category2', 'category3'
]


def get_turso_config():
    """Turso接続設定を取得"""
    load_dotenv()
    url = os.getenv('TURSO_DATABASE_URL', '').replace('libsql://', 'https://')
    token = os.getenv('TURSO_AUTH_TOKEN', '')
    return url, token


def execute_sql(url: str, token: str, sql: str, params: list = None) -> dict:
    """SQLを実行"""
    stmt = {'sql': sql}
    if params:
        stmt['args'] = params

    req = urllib.request.Request(
        f'{url}/v2/pipeline',
        data=json.dumps({'requests': [{'type': 'execute', 'stmt': stmt}]}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )

    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read().decode())


def compute_row_hash(row: dict) -> str:
    """行のハッシュを計算"""
    values = []
    for field in HASH_FIELDS:
        val = str(row.get(field, '')) if pd.notna(row.get(field)) else ''
        values.append(val)
    return hashlib.md5('|'.join(values).encode()).hexdigest()[:16]


def get_existing_hashes(url: str, token: str, job_type: str, batch_size: int = 50000) -> set:
    """既存データのハッシュセットを取得"""
    print(f"既存データのハッシュを取得中 (job_type: {job_type})...")

    hash_fields_sql = ', '.join([f"COALESCE({f}, '')" for f in HASH_FIELDS])

    hashes = set()
    offset = 0

    while True:
        query = f"SELECT {hash_fields_sql} FROM job_seeker_data WHERE job_type = ? LIMIT {batch_size} OFFSET {offset}"
        params = [{'type': 'text', 'value': job_type}]

        try:
            result = execute_sql(url, token, query, params)
            result_data = result.get('results', [{}])[0]
            if result_data.get('type') == 'error':
                print(f"  SQLエラー: {result_data.get('error', {}).get('message', 'Unknown')}")
                break
            rows = result_data.get('response', {}).get('result', {}).get('rows', [])

            if not rows:
                break

            for row in rows:
                values = [str(cell.get('value', '')) if cell.get('type') != 'null' else '' for cell in row]
                h = hashlib.md5('|'.join(values).encode()).hexdigest()[:16]
                hashes.add(h)

            offset += batch_size
            print(f"  取得済み: {len(hashes):,} ハッシュ (offset: {offset:,})")

        except Exception as e:
            print(f"  エラー: {e}")
            break

    print(f"既存ハッシュ数: {len(hashes):,}")
    return hashes


def get_max_id(url: str, token: str) -> int:
    """最大IDを取得"""
    result = execute_sql(url, token, "SELECT MAX(CAST(id AS INTEGER)) FROM job_seeker_data")
    rows = result['results'][0]['response']['result']['rows']
    if rows and rows[0][0].get('type') != 'null':
        return int(rows[0][0]['value'])
    return 0


def convert_value(val, col_name: str):
    """値をTurso API用に変換"""
    if pd.isna(val) or val is None or val == '' or str(val).lower() == 'nan':
        return {'type': 'null'}

    numeric_cols = {'desired_count', 'lat', 'lng', 'female_ratio', 'top_age_ratio',
                    'avg_desired_areas', 'persona_count', 'persona_percentage'}

    if col_name in numeric_cols:
        try:
            return {'type': 'float', 'value': float(val)}
        except:
            return {'type': 'null'}

    return {'type': 'text', 'value': str(val)}


def build_multi_row_insert(columns: list, rows_data: list) -> tuple:
    """複数行INSERTを構築"""
    col_names = ', '.join(columns)
    num_cols = len(columns)
    row_placeholder = '(' + ', '.join(['?' for _ in range(num_cols)]) + ')'
    all_placeholders = ', '.join([row_placeholder for _ in rows_data])

    sql = f"INSERT OR IGNORE INTO job_seeker_data ({col_names}) VALUES {all_placeholders}"

    args = []
    for row in rows_data:
        for col in columns:
            args.append(convert_value(row.get(col), col))

    return sql, args


def insert_batch(url: str, token: str, batch_df: pd.DataFrame,
                 columns: list, batch_num: int) -> tuple:
    """バッチ挿入"""
    rows_data = batch_df.to_dict('records')
    total_rows = len(rows_data)

    chunks = [rows_data[i:i+ROWS_PER_INSERT] for i in range(0, total_rows, ROWS_PER_INSERT)]

    requests = []
    for chunk in chunks:
        sql, args = build_multi_row_insert(columns, chunk)
        requests.append({
            'type': 'execute',
            'stmt': {'sql': sql, 'args': args}
        })

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                f'{url}/v2/pipeline',
                data=json.dumps({'requests': requests}).encode(),
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
            result = json.loads(resp.read().decode())

            errors = []
            for i, r in enumerate(result.get('results', [])):
                if r.get('type') == 'error':
                    errors.append(f"Chunk {i}: {r.get('error', {}).get('message', 'Unknown')}")

            if errors:
                return (batch_num, total_rows, len(errors) * ROWS_PER_INSERT, errors[:2])

            return (batch_num, total_rows, 0, None)

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return (batch_num, total_rows, total_rows, [str(e)[:100]])

    return (batch_num, 0, total_rows, ["Max retries exceeded"])


def main():
    parser = argparse.ArgumentParser(description='Tursoリカバリインポート')
    parser.add_argument('--job_type', type=str, required=True, help='職種名')
    parser.add_argument('--csv_path', type=str, required=True, help='CSVファイルパス')
    parser.add_argument('--dry_run', action='store_true', help='ドライラン')
    args = parser.parse_args()

    job_type = args.job_type
    csv_path = args.csv_path

    print("=" * 60)
    print("Tursoリカバリインポート（コンテンツベース重複検出）")
    print(f"  職種: {job_type}")
    print(f"  CSVパス: {csv_path}")
    print(f"  ドライラン: {args.dry_run}")
    print("=" * 60)

    url, token = get_turso_config()
    if not url or not token:
        print("ERROR: Turso設定が見つかりません")
        sys.exit(1)

    # CSV読み込み
    print(f"\nCSV読み込み中...")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    print(f"CSV行数: {len(df):,}")

    # 重複除去
    df = df.drop_duplicates()
    print(f"重複除去後: {len(df):,}")

    # job_type追加
    df['job_type'] = job_type

    # 既存ハッシュ取得
    existing_hashes = get_existing_hashes(url, token, job_type)

    # 新規行のフィルタリング
    print("\n新規行を特定中...")
    new_rows = []
    for idx, row in df.iterrows():
        h = compute_row_hash(row.to_dict())
        if h not in existing_hashes:
            new_rows.append(idx)

    print(f"新規行数: {len(new_rows):,}")

    if not new_rows:
        print("すべてのデータがインポート済みです")
        return

    # 新規行のDataFrame作成
    new_df = df.loc[new_rows].copy()

    # 新しいID割り当て
    max_id = get_max_id(url, token)
    print(f"現在の最大ID: {max_id}")

    new_df['id'] = [str(max_id + i + 1) for i in range(len(new_df))]
    print(f"新規ID範囲: {max_id + 1} - {max_id + len(new_df)}")

    if args.dry_run:
        print(f"\n[ドライラン] インポート予定: {len(new_df):,} 行")
        return

    # インポート実行
    columns = list(new_df.columns)
    batches = [new_df.iloc[i:i+BATCH_SIZE] for i in range(0, len(new_df), BATCH_SIZE)]
    total_batches = len(batches)

    print(f"\nバッチ数: {total_batches}")
    print("-" * 60)

    start_time = time.time()
    completed = 0
    errors_total = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for i, batch_df in enumerate(batches):
            future = executor.submit(insert_batch, url, token, batch_df, columns, i)
            futures[future] = i

        for future in as_completed(futures):
            batch_num, inserted, errors, error_msgs = future.result()
            completed += 1
            errors_total += errors

            elapsed = time.time() - start_time
            progress = (completed / total_batches) * 100
            rate = (completed * BATCH_SIZE) / elapsed if elapsed > 0 else 0

            status = "OK" if errors == 0 else f"ERR({errors})"
            print(f"\r[{completed:4d}/{total_batches}] {progress:5.1f}% | "
                  f"{rate:,.0f} rows/sec | {status}", end="", flush=True)

            if error_msgs:
                print(f"\n  {error_msgs[0]}")

    elapsed = time.time() - start_time
    print(f"\n\n完了: {len(new_df):,}行 / {elapsed:.1f}秒 / エラー{errors_total}")


if __name__ == "__main__":
    main()
