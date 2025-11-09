"""
包括的テストスイート v2.3
ユニットテスト、統合テスト、E2Eテストを網羅
"""

import unittest
import pandas as pd
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from data_normalizer import DataNormalizer
from config import (
    DEFAULT_AGE_BINS,
    DEFAULT_AGE_LABELS,
    MAX_DESIRED_LOCATIONS,
    OUTPUT_DIR,
    GEOCACHE_FILE,
    CREATE_BACKUP,
    BACKUP_TIMESTAMP_FORMAT
)

# テストデータパス
TEST_DATA_PATH = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251027_180947.csv")


class TestDataNormalizerUnit(unittest.TestCase):
    """ユニットテスト: DataNormalizerの各メソッド"""

    def setUp(self):
        """テスト前の準備"""
        self.normalizer = DataNormalizer()

    # ========================================
    # 1. parse_age_gender() テスト
    # ========================================

    def test_parse_age_gender_normal(self):
        """正常系: 標準的な年齢・性別"""
        result = self.normalizer.parse_age_gender("49歳 女性")
        self.assertEqual(result['age'], 49)
        self.assertEqual(result['gender'], '女性')

    def test_parse_age_gender_male(self):
        """正常系: 男性"""
        result = self.normalizer.parse_age_gender("35歳 男性")
        self.assertEqual(result['age'], 35)
        self.assertEqual(result['gender'], '男性')

    def test_parse_age_gender_boundary_young(self):
        """境界値: 若年層"""
        result = self.normalizer.parse_age_gender("16歳 女性")
        self.assertEqual(result['age'], 16)

    def test_parse_age_gender_boundary_old(self):
        """境界値: 高齢層"""
        result = self.normalizer.parse_age_gender("92歳 男性")
        self.assertEqual(result['age'], 92)

    def test_parse_age_gender_empty(self):
        """異常系: 空文字"""
        result = self.normalizer.parse_age_gender("")
        self.assertIsNone(result['age'])
        self.assertIsNone(result['gender'])

    def test_parse_age_gender_nan(self):
        """異常系: NaN"""
        result = self.normalizer.parse_age_gender(pd.NA)
        self.assertIsNone(result['age'])
        self.assertIsNone(result['gender'])

    def test_parse_age_gender_malformed(self):
        """異常系: 不正な形式"""
        result = self.normalizer.parse_age_gender("年齢不明")
        self.assertIsNone(result['age'])
        self.assertIsNone(result['gender'])

    # ========================================
    # 2. parse_location() テスト
    # ========================================

    def test_parse_location_normal(self):
        """正常系: 標準的な地域"""
        result = self.normalizer.parse_location("京都府京都市上京区")
        self.assertEqual(result['prefecture'], '京都府')
        self.assertEqual(result['municipality'], '京都市上京区')

    def test_parse_location_no_municipality(self):
        """正常系: 市区町村なし"""
        result = self.normalizer.parse_location("京都府")
        self.assertEqual(result['prefecture'], '京都府')
        self.assertIsNone(result['municipality'])

    def test_parse_location_tokyo(self):
        """正常系: 東京都"""
        result = self.normalizer.parse_location("東京都新宿区")
        self.assertEqual(result['prefecture'], '東京都')
        self.assertEqual(result['municipality'], '新宿区')

    def test_parse_location_hokkaido(self):
        """正常系: 北海道"""
        result = self.normalizer.parse_location("北海道札幌市")
        self.assertEqual(result['prefecture'], '北海道')
        self.assertEqual(result['municipality'], '札幌市')

    def test_parse_location_empty(self):
        """異常系: 空文字"""
        result = self.normalizer.parse_location("")
        self.assertIsNone(result['prefecture'])
        self.assertIsNone(result['municipality'])

    # ========================================
    # 3. parse_desired_start() テスト（改善版）
    # ========================================

    def test_parse_desired_start_immediate(self):
        """正常系: 今すぐ"""
        result = self.normalizer.parse_desired_start("今すぐに（2025/10/16時点）")
        self.assertEqual(result['urgency_score'], 5)
        self.assertEqual(result['text'], '今すぐに')
        self.assertIsNotNone(result['date'])
        self.assertIsNotNone(result['urgency_score_dynamic'])

    def test_parse_desired_start_within_1month(self):
        """正常系: 1ヶ月以内"""
        result = self.normalizer.parse_desired_start("1ヶ月以内（2025/10/20時点）")
        self.assertEqual(result['urgency_score'], 4)

    def test_parse_desired_start_within_3months(self):
        """正常系: 3ヶ月以内"""
        result = self.normalizer.parse_desired_start("3ヶ月以内（2025/10/15時点）")
        self.assertEqual(result['urgency_score'], 3)

    def test_parse_desired_start_over_3months(self):
        """正常系: 3ヶ月以上先"""
        result = self.normalizer.parse_desired_start("3ヶ月以上先（2025/09/01時点）")
        self.assertEqual(result['urgency_score'], 2)

    def test_parse_desired_start_if_opportunity(self):
        """正常系: 機会があれば"""
        result = self.normalizer.parse_desired_start("機会があれば（2025/08/01時点）")
        self.assertEqual(result['urgency_score'], 1)

    def test_parse_desired_start_dynamic_scoring(self):
        """動的スコアリング: 経過日数による減衰"""
        reference_date = datetime(2025, 11, 28)  # 基準日: 2025/11/28
        result = self.normalizer.parse_desired_start(
            "今すぐに（2025/10/28時点）",
            reference_date=reference_date
        )
        self.assertEqual(result['urgency_score'], 5)
        self.assertEqual(result['days_elapsed'], 31)  # 31日経過
        # 動的スコア: 5 - (31/60) = 5 - 0.52 = 4.48
        self.assertAlmostEqual(result['urgency_score_dynamic'], 4.48, places=1)

    def test_parse_desired_start_zero_vs_one(self):
        """未記載（0）と機会があれば（1）の区別"""
        result_none = self.normalizer.parse_desired_start("")
        result_opportunity = self.normalizer.parse_desired_start("機会があれば")

        self.assertEqual(result_none['urgency_score'], 0)
        self.assertEqual(result_opportunity['urgency_score'], 1)
        self.assertNotEqual(result_none['urgency_score'], result_opportunity['urgency_score'])

    def test_parse_desired_start_empty(self):
        """異常系: 空文字"""
        result = self.normalizer.parse_desired_start("")
        self.assertEqual(result['urgency_score'], 0)
        self.assertIsNone(result['text'])
        self.assertIsNone(result['date'])

    # ========================================
    # 4. parse_career() テスト（改善版）
    # ========================================

    def test_parse_career_normal(self):
        """正常系: 標準的な学歴"""
        result = self.normalizer.parse_career("ライフクリエイト科(高等学校)(2016年4月卒業)")
        self.assertEqual(result['level'], '高校')
        self.assertEqual(result['field'], 'ライフクリエイト科')
        self.assertEqual(result['grad_year'], 2016)
        self.assertFalse(result['is_current'])

    def test_parse_career_university(self):
        """正常系: 大学"""
        result = self.normalizer.parse_career("経済学部(大学)(2020年3月卒業)")
        self.assertEqual(result['level'], '大学')
        self.assertEqual(result['field'], '経済学部')
        self.assertEqual(result['grad_year'], 2020)

    def test_parse_career_graduate_school(self):
        """正常系: 大学院（最高学歴）"""
        result = self.normalizer.parse_career("工学研究科(大学院)(2022年3月卒業)")
        self.assertEqual(result['level'], '大学院')

    def test_parse_career_multiple_educations(self):
        """複数学歴: 大学と高校"""
        result = self.normalizer.parse_career(
            "経済学部(大学)(2020年3月卒業)、○○科(高校)(2016年3月卒業)"
        )
        self.assertEqual(result['level'], '大学')  # 最高学歴
        self.assertIn('大学', result['all_levels'])
        self.assertIn('高校', result['all_levels'])
        self.assertEqual(len(result['all_levels']), 2)

    def test_parse_career_currently_enrolled(self):
        """在学中判定"""
        result = self.normalizer.parse_career("経済学部(大学)(在学中)")
        self.assertEqual(result['level'], '大学')
        self.assertTrue(result['is_current'])

    def test_parse_career_dropout(self):
        """中退判定"""
        result = self.normalizer.parse_career("経済学部(大学)(中退)")
        self.assertTrue(result['is_current'])  # 中退も is_current=True

    def test_parse_career_grad_year_pattern1(self):
        """卒業年度パターン1: YYYY年MM月卒業"""
        result = self.normalizer.parse_career("○○科(高校)(2016年3月卒業)")
        self.assertEqual(result['grad_year'], 2016)

    def test_parse_career_grad_year_pattern2(self):
        """卒業年度パターン2: YYYY年卒"""
        result = self.normalizer.parse_career("○○科(高校)(2016年卒)")
        self.assertEqual(result['grad_year'], 2016)

    def test_parse_career_grad_year_pattern3(self):
        """卒業年度パターン3: YYYY/MM卒業"""
        result = self.normalizer.parse_career("○○科(高校)(2016/03卒業)")
        self.assertEqual(result['grad_year'], 2016)

    def test_parse_career_junior_high(self):
        """中学レベル"""
        result = self.normalizer.parse_career("○○中学校(2013年3月卒業)")
        self.assertEqual(result['level'], '中学')

    def test_parse_career_empty(self):
        """異常系: 空文字"""
        result = self.normalizer.parse_career("")
        self.assertEqual(result['level'], 'なし')
        self.assertIsNone(result['field'])
        self.assertIsNone(result['grad_year'])

    # ========================================
    # 5. parse_qualifications() テスト
    # ========================================

    def test_parse_qualifications_normal(self):
        """正常系: 複数資格"""
        result = self.normalizer.parse_qualifications("介護福祉士,自動車運転免許")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], '介護福祉士')
        self.assertEqual(result[0]['category'], '国家資格')
        self.assertEqual(result[1]['name'], '自動車運転免許')
        self.assertEqual(result[1]['category'], '免許')

    def test_parse_qualifications_planned(self):
        """資格取得予定"""
        result = self.normalizer.parse_qualifications("介護福祉士取得予定")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], '介護福祉士')
        self.assertTrue(result[0]['is_planned'])

    def test_parse_qualifications_empty(self):
        """異常系: 空文字"""
        result = self.normalizer.parse_qualifications("")
        self.assertEqual(len(result), 0)

    # ========================================
    # 6. cap_desired_location_count() テスト
    # ========================================

    def test_cap_desired_location_count_normal(self):
        """正常系: 上限以下"""
        result = self.normalizer.cap_desired_location_count(30, max_count=50)
        self.assertEqual(result, 30)

    def test_cap_desired_location_count_over_limit(self):
        """上限超過: 491 → 50"""
        result = self.normalizer.cap_desired_location_count(491, max_count=50)
        self.assertEqual(result, 50)

    def test_cap_desired_location_count_exact_limit(self):
        """境界値: ちょうど50"""
        result = self.normalizer.cap_desired_location_count(50, max_count=50)
        self.assertEqual(result, 50)


