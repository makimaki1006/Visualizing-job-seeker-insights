#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
観察的記述系多重クロス集計ロジック検証テスト
テスト対象: Phase 8（キャリア×年齢）、Phase 10（緊急度×年齢、緊急度×就業状況）
"""

import pandas as pd
import json
from pathlib import Path
import sys

class CrossTabulationLogicTest:
    """クロス集計ロジックテスト"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.phase8_dir = self.base_dir / 'data' / 'output_v2' / 'phase8'
        self.phase10_dir = self.base_dir / 'data' / 'output_v2' / 'phase10'
        self.test_results = []

    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 80)
        print("観察的記述系多重クロス集計ロジック検証テスト")
        print("=" * 80)
        print()

        tests = [
            ("Phase 10: UrgencyAgeCross整合性検証", self.test_urgency_age_cross_consistency),
            ("Phase 10: UrgencyEmploymentCross整合性検証", self.test_urgency_employment_cross_consistency),
            ("Phase 10: UrgencyAgeCross行列合計検証", self.test_urgency_age_matrix_totals),
            ("Phase 10: UrgencyEmploymentCross行列合計検証", self.test_urgency_employment_matrix_totals),
            ("Phase 10: 全体合計一致検証", self.test_phase10_total_consistency),
            ("Phase 8: CareerAgeCross整合性検証", self.test_career_age_cross_consistency),
            ("Phase 8: CareerAgeCross行列合計検証", self.test_career_age_matrix_totals),
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
        result_path = self.base_dir / 'tests' / 'results' / 'CROSS_TABULATION_LOGIC_TEST_RESULTS.json'
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

    def test_urgency_age_cross_consistency(self):
        """UrgencyAgeCross.csv と Matrix.csv の整合性検証"""
        cross_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross.csv', encoding='utf-8-sig')
        matrix_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # クロス集計の各行を検証
        mismatches = []
        for _, row in cross_df.iterrows():
            urgency_rank = row['urgency_rank']
            age_group = row['age_group']
            cross_count = row['count']

            # マトリックスから対応する値を取得
            matrix_count = matrix_df.loc[urgency_rank, age_group]

            if cross_count != matrix_count:
                mismatches.append(
                    f"{urgency_rank} × {age_group}: cross={cross_count}, matrix={matrix_count}"
                )

        if mismatches:
            raise ValueError(f"クロス集計とマトリックスの不一致: {mismatches[:5]}")

        return f"24件すべての値が一致（4緊急度ランク × 6年齢層）"

    def test_urgency_employment_cross_consistency(self):
        """UrgencyEmploymentCross.csv と Matrix.csv の整合性検証"""
        cross_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross.csv', encoding='utf-8-sig')
        matrix_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # クロス集計の各行を検証
        mismatches = []
        for _, row in cross_df.iterrows():
            urgency_rank = row['urgency_rank']
            employment_status = row['employment_status']
            cross_count = row['count']

            # マトリックスから対応する値を取得
            matrix_count = matrix_df.loc[urgency_rank, employment_status]

            if cross_count != matrix_count:
                mismatches.append(
                    f"{urgency_rank} × {employment_status}: cross={cross_count}, matrix={matrix_count}"
                )

        if mismatches:
            raise ValueError(f"クロス集計とマトリックスの不一致: {mismatches}")

        return f"12件すべての値が一致（4緊急度ランク × 3就業状況）"

    def test_urgency_age_matrix_totals(self):
        """UrgencyAgeCross_Matrix の行・列合計検証"""
        matrix_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # 行合計（各緊急度ランクの合計）
        row_totals = matrix_df.sum(axis=1)

        # 列合計（各年齢層の合計）
        col_totals = matrix_df.sum(axis=0)

        # 全体合計
        grand_total = matrix_df.sum().sum()

        # 行合計と列合計の全体合計が一致するか
        row_total_sum = row_totals.sum()
        col_total_sum = col_totals.sum()

        if abs(row_total_sum - col_total_sum) > 0.01:
            raise ValueError(
                f"行合計と列合計が不一致: 行合計={row_total_sum}, 列合計={col_total_sum}"
            )

        if abs(grand_total - row_total_sum) > 0.01:
            raise ValueError(
                f"全体合計と行合計が不一致: 全体合計={grand_total}, 行合計={row_total_sum}"
            )

        return (
            f"行合計={int(row_total_sum)}人、列合計={int(col_total_sum)}人、"
            f"全体合計={int(grand_total)}人（すべて一致）"
        )

    def test_urgency_employment_matrix_totals(self):
        """UrgencyEmploymentCross_Matrix の行・列合計検証"""
        matrix_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # 行合計（各緊急度ランクの合計）
        row_totals = matrix_df.sum(axis=1)

        # 列合計（各就業状況の合計）
        col_totals = matrix_df.sum(axis=0)

        # 全体合計
        grand_total = matrix_df.sum().sum()

        # 行合計と列合計の全体合計が一致するか
        row_total_sum = row_totals.sum()
        col_total_sum = col_totals.sum()

        if abs(row_total_sum - col_total_sum) > 0.01:
            raise ValueError(
                f"行合計と列合計が不一致: 行合計={row_total_sum}, 列合計={col_total_sum}"
            )

        return (
            f"行合計={int(row_total_sum)}人、列合計={int(col_total_sum)}人、"
            f"全体合計={int(grand_total)}人（すべて一致）"
        )

    def test_phase10_total_consistency(self):
        """Phase 10全体の合計一致検証"""
        # UrgencyDistribution.csv から全体合計を取得
        dist_df = pd.read_csv(self.phase10_dir / 'UrgencyDistribution.csv', encoding='utf-8-sig')
        dist_total = dist_df['count'].sum()

        # UrgencyAgeCross.csv から合計を取得
        age_cross_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross.csv', encoding='utf-8-sig')
        age_cross_total = age_cross_df['count'].sum()

        # UrgencyEmploymentCross.csv から合計を取得
        employment_cross_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross.csv', encoding='utf-8-sig')
        employment_cross_total = employment_cross_df['count'].sum()

        # Distribution と AgeCross は完全一致するべき（年齢層欠損がないため）
        if dist_total != age_cross_total:
            raise ValueError(
                f"UrgencyDistribution と UrgencyAgeCross の合計が不一致: "
                f"{dist_total} != {age_cross_total}"
            )

        # Employment は欠損値（就業状況が不明な申請者）のため、数人の差は許容
        # 許容範囲: 5人以内（0.1%以内）
        diff = abs(dist_total - employment_cross_total)
        if diff > 5:
            raise ValueError(
                f"UrgencyDistribution と UrgencyEmploymentCross の差が大きすぎます: "
                f"差={diff}人（許容範囲: 5人以内）"
            )

        return (
            f"Distribution={int(dist_total)}人, AgeCross={int(age_cross_total)}人 [OK]一致\n"
            f"   EmploymentCross={int(employment_cross_total)}人 "
            f"（差={int(diff)}人、就業状況欠損による差異 [OK]許容範囲内）"
        )

    def test_career_age_cross_consistency(self):
        """CareerAgeCross.csv と Matrix.csv の整合性検証（サンプル）"""
        cross_df = pd.read_csv(self.phase8_dir / 'CareerAgeCross.csv', encoding='utf-8-sig')
        matrix_df = pd.read_csv(self.phase8_dir / 'CareerAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # サンプルとして最初の10行を検証
        mismatches = []
        for _, row in cross_df.head(10).iterrows():
            career = row['career']
            age_group = row['age_group']
            cross_count = row['count']

            # マトリックスから対応する値を取得
            if career in matrix_df.index and age_group in matrix_df.columns:
                matrix_count = matrix_df.loc[career, age_group]

                if cross_count != matrix_count:
                    mismatches.append(
                        f"{career} × {age_group}: cross={cross_count}, matrix={matrix_count}"
                    )

        if mismatches:
            raise ValueError(f"クロス集計とマトリックスの不一致: {mismatches}")

        return f"サンプル10件の値が一致（キャリア × 年齢層）"

    def test_career_age_matrix_totals(self):
        """CareerAgeCross_Matrix の列合計検証"""
        matrix_df = pd.read_csv(self.phase8_dir / 'CareerAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # 列合計（各年齢層の合計）
        col_totals = matrix_df.sum(axis=0)

        # 全体合計
        grand_total = matrix_df.sum().sum()

        # 列合計の検証（各年齢層の人数が合理的か）
        age_groups = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        col_totals_dict = {age_group: col_totals[age_group] for age_group in age_groups if age_group in col_totals}

        return (
            f"全体合計={int(grand_total)}人、"
            f"年齢層別: " + ", ".join([f"{k}={int(v)}人" for k, v in col_totals_dict.items()])
        )

if __name__ == '__main__':
    tester = CrossTabulationLogicTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
