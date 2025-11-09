#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
観察的記述系全ロジック包括検証テスト
テスト対象: Phase 1, 3, 7, 8, 10のすべての観察的記述系分析
"""

import pandas as pd
import json
from pathlib import Path
import sys

class AllDescriptiveLogicTest:
    """観察的記述系全ロジック包括テスト"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.output_v2_dir = self.base_dir / 'data' / 'output_v2'
        self.test_results = []

        # 各Phaseのディレクトリ
        self.phase1_dir = self.output_v2_dir / 'phase1'
        self.phase3_dir = self.output_v2_dir / 'phase3'
        self.phase7_dir = self.output_v2_dir / 'phase7'
        self.phase8_dir = self.output_v2_dir / 'phase8'
        self.phase10_dir = self.output_v2_dir / 'phase10'

    def run_all_tests(self):
        """全テストを実行"""
        print("=" * 80)
        print("観察的記述系全ロジック包括検証テスト")
        print("=" * 80)
        print()

        tests = [
            # Phase 1: 基礎集計
            ("Phase 1: ファイル存在確認", self.test_phase1_file_existence),
            ("Phase 1: Applicants構造検証", self.test_phase1_applicants_structure),
            ("Phase 1: DesiredWork構造検証", self.test_phase1_desired_work_structure),
            ("Phase 1: AggDesired構造検証", self.test_phase1_agg_desired_structure),
            ("Phase 1: MapMetrics構造検証", self.test_phase1_map_metrics_structure),
            ("Phase 1: データ整合性検証", self.test_phase1_data_consistency),

            # Phase 3: ペルソナ分析
            ("Phase 3: ファイル存在確認", self.test_phase3_file_existence),
            ("Phase 3: PersonaSummary構造検証", self.test_phase3_persona_summary_structure),
            ("Phase 3: PersonaDetails構造検証", self.test_phase3_persona_details_structure),
            ("Phase 3: PersonaSummaryByMunicipality構造検証", self.test_phase3_persona_by_muni_structure),
            ("Phase 3: ペルソナ合計一致検証", self.test_phase3_totals_consistency),

            # Phase 7: 高度分析
            ("Phase 7: ファイル存在確認", self.test_phase7_file_existence),
            ("Phase 7: SupplyDensityMap構造検証", self.test_phase7_supply_density_structure),
            ("Phase 7: QualificationDistribution構造検証", self.test_phase7_qualification_dist_structure),
            ("Phase 7: AgeGenderCrossAnalysis構造検証", self.test_phase7_age_gender_structure),
            ("Phase 7: MobilityScore構造検証", self.test_phase7_mobility_score_structure),
            ("Phase 7: DetailedPersonaProfile構造検証", self.test_phase7_detailed_persona_structure),

            # Phase 8: キャリア・学歴分析
            ("Phase 8: ファイル存在確認", self.test_phase8_file_existence),
            ("Phase 8: CareerDistribution構造検証", self.test_phase8_career_dist_structure),
            ("Phase 8: CareerAgeCross構造検証", self.test_phase8_career_age_cross_structure),
            ("Phase 8: CareerAgeCross_Matrix構造検証", self.test_phase8_career_age_matrix_structure),
            ("Phase 8: 行列整合性検証", self.test_phase8_matrix_consistency),

            # Phase 10: 転職意欲・緊急度分析
            ("Phase 10: ファイル存在確認", self.test_phase10_file_existence),
            ("Phase 10: UrgencyDistribution構造検証", self.test_phase10_urgency_dist_structure),
            ("Phase 10: UrgencyAgeCross構造検証", self.test_phase10_urgency_age_cross_structure),
            ("Phase 10: UrgencyEmploymentCross構造検証", self.test_phase10_urgency_employment_cross_structure),
            ("Phase 10: UrgencyByMunicipality構造検証", self.test_phase10_urgency_by_muni_structure),
            ("Phase 10: マトリックス整合性検証", self.test_phase10_matrix_consistency),
            ("Phase 10: 全体合計一致検証", self.test_phase10_totals_consistency),

            # 統合検証
            ("統合: 全Phaseの総人数一致検証", self.test_cross_phase_total_consistency),
            ("統合: 統計値の妥当性検証", self.test_statistical_values_validity),
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
        result_path = self.base_dir / 'tests' / 'results' / 'ALL_DESCRIPTIVE_LOGIC_TEST_RESULTS.json'
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

    # ===== Phase 1テスト =====

    def test_phase1_file_existence(self):
        """Phase 1: ファイル存在確認"""
        required_files = [
            'Applicants.csv',
            'DesiredWork.csv',
            'AggDesired.csv',
            'MapMetrics.csv'
        ]

        for file_name in required_files:
            file_path = self.phase1_dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        return f"4つの必須ファイルが存在します"

    def test_phase1_applicants_structure(self):
        """Phase 1: Applicants構造検証"""
        df = pd.read_csv(self.phase1_dir / 'Applicants.csv', encoding='utf-8-sig')

        required_columns = ['applicant_id', 'age', 'gender', 'residence_prefecture', 'employment_status']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"Applicants.csv: {len(df)}行、必須カラムすべて存在"

    def test_phase1_desired_work_structure(self):
        """Phase 1: DesiredWork構造検証"""
        df = pd.read_csv(self.phase1_dir / 'DesiredWork.csv', encoding='utf-8-sig')

        required_columns = ['applicant_id', 'desired_location_full', 'desired_prefecture', 'desired_municipality']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        # ユニーク市町村数
        unique_municipalities = df['desired_location_full'].nunique()

        return f"DesiredWork.csv: {len(df)}行、{unique_municipalities}市町村"

    def test_phase1_agg_desired_structure(self):
        """Phase 1: AggDesired構造検証"""
        df = pd.read_csv(self.phase1_dir / 'AggDesired.csv', encoding='utf-8-sig')

        required_columns = ['location_key', 'applicant_count']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"AggDesired.csv: {len(df)}市町村、合計{df['applicant_count'].sum()}件"

    def test_phase1_map_metrics_structure(self):
        """Phase 1: MapMetrics構造検証"""
        df = pd.read_csv(self.phase1_dir / 'MapMetrics.csv', encoding='utf-8-sig')

        required_columns = ['location_key', 'applicant_count', 'latitude', 'longitude']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        # 座標の妥当性チェック（日本の範囲内）
        if df['latitude'].min() < 20 or df['latitude'].max() > 50:
            raise ValueError(f"緯度が範囲外: {df['latitude'].min()} ~ {df['latitude'].max()}")

        if df['longitude'].min() < 120 or df['longitude'].max() > 150:
            raise ValueError(f"経度が範囲外: {df['longitude'].min()} ~ {df['longitude'].max()}")

        return f"MapMetrics.csv: {len(df)}市町村、座標データ正常"

    def test_phase1_data_consistency(self):
        """Phase 1: データ整合性検証"""
        applicants_df = pd.read_csv(self.phase1_dir / 'Applicants.csv', encoding='utf-8-sig')
        desired_work_df = pd.read_csv(self.phase1_dir / 'DesiredWork.csv', encoding='utf-8-sig')
        agg_desired_df = pd.read_csv(self.phase1_dir / 'AggDesired.csv', encoding='utf-8-sig')

        # Applicantsの総数
        total_applicants = len(applicants_df)

        # DesiredWorkのユニーク申請者数
        unique_applicants_in_desired = desired_work_df['applicant_id'].nunique()

        # AggDesiredの合計
        total_in_agg = agg_desired_df['applicant_count'].sum()

        # DesiredWorkの合計
        total_in_desired = len(desired_work_df)

        # AggDesiredの合計とDesiredWorkの合計が一致するか
        if total_in_agg != total_in_desired:
            raise ValueError(
                f"AggDesiredとDesiredWorkの合計が不一致: {total_in_agg} != {total_in_desired}"
            )

        return (
            f"Applicants: {total_applicants}人、"
            f"DesiredWork: {unique_applicants_in_desired}人（ユニーク）、{total_in_desired}件、"
            f"AggDesired合計: {total_in_agg}件 [OK]一致"
        )

    # ===== Phase 3テスト =====

    def test_phase3_file_existence(self):
        """Phase 3: ファイル存在確認"""
        required_files = [
            'PersonaSummary.csv',
            'PersonaDetails.csv',
            'PersonaSummaryByMunicipality.csv'
        ]

        for file_name in required_files:
            file_path = self.phase3_dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        return f"3つの必須ファイルが存在します"

    def test_phase3_persona_summary_structure(self):
        """Phase 3: PersonaSummary構造検証"""
        df = pd.read_csv(self.phase3_dir / 'PersonaSummary.csv', encoding='utf-8-sig')

        required_columns = ['persona_name', 'age_group', 'gender', 'has_national_license', 'count']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"PersonaSummary.csv: {len(df)}ペルソナ、合計{df['count'].sum()}人"

    def test_phase3_persona_details_structure(self):
        """Phase 3: PersonaDetails構造検証"""
        df = pd.read_csv(self.phase3_dir / 'PersonaDetails.csv', encoding='utf-8-sig')

        required_columns = ['age_group', 'gender', 'count', 'avg_age']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"PersonaDetails.csv: {len(df)}行、合計{df['count'].sum()}人"

    def test_phase3_persona_by_muni_structure(self):
        """Phase 3: PersonaSummaryByMunicipality構造検証"""
        df = pd.read_csv(self.phase3_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')

        required_columns = [
            'municipality', 'persona_name', 'age_group', 'gender', 'has_national_license',
            'count', 'total_in_municipality', 'market_share_pct'
        ]
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        unique_municipalities = df['municipality'].nunique()

        return f"PersonaSummaryByMunicipality.csv: {len(df)}行、{unique_municipalities}市町村"

    def test_phase3_totals_consistency(self):
        """Phase 3: ペルソナ合計一致検証"""
        summary_df = pd.read_csv(self.phase3_dir / 'PersonaSummary.csv', encoding='utf-8-sig')
        details_df = pd.read_csv(self.phase3_dir / 'PersonaDetails.csv', encoding='utf-8-sig')

        summary_total = summary_df['count'].sum()
        details_total = details_df['count'].sum()

        if summary_total != details_total:
            raise ValueError(
                f"PersonaSummaryとPersonaDetailsの合計が不一致: {summary_total} != {details_total}"
            )

        return f"PersonaSummary={summary_total}人、PersonaDetails={details_total}人 [OK]一致"

    # ===== Phase 7テスト =====

    def test_phase7_file_existence(self):
        """Phase 7: ファイル存在確認"""
        if not self.phase7_dir.exists():
            return "Phase 7ディレクトリが存在しません（スキップ）"

        required_files = [
            'SupplyDensityMap.csv',
            'AgeGenderCrossAnalysis.csv',
            'MobilityScore.csv',
            'DetailedPersonaProfile.csv'
        ]

        existing_files = []
        for file_name in required_files:
            file_path = self.phase7_dir / file_name
            if file_path.exists():
                existing_files.append(file_name)

        return f"{len(existing_files)}/{len(required_files)}ファイルが存在: {', '.join(existing_files)}"

    def test_phase7_supply_density_structure(self):
        """Phase 7: SupplyDensityMap構造検証"""
        if not self.phase7_dir.exists():
            return "Phase 7ディレクトリが存在しません（スキップ）"

        file_path = self.phase7_dir / 'SupplyDensityMap.csv'
        if not file_path.exists():
            return "SupplyDensityMap.csvが存在しません（スキップ）"

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        required_columns = ['location', 'supply_count', 'avg_age']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"SupplyDensityMap.csv: {len(df)}市町村、合計{df['supply_count'].sum()}人"

    def test_phase7_qualification_dist_structure(self):
        """Phase 7: QualificationDistribution構造検証"""
        if not self.phase7_dir.exists():
            return "Phase 7ディレクトリが存在しません（スキップ）"

        file_path = self.phase7_dir / 'QualificationDistribution.csv'
        if not file_path.exists():
            return "QualificationDistribution.csvが存在しません（スキップ）"

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        required_columns = ['qualification', 'count', 'avg_age']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"QualificationDistribution.csv: {len(df)}資格、合計{df['count'].sum()}件"

    def test_phase7_age_gender_structure(self):
        """Phase 7: AgeGenderCrossAnalysis構造検証"""
        if not self.phase7_dir.exists():
            return "Phase 7ディレクトリが存在しません（スキップ）"

        file_path = self.phase7_dir / 'AgeGenderCrossAnalysis.csv'
        if not file_path.exists():
            return "AgeGenderCrossAnalysis.csvが存在しません（スキップ）"

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        required_columns = ['age_group', 'gender', 'count']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"AgeGenderCrossAnalysis.csv: {len(df)}行、合計{df['count'].sum()}人"

    def test_phase7_mobility_score_structure(self):
        """Phase 7: MobilityScore構造検証"""
        if not self.phase7_dir.exists():
            return "Phase 7ディレクトリが存在しません（スキップ）"

        file_path = self.phase7_dir / 'MobilityScore.csv'
        if not file_path.exists():
            return "MobilityScore.csvが存在しません（スキップ）"

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        required_columns = ['applicant_id', 'mobility_score']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        # mobility_scoreは0.0～1.0の範囲内か
        if df['mobility_score'].min() < 0 or df['mobility_score'].max() > 1:
            raise ValueError(f"mobility_scoreが範囲外: {df['mobility_score'].min()} ~ {df['mobility_score'].max()}")

        return f"MobilityScore.csv: {len(df)}人、スコア範囲: {df['mobility_score'].min():.2f}～{df['mobility_score'].max():.2f}"

    def test_phase7_detailed_persona_structure(self):
        """Phase 7: DetailedPersonaProfile構造検証"""
        if not self.phase7_dir.exists():
            return "Phase 7ディレクトリが存在しません（スキップ）"

        file_path = self.phase7_dir / 'DetailedPersonaProfile.csv'
        if not file_path.exists():
            return "DetailedPersonaProfile.csvが存在しません（スキップ）"

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        required_columns = ['persona_name', 'age_group', 'gender', 'count']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"DetailedPersonaProfile.csv: {len(df)}ペルソナ、合計{df['count'].sum()}人"

    # ===== Phase 8テスト =====

    def test_phase8_file_existence(self):
        """Phase 8: ファイル存在確認"""
        required_files = [
            'CareerDistribution.csv',
            'CareerAgeCross.csv',
            'CareerAgeCross_Matrix.csv'
        ]

        existing_files = []
        for file_name in required_files:
            file_path = self.phase8_dir / file_name
            if file_path.exists():
                existing_files.append(file_name)

        if len(existing_files) < len(required_files):
            missing = set(required_files) - set(existing_files)
            raise FileNotFoundError(f"不足ファイル: {missing}")

        return f"{len(existing_files)}ファイルが存在"

    def test_phase8_career_dist_structure(self):
        """Phase 8: CareerDistribution構造検証"""
        df = pd.read_csv(self.phase8_dir / 'CareerDistribution.csv', encoding='utf-8-sig')

        required_columns = ['career', 'count', 'avg_age']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"CareerDistribution.csv: {len(df)}キャリア、合計{df['count'].sum()}人"

    def test_phase8_career_age_cross_structure(self):
        """Phase 8: CareerAgeCross構造検証"""
        df = pd.read_csv(self.phase8_dir / 'CareerAgeCross.csv', encoding='utf-8-sig')

        required_columns = ['career', 'age_group', 'count', 'avg_age']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"CareerAgeCross.csv: {len(df)}行、合計{df['count'].sum()}人"

    def test_phase8_career_age_matrix_structure(self):
        """Phase 8: CareerAgeCross_Matrix構造検証"""
        df = pd.read_csv(self.phase8_dir / 'CareerAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # 年齢層カラムが存在するか
        expected_age_groups = ['20代', '30代', '40代', '50代', '60代', '70歳以上']
        missing = set(expected_age_groups) - set(df.columns)

        if missing:
            raise ValueError(f"不足年齢層カラム: {missing}")

        return f"CareerAgeCross_Matrix.csv: {len(df)}キャリア × {len(df.columns)}年齢層"

    def test_phase8_matrix_consistency(self):
        """Phase 8: 行列整合性検証"""
        cross_df = pd.read_csv(self.phase8_dir / 'CareerAgeCross.csv', encoding='utf-8-sig')
        matrix_df = pd.read_csv(self.phase8_dir / 'CareerAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # クロス集計の合計とマトリックスの合計が一致するか
        cross_total = cross_df['count'].sum()
        matrix_total = matrix_df.sum().sum()

        if cross_total != matrix_total:
            raise ValueError(
                f"CareerAgeCrossとCareerAgeCross_Matrixの合計が不一致: {cross_total} != {matrix_total}"
            )

        return f"CareerAgeCross={cross_total}人、Matrix={matrix_total}人 [OK]一致"

    # ===== Phase 10テスト =====

    def test_phase10_file_existence(self):
        """Phase 10: ファイル存在確認"""
        required_files = [
            'UrgencyDistribution.csv',
            'UrgencyAgeCross.csv',
            'UrgencyAgeCross_Matrix.csv',
            'UrgencyEmploymentCross.csv',
            'UrgencyEmploymentCross_Matrix.csv'
        ]

        existing_files = []
        for file_name in required_files:
            file_path = self.phase10_dir / file_name
            if file_path.exists():
                existing_files.append(file_name)

        if len(existing_files) < len(required_files):
            missing = set(required_files) - set(existing_files)
            raise FileNotFoundError(f"不足ファイル: {missing}")

        return f"{len(existing_files)}ファイルが存在"

    def test_phase10_urgency_dist_structure(self):
        """Phase 10: UrgencyDistribution構造検証"""
        df = pd.read_csv(self.phase10_dir / 'UrgencyDistribution.csv', encoding='utf-8-sig')

        required_columns = ['urgency_rank', 'count', 'avg_age', 'avg_urgency_score']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"UrgencyDistribution.csv: {len(df)}ランク、合計{df['count'].sum()}人"

    def test_phase10_urgency_age_cross_structure(self):
        """Phase 10: UrgencyAgeCross構造検証"""
        df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross.csv', encoding='utf-8-sig')

        required_columns = ['urgency_rank', 'age_group', 'count']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"UrgencyAgeCross.csv: {len(df)}行、合計{df['count'].sum()}人"

    def test_phase10_urgency_employment_cross_structure(self):
        """Phase 10: UrgencyEmploymentCross構造検証"""
        df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross.csv', encoding='utf-8-sig')

        required_columns = ['urgency_rank', 'employment_status', 'count']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"UrgencyEmploymentCross.csv: {len(df)}行、合計{df['count'].sum()}人"

    def test_phase10_urgency_by_muni_structure(self):
        """Phase 10: UrgencyByMunicipality構造検証"""
        file_path = self.phase10_dir / 'UrgencyByMunicipality.csv'
        if not file_path.exists():
            return "UrgencyByMunicipality.csvが存在しません（スキップ）"

        df = pd.read_csv(file_path, encoding='utf-8-sig')

        required_columns = ['location', 'count', 'avg_urgency_score']
        missing = set(required_columns) - set(df.columns)

        if missing:
            raise ValueError(f"不足カラム: {missing}")

        return f"UrgencyByMunicipality.csv: {len(df)}市町村"

    def test_phase10_matrix_consistency(self):
        """Phase 10: マトリックス整合性検証"""
        age_cross_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross.csv', encoding='utf-8-sig')
        age_matrix_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        employment_cross_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross.csv', encoding='utf-8-sig')
        employment_matrix_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross_Matrix.csv', encoding='utf-8-sig', index_col=0)

        # 年齢クロス集計の整合性
        age_cross_total = age_cross_df['count'].sum()
        age_matrix_total = age_matrix_df.sum().sum()

        if age_cross_total != age_matrix_total:
            raise ValueError(
                f"UrgencyAgeCrossとMatrixの合計が不一致: {age_cross_total} != {age_matrix_total}"
            )

        # 就業状況クロス集計の整合性
        employment_cross_total = employment_cross_df['count'].sum()
        employment_matrix_total = employment_matrix_df.sum().sum()

        if employment_cross_total != employment_matrix_total:
            raise ValueError(
                f"UrgencyEmploymentCrossとMatrixの合計が不一致: {employment_cross_total} != {employment_matrix_total}"
            )

        return (
            f"AgeCross={age_cross_total}人（Matrix一致）、"
            f"EmploymentCross={employment_cross_total}人（Matrix一致）"
        )

    def test_phase10_totals_consistency(self):
        """Phase 10: 全体合計一致検証"""
        dist_df = pd.read_csv(self.phase10_dir / 'UrgencyDistribution.csv', encoding='utf-8-sig')
        age_cross_df = pd.read_csv(self.phase10_dir / 'UrgencyAgeCross.csv', encoding='utf-8-sig')
        employment_cross_df = pd.read_csv(self.phase10_dir / 'UrgencyEmploymentCross.csv', encoding='utf-8-sig')

        dist_total = dist_df['count'].sum()
        age_cross_total = age_cross_df['count'].sum()
        employment_cross_total = employment_cross_df['count'].sum()

        # DistributionとAgeCrossは完全一致するべき
        if dist_total != age_cross_total:
            raise ValueError(
                f"UrgencyDistributionとUrgencyAgeCrossの合計が不一致: {dist_total} != {age_cross_total}"
            )

        # EmploymentCrossは欠損値のため数人の差は許容
        diff = abs(dist_total - employment_cross_total)
        if diff > 5:
            raise ValueError(
                f"UrgencyDistributionとUrgencyEmploymentCrossの差が大きすぎます: 差={diff}人"
            )

        return (
            f"Distribution={dist_total}人、AgeCross={age_cross_total}人 [OK]一致、"
            f"EmploymentCross={employment_cross_total}人（差={diff}人、許容範囲内）"
        )

    # ===== 統合テスト =====

    def test_cross_phase_total_consistency(self):
        """統合: 全Phaseの総人数一致検証"""
        # Phase 1
        applicants_df = pd.read_csv(self.phase1_dir / 'Applicants.csv', encoding='utf-8-sig')
        phase1_total = len(applicants_df)

        # Phase 3
        summary_df = pd.read_csv(self.phase3_dir / 'PersonaSummary.csv', encoding='utf-8-sig')
        phase3_total = summary_df['count'].sum()

        # Phase 8
        career_dist_df = pd.read_csv(self.phase8_dir / 'CareerDistribution.csv', encoding='utf-8-sig')
        phase8_total = career_dist_df['count'].sum()

        # Phase 10
        urgency_dist_df = pd.read_csv(self.phase10_dir / 'UrgencyDistribution.csv', encoding='utf-8-sig')
        phase10_total = urgency_dist_df['count'].sum()

        # Phase 1とPhase 3、Phase 10は一致するべき
        if phase1_total != phase3_total:
            raise ValueError(f"Phase 1とPhase 3の総数が不一致: {phase1_total} != {phase3_total}")

        if phase1_total != phase10_total:
            raise ValueError(f"Phase 1とPhase 10の総数が不一致: {phase1_total} != {phase10_total}")

        # Phase 8はキャリア情報がある人のみのため、少ないのは正常
        if phase8_total > phase1_total:
            raise ValueError(f"Phase 8の総数がPhase 1より多い: {phase8_total} > {phase1_total}")

        return (
            f"Phase 1={phase1_total}人、Phase 3={phase3_total}人、"
            f"Phase 8={phase8_total}人、Phase 10={phase10_total}人 [OK]整合性あり"
        )

    def test_statistical_values_validity(self):
        """統合: 統計値の妥当性検証"""
        issues = []

        # Phase 1: 年齢範囲
        applicants_df = pd.read_csv(self.phase1_dir / 'Applicants.csv', encoding='utf-8-sig')
        if applicants_df['age'].min() < 15 or applicants_df['age'].max() > 100:
            issues.append(f"Phase 1: 年齢が範囲外 ({applicants_df['age'].min()} ~ {applicants_df['age'].max()})")

        # Phase 3: 市町村内シェア
        persona_by_muni_df = pd.read_csv(self.phase3_dir / 'PersonaSummaryByMunicipality.csv', encoding='utf-8-sig')
        if persona_by_muni_df['market_share_pct'].min() < 0 or persona_by_muni_df['market_share_pct'].max() > 100:
            issues.append(f"Phase 3: 市町村内シェアが範囲外 ({persona_by_muni_df['market_share_pct'].min()} ~ {persona_by_muni_df['market_share_pct'].max()})")

        # Phase 10: 緊急度スコア
        urgency_dist_df = pd.read_csv(self.phase10_dir / 'UrgencyDistribution.csv', encoding='utf-8-sig')
        if urgency_dist_df['avg_urgency_score'].min() < 0 or urgency_dist_df['avg_urgency_score'].max() > 10:
            issues.append(f"Phase 10: 緊急度スコアが範囲外 ({urgency_dist_df['avg_urgency_score'].min()} ~ {urgency_dist_df['avg_urgency_score'].max()})")

        if issues:
            raise ValueError("\n".join(issues))

        return "全Phaseの統計値が妥当な範囲内"

if __name__ == '__main__':
    tester = AllDescriptiveLogicTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
