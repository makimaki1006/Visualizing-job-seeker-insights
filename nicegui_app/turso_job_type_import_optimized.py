#!/usr/bin/env python3
"""
職種別Tursoインポートスクリプト（最適化版）

最適化内容:
- 複数行VALUES句による一括INSERT（1文で100行挿入）
- BATCH_SIZE: 2,000 → 5,000
- MAX_WORKERS: 3 → 6
- 理論性能: 300-600 rows/sec（従来比 5-10倍）

使用方法:
    python turso_job_type_import_optimized.py --job_type "看護師" --csv_path "path/to/MapComplete.csv"
"""

import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import pandas as pd

# 最適化設定
BATCH_SIZE = 10000          # 1バッチの総行数（5000→10000: 2倍）
ROWS_PER_INSERT = 200       # 1つのINSERT文で挿入する行数（100→200: 2倍）
MAX_WORKERS = 8             # 並列ワーカー数（6→8: 適度に増加）
MAX_RETRIES = 3             # リトライ回数
REQUEST_TIMEOUT = 300       # リクエストタイムアウト（秒）

# 職種とプレフィックスのマッピング
JOB_TYPE_PREFIX_MAP = {
    "介護職": "",
    "看護師": "NS",
    "保育士": "CH",
    "生活相談員": "SW",
    "栄養士": "DT",
    "管理栄養士": "DT",
    "栄養士、管理栄養士": "DT",
    "理学療法士": "PT",
    "作業療法士": "OT",
    "ケアマネジャー": "CM",
    "サービス管理責任者": "SM",
    "サービス提供責任者": "SP",
    "学童支援": "AS",
    "調理師、調理スタッフ": "CK",
}

# 数値カラムのセット（高速ルックアップ用）
NUMERIC_COLS = frozenset([
    'desired_count', 'lat', 'lng', 'female_ratio', 'top_age_ratio',
    'avg_desired_areas', 'persona_count', 'persona_percentage',
    'supply_count', 'demand_count', 'gap', 'gap_ratio', 'rarity_score',
    'competition_score', 'flow_in', 'flow_out', 'net_flow',
    'latitude', 'longitude', 'avg_age', 'male_count', 'female_count',
    'applicant_count', 'avg_qualifications', 'count',
    'national_license_rate', 'total_in_municipality', 'market_share_pct',
    'avg_mobility_score', 'avg_urgency_score', 'inflow', 'outflow',
    'demand_supply_ratio', 'total_applicants',
    'male_ratio', 'top_employment_ratio', 'avg_qualification_count',
    'retention_rate', 'avg_reference_distance_km', 'median_distance_km',
    'mode_distance_km', 'min_distance_km', 'max_distance_km',
    'std_distance_km', 'q25_distance_km', 'q75_distance_km',
    'percentage', 'avg_desired_area_count'
])

INTEGER_COLS = frozenset(['id', 'desired_count'])


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


def get_current_count(url: str, token: str, job_type: str = None) -> int:
    """現在の行数を取得"""
    if job_type:
        result = execute_sql(url, token,
            "SELECT COUNT(*) FROM job_seeker_data WHERE job_type = ?",
            [{'type': 'text', 'value': job_type}])
    else:
        result = execute_sql(url, token, 'SELECT COUNT(*) FROM job_seeker_data')
    return int(result['results'][0]['response']['result']['rows'][0][0]['value'])


def get_existing_ids_for_job_type(url: str, token: str, job_type: str) -> set:
    """指定職種の既存IDセットを取得"""
    print(f"既存ID確認中 (job_type: {job_type})...")

    result = execute_sql(url, token,
        "SELECT DISTINCT id FROM job_seeker_data WHERE job_type = ?",
        [{'type': 'text', 'value': job_type}])

    rows = result['results'][0]['response']['result'].get('rows', [])
    ids = set()
    for row in rows:
        if row and row[0]:
            ids.add(str(row[0].get('value', '')))
    print(f"既存ID数: {len(ids)}")
    return ids


def convert_value(val, col_name: str):
    """値をTurso API用に変換（最適化版）"""
    # NULL判定
    if pd.isna(val) or val is None or val == '' or str(val).lower() == 'nan':
        return {'type': 'null'}

    # 整数カラム
    if col_name in INTEGER_COLS:
        try:
            return {'type': 'integer', 'value': str(int(float(val)))}
        except (ValueError, TypeError):
            return {'type': 'null'}

    # 数値カラム（REAL型）
    if col_name in NUMERIC_COLS:
        try:
            return {'type': 'float', 'value': float(val)}
        except (ValueError, TypeError):
            return {'type': 'null'}

    # テキストカラム
    return {'type': 'text', 'value': str(val)}


