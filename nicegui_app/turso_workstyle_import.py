#!/usr/bin/env python3
"""
WORKSTYLE差分インポートスクリプト
- 既存のWORKSTYLE行を削除
- 新しいWORKSTYLE行のみをインポート
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import pandas as pd

# 設定
BATCH_SIZE = 500   # 1バッチあたりの行数（小さくしてエラー回避）
MAX_WORKERS = 5    # 並列リクエスト数（増加）
MAX_RETRIES = 3    # リトライ回数

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

def get_workstyle_count(url: str, token: str) -> int:
    """現在のWORKSTYLE行数を取得"""
    result = execute_sql(url, token, "SELECT COUNT(*) FROM job_seeker_data WHERE row_type LIKE 'WORKSTYLE_%'")
    return int(result['results'][0]['response']['result']['rows'][0][0]['value'])

def delete_workstyle_rows(url: str, token: str) -> int:
    """既存のWORKSTYLE行を削除"""
    result = execute_sql(url, token, "DELETE FROM job_seeker_data WHERE row_type LIKE 'WORKSTYLE_%'")
    affected = result['results'][0]['response']['result'].get('affected_row_count', 0)
    return affected

def convert_value(val, col_name: str):
    """値をTurso API用に変換"""
    if pd.isna(val) or val is None or val == '' or str(val).lower() == 'nan':
        return {'type': 'null'}

    # 数値カラム
    numeric_cols = [
        'desired_count', 'lat', 'lng', 'female_ratio', 'top_age_ratio',
        'avg_desired_areas', 'persona_count', 'persona_percentage',
        'supply_count', 'demand_count', 'gap', 'gap_ratio', 'rarity_score',
        'competition_score', 'flow_in', 'flow_out', 'net_flow', 'count',
        'percentage', 'male_count', 'female_count', 'male_ratio',
        'cross_count', 'cross_percentage'
    ]

    if col_name in numeric_cols:
        try:
            float_val = float(val)
            if col_name in ['desired_count', 'count', 'male_count', 'female_count', 'cross_count']:
                return {'type': 'integer', 'value': str(int(float_val))}
            return {'type': 'float', 'value': float_val}
        except (ValueError, TypeError):
            return {'type': 'null'}

    # テキストカラム
    return {'type': 'text', 'value': str(val)}

def insert_batch(url: str, token: str, batch_df: pd.DataFrame, columns: list, batch_num: int) -> tuple:
    """バッチ挿入を実行"""
    placeholders = ', '.join(['?' for _ in columns])
    col_names = ', '.join(columns)
    sql = f"INSERT INTO job_seeker_data ({col_names}) VALUES ({placeholders})"

    requests = []
    for _, row in batch_df.iterrows():
        args = [convert_value(row.get(col), col) for col in columns]
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
            resp = urllib.request.urlopen(req, timeout=300)
            result = json.loads(resp.read().decode())

            # エラーチェック
            errors = []
            for i, r in enumerate(result.get('results', [])):
                if r.get('type') == 'error':
                    errors.append(f"Row {i}: {r.get('error', {}).get('message', 'Unknown error')}")

            if errors:
                return (batch_num, len(batch_df), len(errors), errors[:3])

            return (batch_num, len(batch_df), 0, None)

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
                continue
            return (batch_num, len(batch_df), len(batch_df), [str(e)])

    return (batch_num, 0, len(batch_df), ["Max retries exceeded"])

def main():
    print("=" * 60)
    print("WORKSTYLE差分インポート開始")
    print("=" * 60)

    # 設定取得
    url, token = get_turso_config()
    if not url or not token:
        print("ERROR: Turso設定が見つかりません")
        sys.exit(1)

    print(f"Turso URL: {url[:50]}...")

    # CSVパス
    csv_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts\data\output_v2\mapcomplete_complete_sheets\MapComplete_Complete_All_FIXED.csv"

    if not os.path.exists(csv_path):
        print(f"ERROR: CSVファイルが見つかりません: {csv_path}")
        sys.exit(1)

    # 現在のWORKSTYLE行数確認
    current_workstyle = get_workstyle_count(url, token)
    print(f"現在のWORKSTYLE行数: {current_workstyle:,}")

    # 既存WORKSTYLE行を削除
    if current_workstyle > 0:
        print(f"既存WORKSTYLE行を削除中...")
        deleted = delete_workstyle_rows(url, token)
        print(f"削除完了: {deleted:,} 行")

    # CSV読み込み（WORKSTYLEのみ）
    print(f"\nCSV読み込み中: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)

    # 必要なWORKSTYLE row_typeのみフィルタ（db_helper.pyで使用するもののみ）
    needed_row_types = [
        'WORKSTYLE_DISTRIBUTION',
        'WORKSTYLE_AGE_CROSS',
        'WORKSTYLE_GENDER_CROSS',
        'WORKSTYLE_URGENCY',
        'WORKSTYLE_EMPLOYMENT_STATUS',
        'WORKSTYLE_DESIRED_AREA_COUNT'
    ]
    workstyle_df = df[df['row_type'].isin(needed_row_types)].copy()
    total_rows = len(workstyle_df)
    print(f"WORKSTYLE行数: {total_rows:,} (6種類のrow_typeのみ)")

    # row_type別の内訳
    print("\nrow_type別内訳:")
    for rt, cnt in workstyle_df['row_type'].value_counts().items():
        print(f"  {rt}: {cnt:,}")

    if total_rows == 0:
        print("インポートするWORKSTYLEデータがありません")
        return

    # カラムリスト
    columns = list(df.columns)
    print(f"\nカラム数: {len(columns)}")

    # バッチ分割
    batches = [workstyle_df.iloc[i:i+BATCH_SIZE] for i in range(0, total_rows, BATCH_SIZE)]
    total_batches = len(batches)
    print(f"バッチ数: {total_batches} (各{BATCH_SIZE}行)")
    print("-" * 60)

    # 並列インポート
    start_time = time.time()
    completed = 0
    errors_total = 0
    rows_inserted = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for i, batch_df in enumerate(batches):
            future = executor.submit(insert_batch, url, token, batch_df, columns, i)
            futures[future] = i

        for future in as_completed(futures):
            batch_num, inserted, errors, error_msgs = future.result()
            completed += 1
            errors_total += errors
            rows_inserted += inserted - errors

            elapsed = time.time() - start_time
            rows_done = min(completed * BATCH_SIZE, total_rows)

            # 進捗計算
            progress = (rows_done / total_rows) * 100
            rate = rows_done / elapsed if elapsed > 0 else 0
            remaining = (total_rows - rows_done) / rate if rate > 0 else 0

            status = "OK" if errors == 0 else f"ERR({errors})"
            print(f"\r[{completed:4d}/{total_batches}] {progress:5.1f}% | "
                  f"{rate:,.0f} rows/s | ETA {remaining/60:.1f}min | {status}", end="", flush=True)

            if error_msgs:
                print(f"\n  エラー: {error_msgs[0][:100]}")

    # 完了
    elapsed = time.time() - start_time
    final_workstyle = get_workstyle_count(url, token)

    print("\n" + "=" * 60)
    print("インポート完了")
    print(f"  処理時間: {elapsed/60:.1f}分")
    print(f"  処理行数: {total_rows:,}")
    print(f"  処理速度: {total_rows/elapsed:,.0f} 行/秒")
    print(f"  エラー数: {errors_total}")
    print(f"  最終WORKSTYLE行数: {final_workstyle:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
