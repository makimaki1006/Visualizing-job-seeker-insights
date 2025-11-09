"""
データ正規化モジュール
新しいCSV形式（results_*.csv）の表記ゆれを正規化
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from config import MISSING_VALUE_POLICY


class DataNormalizer:
    """
    データ正規化クラス
    各カラムの表記ゆれを統一し、分析可能な形式に変換
    """

    def __init__(self):
        """初期化"""
        pass

    # ========================================
    # 1. age_gender（年齢・性別）の分離
    # ========================================

    def parse_age_gender(self, age_gender_str: str) -> Dict[str, Optional[int]]:
        """
        年齢・性別を分離

        Args:
            age_gender_str: "49歳 女性" 形式の文字列

        Returns:
            {'age': 49, 'gender': '女性'}
        """
        if pd.isna(age_gender_str) or age_gender_str.strip() == '':
            return {'age': None, 'gender': None}

        # 正規表現で抽出
        match = re.search(r'(\d+)歳\s*(男性|女性)', age_gender_str)
        if match:
            return {
                'age': int(match.group(1)),
                'gender': match.group(2)
            }

        return {'age': None, 'gender': None}

    # ========================================
    # 2. location（居住地）の分離
    # ========================================

    def parse_location(self, location_str: str) -> Dict[str, Optional[str]]:
        """
        居住地を都道府県と市区町村に分離

        Args:
            location_str: "京都府京都市上京区" 形式の文字列

        Returns:
            {'prefecture': '京都府', 'municipality': '京都市上京区'}
        """
        if pd.isna(location_str) or location_str.strip() == '':
            return {'prefecture': None, 'municipality': None}

        # 都道府県を抽出（修正版：優先順位付き検索）
        # 「京都府」のような場合も正しく抽出するため、「府」「道」を優先
        # 優先順位: 道（北海道） > 府（京都府、大阪府） > 都（東京都） > 県（その他）
        for suffix in ['道', '府', '都', '県']:
            index = location_str.find(suffix)
            if index != -1:
                prefecture = location_str[:index+1]
                municipality = location_str[index+1:].strip()
                return {
                    'prefecture': prefecture,
                    'municipality': municipality if municipality else None
                }

        # 都道府県が見つからない場合
        return {'prefecture': None, 'municipality': location_str}

    # ========================================
    # 3. desired_area（希望勤務地）の展開
    # ========================================

    def parse_desired_area(self, desired_area_str: str) -> List[Dict[str, str]]:
        """
        希望勤務地をカンマ区切りで分割し、各地域を都道府県と市区町村に分離

        Args:
            desired_area_str: "奈良県奈良市,京都府木津川市" 形式の文字列

        Returns:
            [
                {'prefecture': '奈良県', 'municipality': '奈良市'},
                {'prefecture': '京都府', 'municipality': '木津川市'}
            ]
        """
        if pd.isna(desired_area_str) or desired_area_str.strip() == '':
            return []

        # "なし" の場合
        if desired_area_str.strip().lower() == 'なし':
            return []

        areas = []
        for area in desired_area_str.split(','):
            area = area.strip()
            if area:
                parsed = self.parse_location(area)
                areas.append(parsed)

        return areas

    # ========================================
    # 4. desired_job（希望職種）のパース
    # ========================================

    def parse_desired_jobs(self, job_str: str) -> List[Dict[str, Optional[str]]]:
        """
        希望職種を職種名と経験年数に分離

        Args:
            job_str: "介護職/ヘルパー (10年以上),生活支援員 (2年未満)" 形式

        Returns:
            [
                {'job_name': '介護職/ヘルパー', 'experience_text': '10年以上', 'experience_years': 10},
                {'job_name': '生活支援員', 'experience_text': '2年未満', 'experience_years': 2}
            ]
        """
        if pd.isna(job_str) or job_str.strip() == '':
            return []

        jobs = []
        for job in job_str.split(','):
            job = job.strip()

            # 経験年数抽出
            exp_match = re.search(r'\(([^)]+)\)$', job)
            if exp_match:
                experience_text = exp_match.group(1)
                job_name = job[:exp_match.start()].strip()
            else:
                experience_text = None
                job_name = job

            # 経験年数を数値化
            exp_years = self._parse_experience_years(experience_text)

            jobs.append({
                'job_name': job_name,
                'experience_text': experience_text,
                'experience_years': exp_years
            })

        return jobs

    def _parse_experience_years(self, experience_text: Optional[str]) -> Optional[int]:
        """
        経験年数テキストを数値に変換

        Args:
            experience_text: "10年以上", "5年未満", "未経験" など

        Returns:
            数値（年数）または None
        """
        if not experience_text:
            return None

        if '未経験' in experience_text:
            return 0

        if '10年以上' in experience_text:
            return 10

        # "N年未満" または "N年"
        num_match = re.search(r'(\d+)年', experience_text)
        if num_match:
            return int(num_match.group(1))

        return None

    # ========================================
    # 5. qualifications（資格）のパース
    # ========================================

    def parse_qualifications(self, qual_str: str) -> List[Dict[str, str]]:
        """
        資格をカンマ区切りで分割し、正規化

        Args:
            qual_str: "介護福祉士,自動車運転免許,その他（喀痰吸引）" 形式

        Returns:
            [
                {'name': '介護福祉士', 'category': '国家資格', 'is_planned': False},
                {'name': '自動車運転免許', 'category': '免許', 'is_planned': False}
            ]
        """
        if pd.isna(qual_str) or qual_str.strip() == '':
            return []

        quals = []
        for qual in qual_str.split(','):
            qual = qual.strip()

            # "取得予定" を分離
            is_planned = '取得予定' in qual
            qual_name = re.sub(r'\s*取得予定.*$', '', qual).strip()

            # カテゴリ分類
            category = self._categorize_qualification(qual_name)

            quals.append({
                'name': qual_name,
                'category': category,
                'is_planned': is_planned
            })

        return quals

    def _categorize_qualification(self, qual_name: str) -> str:
        """
        資格をカテゴリ分類

        Args:
            qual_name: 資格名

        Returns:
            カテゴリ名
        """
        if '介護福祉士' in qual_name:
            return '国家資格'
        elif 'ケアマネ' in qual_name or '介護支援専門員' in qual_name:
            return '専門資格'
        elif '実務者研修' in qual_name or '初任者研修' in qual_name:
            return '介護研修'
        elif '自動車' in qual_name or '運転免許' in qual_name:
            return '免許'
        elif '看護' in qual_name or '准看護' in qual_name:
            return '医療資格'
        elif 'その他' in qual_name:
            return 'その他'
        else:
            return '専門資格'

    # ========================================
    # 6. career（学歴）のパース
    # ========================================

    def parse_career(self, career_str: str) -> Dict[str, Optional[str]]:
        """
        学歴情報を抽出（改善版：複数学歴対応、在学中対応、パターン拡充）

        Args:
            career_str: "ライフクリエイト科(高等学校)(2016年4月卒業)" 形式
                       または複数学歴: "経済学部(大学)(2020年3月卒業)、○○科(高校)(2016年3月卒業)"

        Returns:
            {
                'level': '高校',              # 最高学歴レベル
                'field': 'ライフクリエイト科', # 学部・学科
                'grad_year': 2016,           # 卒業年度
                'is_current': False,         # 在学中かどうか
                'all_levels': ['大学', '高校'] # すべての学歴レベル（優先順）
            }
        """
        if pd.isna(career_str) or career_str.strip() == '':
            return {
                'level': 'なし',
                'field': None,
                'grad_year': None,
                'is_current': False,
                'all_levels': []
            }

        # 複数学歴が「、」で区切られている場合は分割
        career_entries = [entry.strip() for entry in career_str.split('、') if entry.strip()]

        # 学歴レベル優先順位マップ（高い順）
        level_priority = {
            '大学院': 7,
            '大学': 6,
            '短大': 5,
            '短期大学': 5,
            '高専': 4,
            '高等専門学校': 4,
            '専門': 3,
            '専門学校': 3,
            '高校': 2,
            '高等学校': 2,
            '中学': 1,
            '中学校': 1,
            'その他': 0
        }

        all_parsed = []

        for entry in career_entries:
            # 学歴レベル抽出（優先順位付き）
            level = 'その他'
            max_priority = 0

            # すべてのキーワードをチェック
            for keyword, priority in level_priority.items():
                if keyword in entry:
                    if priority > max_priority:
                        level = self._normalize_education_level(keyword)
                        max_priority = priority

            # 学部・学科抽出（最初の括弧の前まで）
            field_match = re.search(r'^([^(（]+)(?=[（(])', entry)
            field = field_match.group(1).strip() if field_match else None

            # 卒業年度抽出（複数パターン対応）
            # パターン1: "2016年4月卒業" / "2016年3月卒業"
            year_match = re.search(r'(\d{4})年(\d{1,2})月卒業', entry)
            # パターン2: "2016年卒" / "2016卒"
            if not year_match:
                year_match = re.search(r'(\d{4})年?卒', entry)
            # パターン3: "2016/03卒業"
            if not year_match:
                year_match = re.search(r'(\d{4})/\d{1,2}\s*卒業', entry)

            grad_year = int(year_match.group(1)) if year_match else None

            # 在学中判定
            is_current = '在学中' in entry or '在学' in entry or '中退' in entry

            all_parsed.append({
                'level': level,
                'field': field,
                'grad_year': grad_year,
                'is_current': is_current,
                'priority': max_priority
            })

        # 最高学歴を選択（優先順位が最も高いもの）
        if all_parsed:
            best_education = max(all_parsed, key=lambda x: x['priority'])

            return {
                'level': best_education['level'],
                'field': best_education['field'],
                'grad_year': best_education['grad_year'],
                'is_current': best_education['is_current'],
                'all_levels': [item['level'] for item in sorted(all_parsed, key=lambda x: -x['priority'])]
            }
        else:
            return {
                'level': 'その他',
                'field': None,
                'grad_year': None,
                'is_current': False,
                'all_levels': []
            }

    def _normalize_education_level(self, keyword: str) -> str:
        """学歴レベルキーワードを標準形式に正規化"""
        if '大学院' in keyword:
            return '大学院'
        elif '大学' in keyword:
            return '大学'
        elif '短期大学' in keyword or '短大' in keyword:
            return '短大'
        elif '高等専門学校' in keyword or '高専' in keyword:
            return '高専'
        elif '専門学校' in keyword or '専門' in keyword:
            return '専門'
        elif '高等学校' in keyword or '高校' in keyword:
            return '高校'
        elif '中学' in keyword:
            return '中学'
        else:
            return 'その他'

    # ========================================
    # 7. desired_start（転職時期）のパース
    # ========================================

    def parse_desired_start(self, start_str: str, reference_date: Optional[datetime] = None) -> Dict[str, any]:
        """
        転職時期を緊急度スコアに変換（日付活用、動的スコアリング）

        Args:
            start_str: "今すぐに（2025/10/16時点）" 形式
            reference_date: 基準日（デフォルト: 実行時の現在日時）

        Returns:
            {
                'urgency_score': 5,           # 基本スコア（1-5）
                'urgency_score_dynamic': 5.0, # 動的スコア（日付考慮、0.0-5.0）
                'text': '今すぐに',
                'date': '2025-10-16',
                'days_elapsed': 12            # 経過日数（基準日からの差分）
            }
        """
        if pd.isna(start_str) or start_str.strip() == '':
            return {
                'urgency_score': 0,
                'urgency_score_dynamic': 0.0,
                'text': None,
                'date': None,
                'days_elapsed': None
            }

        # 基準日（指定されない場合は現在日時）
        if reference_date is None:
            reference_date = datetime.now()

        # 緊急度スコア（1-5）
        if '今すぐ' in start_str:
            urgency = 5
        elif '1ヶ月以内' in start_str:
            urgency = 4
        elif '3ヶ月以内' in start_str:
            urgency = 3
        elif '3ヶ月以上先' in start_str:
            urgency = 2
        elif '機会があれば' in start_str:
            urgency = 1
        else:
            # 未知のパターンはurgency=0とする（NaNとは区別）
            urgency = 0

        # テキスト抽出（括弧の前まで）
        text_match = re.search(r'^([^（(]+)', start_str)
        text = text_match.group(1).strip() if text_match else start_str

        # 日付抽出
        date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', start_str)
        date_str = None
        days_elapsed = None
        urgency_dynamic = float(urgency)  # デフォルトは基本スコアと同じ

        if date_match:
            date_str = f"{date_match.group(1)}-{date_match.group(2):0>2}-{date_match.group(3):0>2}"

            # 経過日数を計算
            try:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                days_elapsed = (reference_date - parsed_date).days

                # 動的スコアリング（経過日数に応じて減衰）
                if urgency >= 1:  # 「機会があれば」以上の場合のみ動的調整
                    # 経過日数に応じてスコアを減衰
                    # 30日で0.5減少、90日で1.5減少、180日で3.0減少
                    decay_factor = days_elapsed / 60.0  # 60日で1.0減少
                    urgency_dynamic = max(1.0, float(urgency) - decay_factor)

            except ValueError:
                # 日付パースに失敗した場合は動的スコアは基本スコアと同じ
                pass

        return {
            'urgency_score': urgency,
            'urgency_score_dynamic': round(urgency_dynamic, 2),
            'text': text,
            'date': date_str,
            'days_elapsed': days_elapsed
        }

    # ========================================
    # 8. 外れ値処理
    # ========================================

    def cap_desired_location_count(self, count: int, max_count: int = 50) -> int:
        """
        希望勤務地数の上限設定

        Args:
            count: 元の希望勤務地数
            max_count: 上限値（デフォルト: 50）

        Returns:
            上限適用後の希望勤務地数
        """
        return min(count, max_count)

    # ========================================
    # 9. 欠損値処理
    # ========================================

    def apply_missing_value_policy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        欠損値処理ポリシーを適用

        Args:
            df: 処理対象のDataFrame

        Returns:
            欠損値処理済みのDataFrame
        """
        df_processed = df.copy()

        for column, fill_value in MISSING_VALUE_POLICY.items():
            if column in df_processed.columns:
                # リスト型の場合は個別処理（fillna()では使えない）
                if isinstance(fill_value, list):
                    # 欠損値のインデックスを取得
                    mask = df_processed[column].isna()
                    # 欠損値を空リストのコピーに置換（元のリストを変更しないため）
                    df_processed.loc[mask, column] = df_processed.loc[mask, column].apply(
                        lambda x: fill_value.copy() if pd.isna(x) else x
                    )
                # スカラー値の場合はfillna()を使用
                elif fill_value is not None:
                    df_processed[column] = df_processed[column].fillna(fill_value)
                # Noneの場合は欠損値をそのまま維持（何もしない）

        return df_processed

    # ========================================
    # 9. 定数ベースの正規化メソッド
    # ========================================

    def normalize_employment_status(self, status_str: str) -> Optional[str]:
        """
        就業状態を正規化（constants.pyのEmploymentStatusを使用）

        Args:
            status_str: 元の就業状態文字列

        Returns:
            正規化された就業状態（'就業中', '離職中', '在学中'）
            認識できない場合は None

        Examples:
            >>> normalizer.normalize_employment_status('在職中')
            '就業中'
            >>> normalizer.normalize_employment_status('退職済み')
            '離職中'
        """
        try:
            from constants import EmploymentStatus
            return EmploymentStatus.normalize(status_str)
        except ImportError:
            # constants.pyがない場合のフォールバック
            if pd.isna(status_str):
                return None

            status_clean = status_str.strip()

            # 就業中のバリエーション
            if status_clean in ['就業中', '在職中']:
                return '就業中'

            # 離職中のバリエーション
            if status_clean in ['離職中', '退職済み', '無職']:
                return '離職中'

            # 在学中のバリエーション
            if status_clean in ['在学中', '学生']:
                return '在学中'

            return None

    def normalize_education(self, education_str: str) -> Optional[str]:
        """
        学歴を正規化（constants.pyのEducationLevelを使用）

        Args:
            education_str: 元の学歴文字列

        Returns:
            正規化された学歴レベル
            認識できない場合は None

        Examples:
            >>> normalizer.normalize_education('大学卒')
            '大学'
            >>> normalizer.normalize_education('専門')
            '専門学校'
        """
        try:
            from constants import EducationLevel
            return EducationLevel.normalize(education_str)
        except ImportError:
            # constants.pyがない場合のフォールバック
            if pd.isna(education_str):
                return None

            education_clean = education_str.strip()

            if any(keyword in education_clean for keyword in ['大学院', '修士', '博士']):
                return '大学院'

            if any(keyword in education_clean for keyword in ['大学', '大卒']):
                return '大学'

            if any(keyword in education_clean for keyword in ['専門学校', '専門']):
                return '専門学校'

            if any(keyword in education_clean for keyword in ['高等学校', '高校', '高卒']):
                return '高等学校'

            return None

    def normalize_gender(self, gender_str: str) -> Optional[str]:
        """
        性別を正規化（constants.pyのGenderを使用）

        Args:
            gender_str: 元の性別文字列

        Returns:
            正規化された性別（'男性', '女性', 'その他'）
            認識できない場合は None

        Examples:
            >>> normalizer.normalize_gender('男')
            '男性'
            >>> normalizer.normalize_gender('女')
            '女性'
        """
        try:
            from constants import Gender
            return Gender.normalize(gender_str)
        except ImportError:
            # constants.pyがない場合のフォールバック
            if pd.isna(gender_str):
                return None

            gender_clean = gender_str.strip()

            if gender_clean in ['男性', '男']:
                return '男性'

            if gender_clean in ['女性', '女']:
                return '女性'

            return 'その他'

    # ========================================
    # 10. 統合正規化メソッド
    # ========================================

    def normalize_dataframe(self, df: pd.DataFrame, cap_desired_locations: bool = True,
                          max_desired_locations: int = 50, apply_missing_policy: bool = True,
                          verbose: bool = True) -> pd.DataFrame:
        """
        DataFrameの全カラムを正規化

        Args:
            df: 元のDataFrame
            cap_desired_locations: 希望勤務地数の上限設定を行うか（デフォルト: True）
            max_desired_locations: 希望勤務地数の上限値（デフォルト: 50）
            apply_missing_policy: 欠損値処理ポリシーを適用するか（デフォルト: True）
            verbose: 詳細ログを出力するか（デフォルト: True）

        Returns:
            正規化されたDataFrame
        """
        df_normalized = df.copy()
        total_rows = len(df)

        if verbose:
            print("  [データ正規化] 詳細ログ")

        # age_gender分離
        if 'age_gender' in df.columns:
            age_gender_parsed = df['age_gender'].apply(self.parse_age_gender)
            df_normalized['age'] = age_gender_parsed.apply(lambda x: x['age'])
            df_normalized['gender'] = age_gender_parsed.apply(lambda x: x['gender'])

            if verbose:
                success_count = df_normalized['age'].notna().sum()
                fail_count = df_normalized['age'].isna().sum()
                print(f"    age_gender分離: 成功 {success_count}件 / 失敗 {fail_count}件 / 全体 {total_rows}件")

        # location分離
        if 'location' in df.columns:
            location_parsed = df['location'].apply(self.parse_location)
            df_normalized['residence_pref'] = location_parsed.apply(lambda x: x['prefecture'])
            df_normalized['residence_muni'] = location_parsed.apply(lambda x: x['municipality'])

            if verbose:
                success_count = df_normalized['residence_pref'].notna().sum()
                fail_count = df_normalized['residence_pref'].isna().sum()
                print(f"    location分離: 成功 {success_count}件 / 失敗 {fail_count}件 / 全体 {total_rows}件")

        # desired_start正規化（改善版：動的スコアリング対応）
        if 'desired_start' in df.columns:
            start_parsed = df['desired_start'].apply(self.parse_desired_start)
            df_normalized['urgency_score'] = start_parsed.apply(lambda x: x['urgency_score'])
            df_normalized['urgency_score_dynamic'] = start_parsed.apply(lambda x: x['urgency_score_dynamic'])
            df_normalized['desired_start_text'] = start_parsed.apply(lambda x: x['text'])
            df_normalized['desired_start_date'] = start_parsed.apply(lambda x: x['date'])
            df_normalized['days_elapsed'] = start_parsed.apply(lambda x: x['days_elapsed'])

            if verbose:
                success_count = df_normalized['urgency_score'].gt(0).sum()
                fail_count = df_normalized['urgency_score'].eq(0).sum()
                print(f"    desired_start正規化: 成功 {success_count}件 / 未記載/不明 {fail_count}件 / 全体 {total_rows}件")

        # career正規化（改善版：複数学歴対応、在学中フラグ）
        if 'career' in df.columns:
            career_parsed = df['career'].apply(self.parse_career)
            df_normalized['education_level'] = career_parsed.apply(lambda x: x['level'])
            df_normalized['education_field'] = career_parsed.apply(lambda x: x['field'])
            df_normalized['graduation_year'] = career_parsed.apply(lambda x: x['grad_year'])
            df_normalized['is_currently_enrolled'] = career_parsed.apply(lambda x: x['is_current'])
            df_normalized['all_education_levels'] = career_parsed.apply(lambda x: ','.join(x['all_levels']) if x['all_levels'] else None)

            if verbose:
                success_count = df_normalized['education_level'].ne('なし').sum()
                fail_count = df_normalized['education_level'].eq('なし').sum()
                current_count = df_normalized['is_currently_enrolled'].sum()
                multi_education_count = df_normalized['all_education_levels'].str.contains(',', na=False).sum()
                print(f"    career正規化: 成功 {success_count}件 / なし {fail_count}件 / 全体 {total_rows}件")
                print(f"                  在学中 {current_count}件 / 複数学歴 {multi_education_count}件")

        # employment_status正規化（新規追加）
        if 'employment_status' in df.columns:
            df_normalized['employment_status'] = df['employment_status'].apply(self.normalize_employment_status)

            if verbose:
                success_count = df_normalized['employment_status'].notna().sum()
                fail_count = df_normalized['employment_status'].isna().sum()
                employed_count = (df_normalized['employment_status'] == '就業中').sum()
                unemployed_count = (df_normalized['employment_status'] == '離職中').sum()
                enrolled_count = (df_normalized['employment_status'] == '在学中').sum()
                print(f"    employment_status正規化: 成功 {success_count}件 / 失敗 {fail_count}件 / 全体 {total_rows}件")
                print(f"                            就業中 {employed_count}件 / 離職中 {unemployed_count}件 / 在学中 {enrolled_count}件")

        # 希望勤務地数の計算と上限設定
        if 'desired_area' in df.columns and cap_desired_locations:
            raw_counts = df['desired_area'].apply(
                lambda x: len(str(x).split(',')) if pd.notna(x) and str(x).strip() != '' else 0
            )
            df_normalized['希望勤務地数_raw'] = raw_counts  # 元の値を保持
            df_normalized['希望勤務地数'] = raw_counts.apply(
                lambda x: self.cap_desired_location_count(x, max_desired_locations)
            )

            # 上限適用件数をログ出力
            capped_count = (raw_counts > max_desired_locations).sum()
            if capped_count > 0:
                print(f"  [INFO] 希望勤務地数の上限適用: {capped_count}件（上限: {max_desired_locations}箇所）")

        # 欠損値処理ポリシーの適用
        if apply_missing_policy:
            df_normalized = self.apply_missing_value_policy(df_normalized)

        return df_normalized