class TestDataNormalizerIntegration(unittest.TestCase):
    """統合テスト: normalize_dataframe()全体動作"""

    def setUp(self):
        """テスト前の準備"""
        self.normalizer = DataNormalizer()

    def test_normalize_dataframe_basic(self):
        """基本的な正規化処理"""
        df = pd.DataFrame({
            'age_gender': ['49歳 女性', '35歳 男性'],
            'location': ['京都府京都市上京区', '大阪府大阪市'],
            'desired_start': ['今すぐに（2025/10/16時点）', '1ヶ月以内（2025/10/20時点）'],
            'career': ['ライフクリエイト科(高等学校)(2016年4月卒業)', '経済学部(大学)(2020年3月卒業)'],
            'desired_area': ['奈良県奈良市,京都府木津川市', '大阪府大阪市']
        })

        result = self.normalizer.normalize_dataframe(df, verbose=False)

        # age_gender分離
        self.assertIn('age', result.columns)
        self.assertIn('gender', result.columns)
        self.assertEqual(result['age'].iloc[0], 49)
        self.assertEqual(result['gender'].iloc[0], '女性')

        # location分離
        self.assertIn('residence_pref', result.columns)
        self.assertIn('residence_muni', result.columns)
        self.assertEqual(result['residence_pref'].iloc[0], '京都府')

        # desired_start正規化（改善版）
        self.assertIn('urgency_score', result.columns)
        self.assertIn('urgency_score_dynamic', result.columns)
        self.assertIn('days_elapsed', result.columns)
        self.assertEqual(result['urgency_score'].iloc[0], 5)

        # career正規化（改善版）
        self.assertIn('education_level', result.columns)
        self.assertIn('is_currently_enrolled', result.columns)
        self.assertIn('all_education_levels', result.columns)
        self.assertEqual(result['education_level'].iloc[0], '高校')
        self.assertEqual(result['education_level'].iloc[1], '大学')

    def test_normalize_dataframe_with_missing_values(self):
        """欠損値を含むデータ"""
        df = pd.DataFrame({
            'age_gender': ['49歳 女性', None],
            'location': ['京都府京都市', ''],
            'desired_start': ['今すぐに（2025/10/16時点）', None],
            'career': ['○○科(高校)(2016年卒)', ''],
            'desired_area': ['京都府', None]
        })

        result = self.normalizer.normalize_dataframe(df, verbose=False, apply_missing_policy=True)

        # 欠損値処理の確認
        self.assertTrue(result['age'].iloc[1] is pd.NA or pd.isna(result['age'].iloc[1]))
        self.assertEqual(result['urgency_score'].iloc[1], 0)  # デフォルト値

    def test_normalize_dataframe_cap_desired_locations(self):
        """希望勤務地数の上限適用"""
        # 491箇所の希望勤務地を生成（カンマ区切り）
        many_locations = ','.join(['京都府' for _ in range(491)])

        df = pd.DataFrame({
            'age_gender': ['49歳 女性'],
            'location': ['京都府'],
            'desired_area': [many_locations]
        })

        result = self.normalizer.normalize_dataframe(
            df,
            cap_desired_locations=True,
            max_desired_locations=50,
            verbose=False
        )

        self.assertIn('希望勤務地数', result.columns)
        self.assertIn('希望勤務地数_raw', result.columns)
        self.assertEqual(result['希望勤務地数_raw'].iloc[0], 491)
        self.assertEqual(result['希望勤務地数'].iloc[0], 50)


