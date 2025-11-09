#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 7: 高度分析機能拡張
Advanced Analysis Features - Phase 7

実装機能:
1. 人材供給密度マップ (Supply Density Map)
2. 資格別人材分布分析 (Qualification Distribution Analysis)
3. 年齢層×性別クロス分析 (Age-Gender Cross Analysis)
4. 移動許容度スコアリング (Mobility Score)
5. ペルソナ詳細プロファイル (Detailed Persona Profile)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
from scipy.spatial.distance import cdist
import json

class Phase7AdvancedAnalyzer:
    """Phase 7: 高度分析機能"""

    def __init__(self, df, df_processed, geocache, master):
        """
        初期化

        Args:
            df: 元データフレーム
            df_processed: 処理済みデータフレーム
            geocache: 座標キャッシュ辞書
            master: マスターデータインスタンス
        """
        self.df = df
        self.df_processed = df_processed
        self.geocache = geocache
        self.master = master
        self.results = {}

    def run_all_analysis(self):
        """全分析実行"""
        print("\n" + "=" * 60)
        print("Phase 7: 高度分析実行")
        print("=" * 60)

        # 1. 人材供給密度マップ
        print("\n[機能1] 人材供給密度マップ生成中...")
        self.results['supply_density'] = self._analyze_supply_density()
        print(f"  [OK] 完了: {len(self.results['supply_density'])}地域分析")

        # 2. 資格別人材分布
        print("\n[機能2] 資格別人材分布分析中...")
        self.results['qualification_dist'] = self._analyze_qualification_distribution()
        print(f"  [OK] 完了: {len(self.results['qualification_dist'])}資格カテゴリ分析")

        # 3. 年齢層×性別クロス分析
        print("\n[機能3] 年齢層×性別クロス分析中...")
        self.results['age_gender_cross'] = self._analyze_age_gender_cross()
        print(f"  [OK] 完了: {len(self.results['age_gender_cross'])}地域分析")

        # 4. 移動許容度スコアリング
        print("\n[機能4] 移動許容度スコアリング中...")
        self.results['mobility_score'] = self._calculate_mobility_score()
        print(f"  [OK] 完了: {len(self.results['mobility_score'])}名分析")

        # 5. ペルソナ詳細プロファイル
        print("\n[機能5] ペルソナ詳細プロファイル生成中...")
        self.results['detailed_persona'] = self._generate_detailed_persona_profile()
        print(f"  [OK] 完了: {len(self.results['detailed_persona'])}ペルソナ分析")

        print("\n" + "=" * 60)
        print("Phase 7: 全分析完了")
        print("=" * 60)

        return self.results

    def _analyze_supply_density(self):
        """
        機能1: 人材供給密度マップ生成

        地域ごとの求職者密度・資格保有率・年齢構成・緊急度を総合評価
        """
        # データ件数が動的であることを考慮
        if len(self.df_processed) == 0:
            return pd.DataFrame()

        # 市区町村キーで集計（希望勤務地ベース）
        location_col = None
        for col in ['希望勤務地_キー', 'キー', '市区町村キー', 'primary_desired_location', 'residence_muni']:
            if col in self.df_processed.columns:
                location_col = col
                break

        if not location_col:
            print("  警告: 地域キーカラムが見つかりません")
            return pd.DataFrame()

        # 地域ごとの集計
        density_data = []

        for location in self.df_processed[location_col].unique():
            if pd.isna(location):
                continue

            loc_df = self.df_processed[self.df_processed[location_col] == location]

            # 求職者密度（人数）
            applicant_count = len(loc_df)

            # 資格保有率
            qual_col = None
            for col in ['資格数', 'qualifications_count', 'qualification_count']:
                if col in loc_df.columns:
                    qual_col = col
                    break

            if qual_col:
                qualified_rate = (loc_df[qual_col] > 0).mean()
            else:
                qualified_rate = 0.0

            # 平均年齢
            age_col = None
            for col in ['年齢', 'age']:
                if col in loc_df.columns:
                    age_col = col
                    break

            avg_age = loc_df[age_col].mean() if age_col else 0.0

            # 緊急度（今すぐ・1ヶ月以内の割合）
            urgency_col = None
            for col in ['希望入職時期', 'desired_start_timing']:
                if col in loc_df.columns:
                    urgency_col = col
                    break

            if urgency_col:
                urgent_conditions = ['今すぐに', '1ヶ月以内', '1', '2']
                urgency_rate = loc_df[urgency_col].isin(urgent_conditions).mean()
            else:
                urgency_rate = 0.0

            # 総合スコア算出（重み付け）
            # 人数×0.4 + 資格保有率×30 + 緊急度×20
            composite_score = (
                applicant_count * 0.4 +
                qualified_rate * 30 +
                urgency_rate * 20
            )

            # ランク付け
            if composite_score >= 50:
                rank = 'S'
            elif composite_score >= 30:
                rank = 'A'
            elif composite_score >= 15:
                rank = 'B'
            elif composite_score >= 5:
                rank = 'C'
            else:
                rank = 'D'

            density_data.append({
                '市区町村': location,
                '求職者数': applicant_count,
                '資格保有率': round(qualified_rate, 3),
                '平均年齢': round(avg_age, 1),
                '緊急度': round(urgency_rate, 3),
                '総合スコア': round(composite_score, 2),
                'ランク': rank
            })

        result_df = pd.DataFrame(density_data)

        # 降順ソート
        if len(result_df) > 0:
            result_df = result_df.sort_values('総合スコア', ascending=False)

        return result_df

    def _analyze_qualification_distribution(self):
        """
        機能2: 資格別人材分布分析

        主要資格カテゴリごとの地域分布を分析
        """
        if len(self.df_processed) == 0:
            return pd.DataFrame()

        # 資格情報カラムを特定
        qual_info_col = None
        for col in ['資格情報', 'qualifications', 'qualification_info', 'qualifications_list', 'qualification_categories']:
            if col in self.df_processed.columns:
                qual_info_col = col
                break

        if not qual_info_col:
            print("  警告: 資格情報カラムが見つかりません")
            print(f"  利用可能な列: {list(self.df_processed.columns)}")
            return pd.DataFrame()

        # 地域カラムを特定
        location_col = None
        for col in ['希望勤務地_市区町村', '市区町村', 'location', 'primary_desired_location', 'residence_muni']:
            if col in self.df_processed.columns:
                location_col = col
                break

        if not location_col:
            print("  警告: 地域カラムが見つかりません")
            return pd.DataFrame()

        qual_dist_data = []

        # 主要資格カテゴリ
        for category, qualifications in self.master.QUALIFICATIONS.items():
            # この資格カテゴリを持つ求職者
            def has_qualification(x):
                """資格保有チェック（list型対応）"""
                # list型の場合
                if isinstance(x, list):
                    if len(x) == 0:
                        return False
                    return any(q in x for q in qualifications)
                # NaN/None の場合
                elif x is None or (isinstance(x, float) and pd.isna(x)):
                    return False
                # 文字列型の場合
                else:
                    return any(q in str(x) for q in qualifications)

            mask = self.df_processed[qual_info_col].apply(has_qualification)
            qualified_df = self.df_processed[mask]

            if len(qualified_df) == 0:
                continue

            # 地域別カウント
            distribution = qualified_df[location_col].value_counts()

            # トップ3地域
            top3 = distribution.head(3).to_dict()
            top3_str = '; '.join([f"{k}({v}名)" for k, v in top3.items()])

            # 全求職者に対する割合
            total_by_region = self.df_processed[location_col].value_counts()

            # 希少地域（保有率が低い地域）
            penetration = distribution / total_by_region
            rare_regions = penetration.nsmallest(min(3, len(penetration))).to_dict()
            rare_str = '; '.join([f"{k}({v:.1%})" for k, v in rare_regions.items()])

            qual_dist_data.append({
                '資格カテゴリ': category,
                '総保有者数': len(qualified_df),
                '分布TOP3': top3_str,
                '希少地域TOP3': rare_str
            })

        result_df = pd.DataFrame(qual_dist_data)

        # 保有者数でソート
        if len(result_df) > 0:
            result_df = result_df.sort_values('総保有者数', ascending=False)

        return result_df

    def _analyze_age_gender_cross(self):
        """
        機能3: 年齢層×性別クロス分析

        地域ごとの年齢層・性別構成を分析
        """
        if len(self.df_processed) == 0:
            return pd.DataFrame()

        # 必要なカラムを特定
        age_col = None
        for col in ['年齢', 'age']:
            if col in self.df_processed.columns:
                age_col = col
                break

        gender_col = None
        for col in ['性別', 'gender']:
            if col in self.df_processed.columns:
                gender_col = col
                break

        location_col = None
        for col in ['希望勤務地_市区町村', '市区町村', 'location', 'primary_desired_location', 'residence_muni']:
            if col in self.df_processed.columns:
                location_col = col
                break

        if not all([age_col, gender_col, location_col]):
            print("  警告: 必要なカラムが不足しています")
            return pd.DataFrame()

        # 年齢層分類
        df_temp = self.df_processed.copy()
        df_temp['年齢層'] = pd.cut(
            df_temp[age_col],
            bins=[0, 30, 45, 60, 100],
            labels=['若年層', '中年層', '準高齢層', '高齢層']
        )

        cross_data = []

        for location in df_temp[location_col].unique():
            if pd.isna(location):
                continue

            loc_df = df_temp[df_temp[location_col] == location]

            if len(loc_df) == 0:
                continue

            # 年齢層×性別のクロス集計
            cross_tab = pd.crosstab(
                loc_df['年齢層'],
                loc_df[gender_col],
                margins=False
            )

            # 支配的セグメント（最多の組み合わせ）
            age_gender_counts = loc_df.groupby(['年齢層', gender_col]).size()
            if len(age_gender_counts) > 0:
                dominant_segment = age_gender_counts.idxmax()
                dominant_str = f"{dominant_segment[0]}-{dominant_segment[1]}"
            else:
                dominant_str = "不明"

            # ダイバーシティスコア（ハーフィンダール指数の逆数）
            total = len(loc_df)
            proportions = age_gender_counts / total
            hhi = (proportions ** 2).sum()
            diversity_score = 1 - hhi if hhi < 1 else 0

            # 各セグメントの比率
            female_mask = loc_df[gender_col].str.contains('女', na=False)
            young_mask = loc_df['年齢層'] == '若年層'
            middle_mask = loc_df['年齢層'] == '中年層'

            young_female_rate = (young_mask & female_mask).sum() / total if total > 0 else 0
            middle_female_rate = (middle_mask & female_mask).sum() / total if total > 0 else 0

            cross_data.append({
                '市区町村': location,
                '総求職者数': total,
                '支配的セグメント': dominant_str,
                '若年女性比率': round(young_female_rate, 3),
                '中年女性比率': round(middle_female_rate, 3),
                'ダイバーシティスコア': round(diversity_score, 3)
            })

        result_df = pd.DataFrame(cross_data)

        # 求職者数でソート
        if len(result_df) > 0:
            result_df = result_df.sort_values('総求職者数', ascending=False)

        return result_df

    def _calculate_mobility_score(self):
        """
        機能4: 移動許容度スコアリング

        求職者ごとの移動許容度を定量化
        区レベルデータ（高精度）または市レベルデータ（低精度）を使用
        """
        if len(self.df_processed) == 0:
            return pd.DataFrame()

        # 申請者IDカラムを特定
        id_col = None
        for col in ['申請者ID', 'applicant_id', 'ID', 'id']:
            if col in self.df_processed.columns:
                id_col = col
                break

        if not id_col:
            print("  警告: 申請者IDカラムが見つかりません")
            return pd.DataFrame()

        # 区レベルデータの優先使用
        use_detailed = 'desired_locations_keys' in self.df_processed.columns

        if use_detailed:
            print("  [INFO] 区レベルデータ使用（高精度モード）")
        else:
            print("  [WARNING] 市レベルデータ使用（低精度モード）")

        mobility_data = []
        missing_coords_count = 0

        for applicant_id in self.df_processed[id_col].unique():
            if pd.isna(applicant_id):
                continue

            # この申請者のデータ
            applicant_row = self.df_processed[self.df_processed[id_col] == applicant_id].iloc[0]

            # 希望勤務地を取得
            if use_detailed and isinstance(applicant_row.get('desired_locations_keys'), list):
                # 高精度モード: 区レベルデータ使用
                locations = applicant_row['desired_locations_keys']
            else:
                # 低精度モード: 元データ使用
                location_col = None
                for col in ['希望勤務地_キー', 'キー', '市区町村キー', 'primary_desired_location', 'residence_muni']:
                    if col in self.df_processed.columns:
                        location_col = col
                        break

                if location_col:
                    locations = [applicant_row[location_col]]
                else:
                    locations = []

            # 座標データを取得
            coords = []
            missing_keys = []
            for loc in locations:
                if loc in self.geocache:
                    coords.append([
                        self.geocache[loc]['lat'],
                        self.geocache[loc]['lng']
                    ])
                else:
                    missing_keys.append(loc)

            if missing_keys:
                missing_coords_count += 1

            # 移動距離計算
            if len(coords) > 1:
                # 座標の広がり（標準偏差）
                coords_array = np.array(coords)
                spread = np.std(coords_array, axis=0).mean()

                # 最大移動距離（ハバースイン距離）
                distances = cdist(coords_array, coords_array, metric='euclidean')
                max_distance_deg = distances.max()
                # 緯度1度≈111km として概算
                max_distance_km = max_distance_deg * 111
            else:
                spread = 0
                max_distance_km = 0

            # 移動許容度スコア（0-100）
            score = min(100, spread * 50 + max_distance_km * 0.3)

            # レベル分類
            if score >= 70:
                level = 'A'
                level_name = '広域移動OK'
            elif score >= 40:
                level = 'B'
                level_name = '中距離OK'
            elif score >= 10:
                level = 'C'
                level_name = '近距離のみ'
            else:
                level = 'D'
                level_name = '地元限定'

            # 居住地を取得
            residence_col = None
            for col in ['居住地_市区町村', '居住地', 'residence', 'residence_muni', 'residence_raw']:
                if col in self.df_processed.columns:
                    residence_col = col
                    break

            residence = applicant_row[residence_col] if residence_col else '不明'

            mobility_data.append({
                '申請者ID': applicant_id,
                '希望地数': len(locations),
                '最大移動距離km': round(max_distance_km, 1),
                '移動許容度スコア': round(score, 1),
                '移動許容度レベル': level,
                '移動許容度': level_name,
                '居住地': residence
            })

        if missing_coords_count > 0:
            print(f"  [WARNING] 座標が見つからない申請者: {missing_coords_count}名")

        result_df = pd.DataFrame(mobility_data)

        # スコア順でソート
        if len(result_df) > 0:
            result_df = result_df.sort_values('移動許容度スコア', ascending=False)

        return result_df

    def _generate_detailed_persona_profile(self):
        """
        機能5: ペルソナ詳細プロファイル生成

        既存ペルソナを詳細化
        """
        if len(self.df_processed) == 0:
            return pd.DataFrame()

        # セグメントIDカラムを特定
        segment_col = None
        for col in ['segment_id', 'cluster', 'persona_id']:
            if col in self.df_processed.columns:
                segment_col = col
                break

        if not segment_col:
            print("  警告: セグメントIDカラムが見つかりません")
            return pd.DataFrame()

        # セグメント名カラムを特定
        segment_name_col = None
        for col in ['segment_name', 'persona_name', 'cluster_name']:
            if col in self.df_processed.columns:
                segment_name_col = col
                break

        persona_profiles = []

        for segment_id in self.df_processed[segment_col].unique():
            if pd.isna(segment_id) or segment_id == -1:
                continue

            segment_df = self.df_processed[self.df_processed[segment_col] == segment_id]

            if len(segment_df) == 0:
                continue

            # ペルソナ名
            if segment_name_col:
                persona_name = segment_df[segment_name_col].iloc[0]
            else:
                persona_name = f"セグメント{segment_id}"

            # 基本統計
            count = len(segment_df)

            # 年齢
            age_col = None
            for col in ['年齢', 'age']:
                if col in segment_df.columns:
                    age_col = col
                    break
            avg_age = segment_df[age_col].mean() if age_col else 0

            # 性別比率
            gender_col = None
            for col in ['性別', 'gender']:
                if col in segment_df.columns:
                    gender_col = col
                    break

            if gender_col:
                female_count = segment_df[gender_col].str.contains('女', na=False).sum()
                female_ratio = female_count / count if count > 0 else 0
            else:
                female_ratio = 0

            # 資格保有率
            qual_col = None
            for col in ['資格数', 'qualifications_count', 'qualification_count']:
                if col in segment_df.columns:
                    qual_col = col
                    break

            if qual_col:
                qualified_rate = (segment_df[qual_col] > 0).mean()
                avg_qualifications = segment_df[qual_col].mean()
            else:
                qualified_rate = 0
                avg_qualifications = 0

            # 希望勤務地数
            location_count_col = None
            for col in ['希望勤務地数', 'desired_locations_count']:
                if col in segment_df.columns:
                    location_count_col = col
                    break

            avg_desired_locs = segment_df[location_count_col].mean() if location_count_col else 0

            # 緊急度
            urgency_col = None
            for col in ['希望入職時期', 'desired_start_timing']:
                if col in segment_df.columns:
                    urgency_col = col
                    break

            if urgency_col:
                urgent_conditions = ['今すぐに', '1ヶ月以内', '1', '2']
                urgency_rate = segment_df[urgency_col].isin(urgent_conditions).mean()
            else:
                urgency_rate = 0

            # 主要居住地TOP3
            residence_col = None
            for col in ['居住地_市区町村', '居住地', 'residence', 'residence_muni', 'residence_raw']:
                if col in segment_df.columns:
                    residence_col = col
                    break

            if residence_col:
                top_residences = segment_df[residence_col].value_counts().head(3)
                top_res_str = '; '.join([f"{k}({v}名)" for k, v in top_residences.items()])
            else:
                top_res_str = '不明'

            # 特徴サマリー
            if avg_age < 30:
                age_feature = '若年層中心'
            elif avg_age < 45:
                age_feature = '中年層中心'
            elif avg_age < 60:
                age_feature = '準高齢層中心'
            else:
                age_feature = '高齢層中心'

            if female_ratio > 0.7:
                gender_feature = '女性多数'
            elif female_ratio < 0.3:
                gender_feature = '男性多数'
            else:
                gender_feature = '性別バランス良'

            if qualified_rate > 0.7:
                qual_feature = '高資格保有'
            else:
                qual_feature = '資格取得支援推奨'

            persona_profiles.append({
                'セグメントID': segment_id,
                'ペルソナ名': persona_name,
                '人数': count,
                '構成比': round(count / len(self.df_processed), 3),
                '平均年齢': round(avg_age, 1),
                '女性比率': round(female_ratio, 3),
                '資格保有率': round(qualified_rate, 3),
                '平均資格数': round(avg_qualifications, 2),
                '平均希望地数': round(avg_desired_locs, 1),
                '緊急度': round(urgency_rate, 3),
                '主要居住地TOP3': top_res_str,
                '特徴': f"{age_feature}・{gender_feature}・{qual_feature}"
            })

        result_df = pd.DataFrame(persona_profiles)

        # 人数順でソート
        if len(result_df) > 0:
            result_df = result_df.sort_values('人数', ascending=False)

        return result_df

    def _generate_persona_mobility_cross(self):
        """
        GAS改良機能: ペルソナ×移動許容度クロス分析CSV生成

        ペルソナ（cluster）ごとの移動許容度レベル（A/B/C/D）分布を集計
        ROI 13.3 - 最優先機能
        """
        if len(self.df_processed) == 0:
            print("  [WARNING] df_processedが空です")
            return pd.DataFrame()

        if 'mobility_score' not in self.results or len(self.results['mobility_score']) == 0:
            print("  [WARNING] mobility_scoreが見つかりません")
            return pd.DataFrame()

        # クラスタ（ペルソナID）カラムを特定
        cluster_col = None
        for col in ['cluster', 'segment_id', 'persona_id']:
            if col in self.df_processed.columns:
                cluster_col = col
                break

        if not cluster_col:
            print("  [WARNING] ペルソナIDカラムが見つかりません")
            return pd.DataFrame()

        # 申請者IDカラムを特定
        id_col = None
        for col in ['申請者ID', 'ID', 'id', 'applicant_id']:
            if col in self.df_processed.columns:
                id_col = col
                break

        if not id_col:
            print("  [WARNING] 申請者IDカラムが見つかりません")
            return pd.DataFrame()

        # 型を統一
        df_processed_copy = self.df_processed.copy()
        df_processed_copy[id_col] = df_processed_copy[id_col].astype(str)

        mobility_copy = self.results['mobility_score'].copy()
        mobility_copy['申請者ID'] = mobility_copy['申請者ID'].astype(str)

        # マージ
        merged = df_processed_copy.merge(
            mobility_copy[['申請者ID', '移動許容度レベル']],
            left_on=id_col,
            right_on='申請者ID',
            how='inner'
        )

        if len(merged) == 0:
            print("  [WARNING] マージ結果が空です")
            return pd.DataFrame()

        # クロス集計
        cross_table = pd.crosstab(
            merged[cluster_col],
            merged['移動許容度レベル'],
            margins=False
        )

        # カラム順序を保証（A/B/C/D）
        for level in ['A', 'B', 'C', 'D']:
            if level not in cross_table.columns:
                cross_table[level] = 0

        cross_table = cross_table[['A', 'B', 'C', 'D']]

        # ペルソナIDをインデックスから列に
        cross_table = cross_table.reset_index()
        cross_table = cross_table.rename(columns={cluster_col: 'ペルソナID'})

        # ペルソナ名を追加
        persona_name_col = None
        for col in ['segment_name', 'persona_name', 'cluster_name']:
            if col in self.df_processed.columns:
                persona_name_col = col
                break

        if persona_name_col:
            persona_names = self.df_processed.groupby(cluster_col)[persona_name_col].first()
            cross_table['ペルソナ名'] = cross_table['ペルソナID'].map(persona_names)
        else:
            cross_table['ペルソナ名'] = cross_table['ペルソナID'].apply(lambda x: f"セグメント{x}")

        # 列順序を整理
        cross_table = cross_table[['ペルソナID', 'ペルソナ名', 'A', 'B', 'C', 'D']]

        # 合計を追加
        cross_table['合計'] = cross_table[['A', 'B', 'C', 'D']].sum(axis=1)

        # 比率を追加（パーセンテージ）
        for level in ['A', 'B', 'C', 'D']:
            cross_table[f'{level}比率'] = (cross_table[level] / cross_table['合計'] * 100).round(1)

        return cross_table

    def _generate_persona_map_data(self):
        """
        GAS改良機能: ペルソナ地図データ生成（座標付き）

        ペルソナ（cluster）ごとの地理的分布を座標付きで生成
        Google Maps APIで可視化するためのデータ
        ROI 7.1
        """
        if len(self.df_processed) == 0:
            print("  [WARNING] df_processedが空です")
            return pd.DataFrame()

        # クラスタ（ペルソナID）カラムを特定
        cluster_col = None
        for col in ['cluster', 'segment_id', 'persona_id']:
            if col in self.df_processed.columns:
                cluster_col = col
                break

        if not cluster_col:
            print("  [WARNING] ペルソナIDカラムが見つかりません")
            return pd.DataFrame()

        # 居住地カラムを特定
        residence_col = None
        for col in ['residence_muni', 'residence', '居住地_市区町村', '居住地']:
            if col in self.df_processed.columns:
                residence_col = col
                break

        if not residence_col:
            print("  [WARNING] 居住地カラムが見つかりません")
            return pd.DataFrame()

        # 居住地×ペルソナIDのクロス集計
        persona_location_cross = self.df_processed.groupby(
            [residence_col, cluster_col]
        ).size().reset_index(name='count')

        # 座標を追加
        persona_map_data = []
        missing_coords_count = 0

        for _, row in persona_location_cross.iterrows():
            location = row[residence_col]
            persona_id = row[cluster_col]
            count = row['count']

            # geocacheから座標取得（キーマッピング付き）
            lat, lng = None, None

            # 方法1: 直接一致を試行
            if location in self.geocache:
                lat = self.geocache[location]['lat']
                lng = self.geocache[location]['lng']
            else:
                # 方法2: 都道府県+市区町村形式で検索
                # geocacheのキーから市区町村部分が一致するものを探す
                for geocache_key in self.geocache.keys():
                    # geocache_keyが「都道府県+市区町村」形式（例：「東京都新宿区」）
                    # locationが「市区町村」形式（例：「新宿区」）
                    if geocache_key.endswith(location):
                        lat = self.geocache[geocache_key]['lat']
                        lng = self.geocache[geocache_key]['lng']
                        break

            if lat is None or lng is None:
                # 座標が見つからない場合はスキップ
                missing_coords_count += 1
                continue

            persona_map_data.append({
                '市区町村': location,
                '緯度': lat,
                '経度': lng,
                'ペルソナID': persona_id,
                '求職者数': count
            })

        if missing_coords_count > 0:
            print(f"  [INFO] 座標が見つからない地域: {missing_coords_count}件")

        result_df = pd.DataFrame(persona_map_data)

        if len(result_df) == 0:
            print("  [WARNING] 座標付きデータが生成できませんでした")
            return result_df

        # ペルソナ名を追加
        persona_name_col = None
        for col in ['segment_name', 'persona_name', 'cluster_name']:
            if col in self.df_processed.columns:
                persona_name_col = col
                break

        if persona_name_col:
            persona_names = self.df_processed.groupby(cluster_col)[persona_name_col].first()
            result_df['ペルソナ名'] = result_df['ペルソナID'].map(persona_names)
        else:
            result_df['ペルソナ名'] = result_df['ペルソナID'].apply(lambda x: f"セグメント{x}")

        # 統計情報を追加（該当ペルソナの平均値）
        for persona_id in result_df['ペルソナID'].unique():
            persona_df = self.df_processed[self.df_processed[cluster_col] == persona_id]

            # 平均年齢
            age_col = None
            for col in ['年齢', 'age']:
                if col in persona_df.columns:
                    age_col = col
                    break
            avg_age = persona_df[age_col].mean() if age_col else None

            # 女性比率
            gender_col = None
            for col in ['性別', 'gender']:
                if col in persona_df.columns:
                    gender_col = col
                    break

            if gender_col:
                female_ratio = persona_df[gender_col].str.contains('女', na=False).mean()
            else:
                female_ratio = None

            # 資格保有率
            qual_col = None
            for col in ['資格数', 'qualifications_count', 'qualification_count']:
                if col in persona_df.columns:
                    qual_col = col
                    break

            if qual_col:
                qualified_rate = (persona_df[qual_col] > 0).mean()
            else:
                qualified_rate = None

            # データフレームに追加
            result_df.loc[result_df['ペルソナID'] == persona_id, '平均年齢'] = round(avg_age, 1) if avg_age else None
            result_df.loc[result_df['ペルソナID'] == persona_id, '女性比率'] = round(female_ratio, 3) if female_ratio else None
            result_df.loc[result_df['ペルソナID'] == persona_id, '資格保有率'] = round(qualified_rate, 3) if qualified_rate else None

        # 列順序を整理
        columns_order = ['市区町村', '緯度', '経度', 'ペルソナID', 'ペルソナ名', '求職者数', '平均年齢', '女性比率', '資格保有率']
        result_df = result_df[columns_order]

        # 求職者数でソート
        result_df = result_df.sort_values('求職者数', ascending=False)

        return result_df

    def export_phase7_csv(self, output_dir='gas_output_phase7'):
        """Phase 7の結果をCSV出力"""
        print("\n" + "=" * 60)
        print("Phase 7: CSV出力")
        print("=" * 60)

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        files_created = []

        # 1. 人材供給密度マップ
        if 'supply_density' in self.results and len(self.results['supply_density']) > 0:
            filepath = output_path / 'SupplyDensityMap.csv'
            self.results['supply_density'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('SupplyDensityMap.csv', len(self.results['supply_density'])))
            print(f"  [OK] SupplyDensityMap.csv: {len(self.results['supply_density'])}行")

        # 2. 資格別人材分布
        if 'qualification_dist' in self.results and len(self.results['qualification_dist']) > 0:
            filepath = output_path / 'QualificationDistribution.csv'
            self.results['qualification_dist'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('QualificationDistribution.csv', len(self.results['qualification_dist'])))
            print(f"  [OK] QualificationDistribution.csv: {len(self.results['qualification_dist'])}行")

        # 3. 年齢×性別クロス分析
        if 'age_gender_cross' in self.results and len(self.results['age_gender_cross']) > 0:
            filepath = output_path / 'AgeGenderCrossAnalysis.csv'
            self.results['age_gender_cross'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('AgeGenderCrossAnalysis.csv', len(self.results['age_gender_cross'])))
            print(f"  [OK] AgeGenderCrossAnalysis.csv: {len(self.results['age_gender_cross'])}行")

        # 4. 移動許容度スコア
        if 'mobility_score' in self.results and len(self.results['mobility_score']) > 0:
            filepath = output_path / 'MobilityScore.csv'
            self.results['mobility_score'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('MobilityScore.csv', len(self.results['mobility_score'])))
            print(f"  [OK] MobilityScore.csv: {len(self.results['mobility_score'])}行")

        # 5. ペルソナ詳細プロファイル
        if 'detailed_persona' in self.results and len(self.results['detailed_persona']) > 0:
            filepath = output_path / 'DetailedPersonaProfile.csv'
            self.results['detailed_persona'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('DetailedPersonaProfile.csv', len(self.results['detailed_persona'])))
            print(f"  [OK] DetailedPersonaProfile.csv: {len(self.results['detailed_persona'])}行")

        # 6. ペルソナ×移動許容度クロス分析（GAS改良機能）
        print("\n[GAS改良機能] ペルソナ×移動許容度クロス分析生成中...")
        self.results['persona_mobility_cross'] = self._generate_persona_mobility_cross()
        if len(self.results['persona_mobility_cross']) > 0:
            filepath = output_path / 'PersonaMobilityCross.csv'
            self.results['persona_mobility_cross'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('PersonaMobilityCross.csv', len(self.results['persona_mobility_cross'])))
            print(f"  [OK] PersonaMobilityCross.csv: {len(self.results['persona_mobility_cross'])}行")
        else:
            print("  [WARNING] PersonaMobilityCross.csvの生成に失敗しました")

        # 7. ペルソナ地図データ（座標付き）（GAS改良機能）
        print("\n[GAS改良機能] ペルソナ地図データ生成中...")
        self.results['persona_map_data'] = self._generate_persona_map_data()
        if len(self.results['persona_map_data']) > 0:
            filepath = output_path / 'PersonaMapData.csv'
            self.results['persona_map_data'].to_csv(filepath, index=False, encoding='utf-8-sig')
            files_created.append(('PersonaMapData.csv', len(self.results['persona_map_data'])))
            print(f"  [OK] PersonaMapData.csv: {len(self.results['persona_map_data'])}行")
        else:
            print("  [WARNING] PersonaMapData.csvの生成に失敗しました")

        print("\n" + "=" * 60)
        print(f"Phase 7: CSV出力完了（{len(files_created)}ファイル）")
        print("=" * 60)

        return files_created


