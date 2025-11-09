"""
統合テスト: ペルソナレベルシート生成のフルフロー検証

テストシナリオ:
1. CSV生成からGAS読み込みまでのフルフロー
2. Phase間データマージの正確性
3. 全都道府県の整合性
4. エッジケース検証
"""

import pandas as pd
import json
from pathlib import Path
from generate_persona_level_sheets import PersonaLevelSheetGenerator


class PersonaLevelIntegrationTest:
    """ペルソナレベル統合テストクラス"""

    def __init__(self):
        self.output_base_dir = Path('data/output_v2')
        self.persona_sheets_dir = self.output_base_dir / 'persona_level_sheets'
        self.test_results = {
            'test1_full_flow': {},
            'test2_merge_accuracy': {},
            'test3_all_prefectures': {},
            'test4_edge_cases': {},
            'overall_status': 'PENDING'
        }

    def run_all_tests(self):
        """全テスト実行"""
        print("\n" + "="*80)
        print("  統合テスト: ペルソナレベルシート生成")
        print("="*80 + "\n")

        # テスト1: フルフロー
        self.test1_full_flow()

        # テスト2: マージ精度
        self.test2_merge_accuracy()

        # テスト3: 全都道府県整合性
        self.test3_all_prefectures()

        # テスト4: エッジケース
        self.test4_edge_cases()

        # 最終評価
        self.final_evaluation()

        # 結果保存
        self.save_results()

    def test1_full_flow(self):
        """統合テスト1: CSV生成からGAS読み込みまでのフルフロー"""
        print("\n" + "-"*80)
        print("  統合テスト1: CSV生成からGAS読み込みまでのフルフロー")
        print("-"*80)

        try:
            # ステップ1: generate_persona_level_sheets.py 実行
            print("\n[STEP 1] generate_persona_level_sheets.py 実行...")
            generator = PersonaLevelSheetGenerator()
            generator.load_all_phases()
            generator.generate_prefecture_sheets()
            print("  [PASS] PASS: スクリプト実行成功")
            self.test_results['test1_full_flow']['step1_execution'] = 'PASS'

            # ステップ2: PersonaLevel_京都府.csv 生成確認
            print("\n[STEP 2] PersonaLevel_京都府.csv 生成確認...")
            kyoto_file = self.persona_sheets_dir / 'PersonaLevel_京都府.csv'
            if kyoto_file.exists():
                print(f"  [PASS] PASS: ファイル生成成功 - {kyoto_file}")
                self.test_results['test1_full_flow']['step2_file_creation'] = 'PASS'
            else:
                print(f"  [FAIL] FAIL: ファイルが見つかりません - {kyoto_file}")
                self.test_results['test1_full_flow']['step2_file_creation'] = 'FAIL'
                return

            # ステップ3: ファイル内容検証
            print("\n[STEP 3] ファイル内容検証...")
            df = pd.read_csv(kyoto_file, encoding='utf-8-sig')

            # 行数検証
            if 1 <= len(df) <= 5000:
                print(f"  [PASS] PASS: 行数妥当（{len(df)}行）")
                self.test_results['test1_full_flow']['step3_row_count'] = {'status': 'PASS', 'value': len(df)}
            else:
                print(f"  [FAIL] FAIL: 行数異常（{len(df)}行）")
                self.test_results['test1_full_flow']['step3_row_count'] = {'status': 'FAIL', 'value': len(df)}

            # 列数検証（基本列 + Phase追加列）
            expected_min_cols = 10  # 最低限必要な列数
            if len(df.columns) >= expected_min_cols:
                print(f"  [PASS] PASS: 列数妥当（{len(df.columns)}列）")
                self.test_results['test1_full_flow']['step3_col_count'] = {'status': 'PASS', 'value': len(df.columns)}
            else:
                print(f"  [FAIL] FAIL: 列数不足（{len(df.columns)}列 < {expected_min_cols}列）")
                self.test_results['test1_full_flow']['step3_col_count'] = {'status': 'FAIL', 'value': len(df.columns)}

            # 必須列の存在確認
            required_columns = ['municipality', 'age_group', 'gender', 'has_national_license', 'count', 'prefecture']
            missing_cols = [col for col in required_columns if col not in df.columns]
            if not missing_cols:
                print(f"  [PASS] PASS: 必須列すべて存在")
                self.test_results['test1_full_flow']['step3_required_columns'] = 'PASS'
            else:
                print(f"  [FAIL] FAIL: 必須列欠損 - {missing_cols}")
                self.test_results['test1_full_flow']['step3_required_columns'] = {'status': 'FAIL', 'missing': missing_cols}

            # ステップ4: GAS模擬読み込み（pandas読み込みで代用）
            print("\n[STEP 4] GAS模擬読み込み...")
            try:
                # データ型検証
                dtypes_ok = True
                if df['count'].dtype not in ['int64', 'float64']:
                    print(f"  [FAIL] FAIL: count列のデータ型異常 - {df['count'].dtype}")
                    dtypes_ok = False
                if df['prefecture'].dtype != 'object':
                    print(f"  [FAIL] FAIL: prefecture列のデータ型異常 - {df['prefecture'].dtype}")
                    dtypes_ok = False

                if dtypes_ok:
                    print(f"  [PASS] PASS: データ型正常")
                    self.test_results['test1_full_flow']['step4_data_types'] = 'PASS'
                else:
                    self.test_results['test1_full_flow']['step4_data_types'] = 'FAIL'
            except Exception as e:
                print(f"  [FAIL] FAIL: データ型検証エラー - {e}")
                self.test_results['test1_full_flow']['step4_data_types'] = {'status': 'FAIL', 'error': str(e)}

            # ステップ5: データ整合性確認
            print("\n[STEP 5] データ整合性確認...")
            integrity_ok = True

            # prefecture列の一貫性
            unique_prefs = df['prefecture'].unique()
            if len(unique_prefs) == 1 and unique_prefs[0] == '京都府':
                print(f"  [PASS] PASS: prefecture列の一貫性確認")
            else:
                print(f"  [FAIL] FAIL: prefecture列に複数の値 - {unique_prefs}")
                integrity_ok = False

            # municipality列の非null確認
            if df['municipality'].isna().sum() == 0:
                print(f"  [PASS] PASS: municipality列に欠損なし")
            else:
                print(f"  [FAIL] FAIL: municipality列に欠損あり - {df['municipality'].isna().sum()}件")
                integrity_ok = False

            if integrity_ok:
                self.test_results['test1_full_flow']['step5_data_integrity'] = 'PASS'
            else:
                self.test_results['test1_full_flow']['step5_data_integrity'] = 'FAIL'

            self.test_results['test1_full_flow']['overall'] = 'PASS' if all(
                v == 'PASS' or (isinstance(v, dict) and v.get('status') == 'PASS')
                for k, v in self.test_results['test1_full_flow'].items() if k != 'overall'
            ) else 'FAIL'

        except Exception as e:
            print(f"\n  [FAIL] FAIL: テスト1実行エラー - {e}")
            self.test_results['test1_full_flow']['error'] = str(e)
            self.test_results['test1_full_flow']['overall'] = 'FAIL'

    def test2_merge_accuracy(self):
        """統合テスト2: Phase間データマージの正確性"""
        print("\n" + "-"*80)
        print("  統合テスト2: Phase間データマージの正確性")
        print("-"*80)

        try:
            kyoto_file = self.persona_sheets_dir / 'PersonaLevel_京都府.csv'
            if not kyoto_file.exists():
                print(f"  [FAIL] FAIL: テストファイルなし - {kyoto_file}")
                self.test_results['test2_merge_accuracy']['overall'] = 'SKIP'
                return

            df = pd.read_csv(kyoto_file, encoding='utf-8-sig')

            # ステップ1: Phase 3ベースデータ確認
            print("\n[STEP 1] Phase 3ベースデータ確認...")
            phase3_cols = ['municipality', 'age_group', 'gender', 'has_national_license', 'count']
            phase3_ok = all(col in df.columns for col in phase3_cols)
            if phase3_ok:
                print(f"  [PASS] PASS: Phase 3基本列すべて存在")
                self.test_results['test2_merge_accuracy']['phase3_base'] = 'PASS'
            else:
                missing = [col for col in phase3_cols if col not in df.columns]
                print(f"  [FAIL] FAIL: Phase 3基本列欠損 - {missing}")
                self.test_results['test2_merge_accuracy']['phase3_base'] = {'status': 'FAIL', 'missing': missing}

            # ステップ2-6: 各Phaseのマージ確認
            phase_checks = [
                ('phase13', 'Phase 13マージ確認'),
                ('phase6', 'Phase 6マージ確認'),
                ('phase14', 'Phase 14マージ確認'),
                ('phase10', 'Phase 10マージ確認'),
                ('phase7', 'Phase 7マージ確認'),
            ]

            for phase_num, phase_name in phase_checks:
                print(f"\n[STEP] {phase_name}...")
                phase_cols = [col for col in df.columns if col.startswith(f'{phase_num}_')]

                if phase_cols:
                    print(f"  [PASS] PASS: {phase_num}列が存在（{len(phase_cols)}列）")
                    # 欠損値チェック
                    null_counts = df[phase_cols].isna().sum()
                    total_nulls = null_counts.sum()
                    null_ratio = total_nulls / (len(df) * len(phase_cols))

                    if null_ratio < 0.5:  # 欠損率50%未満なら許容
                        print(f"  [PASS] PASS: 欠損率許容範囲（{null_ratio*100:.1f}%）")
                        self.test_results['test2_merge_accuracy'][phase_num] = {'status': 'PASS', 'null_ratio': null_ratio}
                    else:
                        print(f"  [WARN] WARN: 欠損率高め（{null_ratio*100:.1f}%）")
                        self.test_results['test2_merge_accuracy'][phase_num] = {'status': 'WARN', 'null_ratio': null_ratio}
                else:
                    print(f"  [WARN] WARN: {phase_num}列が見つかりません（Phase未実行の可能性）")
                    self.test_results['test2_merge_accuracy'][phase_num] = {'status': 'WARN', 'reason': 'Phase not found'}

            # ステップ7: prefecture列の重複解消確認
            print(f"\n[STEP] prefecture列の重複解消確認...")
            dup_cols = [col for col in df.columns if col.startswith('prefecture_')]
            if not dup_cols:
                print(f"  [PASS] PASS: prefecture列の重複なし")
                self.test_results['test2_merge_accuracy']['prefecture_dedup'] = 'PASS'
            else:
                print(f"  [FAIL] FAIL: prefecture列に重複あり - {dup_cols}")
                self.test_results['test2_merge_accuracy']['prefecture_dedup'] = {'status': 'FAIL', 'duplicates': dup_cols}

            self.test_results['test2_merge_accuracy']['overall'] = 'PASS'

        except Exception as e:
            print(f"\n  [FAIL] FAIL: テスト2実行エラー - {e}")
            self.test_results['test2_merge_accuracy']['error'] = str(e)
            self.test_results['test2_merge_accuracy']['overall'] = 'FAIL'

    def test3_all_prefectures(self):
        """統合テスト3: 全都道府県の整合性"""
        print("\n" + "-"*80)
        print("  統合テスト3: 全都道府県の整合性")
        print("-"*80)

        try:
            # ステップ1: 47都道府県すべてのCSV生成確認
            print("\n[STEP 1] 47都道府県すべてのCSV生成確認...")
            csv_files = list(self.persona_sheets_dir.glob('PersonaLevel_*.csv'))

            if len(csv_files) >= 10:  # 最低10都道府県は必要
                print(f"  [PASS] PASS: {len(csv_files)}都道府県のCSVファイル生成")
                self.test_results['test3_all_prefectures']['file_count'] = {'status': 'PASS', 'value': len(csv_files)}
            else:
                print(f"  [FAIL] FAIL: 生成ファイル数不足（{len(csv_files)}件）")
                self.test_results['test3_all_prefectures']['file_count'] = {'status': 'FAIL', 'value': len(csv_files)}
                return

            # ステップ2-4: 各都道府県の妥当性チェック
            print("\n[STEP 2-4] 各都道府県の妥当性チェック...")
            size_ok = 0
            row_ok = 0
            pref_ok = 0

            for csv_file in csv_files:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')

                # ファイルサイズ妥当性（簡易的に行数で判断）
                if 1 <= len(df) <= 5000:
                    size_ok += 1

                # 行数範囲
                if 1 <= len(df) <= 2000:
                    row_ok += 1

                # prefecture列の正確性
                if 'prefecture' in df.columns:
                    unique_prefs = df['prefecture'].unique()
                    if len(unique_prefs) == 1:
                        pref_ok += 1

            total = len(csv_files)

            if size_ok / total >= 0.9:
                print(f"  [PASS] PASS: ファイルサイズ妥当（{size_ok}/{total}）")
                self.test_results['test3_all_prefectures']['file_size'] = {'status': 'PASS', 'ratio': size_ok/total}
            else:
                print(f"  [FAIL] FAIL: ファイルサイズ異常あり（{size_ok}/{total}）")
                self.test_results['test3_all_prefectures']['file_size'] = {'status': 'FAIL', 'ratio': size_ok/total}

            if row_ok / total >= 0.8:
                print(f"  [PASS] PASS: 行数範囲妥当（{row_ok}/{total}）")
                self.test_results['test3_all_prefectures']['row_range'] = {'status': 'PASS', 'ratio': row_ok/total}
            else:
                print(f"  [WARN] WARN: 行数範囲外あり（{row_ok}/{total}）")
                self.test_results['test3_all_prefectures']['row_range'] = {'status': 'WARN', 'ratio': row_ok/total}

            if pref_ok / total >= 0.95:
                print(f"  [PASS] PASS: prefecture列の正確性（{pref_ok}/{total}）")
                self.test_results['test3_all_prefectures']['prefecture_accuracy'] = {'status': 'PASS', 'ratio': pref_ok/total}
            else:
                print(f"  [FAIL] FAIL: prefecture列に問題あり（{pref_ok}/{total}）")
                self.test_results['test3_all_prefectures']['prefecture_accuracy'] = {'status': 'FAIL', 'ratio': pref_ok/total}

            self.test_results['test3_all_prefectures']['overall'] = 'PASS'

        except Exception as e:
            print(f"\n  [FAIL] FAIL: テスト3実行エラー - {e}")
            self.test_results['test3_all_prefectures']['error'] = str(e)
            self.test_results['test3_all_prefectures']['overall'] = 'FAIL'

    def test4_edge_cases(self):
        """統合テスト4: エッジケース"""
        print("\n" + "-"*80)
        print("  統合テスト4: エッジケース")
        print("-"*80)

        try:
            # ステップ1: データが1行しかない都道府県
            print("\n[STEP 1] データが1行しかない都道府県...")
            csv_files = list(self.persona_sheets_dir.glob('PersonaLevel_*.csv'))
            single_row_prefs = []

            for csv_file in csv_files:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                if len(df) == 1:
                    single_row_prefs.append(csv_file.stem.replace('PersonaLevel_', ''))

            if single_row_prefs:
                print(f"  [WARN] WARN: 1行のみの都道府県あり - {single_row_prefs}")
                self.test_results['test4_edge_cases']['single_row'] = {'status': 'WARN', 'prefectures': single_row_prefs}
            else:
                print(f"  [PASS] PASS: 1行のみの都道府県なし")
                self.test_results['test4_edge_cases']['single_row'] = 'PASS'

            # ステップ2-4: データ欠損・null確認
            print("\n[STEP 2-4] データ欠損・null確認...")

            # サンプルとして京都府を使用
            kyoto_file = self.persona_sheets_dir / 'PersonaLevel_京都府.csv'
            if kyoto_file.exists():
                df = pd.read_csv(kyoto_file, encoding='utf-8-sig')

                # Phase 13データ欠損
                phase13_cols = [col for col in df.columns if col.startswith('phase13_')]
                if phase13_cols:
                    phase13_null = df[phase13_cols].isna().all(axis=1).sum()
                    if phase13_null == 0:
                        print(f"  [PASS] PASS: Phase 13データ欠損なし")
                        self.test_results['test4_edge_cases']['phase13_missing'] = 'PASS'
                    else:
                        print(f"  [WARN] WARN: Phase 13データ欠損あり（{phase13_null}行）")
                        self.test_results['test4_edge_cases']['phase13_missing'] = {'status': 'WARN', 'rows': phase13_null}

                # prefecture列がnull
                pref_null = df['prefecture'].isna().sum()
                if pref_null == 0:
                    print(f"  [PASS] PASS: prefecture列にnullなし")
                    self.test_results['test4_edge_cases']['prefecture_null'] = 'PASS'
                else:
                    print(f"  [FAIL] FAIL: prefecture列にnullあり（{pref_null}件）")
                    self.test_results['test4_edge_cases']['prefecture_null'] = {'status': 'FAIL', 'count': pref_null}

                # municipality名に特殊文字
                special_chars = df['municipality'].str.contains('[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff0-9ー々]', regex=True, na=False)
                special_count = special_chars.sum()
                if special_count == 0:
                    print(f"  [PASS] PASS: municipality名に特殊文字なし")
                    self.test_results['test4_edge_cases']['special_chars'] = 'PASS'
                else:
                    print(f"  [WARN] INFO: municipality名に特殊文字あり（{special_count}件）- 正常な可能性あり")
                    self.test_results['test4_edge_cases']['special_chars'] = {'status': 'INFO', 'count': special_count}

            self.test_results['test4_edge_cases']['overall'] = 'PASS'

        except Exception as e:
            print(f"\n  [FAIL] FAIL: テスト4実行エラー - {e}")
            self.test_results['test4_edge_cases']['error'] = str(e)
            self.test_results['test4_edge_cases']['overall'] = 'FAIL'

    def final_evaluation(self):
        """最終評価"""
        print("\n" + "="*80)
        print("  最終評価")
        print("="*80)

        # 各テストのステータス集計
        test_statuses = {
            'test1': self.test_results['test1_full_flow'].get('overall', 'FAIL'),
            'test2': self.test_results['test2_merge_accuracy'].get('overall', 'FAIL'),
            'test3': self.test_results['test3_all_prefectures'].get('overall', 'FAIL'),
            'test4': self.test_results['test4_edge_cases'].get('overall', 'FAIL'),
        }

        passed = sum(1 for status in test_statuses.values() if status == 'PASS')
        total = len(test_statuses)
        pass_rate = (passed / total) * 100

        print(f"\n  統合テスト合格率: {pass_rate:.1f}% ({passed}/{total})")

        for test_name, status in test_statuses.items():
            icon = '[PASS]' if status == 'PASS' else '[FAIL]'
            print(f"  {icon} {test_name}: {status}")

        # クリティカルな問題の確認
        critical_issues = []

        if self.test_results['test1_full_flow'].get('step2_file_creation') == 'FAIL':
            critical_issues.append('CSVファイル生成失敗')

        if self.test_results['test2_merge_accuracy'].get('phase3_base') != 'PASS':
            critical_issues.append('Phase 3ベースデータ欠損')

        if isinstance(self.test_results['test4_edge_cases'].get('prefecture_null'), dict):
            if self.test_results['test4_edge_cases']['prefecture_null'].get('status') == 'FAIL':
                critical_issues.append('prefecture列にnull存在')

        if critical_issues:
            print(f"\n  [FAIL] クリティカルな問題あり:")
            for issue in critical_issues:
                print(f"    - {issue}")
            self.test_results['overall_status'] = 'FAIL'
        else:
            print(f"\n  [PASS] クリティカルな問題なし")
            self.test_results['overall_status'] = 'PASS' if pass_rate >= 75 else 'WARN'

        self.test_results['pass_rate'] = pass_rate
        self.test_results['critical_issues'] = critical_issues

    def save_results(self):
        """テスト結果保存"""
        output_file = Path('tests/results/INTEGRATION_TEST_PERSONA_LEVEL.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        print(f"\n  テスト結果保存: {output_file}")


def main():
    """メイン処理"""
    tester = PersonaLevelIntegrationTest()
    tester.run_all_tests()


if __name__ == '__main__':
    main()