class TestConfigIntegration(unittest.TestCase):
    """統合テスト: config.pyの設定読み込み"""

    def test_config_age_bins(self):
        """年齢層定義の確認"""
        self.assertEqual(len(DEFAULT_AGE_BINS), 6)
        self.assertEqual(len(DEFAULT_AGE_LABELS), 5)
        self.assertEqual(DEFAULT_AGE_BINS, [0, 29, 39, 49, 59, 100])

    def test_config_max_desired_locations(self):
        """希望勤務地数上限の確認"""
        self.assertEqual(MAX_DESIRED_LOCATIONS, 50)

    def test_config_paths(self):
        """パス設定の確認"""
        self.assertTrue(OUTPUT_DIR.exists() or OUTPUT_DIR.parent.exists())
        self.assertIsInstance(GEOCACHE_FILE, Path)

    def test_config_backup_settings(self):
        """バックアップ設定の確認"""
        self.assertIsInstance(CREATE_BACKUP, bool)
        self.assertIsInstance(BACKUP_TIMESTAMP_FORMAT, str)


class TestEndToEnd(unittest.TestCase):
    """E2Eテスト: 実データでの全処理"""

    @classmethod
    def setUpClass(cls):
        """テストクラス全体の準備"""
        if not TEST_DATA_PATH.exists():
            raise FileNotFoundError(f"テストデータが見つかりません: {TEST_DATA_PATH}")

    def test_e2e_data_loading_and_normalization(self):
        """E2E: データ読み込みと正規化"""
        # データ読み込み
        df = pd.read_csv(TEST_DATA_PATH, encoding='utf-8-sig', nrows=100)
        self.assertGreater(len(df), 0)

        # 正規化
        normalizer = DataNormalizer()
        df_normalized = normalizer.normalize_dataframe(df, verbose=False)

        # 必須カラムの確認
        required_columns = [
            'age', 'gender',
            'residence_pref', 'residence_muni',
            'urgency_score', 'urgency_score_dynamic', 'days_elapsed',
            'education_level', 'is_currently_enrolled', 'all_education_levels'
        ]

        for col in required_columns:
            self.assertIn(col, df_normalized.columns, f"カラム '{col}' が存在しません")

    def test_e2e_backup_function(self):
        """E2E: バックアップ機能"""
        # テスト用の一時ファイル作成
        test_output_dir = OUTPUT_DIR / "test_backup"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        test_phase_dir = test_output_dir / "phase1"
        test_phase_dir.mkdir(parents=True, exist_ok=True)

        test_file = test_phase_dir / "test.csv"
        test_file.write_text("test data")

        # バックアップディレクトリ
        backup_dir = test_output_dir / "backup"

        try:
            # バックアップ実行（模擬）
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime(BACKUP_TIMESTAMP_FORMAT)
            backup_file = backup_dir / f"test_{timestamp}.csv"
            shutil.copy2(test_file, backup_file)

            # 検証
            self.assertTrue(backup_file.exists())
            self.assertEqual(backup_file.read_text(), "test data")

        finally:
            # クリーンアップ
            if test_output_dir.exists():
                shutil.rmtree(test_output_dir)

    def test_e2e_output_file_validation(self):
        """E2E: 出力ファイル検証"""
        # 実際の出力ディレクトリの確認
        if OUTPUT_DIR.exists():
            phase1_dir = OUTPUT_DIR / "phase1"
            if phase1_dir.exists():
                csv_files = list(phase1_dir.glob("*.csv"))
                self.assertGreater(len(csv_files), 0, "Phase1のCSVファイルが存在しません")


