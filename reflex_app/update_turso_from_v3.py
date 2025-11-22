# -*- coding: utf-8 -*-
"""V3 CSVデータをTurso DBに完全置換するスクリプト"""
import pandas as pd
import db_helper
from pathlib import Path

def update_turso_from_v3_csv():
    """V3 CSVファイルをTurso DBに完全アップロード"""

    # V3 CSVファイルパス
    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"

    if not csv_path.exists():
        print(f"[ERROR] V3 CSVファイルが見つかりません: {csv_path}")
        return False

    print("=== V3 CSV → Turso DB 完全置換 ===\n")

    # 1. V3 CSVを読み込み
    print(f"[1/4] V3 CSVファイル読み込み中...")
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
    print(f"      ✅ 読み込み成功: {len(df):,}行 x {len(df.columns)}列")

    # 2. row_type分布を確認
    print(f"\n[2/4] row_type分布確認:")
    row_type_counts = df['row_type'].value_counts()
    for rt, count in row_type_counts.items():
        print(f"      - {rt}: {count:,}行")

    # 3. Turso DBの既存データを削除
    print(f"\n[3/4] Turso DB既存データ削除中...")
    try:
        # db_helperのTurso接続を使用
        if hasattr(db_helper, '_HAS_TURSO') and db_helper._HAS_TURSO:
            # 既存テーブルを削除
            db_helper.execute_sql("DROP TABLE IF EXISTS job_seeker_data")
            print(f"      ✅ 既存テーブル削除成功")

            # 新しいテーブルを作成（dfのスキーマから自動生成）
            # pandasのto_sqlを使用してテーブル作成とデータ挿入を同時実行
            from turso_db import get_turso_connection
            conn = get_turso_connection()

            # テーブル作成
            df.to_sql('job_seeker_data', conn, if_exists='replace', index=False)
            print(f"      ✅ 新しいテーブル作成成功")
        else:
            print(f"      ⚠️ Turso DB未接続（ローカルSQLiteモード）")
            return False
    except Exception as e:
        print(f"      ❌ エラー: {e}")
        return False

    # 4. データ挿入確認
    print(f"\n[4/4] データ挿入確認中...")
    try:
        # 挿入後のデータ件数確認
        result = db_helper.query_df("SELECT COUNT(*) as count FROM job_seeker_data")
        inserted_count = result['count'].iloc[0] if not result.empty else 0

        print(f"      ✅ Turso DB挿入成功: {inserted_count:,}行")

        if inserted_count == len(df):
            print(f"\n[SUCCESS] V3 CSV → Turso DB 完全置換成功！")
            print(f"          - 元のCSV: {len(df):,}行")
            print(f"          - Turso DB: {inserted_count:,}行")
            print(f"          - 一致: ✅")
            return True
        else:
            print(f"\n[WARNING] データ件数が一致しません")
            print(f"          - 元のCSV: {len(df):,}行")
            print(f"          - Turso DB: {inserted_count:,}行")
            print(f"          - 差分: {abs(len(df) - inserted_count):,}行")
            return False
    except Exception as e:
        print(f"      ❌ エラー: {e}")
        return False

if __name__ == "__main__":
    success = update_turso_from_v3_csv()

    if success:
        print("\n次のステップ:")
        print("1. Reflexサーバーを再起動: reflex run")
        print("2. ブラウザでアプリを確認")
        print("3. グラフが正しく表示されることを確認")
    else:
        print("\n[ERROR] Turso DB更新に失敗しました")
        print("代替案: CSVアップロード機能を使用してください")