def build_multi_row_insert(columns: list, rows_data: list) -> tuple:
    """
    複数行VALUES句を持つINSERT文を構築

    Returns:
        (sql, args): SQL文とパラメータリスト
    """
    col_names = ', '.join(columns)
    num_cols = len(columns)

    # 各行のプレースホルダー: (?, ?, ?, ...)
    row_placeholder = '(' + ', '.join(['?' for _ in range(num_cols)]) + ')'
    # 全行のプレースホルダー: (?, ?, ...), (?, ?, ...), ...
    all_placeholders = ', '.join([row_placeholder for _ in rows_data])

    sql = f"INSERT OR REPLACE INTO job_seeker_data ({col_names}) VALUES {all_placeholders}"

    # パラメータをフラット化
    args = []
    for row in rows_data:
        for col in columns:
            args.append(convert_value(row.get(col), col))

    return sql, args


def insert_batch_optimized(url: str, token: str, batch_df: pd.DataFrame,
                           columns: list, batch_num: int) -> tuple:
    """
    最適化バッチ挿入: 複数行VALUES句を使用

    1バッチ(5000行)を、100行ずつの複数INSERT文に分割
    → 50個のINSERT文を1つのパイプラインリクエストで送信
    """
    rows_data = batch_df.to_dict('records')
    total_rows = len(rows_data)

    # 100行ずつのチャンクに分割
    chunks = [rows_data[i:i+ROWS_PER_INSERT] for i in range(0, total_rows, ROWS_PER_INSERT)]

    # 各チャンクのINSERT文を構築
    requests = []
    for chunk in chunks:
        sql, args = build_multi_row_insert(columns, chunk)
        requests.append({
            'type': 'execute',
            'stmt': {'sql': sql, 'args': args}
        })

    # リトライ付きで実行
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                f'{url}/v2/pipeline',
                data=json.dumps({'requests': requests}).encode(),
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            )
            resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
            result = json.loads(resp.read().decode())

            # エラーチェック
            errors = []
            for i, r in enumerate(result.get('results', [])):
                if r.get('type') == 'error':
                    errors.append(f"Chunk {i}: {r.get('error', {}).get('message', 'Unknown error')}")

            if errors:
                return (batch_num, total_rows, len(errors) * ROWS_PER_INSERT, errors[:3])

            return (batch_num, total_rows, 0, None)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if hasattr(e, 'read') else str(e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return (batch_num, total_rows, total_rows, [f"HTTP {e.code}: {error_body[:200]}"])

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            return (batch_num, total_rows, total_rows, [str(e)[:200]])

    return (batch_num, 0, total_rows, ["Max retries exceeded"])


def main():
    parser = argparse.ArgumentParser(description='職種別Tursoインポート（最適化版）')
    parser.add_argument('--job_type', type=str, required=True,
                        help='職種名 (例: 看護師, 保育士)')
    parser.add_argument('--csv_path', type=str, required=True,
                        help='インポートするCSVファイルのパス')
    parser.add_argument('--dry_run', action='store_true',
                        help='ドライラン（実際にインポートしない）')
    parser.add_argument('--batch_size', type=int, default=BATCH_SIZE,
                        help=f'バッチサイズ（デフォルト: {BATCH_SIZE}）')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS,
                        help=f'並列ワーカー数（デフォルト: {MAX_WORKERS}）')
    args = parser.parse_args()

    job_type = args.job_type
    csv_path = args.csv_path
    batch_size = args.batch_size
    workers = args.workers

    print("=" * 60)
    print(f"職種別Tursoインポート（最適化版）")
    print(f"  職種: {job_type}")
    print(f"  CSVパス: {csv_path}")
    print(f"  バッチサイズ: {batch_size:,}")
    print(f"  並列ワーカー: {workers}")
    print(f"  1INSERT当たり行数: {ROWS_PER_INSERT}")
    print(f"  ドライラン: {args.dry_run}")
    print("=" * 60)

    # 設定取得
    url, token = get_turso_config()
    if not url or not token:
        print("ERROR: Turso設定が見つかりません")
        sys.exit(1)

    # CSV読み込み
    if not os.path.exists(csv_path):
        print(f"ERROR: CSVファイルが見つかりません: {csv_path}")
        sys.exit(1)

    print(f"\nCSV読み込み中: {csv_path}")
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    total_rows = len(df)
    print(f"CSV行数（読み込み時）: {total_rows:,}")

    # 重複除去
    print("\n重複除去処理中...")
    df_dedup = df.drop_duplicates()
    dup_count = total_rows - len(df_dedup)
    if dup_count > 0:
        print(f"[WARNING] 重複行を削除: {dup_count:,} 行")
    df = df_dedup
    total_rows = len(df)
    print(f"CSV行数（重複除去後）: {total_rows:,}")

    # job_type列を追加
    if 'job_type' not in df.columns:
        print(f"\njob_type列を追加: '{job_type}'")
        df['job_type'] = job_type
    else:
        print(f"\njob_type列は既に存在: '{df['job_type'].iloc[0]}'")

    # ID列の確認 - プレフィックス付きIDを生成
    prefix = JOB_TYPE_PREFIX_MAP.get(job_type, "")
    if not prefix:
        print(f"[WARNING] 職種 '{job_type}' のプレフィックスが定義されていません")
        # 職種名の先頭2文字をプレフィックスとして使用
        prefix = job_type[:2].upper() if job_type else "XX"

    if 'id' not in df.columns:
        print(f"ID列がないため生成します（プレフィックス: {prefix}）")
        df['id'] = [f"{prefix}_{i}" for i in range(1, len(df) + 1)]
    else:
        # 既存IDにプレフィックスを追加（まだ付いていない場合）
        df['id'] = df['id'].astype(str)
        if not df['id'].iloc[0].startswith(prefix):
            print(f"既存IDにプレフィックス追加: {prefix}")
            df['id'] = df['id'].apply(lambda x: f"{prefix}_{x}")

    df['id'] = df['id'].astype(str)
    # サンプルID確認
    print(f"\nサンプルID (先頭5件):")
    for i, id_val in enumerate(df['id'].head(5)):
        print(f"  {i+1}: {id_val}")

    # 現在の状況確認
    current_count = get_current_count(url, token, job_type)
    print(f"\nTurso現在行数 (job_type='{job_type}'): {current_count:,}")

    total_count = get_current_count(url, token)
    print(f"Turso総行数: {total_count:,}")

    # 既存IDを取得してスキップ
    existing_ids = get_existing_ids_for_job_type(url, token, job_type)

    # 新規行のみフィルタ
    new_df = df[~df['id'].isin(existing_ids)]
    new_rows = len(new_df)
    print(f"\n新規挿入対象: {new_rows:,} 行")

    if new_rows == 0:
        print("すべてのデータがインポート済みです")
        return

    if args.dry_run:
        print("\n[ドライラン] 実際のインポートは行いません")
        print(f"インポート予定: {new_rows:,} 行")
        estimated_time = new_rows / 400  # 400 rows/sec想定
        print(f"推定所要時間: {estimated_time/60:.1f}分（400 rows/sec想定）")
        return

    # カラムリスト
    columns = list(df.columns)
    print(f"カラム数: {len(columns)}")

    # バッチ分割
    batches = [new_df.iloc[i:i+batch_size] for i in range(0, new_rows, batch_size)]
    total_batches = len(batches)
    print(f"バッチ数: {total_batches} (各{batch_size:,}行)")
    print(f"1バッチあたりINSERT文数: {batch_size // ROWS_PER_INSERT}")
    print("-" * 60)

    # 並列インポート
    start_time = time.time()
    completed = 0
    errors_total = 0
    rows_imported = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, batch_df in enumerate(batches):
            future = executor.submit(
                insert_batch_optimized, url, token, batch_df, columns, i
            )
            futures[future] = i

        for future in as_completed(futures):
            batch_num, inserted, errors, error_msgs = future.result()
            completed += 1
            errors_total += errors
            rows_imported += inserted - errors

            elapsed = time.time() - start_time
            rows_done = min(completed * batch_size, new_rows)

            # 進捗計算
            progress = (rows_done / new_rows) * 100
            rate = rows_imported / elapsed if elapsed > 0 else 0
            remaining = (new_rows - rows_done) / rate if rate > 0 else 0

            status = "OK" if errors == 0 else f"ERR({errors})"
            print(f"\r[{completed:4d}/{total_batches}] {progress:5.1f}% | "
                  f"{rate:,.0f} rows/sec | ETA {remaining/60:.1f}min | {status}", end="", flush=True)

            if error_msgs:
                print(f"\n  Error: {error_msgs[0][:100]}")

    # 完了
    elapsed = time.time() - start_time
    final_count = get_current_count(url, token, job_type)
    total_final = get_current_count(url, token)

    print("\n" + "=" * 60)
    print("インポート完了（最適化版）")
    print(f"  職種: {job_type}")
    print(f"  処理時間: {elapsed/60:.1f}分")
    print(f"  処理行数: {new_rows:,}")
    print(f"  処理速度: {new_rows/elapsed:,.0f} 行/秒")
    print(f"  エラー数: {errors_total}")
    print(f"  職種別行数: {final_count:,}")
    print(f"  総行数: {total_final:,}")
    print("=" * 60)

    # パフォーマンス比較
    old_rate = 62  # 従来スクリプトの実測値
    new_rate = new_rows / elapsed if elapsed > 0 else 0
    improvement = new_rate / old_rate if old_rate > 0 else 0
    print(f"\n📈 パフォーマンス比較:")
    print(f"   従来: {old_rate} rows/sec")
    print(f"   今回: {new_rate:,.0f} rows/sec")
    print(f"   改善: {improvement:.1f}倍")


if __name__ == "__main__":
    main()
