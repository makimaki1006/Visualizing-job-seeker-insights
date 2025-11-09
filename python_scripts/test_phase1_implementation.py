#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1実装ユニットテストスイート

テスト対象:
- cross_analysis_engine.py (3次元クロス分析エンジン)
- PersonaMapDataVisualization.gs (データ整合性のみ)
- PersonaMobilityCrossViz.gs (データ整合性のみ)

テスト方針: MECE原則
- Unit Tests (個別関数テスト)
- Integration Tests (データフロー全体テスト)
- Data Validation Tests (データ品質テスト)

工数: 2時間
作成日: 2025-10-27
"""

import unittest
import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'python_scripts'))

from cross_analysis_engine import CrossAnalysisEngine


class TestCrossAnalysisEngineUnit(unittest.TestCase):
    """cross_analysis_engine.py ユニットテスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        print("\n" + "=" * 70)
        print("Phase 1 ユニットテスト開始: CrossAnalysisEngine")
        print("=" * 70)
        cls.project_root = project_root

    def setUp(self):
        """各テストの初期化"""
        self.engine = CrossAnalysisEngine(data_root=str(self.project_root))

    def test_01_engine_initialization(self):
        """エンジン初期化テスト"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.data_cache, {})
        self.assertEqual(self.engine.results, {})
        self.assertTrue(self.engine.data_root.exists())
        print("  [OK] エンジン初期化成功")

    def test_02_load_all_data_execution(self):
        """全CSVファイル読み込みテスト"""
        self.engine.load_all_data()

        # 18ファイル読み込み確認（一部ファイルが存在しない可能性を考慮）
        loaded_count = len(self.engine.data_cache)
        self.assertGreater(loaded_count, 0, "少なくとも1ファイルは読み込まれるべき")

        print(f"  [OK] {loaded_count}ファイル読み込み成功")

        # 主要ファイルの存在確認
        expected_keys = [
            'phase1_agg_desired',
            'phase1_applicants',
            'phase1_desired_work',
            'phase1_map_metrics'
        ]

        for key in expected_keys:
            if key in self.engine.data_cache:
                df = self.engine.data_cache[key]
                self.assertIsInstance(df, pd.DataFrame)
                self.assertGreater(len(df), 0, f"{key}は空であってはならない")
                print(f"    [+] {key}: {len(df)}行")

    def test_03_persona_mobility_qualification_analysis(self):
        """分析1実行テスト（ペルソナ×移動許容度×資格）"""
        self.engine.load_all_data()

        # PersonaMobilityCross.csv が存在する場合のみ実行
        if 'phase7_persona_mobility' not in self.engine.data_cache:
            self.skipTest("PersonaMobilityCross.csv が存在しません")

        results = self.engine.persona_mobility_qualification_analysis()

        # 結果構造検証
        self.assertIsInstance(results, dict)
        self.assertIn('analysis_name', results)
        self.assertIn('dimensions', results)
        self.assertIn('insights', results)

        self.assertEqual(results['dimensions'], 3)
        self.assertIsInstance(results['insights'], list)

        print(f"  [OK] 分析1完了: {len(results['insights'])}件のインサイト生成")

    def test_04_regional_age_gender_analysis(self):
        """分析2実行テスト（地域×年齢層×性別）"""
        self.engine.load_all_data()

        results = self.engine.regional_age_gender_analysis()

        # 結果構造検証
        self.assertIsInstance(results, dict)
        self.assertIn('analysis_name', results)
        self.assertIn('dimensions', results)
        self.assertIn('insights', results)
        self.assertIn('top_regions', results)

        self.assertEqual(results['dimensions'], 3)

        print(f"  [OK] 分析2完了: {len(results['insights'])}件のインサイト生成")

    def test_05_triple_cross_analysis_same_source(self):
        """3次元クロス分析テスト（同一データソース）"""
        self.engine.load_all_data()

        # Applicants.csv で3次元クロス分析（存在する場合）
        if 'phase1_applicants' not in self.engine.data_cache:
            self.skipTest("Applicants.csv が存在しません")

        df = self.engine.data_cache['phase1_applicants']

        # カラム確認（最低限の構造チェック）
        self.assertGreater(len(df.columns), 3, "3次元分析には最低4列必要")

        # データサイズ確認
        self.assertGreater(len(df), 0)

        print(f"  [OK] 3次元クロス分析準備OK（Applicants: {len(df)}行）")

    def test_06_export_to_json(self):
        """JSON出力テスト"""
        self.engine.load_all_data()

        # ダミー結果を追加
        self.engine.results['test_analysis'] = {
            'analysis_name': 'テスト分析',
            'dimensions': 2,
            'total_combinations': 10,
            'insights': [
                {'type': 'test', 'description': 'テストインサイト'}
            ]
        }

        # 一時ディレクトリに出力
        test_output_path = self.project_root / 'python_scripts' / 'test_output'
        test_output_path.mkdir(exist_ok=True)

        self.engine.export_to_json(output_path=str(test_output_path))

        # ファイル存在確認
        json_file = test_output_path / 'CrossAnalysisResults.json'
        self.assertTrue(json_file.exists())

        # JSON内容確認
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn('generated_at', data)
        self.assertIn('analysis_count', data)
        self.assertIn('data_sources_loaded', data)
        self.assertIn('results', data)

        self.assertEqual(data['analysis_count'], 1)
        self.assertIn('test_analysis', data['results'])

        print(f"  [OK] JSON出力成功: {json_file}")

        # クリーンアップ
        json_file.unlink()
        try:
            test_output_path.rmdir()
        except (PermissionError, OSError):
            pass  # Windows環境でディレクトリ削除が失敗する場合は無視

    def test_07_export_to_csv(self):
        """CSV出力テスト"""
        self.engine.load_all_data()

        # ダミークロス集計結果作成
        cross_result = pd.DataFrame({
            'dim1': ['A', 'A', 'B', 'B'],
            'dim2': ['X', 'Y', 'X', 'Y'],
            'dim3': ['P', 'P', 'Q', 'Q'],
            'count': [10, 20, 30, 40],
            'ratio': [10.0, 20.0, 30.0, 40.0]
        })

        # 一時ディレクトリに出力（gas_output_insightsに出力される）
        self.engine.export_to_csv(cross_result, filename='TestCrossResult.csv')

        # ファイル存在確認（実際の出力先はgas_output_insights）
        csv_file = self.project_root / 'gas_output_insights' / 'TestCrossResult.csv'
        self.assertTrue(csv_file.exists(), f"CSVファイルが見つかりません: {csv_file}")

        # CSV内容確認
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        self.assertEqual(len(df), 4)
        self.assertListEqual(list(df.columns), ['dim1', 'dim2', 'dim3', 'count', 'ratio'])

        print(f"  [OK] CSV出力成功: {csv_file}")

        # クリーンアップ（CSVファイル削除）
        if csv_file.exists():
            csv_file.unlink()


class TestPersonaMapDataValidation(unittest.TestCase):
    """PersonaMapData.csv データ検証テスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        print("\n" + "=" * 70)
        print("Phase 1 データ検証テスト: PersonaMapData.csv")
        print("=" * 70)
        cls.project_root = project_root

    def test_01_persona_map_data_existence(self):
        """PersonaMapData.csv 存在確認"""
        # 複数の可能性のあるパスをチェック
        possible_paths = [
            self.project_root / 'gas_output_phase7' / 'PersonaMapData.csv',
            self.project_root / 'python_scripts' / 'gas_output_phase7' / 'PersonaMapData.csv'
        ]

        found_path = None
        for path in possible_paths:
            if path.exists():
                found_path = path
                break

        self.assertIsNotNone(found_path, "PersonaMapData.csv が見つかりません")

        self.csv_path = found_path
        print(f"  [OK] ファイル発見: {self.csv_path}")

    def test_02_persona_map_data_structure(self):
        """PersonaMapData.csv 構造検証"""
        # test_01で設定されたパスを使用
        if not hasattr(self, 'csv_path'):
            self.test_01_persona_map_data_existence()

        df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

        # 行数確認（792行期待）
        self.assertGreater(len(df), 700, "PersonaMapData.csv は700行以上あるべき")
        print(f"  [OK] 行数: {len(df)}行")

        # カラム数確認（9列期待）
        expected_columns = 9
        self.assertEqual(len(df.columns), expected_columns,
                         f"PersonaMapData.csv は{expected_columns}列あるべき")
        print(f"  [OK] カラム数: {len(df.columns)}列")

        # 座標カラム確認（2列目=lat, 3列目=lng）
        lat_col = df.columns[1]
        lng_col = df.columns[2]

        # 座標が数値であることを確認
        self.assertTrue(pd.api.types.is_numeric_dtype(df[lat_col]),
                       f"{lat_col}は数値型であるべき")
        self.assertTrue(pd.api.types.is_numeric_dtype(df[lng_col]),
                       f"{lng_col}は数値型であるべき")

        # 座標範囲確認（日本国内: lat 25-46, lng 127-146）
        lat_min, lat_max = df[lat_col].min(), df[lat_col].max()
        lng_min, lng_max = df[lng_col].min(), df[lng_col].max()

        self.assertGreaterEqual(lat_min, 25, "緯度は25度以上であるべき（沖縄含む）")
        self.assertLessEqual(lat_max, 46, "緯度は46度以下であるべき")
        self.assertGreaterEqual(lng_min, 127, "経度は127度以上であるべき")
        self.assertLessEqual(lng_max, 146, "経度は146度以下であるべき")

        print(f"  [OK] 座標範囲: lat({lat_min:.2f}, {lat_max:.2f}), lng({lng_min:.2f}, {lng_max:.2f})")

    def test_03_persona_map_missing_coordinates(self):
        """PersonaMapData.csv 欠損座標確認"""
        if not hasattr(self, 'csv_path'):
            self.test_01_persona_map_data_existence()

        df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

        lat_col = df.columns[1]
        lng_col = df.columns[2]

        # 欠損値カウント
        lat_missing = df[lat_col].isna().sum()
        lng_missing = df[lng_col].isna().sum()

        total_missing = lat_missing + lng_missing

        # 欠損率計算
        missing_rate = (total_missing / (len(df) * 2)) * 100

        # 欠損率1%以下を期待（792地点中7地点以下）
        self.assertLess(missing_rate, 1.0,
                       f"座標欠損率が高すぎます: {missing_rate:.2f}%")

        print(f"  [OK] 座標欠損: {total_missing}件 ({missing_rate:.2f}%)")


