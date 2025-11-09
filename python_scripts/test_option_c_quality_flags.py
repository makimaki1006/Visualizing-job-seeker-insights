"""
オプションC: 完全統合のユニットテスト
品質フラグ追加機能のテスト
"""

import unittest
import pandas as pd
from data_quality_validator import DataQualityValidator


class TestQualityFlagsAggregation(unittest.TestCase):
    """集計結果への品質フラグ追加テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.validator_descriptive = DataQualityValidator(validation_mode='descriptive')
        self.validator_inferential = DataQualityValidator(validation_mode='inferential')

    def test_add_quality_flags_large_sample(self):
        """大サンプル（n≥100）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'キー': ['京都府京都市'],
            'カウント': [450]
        })

        result = self.validator_inferential.add_quality_flags_to_aggregation(
            test_df,
            count_column='カウント',
            validation_mode='inferential'
        )

        self.assertEqual(result.loc[0, 'サンプルサイズ区分'], 'LARGE')
        self.assertEqual(result.loc[0, '信頼性レベル'], 'HIGH')
        self.assertEqual(result.loc[0, '警告メッセージ'], 'なし')

    def test_add_quality_flags_medium_sample(self):
        """中サンプル（30≤n<100）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'キー': ['京都府○○市'],
            'カウント': [50]
        })

        result = self.validator_inferential.add_quality_flags_to_aggregation(
            test_df,
            count_column='カウント',
            validation_mode='inferential'
        )

        self.assertEqual(result.loc[0, 'サンプルサイズ区分'], 'MEDIUM')
        self.assertEqual(result.loc[0, '信頼性レベル'], 'MEDIUM')
        self.assertEqual(result.loc[0, '警告メッセージ'], 'なし')

    def test_add_quality_flags_small_sample(self):
        """小サンプル（10≤n<30）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'キー': ['京都府○○町'],
            'カウント': [15]
        })

        result = self.validator_inferential.add_quality_flags_to_aggregation(
            test_df,
            count_column='カウント',
            validation_mode='inferential'
        )

        self.assertEqual(result.loc[0, 'サンプルサイズ区分'], 'SMALL')
        self.assertEqual(result.loc[0, '信頼性レベル'], 'LOW')
        self.assertIn('参考データのみ', result.loc[0, '警告メッセージ'])
        self.assertIn('n=15', result.loc[0, '警告メッセージ'])

    def test_add_quality_flags_very_small_sample(self):
        """極小サンプル（n<10）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'キー': ['京都府○○村'],
            'カウント': [1]
        })

        result = self.validator_inferential.add_quality_flags_to_aggregation(
            test_df,
            count_column='カウント',
            validation_mode='inferential'
        )

        self.assertEqual(result.loc[0, 'サンプルサイズ区分'], 'VERY_SMALL')
        self.assertEqual(result.loc[0, '信頼性レベル'], 'CRITICAL')
        self.assertIn('推論には使用不可', result.loc[0, '警告メッセージ'])
        self.assertIn('n=1', result.loc[0, '警告メッセージ'])

    def test_add_quality_flags_descriptive_mode(self):
        """観察的記述モードの品質フラグテスト"""
        test_df = pd.DataFrame({
            'キー': ['京都府○○村'],
            'カウント': [1]
        })

        result = self.validator_descriptive.add_quality_flags_to_aggregation(
            test_df,
            count_column='カウント',
            validation_mode='descriptive'
        )

        self.assertEqual(result.loc[0, 'サンプルサイズ区分'], 'VERY_SMALL')
        self.assertEqual(result.loc[0, '信頼性レベル'], 'DESCRIPTIVE')
        self.assertEqual(result.loc[0, '警告メッセージ'], 'なし（観察的記述）')


class TestQualityFlagsCrosstab(unittest.TestCase):
    """クロス集計への品質フラグ追加テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.validator = DataQualityValidator(validation_mode='inferential')

    def test_add_quality_flags_sufficient_cell(self):
        """十分なセル（n≥30）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'education_level': ['高校'],
            'age_group': ['20代'],
            'カウント': [45]
        })

        result = self.validator.add_quality_flags_to_crosstab(
            test_df,
            count_column='カウント'
        )

        self.assertEqual(result.loc[0, 'セル品質'], 'SUFFICIENT')
        self.assertEqual(result.loc[0, '警告フラグ'], 'なし')
        self.assertEqual(result.loc[0, '警告メッセージ'], 'なし')

    def test_add_quality_flags_marginal_cell(self):
        """限界的なセル（5≤n<30）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'education_level': ['高校'],
            'age_group': ['30代'],
            'カウント': [12]
        })

        result = self.validator.add_quality_flags_to_crosstab(
            test_df,
            count_column='カウント'
        )

        self.assertEqual(result.loc[0, 'セル品質'], 'MARGINAL')
        self.assertEqual(result.loc[0, '警告フラグ'], '要注意')
        self.assertIn('セル数不足', result.loc[0, '警告メッセージ'])
        self.assertIn('n=12', result.loc[0, '警告メッセージ'])

    def test_add_quality_flags_insufficient_cell(self):
        """不十分なセル（n<5）の品質フラグテスト"""
        test_df = pd.DataFrame({
            'education_level': ['専門'],
            'age_group': ['40代'],
            'カウント': [3]
        })

        result = self.validator.add_quality_flags_to_crosstab(
            test_df,
            count_column='カウント'
        )

        self.assertEqual(result.loc[0, 'セル品質'], 'INSUFFICIENT')
        self.assertEqual(result.loc[0, '警告フラグ'], '使用不可')
        self.assertIn('セル数不足', result.loc[0, '警告メッセージ'])
        self.assertIn('n=3 < 5', result.loc[0, '警告メッセージ'])

    def test_add_quality_flags_multiple_cells(self):
        """複数セルの品質フラグテスト"""
        test_df = pd.DataFrame({
            'education_level': ['高校', '高校', '専門'],
            'age_group': ['20代', '30代', '40代'],
            'カウント': [45, 12, 3]
        })

        result = self.validator.add_quality_flags_to_crosstab(
            test_df,
            count_column='カウント'
        )

        # 十分なセル
        self.assertEqual(result.loc[0, 'セル品質'], 'SUFFICIENT')
        self.assertEqual(result.loc[0, '警告フラグ'], 'なし')

        # 限界的なセル
        self.assertEqual(result.loc[1, 'セル品質'], 'MARGINAL')
        self.assertEqual(result.loc[1, '警告フラグ'], '要注意')

        # 不十分なセル
        self.assertEqual(result.loc[2, 'セル品質'], 'INSUFFICIENT')
        self.assertEqual(result.loc[2, '警告フラグ'], '使用不可')


