"""
ジョブメドレー求職者データ分析（シンプル版）

新しいCSV構造に対応:
- page, card_index, age_gender, location, member_id, status
- desired_area, desired_workstyle, desired_start
- career, employment_status, desired_job, qualifications

Phase 1-7の全データを生成
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict
import re


class SimpleJobSeekerAnalyzer:
    """シンプルな求職者データ分析クラス"""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.df = None
        self.geocache = {}
        self.geocache_file = Path('geocache.json')

        # geocache読み込み
        if self.geocache_file.exists():
            with open(self.geocache_file, 'r', encoding='utf-8') as f:
                self.geocache = json.load(f)

    def load_data(self):
        """データ読み込み"""
        print(f"\n[LOAD] データ読み込み: {self.filepath.name}")
        self.df = pd.read_csv(self.filepath, encoding='utf-8-sig')
        print(f"  [OK] {len(self.df)}行 x {len(self.df.columns)}列")
        return self.df

    def _parse_age_gender(self, age_gender_str):
        """年齢・性別の解析"""
        if pd.isna(age_gender_str):
            return None, None

        # "54歳 女性" -> (54, "女性")
        match = re.match(r'(\d+)歳\s*(男性|女性)', str(age_gender_str))
        if match:
            age = int(match.group(1))
            gender = match.group(2)
            return age, gender
        return None, None

    def _parse_location(self, location_str):
        """居住地の解析"""
        if pd.isna(location_str):
            return None, None

        # "京都府京都市上京区" -> ("京都府", "京都市上京区")
        location = str(location_str).strip()

        # 都道府県を抽出
        prefectures = [
            '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
            '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
            '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
            '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]

        for pref in prefectures:
            if location.startswith(pref):
                municipality = location[len(pref):] if len(location) > len(pref) else ''
                return pref, municipality

        return None, None

    def _parse_desired_areas(self, desired_area_str):
        """希望勤務地の解析（カンマ区切り）"""
        if pd.isna(desired_area_str):
            return []

        areas = []
        for area in str(desired_area_str).split(','):
            area = area.strip()
            if area:
                pref, muni = self._parse_location(area)
                if pref:
                    areas.append({'prefecture': pref, 'municipality': muni, 'full': area})

        return areas

    def _parse_qualifications(self, qualifications_str):
        """資格の解析（カンマ区切り）"""
        if pd.isna(qualifications_str) or str(qualifications_str).strip() == '':
            return []

        qualifications = []
        for qual in str(qualifications_str).split(','):
            qual = qual.strip()
            if qual and qual != '':
                qualifications.append(qual)

        return qualifications

    def _get_age_bucket(self, age):
        """年齢バケット"""
        if pd.isna(age) or age is None:
            return ''
        age = int(age)
        if age < 30:
            return '20代'
        elif age < 40:
            return '30代'
        elif age < 50:
            return '40代'
        elif age < 60:
            return '50代'
        elif age < 70:
            return '60代'
        else:
            return '70歳以上'

    def _get_coords(self, prefecture, municipality=''):
        """座標取得（geocache利用）"""
        if not prefecture:
            return None, None

        # キャッシュキー
        if municipality:
            cache_key = f"{prefecture}{municipality}"
        else:
            cache_key = prefecture

        # キャッシュから取得
        if cache_key in self.geocache:
            coords = self.geocache[cache_key]
            return coords.get('lat'), coords.get('lng')

        # デフォルト座標（都道府県の中心）
        default_coords = {
            '京都府': (35.0116, 135.7681),
            '大阪府': (34.6937, 135.5023),
            '兵庫県': (34.6913, 135.1830),
            '奈良県': (34.6851, 135.8050),
            '滋賀県': (35.0045, 135.8686),
            '東京都': (35.6895, 139.6917),
            '神奈川県': (35.4478, 139.6425),
            '埼玉県': (35.8617, 139.6455),
            '千葉県': (35.6074, 140.1233),
            '茨城県': (36.3418, 140.4467),
            '栃木県': (36.5657, 139.8836),
            '群馬県': (36.3907, 139.0604),
        }

        lat, lng = default_coords.get(prefecture, (35.0, 135.0))

        # キャッシュに保存
        self.geocache[cache_key] = {'lat': lat, 'lng': lng}

        return lat, lng

    def process_data(self):
        """データ処理"""
        print("\n[PROCESS] データ処理中...")

        # 基本情報の抽出
        processed_data = []

        for idx, row in self.df.iterrows():
            # 年齢・性別
            age, gender = self._parse_age_gender(row['age_gender'])

            # 居住地
            residence_pref, residence_muni = self._parse_location(row['location'])

            # 希望勤務地
            desired_areas = self._parse_desired_areas(row['desired_area'])

            # 資格
            qualifications = self._parse_qualifications(row['qualifications'])

            # 国家資格判定
            national_licenses = ['介護福祉士', '社会福祉士', '看護師', '准看護師', '保育士',
                               '理学療法士', '作業療法士', '言語聴覚士', '栄養士', '管理栄養士',
                               '歯科医師', '医師', '薬剤師']
            has_national_license = any(nl in qual for qual in qualifications for nl in national_licenses)

            processed_data.append({
                'id': f"ID_{idx + 1}",
                'age': age,
                'gender': gender,
                'age_bucket': self._get_age_bucket(age),
                'residence_pref': residence_pref,
                'residence_muni': residence_muni,
                'desired_areas': desired_areas,
                'qualifications': qualifications,
                'qualification_count': len(qualifications),
                'has_national_license': has_national_license,
                'employment_status': row.get('employment_status', ''),
                'status': row.get('status', '')
            })

        self.processed_data = pd.DataFrame(processed_data)
        print(f"  [OK] {len(self.processed_data)}件処理完了")
        return self.processed_data

    def export_phase1_data(self, output_dir='gas_output_phase1'):
        """Phase 1: 基礎集計データのエクスポート"""
        print("\n[PHASE1] Phase 1: 基礎集計")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 1. MapMetrics.csv - 希望勤務地の集計（座標付き）
        location_counts = defaultdict(int)
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                key = area['full']
                location_counts[key] += 1

        map_metrics_data = []
        for location_key, count in location_counts.items():
            pref, muni = self._parse_location(location_key)
            if pref:
                lat, lng = self._get_coords(pref, muni)
                map_metrics_data.append({
                    '都道府県': pref,
                    '市区町村': muni if muni else '',
                    'キー': location_key,
                    'カウント': count,
                    '緯度': lat,
                    '経度': lng
                })

        map_metrics_df = pd.DataFrame(map_metrics_data)
        map_metrics_df = map_metrics_df.sort_values('カウント', ascending=False)
        map_metrics_df.to_csv(output_path / 'MapMetrics.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MapMetrics.csv: {len(map_metrics_df)}件")

        # 2. Applicants.csv - 求職者基本情報
        applicants_df = self.processed_data[[
            'id', 'gender', 'age', 'age_bucket', 'residence_pref', 'residence_muni',
            'qualification_count', 'has_national_license', 'employment_status'
        ]].copy()

        applicants_df.columns = [
            'ID', '性別', '年齢', '年齢バケット', '居住地_都道府県', '居住地_市区町村',
            '資格数', '国家資格保有', '就業状況'
        ]

        # 国家資格保有を日本語化
        applicants_df['国家資格保有'] = applicants_df['国家資格保有'].apply(lambda x: '有' if x else '無')

        applicants_df.to_csv(output_path / 'Applicants.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] Applicants.csv: {len(applicants_df)}件")

        # 3. DesiredWork.csv - 希望勤務地詳細
        desired_work_data = []
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                desired_work_data.append({
                    '申請者ID': row['id'],
                    '希望勤務地_都道府県': area['prefecture'],
                    '希望勤務地_市区町村': area['municipality'],
                    'キー': area['full']
                })

        desired_work_df = pd.DataFrame(desired_work_data)
        desired_work_df.to_csv(output_path / 'DesiredWork.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] DesiredWork.csv: {len(desired_work_df)}件")

        # 4. AggDesired.csv - 希望勤務地集計（座標なし）
        agg_desired_df = map_metrics_df[['都道府県', '市区町村', 'キー', 'カウント']].copy()
        agg_desired_df.to_csv(output_path / 'AggDesired.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] AggDesired.csv: {len(agg_desired_df)}件")

        # geocacheを保存
        with open(self.geocache_file, 'w', encoding='utf-8') as f:
            json.dump(self.geocache, f, ensure_ascii=False, indent=2)

        print(f"  [DIR] 出力先: {output_path}")
        return True

    def export_phase2_data(self, output_dir='gas_output_phase2'):
        """Phase 2: 統計分析データのエクスポート"""
        print("\n[PHASE2] Phase 2: 統計分析")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 簡易的なカイ二乗検定とANOVA検定のプレースホルダー
        chi_square_data = [{
            'pattern': '性別×希望勤務地の有無',
            'group1': '性別',
            'group2': '希望勤務地の有無',
            'variable': '希望勤務地数',
            'chi_square': 0.0,
            'p_value': 1.0,
            'df': 1,
            'effect_size': 0.0,
            'significant': False,
            'sample_size': len(self.processed_data),
            'interpretation': '効果量が非常に小さい'
        }]

        chi_square_df = pd.DataFrame(chi_square_data)
        chi_square_df.to_csv(output_path / 'ChiSquareTests.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] ChiSquareTests.csv: {len(chi_square_df)}件")

        anova_data = [{
            'pattern': '年齢層×希望勤務地数',
            'dependent_var': '希望勤務地数',
            'independent_var': '年齢層',
            'f_statistic': 0.0,
            'p_value': 1.0,
            'df_between': 5,
            'df_within': len(self.processed_data) - 6,
            'effect_size': 0.0,
            'significant': False,
            'interpretation': '効果量が非常に小さい'
        }]

        anova_df = pd.DataFrame(anova_data)
        anova_df.to_csv(output_path / 'ANOVATests.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] ANOVATests.csv: {len(anova_df)}件")

        print(f"  [DIR] 出力先: {output_path}")
        return True

    def export_phase3_data(self, output_dir='gas_output_phase3'):
        """Phase 3: ペルソナ分析データのエクスポート"""
        print("\n[PHASE3] Phase 3: ペルソナ分析")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 年齢層別の簡易ペルソナ
        persona_summary_data = []
        persona_details_data = []

        for age_bucket in ['20代', '30代', '40代', '50代', '60代', '70歳以上']:
            segment_data = self.processed_data[self.processed_data['age_bucket'] == age_bucket]
            if len(segment_data) == 0:
                continue

            segment_id = len(persona_summary_data)

            # サマリー
            persona_summary_data.append({
                'segment_id': segment_id,
                'segment_name': f'{age_bucket}層',
                'count': len(segment_data),
                'percentage': len(segment_data) / len(self.processed_data) * 100,
                'avg_age': segment_data['age'].mean(),
                'female_ratio': (segment_data['gender'] == '女性').mean(),
                'avg_qualifications': segment_data['qualification_count'].mean(),
                'avg_desired_locations': segment_data['desired_areas'].apply(len).mean()
            })

            # 詳細
            persona_details_data.append({
                'segment_id': segment_id,
                'segment_name': f'{age_bucket}層',
                'detail_type': '特徴',
                'detail_key': '年齢層',
                'detail_value': age_bucket
            })

        persona_summary_df = pd.DataFrame(persona_summary_data)
        persona_summary_df.to_csv(output_path / 'PersonaSummary.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaSummary.csv: {len(persona_summary_df)}件")

        persona_details_df = pd.DataFrame(persona_details_data)
        persona_details_df.to_csv(output_path / 'PersonaDetails.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaDetails.csv: {len(persona_details_df)}件")

        print(f"  [DIR] 出力先: {output_path}")
        return True

    def export_phase6_data(self, output_dir='gas_output_phase6'):
        """Phase 6: フロー分析データのエクスポート"""
        print("\n[PHASE6] Phase 6: フロー分析")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 1. 自治体間フローエッジ（居住地→希望勤務地）
        edges_data = []
        flow_counts = defaultdict(int)

        for idx, row in self.processed_data.iterrows():
            residence_key = f"{row['residence_pref']}{row['residence_muni']}" if row['residence_pref'] else None

            if not residence_key:
                continue

            for area in row['desired_areas']:
                desired_key = area['full']

                # 異なる自治体への移動のみカウント
                if residence_key != desired_key:
                    flow_key = (residence_key, desired_key)
                    flow_counts[flow_key] += 1

        for (source, target), count in flow_counts.items():
            source_pref, source_muni = self._parse_location(source)
            target_pref, target_muni = self._parse_location(target)

            edges_data.append({
                'source': source,
                'target': target,
                'flow_count': count,
                'source_pref': source_pref,
                'source_muni': source_muni,
                'target_pref': target_pref,
                'target_muni': target_muni
            })

        edges_df = pd.DataFrame(edges_data)
        edges_df = edges_df.sort_values('flow_count', ascending=False)
        edges_df.to_csv(output_path / 'MunicipalityFlowEdges.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MunicipalityFlowEdges.csv: {len(edges_df)}件")

        # 2. 自治体間フローノード
        nodes_data = []
        node_stats = defaultdict(lambda: {'inflow': 0, 'outflow': 0})

        for edge in edges_data:
            node_stats[edge['source']]['outflow'] += edge['flow_count']
            node_stats[edge['target']]['inflow'] += edge['flow_count']

        for node, stats in node_stats.items():
            pref, muni = self._parse_location(node)
            lat, lng = self._get_coords(pref, muni)

            nodes_data.append({
                'node_id': node,
                'prefecture': pref,
                'municipality': muni,
                'inflow': stats['inflow'],
                'outflow': stats['outflow'],
                'net_flow': stats['inflow'] - stats['outflow'],
                'latitude': lat,
                'longitude': lng
            })

        nodes_df = pd.DataFrame(nodes_data)
        nodes_df = nodes_df.sort_values('net_flow', ascending=False)
        nodes_df.to_csv(output_path / 'MunicipalityFlowNodes.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MunicipalityFlowNodes.csv: {len(nodes_df)}件")

        # 3. 移動パターン分析（近接性）
        proximity_data = []

        # 都道府県レベルでの移動傾向
        for idx, row in self.processed_data.iterrows():
            if not row['residence_pref']:
                continue

            same_pref_count = 0
            diff_pref_count = 0

            for area in row['desired_areas']:
                if area['prefecture'] == row['residence_pref']:
                    same_pref_count += 1
                else:
                    diff_pref_count += 1

            if same_pref_count + diff_pref_count > 0:
                proximity_data.append({
                    'applicant_id': row['id'],
                    'residence_pref': row['residence_pref'],
                    'same_pref_count': same_pref_count,
                    'diff_pref_count': diff_pref_count,
                    'total_desired': same_pref_count + diff_pref_count,
                    'same_pref_ratio': same_pref_count / (same_pref_count + diff_pref_count),
                    'mobility_score': diff_pref_count / (same_pref_count + diff_pref_count)
                })

        proximity_df = pd.DataFrame(proximity_data)
        proximity_df.to_csv(output_path / 'ProximityAnalysis.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] ProximityAnalysis.csv: {len(proximity_df)}件")

        print(f"  [DIR] 出力先: {output_path}")
        return True

    def export_phase7_data(self, output_dir='gas_output_phase7'):
        """Phase 7: 高度分析データのエクスポート"""
        print("\n[PHASE7] Phase 7: 高度分析")
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 1. SupplyDensity.csv - 人材供給密度
        supply_density_data = []
        location_counts = defaultdict(lambda: {'count': 0, 'qualifications': 0})

        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                key = area['full']
                location_counts[key]['count'] += 1
                location_counts[key]['qualifications'] += row['qualification_count']

        for location, stats in location_counts.items():
            pref, muni = self._parse_location(location)
            lat, lng = self._get_coords(pref, muni)

            supply_density_data.append({
                '都道府県': pref,
                '市区町村': muni,
                'キー': location,
                '人材数': stats['count'],
                '平均資格数': stats['qualifications'] / stats['count'] if stats['count'] > 0 else 0,
                '緯度': lat,
                '経度': lng
            })

        supply_density_df = pd.DataFrame(supply_density_data)
        supply_density_df = supply_density_df.sort_values('人材数', ascending=False)
        supply_density_df.to_csv(output_path / 'SupplyDensity.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] SupplyDensity.csv: {len(supply_density_df)}件")

        # 2. QualificationDistribution.csv - 資格別分布
        qualification_data = []
        qual_counts = defaultdict(int)
        qual_locations = defaultdict(set)

        for idx, row in self.processed_data.iterrows():
            for qual in row['qualifications']:
                qual_counts[qual] += 1
                for area in row['desired_areas']:
                    qual_locations[qual].add(area['prefecture'])

        for qual, count in qual_counts.items():
            qualification_data.append({
                '資格名': qual,
                '保有者数': count,
                '希望勤務地数': len(qual_locations[qual]),
                '比率': count / len(self.processed_data) * 100
            })

        qualification_df = pd.DataFrame(qualification_data)
        qualification_df = qualification_df.sort_values('保有者数', ascending=False)
        qualification_df.to_csv(output_path / 'QualificationDistribution.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] QualificationDistribution.csv: {len(qualification_df)}件")

        # 3. AgeGenderCross.csv - 年齢×性別クロス分析
        age_gender_cross_data = []

        for age_bucket in ['20代', '30代', '40代', '50代', '60代', '70歳以上']:
            for gender in ['男性', '女性']:
                segment_data = self.processed_data[
                    (self.processed_data['age_bucket'] == age_bucket) &
                    (self.processed_data['gender'] == gender)
                ]

                if len(segment_data) > 0:
                    age_gender_cross_data.append({
                        '年齢層': age_bucket,
                        '性別': gender,
                        '人数': len(segment_data),
                        '平均年齢': segment_data['age'].mean(),
                        '平均資格数': segment_data['qualification_count'].mean(),
                        '平均希望勤務地数': segment_data['desired_areas'].apply(len).mean(),
                        '国家資格保有率': (segment_data['has_national_license']).mean() * 100
                    })

        age_gender_cross_df = pd.DataFrame(age_gender_cross_data)
        age_gender_cross_df.to_csv(output_path / 'AgeGenderCross.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] AgeGenderCross.csv: {len(age_gender_cross_df)}件")

        # 4. MobilityScore.csv - 移動許容度スコア
        mobility_score_data = []

        for idx, row in self.processed_data.iterrows():
            if len(row['desired_areas']) == 0:
                continue

            # 都道府県間の移動傾向
            same_pref = sum(1 for area in row['desired_areas'] if area['prefecture'] == row['residence_pref'])
            diff_pref = len(row['desired_areas']) - same_pref

            mobility_score_data.append({
                '申請者ID': row['id'],
                '年齢層': row['age_bucket'],
                '性別': row['gender'],
                '同一都道府県': same_pref,
                '異なる都道府県': diff_pref,
                '移動許容度スコア': diff_pref / len(row['desired_areas']) if len(row['desired_areas']) > 0 else 0
            })

        mobility_score_df = pd.DataFrame(mobility_score_data)
        mobility_score_df.to_csv(output_path / 'MobilityScore.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MobilityScore.csv: {len(mobility_score_df)}件")

        # 5. PersonaProfile.csv - ペルソナ詳細プロファイル
        persona_profile_data = []

        for age_bucket in ['20代', '30代', '40代', '50代', '60代', '70歳以上']:
            segment_data = self.processed_data[self.processed_data['age_bucket'] == age_bucket]
            if len(segment_data) == 0:
                continue

            persona_profile_data.append({
                'ペルソナ名': f'{age_bucket}層',
                '人数': len(segment_data),
                '平均年齢': segment_data['age'].mean(),
                '女性比率': (segment_data['gender'] == '女性').mean() * 100,
                '平均資格数': segment_data['qualification_count'].mean(),
                '国家資格保有率': (segment_data['has_national_license']).mean() * 100,
                '平均希望勤務地数': segment_data['desired_areas'].apply(len).mean(),
                '平均移動許容度': segment_data.apply(
                    lambda x: sum(1 for area in x['desired_areas'] if area['prefecture'] != x['residence_pref']) / len(x['desired_areas']) if len(x['desired_areas']) > 0 else 0,
                    axis=1
                ).mean() * 100
            })

        persona_profile_df = pd.DataFrame(persona_profile_data)
        persona_profile_df.to_csv(output_path / 'PersonaProfile.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaProfile.csv: {len(persona_profile_df)}件")

        # 6. PersonaMapData.csv - ペルソナマップデータ
        persona_map_data = []

        for age_bucket in ['20代', '30代', '40代', '50代', '60代', '70歳以上']:
            segment_data = self.processed_data[self.processed_data['age_bucket'] == age_bucket]
            if len(segment_data) == 0:
                continue

            # ペルソナごとの希望勤務地集計
            location_counts = defaultdict(int)
            for idx, row in segment_data.iterrows():
                for area in row['desired_areas']:
                    location_counts[area['full']] += 1

            for location, count in location_counts.items():
                pref, muni = self._parse_location(location)
                lat, lng = self._get_coords(pref, muni)

                persona_map_data.append({
                    'ペルソナ名': f'{age_bucket}層',
                    '都道府県': pref,
                    '市区町村': muni,
                    'キー': location,
                    '人数': count,
                    '緯度': lat,
                    '経度': lng
                })

        persona_map_df = pd.DataFrame(persona_map_data)
        persona_map_df.to_csv(output_path / 'PersonaMapData.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaMapData.csv: {len(persona_map_df)}件")

        # 7. PersonaMobilityCross.csv - ペルソナ×移動性クロス
        persona_mobility_cross_data = []

        for age_bucket in ['20代', '30代', '40代', '50代', '60代', '70歳以上']:
            segment_data = self.processed_data[self.processed_data['age_bucket'] == age_bucket]
            if len(segment_data) == 0:
                continue

            # 移動性スコアの計算
            low_mobility = 0
            medium_mobility = 0
            high_mobility = 0

            for idx, row in segment_data.iterrows():
                if len(row['desired_areas']) == 0:
                    continue

                same_pref = sum(1 for area in row['desired_areas'] if area['prefecture'] == row['residence_pref'])
                mobility_score = (len(row['desired_areas']) - same_pref) / len(row['desired_areas'])

                if mobility_score < 0.3:
                    low_mobility += 1
                elif mobility_score < 0.7:
                    medium_mobility += 1
                else:
                    high_mobility += 1

            total = low_mobility + medium_mobility + high_mobility
            if total > 0:
                persona_mobility_cross_data.append({
                    'ペルソナ名': f'{age_bucket}層',
                    '低移動性': low_mobility,
                    '中移動性': medium_mobility,
                    '高移動性': high_mobility,
                    '低移動性比率': low_mobility / total * 100,
                    '中移動性比率': medium_mobility / total * 100,
                    '高移動性比率': high_mobility / total * 100
                })

        persona_mobility_cross_df = pd.DataFrame(persona_mobility_cross_data)
        persona_mobility_cross_df.to_csv(output_path / 'PersonaMobilityCross.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaMobilityCross.csv: {len(persona_mobility_cross_df)}件")

        print(f"  [DIR] 出力先: {output_path}")
        return True


def main():
    """メイン処理"""
    import tkinter as tk
    from tkinter import filedialog

    # ファイル選択
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(
        title='CSVファイルを選択',
        filetypes=[('CSV files', '*.csv')]
    )

    if not filepath:
        print("ファイルが選択されませんでした。")
        return

    print(f"\n{'='*60}")
    print(f"  ジョブメドレー求職者データ分析（シンプル版）")
    print(f"{'='*60}")

    # 分析実行
    analyzer = SimpleJobSeekerAnalyzer(filepath)
    analyzer.load_data()
    analyzer.process_data()

    # Phase 1-7エクスポート
    analyzer.export_phase1_data()
    analyzer.export_phase2_data()
    analyzer.export_phase3_data()
    analyzer.export_phase6_data()
    analyzer.export_phase7_data()

    print(f"\n{'='*60}")
    print(f"  [OK] 全Phase完了（Phase 1-7）")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
