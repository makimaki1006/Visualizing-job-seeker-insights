"""Ultrathink Stage 11-20: 超深掘りデータ妥当性検証"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

class UltrathinkValidator:
    def __init__(self):
        self.base_dir = Path('data/output_v2')
        self.map_complete_path = self.base_dir / 'mapcomplete_complete_sheets' / 'MapComplete_Complete_All.csv'
        self.df_map = pd.read_csv(self.map_complete_path, encoding='utf-8-sig')
        self.results = {}

    def stage11_municipality_normalization_check(self):
        """Stage 11: municipality列の正規化ロジック検証"""
        print('\n' + '='*100)
        print('STAGE 11: Municipality Normalization Logic Validation')
        print('='*100)

        issues = []

        # 各row_typeのmunicipality列を確認
        for row_type in self.df_map['row_type'].unique():
            df_rt = self.df_map[self.df_map['row_type'] == row_type]

            # municipality列に都道府県名が残っているか確認
            for _, row in df_rt.iterrows():
                muni = str(row['municipality'])
                pref = str(row['prefecture'])

                # 都道府県名で始まるmunicipality（都道府県名が除去されていない）
                if muni.startswith(pref) and muni != pref:
                    issues.append({
                        'row_type': row_type,
                        'prefecture': pref,
                        'municipality': muni,
                        'issue': 'Prefecture name not removed from municipality'
                    })

        print(f'Total municipality normalization issues: {len(issues)}')
        if len(issues) > 0:
            print(f'Sample issues (first 10):')
            for issue in issues[:10]:
                print(f'  {issue["row_type"]}: {issue["prefecture"]} | {issue["municipality"]}')

        self.results['stage11'] = {
            'total_issues': len(issues),
            'sample_issues': issues[:20]
        }

        return len(issues) == 0

    def stage12_duplicate_records_check(self):
        """Stage 12: 重複レコードの完全検証"""
        print('\n' + '='*100)
        print('STAGE 12: Duplicate Records Comprehensive Check')
        print('='*100)

        duplicate_info = {}

        for row_type in self.df_map['row_type'].unique():
            df_rt = self.df_map[self.df_map['row_type'] == row_type]

            # prefecture, municipality, category1, category2の組み合わせで重複チェック
            key_cols = ['prefecture', 'municipality', 'category1', 'category2']
            existing_cols = [col for col in key_cols if col in df_rt.columns]

            if len(existing_cols) >= 2:
                duplicates = df_rt[df_rt.duplicated(subset=existing_cols, keep=False)]

                if len(duplicates) > 0:
                    duplicate_info[row_type] = {
                        'count': len(duplicates),
                        'unique_keys': len(duplicates.drop_duplicates(subset=existing_cols))
                    }
                    print(f'{row_type}: {len(duplicates)} duplicate rows')

        self.results['stage12'] = duplicate_info
        return len(duplicate_info) == 0

    def stage13_numeric_data_integrity(self):
        """Stage 13: 数値データの整合性検証"""
        print('\n' + '='*100)
        print('STAGE 13: Numeric Data Integrity Validation')
        print('='*100)

        numeric_issues = {}

        numeric_cols = ['count', 'avg_age', 'avg_urgency_score', 'rarity_score',
                        'gap', 'demand_count', 'supply_count', 'inflow', 'outflow']

        for col in numeric_cols:
            if col in self.df_map.columns:
                series = self.df_map[col]

                # 負の値チェック
                negative_count = (series < 0).sum()

                # NaN/Inf チェック
                nan_count = series.isna().sum()
                inf_count = np.isinf(series).sum() if series.dtype in [np.float64, np.float32] else 0

                # 異常値チェック（極端に大きい値）
                if series.dtype in [np.float64, np.float32, np.int64, np.int32]:
                    mean_val = series.mean()
                    std_val = series.std()
                    outliers = ((series - mean_val).abs() > 5 * std_val).sum()
                else:
                    outliers = 0

                if negative_count > 0 or inf_count > 0 or outliers > 10:
                    numeric_issues[col] = {
                        'negative': int(negative_count),
                        'nan': int(nan_count),
                        'inf': int(inf_count),
                        'outliers': int(outliers)
                    }

        print(f'Numeric columns with issues: {len(numeric_issues)}')
        for col, issues in numeric_issues.items():
            print(f'  {col}: {issues}')

        self.results['stage13'] = numeric_issues
        return len(numeric_issues) == 0

    def stage14_prefecture_coverage_check(self):
        """Stage 14: 都道府県カバレッジ検証"""
        print('\n' + '='*100)
        print('STAGE 14: Prefecture Coverage Validation')
        print('='*100)

        expected_prefs = 47  # 日本の都道府県数
        coverage = {}

        for row_type in self.df_map['row_type'].unique():
            df_rt = self.df_map[self.df_map['row_type'] == row_type]
            actual_prefs = df_rt['prefecture'].nunique()

            coverage[row_type] = {
                'expected': expected_prefs,
                'actual': actual_prefs,
                'coverage_pct': actual_prefs / expected_prefs * 100
            }

            if actual_prefs < expected_prefs:
                missing_prefs = set(self.df_map['prefecture'].unique()) - set(df_rt['prefecture'].unique())
                coverage[row_type]['missing'] = list(missing_prefs)
                print(f'{row_type}: {actual_prefs}/{expected_prefs} prefectures ({actual_prefs/expected_prefs*100:.1f}%)')
                if len(missing_prefs) <= 5:
                    print(f'  Missing: {missing_prefs}')

        self.results['stage14'] = coverage
        return all(v['actual'] >= 40 for v in coverage.values())  # 40都道府県以上をOKとする

    def stage15_category_consistency_check(self):
        """Stage 15: カテゴリー値の一貫性検証"""
        print('\n' + '='*100)
        print('STAGE 15: Category Value Consistency Check')
        print('='*100)

        category_issues = {}

        # category1, category2, category3の値が適切か確認
        for row_type in self.df_map['row_type'].unique():
            df_rt = self.df_map[self.df_map['row_type'] == row_type]

            for cat_col in ['category1', 'category2', 'category3']:
                if cat_col in df_rt.columns:
                    unique_vals = df_rt[cat_col].unique()

                    # 空文字列、NaN以外の異常な値をチェック
                    non_standard = [v for v in unique_vals if pd.notna(v) and str(v).strip() != '' and len(str(v)) > 100]

                    if len(non_standard) > 0:
                        if row_type not in category_issues:
                            category_issues[row_type] = {}
                        category_issues[row_type][cat_col] = {
                            'total_unique': len(unique_vals),
                            'non_standard_count': len(non_standard),
                            'samples': non_standard[:3]
                        }

        print(f'Row types with category issues: {len(category_issues)}')
        self.results['stage15'] = category_issues
        return len(category_issues) == 0

    def stage16_row_count_distribution_analysis(self):
        """Stage 16: 行数分布の統計的分析"""
        print('\n' + '='*100)
        print('STAGE 16: Row Count Distribution Statistical Analysis')
        print('='*100)

        distribution_analysis = {}

        for row_type in self.df_map['row_type'].unique():
            df_rt = self.df_map[self.df_map['row_type'] == row_type]

            # 都道府県別の行数分布
            pref_counts = df_rt.groupby('prefecture').size()

            analysis = {
                'total_rows': len(df_rt),
                'prefecture_count': len(pref_counts),
                'mean_rows_per_pref': float(pref_counts.mean()),
                'std_rows_per_pref': float(pref_counts.std()),
                'min_rows': int(pref_counts.min()),
                'max_rows': int(pref_counts.max()),
                'coefficient_of_variation': float(pref_counts.std() / pref_counts.mean()) if pref_counts.mean() > 0 else 0
            }

            # 変動係数が異常に小さい（ほぼ同じ行数）場合は重複の可能性
            if analysis['coefficient_of_variation'] < 0.01 and analysis['prefecture_count'] > 40:
                analysis['warning'] = 'POSSIBLE DUPLICATION: All prefectures have nearly identical row counts'
                print(f'{row_type}: WARNING - Coefficient of Variation = {analysis["coefficient_of_variation"]:.4f}')

            distribution_analysis[row_type] = analysis

        self.results['stage16'] = distribution_analysis
        return True

    def stage17_source_data_lineage_check(self):
        """Stage 17: ソースデータの系譜追跡"""
        print('\n' + '='*100)
        print('STAGE 17: Source Data Lineage Tracking')
        print('='*100)

        lineage = {}

        # 各row_typeのソースファイルを特定
        row_type_sources = {
            'SUMMARY': ('phase1', 'Phase1_MapMetrics.csv'),
            'AGE_GENDER': ('phase7', 'Phase7_AgeGenderCrossAnalysis.csv'),
            'PERSONA': ('phase7', 'Phase7_DetailedPersonaProfile.csv'),
            'PERSONA_MUNI': ('phase3', 'Phase3_PersonaSummaryByMunicipality.csv'),
            'CAREER_CROSS': ('phase8', 'Phase8_CareerAgeCross.csv'),
            'URGENCY_AGE': ('phase10', 'Phase10_UrgencyAgeCross_ByMunicipality.csv'),
            'URGENCY_EMPLOYMENT': ('phase10', 'Phase10_UrgencyEmploymentCross_ByMunicipality.csv'),
            'FLOW': ('phase6', 'Phase6_MunicipalityFlowNodes.csv'),
            'GAP': ('phase12', 'Phase12_SupplyDemandGap.csv'),
            'RARITY': ('phase13', 'Phase13_RarityScore.csv'),
            'COMPETITION': ('phase14', 'Phase14_CompetitionProfile.csv'),
        }

        for row_type, (phase, filename) in row_type_sources.items():
            source_path = self.base_dir / phase / filename

            if source_path.exists():
                df_source = pd.read_csv(source_path, encoding='utf-8-sig')
                df_map_rt = self.df_map[self.df_map['row_type'] == row_type]

                lineage[row_type] = {
                    'source_file': str(source_path),
                    'source_rows': len(df_source),
                    'map_rows': len(df_map_rt),
                    'row_diff': len(df_map_rt) - len(df_source),
                    'has_prefecture_col': 'prefecture' in df_source.columns,
                    'has_location_col': 'location' in df_source.columns
                }

                if lineage[row_type]['row_diff'] != 0:
                    print(f'{row_type}: Source {len(df_source)} -> Map {len(df_map_rt)} (diff: {lineage[row_type]["row_diff"]})')

        self.results['stage17'] = lineage
        return True

    def stage18_coordinate_data_validation(self):
        """Stage 18: 座標データの妥当性検証"""
        print('\n' + '='*100)
        print('STAGE 18: Coordinate Data Validation')
        print('='*100)

        coord_issues = {}

        if 'latitude' in self.df_map.columns and 'longitude' in self.df_map.columns:
            # 日本の緯度経度範囲
            valid_lat_range = (24.0, 46.0)  # 沖縄～北海道
            valid_lon_range = (122.0, 154.0)  # 与那国島～択捉島

            invalid_lat = ((self.df_map['latitude'] < valid_lat_range[0]) |
                          (self.df_map['latitude'] > valid_lat_range[1])).sum()
            invalid_lon = ((self.df_map['longitude'] < valid_lon_range[0]) |
                          (self.df_map['longitude'] > valid_lon_range[1])).sum()

            missing_coords = (self.df_map['latitude'].isna() | self.df_map['longitude'].isna()).sum()

            coord_issues = {
                'invalid_latitude_count': int(invalid_lat),
                'invalid_longitude_count': int(invalid_lon),
                'missing_coordinates_count': int(missing_coords),
                'total_rows': len(self.df_map)
            }

            print(f'Invalid latitude: {invalid_lat}')
            print(f'Invalid longitude: {invalid_lon}')
            print(f'Missing coordinates: {missing_coords}')

        self.results['stage18'] = coord_issues
        return coord_issues.get('invalid_latitude_count', 0) == 0 and coord_issues.get('invalid_longitude_count', 0) == 0

    def stage19_data_type_consistency(self):
        """Stage 19: データ型の一貫性検証"""
        print('\n' + '='*100)
        print('STAGE 19: Data Type Consistency Validation')
        print('='*100)

        type_issues = {}

        expected_types = {
            'prefecture': 'object',
            'municipality': 'object',
            'row_type': 'object',
            'count': ['int64', 'float64'],
            'avg_age': ['float64'],
            'latitude': ['float64'],
            'longitude': ['float64']
        }

        for col, expected in expected_types.items():
            if col in self.df_map.columns:
                actual_type = str(self.df_map[col].dtype)

                if isinstance(expected, list):
                    if actual_type not in expected:
                        type_issues[col] = {
                            'expected': expected,
                            'actual': actual_type
                        }
                else:
                    if actual_type != expected:
                        type_issues[col] = {
                            'expected': expected,
                            'actual': actual_type
                        }

        print(f'Columns with type issues: {len(type_issues)}')
        for col, issue in type_issues.items():
            print(f'  {col}: expected {issue["expected"]}, got {issue["actual"]}')

        self.results['stage19'] = type_issues
        return len(type_issues) == 0

    def stage20_comprehensive_summary(self):
        """Stage 20: 包括的検証サマリー"""
        print('\n' + '='*100)
        print('STAGE 20: Comprehensive Validation Summary')
        print('='*100)

        # 全ステージの結果を集計
        summary = {
            'total_rows': len(self.df_map),
            'total_columns': len(self.df_map.columns),
            'row_types_count': self.df_map['row_type'].nunique(),
            'prefectures_count': self.df_map['prefecture'].nunique(),
            'validation_stages_completed': 20,
            'critical_issues': [],
            'warnings': [],
            'passed_checks': []
        }

        # Stage 11-19の結果を解析
        if self.results.get('stage11', {}).get('total_issues', 0) > 0:
            summary['warnings'].append(f'Stage 11: {self.results["stage11"]["total_issues"]} municipality normalization issues')
        else:
            summary['passed_checks'].append('Stage 11: Municipality normalization OK')

        if len(self.results.get('stage12', {})) > 0:
            summary['critical_issues'].append(f'Stage 12: Duplicate records found in {len(self.results["stage12"])} row types')
        else:
            summary['passed_checks'].append('Stage 12: No duplicate records')

        if len(self.results.get('stage13', {})) > 0:
            summary['warnings'].append(f'Stage 13: Numeric data issues in {len(self.results["stage13"])} columns')
        else:
            summary['passed_checks'].append('Stage 13: Numeric data integrity OK')

        # Stage 16の重複警告をチェック
        stage16_warnings = [k for k, v in self.results.get('stage16', {}).items()
                           if 'warning' in v]
        if stage16_warnings:
            summary['critical_issues'].append(f'Stage 16: Possible duplication in {len(stage16_warnings)} row types')

        # Stage 17の行数差分をチェック
        stage17_diffs = {k: v for k, v in self.results.get('stage17', {}).items()
                        if abs(v.get('row_diff', 0)) > 0}
        if stage17_diffs:
            summary['warnings'].append(f'Stage 17: Row count differences in {len(stage17_diffs)} row types')

        print('\n' + '='*100)
        print('VALIDATION SUMMARY')
        print('='*100)
        print(f'Total Rows: {summary["total_rows"]:,}')
        print(f'Total Columns: {summary["total_columns"]}')
        print(f'Row Types: {summary["row_types_count"]}')
        print(f'Prefectures: {summary["prefectures_count"]}')
        print(f'\nCritical Issues: {len(summary["critical_issues"])}')
        for issue in summary["critical_issues"]:
            print(f'  - {issue}')
        print(f'\nWarnings: {len(summary["warnings"])}')
        for warning in summary["warnings"]:
            print(f'  - {warning}')
        print(f'\nPassed Checks: {len(summary["passed_checks"])}')
        for check in summary["passed_checks"]:
            print(f'  - {check}')

        self.results['stage20_summary'] = summary
        return summary

    def run_all_stages(self):
        """全ステージを実行"""
        print('='*100)
        print('ULTRATHINK VALIDATION: STAGE 11-20')
        print('='*100)

        self.stage11_municipality_normalization_check()
        self.stage12_duplicate_records_check()
        self.stage13_numeric_data_integrity()
        self.stage14_prefecture_coverage_check()
        self.stage15_category_consistency_check()
        self.stage16_row_count_distribution_analysis()
        self.stage17_source_data_lineage_check()
        self.stage18_coordinate_data_validation()
        self.stage19_data_type_consistency()
        summary = self.stage20_comprehensive_summary()

        # 結果をJSON保存
        output_path = self.base_dir / 'mapcomplete_complete_sheets' / 'validation_stage11_20.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)

        print(f'\n\nValidation results saved to: {output_path}')

        return summary

if __name__ == '__main__':
    validator = UltrathinkValidator()
    summary = validator.run_all_stages()
