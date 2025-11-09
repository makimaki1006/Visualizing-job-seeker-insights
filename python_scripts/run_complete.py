"""
市区町村データ抽出 - 完全版（Phase 1-7 + Network Analysis統合）

このスクリプトはすべてを実行します：
- GUIファイル選択
- Phase 1-6フォルダ出力（11ファイル）
- Phase 7フォルダ出力（5ファイル）
- ネットワーク中心性分析（2ファイル）← Phase 2-2 NEW!
- 拡張分析グラフ（PNG）
- 補助ファイル（JSON, CSV）

使い方:
    python run_complete.py
"""

import sys
from pathlib import Path
from test_phase6_temp import AdvancedJobSeekerAnalyzer, select_csv_file


def print_header(text):
    """ヘッダー表示"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def main():
    """メイン処理"""
    print_header("市区町村データ抽出 - 完全版（Phase 1-7 + Network）")
    print("このスクリプトは以下をすべて実行します：")
    print("  [OK] Phase 1-6フォルダ出力（11ファイル）")
    print("  [OK] Phase 7フォルダ出力（5ファイル）")
    print("  [OK] ネットワーク中心性分析（2ファイル）← NEW!")
    print("  [OK] 拡張分析グラフ（advanced_analysis.png）")
    print("  [OK] 補助ファイル（JSON, segment CSV等）")
    print()

    # GUIファイル選択
    print("CSVファイルを選択してください...")
    filepath = select_csv_file()

    if not filepath:
        print("[ERROR] ファイルが選択されませんでした。終了します。")
        return

    print(f"\n[OK] 選択されたファイル: {Path(filepath).name}\n")

    try:
        # Analyzerインスタンス作成
        print("Analyzerを初期化しています...")
        analyzer = AdvancedJobSeekerAnalyzer(filepath=str(filepath))
        print("[OK] 初期化完了\n")

        # データ読み込み
        print_header("ステップ1: データ読み込み")
        analyzer.load_data()
        print("[OK] データ読み込み完了\n")

        # データ処理
        print_header("ステップ2: データ処理")
        try:
            analyzer.process_data()
            print("[OK] データ処理完了\n")
        except Exception as e:
            print(f"[WARNING] 警告: データ処理でエラー発生: {e}")
            print("   最小限の処理を実行します...\n")
            import pandas as pd
            analyzer.df_processed = pd.DataFrame()
            analyzer.df_processed["id"] = range(1, len(analyzer.df) + 1)
            analyzer._extract_basic_info()
            analyzer._extract_desired_locations()
            print("[OK] 最小限の処理完了\n")

        # Phase 1-6エクスポート
        print_header("ステップ3: Phase 1-6エクスポート")

        # Phase 1
        print("[PHASE1] Phase 1: 基礎集計")
        try:
            analyzer.export_phase1_data(output_dir="gas_output_phase1")
            print("   [OK] Phase 1完了 (4ファイル)\n")
        except Exception as e:
            print(f"   [ERROR] Phase 1エラー: {e}\n")

        # Phase 2
        print("[PHASE2] Phase 2: 統計分析")
        try:
            analyzer.export_phase2_data(output_dir="gas_output_phase2")
            print("   [OK] Phase 2完了 (2ファイル)\n")
        except Exception as e:
            print(f"   [ERROR] Phase 2エラー: {e}\n")

        # Phase 3
        print("[PHASE3] Phase 3: ペルソナ分析")
        try:
            analyzer.export_phase3_data(output_dir="gas_output_phase3", n_clusters=5)
            print("   [OK] Phase 3完了 (2ファイル)\n")
        except Exception as e:
            print(f"   [ERROR] Phase 3エラー: {e}\n")

        # Phase 7（Phase 6より先に実行 - 最適化）
        print("[PHASE7] Phase 7: 高度分析機能")
        try:
            from phase7_advanced_analysis import run_phase7_analysis

            phase7_analyzer = run_phase7_analysis(
                df=analyzer.df,
                df_processed=analyzer.df_processed,
                geocache=analyzer.geocache,
                master=analyzer.master,
                output_dir='gas_output_phase7'
            )
            print("   [OK] Phase 7完了 (5ファイル)\n")
        except ImportError as ie:
            print(f"   [WARNING] Phase 7モジュールが見つかりません: {ie}")
            print("   Phase 7をスキップします...\n")
        except Exception as e:
            print(f"   [ERROR] Phase 7エラー: {e}\n")

        # Phase 6（最後に実行 - 最適化により高速化）
        print("[PHASE6] Phase 6: フローネットワーク分析（最適化版）")
        try:
            analyzer.export_phase6_data(output_dir="gas_output_phase6")
            print("   [OK] Phase 6完了 (3ファイル)\n")
        except Exception as e:
            print(f"   [ERROR] Phase 6エラー: {e}\n")

        # Phase 2-2: ネットワーク中心性分析（Phase 6の後に実行）
        print("[NETWORK] ネットワーク中心性分析（NetworkX）")
        try:
            from network_analyzer import NetworkAnalyzer

            network_analyzer = NetworkAnalyzer(data_root=str(Path(__file__).parent.parent))
            network_analyzer.run_complete_analysis(top_n=20)
            print("   [OK] ネットワーク分析完了 (2ファイル: NetworkMetrics.json, CentralityRanking.csv)\n")
        except ImportError as ie:
            print(f"   [WARNING] NetworkAnalyzerモジュールが見つかりません: {ie}")
            print("   ネットワーク分析をスキップします...\n")
        except Exception as e:
            print(f"   [ERROR] ネットワーク分析エラー: {e}\n")

        # 拡張分析
        print_header("ステップ4: 拡張分析")

        print("[VISUALIZE] 拡張可視化を実行中...")
        try:
            analyzer.advanced_visualizations()
            print("   [OK] advanced_analysis.png 生成完了\n")
        except Exception as e:
            print(f"   [WARNING] 可視化スキップ: {e}\n")

        print("[INSIGHTS] 拡張インサイトを生成中...")
        try:
            analyzer.generate_advanced_insights()
            print("   [OK] インサイト生成完了\n")
        except Exception as e:
            print(f"   [WARNING] インサイト生成スキップ: {e}\n")

        # 結果エクスポート（補助ファイル）
        print_header("ステップ5: 補助ファイルエクスポート")
        try:
            analyzer.export_results()
            print("[OK] 補助ファイル出力完了\n")
        except Exception as e:
            print(f"[WARNING] 補助ファイル出力エラー: {e}\n")

        # 結果サマリー
        print_header("実行結果サマリー")

        base_dir = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管")

        # Phase 1-7フォルダ + ネットワーク分析
        phase_dirs = [
            ("Phase 1", base_dir / 'gas_output_phase1'),
            ("Phase 2", base_dir / 'gas_output_phase2'),
            ("Phase 3", base_dir / 'gas_output_phase3'),
            ("Phase 6", base_dir / 'gas_output_phase6'),
            ("Phase 7", base_dir / 'gas_output_phase7'),
            ("Network Insights", base_dir / 'job_medley_project' / 'gas_output_insights'),
        ]

        total_files = 0
        for phase_name, phase_dir in phase_dirs:
            if phase_dir.exists():
                files = list(phase_dir.glob("*"))
                if files:
                    print(f"\n[FOLDER] {phase_name}出力 ({phase_dir.name}):")
                    for file in sorted(files):
                        print(f"   - {file.name}")
                    total_files += len(files)

        # 補助ファイル
        print(f"\n[FILES] 補助ファイル（プロジェクトルート）:")
        aux_files = [
            "advanced_analysis.png",
            "processed_data_complete.csv",
            "analysis_results_complete.json",
            "geocache.json",
        ]
        for aux_file in aux_files:
            aux_path = base_dir / aux_file
            if aux_path.exists():
                print(f"   - {aux_file}")
                total_files += 1

        # segment_*.csv
        segment_files = list(base_dir.glob("segment_*.csv"))
        if segment_files:
            print(f"   - segment_*.csv ({len(segment_files)}ファイル)")
            total_files += len(segment_files)

        print(f"\n{'=' * 60}")
        print(f"[COMPLETE] すべての処理が完了しました！")
        print(f"   合計出力ファイル: {total_files}件")
        print(f"{'=' * 60}\n")

    except Exception as e:
        print(f"\n[ERROR] エラーが発生しました:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()