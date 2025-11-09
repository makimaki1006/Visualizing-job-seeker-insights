#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市町村別ペルソナ分析機能の統合テストスイート
テスト範囲: Python実行 → データ生成 → データ整合性検証
"""

import pandas as pd
import json
from pathlib import Path
import sys

class MunicipalityPersonaTest:
    """市町村別ペルソナ分析テスト"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / 'data' / 'output_v2' / 'phase3'
        self.phase1_dir = self.base_dir / 'data' / 'output_v2' / 'phase1'
        self.test_results = []

    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 80)
        print("市町村別ペルソナ分析 統合テストスイート")
        print("=" * 80)
        print()

        tests = [
            ("ファイル存在確認", self.test_file_existence),
            ("データ構造検証", self.test_data_structure),
            ("市町村数検証", self.test_municipality_count),
            ("市町村内シェア計算検証", self.test_market_share_calculation),
            ("データ整合性検証", self.test_data_consistency),
            ("人数合計検証", self.test_count_totals),
            ("統計値検証", self.test_statistical_values),
            ("サンプルデータ詳細確認", self.test_sample_data_details),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                    self.test_results.append({
                        'test': test_name,
                        'status': 'PASS',
                        'message': result
                    })
                    print(f"[PASS] {test_name}")
                    print(f"   {result}")
                else:
                    failed += 1
                    self.test_results.append({
                        'test': test_name,
                        'status': 'FAIL',
                        'message': 'テスト失敗'
                    })
                    print(f"[FAIL] {test_name}")
            except Exception as e:
                failed += 1
                self.test_results.append({
                    'test': test_name,
                    'status': 'ERROR',
                    'message': str(e)
                })
                print(f"[ERROR] {test_name}")
                print(f"   エラー: {e}")
            print()

        # サマリー
        print("=" * 80)
        print(f"テスト結果サマリー")
        print("=" * 80)
        print(f"[OK] 成功: {passed}/{len(tests)}")
        print(f"[NG] 失敗: {failed}/{len(tests)}")
        print(f"成功率: {passed/len(tests)*100:.1f}%")
        print()

        # 結果をJSONで保存
        result_path = self.base_dir / 'tests' / 'results' / 'MUNICIPALITY_PERSONA_TEST_RESULTS.json'
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_tests': len(tests),
                'passed': passed,
                'failed': failed,
                'success_rate': passed/len(tests)*100,
                'test_results': self.test_results
            }, f, ensure_ascii=False, indent=2)
        print(f"[FILE] テスト結果を保存: {result_path}")

        return passed == len(tests)

    def test_file_existence(self):
        """ファイル存在確認"""
        expected_files = [
            self.output_dir / 'PersonaSummaryByMunicipality.csv',
            self.phase1_dir / 'DesiredWork.csv',
            self.phase1_dir / 'Applicants.csv'
        ]

        for file_path in expected_files:
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        return f"3つの必須ファイルが存在します"

    def test_data_structure(self):
        """データ構造検証"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')

        expected_columns = [
            'municipality', 'persona_name', 'age_group', 'gender', 'has_national_license',
            'count', 'total_in_municipality', 'market_share_pct', 'avg_age',
            'avg_desired_areas', 'avg_qualifications', 'employment_rate'
        ]

        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"不足しているカラム: {missing_columns}")

        return f"12カラム全て存在（{len(df)}行）"

    def test_municipality_count(self):
        """市町村数検証"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')
        unique_municipalities = df['municipality'].nunique()

        # DesiredWork.csvから市町村数を確認
        desired_work_df = pd.read_csv(self.phase1_dir / 'DesiredWork.csv', encoding='utf-8-sig')
        expected_municipalities = desired_work_df['desired_location_full'].nunique()

        if unique_municipalities != expected_municipalities:
            raise ValueError(
                f"市町村数が一致しません: 実際={unique_municipalities}, 期待={expected_municipalities}"
            )

        return f"市町村数: {unique_municipalities}（DesiredWork.csvと一致）"

    def test_market_share_calculation(self):
        """市町村内シェア計算検証"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')

        # ランダムに5市町村をサンプリング
        sample_municipalities = df['municipality'].unique()[:5]

        for municipality in sample_municipalities:
            muni_df = df[df['municipality'] == municipality]

            # 各ペルソナのシェア検証
            for _, row in muni_df.iterrows():
                expected_share = (row['count'] / row['total_in_municipality']) * 100
                actual_share = row['market_share_pct']

                # 誤差許容範囲: 0.01%
                if abs(expected_share - actual_share) > 0.01:
                    raise ValueError(
                        f"市町村内シェア計算エラー: {municipality} - {row['persona_name']}\n"
                        f"期待値={expected_share:.2f}%, 実際={actual_share:.2f}%"
                    )

        return f"5市町村のシェア計算が正確（誤差<0.01%）"

    def test_data_consistency(self):
        """データ整合性検証"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')
        applicants_df = pd.read_csv(self.phase1_dir / 'Applicants.csv', encoding='utf-8-sig')
        desired_work_df = pd.read_csv(self.phase1_dir / 'DesiredWork.csv', encoding='utf-8-sig')

        # 市町村ごとの総人数チェック
        sample_municipalities = df['municipality'].unique()[:3]

        for municipality in sample_municipalities:
            # PersonaSummaryByMunicipalityの総人数
            muni_df = df[df['municipality'] == municipality]
            declared_total = muni_df['total_in_municipality'].iloc[0]

            # DesiredWork.csvから実際の人数を計算
            actual_applicant_ids = desired_work_df[
                desired_work_df['desired_location_full'] == municipality
            ]['applicant_id'].unique()
            actual_total = len(actual_applicant_ids)

            if declared_total != actual_total:
                raise ValueError(
                    f"市町村内総人数が一致しません: {municipality}\n"
                    f"宣言された総数={declared_total}, 実際の総数={actual_total}"
                )

        return f"3市町村の総人数がDesiredWork.csvと一致"

    def test_count_totals(self):
        """人数合計検証"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')

        # 各市町村でペルソナの人数合計が total_in_municipality と一致するか
        sample_municipalities = df['municipality'].unique()[:5]

        for municipality in sample_municipalities:
            muni_df = df[df['municipality'] == municipality]
            sum_counts = muni_df['count'].sum()
            declared_total = muni_df['total_in_municipality'].iloc[0]

            if sum_counts != declared_total:
                raise ValueError(
                    f"ペルソナ人数合計が一致しません: {municipality}\n"
                    f"ペルソナ合計={sum_counts}, 宣言された総数={declared_total}"
                )

        return f"5市町村でペルソナ人数合計が総数と一致"

    def test_statistical_values(self):
        """統計値検証"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')

        # 統計値の範囲チェック
        issues = []

        # 市町村内シェア: 0% ~ 100%
        if df['market_share_pct'].min() < 0 or df['market_share_pct'].max() > 100:
            issues.append(f"市町村内シェアが範囲外: {df['market_share_pct'].min():.2f}% ~ {df['market_share_pct'].max():.2f}%")

        # 平均年齢: 15 ~ 100歳（高校生も求職者として存在）
        if df['avg_age'].min() < 15 or df['avg_age'].max() > 100:
            issues.append(f"平均年齢が範囲外: {df['avg_age'].min():.1f}歳 ~ {df['avg_age'].max():.1f}歳")

        # 就業率: 0% ~ 100%
        if df['employment_rate'].min() < 0 or df['employment_rate'].max() > 1:
            issues.append(f"就業率が範囲外: {df['employment_rate'].min():.2%} ~ {df['employment_rate'].max():.2%}")

        if issues:
            raise ValueError("\n".join(issues))

        return f"統計値が合理的な範囲内（シェア: 0-100%, 年齢: 15-100歳, 就業率: 0-100%）"

    def test_sample_data_details(self):
        """サンプルデータ詳細確認"""
        df = pd.read_csv(self.output_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')

        # 京都市伏見区のデータを詳細確認
        target_municipality = '京都府京都市伏見区'
        if target_municipality in df['municipality'].values:
            muni_df = df[df['municipality'] == target_municipality]

            # 最も人数の多いペルソナ
            top_persona = muni_df.nlargest(1, 'count').iloc[0]

            # 最も人数の少ないペルソナ
            bottom_persona = muni_df.nsmallest(1, 'count').iloc[0]

            details = (
                f"{target_municipality}:\n"
                f"  総希望者数: {muni_df['total_in_municipality'].iloc[0]}人\n"
                f"  ペルソナ種類数: {len(muni_df)}\n"
                f"  最多ペルソナ: {top_persona['persona_name']} ({top_persona['count']}人, {top_persona['market_share_pct']:.2f}%)\n"
                f"  最少ペルソナ: {bottom_persona['persona_name']} ({bottom_persona['count']}人, {bottom_persona['market_share_pct']:.2f}%)"
            )
            return details
        else:
            return f"サンプル市町村（{target_municipality}）が見つかりませんでした"

if __name__ == '__main__':
    tester = MunicipalityPersonaTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
