# -*- coding: utf-8 -*-
"""求人データCSVをTursoDB job_openingsテーブルにインポートするスクリプト

使い方:
    # 件数確認のみ（DB操作なし）
    python scripts/import_job_openings.py --dry-run

    # インポート実行
    python scripts/import_job_openings.py

    # CSVパスを指定
    python scripts/import_job_openings.py --csv path/to/file.csv

注意: Claudeはこのスクリプトを実行しない。ユーザーが手動で実行すること。
"""

import os
import sys
import csv
import argparse
from pathlib import Path

# .env読み込み
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env.production"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()
except ImportError:
    pass

try:
    import httpx
except ImportError:
    print("[ERROR] httpx が必要です: pip install httpx")
    sys.exit(1)

TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

if TURSO_DATABASE_URL.startswith("libsql://"):
    TURSO_DATABASE_URL = TURSO_DATABASE_URL.replace("libsql://", "https://")

# デフォルトCSVパス
DEFAULT_CSV_PATH = Path(__file__).parent.parent.parent / "python_scripts" / "data" / "external" / "job_openings" / "job_openings_2026-01.csv"

# CSV側の職種名 → DB側の職種名マッピング
JOB_TYPE_MAP = {
    "看護師/准看護師": "看護師",
    "介護職/ヘルパー": "介護職",
    "調理師/調理スタッフ": "調理師、調理スタッフ",
    "管理栄養士/栄養士": "栄養士",
    # 以下は一致しているもの（念のため明示）
    "保育士": "保育士",
    "生活相談員": "生活相談員",
    "理学療法士": "理学療法士",
    "作業療法士": "作業療法士",
    "ケアマネジャー": "ケアマネジャー",
    "サービス管理責任者": "サービス管理責任者",
    "サービス提供責任者": "サービス提供責任者",
    "歯科衛生士": "歯科衛生士",
}

# テーブル定義
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS job_openings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prefecture TEXT NOT NULL,
    municipality TEXT NOT NULL,
    job_type TEXT NOT NULL,
    job_count INTEGER NOT NULL,
    source_job_type TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(prefecture, municipality, job_type)
)
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_jo_job_type ON job_openings(job_type)",
    "CREATE INDEX IF NOT EXISTS idx_jo_pref ON job_openings(prefecture)",
]

BATCH_SIZE = 500


def turso_execute(sql: str, params: list = None) -> dict:
    """Turso HTTP APIでSQL実行"""
    http_url = TURSO_DATABASE_URL
    if not http_url.endswith("/"):
        http_url += "/"
    url = http_url + "v2/pipeline"

    stmt = {"type": "execute", "stmt": {"sql": sql}}
    if params:
        stmt["stmt"]["args"] = [
            {"type": "text", "value": str(v)} if isinstance(v, str)
            else {"type": "integer", "value": str(v)}
            for v in params
        ]

    payload = {"requests": [stmt, {"type": "close"}]}
    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def turso_batch_execute(statements: list) -> dict:
    """複数SQLをバッチ実行"""
    http_url = TURSO_DATABASE_URL
    if not http_url.endswith("/"):
        http_url += "/"
    url = http_url + "v2/pipeline"

    requests = []
    for sql, params in statements:
        stmt = {"type": "execute", "stmt": {"sql": sql}}
        if params:
            stmt["stmt"]["args"] = [
                {"type": "text", "value": str(v)} if isinstance(v, str)
                else {"type": "integer", "value": str(v)}
                for v in params
            ]
        requests.append(stmt)
    requests.append({"type": "close"})

    payload = {"requests": requests}
    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    resp = httpx.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def read_csv(csv_path: Path) -> list[dict]:
    """CSVを読み込んでリストで返す（都道府県合計行を除外、職種名をDB名に変換）"""
    if not csv_path.exists():
        print(f"[ERROR] CSVが見つかりません: {csv_path}")
        sys.exit(1)

    rows = []
    skipped_types = set()
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 都道府県合計行（municipality空欄）はスキップ
            municipality = row.get("municipality", "").strip()
            if not municipality:
                continue

            try:
                count = int(row["job_count"])
            except (ValueError, KeyError):
                continue

            # 職種名をDB側にマッピング
            source_job_type = row["job_type"].strip()
            db_job_type = JOB_TYPE_MAP.get(source_job_type)
            if db_job_type is None:
                skipped_types.add(source_job_type)
                continue

            rows.append({
                "prefecture": row["prefecture"].strip(),
                "municipality": municipality,
                "job_type": db_job_type,
                "source_job_type": source_job_type,
                "job_count": count,
            })

    if skipped_types:
        print(f"[WARNING] マッピング未定義の職種をスキップ: {skipped_types}")

    return rows


