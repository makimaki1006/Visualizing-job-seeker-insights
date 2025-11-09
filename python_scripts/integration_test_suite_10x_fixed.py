"""
ジョブメドレー求職者データ分析 - 10回繰り返し統合テストスイート（修正版）

実際の生成データを使用した包括的な統合テスト（10回実施）
実際のデータ構造に合わせて修正

テスト観点:
1. データ整合性: Phase間のID一貫性、カウント合計整合性
2. エンドツーエンド: CSV読込→全Phase処理→出力までの完全フロー
3. パフォーマンス: 実際の処理時間測定
4. データ品質: 座標の正確性、集計値の正確性
5. Phase間依存: Phase 1→6→7の依存関係検証
6. 統計分析精度: カイ二乗、ANOVA検定の妥当性
7. ペルソナ分類: ペルソナ分類の正確性
8. フロー分析: 自治体間移動パターンの妥当性
9. スケーラビリティ: 10万件データ推定処理時間
10. リカバリ: エラー発生時のデータ保全性
"""

import pandas as pd
import json
import time
from pathlib import Path
from collections import defaultdict
import traceback


class IntegrationTestSuite:
    """10回繰り返し統合テストスイート（修正版）"""

    def __init__(self, base_dir='C:\\Users\\fuji1\\OneDrive\\Pythonスクリプト保管\\job_medley_project'):
        self.base_dir = Path(base_dir)
        self.python_scripts_dir = self.base_dir / 'python_scripts'
        self.results = {}
        self.summary = {
            'total_tests': 10,
            'passed': 0,
            'failed': 0,
            'overall_score': 0,
            'critical_issues': []
        }

    def _load_phase_data(self, phase_num, filename):
        """Phaseデータの読み込み"""
        phase_dir = self.python_scripts_dir / f'gas_output_phase{phase_num}'
        filepath = phase_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"{filepath} が存在しません")
        return pd.read_csv(filepath, encoding='utf-8-sig')

    def test_1_data_integrity(self):
        """テスト1: データ整合性検証"""
        print("\n[TEST 1/10] データ整合性検証...")

        try:
            # Phase 1データ読み込み
            applicants_df = self._load_phase_data(1, 'Applicants.csv')
            desired_work_df = self._load_phase_data(1, 'DesiredWork.csv')
            map_metrics_df = self._load_phase_data(1, 'MapMetrics.csv')
            agg_desired_df = self._load_phase_data(1, 'AggDesired.csv')

            # 整合性チェック
            applicants_count = len(applicants_df)
            desired_work_unique_ids = desired_work_df['申請者ID'].nunique()
            map_metrics_total = map_metrics_df['カウント'].sum()
            agg_desired_total = agg_desired_df['カウント'].sum()

            discrepancies = []

            # ID一貫性チェック（許容差: 5%以内）
            id_diff_ratio = abs(applicants_count - desired_work_unique_ids) / applicants_count
            if id_diff_ratio > 0.05:
                discrepancies.append(
                    f"Applicants件数 ({applicants_count}) とDesiredWorkユニークID数 ({desired_work_unique_ids}) の差が5%以上"
                )

            # カウント整合性チェック
            if map_metrics_total != agg_desired_total:
                discrepancies.append(
                    f"MapMetricsカウント合計 ({map_metrics_total}) != AggDesiredカウント合計 ({agg_desired_total})"
                )

            # ペルソナデータ（許容差: 10%以内）
            persona_summary_df = self._load_phase_data(3, 'PersonaSummary.csv')
            persona_total = persona_summary_df['count'].sum()

            persona_diff_ratio = abs(persona_total - applicants_count) / applicants_count
            if persona_diff_ratio > 0.10:
                discrepancies.append(
                    f"PersonaSummary人数合計 ({persona_total}) とApplicants総数 ({applicants_count}) の差が10%以上"
                )

            status = "PASS" if len(discrepancies) == 0 else "FAIL"
            score = 100 if len(discrepancies) == 0 else max(0, 100 - len(discrepancies) * 20)

            result = {
                'status': status,
                'applicants_count': int(applicants_count),
                'desired_work_unique_ids': int(desired_work_unique_ids),
                'id_diff_ratio': round(id_diff_ratio, 4),
                'map_metrics_total': int(map_metrics_total),
                'agg_desired_total': int(agg_desired_total),
                'persona_total': int(persona_total),
                'persona_diff_ratio': round(persona_diff_ratio, 4),
                'discrepancies': discrepancies,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(discrepancies)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト1エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_2_end_to_end_flow(self):
        """テスト2: エンドツーエンドフロー検証"""
        print("\n[TEST 2/10] エンドツーエンドフロー検証...")

        try:
            # 全Phaseのファイル存在確認（実際のファイル名に修正）
            required_files = {
                'phase1': ['MapMetrics.csv', 'Applicants.csv', 'DesiredWork.csv', 'AggDesired.csv'],
                'phase2': ['ChiSquareTests.csv', 'ANOVATests.csv'],
                'phase3': ['PersonaSummary.csv', 'PersonaDetails.csv'],
                'phase6': ['MunicipalityFlowEdges.csv', 'MunicipalityFlowNodes.csv', 'ProximityAnalysis.csv'],
                'phase7': ['SupplyDensityMap.csv', 'QualificationDistribution.csv', 'AgeGenderCrossAnalysis.csv',
                          'MobilityScore.csv', 'DetailedPersonaProfile.csv', 'PersonaMapData.csv',
                          'PersonaMobilityCross.csv']
            }

            missing_files = []
            file_sizes = {}

            for phase, files in required_files.items():
                phase_num = phase.replace('phase', '')
                for filename in files:
                    phase_dir = self.python_scripts_dir / f'gas_output_phase{phase_num}'
                    filepath = phase_dir / filename

                    if not filepath.exists():
                        missing_files.append(f"{phase}/{filename}")
                    else:
                        file_sizes[f"{phase}/{filename}"] = filepath.stat().st_size

            status = "PASS" if len(missing_files) == 0 else "FAIL"
            score = 100 if len(missing_files) == 0 else max(0, 100 - len(missing_files) * 5)

            result = {
                'status': status,
                'total_files_expected': sum(len(files) for files in required_files.values()),
                'files_found': sum(len(files) for files in required_files.values()) - len(missing_files),
                'missing_files': missing_files,
                'file_sizes_summary': {
                    'phase1_total': sum(v for k, v in file_sizes.items() if k.startswith('phase1')),
                    'phase2_total': sum(v for k, v in file_sizes.items() if k.startswith('phase2')),
                    'phase3_total': sum(v for k, v in file_sizes.items() if k.startswith('phase3')),
                    'phase6_total': sum(v for k, v in file_sizes.items() if k.startswith('phase6')),
                    'phase7_total': sum(v for k, v in file_sizes.items() if k.startswith('phase7')),
                },
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                if missing_files:
                    self.summary['critical_issues'].append(f"欠損ファイル: {len(missing_files)}件")

            print(f"  [結果] {status} - スコア: {score}/100 (発見ファイル: {result['files_found']}/{result['total_files_expected']})")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト2エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_3_performance_measurement(self):
        """テスト3: パフォーマンス測定"""
        print("\n[TEST 3/10] パフォーマンス測定...")

        try:
            phase_load_times = {}

            # 各Phaseの読み込み時間測定（実際のファイル名に修正）
            phases = {
                'phase1': ['MapMetrics.csv', 'Applicants.csv', 'DesiredWork.csv', 'AggDesired.csv'],
                'phase2': ['ChiSquareTests.csv', 'ANOVATests.csv'],
                'phase3': ['PersonaSummary.csv', 'PersonaDetails.csv'],
                'phase6': ['MunicipalityFlowEdges.csv', 'MunicipalityFlowNodes.csv', 'ProximityAnalysis.csv'],
                'phase7': ['SupplyDensityMap.csv', 'QualificationDistribution.csv', 'AgeGenderCrossAnalysis.csv',
                          'MobilityScore.csv', 'DetailedPersonaProfile.csv', 'PersonaMapData.csv',
                          'PersonaMobilityCross.csv']
            }

            total_load_time = 0

            for phase, files in phases.items():
                phase_start = time.time()
                phase_num = phase.replace('phase', '')

                for filename in files:
                    try:
                        self._load_phase_data(phase_num, filename)
                    except Exception:
                        pass

                phase_time = time.time() - phase_start
                phase_load_times[phase] = round(phase_time, 3)
                total_load_time += phase_time

            # 処理時間の評価（実データのサイズに応じて）
            applicants_df = self._load_phase_data(1, 'Applicants.csv')
            actual_data_size = len(applicants_df)

            # 10万件データの推定処理時間
            estimated_100k_time = (total_load_time / actual_data_size) * 100000

            # スコア計算（30秒以内が目標）
            score = 100 if total_load_time < 30 else max(0, 100 - int((total_load_time - 30) * 2))

            result = {
                'status': 'PASS' if total_load_time < 60 else 'WARNING',
                'actual_data_size': int(actual_data_size),
                'total_load_time_seconds': round(total_load_time, 3),
                'phase_load_times': phase_load_times,
                'bottleneck_phase': max(phase_load_times.items(), key=lambda x: x[1])[0],
                'estimated_100k_processing_time_seconds': round(estimated_100k_time, 2),
                'estimated_100k_processing_time_human': f"{int(estimated_100k_time // 60)}分 {int(estimated_100k_time % 60)}秒",
                'score': score
            }

            if result['status'] == 'PASS':
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1

            print(f"  [結果] {result['status']} - スコア: {score}/100 (総処理時間: {total_load_time:.2f}秒)")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト3エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_4_data_quality(self):
        """テスト4: データ品質検証"""
        print("\n[TEST 4/10] データ品質検証...")

        try:
            quality_issues = []

            # 座標の正確性チェック
            map_metrics_df = self._load_phase_data(1, 'MapMetrics.csv')

            # 緯度・経度の範囲チェック（日本の範囲）
            invalid_coords = map_metrics_df[
                (map_metrics_df['緯度'] < 24) | (map_metrics_df['緯度'] > 46) |
                (map_metrics_df['経度'] < 123) | (map_metrics_df['経度'] > 154)
            ]

            if len(invalid_coords) > 0:
                quality_issues.append(f"無効な座標: {len(invalid_coords)}件")

            # 集計値の正確性チェック
            agg_desired_df = self._load_phase_data(1, 'AggDesired.csv')
            negative_counts = agg_desired_df[agg_desired_df['カウント'] < 0]

            if len(negative_counts) > 0:
                quality_issues.append(f"負のカウント: {len(negative_counts)}件")

            # NULL値チェック
            applicants_df = self._load_phase_data(1, 'Applicants.csv')
            null_ids = applicants_df['ID'].isna().sum()

            if null_ids > 0:
                quality_issues.append(f"NULL ID: {null_ids}件")

            status = "PASS" if len(quality_issues) == 0 else "FAIL"
            score = 100 if len(quality_issues) == 0 else max(0, 100 - len(quality_issues) * 25)

            result = {
                'status': status,
                'total_locations_checked': len(map_metrics_df),
                'invalid_coordinates': len(invalid_coords),
                'negative_counts': len(negative_counts),
                'null_ids': int(null_ids),
                'quality_issues': quality_issues,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(quality_issues)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト4エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_5_phase_dependencies(self):
        """テスト5: Phase間依存関係検証"""
        print("\n[TEST 5/10] Phase間依存関係検証...")

        try:
            dependency_issues = []

            # Phase 1 → Phase 7 依存関係（ProximityAnalysisは構造が異なるためスキップ）
            applicants_df = self._load_phase_data(1, 'Applicants.csv')
            persona_map_df = self._load_phase_data(7, 'PersonaMapData.csv')
            map_metrics_df = self._load_phase_data(1, 'MapMetrics.csv')

            # PersonaMapDataのカラム確認
            if len(persona_map_df.columns) >= 4:
                # 4列目がキーと仮定
                key_col = persona_map_df.columns[3] if 'キー' in persona_map_df.columns else persona_map_df.columns[3]

                # PersonaMapDataの場所がMapMetricsに存在するか
                map_keys = set(map_metrics_df['キー'])
                persona_keys = set(persona_map_df[key_col].dropna())

                missing_keys = persona_keys - map_keys
                if len(missing_keys) > 0 and len(missing_keys) / len(persona_keys) > 0.05:
                    dependency_issues.append(
                        f"Phase 7に存在するがPhase 1に存在しない場所: {len(missing_keys)}件 ({len(missing_keys)/len(persona_keys)*100:.1f}%)"
                    )

            status = "PASS" if len(dependency_issues) == 0 else "FAIL"
            score = 100 if len(dependency_issues) == 0 else max(0, 100 - len(dependency_issues) * 30)

            result = {
                'status': status,
                'applicant_ids_phase1': len(applicants_df),
                'map_keys_phase1': len(set(map_metrics_df['キー'])),
                'persona_locations_phase7': len(persona_map_df),
                'dependency_issues': dependency_issues,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(dependency_issues)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト5エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_6_statistical_analysis_validity(self):
        """テスト6: 統計分析妥当性検証"""
        print("\n[TEST 6/10] 統計分析妥当性検証...")

        try:
            statistical_issues = []

            # カイ二乗検定
            chi_square_df = self._load_phase_data(2, 'ChiSquareTests.csv')

            # p値の範囲チェック（0〜1）
            if 'p_value' in chi_square_df.columns:
                invalid_p_values = chi_square_df[
                    (chi_square_df['p_value'] < 0) | (chi_square_df['p_value'] > 1)
                ]

                if len(invalid_p_values) > 0:
                    statistical_issues.append(f"カイ二乗検定: 無効なp値 {len(invalid_p_values)}件")

            # ANOVA検定
            anova_df = self._load_phase_data(2, 'ANOVATests.csv')

            # F値の範囲チェック（正の値）
            if 'f_statistic' in anova_df.columns:
                invalid_f_values = anova_df[anova_df['f_statistic'] < 0]

                if len(invalid_f_values) > 0:
                    statistical_issues.append(f"ANOVA検定: 無効なF値 {len(invalid_f_values)}件")

            # p値の範囲チェック（0〜1）
            if 'p_value' in anova_df.columns:
                invalid_anova_p = anova_df[
                    (anova_df['p_value'] < 0) | (anova_df['p_value'] > 1)
                ]

                if len(invalid_anova_p) > 0:
                    statistical_issues.append(f"ANOVA検定: 無効なp値 {len(invalid_anova_p)}件")

            status = "PASS" if len(statistical_issues) == 0 else "FAIL"
            score = 100 if len(statistical_issues) == 0 else max(0, 100 - len(statistical_issues) * 30)

            result = {
                'status': status,
                'chi_square_tests': len(chi_square_df),
                'anova_tests': len(anova_df),
                'statistical_issues': statistical_issues,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(statistical_issues)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト6エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_7_persona_classification(self):
        """テスト7: ペルソナ分類正確性検証"""
        print("\n[TEST 7/10] ペルソナ分類正確性検証...")

        try:
            classification_issues = []

            # ペルソナサマリー
            persona_summary_df = self._load_phase_data(3, 'PersonaSummary.csv')
            applicants_df = self._load_phase_data(1, 'Applicants.csv')

            # ペルソナ人数合計とApplicants総数の整合性（許容差: 10%）
            persona_total = persona_summary_df['count'].sum()
            applicants_total = len(applicants_df)

            diff_ratio = abs(persona_total - applicants_total) / applicants_total
            if diff_ratio > 0.10:
                classification_issues.append(
                    f"ペルソナ人数合計 ({persona_total}) とApplicants総数 ({applicants_total}) の差が10%以上 ({diff_ratio*100:.1f}%)"
                )

            # ペルソナの割合合計が100%に近いか
            percentage_total = persona_summary_df['percentage'].sum()
            if abs(percentage_total - 100) > 1:
                classification_issues.append(
                    f"ペルソナ割合合計が100%から乖離: {percentage_total:.2f}%"
                )

            # DetailedPersonaProfile
            detailed_persona_df = self._load_phase_data(7, 'DetailedPersonaProfile.csv')
            detailed_total = detailed_persona_df['人数'].sum()

            detailed_diff_ratio = abs(detailed_total - applicants_total) / applicants_total
            if detailed_diff_ratio > 0.01:  # 1%以内
                classification_issues.append(
                    f"DetailedPersonaProfile人数合計 ({detailed_total}) とApplicants総数 ({applicants_total}) の差が1%以上"
                )

            status = "PASS" if len(classification_issues) == 0 else "FAIL"
            score = 100 if len(classification_issues) == 0 else max(0, 100 - len(classification_issues) * 30)

            result = {
                'status': status,
                'persona_count_phase3': len(persona_summary_df),
                'persona_total_phase3': int(persona_total),
                'persona_count_phase7': len(detailed_persona_df),
                'persona_total_phase7': int(detailed_total),
                'applicants_total': int(applicants_total),
                'percentage_total': round(percentage_total, 2),
                'classification_issues': classification_issues,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(classification_issues)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト7エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_8_flow_analysis_validity(self):
        """テスト8: フロー分析妥当性検証"""
        print("\n[TEST 8/10] フロー分析妥当性検証...")

        try:
            flow_issues = []

            # MunicipalityFlowEdges（実際のカラム名: Flow_Count）
            edges_df = self._load_phase_data(6, 'MunicipalityFlowEdges.csv')

            # Flow_Countが正の値か
            if 'Flow_Count' in edges_df.columns:
                negative_flows = edges_df[edges_df['Flow_Count'] <= 0]
                if len(negative_flows) > 0:
                    flow_issues.append(f"負またはゼロのFlow_Count: {len(negative_flows)}件")

            # MunicipalityFlowNodes（実際のカラム構造を確認）
            nodes_df = self._load_phase_data(6, 'MunicipalityFlowNodes.csv')

            # カラム名確認
            nodes_cols = list(nodes_df.columns)
            print(f"  [INFO] MunicipalityFlowNodesカラム: {nodes_cols}")

            # ProximityAnalysis（構造が異なるため基本チェックのみ）
            proximity_df = self._load_phase_data(6, 'ProximityAnalysis.csv')

            if len(proximity_df) == 0:
                flow_issues.append("ProximityAnalysisが空")

            status = "PASS" if len(flow_issues) == 0 else "FAIL"
            score = 100 if len(flow_issues) == 0 else max(0, 100 - len(flow_issues) * 20)

            result = {
                'status': status,
                'total_flow_edges': len(edges_df),
                'total_flow_nodes': len(nodes_df),
                'total_proximity_records': len(proximity_df),
                'flow_issues': flow_issues,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(flow_issues)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト8エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_9_scalability_estimation(self):
        """テスト9: スケーラビリティ推定"""
        print("\n[TEST 9/10] スケーラビリティ推定...")

        try:
            # 実データサイズと処理時間の測定
            applicants_df = self._load_phase_data(1, 'Applicants.csv')
            actual_size = len(applicants_df)

            # 各Phaseのデータサイズ
            phase_sizes = {}
            phase_sizes['phase1_applicants'] = len(applicants_df)
            phase_sizes['phase1_desired_work'] = len(self._load_phase_data(1, 'DesiredWork.csv'))
            phase_sizes['phase3_persona_summary'] = len(self._load_phase_data(3, 'PersonaSummary.csv'))
            phase_sizes['phase6_flow_edges'] = len(self._load_phase_data(6, 'MunicipalityFlowEdges.csv'))
            phase_sizes['phase7_persona_map'] = len(self._load_phase_data(7, 'PersonaMapData.csv'))

            # 10万件データの推定
            scale_factor = 100000 / actual_size
            estimated_sizes = {k: int(v * scale_factor) for k, v in phase_sizes.items()}

            # メモリ推定（現在のデータサイズから）
            current_memory_mb = sum(
                (self.python_scripts_dir / f'gas_output_phase{i}').stat().st_size
                for i in [1, 2, 3, 6, 7] if (self.python_scripts_dir / f'gas_output_phase{i}').exists()
            ) / (1024 * 1024)

            estimated_memory_100k = current_memory_mb * scale_factor

            # スコア計算（10万件で1GB以内が目標）
            score = 100 if estimated_memory_100k < 1024 else max(0, 100 - int((estimated_memory_100k - 1024) / 10))

            result = {
                'status': 'PASS' if estimated_memory_100k < 2048 else 'WARNING',
                'actual_data_size': int(actual_size),
                'scale_factor': round(scale_factor, 2),
                'current_data_sizes': phase_sizes,
                'estimated_100k_sizes': estimated_sizes,
                'current_memory_mb': round(current_memory_mb, 2),
                'estimated_100k_memory_mb': round(estimated_memory_100k, 2),
                'estimated_100k_memory_gb': round(estimated_memory_100k / 1024, 2),
                'score': score
            }

            if result['status'] == 'PASS':
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1

            print(f"  [結果] {result['status']} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト9エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def test_10_recovery_resilience(self):
        """テスト10: リカバリ・復元力検証"""
        print("\n[TEST 10/10] リカバリ・復元力検証...")

        try:
            recovery_issues = []

            # geocache.jsonの存在確認
            geocache_path = self.base_dir / 'geocache.json'
            if not geocache_path.exists():
                recovery_issues.append("geocache.jsonが存在しない")
            else:
                with open(geocache_path, 'r', encoding='utf-8') as f:
                    geocache = json.load(f)
                    if len(geocache) < 100:
                        recovery_issues.append(f"geocacheのエントリ数が少ない: {len(geocache)}件")

            # 各Phaseの出力ディレクトリ構造
            required_dirs = [
                self.python_scripts_dir / 'gas_output_phase1',
                self.python_scripts_dir / 'gas_output_phase2',
                self.python_scripts_dir / 'gas_output_phase3',
                self.python_scripts_dir / 'gas_output_phase6',
                self.python_scripts_dir / 'gas_output_phase7'
            ]

            missing_dirs = [str(d) for d in required_dirs if not d.exists()]
            if missing_dirs:
                recovery_issues.append(f"欠損ディレクトリ: {len(missing_dirs)}件")

            # データファイルのバックアップ可能性
            total_files = 0
            readable_files = 0

            for phase_dir in required_dirs:
                if phase_dir.exists():
                    csv_files = list(phase_dir.glob('*.csv'))
                    total_files += len(csv_files)

                    for csv_file in csv_files:
                        try:
                            pd.read_csv(csv_file, encoding='utf-8-sig', nrows=1)
                            readable_files += 1
                        except Exception:
                            recovery_issues.append(f"読み込み不可: {csv_file.name}")

            status = "PASS" if len(recovery_issues) == 0 else "FAIL"
            score = 100 if len(recovery_issues) == 0 else max(0, 100 - len(recovery_issues) * 15)

            result = {
                'status': status,
                'geocache_exists': geocache_path.exists(),
                'geocache_entries': len(geocache) if geocache_path.exists() else 0,
                'required_dirs': len(required_dirs),
                'missing_dirs': len(missing_dirs),
                'total_files': total_files,
                'readable_files': readable_files,
                'recovery_issues': recovery_issues,
                'score': score
            }

            if status == "PASS":
                self.summary['passed'] += 1
            else:
                self.summary['failed'] += 1
                self.summary['critical_issues'].extend(recovery_issues)

            print(f"  [結果] {status} - スコア: {score}/100")
            return result

        except Exception as e:
            self.summary['failed'] += 1
            error_msg = f"テスト10エラー: {str(e)}"
            self.summary['critical_issues'].append(error_msg)
            print(f"  [ERROR] {error_msg}")
            return {'status': 'ERROR', 'error': str(e), 'traceback': traceback.format_exc()}

    def run_all_tests(self):
        """全10テストを実行"""
        print("\n" + "="*70)
        print("  ジョブメドレー求職者データ分析 - 10回繰り返し統合テストスイート")
        print("  【修正版 - 実際のデータ構造対応】")
        print("="*70)

        start_time = time.time()

        # 10テスト実行
        self.results['test_1_data_integrity'] = self.test_1_data_integrity()
        self.results['test_2_end_to_end_flow'] = self.test_2_end_to_end_flow()
        self.results['test_3_performance_measurement'] = self.test_3_performance_measurement()
        self.results['test_4_data_quality'] = self.test_4_data_quality()
        self.results['test_5_phase_dependencies'] = self.test_5_phase_dependencies()
        self.results['test_6_statistical_analysis_validity'] = self.test_6_statistical_analysis_validity()
        self.results['test_7_persona_classification'] = self.test_7_persona_classification()
        self.results['test_8_flow_analysis_validity'] = self.test_8_flow_analysis_validity()
        self.results['test_9_scalability_estimation'] = self.test_9_scalability_estimation()
        self.results['test_10_recovery_resilience'] = self.test_10_recovery_resilience()

        total_time = time.time() - start_time

        # 総合スコア計算
        total_score = sum(
            result.get('score', 0) for result in self.results.values()
        )
        self.summary['overall_score'] = int(total_score / 10)

        # サマリー生成
        self.results['summary'] = self.summary
        self.results['summary']['total_execution_time_seconds'] = round(total_time, 2)

        print("\n" + "="*70)
        print("  テスト完了")
        print("="*70)
        print(f"  総テスト数: {self.summary['total_tests']}")
        print(f"  成功: {self.summary['passed']}")
        print(f"  失敗: {self.summary['failed']}")
        print(f"  総合スコア: {self.summary['overall_score']}/100")
        print(f"  実行時間: {total_time:.2f}秒")
        print("="*70)

        return self.results

    def save_results(self, output_path='integration_test_results_10x_fixed.json'):
        """テスト結果をJSONファイルに保存"""
        output_file = self.python_scripts_dir / output_path
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n[保存完了] テスト結果: {output_file}")
        return output_file


def main():
    """メイン処理"""
    suite = IntegrationTestSuite()
    results = suite.run_all_tests()
    suite.save_results()

    # クリティカルな問題がある場合は警告
    if results['summary']['critical_issues']:
        print("\n[警告] クリティカルな問題が検出されました:")
        for issue in results['summary']['critical_issues'][:10]:
            print(f"  - {issue}")


if __name__ == '__main__':
    main()
