# -*- coding: utf-8 -*-
"""
ハイブリッドデータベースアクセスヘルパー（Turso + SQLite + PostgreSQL対応）

DashboardStateでのデータベースアクセスを簡潔にするヘルパー関数群。
環境変数で自動切り替え：
- TURSO_DATABASE_URL設定あり → Turso使用
- DATABASE_URL設定あり → PostgreSQL使用
- どちらも未設定 → SQLite使用
"""

import os
import sqlite3
import asyncio
import pandas as pd
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env ファイルを読み込み
load_dotenv()

# Turso環境変数
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# PostgreSQL環境変数
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLiteパス（ローカル開発用）
DB_PATH = Path(__file__).parent / "data" / "job_medley.db"

# データディレクトリ自動作成（SQLiteフォールバック対策）
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Turso libsql-clientインポート
_HAS_TURSO = False
if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN:
    try:
        import libsql_client
        _HAS_TURSO = True
        # libsql:// を https:// に変換
        if TURSO_DATABASE_URL.startswith('libsql://'):
            TURSO_DATABASE_URL = TURSO_DATABASE_URL.replace('libsql://', 'https://')
    except ImportError:
        print("WARNING: libsql-client not installed. Install with: pip install libsql-client")

# PostgreSQL接続用（必要な場合のみimport）
_HAS_POSTGRES = False
if DATABASE_URL and not _HAS_TURSO:
    try:
        import psycopg2
        import psycopg2.extras
        _HAS_POSTGRES = True
    except ImportError:
        print("WARNING: psycopg2 not installed. Install with: pip install psycopg2-binary")

# キャッシュ設定（Turso用）
_cache: dict = {}
_cache_time: dict = {}
_max_cache_items = 50
_ttl_minutes = 30


def get_db_type() -> str:
    """使用中のデータベースタイプを取得"""
    if _HAS_TURSO:
        return "turso"
    elif DATABASE_URL and _HAS_POSTGRES:
        return "postgresql"
    else:
        return "sqlite"


def get_connection() -> Union[sqlite3.Connection, "psycopg2.extensions.connection", object]:
    """データベース接続を取得（環境変数で自動切り替え）"""
    if _HAS_TURSO:
        # Tursoはasyncベースなので、ダミー接続を返す
        class TursoDummyConnection:
            def close(self):
                pass
        return TursoDummyConnection()
    elif DATABASE_URL and _HAS_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"データベースファイルが見つかりません: {DB_PATH}\n"
                f"migrate_csv_to_db.py を実行してデータベースを作成してください。"
            )
        return sqlite3.connect(str(DB_PATH))


async def _turso_async_query(sql: str, params: list = None) -> tuple:
    """Turso非同期クエリ実行"""
    async with libsql_client.create_client(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    ) as client:
        if params:
            result = await client.execute(sql, params)
        else:
            result = await client.execute(sql)
        return result.rows, result.columns


def _convert_sql_placeholders(sql: str, db_type: str) -> str:
    """SQLプレースホルダーをDB種別に応じて変換"""
    if db_type == "postgresql":
        return sql.replace("?", "%s")
    return sql


def query_df(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """SQLクエリを実行してDataFrameとして取得（全DB対応）"""
    db_type = get_db_type()

    if db_type == "turso":
        # Turso用非同期クエリ
        try:
            params_list = list(params) if params else None

            # 既存のイベントループがあるかチェック（Reflex対応）
            try:
                loop = asyncio.get_running_loop()
                # 既存ループがある場合は新しいスレッドで実行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(_turso_async_query(sql, params_list))
                    )
                    rows, columns = future.result(timeout=30)
            except RuntimeError:
                # 既存ループがない場合は直接実行
                rows, columns = asyncio.run(_turso_async_query(sql, params_list))

            if not rows:
                return pd.DataFrame()

            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            print(f"[ERROR] Turso query failed: {e}")
            return pd.DataFrame()

    else:
        # SQLite/PostgreSQL用
        conn = get_connection()
        try:
            converted_sql = _convert_sql_placeholders(sql, db_type)
            if params:
                df = pd.read_sql_query(converted_sql, conn, params=params)
            else:
                df = pd.read_sql_query(converted_sql, conn)
            return df
        finally:
            conn.close()