class TestSampleSizeCategory(unittest.TestCase):
    """サンプルサイズ区分判定テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.validator = DataQualityValidator()

    def test_sample_size_category_large(self):
        """LARGEカテゴリテスト（n≥100）"""
        self.assertEqual(self.validator._get_sample_size_category(100), 'LARGE')
        self.assertEqual(self.validator._get_sample_size_category(500), 'LARGE')
        self.assertEqual(self.validator._get_sample_size_category(1000), 'LARGE')

    def test_sample_size_category_medium(self):
        """MEDIUMカテゴリテスト（30≤n<100）"""
        self.assertEqual(self.validator._get_sample_size_category(30), 'MEDIUM')
        self.assertEqual(self.validator._get_sample_size_category(50), 'MEDIUM')
        self.assertEqual(self.validator._get_sample_size_category(99), 'MEDIUM')

    def test_sample_size_category_small(self):
        """SMALLカテゴリテスト（10≤n<30）"""
        self.assertEqual(self.validator._get_sample_size_category(10), 'SMALL')
        self.assertEqual(self.validator._get_sample_size_category(15), 'SMALL')
        self.assertEqual(self.validator._get_sample_size_category(29), 'SMALL')

    def test_sample_size_category_very_small(self):
        """VERY_SMALLカテゴリテスト（n<10）"""
        self.assertEqual(self.validator._get_sample_size_category(1), 'VERY_SMALL')
        self.assertEqual(self.validator._get_sample_size_category(5), 'VERY_SMALL')
        self.assertEqual(self.validator._get_sample_size_category(9), 'VERY_SMALL')


class TestCellQuality(unittest.TestCase):
    """セル品質判定テスト"""

    def setUp(self):
        """テスト前の準備"""
        self.validator = DataQualityValidator()

    def test_cell_quality_sufficient(self):
        """SUFFICIENT品質テスト（n≥30）"""
        result = self.validator._get_cell_quality(30)
        self.assertEqual(result['セル品質'], 'SUFFICIENT')
        self.assertEqual(result['警告フラグ'], 'なし')

    def test_cell_quality_marginal(self):
        """MARGINAL品質テスト（5≤n<30）"""
        result = self.validator._get_cell_quality(5)
        self.assertEqual(result['セル品質'], 'MARGINAL')
        self.assertEqual(result['警告フラグ'], '要注意')

        result = self.validator._get_cell_quality(29)
        self.assertEqual(result['セル品質'], 'MARGINAL')

    def test_cell_quality_insufficient(self):
        """INSUFFICIENT品質テスト（n<5）"""
        result = self.validator._get_cell_quality(4)
        self.assertEqual(result['セル品質'], 'INSUFFICIENT')
        self.assertEqual(result['警告フラグ'], '使用不可')

        result = self.validator._get_cell_quality(1)
        self.assertEqual(result['セル品質'], 'INSUFFICIENT')


if __name__ == '__main__':
    # テスト実行
    print("=" * 80)
    print("オプションC: 完全統合 - ユニットテスト")
    print("=" * 80)
    print()

    # テストスイート作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # テストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestQualityFlagsAggregation))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityFlagsCrosstab))
    suite.addTests(loader.loadTestsFromTestCase(TestSampleSizeCategory))
    suite.addTests(loader.loadTestsFromTestCase(TestCellQuality))

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print()
    print("=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("[OK] すべてのテストが成功しました！")
        exit(0)
    else:
        print("[FAIL] 一部のテストが失敗しました")
        exit(1)
