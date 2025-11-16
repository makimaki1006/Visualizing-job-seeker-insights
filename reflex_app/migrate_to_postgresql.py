"""
SQLite → PostgreSQL移行スクリプト

既存のSQLiteデータベースをPostgreSQLに移行します。
Render等のクラウドデプロイ用。

使用方法:
    # 環境変数を設定してから実行
    set DATABASE_URL=postgresql://user:password@host:port/dbname
    python migrate_to_postgresql.py

前提条件:
    - migrate_csv_to_db.pyを実行してSQLiteデータベースが作成済み
    - psycopg2-binaryがインストール済み (pip install psycopg2-binary)
    - PostgreSQLデータベースが作成済み（Neon/Supabase等）
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List
from database_schema import DATABASE_SCHEMA, get_all_create_table_sqls

try:
    import psycopg2
    import psycopg2.extras
    _HAS_POSTGRES = True
except ImportError:
    print("ERROR: psycopg2が見つかりません。以下を実行してください:")
    print("  pip install psycopg2-binary")
    exit(1)

# データディレクトリ
SQLITE_DB_PATH = Path(__file__).parent / "data" / "job_medley.db"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL環境変数が設定されていません。")
    print("以下のように設定してください:")
    print('  set DATABASE_URL=postgresql://user:password@host:port/dbname')
    exit(1)


def get_sqlite_connection() -> sqlite3.Connection:
    """
    SQLite接続を取得

    Returns:
        sqlite3接続オブジェクト
    """
    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(
            f"SQLiteデータベースが見つかりません: {SQLITE_DB_PATH}\n"
            f"migrate_csv_to_db.py を実行してデータベースを作成してください。"
        )
    return sqlite3.connect(str(SQLITE_DB_PATH))


def get_postgres_connection():
    """
    PostgreSQL接続を取得

    Returns:
        psycopg2接続オブジェクト
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"ERROR: PostgreSQL接続に失敗しました: {e}")
        print(f"DATABASE_URL: {DATABASE_URL[:30]}...")
        exit(1)


def create_postgres_schema(pg_conn) -> None:
    """
    PostgreSQLにスキーマを作成

    Args:
        pg_conn: psycopg2接続オブジェクト
    """
    cursor = pg_conn.cursor()

    # 既存のテーブルを削除（クリーンインストール）
    print("\n既存のテーブルを削除中...")
    for table_name in DATABASE_SCHEMA.keys():
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        except Exception as e:
            print(f"  [WARN] {table_name}: {e}")

    pg_conn.commit()

    # スキーマ適用
    print("\nテーブルを作成中...")
    sqls = get_all_create_table_sqls()

    # PostgreSQL用にSQLを変換
    converted_sqls = []
    for sql in sqls:
        # SQLiteのAUTOINCREMENT → PostgreSQLのSERIAL
        sql = sql.replace("AUTOINCREMENT", "")
        sql = sql.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")

        # SQLiteのBOOLEAN → PostgreSQLのBOOLEAN（変更不要）
        converted_sqls.append(sql)

    for sql in converted_sqls:
        try:
            cursor.execute(sql)
        except Exception as e:
            print(f"  [ERROR] SQL実行エラー: {e}")
            print(f"  SQL: {sql[:100]}...")

    pg_conn.commit()
    print(f"テーブル作成完了: {len(DATABASE_SCHEMA)}個のテーブル")


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    table_name: str
) -> int:
    """
    1つのテーブルをSQLiteからPostgreSQLに移行

    Args:
        sqlite_conn: SQLite接続オブジェクト
        pg_conn: PostgreSQL接続オブジェクト
        table_name: テーブル名

    Returns:
        移行した行数
    """
    # SQLiteからデータを読み込み
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
    except Exception as e:
        print(f"  [SKIP] {table_name}: SQLiteから読み込めません ({e})")
        return 0

    if len(df) == 0:
        print(f"  [SKIP] {table_name}: データなし")
        return 0

    # PostgreSQLにインポート
    try:
        df.to_sql(table_name, pg_conn, if_exists="replace", index=False, method="multi")
        print(f"  [OK] {table_name}: {len(df)}行を移行")
        return len(df)
    except Exception as e:
        print(f"  [ERROR] {table_name}: 移行失敗 ({e})")
        return 0


def migrate_all_tables(
    sqlite_conn: sqlite3.Connection,
    pg_conn
) -> Dict[str, int]:
    """
    全テーブルを移行

    Args:
        sqlite_conn: SQLite接続オブジェクト
        pg_conn: PostgreSQL接続オブジェクト

    Returns:
        テーブル名→移行行数の辞書
    """
    results = {}

    print("\nデータ移行開始...")
    for table_name in DATABASE_SCHEMA.keys():
        row_count = migrate_table(sqlite_conn, pg_conn, table_name)
        results[table_name] = row_count

    return results