def _get_cached(key: str):
    """キャッシュからデータを取得"""
    if key not in _cache:
        return None
    elapsed = datetime.now() - _cache_time[key]
    if elapsed > timedelta(minutes=_ttl_minutes):
        del _cache[key]
        del _cache_time[key]
        return None
    return _cache[key]


def _set_cache(key: str, data):
    """キャッシュにデータを保存"""
    if len(_cache) >= _max_cache_items:
        oldest = min(_cache_time, key=_cache_time.get)
        del _cache[oldest]
        del _cache_time[oldest]
    _cache[key] = data
    _cache_time[key] = datetime.now()


def clear_cache():
    """キャッシュをクリア"""
    global _cache, _cache_time
    _cache = {}
    _cache_time = {}


def get_table(table_name: str) -> pd.DataFrame:
    """テーブル全体をDataFrameとして取得"""
    return query_df(f"SELECT * FROM {table_name}")


def get_all_data() -> pd.DataFrame:
    """Turso job_seeker_data テーブルから全データを取得（キャッシュ対応）"""
    cache_key = "ALL_DATA"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if _HAS_TURSO:
        df = query_df("SELECT * FROM job_seeker_data")
    else:
        df = query_df("SELECT * FROM mapcomplete_raw")

    _set_cache(cache_key, df)
    return df


def get_prefectures() -> list:
    """都道府県一覧を取得"""
    if _HAS_TURSO:
        df = query_df("SELECT DISTINCT prefecture FROM job_seeker_data ORDER BY prefecture")
        if df.empty:
            return []
        return df['prefecture'].tolist()
    else:
        return get_unique_values("applicants", "residence_prefecture")


def get_municipalities(prefecture: str) -> list:
    """指定都道府県の市区町村一覧を取得"""
    if _HAS_TURSO:
        df = query_df(
            "SELECT DISTINCT municipality FROM job_seeker_data WHERE prefecture = ? AND municipality IS NOT NULL ORDER BY municipality",
            (prefecture,)
        )
        if df.empty:
            return []
        return df['municipality'].tolist()
    else:
        sql = """
            SELECT DISTINCT residence_municipality
            FROM applicants
            WHERE residence_prefecture = ?
            ORDER BY residence_municipality
        """
        df = query_df(sql, (prefecture,))
        return df["residence_municipality"].tolist()


def query_municipality(prefecture: str, municipality: str = None) -> pd.DataFrame:
    """市区町村単位でデータを取得（キャッシュ対応、Turso専用）"""
    cache_key = f"{prefecture}_{municipality or 'ALL'}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    if municipality:
        sql = "SELECT * FROM job_seeker_data WHERE prefecture = ? AND municipality = ?"
        df = query_df(sql, (prefecture, municipality))
    else:
        sql = "SELECT * FROM job_seeker_data WHERE prefecture = ?"
        df = query_df(sql, (prefecture,))

    _set_cache(cache_key, df)
    return df


def get_filtered_data(prefecture: str, municipality: str = None) -> pd.DataFrame:
    """サーバーサイドフィルタリング: 指定地域のデータのみ取得

    Args:
        prefecture: 都道府県名
        municipality: 市区町村名（Noneの場合は都道府県全体）

    Returns:
        フィルタ済みDataFrame（数十〜数百行）
    """
    if _HAS_TURSO:
        return query_municipality(prefecture, municipality)
    else:
        # SQLite/PostgreSQL用
        sql = "SELECT * FROM mapcomplete_raw WHERE 1=1"
        params = []

        if prefecture:
            sql += " AND prefecture = ?"
            params.append(prefecture)

        if municipality:
            sql += " AND municipality = ?"
            params.append(municipality)

        return query_df(sql, tuple(params)) if params else query_df(sql)


def get_row_count_by_location(prefecture: str, municipality: str = None) -> int:
    """指定地域のデータ行数を取得（軽量クエリ）"""
    if _HAS_TURSO:
        if municipality:
            sql = "SELECT COUNT(*) as cnt FROM job_seeker_data WHERE prefecture = ? AND municipality = ?"
            df = query_df(sql, (prefecture, municipality))
        else:
            sql = "SELECT COUNT(*) as cnt FROM job_seeker_data WHERE prefecture = ?"
            df = query_df(sql, (prefecture,))
    else:
        sql = "SELECT COUNT(*) as cnt FROM mapcomplete_raw WHERE 1=1"
        params = []

        if prefecture:
            sql += " AND prefecture = ?"
            params.append(prefecture)

        if municipality:
            sql += " AND municipality = ?"
            params.append(municipality)

        df = query_df(sql, tuple(params)) if params else query_df(sql)

    if not df.empty and 'cnt' in df.columns:
        return int(df['cnt'].iloc[0])
    return 0


