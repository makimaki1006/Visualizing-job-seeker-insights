"""
CSV→SQLiteデータベース移行スクリプト

既存のCSVファイルを無料のSQLiteデータベースに移行します。
パフォーマンス向上とスケーラビリティを実現。

使用方法:
    python migrate_csv_to_db.py

出力:
    data/job_medley.db (SQLiteデータベースファイル)
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List
from database_schema import DATABASE_SCHEMA, get_all_create_table_sqls

# データディレクトリ
BASE_DIR = Path(__file__).parent.parent / "python_scripts" / "data" / "output_v2"
DB_PATH = Path(__file__).parent / "data" / "job_medley.db"

# CSV→テーブルマッピング
CSV_TABLE_MAPPING = {
    # Phase 1
    "phase1/Phase1_Applicants.csv": "applicants",
    "phase1/Phase1_DesiredWork.csv": "desired_work",
    "phase1/Phase1_AggDesired.csv": "agg_desired",
    "phase1/Phase1_MapMetrics.csv": "map_metrics",
    # Phase 2
    "phase2/Phase2_ChiSquareTests.csv": "chi_square_tests",
    "phase2/Phase2_ANOVATests.csv": "anova_tests",
    # Phase 3
    "phase3/Phase3_PersonaSummary.csv": "persona_summary",
    "phase3/Phase3_PersonaDetails.csv": "persona_details",
    "phase3/Phase3_PersonaSummaryByMunicipality.csv": "persona_summary_by_municipality",
    # Phase 6
    "phase6/Phase6_MunicipalityFlowEdges.csv": "municipality_flow_edges",
    "phase6/Phase6_MunicipalityFlowNodes.csv": "municipality_flow_nodes",
    "phase6/Phase6_ProximityAnalysis.csv": "proximity_analysis",
    # Phase 7
    "phase7/Phase7_SupplyDensityMap.csv": "supply_density_map",
    "phase7/Phase7_QualificationDistribution.csv": "qualification_distribution",
    "phase7/Phase7_AgeGenderCrossAnalysis.csv": "age_gender_cross_analysis",
    "phase7/Phase7_MobilityScore.csv": "mobility_score",
    "phase7/Phase7_DetailedPersonaProfile.csv": "detailed_persona_profile",
    # Phase 8
    "phase8/Phase8_CareerDistribution.csv": "career_distribution",
    "phase8/Phase8_CareerAgeCross.csv": "career_age_cross",
    "phase8/Phase8_GraduationYearDistribution.csv": "graduation_year_distribution",
    # Phase 10
    "phase10/Phase10_UrgencyDistribution.csv": "urgency_distribution",
    "phase10/Phase10_UrgencyAgeCross.csv": "urgency_age_cross",
    "phase10/Phase10_UrgencyEmploymentCross.csv": "urgency_employment_cross",
}


def create_database(db_path: Path) -> sqlite3.Connection:
    """
    SQLiteデータベースを作成し、スキーマを適用

    Args:
        db_path: データベースファイルパス

    Returns:
        sqlite3接続オブジェクト
    """
    # データベースディレクトリ作成
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 既存データベースを削除（クリーンインストール）
    if db_path.exists():
        print(f"既存のデータベースを削除: {db_path}")
        db_path.unlink()

    # データベース作成
    conn = sqlite3.connect(str(db_path))
    print(f"データベース作成: {db_path}")

    # スキーマ適用
    sqls = get_all_create_table_sqls()
    for sql in sqls:
        conn.execute(sql)

    conn.commit()
    print(f"テーブル作成完了: {len(DATABASE_SCHEMA)}個のテーブル")

    return conn


def import_csv_to_table(
    conn: sqlite3.Connection, csv_path: Path, table_name: str
) -> int:
    """
    CSVファイルをデータベーステーブルにインポート

    Args:
        conn: sqlite3接続オブジェクト
        csv_path: CSVファイルパス
        table_name: テーブル名

    Returns:
        インポートした行数
    """
    if not csv_path.exists():
        print(f"[SKIP] ファイルが存在しません: {csv_path}")
        return 0

    # CSVを読み込み
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception as e:
        print(f"[ERROR] CSVの読み込みに失敗: {csv_path} - {e}")
        return 0

    # テーブルにインポート
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(
            f"[OK] {table_name}: {len(df)}行をインポート ({csv_path.name})"
        )
        return len(df)
    except Exception as e:
        print(f"[ERROR] インポートに失敗: {table_name} - {e}")
        return 0


def migrate_all_csvs(conn: sqlite3.Connection, base_dir: Path) -> Dict[str, int]:
    """
    全CSVファイルをデータベースに移行

    Args:
        conn: sqlite3接続オブジェクト
        base_dir: CSVファイルのベースディレクトリ

    Returns:
        テーブル名→インポート行数の辞書
    """
    results = {}

    for csv_path_str, table_name in CSV_TABLE_MAPPING.items():
        csv_path = base_dir / csv_path_str
        row_count = import_csv_to_table(conn, csv_path, table_name)
        results[table_name] = row_count

    return results


def analyze_database(conn: sqlite3.Connection) -> None:
    """
    データベース統計情報を表示

    Args:
        conn: sqlite3接続オブジェクト
    """
    print("\n" + "=" * 60)
    print("データベース統計")
    print("=" * 60)

    cursor = conn.cursor()

    # テーブルごとの行数
    for table_name in DATABASE_SCHEMA.keys():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"{table_name:40s} : {count:>10,}行")
        except Exception as e:
            print(f"{table_name:40s} : [ERROR] {e}")

    # データベースファイルサイズ
    db_size = DB_PATH.stat().st_size / 1024 / 1024  # MB
    print(f"\nデータベースファイルサイズ: {db_size:.2f} MB")


def verify_data_integrity(conn: sqlite3.Connection) -> bool:
    """
    データ整合性を検証

    Args:
        conn: sqlite3接続オブジェクト

    Returns:
        検証成功ならTrue
    """
    print("\n" + "=" * 60)
    print("データ整合性検証")
    print("=" * 60)

    cursor = conn.cursor()
    all_passed = True

    # 1. applicantsテーブルのユニーク性チェック
    cursor.execute(
        """
        SELECT COUNT(*), COUNT(DISTINCT applicant_id)
        FROM applicants
    """
    )
    total, unique = cursor.fetchone()
    if total == unique:
        print(f"[OK] applicants.applicant_id: ユニーク ({unique}件)")
    else:
        print(
            f"[NG] applicants.applicant_id: 重複あり (全{total}件, ユニーク{unique}件)"
        )
        all_passed = False

    # 2. persona_summaryテーブルのユニーク性チェック
    cursor.execute(
        """
        SELECT COUNT(*), COUNT(DISTINCT persona_name)
        FROM persona_summary
    """
    )
    total, unique = cursor.fetchone()
    if total == unique:
        print(f"[OK] persona_summary.persona_name: ユニーク ({unique}件)")
    else:
        print(
            f"[NG] persona_summary.persona_name: 重複あり (全{total}件, ユニーク{unique}件)"
        )
        all_passed = False

    # 3. 外部キー整合性チェック（desired_work → applicants）
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM desired_work dw
        LEFT JOIN applicants a ON dw.applicant_id = a.applicant_id
        WHERE a.applicant_id IS NULL
    """
    )
    orphaned = cursor.fetchone()[0]
    if orphaned == 0:
        print(f"[OK] desired_work -> applicants: 外部キー整合性OK")
    else:
        print(
            f"[NG] desired_work -> applicants: 孤立レコード {orphaned}件"
        )
        all_passed = False

    if all_passed:
        print("\n[OK] データ整合性検証: すべて成功")
    else:
        print("\n[NG] データ整合性検証: 一部失敗")

    return all_passed


def main():
    """メイン処理"""
    print("=" * 60)
    print("CSV→SQLite移行スクリプト")
    print("=" * 60)
    print()

    # データベース作成
    conn = create_database(DB_PATH)

    # CSV移行
    print("\n" + "=" * 60)
    print("CSVインポート開始")
    print("=" * 60)
    results = migrate_all_csvs(conn, BASE_DIR)

    # 統計情報表示
    analyze_database(conn)

    # データ整合性検証
    verify_data_integrity(conn)

    # 接続クローズ
    conn.close()

    print("\n" + "=" * 60)
    print("移行完了！")
    print("=" * 60)
    print(f"データベースファイル: {DB_PATH}")
    print(
        f"総行数: {sum(results.values()):,}行"
    )
    print(
        f"総テーブル数: {len([r for r in results.values() if r > 0])}テーブル"
    )


if __name__ == "__main__":
    main()
