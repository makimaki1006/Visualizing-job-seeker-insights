"""
SQLiteデータベースアクセスヘルパー

DashboardStateでのデータベースアクセスを簡潔にするヘルパー関数群。
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional

# データベースパス
DB_PATH = Path(__file__).parent / "data" / "job_medley.db"


def get_connection() -> sqlite3.Connection:
    """
    データベース接続を取得

    Returns:
        sqlite3接続オブジェクト
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"データベースファイルが見つかりません: {DB_PATH}\n"
            f"migrate_csv_to_db.py を実行してデータベースを作成してください。"
        )

    conn = sqlite3.connect(str(DB_PATH))
    return conn


def query_df(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """
    SQLクエリを実行してDataFrameとして取得

    Args:
        sql: SQLクエリ文字列
        params: パラメータタプル（オプション）

    Returns:
        クエリ結果のDataFrame
    """
    conn = get_connection()
    try:
        if params:
            df = pd.read_sql_query(sql, conn, params=params)
        else:
            df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


def get_table(table_name: str) -> pd.DataFrame:
    """
    テーブル全体をDataFrameとして取得

    Args:
        table_name: テーブル名

    Returns:
        テーブル全体のDataFrame
    """
    return query_df(f"SELECT * FROM {table_name}")


def get_applicants(
    prefecture: Optional[str] = None, municipality: Optional[str] = None
) -> pd.DataFrame:
    """
    申請者データを取得（フィルタ可能）

    Args:
        prefecture: 都道府県（オプション）
        municipality: 市区町村（オプション）

    Returns:
        申請者データのDataFrame
    """
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
    """
    ペルソナサマリーを取得（フィルタ可能）

    Args:
        age_group: 年齢層（オプション）
        gender: 性別（オプション）
        has_national_license: 国家資格有無（オプション）

    Returns:
        ペルソナサマリーのDataFrame
    """
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
    """
    人材供給密度マップデータを取得

    Args:
        location: 地域（オプション）

    Returns:
        人材供給密度マップのDataFrame
    """
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
    """
    自治体間フローエッジを取得

    Args:
        from_prefecture: 出発都道府県（オプション）
        from_municipality: 出発市区町村（オプション）
        to_prefecture: 到着都道府県（オプション）
        to_municipality: 到着市区町村（オプション）

    Returns:
        自治体間フローエッジのDataFrame
    """
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
    """
    テーブルの指定カラムのユニーク値を取得

    Args:
        table_name: テーブル名
        column_name: カラム名

    Returns:
        ユニーク値のリスト
    """
    sql = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL ORDER BY {column_name}"
    df = query_df(sql)
    return df[column_name].tolist()


def get_prefectures() -> list:
    """
    都道府県一覧を取得

    Returns:
        都道府県のリスト
    """
    return get_unique_values("applicants", "residence_prefecture")


def get_municipalities(prefecture: str) -> list:
    """
    指定都道府県の市区町村一覧を取得

    Args:
        prefecture: 都道府県

    Returns:
        市区町村のリスト
    """
    sql = """
        SELECT DISTINCT residence_municipality
        FROM applicants
        WHERE residence_prefecture = ?
        ORDER BY residence_municipality
    """
    df = query_df(sql, (prefecture,))
    return df["residence_municipality"].tolist()


def execute_custom_query(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """
    カスタムSQLクエリを実行

    Args:
        sql: SQLクエリ文字列
        params: パラメータタプル（オプション）

    Returns:
        クエリ結果のDataFrame
    """
    return query_df(sql, params)


# パフォーマンス比較用
def benchmark_csv_vs_db():
    """
    CSV読み込みとDB読み込みのパフォーマンス比較
    """
    import time

    # CSV読み込み（従来方式）
    csv_path = Path(__file__).parent.parent / "python_scripts" / "data" / "output_v2" / "phase1" / "Phase1_Applicants.csv"

    if csv_path.exists():
        start = time.time()
        df_csv = pd.read_csv(csv_path, encoding="utf-8-sig")
        csv_time = time.time() - start
        print(f"CSV読み込み: {csv_time:.3f}秒 ({len(df_csv)}行)")
    else:
        print(f"CSVファイルが見つかりません: {csv_path}")
        csv_time = None

    # DB読み込み（新方式）
    start = time.time()
    df_db = get_table("applicants")
    db_time = time.time() - start
    print(f"DB読み込み: {db_time:.3f}秒 ({len(df_db)}行)")

    if csv_time:
        speedup = csv_time / db_time
        print(f"高速化: {speedup:.2f}倍")


if __name__ == "__main__":
    print("=" * 60)
    print("データベースヘルパーテスト")
    print("=" * 60)

    # 都道府県一覧取得
    print("\n都道府県一覧:")
    prefectures = get_prefectures()
    print(f"  {len(prefectures)}都道府県")
    print(f"  例: {prefectures[:3]}")

    # 京都府の市区町村一覧
    print("\n京都府の市区町村:")
    municipalities = get_municipalities("京都府")
    print(f"  {len(municipalities)}市区町村")
    print(f"  例: {municipalities[:3]}")

    # 京都市の申請者データ
    print("\n京都市の申請者データ:")
    df_kyoto = get_applicants("京都府", "京都市")
    print(f"  {len(df_kyoto)}件")

    # ペルソナサマリー（上位5件）
    print("\nペルソナサマリー（上位5件）:")
    df_persona = get_persona_summary()
    print(df_persona.head()[["persona_name", "count"]])

    # パフォーマンス比較
    print("\n" + "=" * 60)
    print("パフォーマンス比較")
    print("=" * 60)
    benchmark_csv_vs_db()