def main():
    parser = argparse.ArgumentParser(description="求人データCSVをTursoにインポート")
    parser.add_argument("--dry-run", action="store_true", help="件数確認のみ（DB操作なし）")
    parser.add_argument("--csv", type=str, default=None, help="CSVファイルパス（省略時はデフォルト）")
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else DEFAULT_CSV_PATH

    if not args.dry_run and (not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN):
        print("[ERROR] TURSO_DATABASE_URL / TURSO_AUTH_TOKEN が未設定です")
        sys.exit(1)

    # CSV読み込み
    rows = read_csv(csv_path)
    job_types = sorted(set(r["job_type"] for r in rows))
    prefectures = sorted(set(r["prefecture"] for r in rows))

    print(f"[CSV] ファイル: {csv_path}")
    print(f"[CSV] 総行数: {len(rows):,}（都道府県合計行は除外済み）")
    print(f"[CSV] 職種数: {len(job_types)}")
    print(f"[CSV] 都道府県数: {len(prefectures)}")
    print()

    # 職種別件数
    print(f"  {'DB職種名':<24} {'CSV職種名':<24} {'行数':>8} {'求人計':>10}")
    print(f"  {'-'*24} {'-'*24} {'-'*8} {'-'*10}")
    for jt in job_types:
        jt_rows = [r for r in rows if r["job_type"] == jt]
        total_count = sum(r["job_count"] for r in jt_rows)
        source = jt_rows[0]["source_job_type"] if jt_rows else ""
        print(f"  {jt:<24} {source:<24} {len(jt_rows):>8,} {total_count:>10,}")

    if args.dry_run:
        print("\n[DRY-RUN] DB操作は行いません")
        return

    print("\n[DB] テーブル作成...")
    turso_execute(CREATE_TABLE_SQL)
    for idx_sql in CREATE_INDEX_SQL:
        turso_execute(idx_sql)
    print("[DB] テーブル作成完了")

    # 既存データ削除
    print("[DB] 既存データ削除...")
    turso_execute("DELETE FROM job_openings")
    print("[DB] 既存データ削除完了")

    # バッチINSERT
    insert_sql = (
        "INSERT INTO job_openings (prefecture, municipality, job_type, job_count, source_job_type) "
        "VALUES (?, ?, ?, ?, ?)"
    )
    total_inserted = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        statements = [
            (insert_sql, [r["prefecture"], r["municipality"], r["job_type"], r["job_count"], r["source_job_type"]])
            for r in batch
        ]
        turso_batch_execute(statements)
        total_inserted += len(batch)
        print(f"  {total_inserted:,} / {len(rows):,} 行挿入済み")

    print(f"\n[完了] {total_inserted:,}行をインポートしました")

    # 検証
    print("\n[検証] インポート結果確認...")
    result = turso_execute("SELECT job_type, COUNT(*) as cnt, SUM(job_count) as total FROM job_openings GROUP BY job_type ORDER BY job_type")
    resp_results = result.get("results", [])
    if resp_results:
        res = resp_results[0].get("response", {}).get("result", {})
        cols = [c["name"] for c in res.get("cols", [])]
        db_rows = res.get("rows", [])
        if cols and db_rows:
            print(f"  {'職種':<24} {'行数':>8} {'求人計':>10}")
            print(f"  {'-'*24} {'-'*8} {'-'*10}")
            for row in db_rows:
                vals = [c.get("value", "") for c in row]
                print(f"  {vals[0]:<24} {vals[1]:>8} {vals[2]:>10}")


if __name__ == "__main__":
    main()