class TestPersonaMobilityCrossValidation(unittest.TestCase):
    """PersonaMobilityCross.csv データ検証テスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        print("\n" + "=" * 70)
        print("Phase 1 データ検証テスト: PersonaMobilityCross.csv")
        print("=" * 70)
        cls.project_root = project_root

    def test_01_persona_mobility_cross_existence(self):
        """PersonaMobilityCross.csv 存在確認"""
        possible_paths = [
            self.project_root / 'gas_output_phase7' / 'PersonaMobilityCross.csv',
            self.project_root / 'python_scripts' / 'gas_output_phase7' / 'PersonaMobilityCross.csv'
        ]

        found_path = None
        for path in possible_paths:
            if path.exists():
                found_path = path
                break

        self.assertIsNotNone(found_path, "PersonaMobilityCross.csv が見つかりません")

        self.csv_path = found_path
        print(f"  [OK] ファイル発見: {self.csv_path}")

    def test_02_persona_mobility_cross_structure(self):
        """PersonaMobilityCross.csv 構造検証"""
        if not hasattr(self, 'csv_path'):
            self.test_01_persona_mobility_cross_existence()

        df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

        # 行数確認（11ペルソナ期待）
        self.assertGreaterEqual(len(df), 10, "PersonaMobilityCross.csv は10行以上あるべき")
        print(f"  [OK] 行数: {len(df)}行（ペルソナ数）")

        # カラム数確認（11列期待: ID, 名前, A, B, C, D, 合計, A%, B%, C%, D%）
        expected_columns = 11
        self.assertEqual(len(df.columns), expected_columns,
                         f"PersonaMobilityCross.csv は{expected_columns}列あるべき")
        print(f"  [OK] カラム数: {len(df.columns)}列")

    def test_03_persona_mobility_ratio_sum(self):
        """PersonaMobilityCross.csv 比率合計=100%検証"""
        if not hasattr(self, 'csv_path'):
            self.test_01_persona_mobility_cross_existence()

        df = pd.read_csv(self.csv_path, encoding='utf-8-sig')

        # 比率カラム（8-11列目: A%, B%, C%, D%）
        ratio_cols = df.columns[7:11]

        # 各行の比率合計を計算
        for idx, row in df.iterrows():
            ratio_sum = sum(row[col] for col in ratio_cols)

            # 100% ± 1.0% 許容範囲（丸め誤差を考慮）
            self.assertAlmostEqual(ratio_sum, 100.0, delta=1.0,
                                  msg=f"行{idx}の比率合計が100%ではありません: {ratio_sum:.2f}%")

        print(f"  [OK] 全{len(df)}行の比率合計=100%検証完了")


class TestCrossAnalysisEngineIntegration(unittest.TestCase):
    """cross_analysis_engine.py 統合テスト"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の初期化"""
        print("\n" + "=" * 70)
        print("Phase 1 統合テスト: CrossAnalysisEngine 全機能")
        print("=" * 70)
        cls.project_root = project_root

    def test_01_run_all_analyses_execution(self):
        """run_all_analyses() 全分析実行テスト"""
        engine = CrossAnalysisEngine(data_root=str(self.project_root))

        # 全分析実行
        engine.run_all_analyses()

        # 結果確認
        self.assertGreater(len(engine.results), 0, "少なくとも1件の分析結果があるべき")

        # 各分析結果の構造確認
        for key, result in engine.results.items():
            self.assertIsInstance(result, dict)
            self.assertIn('analysis_name', result)
            self.assertIn('dimensions', result)
            print(f"  [OK] {key}: {result['analysis_name']}完了")

    def test_02_json_output_verification(self):
        """JSON出力ファイル検証"""
        # CrossAnalysisResults.json が生成されているか確認
        possible_paths = [
            self.project_root / 'gas_output_insights' / 'CrossAnalysisResults.json',
            self.project_root / 'python_scripts' / 'gas_output_insights' / 'CrossAnalysisResults.json'
        ]

        found_path = None
        for path in possible_paths:
            if path.exists():
                found_path = path
                break

        if found_path is None:
            self.skipTest("CrossAnalysisResults.json が見つかりません（テスト実行順序の問題かも）")

        # JSON読み込み
        with open(found_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 構造検証
        self.assertIn('generated_at', data)
        self.assertIn('analysis_count', data)
        self.assertIn('data_sources_loaded', data)
        self.assertIn('results', data)

        print(f"  [OK] JSON出力検証完了: {found_path}")
        print(f"    - 分析件数: {data['analysis_count']}")
        print(f"    - データソース: {data['data_sources_loaded']}")


def run_phase1_tests():
    """Phase 1テスト実行メイン関数"""
    print("\n" + "=" * 70)
    print(" " * 15 + "Phase 1 実装ユニットテストスイート")
    print(" " * 20 + "MECE準拠テスト設計")
    print("=" * 70)
    print(f"\n実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"プロジェクトルート: {project_root}")

    # テストスイート作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストクラス追加（実行順序重要）
    suite.addTests(loader.loadTestsFromTestCase(TestCrossAnalysisEngineUnit))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonaMapDataValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPersonaMobilityCrossValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossAnalysisEngineIntegration))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # サマリー表示
    print("\n" + "=" * 70)
    print(" " * 25 + "テスト結果サマリー")
    print("=" * 70)
    print(f"  実行テスト数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  エラー: {len(result.errors)}")
    print(f"  スキップ: {len(result.skipped)}")

    # 成功率計算
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"\n  成功率: {success_rate:.1f}%")

        if success_rate == 100.0:
            print("\n  [SUCCESS] 全テスト合格！Phase 1実装は品質基準を満たしています。")
        elif success_rate >= 90.0:
            print("\n  [GOOD] 90%以上のテストが合格。優れた品質です。")
        elif success_rate >= 70.0:
            print("\n  [WARNING] 70%以上のテストが合格。改善の余地があります。")
        else:
            print("\n  [ERROR] テスト合格率が低すぎます。実装を見直してください。")

    print("=" * 70)

    return result


if __name__ == '__main__':
    result = run_phase1_tests()

    # 終了コード設定（CI/CD対応）
    sys.exit(0 if result.wasSuccessful() else 1)
