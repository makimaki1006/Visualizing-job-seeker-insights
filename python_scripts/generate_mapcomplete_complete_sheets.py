"""
MapComplete完全統合シート生成スクリプト

全Phaseのすべての粒度のデータを1つのCSVにまとめます。
これにより、GAS側は1シートのみ読み込めば全データを取得できます。
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict


class MapCompleteCompleteSheetGenerator:
    """MapComplete完全統合シート生成クラス"""

    def __init__(self, output_base_dir='data/output_v2'):
        self.output_base_dir = Path(output_base_dir)
        self.complete_dir = self.output_base_dir / 'mapcomplete_complete_sheets'
        self.complete_dir.mkdir(exist_ok=True)

        # 各PhaseのデータをDataFrameとして保持
        self.phase_data = {}

    def load_all_phases(self):
        """全PhaseのCSVデータを読み込む"""
        print("\n[LOAD] 全Phaseデータ読み込み開始...")

        # Phase 1
        self._load_phase('phase1', [
            'Phase1_MapMetrics.csv',
            'Phase1_Applicants.csv',
            'Phase1_DesiredWork.csv'
        ])

        # Phase 3
        self._load_phase('phase3', [
            'Phase3_PersonaSummary.csv',
            'Phase3_PersonaDetails.csv',
            'Phase3_PersonaSummaryByMunicipality.csv'
        ])

        # Phase 6
        self._load_phase('phase6', [
            'Phase6_MunicipalityFlowEdges.csv',
            'Phase6_MunicipalityFlowNodes.csv',
            'Phase6_ProximityAnalysis.csv'
        ])

        # Phase 7
        self._load_phase('phase7', [
            'Phase7_SupplyDensityMap.csv',
            'Phase7_AgeGenderCrossAnalysis.csv',
            'Phase7_DetailedPersonaProfile.csv',
            'Phase7_MobilityScore.csv'
        ])

        # Phase 8
        self._load_phase('phase8', [
            'Phase8_GraduationYearDistribution.csv',
            'Phase8_CareerDistribution.csv',
            'Phase8_CareerAgeCross.csv'  # Matrix版ではなく長形式を使用
        ])

        # カスタムデータ（新規追加）
        self._load_phase('qualification_detail', ['QualificationDetail.csv'])
        self._load_phase('desired_area_pattern', ['DesiredAreaPattern.csv'])
        self._load_phase('residence_flow', ['ResidenceFlow.csv'])
        self._load_phase('mobility_pattern', ['MobilityPattern.csv'])

        # Phase 10 (コメントアウト: URGENCY関連データは不要なため削除)
        # self._load_phase('phase10', [
        #     'Phase10_UrgencyDistribution.csv',
        #     'Phase10_UrgencyByMunicipality.csv',
        #     'Phase10_UrgencyAgeCross_ByMunicipality.csv',
        #     'Phase10_UrgencyEmploymentCross_ByMunicipality.csv'
        # ])

        # Phase 12-14 (コメントアウト: 不要なrow_type削除のため)
        # self._load_phase('phase12', ['Phase12_SupplyDemandGap.csv'])
        # self._load_phase('phase13', ['Phase13_RarityScore.csv'])
        # self._load_phase('phase14', ['Phase14_CompetitionProfile.csv'])

        print("  [OK] 全Phaseデータ読み込み完了\n")

    def _load_phase(self, phase_name, csv_files):
        """個別Phaseのデータ読み込み"""
        phase_dir = self.output_base_dir / phase_name
        self.phase_data[phase_name] = {}

        for csv_file in csv_files:
            file_path = phase_dir / csv_file
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')

                    # Phase1_MapMetricsの日本語カラム名を英語に正規化
                    if csv_file == 'Phase1_MapMetrics.csv':
                        column_mapping = {
                            '都道府県': 'prefecture',
                            '市区町村': 'municipality',
                            'キー': 'location_key',
                            'カウント': 'applicant_count',
                            '緯度': 'latitude',
                            '経度': 'longitude'
                        }
                        df = df.rename(columns=column_mapping)

                    key = csv_file.replace('.csv', '').replace(f'{phase_name.capitalize()}_', '')
                    self.phase_data[phase_name][key] = df
                    print(f"  [OK] {phase_name}/{csv_file}: {len(df)}行")
                except Exception as e:
                    print(f"  [WARN] {phase_name}/{csv_file}: 読み込みエラー - {e}")
            else:
                print(f"  [SKIP] {phase_name}/{csv_file}: ファイルなし")

    def generate_complete_sheets(self):
        """全都道府県統合シート生成（1ファイル）"""
        print("\n[GENERATE] 全都道府県統合シート生成開始...")

        # Phase1のMapMetricsから都道府県リストを取得
        map_metrics = self.phase_data.get('phase1', {}).get('MapMetrics')
        if map_metrics is None or map_metrics.empty:
            print("  [ERROR] MapMetricsが見つかりません")
            return

        # 都道府県列名の候補
        pref_cols = ['prefecture', 'residence_pref', '都道府県', '居住都道府県']
        pref_col = None
        for col in pref_cols:
            if col in map_metrics.columns:
                pref_col = col
                break

        if pref_col is None:
            print(f"  [ERROR] 都道府県列が見つかりません。利用可能な列: {list(map_metrics.columns)}")
            return

        # 都道府県リスト取得
        prefectures = map_metrics[pref_col].dropna().unique()
        print(f"  [INFO] 都道府県数: {len(prefectures)}件")

        # すべての都道府県データを1つのリストに統合
        all_rows = []
        for prefecture in prefectures:
            prefecture_rows = self._generate_prefecture_rows(prefecture, pref_col)
            all_rows.extend(prefecture_rows)
            print(f"    [OK] {prefecture}: {len(prefecture_rows)}行")

        # 1つのCSVファイルとして出力
        if len(all_rows) > 0:
            df_complete = pd.DataFrame(all_rows)
            output_file = self.complete_dir / 'MapComplete_Complete_All.csv'
            df_complete.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"\n  [OK] 全都道府県統合シート生成完了: {output_file}")
            print(f"  [INFO] 総行数: {len(df_complete)}行 × {len(df_complete.columns)}列")

            # バグ修正処理（自動適用）
            print("\n[BUGFIX] データ品質向上処理を実行中...")
            df_fixed = self._apply_bugfixes(df_complete)

            # 修正版を保存
            output_file_fixed = self.complete_dir / 'MapComplete_Complete_All_FIXED.csv'
            df_fixed.to_csv(output_file_fixed, index=False, encoding='utf-8-sig')
            print(f"  [OK] 品質向上版を保存: {output_file_fixed}")
            print(f"  [INFO] 修正後行数: {len(df_fixed)}行 × {len(df_fixed.columns)}列")
            print(f"  [INFO] 行数変化: {len(df_fixed) - len(df_complete):+d}行")
        else:
            print("  [ERROR] データが生成されませんでした")

        print(f"\n  [OK] 統合シート生成完了: {self.complete_dir}")

    def _generate_prefecture_rows(self, prefecture, pref_col):
        """単一都道府県のデータ行生成"""
        all_rows = []

        # 1. 市区町村サマリー行（Phase1基本情報）
        map_metrics = self.phase_data.get('phase1', {}).get('MapMetrics')
        if map_metrics is not None:
            pref_metrics = map_metrics[map_metrics[pref_col] == prefecture].copy()
            for _, row in pref_metrics.iterrows():
                municipality = row.get('municipality', '')
                all_rows.append({
                    'row_type': 'SUMMARY',
                    'prefecture': prefecture,
                    'municipality': municipality,
                    'category1': '',
                    'category2': '',
                    'category3': '',
                    'applicant_count': row.get('applicant_count', 0),
                    'avg_age': row.get('avg_age', None),
                    'male_count': row.get('male_count', 0),
                    'female_count': row.get('female_count', 0),
                    'avg_qualifications': row.get('avg_qualifications', None),
                    'latitude': row.get('latitude', None),
                    'longitude': row.get('longitude', None)
                })

        # 2. Phase7: 年齢層×性別クロス分析（市区町村レベル）
        age_gender = self.phase_data.get('phase7', {}).get('AgeGenderCrossAnalysis')
        if age_gender is not None and not age_gender.empty:
            # prefecture列でフィルタリング
            if 'prefecture' in age_gender.columns:
                pref_age_gender = age_gender[age_gender['prefecture'] == prefecture]
            else:
                pref_age_gender = age_gender

            for _, row in pref_age_gender.iterrows():
                # municipality列の取得（location列から都道府県名を削除）
                municipality = row.get('municipality', '')
                if not municipality and 'location' in row:
                    location = str(row['location'])
                    municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location

                # 市町村が空のレコードをスキップ（都道府県レベル集計を除外）
                if not municipality or pd.isna(municipality) or municipality == '' or municipality == prefecture:
                    continue

                all_rows.append({
                    'row_type': 'AGE_GENDER',
                    'prefecture': prefecture,
                    'municipality': municipality,
                    'category1': row.get('age_group', ''),
                    'category2': row.get('gender', ''),
                    'category3': '',
                    'count': row.get('count', 0),
                    'avg_age': row.get('avg_age', None),
                    'avg_desired_areas': row.get('avg_desired_areas', None),
                    'avg_qualifications': row.get('avg_qualifications', None),
                    'employment_rate': row.get('employment_rate', None),
                    'national_license_rate': row.get('national_license_rate', None),
                    'latitude': row.get('latitude', None),
                    'longitude': row.get('longitude', None)
                })

        # 3. Phase7: ペルソナ詳細プロファイル（市区町村レベル）
        persona_profile = self.phase_data.get('phase7', {}).get('DetailedPersonaProfile')
        if persona_profile is not None and not persona_profile.empty:
            # prefecture列でフィルタリング
            if 'prefecture' in persona_profile.columns:
                pref_persona = persona_profile[persona_profile['prefecture'] == prefecture]
            else:
                pref_persona = persona_profile

            for _, row in pref_persona.iterrows():
                # municipality列の取得（location列から都道府県名を削除）
                municipality = row.get('municipality', '')
                if not municipality and 'location' in row:
                    location = str(row['location'])
                    municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location

                all_rows.append({
                    'row_type': 'PERSONA',
                    'prefecture': prefecture,
                    'municipality': municipality,
                    'category1': row.get('persona_name', ''),
                    'category2': row.get('age_group', ''),
                    'category3': row.get('gender', ''),
                    'count': row.get('count', 0),
                    'avg_age': row.get('avg_age', None),
                    'has_national_license': row.get('national_license_rate', row.get('has_national_license', False)),
                    'avg_qualifications': row.get('avg_qualifications', None),
                    'employment_rate': row.get('employment_status', row.get('employment_rate', None)),
                    'avg_desired_areas': row.get('avg_desired_areas', None),
                    'avg_mobility_score': row.get('avg_mobility_score', None),
                    'latitude': row.get('latitude', None),
                    'longitude': row.get('longitude', None)
                })

        # 4. Phase3: ペルソナサマリー（市区町村別）
        persona_by_muni = self.phase_data.get('phase3', {}).get('PersonaSummaryByMunicipality')
        if persona_by_muni is not None and not persona_by_muni.empty:
            pref_persona = persona_by_muni[persona_by_muni['prefecture'] == prefecture] if 'prefecture' in persona_by_muni.columns else persona_by_muni
            for _, row in pref_persona.iterrows():
                # municipality列から都道府県名を削除（NaN対応、都道府県単独データは保持）
                raw_municipality = row.get('municipality', '')
                raw_municipality = str(raw_municipality) if raw_municipality and str(raw_municipality) != 'nan' else ''

                # prefecture列がない場合、都道府県名でフィルタリング
                if 'prefecture' not in persona_by_muni.columns and not raw_municipality.startswith(prefecture):
                    continue

                # 都道府県単独データはそのまま保持、それ以外は都道府県名を削除
                if raw_municipality == prefecture:
                    clean_municipality = raw_municipality
                elif raw_municipality.startswith(prefecture):
                    clean_municipality = raw_municipality.replace(prefecture, '', 1)
                else:
                    clean_municipality = raw_municipality

                all_rows.append({
                    'row_type': 'PERSONA_MUNI',
                    'prefecture': prefecture,
                    'municipality': clean_municipality,
                    'category1': row.get('persona_name', ''),
                    'category2': row.get('age_group', ''),
                    'category3': row.get('gender', ''),
                    'count': row.get('count', 0),
                    'total_in_municipality': row.get('total_in_municipality', 0),
                    'market_share_pct': row.get('market_share_pct', None)
                })

        # 4.5. Phase1: 就業ステータス×年齢×性別クロス分析（市町村別）
        # Applicants.csv + DesiredWork.csvを使用（Careerタブの「就業ステータス×年齢」グラフ用）
        # 希望勤務地（desired_prefecture/municipality）別にクロス集計
        applicants = self.phase_data.get('phase1', {}).get('Applicants')
        desired_work = self.phase_data.get('phase1', {}).get('DesiredWork')

        if applicants is not None and not applicants.empty and desired_work is not None and not desired_work.empty:
            # ApplicantsとDesiredWorkをapplicant_idで結合
            merged = pd.merge(
                applicants[['applicant_id', 'age', 'age_group', 'gender', 'employment_status',
                           'qualification_count', 'has_national_license', 'desired_area_count']],
                desired_work[['applicant_id', 'desired_prefecture', 'desired_municipality']],
                on='applicant_id',
                how='inner'
            )

            # この都道府県のデータでフィルタ
            pref_merged = merged[merged['desired_prefecture'] == prefecture]

            # この都道府県内のすべての市区町村を取得
            municipalities = pref_merged['desired_municipality'].dropna().unique()

            # 各市区町村ごとにクロス集計
            for municipality in municipalities:
                # 市区町村でフィルタ
                muni_filtered = pref_merged[pref_merged['desired_municipality'] == municipality]

                if not muni_filtered.empty:
                    # employment_status × age_group × genderでグループ化
                    grouped = muni_filtered.groupby(['employment_status', 'age_group', 'gender']).agg({
                        'applicant_id': 'count',  # 人数
                        'age': 'mean',  # 平均年齢
                        'desired_area_count': 'mean',  # 平均希望エリア数
                        'qualification_count': 'mean',  # 平均資格数
                        'has_national_license': 'mean'  # 国家資格保有率
                    }).reset_index()

                    grouped.columns = ['employment_status', 'age_group', 'gender', 'count',
                                      'avg_age', 'avg_desired_areas', 'avg_qualifications', 'national_license_rate']

                    # EMPLOYMENT_AGE_CROSSとして追加
                    for _, row in grouped.iterrows():
                        all_rows.append({
                            'row_type': 'EMPLOYMENT_AGE_CROSS',
                            'prefecture': prefecture,
                            'municipality': municipality,
                            'category1': row['employment_status'],  # 就業中、離職中、在学中
                            'category2': row['age_group'],          # 20代、30代、等
                            'category3': row['gender'],             # 男性、女性
                            'count': row['count'],
                            'avg_age': row['avg_age'],
                            'avg_desired_areas': row['avg_desired_areas'],
                            'avg_qualifications': row['avg_qualifications'],
                            'national_license_rate': row['national_license_rate'],
                            'avg_mobility_score': None  # Phase1データには含まれない
                        })

        # 5. Phase8: キャリアクロス分析（市区町村レベル）
        # CareerAgeCross.csv（長形式）を使用（Matrix版はピボットテーブルでprefecture列なし）
        career_cross = self.phase_data.get('phase8', {}).get('CareerAgeCross')
        if career_cross is not None and not career_cross.empty:
            # prefecture列でフィルタリング
            if 'prefecture' in career_cross.columns:
                pref_career = career_cross[career_cross['prefecture'] == prefecture]
            else:
                pref_career = career_cross

            for _, row in pref_career.iterrows():
                # municipality列を直接取得（既に正規化済み）
                municipality = row.get('municipality', '')

                all_rows.append({
                    'row_type': 'CAREER_CROSS',
                    'prefecture': prefecture,
                    'municipality': municipality,
                    'category1': row.get('career', ''),
                    'category2': row.get('age_group', ''),
                    'category3': '',
                    'count': row.get('count', 0),
                    'avg_age': row.get('avg_age', None),
                    'avg_qualifications': row.get('avg_qualifications', None),
                    'latitude': row.get('latitude', None),
                    'longitude': row.get('longitude', None)
                })

        # 6. Phase10: 緊急度×年齢クロス分析（市区町村レベル）
        # ※コメントアウト: URGENCY_AGEは不要なrow_typeのため削除
        # urgency_age = self.phase_data.get('phase10', {}).get('UrgencyAgeCross_ByMunicipality')
        # if urgency_age is not None and not urgency_age.empty:
        #     # location列から都道府県フィルタリング
        #     for _, row in urgency_age.iterrows():
        #         location = str(row.get('location', ''))
        #         if not location.startswith(prefecture):
        #             continue  # この都道府県のデータではない
        #
        #         # municipality列の取得（location列から都道府県名を削除）
        #         municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location
        #
        #         all_rows.append({
        #             'row_type': 'URGENCY_AGE',
        #             'prefecture': prefecture,
        #             'municipality': municipality,
        #             'category1': '',
        #             'category2': row.get('age_group', ''),
        #             'category3': '',
        #             'count': row.get('count', 0),
        #             'avg_urgency_score': row.get('avg_urgency_score', None),
        #             'latitude': row.get('latitude', None),
        #             'longitude': row.get('longitude', None)
        #         })

        # 7. Phase10: 緊急度×就業状況クロス分析（市区町村レベル）
        # ※コメントアウト: URGENCY_EMPLOYMENTは不要なrow_typeのため削除
        # urgency_employment = self.phase_data.get('phase10', {}).get('UrgencyEmploymentCross_ByMunicipality')
        # if urgency_employment is not None and not urgency_employment.empty:
        #     # location列から都道府県フィルタリング
        #     for _, row in urgency_employment.iterrows():
        #         location = str(row.get('location', ''))
        #         if not location.startswith(prefecture):
        #             continue  # この都道府県のデータではない
        #
        #         # municipality列の取得（location列から都道府県名を削除）
        #         municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location
        #
        #         all_rows.append({
        #             'row_type': 'URGENCY_EMPLOYMENT',
        #             'prefecture': prefecture,
        #             'municipality': municipality,
        #             'category1': '',
        #             'category2': row.get('employment_status', ''),
        #             'category3': '',
        #             'count': row.get('count', 0),
        #             'avg_urgency_score': row.get('avg_urgency_score', None),
        #             'latitude': row.get('latitude', None),
        #             'longitude': row.get('longitude', None)
        #         })

        # 7. Phase6: フロー分析（市区町村別）
        # ※コメントアウト: FLOWは不要なrow_typeのため削除
        # flow_nodes = self.phase_data.get('phase6', {}).get('MunicipalityFlowNodes')
        # if flow_nodes is not None and not flow_nodes.empty:
        #     if 'prefecture' in flow_nodes.columns:
        #         pref_flow = flow_nodes[flow_nodes['prefecture'] == prefecture].copy()
        #         for _, row in pref_flow.iterrows():
        #             # municipality列から都道府県名を削除（NaN対応、都道府県単独データは保持）
        #             raw_municipality = row.get('municipality', '')
        #             raw_municipality = str(raw_municipality) if raw_municipality and str(raw_municipality) != 'nan' else ''
        #
        #             # 都道府県単独データはそのまま保持、それ以外は都道府県名を削除
        #             if raw_municipality == prefecture:
        #                 clean_municipality = raw_municipality
        #             elif raw_municipality.startswith(prefecture):
        #                 clean_municipality = raw_municipality.replace(prefecture, '', 1)
        #             else:
        #                 clean_municipality = raw_municipality
        #
        #             all_rows.append({
        #                 'row_type': 'FLOW',
        #                 'prefecture': prefecture,
        #                 'municipality': clean_municipality,
        #                 'category1': '',
        #                 'category2': '',
        #                 'category3': '',
        #                 'inflow': row.get('inflow', 0),
        #                 'outflow': row.get('outflow', 0),
        #                 'net_flow': row.get('net_flow', 0),
        #                 'applicant_count': row.get('applicant_count', 0)
        #             })

        # 8. Phase12: 需給ギャップ分析
        # ※コメントアウト: GAPは不要なrow_typeのため削除（Phase12全体削除に伴う）
        # supply_demand_gap = self.phase_data.get('phase12', {}).get('SupplyDemandGap')
        # if supply_demand_gap is not None and not supply_demand_gap.empty:
        #     # prefecture列でフィルタリング
        #     if 'prefecture' in supply_demand_gap.columns:
        #         pref_gap = supply_demand_gap[supply_demand_gap['prefecture'] == prefecture]
        #     else:
        #         pref_gap = supply_demand_gap
        #
        #     for _, row in pref_gap.iterrows():
        #         # municipality列の取得（location列から都道府県名を削除）
        #         municipality = row.get('municipality', '')
        #         if not municipality and 'location' in row:
        #             location = str(row['location'])
        #             municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location
        #
        #         all_rows.append({
        #             'row_type': 'GAP',
        #             'prefecture': prefecture,
        #             'municipality': municipality,
        #             'category1': '',
        #             'category2': '',
        #             'category3': '',
        #             'demand_count': row.get('demand_count', 0),
        #             'supply_count': row.get('supply_count', 0),
        #             'gap': row.get('gap', 0),
        #             'demand_supply_ratio': row.get('demand_supply_ratio', None),
        #             'latitude': row.get('latitude', None),
        #             'longitude': row.get('longitude', None)
        #         })

        # 9. Phase13: 希少人材スコア
        # ※コメントアウト: RARITYは不要なrow_typeのため削除
        # rarity_score = self.phase_data.get('phase13', {}).get('RarityScore')
        # if rarity_score is not None and not rarity_score.empty:
        #     # prefecture列でフィルタリング
        #     if 'prefecture' in rarity_score.columns:
        #         pref_rarity = rarity_score[rarity_score['prefecture'] == prefecture]
        #     else:
        #         pref_rarity = rarity_score
        #
        #     for _, row in pref_rarity.iterrows():
        #         # municipality列の取得（location列から都道府県名を削除）
        #         municipality = row.get('municipality', '')
        #         if not municipality and 'location' in row:
        #             location = str(row['location'])
        #             municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location
        #
        #         all_rows.append({
        #             'row_type': 'RARITY',
        #             'prefecture': prefecture,
        #             'municipality': municipality,
        #             'category1': row.get('age_bucket', ''),
        #             'category2': row.get('gender', ''),
        #             'category3': row.get('rarity_rank', ''),
        #             'count': row.get('count', 0),
        #             'rarity_score': row.get('rarity_score', None),
        #             'has_national_license': row.get('has_national_license', False),
        #             'latitude': row.get('latitude', None),
        #             'longitude': row.get('longitude', None)
        #         })

        # 10. Phase14: 競争プロファイル
        # ※コメントアウト: COMPETITIONは不要なrow_typeのため削除
        # competition_profile = self.phase_data.get('phase14', {}).get('CompetitionProfile')
        # if competition_profile is not None and not competition_profile.empty:
        #     # prefecture列でフィルタリング
        #     if 'prefecture' in competition_profile.columns:
        #         pref_comp = competition_profile[competition_profile['prefecture'] == prefecture]
        #     else:
        #         pref_comp = competition_profile
        #
        #     for _, row in pref_comp.iterrows():
        #         # municipality列の取得（location列から都道府県名を削除）
        #         municipality = row.get('municipality', '')
        #         if not municipality and 'location' in row:
        #             location = str(row['location'])
        #             municipality = location.replace(prefecture, '', 1) if location.startswith(prefecture) else location
        #
        #         all_rows.append({
        #             'row_type': 'COMPETITION',
        #             'prefecture': prefecture,
        #             'municipality': municipality,
        #             'category1': row.get('top_age_group', ''),
        #             'category2': row.get('top_employment_status', ''),
        #             'category3': '',
        #             'total_applicants': row.get('total_applicants', 0),
        #             'top_age_ratio': row.get('top_age_ratio', None),
        #             'female_ratio': row.get('female_ratio', None),
        #             'male_ratio': row.get('male_ratio', None),
        #             'national_license_rate': row.get('national_license_rate', None),
        #             'top_employment_ratio': row.get('top_employment_ratio', None),
        #             'avg_qualification_count': row.get('avg_qualification_count', None),
        #             'latitude': row.get('latitude', None),
        #             'longitude': row.get('longitude', None)
        #         })

        # 11. QUALIFICATION_DETAIL（資格詳細）
        qual_detail = self.phase_data.get('qualification_detail', {}).get('QualificationDetail')
        if qual_detail is not None and not qual_detail.empty:
            pref_qual = qual_detail[qual_detail['prefecture'] == prefecture]
            for _, row in pref_qual.iterrows():
                all_rows.append({
                    'row_type': 'QUALIFICATION_DETAIL',
                    'prefecture': prefecture,
                    'municipality': row.get('municipality', ''),
                    'category1': row.get('qualification_name', ''),
                    'category2': row.get('age_group', ''),
                    'category3': row.get('gender', ''),
                    'count': row.get('count', 0),
                    'is_national_license': row.get('is_national_license', False),
                    'employment_status': row.get('employment_status', '')
                })

        # 12. DESIRED_AREA_PATTERN（併願パターン）
        area_pattern = self.phase_data.get('desired_area_pattern', {}).get('DesiredAreaPattern')
        if area_pattern is not None and not area_pattern.empty:
            pref_pattern = area_pattern[area_pattern['prefecture'] == prefecture]
            for _, row in pref_pattern.iterrows():
                all_rows.append({
                    'row_type': 'DESIRED_AREA_PATTERN',
                    'prefecture': prefecture,
                    'municipality': row.get('municipality', ''),
                    'category1': row.get('age_group', ''),
                    'category2': row.get('gender', ''),
                    'category3': '',
                    'count': row.get('count', 0),
                    'co_desired_prefecture': row.get('co_desired_prefecture', ''),
                    'co_desired_municipality': row.get('co_desired_municipality', '')
                })

        # 13. RESIDENCE_FLOW（居住地→希望地フロー）
        residence_flow = self.phase_data.get('residence_flow', {}).get('ResidenceFlow')
        if residence_flow is not None and not residence_flow.empty:
            pref_flow = residence_flow[residence_flow['residence_prefecture'] == prefecture]
            for _, row in pref_flow.iterrows():
                all_rows.append({
                    'row_type': 'RESIDENCE_FLOW',
                    'prefecture': prefecture,
                    'municipality': row.get('residence_municipality', ''),
                    'category1': row.get('age_group', ''),
                    'category2': row.get('gender', ''),
                    'category3': '',
                    'count': row.get('count', 0),
                    'desired_prefecture': row.get('desired_prefecture', ''),
                    'desired_municipality': row.get('desired_municipality', '')
                })

        # 14. MOBILITY_PATTERN（移動パターン）
        mobility_pattern = self.phase_data.get('mobility_pattern', {}).get('MobilityPattern')
        if mobility_pattern is not None and not mobility_pattern.empty:
            pref_mobility = mobility_pattern[mobility_pattern['residence_prefecture'] == prefecture]
            for _, row in pref_mobility.iterrows():
                all_rows.append({
                    'row_type': 'MOBILITY_PATTERN',
                    'prefecture': prefecture,
                    'municipality': row.get('residence_municipality', ''),
                    'category1': row.get('age_group', ''),
                    'category2': row.get('gender', ''),
                    'category3': row.get('employment_status', ''),
                    'count': row.get('count', 0),
                    'desired_prefecture': row.get('desired_prefecture', ''),
                    'desired_municipality': row.get('desired_municipality', ''),
                    'mobility_type': row.get('mobility_type', ''),
                    'avg_reference_distance_km': row.get('avg_reference_distance_km', None)
                })

        # データ行をリストで返す
        return all_rows


    def _apply_bugfixes(self, df):
        """
        データ品質向上処理（バグ修正）

        修正項目:
        - BUG 1: PERSONA重複削除（全都道府県に複製されているものを1都道府県のみに）
        - BUG 2: AGE_GENDER NaN municipality処理（空文字列に変換）
        - BUG 3: GAP欠落都道府県追加（Phase12ソースから追加）
        - BUG 4: RARITY重複削除
        - BUG 6: GAP計算不整合修正（gap = demand_count - supply_count）

        注意: BUG 5（gap列負の値クリップ）は削除（仕様として正しいため）
        """
        print("  [1/5] PERSONA重複削除...")
        persona_rows = df[df['row_type'] == 'PERSONA']
        if len(persona_rows) > 0:
            first_pref = persona_rows['prefecture'].iloc[0]
            df = pd.concat([
                df[df['row_type'] != 'PERSONA'],
                persona_rows[persona_rows['prefecture'] == first_pref]
            ])
            print(f"    修正: {len(persona_rows)}行 → {len(df[df['row_type'] == 'PERSONA'])}行（{first_pref}のみ）")

        print("  [2/5] AGE_GENDER NaN municipality処理...")
        age_gender_nan = df[(df['row_type'] == 'AGE_GENDER') & (df['municipality'].isna())]
        if len(age_gender_nan) > 0:
            df.loc[(df['row_type'] == 'AGE_GENDER') & (df['municipality'].isna()), 'municipality'] = ''
            print(f"    修正: {len(age_gender_nan)}行のNaN municipalityを空文字列に変換")
        else:
            print(f"    スキップ: NaN municipalityなし")

        print("  [3/5] GAP欠落都道府県追加...")
        print("    スキップ: GAPは削除済みのため処理不要")
        # gap_prefs = df[df['row_type'] == 'GAP']['prefecture'].unique()
        # gap_source_path = self.output_base_dir / 'phase12' / 'Phase12_SupplyDemandGap.csv'
        #
        # if gap_source_path.exists():
        #     gap_source = pd.read_csv(gap_source_path, encoding='utf-8-sig')
        #     gap_source_prefs = gap_source['prefecture'].unique()
        #     missing_prefs = set(gap_source_prefs) - set(gap_prefs)
        #
        #     if missing_prefs:
        #         print(f"    追加: {len(missing_prefs)}都道府県（{', '.join(missing_prefs)}）")
        #         for pref in missing_prefs:
        #             pref_data = gap_source[gap_source['prefecture'] == pref]
        #             for _, row in pref_data.iterrows():
        #                 df = pd.concat([df, pd.DataFrame([{
        #                     'row_type': 'GAP',
        #                     'prefecture': pref,
        #                     'municipality': row.get('municipality', ''),
        #                     'category1': '',
        #                     'category2': '',
        #                     'category3': '',
        #                     'demand_count': row.get('demand_count', 0),
        #                     'supply_count': row.get('supply_count', 0),
        #                     'gap': row.get('gap', 0),
        #                     'demand_supply_ratio': row.get('demand_supply_ratio', None),
        #                     'latitude': row.get('latitude', None),
        #                     'longitude': row.get('longitude', None)
        #                 }])], ignore_index=True)
        #     else:
        #         print(f"    スキップ: すべての都道府県が存在")
        # else:
        #     print(f"    スキップ: Phase12ソースファイルなし")

        print("  [4/5] RARITY重複削除...")
        print("    スキップ: RARITYは削除済みのため処理不要")
        # rarity_before = len(df[df['row_type'] == 'RARITY'])
        # df = df.drop_duplicates(
        #     subset=['row_type', 'prefecture', 'municipality', 'category1', 'category2'],
        #     keep='first'
        # )
        # rarity_after = len(df[df['row_type'] == 'RARITY'])
        # print(f"    修正: {rarity_before}行 → {rarity_after}行（削除: {rarity_before - rarity_after}行）")

        print("  [5/5] GAP計算不整合修正...")
        print("    スキップ: GAPは削除済みのため処理不要")
        # gap_rows = df[df['row_type'] == 'GAP'].copy()
        # gap_rows['calculated_gap'] = gap_rows['demand_count'] - gap_rows['supply_count']
        # gap_rows['gap_diff'] = abs(gap_rows['gap'] - gap_rows['calculated_gap'])
        # mismatches_before = len(gap_rows[gap_rows['gap_diff'] > 0.01])
        #
        # if mismatches_before > 0:
        #     df.loc[df['row_type'] == 'GAP', 'gap'] = (
        #         df.loc[df['row_type'] == 'GAP', 'demand_count'] -
        #         df.loc[df['row_type'] == 'GAP', 'supply_count']
        #     )
        #     print(f"    修正: {mismatches_before}行の不整合を修正（gap = demand_count - supply_count）")
        # else:
        #     print(f"    スキップ: 不整合なし")

        print("  [OK] データ品質向上処理完了")
        return df


def main():
    """メイン処理"""
    print(f"\n{'='*60}")
    print(f"  MapComplete完全統合シート生成")
    print(f"{'='*60}")

    generator = MapCompleteCompleteSheetGenerator()
    generator.load_all_phases()
    generator.generate_complete_sheets()

    print(f"\n{'='*60}")
    print(f"  [OK] 処理完了")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