def run_single_test_iteration(iteration_number: int):
    """単一のテスト反復実行"""
    print(f"\n{'=' * 80}")
    print(f"テスト反復 #{iteration_number}")
    print(f"{'=' * 80}\n")

    # テストスイートの作成
    suite = unittest.TestSuite()

    # ユニットテスト
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataNormalizerUnit))

    # 統合テスト
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataNormalizerIntegration))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestConfigIntegration))

    # E2Eテスト
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestEndToEnd))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


def main():
    """メイン関数: 10回反復テスト"""
    print("=" * 80)
    print("包括的テストスイート v2.3")
    print("ユニットテスト、統合テスト、E2Eテストを10回反復実行")
    print("=" * 80)

    all_results = []

    for i in range(1, 11):
        result = run_single_test_iteration(i)
        all_results.append({
            'iteration': i,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        })

    # 最終サマリー
    print("\n" + "=" * 80)
    print("最終サマリー: 10回反復テスト結果")
    print("=" * 80)

    total_tests = 0
    total_failures = 0
    total_errors = 0
    success_count = 0

    for result in all_results:
        total_tests += result['tests_run']
        total_failures += result['failures']
        total_errors += result['errors']
        if result['success']:
            success_count += 1

        status = "[OK] 成功" if result['success'] else "[NG] 失敗"
        print(f"反復 #{result['iteration']:2d}: {status} | "
              f"テスト {result['tests_run']:3d}件 | "
              f"失敗 {result['failures']:2d}件 | "
              f"エラー {result['errors']:2d}件")

    print("\n" + "-" * 80)
    print(f"合計テスト実行数: {total_tests}件")
    print(f"合計失敗数: {total_failures}件")
    print(f"合計エラー数: {total_errors}件")
    print(f"成功率: {success_count}/10回 ({success_count * 10}%)")

    if success_count == 10 and total_failures == 0 and total_errors == 0:
        print("\n[SUCCESS] すべてのテストが10回連続で成功しました！")
        return 0
    else:
        print("\n[FAILED] 一部のテストが失敗しました。")
        return 1


if __name__ == "__main__":
    exit(main())
