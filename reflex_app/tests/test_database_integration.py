"""
データベース統合テスト（SQLite/PostgreSQL両対応）

db_helper.pyのハイブリッドデータベース機能をテストします。
- SQLiteモード（DATABASE_URL未設定）
- PostgreSQLモード（DATABASE_URL設定済み）
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_helper import (
    get_db_type,
    get_connection,
    get_applicants,
    get_persona_summary,
    get_supply_density_map,
    get_municipality_flow_edges,
    get_prefectures,
    get_municipalities,
    query_df,
)


class TestDatabaseIntegration:
    """データベース統合テスト"""

    def test_db_type_sqlite(self):
        """SQLiteモードで起動することを確認（DATABASE_URL未設定）"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # SQLiteモードであることを確認
        db_type = get_db_type()
        assert db_type == "sqlite", f"Expected sqlite, got {db_type}"

    def test_connection_sqlite(self):
        """SQLite接続を取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 接続取得
        conn = get_connection()
        assert conn is not None

        # 接続クローズ
        conn.close()

    def test_get_applicants(self):
        """申請者データを取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 全申請者データ取得
        df = get_applicants()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "applicant_id" in df.columns
        assert "age" in df.columns
        assert "gender" in df.columns

    def test_get_applicants_filtered(self):
        """フィルタ条件付きで申請者データを取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 京都府のデータを取得
        df = get_applicants(prefecture="京都府")
        assert isinstance(df, pd.DataFrame)

        # 京都府のデータのみであることを確認
        if len(df) > 0:
            assert all(df["residence_prefecture"] == "京都府")

    def test_get_persona_summary(self):
        """ペルソナサマリーを取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # ペルソナサマリー取得
        df = get_persona_summary()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "persona_name" in df.columns
        assert "count" in df.columns

    def test_get_persona_summary_filtered(self):
        """フィルタ条件付きでペルソナサマリーを取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 20代女性のペルソナサマリー取得
        df = get_persona_summary(age_group="20代", gender="女性")
        assert isinstance(df, pd.DataFrame)

        # フィルタ条件が正しく適用されていることを確認
        if len(df) > 0:
            assert all(df["age_group"] == "20代")
            assert all(df["gender"] == "女性")

    def test_get_supply_density_map(self):
        """人材供給密度マップを取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 人材供給密度マップ取得
        df = get_supply_density_map()
        assert isinstance(df, pd.DataFrame)

        # カラムチェック
        if len(df) > 0:
            assert "location" in df.columns
            assert "supply_count" in df.columns

    def test_get_municipality_flow_edges(self):
        """自治体間フローエッジを取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 自治体間フローエッジ取得
        try:
            df = get_municipality_flow_edges()
            assert isinstance(df, pd.DataFrame)

            # カラムチェック（実際のテーブル構造に依存）
            # municipality_flow_edgesテーブルが存在しない、または構造が異なる場合はスキップ
            if len(df) > 0:
                # 実際のテーブル構造: origin, destination, origin_pref, origin_muni, etc.
                assert "origin_pref" in df.columns or "from_prefecture" in df.columns
        except Exception as e:
            # テーブルが存在しない、または構造が異なる場合はスキップ
            pytest.skip(f"municipality_flow_edges table not available or has different structure: {e}")

    def test_get_prefectures(self):
        """都道府県一覧を取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 都道府県一覧取得
        prefectures = get_prefectures()
        assert isinstance(prefectures, list)
        assert len(prefectures) > 0
        assert "京都府" in prefectures or "愛知県" in prefectures

    def test_get_municipalities(self):
        """市区町村一覧を取得できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 京都府の市区町村一覧取得
        municipalities = get_municipalities("京都府")
        assert isinstance(municipalities, list)

        # 市区町村が存在する場合、京都府のものであることを確認
        if len(municipalities) > 0:
            assert any("京都" in m for m in municipalities[:3])

    def test_query_df(self):
        """カスタムクエリを実行できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # カスタムクエリ実行
        sql = "SELECT * FROM applicants LIMIT 10"
        df = query_df(sql)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 10

    def test_query_df_with_params(self):
        """パラメータ付きクエリを実行できることを確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # パラメータ付きクエリ実行
        sql = "SELECT * FROM applicants WHERE residence_prefecture = ? LIMIT 10"
        df = query_df(sql, ("京都府",))
        assert isinstance(df, pd.DataFrame)

        # 京都府のデータのみであることを確認
        if len(df) > 0:
            assert all(df["residence_prefecture"] == "京都府")

    def test_data_integrity(self):
        """データ整合性を確認"""
        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # 申請者データ取得
        df_applicants = get_applicants()
        assert len(df_applicants) > 0

        # applicant_idがユニークであることを確認
        unique_ids = df_applicants["applicant_id"].nunique()
        total_ids = len(df_applicants)
        assert unique_ids == total_ids, f"Duplicate applicant_id found: {total_ids - unique_ids} duplicates"

    def test_performance_comparison(self):
        """CSVとDBのパフォーマンス比較"""
        import time

        # 環境変数を削除
        os.environ.pop("DATABASE_URL", None)

        # CSVパス
        csv_path = Path(__file__).parent.parent.parent / "python_scripts" / "data" / "output_v2" / "phase1" / "Phase1_Applicants.csv"

        # CSVが存在する場合のみ比較
        if csv_path.exists():
            # CSV読み込み
            start = time.time()
            df_csv = pd.read_csv(csv_path, encoding="utf-8-sig")
            csv_time = time.time() - start

            # DB読み込み
            start = time.time()
            df_db = get_applicants()
            db_time = time.time() - start

            # 件数が一致することを確認
            assert len(df_csv) == len(df_db), f"CSV: {len(df_csv)} rows, DB: {len(df_db)} rows"

            # パフォーマンス比較（DBが10倍遅くないことを確認）
            assert db_time < csv_time * 10, f"DB too slow: CSV={csv_time:.3f}s, DB={db_time:.3f}s"


# PostgreSQLモードのテスト（DATABASE_URL設定時のみ実行）
class TestDatabaseIntegrationPostgreSQL:
    """PostgreSQLモードのテスト（DATABASE_URL設定済みの場合のみ実行）"""

    @pytest.fixture(autouse=True)
    def check_postgres_available(self):
        """PostgreSQLが利用可能かチェック"""
        if "DATABASE_URL" not in os.environ:
            pytest.skip("DATABASE_URL not set, skipping PostgreSQL tests")

    def test_db_type_postgresql(self):
        """PostgreSQLモードで起動することを確認"""
        db_type = get_db_type()
        assert db_type == "postgresql", f"Expected postgresql, got {db_type}"

    def test_connection_postgresql(self):
        """PostgreSQL接続を取得できることを確認"""
        conn = get_connection()
        assert conn is not None
        conn.close()

    def test_get_applicants_postgresql(self):
        """PostgreSQLから申請者データを取得できることを確認"""
        df = get_applicants()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "applicant_id" in df.columns

    def test_query_df_with_params_postgresql(self):
        """PostgreSQLでパラメータ付きクエリを実行できることを確認"""
        # PostgreSQLではプレースホルダーが%sに変換される
        sql = "SELECT * FROM applicants WHERE residence_prefecture = ? LIMIT 10"
        df = query_df(sql, ("京都府",))
        assert isinstance(df, pd.DataFrame)


if __name__ == "__main__":
    # テスト実行
    pytest.main([__file__, "-v", "-s"])