def _integrate_desired_work_to_df_processed(df_processed):
    """
    DesiredWorkをdf_processedに統合

    Phase 7の責任として実行する
    区レベルの希望勤務地データを統合し、高精度な移動距離計算を可能にする
    """
    desired_work_path = Path("gas_output_phase1/DesiredWork.csv")

    if not desired_work_path.exists():
        print("  [INFO] DesiredWork.csvが見つかりません")
        print("  [INFO] フォールバックモード: 元データを使用（精度低下）")
        return

    try:
        # ファイルサイズチェック
        file_size_mb = desired_work_path.stat().st_size / 1024 / 1024
        if file_size_mb > 500:  # 500MB超
            print(f"  [WARNING] DesiredWorkが大きすぎます({file_size_mb:.1f}MB)")
            print("  [WARNING] メモリ不足の可能性があります")

        # DesiredWorkを読み込み
        desired_work = pd.read_csv(desired_work_path, encoding='utf-8-sig')

        # カラム確認
        if '申請者ID' not in desired_work.columns:
            print("  [ERROR] DesiredWorkに申請者IDカラムがありません")
            return

        if 'キー' not in desired_work.columns:
            print("  [ERROR] DesiredWorkにキーカラムがありません")
            return

        # 申請者IDカラムを特定
        id_col = None
        for col in ['申請者ID', 'ID', 'id', 'applicant_id']:
            if col in df_processed.columns:
                id_col = col
                break

        if not id_col:
            print("  [WARNING] 申請者IDカラムが見つかりません")
            return

        # 型を統一（重要！）
        df_processed[id_col] = df_processed[id_col].astype(str)
        desired_work['申請者ID'] = desired_work['申請者ID'].astype(str)

        # ID_プレフィックスを処理
        # DesiredWorkが "ID_1" 形式で、df_processedが "1" 形式の場合
        sample_dw_id = desired_work['申請者ID'].iloc[0]
        sample_df_id = df_processed[id_col].iloc[0]

        if sample_dw_id.startswith('ID_') and not sample_df_id.startswith('ID_'):
            # DesiredWorkから "ID_" を削除
            desired_work['申請者ID'] = desired_work['申請者ID'].str.replace('ID_', '', regex=False)
            print(f"  [INFO] DesiredWorkのIDから 'ID_' プレフィックスを削除")
        elif not sample_dw_id.startswith('ID_') and sample_df_id.startswith('ID_'):
            # df_processedに "ID_" を追加
            df_processed[id_col] = 'ID_' + df_processed[id_col]
            print(f"  [INFO] df_processedのIDに 'ID_' プレフィックスを追加")

        # 申請者ごとの希望勤務地リスト作成
        desired_locs_map = {}
        for applicant_id in desired_work['申請者ID'].unique():
            locs = desired_work[
                desired_work['申請者ID'] == applicant_id
            ]['キー'].tolist()
            desired_locs_map[applicant_id] = locs

        # df_processedに追加（破壊的変更）
        df_processed['desired_locations_keys'] = df_processed[id_col].map(desired_locs_map)

        # NaNを空リストに変換
        df_processed['desired_locations_keys'] = df_processed['desired_locations_keys'].apply(
            lambda x: x if isinstance(x, list) else []
        )

        # 統計情報
        total = len(df_processed)
        with_locations = (df_processed['desired_locations_keys'].apply(len) > 0).sum()

        print(f"  [統合] 区レベル希望地データ統合完了")
        print(f"    - 希望地あり: {with_locations}/{total}人")
        print(f"    - 希望地0件: {total - with_locations}人")

    except pd.errors.ParserError as e:
        print(f"  [ERROR] CSVパースエラー: {e}")
    except MemoryError:
        print(f"  [ERROR] メモリ不足")
    except Exception as e:
        print(f"  [ERROR] 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()


def run_phase7_analysis(df, df_processed, geocache, master, output_dir='gas_output_phase7'):
    """
    Phase 7分析のメイン実行関数

    Args:
        df: 元データフレーム
        df_processed: 処理済みデータフレーム
        geocache: 座標キャッシュ辞書
        master: マスターデータインスタンス
        output_dir: 出力ディレクトリ

    Returns:
        Phase7AdvancedAnalyzer: 分析結果を含むインスタンス
    """
    # ============================================
    # ステップ1: DesiredWorkをdf_processedに統合
    # ============================================
    if 'desired_locations_keys' not in df_processed.columns:
        _integrate_desired_work_to_df_processed(df_processed)

    # ============================================
    # ステップ2: 分析実行
    # ============================================
    analyzer = Phase7AdvancedAnalyzer(df, df_processed, geocache, master)
    analyzer.run_all_analysis()
    analyzer.export_phase7_csv(output_dir)

    return analyzer


if __name__ == '__main__':
    print("Phase 7: 高度分析機能モジュール")
    print("このファイルは test_phase6_temp.py から呼び出されます")
