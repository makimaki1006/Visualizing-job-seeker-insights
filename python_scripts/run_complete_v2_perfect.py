"""
ジョブメドレー求職者データ分析 v2.2 - MAP統合版
Phase 1-3, 6-8, 10, 12-14の全実装

【対応内容】
✅ 出力先: data/output_v2/phase*/
✅ Phase別ファイル名: P{Phase}_QualityReport*.csv
✅ 品質レポート: 全Phaseで生成（Descriptive/Inferential）
✅ Phase 8: キャリア・学歴分析（完全実装）
✅ Phase 10: 転職意欲・緊急度分析（完全実装）
✅ Phase 12: 需給ギャップ分析（MAP統合対応）
✅ Phase 13: 希少性スコア（MAP統合対応）
✅ Phase 14: 競合分析（MAP統合対応）
✅ data_normalizer統合: 表記ゆれ正規化
✅ Phase 7ファイル名修正: SupplyDensityMap.csv等
✅ MAP統合: latitude/longitude列追加
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict
import re
import sys
import io
import tkinter as tk
from tkinter import filedialog
from scipy.stats import chi2_contingency, f_oneway

# Windows環境での絵文字出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 依存モジュールのインポート
try:
    from data_normalizer import DataNormalizer
    from data_quality_validator import DataQualityValidator
    from constants import EmploymentStatus, EducationLevel, AgeGroup, Gender
except ImportError as e:
    print(f"警告: 依存モジュールのインポートに失敗しました: {e}")
    print("data_normalizer.py、data_quality_validator.py、constants.py が必要です")
    sys.exit(1)


class PerfectJobSeekerAnalyzer:
    """完璧版求職者データ分析クラス"""

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.df = None
        self.df_normalized = None
        self.processed_data = None
        self.geocache = {}
        self.municipality_coords = {}

        # geocache.jsonのパスを統一（data/output_v2/geocache.json）
        self.geocache_file = Path('data/output_v2/geocache.json')
        self.geocache_file.parent.mkdir(parents=True, exist_ok=True)

        # geocache読み込み
        if self.geocache_file.exists():
            with open(self.geocache_file, 'r', encoding='utf-8') as f:
                self.geocache = json.load(f)

        # municipality_coords.csv読み込み
        municipality_coords_file = Path('data/municipality_coords.csv')
        if municipality_coords_file.exists():
            try:
                coords_df = pd.read_csv(municipality_coords_file, encoding='utf-8-sig')
                for _, row in coords_df.iterrows():
                    key = f"{row['prefecture']}{row['municipality']}"
                    self.municipality_coords[key] = (row['latitude'], row['longitude'])
                print(f"[INFO] 市区町村座標データ読み込み: {len(self.municipality_coords)}件")
            except Exception as e:
                print(f"[WARNING] 市区町村座標データの読み込みに失敗しました: {e}")
                print(f"[WARNING] フォールバックロジックを使用します")

        # DataNormalizerとDataQualityValidatorの初期化
        self.normalizer = DataNormalizer()
        self.validator_descriptive = DataQualityValidator(validation_mode='descriptive')
        self.validator_inferential = DataQualityValidator(validation_mode='inferential')

    def load_data(self):
        """データ読み込みと正規化"""
        print(f"\n[LOAD] データ読み込み: {self.filepath.name}")
        self.df = pd.read_csv(self.filepath, encoding='utf-8-sig')
        print(f"  [OK] {len(self.df)}行 x {len(self.df.columns)}列")

        # データ正規化
        print("\n[NORMALIZE] データ正規化中...")
        self.df_normalized = self.normalizer.normalize_dataframe(self.df)
        print(f"  [OK] 正規化完了")

        return self.df_normalized

    def process_data(self):
        """データ処理"""
        print("\n[PROCESS] データ処理...")

        processed_rows = []
        for idx, row in self.df_normalized.iterrows():
            age, gender = self._parse_age_gender(row.get('age_gender'))
            residence_pref, residence_muni = self._parse_location(row.get('location'))
            desired_areas = self._parse_desired_areas(row.get('desired_area'))
            qualifications = self._parse_qualifications(row.get('qualifications'))

            # 年齢層の算出
            age_bucket = self._get_age_bucket(age)

            # 国家資格保有フラグ
            national_licenses = ['看護師', '准看護師', '保健師', '助産師', '理学療法士', '作業療法士']
            has_national_license = any(q in national_licenses for q in qualifications)

            processed_rows.append({
                'id': idx,
                'page': row.get('page'),
                'card_index': row.get('card_index'),
                'age': age,
                'gender': gender,
                'age_bucket': age_bucket,
                'residence_pref': residence_pref,
                'residence_muni': residence_muni,
                'desired_areas': desired_areas,
                'desired_workstyle': row.get('desired_workstyle'),
                'desired_start': row.get('desired_start'),
                'career': row.get('career'),
                'employment_status': row.get('employment_status'),
                'desired_job': row.get('desired_job'),
                'qualifications': qualifications,
                'qualification_count': len(qualifications),
                'has_national_license': has_national_license,
                'member_id': row.get('member_id'),
                'status': row.get('status'),
                '年齢層': self._get_age_group_5year(age),
                '希望勤務地数': len(desired_areas),
            })

        self.processed_data = pd.DataFrame(processed_rows)
        print(f"  [OK] {len(self.processed_data)}件処理完了")
        return self.processed_data

    def _parse_age_gender(self, age_gender_str):
        """年齢・性別の解析"""
        if pd.isna(age_gender_str):
            return None, None

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

        location = str(location_str).strip()

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
            if qual:
                qualifications.append(qual)

        return qualifications

    def _get_age_bucket(self, age):
        """年齢層の算出（10年単位）"""
        if age is None or pd.isna(age):
            return None

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

    def _get_age_group_5year(self, age):
        """年齢層の算出（5年単位）"""
        if age is None or pd.isna(age):
            return None

        age = int(age)
        if age <= 29:
            return '20代以下'
        elif age <= 39:
            return '30代'
        elif age <= 49:
            return '40代'
        elif age <= 59:
            return '50代'
        else:
            return '60代以上'

    def _get_coords(self, prefecture, municipality):
        """座標取得（geocache使用 + 市区町村レベル座標対応）

        優先順位:
        1. self.municipality_coords（CSVから読み込んだ市区町村レベル座標）
        2. geocache（API取得済みキャッシュ）
        3. default_coords（都道府県レベルのフォールバック）
        """
        key = f"{prefecture}{municipality}"

        # 市区町村レベルの座標が存在する場合（最優先）
        if key in self.municipality_coords:
            lat, lng = self.municipality_coords[key]
            self.geocache[key] = {'lat': lat, 'lng': lng}  # geocacheを更新
            return lat, lng

        # geocacheに既存のデータがある場合（API取得済みキャッシュ）
        if key in self.geocache:
            return self.geocache[key]['lat'], self.geocache[key]['lng']

        # デフォルト座標（都道府県庁所在地の概算）
        default_coords = {
            '北海道': (43.06, 141.35), '青森県': (40.82, 140.74), '岩手県': (39.70, 141.15),
            '宮城県': (38.27, 140.87), '秋田県': (39.72, 140.10), '山形県': (38.25, 140.34),
            '福島県': (37.75, 140.47), '茨城県': (36.34, 140.45), '栃木県': (36.57, 139.88),
            '群馬県': (36.39, 139.06), '埼玉県': (35.86, 139.65), '千葉県': (35.61, 140.11),
            '東京都': (35.69, 139.69), '神奈川県': (35.45, 139.64), '新潟県': (37.90, 139.02),
            '富山県': (36.70, 137.21), '石川県': (36.59, 136.63), '福井県': (36.07, 136.22),
            '山梨県': (35.66, 138.57), '長野県': (36.65, 138.18), '岐阜県': (35.39, 136.72),
            '静岡県': (34.98, 138.38), '愛知県': (35.18, 136.91), '三重県': (34.73, 136.51),
            '滋賀県': (35.00, 135.87), '京都府': (35.02, 135.75), '大阪府': (34.69, 135.50),
            '兵庫県': (34.69, 135.18), '奈良県': (34.69, 135.83), '和歌山県': (34.23, 135.17),
            '鳥取県': (35.50, 134.23), '島根県': (35.47, 133.05), '岡山県': (34.66, 133.92),
            '広島県': (34.40, 132.46), '山口県': (34.19, 131.47), '徳島県': (34.07, 134.56),
            '香川県': (34.34, 134.04), '愛媛県': (33.84, 132.77), '高知県': (33.56, 133.53),
            '福岡県': (33.61, 130.42), '佐賀県': (33.25, 130.30), '長崎県': (32.75, 129.88),
            '熊本県': (32.79, 130.71), '大分県': (33.24, 131.61), '宮崎県': (31.91, 131.42),
            '鹿児島県': (31.56, 130.56), '沖縄県': (26.21, 127.68)
        }

        if prefecture in default_coords:
            lat, lng = default_coords[prefecture]
            # geocacheに保存
            self.geocache[key] = {'lat': lat, 'lng': lng}
            return lat, lng

        return None, None

    def _save_geocache(self):
        """geocacheの保存"""
        with open(self.geocache_file, 'w', encoding='utf-8') as f:
            json.dump(self.geocache, f, ensure_ascii=False, indent=2)

    def _save_quality_report(self, df, phase_num, output_path, mode='inferential'):
        """品質レポート保存ヘルパー"""
        validator = self.validator_inferential if mode == 'inferential' else self.validator_descriptive
        report = validator.generate_quality_report(df)

        # Phase別ファイル名
        if mode == 'inferential':
            filename = f'P{phase_num}_QualityReport_Inferential.csv'
        else:
            filename = f'P{phase_num}_QualityReport_Descriptive.csv'

        validator.export_quality_report_csv(report, str(output_path / filename))
        print(f"  [OK] {filename}")

        return report  # 品質レポートを返す

    def _calculate_quality_score(self, report):
        """品質レポートからスコアを抽出"""
        if 'overall_status' in report and 'quality_score' in report['overall_status']:
            return report['overall_status']['quality_score']
        return 0

    def _check_quality_gate(self, df, phase_num, phase_name, mode='inferential'):
        """
        品質ゲートチェック

        Args:
            df: 検証対象DataFrame
            phase_num: Phaseナンバー
            phase_name: Phase名
            mode: 検証モード（'inferential' or 'descriptive'）

        Returns:
            (save_data, quality_score):
                save_data: True（保存する）/ False（スキップ）
                quality_score: 品質スコア
        """
        validator = self.validator_inferential if mode == 'inferential' else self.validator_descriptive
        report = validator.generate_quality_report(df)
        quality_score = self._calculate_quality_score(report)

        # スコアが60未満の場合、警告と確認
        if quality_score < 60:
            print(f"\n  ⚠️  [警告] Phase {phase_num}の品質スコア: {quality_score:.1f}/100 (POOR)")
            print(f"  ⚠️  [警告] このデータは推論的考察には使用できません")
            print(f"  ⚠️  [警告] 観察的記述のみ使用可能です（件数、平均値などの記述）")
            print(f"")
            print(f"  選択肢:")
            print(f"  1. 観察的記述専用として保存（推奨）")
            print(f"  2. 保存をスキップ")
            print(f"  3. 強制的に保存（非推奨、自己責任）")
            print(f"")

            while True:
                try:
                    choice = input(f"  選択してください (1/2/3): ").strip()
                    if choice in ['1', '2', '3']:
                        break
                    else:
                        print(f"  ❌ 1, 2, 3のいずれかを入力してください")
                except KeyboardInterrupt:
                    print(f"\n  [CANCEL] ユーザーによりキャンセルされました")
                    return False, quality_score
                except EOFError:
                    # 非対話モードの場合、自動的に選択肢1（観察的記述専用）を選択
                    print(f"  [AUTO] 非対話モードのため、自動的に選択肢1（観察的記述専用）を選択します")
                    choice = '1'
                    break

            if choice == '1':
                print(f"  [OK] 観察的記述専用として保存します")
                return True, quality_score
            elif choice == '2':
                print(f"  [SKIP] Phase {phase_num}をスキップしました")
                return False, quality_score
            elif choice == '3':
                print(f"  ⚠️  [WARNING] 強制保存します（自己責任）")
                return True, quality_score

        # スコアが60以上の場合、通常保存
        return True, quality_score

    # ===========================================
    # Phase 1: 基礎集計
    # ===========================================

    def export_phase1(self, output_dir='data/output_v2/phase1'):
        """Phase 1: 基礎集計データのエクスポート"""
        print("\n[PHASE1] Phase 1: 基礎集計")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. MapMetrics.csv - 地図表示用データ
        map_data = []
        location_stats = defaultdict(lambda: {
            'count': 0,
            'ages': [],
            'genders': {'男性': 0, '女性': 0},
            'qualifications': 0
        })

        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                key = area['full']
                location_stats[key]['count'] += 1
                if row['age']:
                    location_stats[key]['ages'].append(row['age'])
                location_stats[key]['genders'][row['gender']] += 1
                location_stats[key]['qualifications'] += row['qualification_count']

        for location, stats in location_stats.items():
            pref, muni = self._parse_location(location)
            lat, lng = self._get_coords(pref, muni)

            map_data.append({
                'prefecture': pref,
                'municipality': muni,
                'location_key': location,
                'applicant_count': stats['count'],
                'avg_age': np.mean(stats['ages']) if stats['ages'] else None,
                'male_count': stats['genders']['男性'],
                'female_count': stats['genders']['女性'],
                'avg_qualifications': stats['qualifications'] / stats['count'] if stats['count'] > 0 else 0,
                'latitude': lat,
                'longitude': lng
            })

        map_metrics_df = pd.DataFrame(map_data)
        map_metrics_df = map_metrics_df.sort_values('applicant_count', ascending=False)
        map_metrics_df.to_csv(output_path / 'Phase1_MapMetrics.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MapMetrics.csv: {len(map_metrics_df)}件")

        # 2. Applicants.csv - 申請者基本情報（完全版）
        applicants_data = []
        for idx, row in self.processed_data.iterrows():
            # 資格リストをJSON文字列に変換（カンマ区切りでCSV互換性を確保）
            qualifications_str = ','.join(row['qualifications']) if row['qualifications'] else ''

            applicants_data.append({
                'applicant_id': row['id'],
                'age': row['age'],
                'gender': row['gender'],
                'age_group': row['age_bucket'],
                'residence_prefecture': row['residence_pref'],
                'residence_municipality': row['residence_muni'],
                'desired_area_count': len(row['desired_areas']),
                'qualification_count': row['qualification_count'],
                'has_national_license': row['has_national_license'],
                'qualifications': qualifications_str,
                'desired_workstyle': row['desired_workstyle'],
                'desired_start': row['desired_start'],
                'desired_job': row['desired_job'],
                'career': row['career'],
                'employment_status': row['employment_status'],
                'status': row['status'],
                'member_id': row['member_id']
            })

        applicants_df = pd.DataFrame(applicants_data)
        applicants_df.to_csv(output_path / 'Phase1_Applicants.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] Applicants.csv: {len(applicants_df)}件（全17カラム）")

        # 3. DesiredWork.csv - 希望勤務地詳細
        desired_work_data = []
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                desired_work_data.append({
                    'applicant_id': row['id'],
                    'desired_prefecture': area['prefecture'],
                    'desired_municipality': area['municipality'],
                    'desired_location_full': area['full']
                })

        desired_work_df = pd.DataFrame(desired_work_data)
        desired_work_df.to_csv(output_path / 'Phase1_DesiredWork.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] DesiredWork.csv: {len(desired_work_df)}件")

        # 4. AggDesired.csv - 集計データ
        agg_desired_df = map_metrics_df[['prefecture', 'municipality', 'location_key', 'applicant_count']].copy()
        agg_desired_df.to_csv(output_path / 'Phase1_AggDesired.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] AggDesired.csv: {len(agg_desired_df)}件")

        # 5-6. 品質レポート（Descriptive）
        self._save_quality_report(self.df_normalized, 1, output_path, mode='descriptive')

        # 総合品質レポート（オプション）
        report_overall = self.validator_descriptive.generate_quality_report(self.df_normalized)
        self.validator_descriptive.export_quality_report_csv(report_overall, str(output_path / 'P1_QualityReport.csv'))
        print(f"  [OK] P1_QualityReport.csv")

        # geocache保存
        self._save_geocache()

        # 7. マスタデータ生成（フィルタ選択肢用）
        print("\n  [MASTER] マスタデータ生成中...")

        # 7-1. 資格マスタ
        qual_master_df = self._generate_qualification_master()
        qual_master_df.to_csv(output_path / 'Phase1_QualificationMaster.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] QualificationMaster.csv: {len(qual_master_df)}件")

        # 7-2. 都道府県マスタ
        pref_master_df = self._generate_prefecture_master()
        pref_master_df.to_csv(output_path / 'Phase1_PrefectureMaster.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PrefectureMaster.csv: {len(pref_master_df)}件")

        # 7-3. 就業状況マスタ
        emp_master_df = self._generate_employment_status_master()
        emp_master_df.to_csv(output_path / 'Phase1_EmploymentStatusMaster.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] EmploymentStatusMaster.csv: {len(emp_master_df)}件")

        # 8. 市町村別詳細データ生成
        print("\n  [DETAIL] 市町村別詳細データ生成中...")

        # 8-1. 市町村×居住地×ペルソナのクロス集計
        persona_residence_df = self._generate_persona_by_municipality_with_residence()
        persona_residence_df.to_csv(output_path / 'Phase1_PersonaByMunicipality_WithResidence.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaByMunicipality_WithResidence.csv: {len(persona_residence_df)}件")

        # 8-2. 市町村×資格のクロス集計
        qual_dist_df = self._generate_qualification_distribution_by_municipality()
        qual_dist_df.to_csv(output_path / 'Phase1_QualificationDistributionByMunicipality.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] QualificationDistributionByMunicipality.csv: {len(qual_dist_df)}件")

        print(f"  [DIR] 出力先: {output_path}")

    # ===========================================
    # Phase 1 ヘルパーメソッド: マスタデータ生成
    # ===========================================

    def _generate_qualification_master(self):
        """資格マスタを生成"""
        qual_stats = defaultdict(lambda: {'count': 0, 'ages': [], 'national': False})

        for idx, row in self.processed_data.iterrows():
            for qual in row['qualifications']:
                qual_stats[qual]['count'] += 1
                if row['age']:
                    qual_stats[qual]['ages'].append(row['age'])

        # 国家資格判定
        national_licenses = ['看護師', '准看護師', '保健師', '助産師', '理学療法士', '作業療法士',
                            '介護福祉士', '社会福祉士', '精神保健福祉士', '保育士', '栄養士', '管理栄養士']

        results = []
        for qual_name, stats in qual_stats.items():
            is_national = qual_name in national_licenses
            results.append({
                'qualification_name': qual_name,
                'is_national_license': is_national,
                'applicant_count': stats['count'],
                'avg_age': np.mean(stats['ages']) if stats['ages'] else None
            })

        df = pd.DataFrame(results)
        return df.sort_values('applicant_count', ascending=False)

    def _generate_prefecture_master(self):
        """都道府県マスタを生成（居住地ベース）"""
        pref_stats = defaultdict(lambda: {'count': 0, 'municipalities': set()})

        for idx, row in self.processed_data.iterrows():
            if row['residence_pref']:
                pref_stats[row['residence_pref']]['count'] += 1
                if row['residence_muni']:
                    pref_stats[row['residence_pref']]['municipalities'].add(row['residence_muni'])

        results = []
        for pref, stats in pref_stats.items():
            results.append({
                'prefecture': pref,
                'applicant_count': stats['count'],
                'municipality_count': len(stats['municipalities'])
            })

        df = pd.DataFrame(results)
        return df.sort_values('applicant_count', ascending=False)

    def _generate_employment_status_master(self):
        """就業状況マスタを生成"""
        emp_stats = self.processed_data['employment_status'].value_counts()

        results = []
        for status, count in emp_stats.items():
            results.append({
                'employment_status': status,
                'applicant_count': count
            })

        return pd.DataFrame(results)

    def _generate_persona_by_municipality_with_residence(self):
        """市町村×居住地×ペルソナのクロス集計"""
        results = []

        # DesiredWorkから市町村ごとの申請者IDを取得
        municipality_applicants = defaultdict(set)
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                target_muni = area['full']
                municipality_applicants[target_muni].add(row['id'])

        # 各市町村について処理
        for target_muni, applicant_ids in municipality_applicants.items():
            muni_data = self.processed_data[self.processed_data['id'].isin(applicant_ids)]

            # ペルソナ×居住地でグループ化
            for (age_group, gender, has_license, residence_pref), group_df in muni_data.groupby(
                ['age_bucket', 'gender', 'has_national_license', 'residence_pref']
            ):
                if pd.isna(age_group) or pd.isna(gender) or pd.isna(residence_pref):
                    continue

                # 上位資格を取得
                all_quals = []
                for quals in group_df['qualifications']:
                    all_quals.extend(quals)
                top_quals = pd.Series(all_quals).value_counts().head(3).index.tolist() if all_quals else []

                results.append({
                    'target_municipality': target_muni,
                    'age_group': age_group,
                    'gender': gender,
                    'has_national_license': has_license,
                    'residence_prefecture': residence_pref,
                    'count': len(group_df),
                    'avg_age': group_df['age'].mean(),
                    'employment_rate': (group_df['employment_status'] == '就業中').mean(),
                    'top_qualifications': ';'.join(top_quals) if top_quals else ''
                })

        df = pd.DataFrame(results)
        return df.sort_values(['target_municipality', 'count'], ascending=[True, False])

    def _generate_qualification_distribution_by_municipality(self):
        """市町村×資格のクロス集計"""
        results = []

        # DesiredWorkから市町村ごとの申請者IDを取得
        municipality_applicants = defaultdict(set)
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                target_muni = area['full']
                municipality_applicants[target_muni].add(row['id'])

        # 各市町村について処理
        for target_muni, applicant_ids in municipality_applicants.items():
            muni_data = self.processed_data[self.processed_data['id'].isin(applicant_ids)]

            # 資格ごとに集計
            qual_counts = defaultdict(lambda: {'count': 0, 'ages': [], 'employed': 0})
            for idx, row in muni_data.iterrows():
                for qual in row['qualifications']:
                    qual_counts[qual]['count'] += 1
                    if row['age']:
                        qual_counts[qual]['ages'].append(row['age'])
                    if row['employment_status'] == '就業中':
                        qual_counts[qual]['employed'] += 1

            for qual_name, stats in qual_counts.items():
                results.append({
                    'target_municipality': target_muni,
                    'qualification_name': qual_name,
                    'applicant_count': stats['count'],
                    'avg_age': np.mean(stats['ages']) if stats['ages'] else None,
                    'employment_rate': stats['employed'] / stats['count'] if stats['count'] > 0 else 0
                })

        df = pd.DataFrame(results)
        return df.sort_values(['target_municipality', 'applicant_count'], ascending=[True, False])

    # ===========================================
    # Phase 2: 統計分析
    # ===========================================

    def export_phase2(self, output_dir='data/output_v2/phase2'):
        """Phase 2: 統計分析データのエクスポート"""
        print("\n[PHASE2] Phase 2: 統計分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        chi_square_results = self._run_chi_square_tests(self.processed_data)
        anova_results = self._run_anova_tests(self.processed_data)
        combined_df = pd.concat([chi_square_results, anova_results], ignore_index=True)

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(combined_df, 2, "統計分析", mode='inferential')

        if not save_data:
            print(f"  [SKIP] Phase 2をスキップしました")
            return

        # 3. CSV保存
        chi_square_results.to_csv(output_path / 'Phase2_ChiSquareTests.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] ChiSquareTests.csv: {len(chi_square_results)}件")

        anova_results.to_csv(output_path / 'Phase2_ANOVATests.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] ANOVATests.csv: {len(anova_results)}件")

        # 4. 品質レポート保存
        self._save_quality_report(combined_df, 2, output_path, mode='inferential')

        print(f"  [OK] Phase 2完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _run_chi_square_tests(self, df):
        """カイ二乗検定を実施"""
        results = []

        # データフィルタリング
        df_filtered = df[(df['gender'].notna()) & (df['gender'] != '') &
                        (df['年齢層'].notna()) & (df['年齢層'] != '')].copy()

        print(f"  フィルタ後のデータ件数: {len(df_filtered)}件")

        if len(df_filtered) == 0:
            print("  [警告] フィルタ後のデータが0件です")
            return pd.DataFrame(results)

        # 希望勤務地数の分布確認
        print(f"  希望勤務地数の分布:")
        print(f"    あり: {(df_filtered['希望勤務地数'] > 0).sum()}件")
        print(f"    なし: {(df_filtered['希望勤務地数'] == 0).sum()}件")

        # パターン1: 性別 × 希望勤務地の有無
        try:
            df_temp = df_filtered.copy()
            df_temp['希望勤務地あり'] = (df_temp['希望勤務地数'] > 0).astype(int)

            contingency_table = pd.crosstab(df_temp['gender'], df_temp['希望勤務地あり'])

            if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)

                # 効果量（Cramér's V）
                n = contingency_table.sum().sum()
                min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
                cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

                # 解釈
                if cramers_v < 0.1:
                    interpretation = "効果量が非常に小さい"
                elif cramers_v < 0.3:
                    interpretation = "効果量が小さい"
                elif cramers_v < 0.5:
                    interpretation = "効果量が中程度"
                else:
                    interpretation = "効果量が大きい"

                results.append({
                    'pattern': '性別×希望勤務地の有無',
                    'group1': '性別',
                    'group2': '希望勤務地の有無',
                    'variable': '希望勤務地数',
                    'chi_square': round(chi2, 4),
                    'p_value': round(p_value, 6),
                    'df': dof,
                    'effect_size': round(cramers_v, 4),
                    'significant': p_value < 0.05,
                    'sample_size': n,
                    'interpretation': interpretation
                })
                print("  [OK] パターン1（性別×希望勤務地の有無）検定成功")
            else:
                print(f"  [スキップ] パターン1: クロス集計表の形状が不十分 ({contingency_table.shape})")
        except Exception as e:
            print(f"  [警告] パターン1の検定に失敗: {e}")

        # パターン2: 年齢層 × 希望勤務地の有無
        try:
            df_temp = df_filtered.copy()
            df_temp['希望勤務地あり'] = (df_temp['希望勤務地数'] > 0).astype(int)

            contingency_table = pd.crosstab(df_temp['年齢層'], df_temp['希望勤務地あり'])

            if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)

                # 効果量（Cramér's V）
                n = contingency_table.sum().sum()
                min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
                cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

                # 解釈
                if cramers_v < 0.1:
                    interpretation = "効果量が非常に小さい"
                elif cramers_v < 0.3:
                    interpretation = "効果量が小さい"
                elif cramers_v < 0.5:
                    interpretation = "効果量が中程度"
                else:
                    interpretation = "効果量が大きい"

                results.append({
                    'pattern': '年齢層×希望勤務地の有無',
                    'group1': '年齢層',
                    'group2': '希望勤務地の有無',
                    'variable': '希望勤務地数',
                    'chi_square': round(chi2, 4),
                    'p_value': round(p_value, 6),
                    'df': dof,
                    'effect_size': round(cramers_v, 4),
                    'significant': p_value < 0.05,
                    'sample_size': n,
                    'interpretation': interpretation
                })
                print("  [OK] パターン2（年齢層×希望勤務地の有無）検定成功")
            else:
                print(f"  [スキップ] パターン2: クロス集計表の形状が不十分 ({contingency_table.shape})")
        except Exception as e:
            print(f"  [警告] パターン2の検定に失敗: {e}")

        # パターン3: 性別 × 年齢層
        try:
            contingency_table = pd.crosstab(df_filtered['gender'], df_filtered['年齢層'])

            if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)

                # 効果量（Cramér's V）
                n = contingency_table.sum().sum()
                min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
                cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

                # 解釈
                if cramers_v < 0.1:
                    interpretation = "効果量が非常に小さい（性別と年齢層に関連性はほとんどない）"
                elif cramers_v < 0.3:
                    interpretation = "効果量が小さい（性別と年齢層に弱い関連性）"
                elif cramers_v < 0.5:
                    interpretation = "効果量が中程度（性別と年齢層に中程度の関連性）"
                else:
                    interpretation = "効果量が大きい（性別と年齢層に強い関連性）"

                results.append({
                    'pattern': '性別×年齢層',
                    'group1': '性別',
                    'group2': '年齢層',
                    'variable': '年齢',
                    'chi_square': round(chi2, 4),
                    'p_value': round(p_value, 6),
                    'df': dof,
                    'effect_size': round(cramers_v, 4),
                    'significant': p_value < 0.05,
                    'sample_size': n,
                    'interpretation': interpretation
                })
                print("  [OK] パターン3（性別×年齢層）検定成功")
        except Exception as e:
            print(f"  [警告] パターン3の検定に失敗: {e}")

        # パターン4: 就業状態 × 年齢層
        try:
            df_with_employment = df_filtered[df_filtered['employment_status'].notna() & (df_filtered['employment_status'] != '')]

            if len(df_with_employment) > 0:
                contingency_table = pd.crosstab(df_with_employment['employment_status'], df_with_employment['年齢層'])

                if contingency_table.shape[0] > 1 and contingency_table.shape[1] > 1:
                    chi2, p_value, dof, expected = chi2_contingency(contingency_table)

                    # 効果量（Cramér's V）
                    n = contingency_table.sum().sum()
                    min_dim = min(contingency_table.shape[0] - 1, contingency_table.shape[1] - 1)
                    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

                    # 解釈
                    if cramers_v < 0.1:
                        interpretation = "効果量が非常に小さい（就業状態と年齢層に関連性はほとんどない）"
                    elif cramers_v < 0.3:
                        interpretation = "効果量が小さい（就業状態と年齢層に弱い関連性）"
                    elif cramers_v < 0.5:
                        interpretation = "効果量が中程度（就業状態と年齢層に中程度の関連性）"
                    else:
                        interpretation = "効果量が大きい（就業状態と年齢層に強い関連性）"

                    results.append({
                        'pattern': '就業状態×年齢層',
                        'group1': '就業状態',
                        'group2': '年齢層',
                        'variable': '年齢',
                        'chi_square': round(chi2, 4),
                        'p_value': round(p_value, 6),
                        'df': dof,
                        'effect_size': round(cramers_v, 4),
                        'significant': p_value < 0.05,
                        'sample_size': n,
                        'interpretation': interpretation
                    })
                    print("  [OK] パターン4（就業状態×年齢層）検定成功")
        except Exception as e:
            print(f"  [警告] パターン4の検定に失敗: {e}")

        print(f"  カイ二乗検定結果: {len(results)}件")

        return pd.DataFrame(results)

    def _run_anova_tests(self, df):
        """ANOVA検定を実施"""
        results = []

        # データフィルタリング
        df_filtered = df[(df['age'].notna()) & (df['年齢層'].notna()) & (df['年齢層'] != '')].copy()

        print(f"  フィルタ後のデータ件数: {len(df_filtered)}件")

        if len(df_filtered) == 0:
            print("  [警告] フィルタ後のデータが0件です")
            return pd.DataFrame(results)

        # パターン1: 年齢層別の資格数
        try:
            groups = []
            age_groups = df_filtered['年齢層'].unique()

            for age_group in age_groups:
                group_data = df_filtered[df_filtered['年齢層'] == age_group]['qualification_count'].dropna()
                if len(group_data) > 0:
                    groups.append(group_data.values)

            if len(groups) >= 2:
                f_stat, p_value = f_oneway(*groups)

                # 効果量（η²）
                overall_mean = df_filtered['qualification_count'].mean()
                ss_between = sum(len(g) * (np.mean(g) - overall_mean) ** 2 for g in groups)
                ss_total = sum((df_filtered['qualification_count'] - overall_mean) ** 2)
                eta_squared = ss_between / ss_total if ss_total > 0 else 0

                # 解釈
                if eta_squared < 0.01:
                    interpretation = "効果量が非常に小さい"
                elif eta_squared < 0.06:
                    interpretation = "効果量が小さい"
                elif eta_squared < 0.14:
                    interpretation = "効果量が中程度"
                else:
                    interpretation = "効果量が大きい"

                results.append({
                    'pattern': '年齢層別の資格数',
                    'group': '年齢層',
                    'variable': '資格数',
                    'f_statistic': round(f_stat, 4),
                    'p_value': round(p_value, 6),
                    'effect_size': round(eta_squared, 4),
                    'significant': p_value < 0.05,
                    'sample_size': len(df_filtered),
                    'interpretation': interpretation
                })
                print("  [OK] パターン1（年齢層別の資格数）検定成功")
        except Exception as e:
            print(f"  [警告] パターン1の検定に失敗: {e}")

        # パターン2: 性別別の年齢
        try:
            groups = []
            genders = df_filtered['gender'].unique()

            for gender in genders:
                group_data = df_filtered[df_filtered['gender'] == gender]['age'].dropna()
                if len(group_data) > 0:
                    groups.append(group_data.values)

            if len(groups) >= 2:
                f_stat, p_value = f_oneway(*groups)

                # 効果量（η²）
                overall_mean = df_filtered['age'].mean()
                ss_between = sum(len(g) * (np.mean(g) - overall_mean) ** 2 for g in groups)
                ss_total = sum((df_filtered['age'] - overall_mean) ** 2)
                eta_squared = ss_between / ss_total if ss_total > 0 else 0

                # 解釈
                if eta_squared < 0.01:
                    interpretation = "効果量が非常に小さい（性別による年齢差はほとんどない）"
                elif eta_squared < 0.06:
                    interpretation = "効果量が小さい（性別による年齢差が弱い）"
                elif eta_squared < 0.14:
                    interpretation = "効果量が中程度（性別による年齢差が中程度）"
                else:
                    interpretation = "効果量が大きい（性別による年齢差が大きい）"

                results.append({
                    'pattern': '性別別の年齢',
                    'group': '性別',
                    'variable': '年齢',
                    'f_statistic': round(f_stat, 4),
                    'p_value': round(p_value, 6),
                    'effect_size': round(eta_squared, 4),
                    'significant': p_value < 0.05,
                    'sample_size': len(df_filtered),
                    'interpretation': interpretation
                })
                print("  [OK] パターン2（性別別の年齢）検定成功")
        except Exception as e:
            print(f"  [警告] パターン2の検定に失敗: {e}")

        print(f"  ANOVA検定結果: {len(results)}件")

        return pd.DataFrame(results)

    # ===========================================
    # Phase 3: ペルソナ分析
    # ===========================================

    def export_phase3(self, output_dir='data/output_v2/phase3'):
        """Phase 3: ペルソナ分析データのエクスポート"""
        print("\n[PHASE3] Phase 3: ペルソナ分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        persona_summary = self._generate_persona_summary(self.processed_data)
        persona_details = self._generate_persona_details(self.processed_data)
        combined_df = pd.concat([persona_summary, persona_details], ignore_index=True)

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(combined_df, 3, "ペルソナ分析", mode='inferential')

        if not save_data:
            print(f"  [SKIP] Phase 3をスキップしました")
            return

        # 3. CSV保存
        persona_summary.to_csv(output_path / 'Phase3_PersonaSummary.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaSummary.csv: {len(persona_summary)}件")

        persona_details.to_csv(output_path / 'Phase3_PersonaDetails.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] PersonaDetails.csv: {len(persona_details)}件")

        # 4. 市町村別ペルソナ分析（新機能）
        persona_by_muni = self._generate_persona_by_municipality(self.processed_data)
        if not persona_by_muni.empty:
            persona_by_muni.to_csv(output_path / 'Phase3_PersonaSummaryByMunicipality.csv', index=False, encoding='utf-8-sig')
            print(f"  [OK] PersonaSummaryByMunicipality.csv: {len(persona_by_muni)}件（{persona_by_muni['municipality'].nunique()}市町村）")

        # 5. 品質レポート保存
        self._save_quality_report(combined_df, 3, output_path, mode='inferential')

        print(f"  [OK] Phase 3完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_persona_summary(self, df):
        """ペルソナサマリーを生成"""
        results = []

        # ペルソナ定義（年齢層×性別×資格有無）
        for age_group in df['age_bucket'].dropna().unique():
            for gender in df['gender'].dropna().unique():
                for has_license in [True, False]:
                    persona_df = df[
                        (df['age_bucket'] == age_group) &
                        (df['gender'] == gender) &
                        (df['has_national_license'] == has_license)
                    ]

                    if len(persona_df) == 0:
                        continue

                    # ペルソナ名
                    license_label = "国家資格あり" if has_license else "国家資格なし"
                    persona_name = f"{age_group}・{gender}・{license_label}"

                    # 統計情報
                    results.append({
                        'persona_name': persona_name,
                        'age_group': age_group,
                        'gender': gender,
                        'has_national_license': has_license,
                        'count': len(persona_df),
                        'avg_desired_areas': persona_df['希望勤務地数'].mean(),
                        'avg_qualifications': persona_df['qualification_count'].mean(),
                        'employment_rate': (persona_df['employment_status'] == EmploymentStatus.EMPLOYED).sum() / len(persona_df) if len(persona_df) > 0 else 0
                    })

        return pd.DataFrame(results).sort_values('count', ascending=False)

    def _generate_persona_details(self, df):
        """ペルソナ詳細を生成"""
        results = []

        # ペルソナ定義（年齢層×性別）
        for age_group in df['age_bucket'].dropna().unique():
            for gender in df['gender'].dropna().unique():
                persona_df = df[
                    (df['age_bucket'] == age_group) &
                    (df['gender'] == gender)
                ]

                if len(persona_df) == 0:
                    continue

                # ペルソナ名
                persona_name = f"{age_group}・{gender}"

                # 詳細統計情報
                results.append({
                    'persona_name': persona_name,
                    'age_group': age_group,
                    'gender': gender,
                    'count': len(persona_df),
                    'avg_age': persona_df['age'].mean(),
                    'avg_desired_areas': persona_df['希望勤務地数'].mean(),
                    'avg_qualifications': persona_df['qualification_count'].mean(),
                    'national_license_rate': persona_df['has_national_license'].sum() / len(persona_df) if len(persona_df) > 0 else 0,
                    'employment_rate': (persona_df['employment_status'] == EmploymentStatus.EMPLOYED).sum() / len(persona_df) if len(persona_df) > 0 else 0,
                    'top_residence_pref': persona_df['residence_pref'].mode()[0] if len(persona_df['residence_pref'].mode()) > 0 else None
                })

        return pd.DataFrame(results).sort_values('count', ascending=False)

    def _generate_persona_by_municipality(self, df, output_dir='data/output_v2/phase1'):
        """市町村別ペルソナサマリーを生成"""
        print("  [INFO] 市町村別ペルソナ分析を開始...")

        # 1. DesiredWork.csvを読み込み
        desired_work_path = Path(output_dir) / 'DesiredWork.csv'
        if not desired_work_path.exists():
            print(f"  [ERROR] DesiredWork.csvが見つかりません: {desired_work_path}")
            return pd.DataFrame()

        desired_work_df = pd.read_csv(desired_work_path, encoding='utf-8-sig')

        # 2. 市町村のリスト（人数の多い順にソート）
        municipality_counts = desired_work_df['desired_location_full'].value_counts()
        municipalities = municipality_counts.index.tolist()

        print(f"  [INFO] 分析対象市町村数: {len(municipalities)}")

        results = []

        # 3. 各市町村について処理
        for idx, municipality in enumerate(municipalities):
            if (idx + 1) % 50 == 0:
                print(f"  [PROGRESS] {idx + 1}/{len(municipalities)} 市町村処理済み...")

            # その市町村を希望している applicant_id のリスト
            applicant_ids = desired_work_df[
                desired_work_df['desired_location_full'] == municipality
            ]['applicant_id'].unique()

            # その applicant_id のペルソナ情報を取得
            # dfのインデックスがapplicant_idと仮定
            muni_df = df[df.index.isin(applicant_ids)]

            if len(muni_df) == 0:
                continue

            # 市町村内の母数
            total_in_muni = len(muni_df)

            # ペルソナ別集計（年齢層×性別×資格有無）
            for age_group in muni_df['age_bucket'].dropna().unique():
                for gender in muni_df['gender'].dropna().unique():
                    for has_license in [True, False]:
                        persona_df = muni_df[
                            (muni_df['age_bucket'] == age_group) &
                            (muni_df['gender'] == gender) &
                            (muni_df['has_national_license'] == has_license)
                        ]

                        if len(persona_df) == 0:
                            continue

                        # ペルソナ名
                        license_label = "国家資格あり" if has_license else "国家資格なし"
                        persona_name = f"{age_group}・{gender}・{license_label}"

                        # 市町村内シェア
                        market_share_pct = len(persona_df) / total_in_muni * 100

                        # 統計情報
                        results.append({
                            'municipality': municipality,
                            'persona_name': persona_name,
                            'age_group': age_group,
                            'gender': gender,
                            'has_national_license': has_license,
                            'count': len(persona_df),
                            'total_in_municipality': total_in_muni,
                            'market_share_pct': market_share_pct,
                            'avg_age': persona_df['age'].mean(),
                            'avg_desired_areas': persona_df['希望勤務地数'].mean(),
                            'avg_qualifications': persona_df['qualification_count'].mean(),
                            'employment_rate': (persona_df['employment_status'] == EmploymentStatus.EMPLOYED).sum() / len(persona_df) if len(persona_df) > 0 else 0
                        })

        print(f"  [OK] 市町村別ペルソナ分析完了: {len(results)}件")
        return pd.DataFrame(results)

    # ===========================================
    # Phase 6: フロー分析
    # ===========================================

    def export_phase6(self, output_dir='data/output_v2/phase6'):
        """Phase 6: フロー分析データのエクスポート"""
        print("\n[PHASE6] Phase 6: フロー分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        flow_edges = self._generate_flow_edges(self.processed_data)
        flow_nodes = self._generate_flow_nodes(self.processed_data)
        proximity_analysis = self._generate_proximity_analysis(self.processed_data)
        combined_df = pd.concat([flow_edges, flow_nodes, proximity_analysis], ignore_index=True)

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(combined_df, 6, "フロー分析", mode='inferential')

        if not save_data:
            print(f"  [SKIP] Phase 6をスキップしました")
            return

        # 3. CSV保存
        flow_edges.to_csv(output_path / 'Phase6_MunicipalityFlowEdges.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MunicipalityFlowEdges.csv: {len(flow_edges)}件")

        flow_nodes.to_csv(output_path / 'Phase6_MunicipalityFlowNodes.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MunicipalityFlowNodes.csv: {len(flow_nodes)}件")

        proximity_analysis.to_csv(output_path / 'Phase6_ProximityAnalysis.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] ProximityAnalysis.csv: {len(proximity_analysis)}件")

        # 集約フローエッジ生成（FlowNetworkMap用）
        aggregated_flow_edges = self._generate_aggregated_flow_edges(flow_edges)
        aggregated_flow_edges.to_csv(output_path / 'Phase6_AggregatedFlowEdges.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] AggregatedFlowEdges.csv: {len(aggregated_flow_edges)}件（Origin→Destination集約）")

        # 4. 品質レポート保存
        self._save_quality_report(combined_df, 6, output_path, mode='inferential')

        print(f"  [OK] Phase 6完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_flow_edges(self, df):
        """自治体間フローエッジを生成"""
        results = []

        for idx, row in df.iterrows():
            if not row['residence_pref'] or not row['residence_muni']:
                continue

            origin = f"{row['residence_pref']}{row['residence_muni']}"

            for area in row['desired_areas']:
                destination = area['full']

                if origin != destination:
                    results.append({
                        'origin': origin,
                        'destination': destination,
                        'origin_pref': row['residence_pref'],
                        'origin_muni': row['residence_muni'],
                        'destination_pref': area['prefecture'],
                        'destination_muni': area['municipality'],
                        'applicant_id': row['id'],
                        'age': row['age'],
                        'gender': row['gender']
                    })

        return pd.DataFrame(results)

    def _generate_flow_nodes(self, df):
        """自治体間フローノードを生成"""
        results = defaultdict(lambda: {'inflow': 0, 'outflow': 0, 'applicants': set()})

        for idx, row in df.iterrows():
            if not row['residence_pref'] or not row['residence_muni']:
                continue

            origin = f"{row['residence_pref']}{row['residence_muni']}"

            for area in row['desired_areas']:
                destination = area['full']

                if origin != destination:
                    # 流出
                    results[origin]['outflow'] += 1
                    results[origin]['applicants'].add(row['id'])

                    # 流入
                    results[destination]['inflow'] += 1
                    results[destination]['applicants'].add(row['id'])

        # DataFrameに変換
        nodes = []
        for location, data in results.items():
            pref, muni = self._parse_location(location)
            nodes.append({
                'location': location,
                'prefecture': pref,
                'municipality': muni,
                'inflow': data['inflow'],
                'outflow': data['outflow'],
                'net_flow': data['inflow'] - data['outflow'],
                'applicant_count': len(data['applicants'])
            })

        return pd.DataFrame(nodes).sort_values('net_flow', ascending=False)

    def _generate_aggregated_flow_edges(self, flow_edges_df):
        """
        Origin→Destinationの組み合わせでフローを集約

        FlowNetworkMap.htmlで地図上に矢印表示するための集約データ。
        各Origin→Destinationの組み合わせごとに、フロー数、平均年齢、最頻性別を算出。

        Parameters
        ----------
        flow_edges_df : pd.DataFrame
            _generate_flow_edges()で生成された個別フローデータ

        Returns
        -------
        pd.DataFrame
            集約されたフローデータ（Origin→Destinationごと）

        Examples
        --------
        >>> # 個別フロー（6,862行）
        >>> flow_edges_df
           origin                  destination             applicant_id  age  gender
           奈良県生駒郡平群町      大阪府東大阪市          1             27   男性
           奈良県生駒郡平群町      大阪府東大阪市          5             32   男性

        >>> # 集約後（数百行）
        >>> aggregated = _generate_aggregated_flow_edges(flow_edges_df)
           origin                  destination             flow_count  avg_age  gender_mode
           奈良県生駒郡平群町      大阪府東大阪市          87          35.2     男性
        """
        if flow_edges_df.empty:
            return pd.DataFrame(columns=[
                'origin', 'destination', 'origin_pref', 'origin_muni',
                'destination_pref', 'destination_muni', 'flow_count', 'avg_age', 'gender_mode'
            ])

        # Origin→Destinationの組み合わせで集約
        agg = flow_edges_df.groupby([
            'origin', 'destination',
            'origin_pref', 'origin_muni',
            'destination_pref', 'destination_muni'
        ]).agg({
            'applicant_id': 'count',  # フロー数
            'age': 'mean',            # 平均年齢
            'gender': lambda x: x.mode()[0] if len(x.mode()) > 0 else '不明'  # 最頻性別
        }).reset_index()

        # カラム名をわかりやすく変更
        agg.rename(columns={
            'applicant_id': 'flow_count',
            'age': 'avg_age',
            'gender': 'gender_mode'
        }, inplace=True)

        # フロー数でソート（降順）
        agg = agg.sort_values('flow_count', ascending=False)

        return agg

    def _generate_proximity_analysis(self, df):
        """移動パターン分析を生成"""
        results = []

        # 都道府県内移動 vs 都道府県外移動
        for idx, row in df.iterrows():
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
                results.append({
                    'applicant_id': row['id'],
                    'residence_pref': row['residence_pref'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'same_prefecture_count': same_pref_count,
                    'different_prefecture_count': diff_pref_count,
                    'total_desired_areas': same_pref_count + diff_pref_count,
                    'mobility_score': diff_pref_count / (same_pref_count + diff_pref_count) if (same_pref_count + diff_pref_count) > 0 else 0
                })

        return pd.DataFrame(results)

    # ===========================================
    # Phase 7: 高度分析（5つの分析）
    # ===========================================

    def export_phase7(self, output_dir='data/output_v2/phase7'):
        """Phase 7: 高度分析データのエクスポート"""
        print("\n[PHASE7] Phase 7: 高度分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        supply_density = self._generate_supply_density_map(self.processed_data)
        qualification_dist = self._generate_qualification_distribution(self.processed_data)
        age_gender_cross = self._generate_age_gender_cross_analysis(self.processed_data)
        mobility_score = self._generate_mobility_score(self.processed_data)
        persona_profile = self._generate_detailed_persona_profile(self.processed_data)
        combined_df = pd.concat([supply_density, qualification_dist, age_gender_cross, mobility_score, persona_profile], ignore_index=True)

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(combined_df, 7, "高度分析", mode='inferential')

        if not save_data:
            print(f"  [SKIP] Phase 7をスキップしました")
            return

        # 3. CSV保存
        supply_density.to_csv(output_path / 'Phase7_SupplyDensityMap.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] SupplyDensityMap.csv: {len(supply_density)}件")

        qualification_dist.to_csv(output_path / 'Phase7_QualificationDistribution.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] QualificationDistribution.csv: {len(qualification_dist)}件")

        age_gender_cross.to_csv(output_path / 'Phase7_AgeGenderCrossAnalysis.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] AgeGenderCrossAnalysis.csv: {len(age_gender_cross)}件")

        mobility_score.to_csv(output_path / 'Phase7_MobilityScore.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] MobilityScore.csv: {len(mobility_score)}件")

        persona_profile.to_csv(output_path / 'Phase7_DetailedPersonaProfile.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] DetailedPersonaProfile.csv: {len(persona_profile)}件")

        # 4. 品質レポート保存
        self._save_quality_report(combined_df, 7, output_path, mode='inferential')

        print(f"  [OK] Phase 7完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_supply_density_map(self, df):
        """人材供給密度マップを生成"""
        results = []

        # 希望勤務地別の人材供給密度
        for idx, row in df.iterrows():
            for area in row['desired_areas']:
                results.append({
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'],
                    'location': area['full'],
                    'applicant_id': row['id'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'has_national_license': row['has_national_license'],
                    'qualification_count': row['qualification_count']
                })

        df_results = pd.DataFrame(results)

        # 集計
        density_map = df_results.groupby('location').agg({
            'applicant_id': 'count',
            'age': 'mean',
            'has_national_license': 'sum',
            'qualification_count': 'mean'
        }).reset_index()

        density_map.columns = ['location', 'supply_count', 'avg_age', 'national_license_count', 'avg_qualifications']

        return density_map.sort_values('supply_count', ascending=False)

    def _generate_qualification_distribution(self, df):
        """資格別人材分布を生成"""
        results = []

        for idx, row in df.iterrows():
            for qual in row['qualifications']:
                results.append({
                    'qualification': qual,
                    'applicant_id': row['id'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'residence_pref': row['residence_pref']
                })

        df_results = pd.DataFrame(results)

        # 集計
        qual_dist = df_results.groupby('qualification').agg({
            'applicant_id': 'count',
            'age': 'mean'
        }).reset_index()

        qual_dist.columns = ['qualification', 'count', 'avg_age']

        return qual_dist.sort_values('count', ascending=False)

    def _generate_age_gender_cross_analysis(self, df):
        """年齢層×性別クロス分析を生成"""
        results = []

        for age_group in df['age_bucket'].dropna().unique():
            for gender in df['gender'].dropna().unique():
                subset = df[(df['age_bucket'] == age_group) & (df['gender'] == gender)]

                if len(subset) > 0:
                    results.append({
                        'age_group': age_group,
                        'gender': gender,
                        'count': len(subset),
                        'avg_desired_areas': subset['希望勤務地数'].mean(),
                        'avg_qualifications': subset['qualification_count'].mean(),
                        'national_license_rate': subset['has_national_license'].sum() / len(subset) if len(subset) > 0 else 0
                    })

        return pd.DataFrame(results).sort_values(['age_group', 'gender'])

    def _generate_mobility_score(self, df):
        """移動許容度スコアリングを生成"""
        results = []

        for idx, row in df.iterrows():
            if not row['residence_pref']:
                continue

            same_pref_count = 0
            diff_pref_count = 0

            for area in row['desired_areas']:
                if area['prefecture'] == row['residence_pref']:
                    same_pref_count += 1
                else:
                    diff_pref_count += 1

            total_areas = same_pref_count + diff_pref_count
            if total_areas > 0:
                mobility_score = diff_pref_count / total_areas

                # スコアランク
                if mobility_score == 0:
                    rank = 'A: 低い（県内のみ）'
                elif mobility_score < 0.5:
                    rank = 'B: やや低い'
                elif mobility_score < 0.8:
                    rank = 'C: 中程度'
                else:
                    rank = 'D: 高い（県外多数）'

                results.append({
                    'applicant_id': row['id'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'residence_pref': row['residence_pref'],
                    'same_prefecture_count': same_pref_count,
                    'different_prefecture_count': diff_pref_count,
                    'total_desired_areas': total_areas,
                    'mobility_score': round(mobility_score, 4),
                    'mobility_rank': rank
                })

        return pd.DataFrame(results).sort_values('mobility_score', ascending=False)

    def _generate_detailed_persona_profile(self, df):
        """ペルソナ詳細プロファイルを生成"""
        results = []

        # ペルソナ定義（年齢層×性別×就業状態）
        for age_group in df['age_bucket'].dropna().unique():
            for gender in df['gender'].dropna().unique():
                for employment in df['employment_status'].dropna().unique():
                    subset = df[
                        (df['age_bucket'] == age_group) &
                        (df['gender'] == gender) &
                        (df['employment_status'] == employment)
                    ]

                    if len(subset) == 0:
                        continue

                    persona_name = f"{age_group}・{gender}・{employment}"

                    results.append({
                        'persona_name': persona_name,
                        'age_group': age_group,
                        'gender': gender,
                        'employment_status': employment,
                        'count': len(subset),
                        'avg_age': subset['age'].mean(),
                        'avg_desired_areas': subset['希望勤務地数'].mean(),
                        'avg_qualifications': subset['qualification_count'].mean(),
                        'national_license_rate': subset['has_national_license'].sum() / len(subset) if len(subset) > 0 else 0,
                        'avg_mobility_score': self._calculate_avg_mobility_score(subset)
                    })

        return pd.DataFrame(results).sort_values('count', ascending=False)

    def _calculate_avg_mobility_score(self, subset):
        """移動許容度スコアの平均を計算"""
        mobility_scores = []

        for idx, row in subset.iterrows():
            if not row['residence_pref']:
                continue

            same_pref_count = 0
            diff_pref_count = 0

            for area in row['desired_areas']:
                if area['prefecture'] == row['residence_pref']:
                    same_pref_count += 1
                else:
                    diff_pref_count += 1

            total_areas = same_pref_count + diff_pref_count
            if total_areas > 0:
                mobility_scores.append(diff_pref_count / total_areas)

        return np.mean(mobility_scores) if mobility_scores else 0

    # ===========================================
    # Phase 8: キャリア・学歴分析
    # ===========================================

    def export_phase8(self, output_dir='data/output_v2/phase8'):
        """Phase 8: キャリア・学歴分析データのエクスポート（career列使用）"""
        print("\n[PHASE8] Phase 8: キャリア・学歴分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # キャリア（学歴）データの存在確認
        if 'career' not in self.df_normalized.columns:
            print("  [警告] career列が存在しません。Phase 8をスキップします。")
            return

        # 1. データ生成
        career_dist = self._generate_education_distribution(self.processed_data)
        career_age_cross = self._generate_education_age_cross(self.processed_data)
        career_age_matrix = self._generate_education_age_matrix(self.processed_data)
        graduation_year_dist = self._generate_graduation_year_distribution(self.processed_data)
        combined_df = pd.concat([career_dist, career_age_cross], ignore_index=True)

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(combined_df, 8, "キャリア・学歴分析", mode='inferential')

        if not save_data:
            print(f"  [SKIP] Phase 8をスキップしました")
            return

        # 3. CSV保存
        career_dist.to_csv(output_path / 'Phase8_CareerDistribution.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] CareerDistribution.csv: {len(career_dist)}件")

        career_age_cross.to_csv(output_path / 'Phase8_CareerAgeCross.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] CareerAgeCross.csv: {len(career_age_cross)}件")

        career_age_matrix.to_csv(output_path / 'Phase8_CareerAgeCross_Matrix.csv', index=True, encoding='utf-8-sig')
        print(f"  [OK] CareerAgeCross_Matrix.csv: {career_age_matrix.shape[0]}行 x {career_age_matrix.shape[1]}列")

        if graduation_year_dist is not None and len(graduation_year_dist) > 0:
            graduation_year_dist.to_csv(output_path / 'Phase8_GraduationYearDistribution.csv', index=False, encoding='utf-8-sig')
            print(f"  [OK] GraduationYearDistribution.csv: {len(graduation_year_dist)}件")

        # 4. 品質レポート保存
        self._save_quality_report(combined_df, 8, output_path, mode='inferential')

        report_overall = self.validator_inferential.generate_quality_report(combined_df)
        self.validator_inferential.export_quality_report_csv(report_overall, str(output_path / 'P8_QualityReport.csv'))
        print(f"  [OK] P8_QualityReport.csv")

        print(f"  [OK] Phase 8完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_education_distribution(self, df):
        """キャリア（学歴）分布を生成"""
        if 'career' not in self.df_normalized.columns:
            return pd.DataFrame()

        # キャリア（学歴）データを処理データに追加
        df_with_career = df.copy()
        df_with_career['career'] = self.df_normalized['career'].values

        # 欠損・空文字を除外
        df_with_career = df_with_career[df_with_career['career'].notna() & (df_with_career['career'] != '')]

        if len(df_with_career) == 0:
            return pd.DataFrame()

        # キャリア（学歴）分布
        career_dist = df_with_career.groupby('career').agg({
            'id': 'count',
            'age': 'mean',
            'qualification_count': 'mean'
        }).reset_index()

        career_dist.columns = ['career', 'count', 'avg_age', 'avg_qualifications']

        return career_dist.sort_values('count', ascending=False)

    def _generate_education_age_cross(self, df):
        """キャリア（学歴）×年齢層クロス分析を生成"""
        if 'career' not in self.df_normalized.columns:
            return pd.DataFrame()

        # キャリア（学歴）データを処理データに追加
        df_with_career = df.copy()
        df_with_career['career'] = self.df_normalized['career'].values

        # 欠損・空文字を除外
        df_with_career = df_with_career[df_with_career['career'].notna() & (df_with_career['career'] != '')]

        if len(df_with_career) == 0:
            return pd.DataFrame()

        results = []

        for career in df_with_career['career'].dropna().unique():
            for age_group in df_with_career['age_bucket'].dropna().unique():
                subset = df_with_career[
                    (df_with_career['career'] == career) &
                    (df_with_career['age_bucket'] == age_group)
                ]

                if len(subset) > 0:
                    results.append({
                        'career': career,
                        'age_group': age_group,
                        'count': len(subset),
                        'avg_age': subset['age'].mean(),
                        'avg_qualifications': subset['qualification_count'].mean()
                    })

        return pd.DataFrame(results).sort_values(['career', 'age_group'])

    def _generate_education_age_matrix(self, df):
        """キャリア（学歴）×年齢層クロス集計マトリックスを生成"""
        if 'career' not in self.df_normalized.columns:
            return pd.DataFrame()

        # キャリア（学歴）データを処理データに追加
        df_with_career = df.copy()
        df_with_career['career'] = self.df_normalized['career'].values

        # 欠損・空文字を除外
        df_with_career = df_with_career[df_with_career['career'].notna() & (df_with_career['career'] != '')]

        if len(df_with_career) == 0:
            return pd.DataFrame()

        # クロス集計
        matrix = pd.crosstab(df_with_career['career'], df_with_career['age_bucket'])

        return matrix

    def _generate_graduation_year_distribution(self, df):
        """卒業年分布を生成（career列から抽出）"""
        if 'career' not in self.df_normalized.columns:
            return None

        # career列から卒業年を抽出
        df_with_career = df.copy()
        df_with_career['career'] = self.df_normalized['career'].values

        # 欠損・空文字を除外
        df_with_career = df_with_career[df_with_career['career'].notna() & (df_with_career['career'] != '')]

        if len(df_with_career) == 0:
            return None

        # 卒業年を抽出（例: "1990年3月卒業" → 1990）
        import re
        graduation_years = []
        for idx, row in df_with_career.iterrows():
            career_text = str(row['career'])
            # "YYYY年" パターンを検索
            matches = re.findall(r'(\d{4})年', career_text)
            if matches:
                # 最後に出現する年を卒業年とする
                year = int(matches[-1])
                # 1950-2030の範囲内の年のみ有効
                if 1950 <= year <= 2030:
                    graduation_years.append({
                        'id': row['id'],
                        'graduation_year': year,
                        'age': row['age']
                    })

        if not graduation_years:
            return None

        df_graduation = pd.DataFrame(graduation_years)

        # 卒業年分布
        graduation_dist = df_graduation.groupby('graduation_year').agg({
            'id': 'count',
            'age': 'mean'
        }).reset_index()

        graduation_dist.columns = ['graduation_year', 'count', 'avg_age']

        return graduation_dist.sort_values('graduation_year', ascending=False)

    # ===========================================
    # Phase 10: 転職意欲・緊急度分析
    # ===========================================

    def export_phase10(self, output_dir='data/output_v2/phase10'):
        """Phase 10: 転職意欲・緊急度分析データのエクスポート"""
        print("\n[PHASE10] Phase 10: 転職意欲・緊急度分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        df_with_urgency = self._calculate_urgency_score(self.processed_data)
        urgency_dist = self._generate_urgency_distribution(df_with_urgency)
        urgency_age_cross = self._generate_urgency_age_cross(df_with_urgency)
        urgency_age_matrix = self._generate_urgency_age_matrix(df_with_urgency)
        urgency_employment_cross = self._generate_urgency_employment_cross(df_with_urgency)
        urgency_employment_matrix = self._generate_urgency_employment_matrix(df_with_urgency)
        urgency_by_muni = self._generate_urgency_by_municipality(df_with_urgency)
        urgency_age_muni = self._generate_urgency_age_by_municipality(df_with_urgency)
        urgency_employment_muni = self._generate_urgency_employment_by_municipality(df_with_urgency)
        combined_df = pd.concat([urgency_dist, urgency_age_cross, urgency_employment_cross], ignore_index=True)

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(combined_df, 10, "転職意欲・緊急度分析", mode='inferential')

        if not save_data:
            print(f"  [SKIP] Phase 10をスキップしました")
            return

        # 3. CSV保存
        urgency_dist.to_csv(output_path / 'Phase10_UrgencyDistribution.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] UrgencyDistribution.csv: {len(urgency_dist)}件")

        urgency_age_cross.to_csv(output_path / 'Phase10_UrgencyAgeCross.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] UrgencyAgeCross.csv: {len(urgency_age_cross)}件")

        urgency_age_matrix.to_csv(output_path / 'Phase10_UrgencyAgeCross_Matrix.csv', index=True, encoding='utf-8-sig')
        print(f"  [OK] UrgencyAgeCross_Matrix.csv: {urgency_age_matrix.shape[0]}行 x {urgency_age_matrix.shape[1]}列")

        urgency_employment_cross.to_csv(output_path / 'Phase10_UrgencyEmploymentCross.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] UrgencyEmploymentCross.csv: {len(urgency_employment_cross)}件")

        urgency_employment_matrix.to_csv(output_path / 'Phase10_UrgencyEmploymentCross_Matrix.csv', index=True, encoding='utf-8-sig')
        print(f"  [OK] UrgencyEmploymentCross_Matrix.csv: {urgency_employment_matrix.shape[0]}行 x {urgency_employment_matrix.shape[1]}列")

        urgency_by_muni.to_csv(output_path / 'Phase10_UrgencyByMunicipality.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] UrgencyByMunicipality.csv: {len(urgency_by_muni)}件")

        urgency_age_muni.to_csv(output_path / 'Phase10_UrgencyAgeCross_ByMunicipality.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] UrgencyAgeCross_ByMunicipality.csv: {len(urgency_age_muni)}件")

        urgency_employment_muni.to_csv(output_path / 'Phase10_UrgencyEmploymentCross_ByMunicipality.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] UrgencyEmploymentCross_ByMunicipality.csv: {len(urgency_employment_muni)}件")

        # 4. 品質レポート保存
        self._save_quality_report(combined_df, 10, output_path, mode='inferential')

        report_overall = self.validator_inferential.generate_quality_report(combined_df)
        self.validator_inferential.export_quality_report_csv(report_overall, str(output_path / 'P10_QualityReport.csv'))
        print(f"  [OK] P10_QualityReport.csv")

        print(f"  [OK] Phase 10完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _calculate_urgency_score(self, df):
        """転職意欲・緊急度スコアを算出"""
        df_copy = df.copy()

        # スコアリングロジック
        urgency_scores = []

        for idx, row in df_copy.iterrows():
            score = 0

            # 1. 希望勤務地数（0-3点）
            if row['希望勤務地数'] == 0:
                score += 0
            elif row['希望勤務地数'] <= 2:
                score += 1
            elif row['希望勤務地数'] <= 5:
                score += 2
            else:
                score += 3

            # 2. 資格数（0-2点）
            if row['qualification_count'] >= 3:
                score += 2
            elif row['qualification_count'] >= 1:
                score += 1

            # 3. 国家資格保有（+2点）
            if row['has_national_license']:
                score += 2

            # 4. 就業状態（0-2点）
            if row['employment_status'] == EmploymentStatus.UNEMPLOYED:
                score += 2
            elif row['employment_status'] == EmploymentStatus.EMPLOYED:
                score += 1

            urgency_scores.append(score)

        df_copy['urgency_score'] = urgency_scores

        # スコアランク
        def get_urgency_rank(score):
            if score <= 2:
                return 'D: 低い'
            elif score <= 4:
                return 'C: やや低い'
            elif score <= 6:
                return 'B: 中程度'
            else:
                return 'A: 高い'

        df_copy['urgency_rank'] = df_copy['urgency_score'].apply(get_urgency_rank)

        return df_copy

    def _generate_urgency_distribution(self, df):
        """緊急度分布を生成"""
        urgency_dist = df.groupby('urgency_rank').agg({
            'id': 'count',
            'age': 'mean',
            'urgency_score': 'mean'
        }).reset_index()

        urgency_dist.columns = ['urgency_rank', 'count', 'avg_age', 'avg_urgency_score']

        return urgency_dist.sort_values('avg_urgency_score', ascending=False)

    def _generate_urgency_age_cross(self, df):
        """緊急度×年齢層クロス分析を生成"""
        results = []

        for urgency_rank in df['urgency_rank'].unique():
            for age_group in df['age_bucket'].dropna().unique():
                subset = df[
                    (df['urgency_rank'] == urgency_rank) &
                    (df['age_bucket'] == age_group)
                ]

                if len(subset) > 0:
                    results.append({
                        'urgency_rank': urgency_rank,
                        'age_group': age_group,
                        'count': len(subset),
                        'avg_age': subset['age'].mean(),
                        'avg_urgency_score': subset['urgency_score'].mean()
                    })

        return pd.DataFrame(results).sort_values(['urgency_rank', 'age_group'])

    def _generate_urgency_age_matrix(self, df):
        """緊急度×年齢層クロス集計マトリックスを生成"""
        matrix = pd.crosstab(df['urgency_rank'], df['age_bucket'])
        return matrix

    def _generate_urgency_employment_cross(self, df):
        """緊急度×就業状態クロス分析を生成"""
        results = []

        for urgency_rank in df['urgency_rank'].unique():
            for employment in df['employment_status'].dropna().unique():
                subset = df[
                    (df['urgency_rank'] == urgency_rank) &
                    (df['employment_status'] == employment)
                ]

                if len(subset) > 0:
                    results.append({
                        'urgency_rank': urgency_rank,
                        'employment_status': employment,
                        'count': len(subset),
                        'avg_age': subset['age'].mean(),
                        'avg_urgency_score': subset['urgency_score'].mean()
                    })

        return pd.DataFrame(results).sort_values(['urgency_rank', 'employment_status'])

    def _generate_urgency_employment_matrix(self, df):
        """緊急度×就業状態クロス集計マトリックスを生成"""
        matrix = pd.crosstab(df['urgency_rank'], df['employment_status'])
        return matrix

    def _generate_urgency_by_municipality(self, df):
        """市区町村別緊急度集計を生成"""
        results = []

        for idx, row in df.iterrows():
            for area in row['desired_areas']:
                results.append({
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'],
                    'location': area['full'],
                    'urgency_score': row['urgency_score'],
                    'urgency_rank': row['urgency_rank']
                })

        df_results = pd.DataFrame(results)

        # 集計
        urgency_by_muni = df_results.groupby('location').agg({
            'urgency_score': ['count', 'mean']
        }).reset_index()

        urgency_by_muni.columns = ['location', 'count', 'avg_urgency_score']

        return urgency_by_muni.sort_values('avg_urgency_score', ascending=False)

    def _generate_urgency_age_by_municipality(self, df):
        """市区町村×年齢層別緊急度集計を生成"""
        results = []

        for idx, row in df.iterrows():
            for area in row['desired_areas']:
                results.append({
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'],
                    'location': area['full'],
                    'age_group': row['age_bucket'],
                    'urgency_score': row['urgency_score'],
                    'urgency_rank': row['urgency_rank']
                })

        df_results = pd.DataFrame(results)

        # 集計
        urgency_age_muni = df_results.groupby(['location', 'age_group']).agg({
            'urgency_score': ['count', 'mean']
        }).reset_index()

        urgency_age_muni.columns = ['location', 'age_group', 'count', 'avg_urgency_score']

        return urgency_age_muni.sort_values(['location', 'age_group'])

    def _generate_urgency_employment_by_municipality(self, df):
        """市区町村×就業状態別緊急度集計を生成"""
        results = []

        for idx, row in df.iterrows():
            for area in row['desired_areas']:
                results.append({
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'],
                    'location': area['full'],
                    'employment_status': row['employment_status'],
                    'urgency_score': row['urgency_score'],
                    'urgency_rank': row['urgency_rank']
                })

        df_results = pd.DataFrame(results)

        # 集計
        urgency_employment_muni = df_results.groupby(['location', 'employment_status']).agg({
            'urgency_score': ['count', 'mean']
        }).reset_index()

        urgency_employment_muni.columns = ['location', 'employment_status', 'count', 'avg_urgency_score']

        return urgency_employment_muni.sort_values(['location', 'employment_status'])

    # ===========================================
    # Phase 12: 需給ギャップ分析
    # ===========================================

    def export_phase12(self, output_dir='data/output_v2/phase12'):
        """Phase 12: 需給ギャップ分析のエクスポート"""
        print("\n[PHASE12] Phase 12: 需給ギャップ分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        supply_demand_gap = self._generate_supply_demand_gap()

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(supply_demand_gap, 12, "需給ギャップ分析", mode='descriptive')

        if not save_data:
            print(f"  [SKIP] Phase 12をスキップしました")
            return

        # 3. CSV保存
        supply_demand_gap.to_csv(output_path / 'Phase12_SupplyDemandGap.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] SupplyDemandGap.csv: {len(supply_demand_gap)}件")

        # 4. 品質レポート保存
        self._save_quality_report(supply_demand_gap, 12, output_path, mode='descriptive')

        report = self.validator_descriptive.generate_quality_report(supply_demand_gap)
        self.validator_descriptive.export_quality_report_csv(report, str(output_path / 'P12_QualityReport.csv'))
        print(f"  [OK] P12_QualityReport.csv")

        print(f"  [OK] Phase 12完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_supply_demand_gap(self):
        """需給ギャップ分析データを生成（MAP統合対応）"""

        # 各市町村への需要（希望者数）
        demand_list = []
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                demand_list.append({
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'] if area['municipality'] else '',
                    'location': area['full']
                })

        demand_df = pd.DataFrame(demand_list)
        demand = demand_df.groupby('location').size().reset_index(name='demand_count')

        # 各市町村からの供給（居住者数）
        # 修正: location フォーマットを demand と同じ形式（都道府県+市町村）に統一
        supply_list = []
        for idx, row in self.processed_data.iterrows():
            if row['residence_pref'] and row['residence_muni']:
                location = f"{row['residence_pref']}{row['residence_muni']}"
                supply_list.append({'location': location})

        if supply_list:
            supply_df = pd.DataFrame(supply_list)
            supply = supply_df.groupby('location').size().reset_index(name='supply_count')
        else:
            supply = pd.DataFrame(columns=['location', 'supply_count'])

        # 需給マッチング
        gap = pd.merge(demand, supply, on='location', how='outer').fillna(0)
        gap['demand_supply_ratio'] = gap['demand_count'] / (gap['supply_count'] + 1)
        gap['gap'] = gap['demand_count'] - gap['supply_count']

        # 都道府県・市町村に分割
        gap[['prefecture', 'municipality']] = gap['location'].str.extract(r'^([\u4e00-\u9fff]{2,3}[都道府県])(.*)')
        gap['municipality'] = gap['municipality'].fillna('')

        # 座標を追加（MAP統合用）
        gap['latitude'] = None
        gap['longitude'] = None

        for idx, row in gap.iterrows():
            location_key = row['location']
            if location_key in self.municipality_coords:
                lat, lon = self.municipality_coords[location_key]
                gap.at[idx, 'latitude'] = lat
                gap.at[idx, 'longitude'] = lon
            elif location_key in self.geocache:
                cache_data = self.geocache[location_key]
                gap.at[idx, 'latitude'] = cache_data.get('lat')
                gap.at[idx, 'longitude'] = cache_data.get('lng')

        # カラム順序を整理（MAP統合に適した形式）
        gap = gap[['prefecture', 'municipality', 'location', 'demand_count', 'supply_count',
                   'demand_supply_ratio', 'gap', 'latitude', 'longitude']]

        return gap.sort_values('demand_supply_ratio', ascending=False)

    # ===========================================
    # Phase 13: 希少性スコア
    # ===========================================

    def export_phase13(self, output_dir='data/output_v2/phase13'):
        """Phase 13: 希少性スコアのエクスポート"""
        print("\n[PHASE13] Phase 13: 希少性スコア")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        rarity_score = self._generate_rarity_score()

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(rarity_score, 13, "希少性スコア", mode='descriptive')

        if not save_data:
            print(f"  [SKIP] Phase 13をスキップしました")
            return

        # 3. CSV保存
        rarity_score.to_csv(output_path / 'Phase13_RarityScore.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] RarityScore.csv: {len(rarity_score)}件")

        # 4. 品質レポート保存
        self._save_quality_report(rarity_score, 13, output_path, mode='descriptive')

        report = self.validator_descriptive.generate_quality_report(rarity_score)
        self.validator_descriptive.export_quality_report_csv(report, str(output_path / 'P13_QualityReport.csv'))
        print(f"  [OK] P13_QualityReport.csv")

        print(f"  [OK] Phase 13完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_rarity_score(self):
        """希少性スコアを生成（MAP統合対応）"""

        # 希望勤務地を展開
        desired_list = []
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                desired_list.append({
                    'location': area['full'],
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'] if area['municipality'] else '',
                    'age_bucket': row['age_bucket'],
                    'gender': row['gender'],
                    'has_national_license': row['has_national_license']
                })

        desired_df = pd.DataFrame(desired_list)

        # 市町村 × 年齢層 × 性別 × 国家資格でグループ化
        rarity = desired_df.groupby(['location', 'prefecture', 'municipality',
                                       'age_bucket', 'gender', 'has_national_license']).size().reset_index(name='count')

        # 希少性スコア = 1 / count
        rarity['rarity_score'] = 1 / rarity['count']

        # ランク付け
        def get_rarity_rank(score):
            if score >= 1.0:
                return 'S: 超希少（1人のみ）'
            elif score >= 0.5:
                return 'A: 非常に希少（2人）'
            elif score >= 0.2:
                return 'B: 希少（3-5人）'
            elif score >= 0.05:
                return 'C: やや希少（6-20人）'
            else:
                return 'D: 一般的（20人超）'

        rarity['rarity_rank'] = rarity['rarity_score'].apply(get_rarity_rank)

        # 座標を追加（MAP統合用）
        rarity['latitude'] = None
        rarity['longitude'] = None

        for idx, row in rarity.iterrows():
            location_key = row['location']
            if location_key in self.municipality_coords:
                lat, lon = self.municipality_coords[location_key]
                rarity.at[idx, 'latitude'] = lat
                rarity.at[idx, 'longitude'] = lon
            elif location_key in self.geocache:
                cache_data = self.geocache[location_key]
                rarity.at[idx, 'latitude'] = cache_data.get('lat')
                rarity.at[idx, 'longitude'] = cache_data.get('lng')

        # カラム順序を整理
        rarity = rarity[['prefecture', 'municipality', 'location', 'age_bucket', 'gender',
                         'has_national_license', 'count', 'rarity_score', 'rarity_rank',
                         'latitude', 'longitude']]

        return rarity.sort_values('rarity_score', ascending=False)

    # ===========================================
    # Phase 14: 競合分析
    # ===========================================

    def export_phase14(self, output_dir='data/output_v2/phase14'):
        """Phase 14: 競合分析のエクスポート"""
        print("\n[PHASE14] Phase 14: 競合分析")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. データ生成
        competition_profile = self._generate_competition_profile()

        # 2. 品質ゲートチェック
        save_data, quality_score = self._check_quality_gate(competition_profile, 14, "競合分析", mode='descriptive')

        if not save_data:
            print(f"  [SKIP] Phase 14をスキップしました")
            return

        # 3. CSV保存
        competition_profile.to_csv(output_path / 'Phase14_CompetitionProfile.csv', index=False, encoding='utf-8-sig')
        print(f"  [OK] CompetitionProfile.csv: {len(competition_profile)}件")

        # 4. 品質レポート保存
        self._save_quality_report(competition_profile, 14, output_path, mode='descriptive')

        report = self.validator_descriptive.generate_quality_report(competition_profile)
        self.validator_descriptive.export_quality_report_csv(report, str(output_path / 'P14_QualityReport.csv'))
        print(f"  [OK] P14_QualityReport.csv")

        print(f"  [OK] Phase 14完了（品質スコア: {quality_score:.1f}/100）")
        print(f"  [DIR] 出力先: {output_path}")

    def _generate_competition_profile(self):
        """競合分析データを生成（MAP統合対応）"""

        # 希望勤務地を展開
        desired_list = []
        for idx, row in self.processed_data.iterrows():
            for area in row['desired_areas']:
                desired_list.append({
                    'location': area['full'],
                    'prefecture': area['prefecture'],
                    'municipality': area['municipality'] if area['municipality'] else '',
                    'age_bucket': row['age_bucket'],
                    'gender': row['gender'],
                    'has_national_license': row['has_national_license'],
                    'employment_status': row['employment_status'],
                    'qualification_count': row['qualification_count']
                })

        desired_df = pd.DataFrame(desired_list)

        # 市町村ごとに集計
        results = []

        for location in desired_df['location'].unique():
            muni_data = desired_df[desired_df['location'] == location]

            if len(muni_data) == 0:
                continue

            # 基本統計
            total_count = len(muni_data)

            # 年齢層分布（最も多い年齢層）
            age_dist = muni_data['age_bucket'].value_counts()
            top_age = age_dist.index[0] if len(age_dist) > 0 else None
            top_age_count = age_dist.iloc[0] if len(age_dist) > 0 else 0
            top_age_ratio = top_age_count / total_count if total_count > 0 else 0

            # 性別分布
            gender_dist = muni_data['gender'].value_counts()
            female_count = gender_dist.get('女性', 0)
            male_count = gender_dist.get('男性', 0)
            female_ratio = female_count / total_count if total_count > 0 else 0

            # 国家資格保有率
            national_license_rate = muni_data['has_national_license'].mean()

            # 就業状態分布（最も多い状態）
            emp_dist = muni_data['employment_status'].value_counts()
            top_employment = emp_dist.index[0] if len(emp_dist) > 0 else None
            top_employment_count = emp_dist.iloc[0] if len(emp_dist) > 0 else 0
            top_employment_ratio = top_employment_count / total_count if total_count > 0 else 0

            # 平均資格数
            avg_qualification = muni_data['qualification_count'].mean()

            # 都道府県・市町村
            prefecture = muni_data['prefecture'].iloc[0] if len(muni_data) > 0 else ''
            municipality = muni_data['municipality'].iloc[0] if len(muni_data) > 0 else ''

            results.append({
                'prefecture': prefecture,
                'municipality': municipality,
                'location': location,
                'total_applicants': total_count,
                'top_age_group': top_age,
                'top_age_ratio': top_age_ratio,
                'female_ratio': female_ratio,
                'male_ratio': 1 - female_ratio,
                'national_license_rate': national_license_rate,
                'top_employment_status': top_employment,
                'top_employment_ratio': top_employment_ratio,
                'avg_qualification_count': avg_qualification
            })

        competition_df = pd.DataFrame(results)

        # 座標を追加（MAP統合用）
        competition_df['latitude'] = None
        competition_df['longitude'] = None

        for idx, row in competition_df.iterrows():
            location_key = row['location']
            if location_key in self.municipality_coords:
                lat, lon = self.municipality_coords[location_key]
                competition_df.at[idx, 'latitude'] = lat
                competition_df.at[idx, 'longitude'] = lon
            elif location_key in self.geocache:
                cache_data = self.geocache[location_key]
                competition_df.at[idx, 'latitude'] = cache_data.get('lat')
                competition_df.at[idx, 'longitude'] = cache_data.get('lng')

        # カラム順序を整理
        competition_df = competition_df[['prefecture', 'municipality', 'location', 'total_applicants',
                                         'top_age_group', 'top_age_ratio', 'female_ratio', 'male_ratio',
                                         'national_license_rate', 'top_employment_status', 'top_employment_ratio',
                                         'avg_qualification_count', 'latitude', 'longitude']]

        return competition_df.sort_values('total_applicants', ascending=False)

    # ===========================================
    # 統合品質レポート生成
    # ===========================================

    def generate_overall_quality_report(self):
        """統合品質レポートを生成"""
        print("\n[OVERALL] 統合品質レポート生成")

        # 全PhaseのCSVファイルを収集
        all_csvs = []
        output_base = Path('data/output_v2')

        for phase_dir in output_base.glob('phase*'):
            for csv_file in phase_dir.glob('*.csv'):
                if 'QualityReport' not in csv_file.name:
                    try:
                        df = pd.read_csv(csv_file, encoding='utf-8-sig')
                        all_csvs.append(df)
                    except Exception as e:
                        print(f"  [警告] {csv_file.name}の読み込みに失敗: {e}")

        if not all_csvs:
            print("  [警告] 統合対象のCSVファイルが見つかりませんでした")
            return

        # 統合DataFrame
        combined_df = pd.concat(all_csvs, ignore_index=True)

        # 統合品質レポート生成
        report = self.validator_inferential.generate_quality_report(combined_df)
        self.validator_inferential.export_quality_report_csv(report, str(output_base / 'OverallQualityReport_Inferential.csv'))
        print(f"  [OK] OverallQualityReport_Inferential.csv")

        # 記述統計用統合レポート
        report_descriptive = self.validator_descriptive.generate_quality_report(combined_df)
        self.validator_descriptive.export_quality_report_csv(report_descriptive, str(output_base / 'OverallQualityReport.csv'))
        print(f"  [OK] OverallQualityReport.csv")

        print(f"  [DIR] 出力先: {output_base}")


# メイン実行
if __name__ == "__main__":
    print("=" * 80)
    print("ジョブメドレー求職者データ分析 v2.2 - MAP統合版")
    print("Phase 1-3, 6-8, 10, 12-14の全実装（品質検証統合 + MAP統合対応）")
    print("=" * 80)
    print()

    # CSVファイル選択（GUI）
    root = tk.Tk()
    root.withdraw()
    csv_path = filedialog.askopenfilename(
        title="CSVファイルを選択",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialdir=r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out"
    )
    root.destroy()

    if not csv_path:
        print("ファイルが選択されませんでした")
        sys.exit(1)

    print(f"選択されたファイル: {csv_path}")
    print()

    # 完璧版アナライザーを使用
    analyzer = PerfectJobSeekerAnalyzer(csv_path)
    analyzer.load_data()
    analyzer.process_data()

    # Phase 1-10実行
    analyzer.export_phase1()
    analyzer.export_phase2()
    analyzer.export_phase3()
    analyzer.export_phase6()
    analyzer.export_phase7()
    analyzer.export_phase8()
    analyzer.export_phase10()

    # Phase 12-14実行（MAP統合対応）
    analyzer.export_phase12()
    analyzer.export_phase13()
    analyzer.export_phase14()

    # 統合品質レポート
    analyzer.generate_overall_quality_report()

    print()
    print("=" * 80)
    print("全フェーズ完了✅")
    print("=" * 80)
    print()
    print("出力先:")
    print("  - data/output_v2/phase1/ (6ファイル)")
    print("  - data/output_v2/phase2/ (3ファイル)")
    print("  - data/output_v2/phase3/ (3ファイル)")
    print("  - data/output_v2/phase6/ (4ファイル)")
    print("  - data/output_v2/phase7/ (6ファイル)")
    print("  - data/output_v2/phase8/ (6ファイル)")
    print("  - data/output_v2/phase10/ (10ファイル)")
    print("  - data/output_v2/phase12/ (2ファイル) 🆕")
    print("  - data/output_v2/phase13/ (2ファイル) 🆕")
    print("  - data/output_v2/phase14/ (2ファイル) 🆕")
    print("  - data/output_v2/ (統合品質レポート2ファイル)")
    print()
    print("合計: 46ファイル | Phase 12-14追加（MAP統合対応）")