def analyze_postgres_database(pg_conn) -> None:
    """
    PostgreSQLデータベースの統計情報を表示

    Args:
        pg_conn: PostgreSQL接続オブジェクト
    """
    print("\n" + "=" * 60)
    print("PostgreSQLデータベース統計")
    print("=" * 60)

    cursor = pg_conn.cursor()

    # テーブルごとの行数
    for table_name in DATABASE_SCHEMA.keys():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"{table_name:40s} : {count:>10,}行")
        except Exception as e:
            print(f"{table_name:40s} : [ERROR] {e}")

    # データベースサイズ（PostgreSQL）
    try:
        cursor.execute("""
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """)
        db_size = cursor.fetchone()[0]
        print(f"\nデータベースサイズ: {db_size}")
    except Exception as e:
        print(f"\nデータベースサイズ取得エラー: {e}")


def verify_postgres_integrity(pg_conn) -> bool:
    """
    PostgreSQLデータ整合性を検証

    Args:
        pg_conn: PostgreSQL接続オブジェクト

    Returns:
        検証成功ならTrue
    """
    print("\n" + "=" * 60)
    print("データ整合性検証")
    print("=" * 60)

    cursor = pg_conn.cursor()
    all_passed = True

    # 1. applicantsテーブルのユニーク性チェック
    cursor.execute("""
        SELECT COUNT(*), COUNT(DISTINCT applicant_id)
        FROM applicants
    """)
    total, unique = cursor.fetchone()
    if total == unique:
        print(f"[OK] applicants.applicant_id: ユニーク ({unique}件)")
    else:
        print(f"[NG] applicants.applicant_id: 重複あり (全{total}件, ユニーク{unique}件)")
        all_passed = False

    # 2. persona_summaryテーブルのユニーク性チェック
    cursor.execute("""
        SELECT COUNT(*), COUNT(DISTINCT persona_name)
        FROM persona_summary
    """)
    total, unique = cursor.fetchone()
    if total == unique:
        print(f"[OK] persona_summary.persona_name: ユニーク ({unique}件)")
    else:
        print(f"[NG] persona_summary.persona_name: 重複あり (全{total}件, ユニーク{unique}件)")
        all_passed = False

    # 3. 外部キー整合性チェック（desired_work → applicants）
    cursor.execute("""
        SELECT COUNT(*)
        FROM desired_work dw
        LEFT JOIN applicants a ON dw.applicant_id = a.applicant_id
        WHERE a.applicant_id IS NULL
    """)
    orphaned = cursor.fetchone()[0]
    if orphaned == 0:
        print(f"[OK] desired_work -> applicants: 外部キー整合性OK")
    else:
        print(f"[NG] desired_work -> applicants: 孤立レコード {orphaned}件")
        all_passed = False

    if all_passed:
        print("\n[OK] データ整合性検証: すべて成功")
    else:
        print("\n[NG] データ整合性検証: 一部失敗")

    return all_passed


def compare_databases(sqlite_conn: sqlite3.Connection, pg_conn) -> None:
    """
    SQLiteとPostgreSQLのデータ件数を比較

    Args:
        sqlite_conn: SQLite接続オブジェクト
        pg_conn: PostgreSQL接続オブジェクト
    """
    print("\n" + "=" * 60)
    print("データ件数比較（SQLite vs PostgreSQL）")
    print("=" * 60)

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    all_matched = True

    for table_name in DATABASE_SCHEMA.keys():
        try:
            # SQLiteの件数
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_count = sqlite_cursor.fetchone()[0]

            # PostgreSQLの件数
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            pg_count = pg_cursor.fetchone()[0]

            status = "[OK]" if sqlite_count == pg_count else "[NG]"
            print(f"{status} {table_name:40s} : SQLite={sqlite_count:>6,}件 | PostgreSQL={pg_count:>6,}件")

            if sqlite_count != pg_count:
                all_matched = False

        except Exception as e:
            print(f"[ERROR] {table_name}: {e}")
            all_matched = False

    if all_matched:
        print("\n[OK] すべてのテーブルが一致しました")
    else:
        print("\n[NG] 一部のテーブルで件数が異なります")


def main():
    """メイン処理"""
    print("=" * 60)
    print("SQLite → PostgreSQL移行スクリプト")
    print("=" * 60)
    print()

    # SQLite接続
    print(f"SQLiteデータベース: {SQLITE_DB_PATH}")
    sqlite_conn = get_sqlite_connection()

    # PostgreSQL接続
    print(f"PostgreSQLデータベース: {DATABASE_URL[:50]}...")
    pg_conn = get_postgres_connection()

    # PostgreSQLスキーマ作成
    create_postgres_schema(pg_conn)

    # データ移行
    results = migrate_all_tables(sqlite_conn, pg_conn)

    # PostgreSQL統計情報
    analyze_postgres_database(pg_conn)

    # データ整合性検証
    verify_postgres_integrity(pg_conn)

    # データ件数比較
    compare_databases(sqlite_conn, pg_conn)

    # 接続クローズ
    sqlite_conn.close()
    pg_conn.close()

    print("\n" + "=" * 60)
    print("移行完了！")
    print("=" * 60)
    print(f"総行数: {sum(results.values()):,}行")
    print(f"総テーブル数: {len([r for r in results.values() if r > 0])}テーブル")
    print()
    print("次のステップ:")
    print("1. Reflexアプリの環境変数を設定:")
    print(f'   set DATABASE_URL={DATABASE_URL[:50]}...')
    print("2. db_helper.pyが自動的にPostgreSQLを使用します")


if __name__ == "__main__":
    main()
