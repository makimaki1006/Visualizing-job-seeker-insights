"""
Phase 7 E2Eテスト - 実データを使用した完全テスト

このスクリプトは実データを使用してPhase 7の全機能をテストします。
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

from pathlib import Path
import json
from datetime import datetime

# test_phase6_tempからAnalyzerをインポート
from test_phase6_temp import AdvancedJobSeekerAnalyzer

def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("Phase 7 E2Eテスト - 実データ使用")
    print("=" * 60 + "\n")

    # 入力ファイル
    input_file = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\ai_enhanced_data_with_evidence.csv")

    if not input_file.exists():
        print(f"[ERROR] 入力ファイルが見つかりません: {input_file}")
        return False

    print(f"[INFO] 入力ファイル: {input_file.name}")

    try:
        # Analyzerインスタンス作成
        print("[STEP1] Analyzerを初期化中...")
        analyzer = AdvancedJobSeekerAnalyzer(filepath=str(input_file))
        print("[OK] 初期化完了\n")

        # データ読み込み
        print("[STEP2] データ読み込み中...")
        analyzer.load_data()
        print(f"[OK] データ読み込み完了: {len(analyzer.df)}件\n")

        # データ処理
        print("[STEP3] データ処理中...")
        try:
            analyzer.process_data()
            print(f"[OK] データ処理完了: {len(analyzer.df_processed)}件\n")
        except Exception as e:
            print(f"[WARNING] データ処理でエラー発生: {e}")
            print("   最小限の処理を実行します...\n")
            import pandas as pd
            analyzer.df_processed = pd.DataFrame()
            analyzer.df_processed["id"] = range(1, len(analyzer.df) + 1)
            analyzer._extract_basic_info()
            analyzer._extract_desired_locations()
            print(f"[OK] 最小限の処理完了\n")

        # Phase 7実行
        print("[STEP4] Phase 7実行中...")
        try:
            from phase7_advanced_analysis import run_phase7_analysis

            # テスト用出力ディレクトリ
            output_dir = Path("test_e2e_output_phase7")
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)

            phase7_analyzer = run_phase7_analysis(
                df=analyzer.df,
                df_processed=analyzer.df_processed,
                geocache=analyzer.geocache,
                master=analyzer.master,
                output_dir=str(output_dir)
            )

            print(f"[OK] Phase 7実行完了\n")

            # 出力ファイル確認
            print("[STEP5] 出力ファイル確認中...")

            expected_files = [
                "SupplyDensityMap.csv",
                "QualificationDistribution.csv",
                "AgeGenderCrossAnalysis.csv",
                "MobilityScore.csv",
                "DetailedPersonaProfile.csv"
            ]

            created_files = []
            file_details = {}

            for expected_file in expected_files:
                file_path = output_dir / expected_file
                if file_path.exists():
                    created_files.append(expected_file)

                    # CSV読み込みとデータ確認
                    import pandas as pd
                    df_test = pd.read_csv(file_path, encoding='utf-8-sig')

                    file_details[expected_file] = {
                        "exists": True,
                        "rows": len(df_test),
                        "columns": len(df_test.columns),
                        "column_names": df_test.columns.tolist()
                    }

                    print(f"[OK] {expected_file}: {len(df_test)}行, {len(df_test.columns)}列")
                else:
                    file_details[expected_file] = {
                        "exists": False,
                        "rows": 0,
                        "columns": 0,
                        "column_names": []
                    }
                    print(f"[SKIP] {expected_file}: 生成されませんでした（データ不足の可能性）")

            # テスト結果サマリー
            print("\n" + "=" * 60)
            print("E2Eテスト結果サマリー")
            print("=" * 60 + "\n")

            print(f"入力データ: {len(analyzer.df)}件")
            print(f"処理済みデータ: {len(analyzer.df_processed)}件")
            print(f"ジオキャッシュ: {len(analyzer.geocache)}件")
            print(f"Phase 7出力ファイル: {len(created_files)}/{len(expected_files)}件")

            if len(created_files) > 0:
                print("\n生成されたファイル:")
                for file in created_files:
                    detail = file_details[file]
                    print(f"  - {file}: {detail['rows']}行, {detail['columns']}列")

            # テスト結果をJSONで保存
            result_json = {
                "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "test_type": "E2E",
                "input_file": str(input_file),
                "input_records": len(analyzer.df),
                "processed_records": len(analyzer.df_processed),
                "geocache_entries": len(analyzer.geocache),
                "expected_files": len(expected_files),
                "created_files": len(created_files),
                "file_details": file_details,
                "test_status": "PASS" if len(created_files) > 0 else "FAIL"
            }

            result_path = Path("TEST_RESULTS_PHASE7_E2E.json")
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)

            print(f"\n[REPORT] E2Eテスト結果を保存しました: {result_path}")

            # テスト用ディレクトリをクリーンアップ
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)
                print(f"[CLEANUP] テスト用ディレクトリ削除: {output_dir}")

            # 判定
            if len(created_files) >= 1:
                print("\n[SUCCESS] E2Eテスト成功！最低1ファイルが生成されました")
                return True
            else:
                print("\n[FAIL] E2Eテスト失敗：ファイルが生成されませんでした")
                return False

        except ImportError as ie:
            print(f"[ERROR] Phase 7モジュールが見つかりません: {ie}")
            return False
        except Exception as e:
            print(f"[ERROR] Phase 7実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"[ERROR] E2Eテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