def get_applicants(
    prefecture: Optional[str] = None, municipality: Optional[str] = None
) -> pd.DataFrame:
    """申請者データを取得（フィルタ可能）"""
    sql = "SELECT * FROM applicants WHERE 1=1"
    params = []

    if prefecture:
        sql += " AND residence_prefecture = ?"
        params.append(prefecture)

    if municipality:
        sql += " AND residence_municipality = ?"
        params.append(municipality)

    return query_df(sql, tuple(params)) if params else query_df(sql)


def get_persona_summary(
    age_group: Optional[str] = None,
    gender: Optional[str] = None,
    has_national_license: Optional[bool] = None,
) -> pd.DataFrame:
    """ペルソナサマリーを取得（フィルタ可能）"""
    sql = "SELECT * FROM persona_summary WHERE 1=1"
    params = []

    if age_group:
        sql += " AND age_group = ?"
        params.append(age_group)

    if gender:
        sql += " AND gender = ?"
        params.append(gender)

    if has_national_license is not None:
        sql += " AND has_national_license = ?"
        params.append(1 if has_national_license else 0)

    sql += " ORDER BY count DESC"

    return query_df(sql, tuple(params)) if params else query_df(sql)


def get_supply_density_map(location: Optional[str] = None) -> pd.DataFrame:
    """人材供給密度マップデータを取得"""
    sql = "SELECT * FROM supply_density_map WHERE 1=1"
    params = []

    if location:
        sql += " AND location = ?"
        params.append(location)

    sql += " ORDER BY supply_count DESC"

    return query_df(sql, tuple(params)) if params else query_df(sql)


def get_municipality_flow_edges(
    from_prefecture: Optional[str] = None,
    from_municipality: Optional[str] = None,
    to_prefecture: Optional[str] = None,
    to_municipality: Optional[str] = None,
) -> pd.DataFrame:
    """自治体間フローエッジを取得"""
    sql = "SELECT * FROM municipality_flow_edges WHERE 1=1"
    params = []

    if from_prefecture:
        sql += " AND from_prefecture = ?"
        params.append(from_prefecture)

    if from_municipality:
        sql += " AND from_municipality = ?"
        params.append(from_municipality)

    if to_prefecture:
        sql += " AND to_prefecture = ?"
        params.append(to_prefecture)

    if to_municipality:
        sql += " AND to_municipality = ?"
        params.append(to_municipality)

    sql += " ORDER BY flow_count DESC"

    return query_df(sql, tuple(params)) if params else query_df(sql)


def get_unique_values(table_name: str, column_name: str) -> list:
    """テーブルの指定カラムのユニーク値を取得"""
    sql = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL ORDER BY {column_name}"
    df = query_df(sql)
    return df[column_name].tolist()


def execute_custom_query(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """カスタムSQLクエリを実行"""
    return query_df(sql, params)


if __name__ == "__main__":
    print("=" * 60)
    print("データベースヘルパーテスト")
    print("=" * 60)
    print(f"Database Type: {get_db_type()}")

    if _HAS_TURSO:
        print(f"Turso URL: {TURSO_DATABASE_URL}")

        # 都道府県一覧取得
        print("\n都道府県一覧:")
        prefectures = get_prefectures()
        print(f"  {len(prefectures)}都道府県")
        if prefectures:
            print(f"  例: {prefectures[:3]}")

            # 最初の都道府県の市区町村
            first_pref = prefectures[0]
            municipalities = get_municipalities(first_pref)
            print(f"\n{first_pref}の市区町村: {len(municipalities)}")

            # データ取得テスト
            df = query_municipality(first_pref)
            print(f"{first_pref}のデータ: {len(df)}行")
    else:
        print("Turso未設定。SQLite/PostgreSQLモード。")
