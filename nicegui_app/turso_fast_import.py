#!/usr/bin/env python3
"""
高速Tursoインポートスクリプト
- バッチサイズ: 2000行（HTTP APIの限界付近）
- 並列リクエスト: 3並列
- 進捗表示: リアルタイム
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
BATCH_SIZE = 2000  # 1バッチあたりの行数（大幅増加）
MAX_WORKERS = 3    # 並列リクエスト数
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

def get_current_count(url: str, token: str) -> int:
    """現在の行数を取得"""
    result = execute_sql(url, token, 'SELECT COUNT(*) FROM job_seeker_data')
    return int(result['results'][0]['response']['result']['rows'][0][0]['value'])

def get_existing_ids(url: str, token: str) -> set:
    """既存のIDセットを取得（高速化のため最小限のクエリ）"""
    print("既存データのID確認中...")
    result = execute_sql(url, token, 'SELECT DISTINCT id FROM job_seeker_data')
    rows = result['results'][0]['response']['result'].get('rows', [])
    ids = set()
    for row in rows:
        if row and row[0]:
            ids.add(str(row[0].get('value', '')))
    print(f"既存ID数: {len(ids)}")
    return ids

def convert_value(val, col_name: str):
    """値をTurso API用に変換"""
    if pd.isna(val) or val is None or val == '' or str(val).lower() == 'nan':
        return {'type': 'null'}

    # 数値カラム
    numeric_cols = [
        'desired_count', 'lat', 'lng', 'female_ratio', 'top_age_ratio',
        'avg_desired_areas', 'persona_count', 'persona_percentage',
        'supply_count', 'demand_count', 'gap', 'gap_ratio', 'rarity_score',
        'competition_score', 'flow_in', 'flow_out', 'net_flow'
    ]

    if col_name in numeric_cols:
        try:
            float_val = float(val)
            if col_name == 'desired_count':
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
    sql = f"INSERT OR REPLACE INTO job_seeker_data ({col_names}) VALUES ({placeholders})"

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
    print("高速Tursoインポート開始")
    print("=" * 60)

    # 設定取得
    url, token = get_turso_config()
    if not url or not token:
        print("ERROR: Turso設定が見つかりません")
        sys.exit(1)

    # CSVパス
    csv_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts\data\output_v2\mapcomplete_complete_sheets\MapComplete_Complete_All_FIXED.csv"

    if not os.path.exists(csv_path):
        print(f"ERROR: CSVファイルが見つかりません: {csv_path}")
        sys.exit(1)

    # CSV読み込み
    print(f"CSV読み込み中: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    total_rows = len(df)
    print(f"CSV行数（読み込み時）: {total_rows:,}")

    # 重複除去（必須: DATA_IMPORT_RULES.md参照）
    print("\n重複除去処理中...")
    df_dedup = df.drop_duplicates()
    dup_count = total_rows - len(df_dedup)
    if dup_count > 0:
        print(f"[WARNING] 重複行を削除: {dup_count:,} 行 ({dup_count/total_rows*100:.1f}%)")
        # row_type別の重複状況
        print("\nrow_type別重複状況:")
        for rt in df['row_type'].unique():
            orig = len(df[df['row_type'] == rt])
            dedup = len(df_dedup[df_dedup['row_type'] == rt])
            if orig != dedup:
                print(f"  {rt}: {orig:,} -> {dedup:,} (削除: {orig-dedup:,})")
    else:
        print("[OK] 重複なし")

    df = df_dedup
    total_rows = len(df)
    print(f"\nCSV行数（重複除去後）: {total_rows:,}")

    # 現在の状況確認
    current_count = get_current_count(url, token)
    print(f"Turso現在行数: {current_count:,}")

    # 既存IDを取得してスキップ
    existing_ids = get_existing_ids(url, token)

    # IDカラムを作成（なければ行番号）
    if 'id' not in df.columns:
        df['id'] = range(1, len(df) + 1)
    df['id'] = df['id'].astype(str)

    # 新規行のみフィルタ
    new_df = df[~df['id'].isin(existing_ids)]
    new_rows = len(new_df)
    print(f"新規挿入対象: {new_rows:,} 行")

    if new_rows == 0:
        print("すべてのデータがインポート済みです")
        return

    # カラムリスト
    columns = list(df.columns)
    print(f"カラム数: {len(columns)}")

    # バッチ分割
    batches = [new_df.iloc[i:i+BATCH_SIZE] for i in range(0, new_rows, BATCH_SIZE)]
    total_batches = len(batches)
    print(f"バッチ数: {total_batches} (各{BATCH_SIZE}行)")
    print("-" * 60)

    # 並列インポート
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
            rows_done = completed * BATCH_SIZE
            if rows_done > new_rows:
                rows_done = new_rows

            # 進捗計算
            progress = (rows_done / new_rows) * 100
            rate = rows_done / elapsed if elapsed > 0 else 0
            remaining = (new_rows - rows_done) / rate if rate > 0 else 0

            status = "✓" if errors == 0 else f"✗({errors})"
            print(f"\r[{completed:4d}/{total_batches}] {progress:5.1f}% | "
                  f"{rate:,.0f} 行/秒 | 残り {remaining/60:.1f}分 | {status}", end="", flush=True)

            if error_msgs:
                print(f"\n  エラー: {error_msgs[0][:100]}")

    # 完了
    elapsed = time.time() - start_time
    final_count = get_current_count(url, token)

    print("\n" + "=" * 60)
    print("インポート完了")
    print(f"  処理時間: {elapsed/60:.1f}分")
    print(f"  処理行数: {new_rows:,}")
    print(f"  処理速度: {new_rows/elapsed:,.0f} 行/秒")
    print(f"  エラー数: {errors_total}")
    print(f"  最終行数: {final_count:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
