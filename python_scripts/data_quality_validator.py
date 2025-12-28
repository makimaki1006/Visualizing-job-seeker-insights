"""
データ品質検証モジュール
サンプルサイズ、欠損率、統計的信頼性を評価
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class DataQualityValidator:
    """
    データ品質検証クラス
    統計的に信頼できるかを判定

    検証モード:
    - 'inferential': 推論的考察用（統計的信頼性を重視）
    - 'descriptive': 観察的記述用（入力整合性のみ検証）
    """

    def __init__(self, validation_mode: str = 'inferential'):
        """
        初期化

        Args:
            validation_mode: 'inferential'（推論的考察）または 'descriptive'（観察的記述）
        """
        self.validation_mode = validation_mode

        # 最小サンプルサイズの基準（推論的考察用）
        self.MIN_SAMPLE_TOTAL = 100  # 全体最小件数
        self.MIN_SAMPLE_GROUP = 30   # グループ最小件数
        self.MIN_SAMPLE_CROSS = 5    # クロス集計セル最小件数

        # 欠損率の基準
        self.MAX_MISSING_RATE = 0.7  # 70%以上欠損は警告

    # ========================================
    # 1. 基本的な品質指標
    # ========================================

    def validate_basic_stats(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        基本的な品質指標を算出

        Args:
            df: 対象DataFrame

        Returns:
            品質指標辞書
        """
        total_rows = len(df)

        # カラムごとの欠損率
        missing_rates = {}
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_rate = missing_count / total_rows
            missing_rates[col] = {
                'missing_count': int(missing_count),
                'missing_rate': round(missing_rate, 4),
                'status': self._get_missing_status(missing_rate)
            }

        return {
            'total_rows': total_rows,
            'total_columns': len(df.columns),
            'missing_rates': missing_rates
        }

    def _get_missing_status(self, missing_rate: float) -> str:
        """
        欠損率からステータスを判定

        Args:
            missing_rate: 欠損率（0-1）

        Returns:
            ステータス文字列
        """
        if missing_rate == 0:
            return 'OK'
        elif missing_rate < 0.1:
            return 'GOOD'
        elif missing_rate < 0.3:
            return 'ACCEPTABLE'
        elif missing_rate < 0.7:
            return 'WARNING'
        else:
            return 'CRITICAL'

    # ========================================
    # 2. サンプルサイズ検証
    # ========================================

    def validate_sample_size(self, df: pd.DataFrame, column: str) -> Dict[str, any]:
        """
        カラムごとのサンプルサイズを検証

        Args:
            df: 対象DataFrame
            column: 検証対象カラム

        Returns:
            検証結果
        """
        # 有効データ数
        valid_count = df[column].notna().sum()

        # グループごとの件数
        value_counts = df[column].value_counts()

        # 最小グループサイズ
        min_group_size = value_counts.min() if len(value_counts) > 0 else 0

        # 判定
        is_reliable = self._is_sample_reliable(valid_count, min_group_size)

        return {
            'column': column,
            'valid_count': int(valid_count),
            'unique_values': len(value_counts),
            'min_group_size': int(min_group_size),
            'max_group_size': int(value_counts.max()) if len(value_counts) > 0 else 0,
            'is_reliable': is_reliable,
            'reliability_level': self._get_reliability_level(valid_count, min_group_size),
            'warning': self._get_sample_warning(valid_count, min_group_size)
        }

    def _is_sample_reliable(self, valid_count: int, min_group_size: int) -> bool:
        """
        サンプルサイズが統計的に信頼できるか判定

        Args:
            valid_count: 有効データ数
            min_group_size: 最小グループサイズ

        Returns:
            True: 信頼できる / False: 信頼できない
        """
        # 観察的記述モードの場合、データがあればOK
        if self.validation_mode == 'descriptive':
            return valid_count > 0

        # 推論的考察モードの場合、最小サンプル数を要求
        return (valid_count >= self.MIN_SAMPLE_TOTAL and
                min_group_size >= self.MIN_SAMPLE_GROUP)

    def _get_reliability_level(self, valid_count: int, min_group_size: int) -> str:
        """
        信頼性レベルを判定

        Args:
            valid_count: 有効データ数
            min_group_size: 最小グループサイズ

        Returns:
            信頼性レベル（HIGH/MEDIUM/LOW/CRITICAL/DESCRIPTIVE）
        """
        # 観察的記述モードの場合、データがあればOK
        if self.validation_mode == 'descriptive':
            if valid_count > 0:
                return 'DESCRIPTIVE'
            else:
                return 'NO_DATA'

        # 推論的考察モードの場合、統計的信頼性を評価
        if valid_count >= 1000 and min_group_size >= 50:
            return 'HIGH'
        elif valid_count >= 500 and min_group_size >= 30:
            return 'MEDIUM'
        elif valid_count >= 100 and min_group_size >= 10:
            return 'LOW'
        else:
            return 'CRITICAL'

    def _get_sample_warning(self, valid_count: int, min_group_size: int) -> str:
        """
        サンプルサイズに関する警告メッセージ

        Args:
            valid_count: 有効データ数
            min_group_size: 最小グループサイズ

        Returns:
            警告メッセージ
        """
        # 観察的記述モードの場合、サンプルサイズ警告は不要
        if self.validation_mode == 'descriptive':
            return "なし（観察的記述）"

        warnings = []

        if valid_count < self.MIN_SAMPLE_TOTAL:
            warnings.append(f"推論用サンプル数不足（{valid_count}件 < {self.MIN_SAMPLE_TOTAL}件）")

        if min_group_size < self.MIN_SAMPLE_GROUP:
            warnings.append(f"推論用最小グループ不足（{min_group_size}件 < {self.MIN_SAMPLE_GROUP}件）")

        if len(warnings) == 0:
            return "なし"

        return " / ".join(warnings)

    # ========================================
    # 3. クロス集計の信頼性検証
    # ========================================

    def validate_crosstab(self, df: pd.DataFrame, col1: str, col2: str) -> Dict[str, any]:
        """
        クロス集計の信頼性を検証

        Args:
            df: 対象DataFrame
            col1: 行カラム
            col2: 列カラム

        Returns:
            検証結果
        """
        # クロス集計実行
        crosstab = pd.crosstab(df[col1], df[col2])

        # セル数
        total_cells = crosstab.size
        valid_cells = (crosstab > 0).sum().sum()
        empty_cells = total_cells - valid_cells

        # 最小・最大セル値
        min_cell_value = crosstab[crosstab > 0].min().min() if valid_cells > 0 else 0
        max_cell_value = crosstab.max().max()

        # 小さすぎるセル（< MIN_SAMPLE_CROSS）
        small_cells = (crosstab < self.MIN_SAMPLE_CROSS).sum().sum() - empty_cells

        # 信頼性判定
        if self.validation_mode == 'descriptive':
            # 観察的記述モードの場合、データがあれば信頼できる
            is_reliable = valid_cells > 0
        else:
            # 推論的考察モードの場合、小セル比率で判定
            is_reliable = (small_cells / total_cells) < 0.3  # 30%未満なら信頼できる

        return {
            'col1': col1,
            'col2': col2,
            'total_cells': int(total_cells),
            'valid_cells': int(valid_cells),
            'empty_cells': int(empty_cells),
            'small_cells': int(small_cells),
            'min_cell_value': int(min_cell_value),
            'max_cell_value': int(max_cell_value),
            'is_reliable': is_reliable,
            'reliability_level': self._get_crosstab_reliability(small_cells, total_cells),
            'warning': self._get_crosstab_warning(small_cells, total_cells, empty_cells)
        }

    def _get_crosstab_reliability(self, small_cells: int, total_cells: int) -> str:
        """
        クロス集計の信頼性レベルを判定

        Args:
            small_cells: 小さすぎるセル数
            total_cells: 総セル数

        Returns:
            信頼性レベル
        """
        # 観察的記述モードの場合、データがあればOK
        if self.validation_mode == 'descriptive':
            return 'DESCRIPTIVE'

        # 推論的考察モードの場合、小セル割合で判定
        small_ratio = small_cells / total_cells

        if small_ratio < 0.1:
            return 'HIGH'
        elif small_ratio < 0.3:
            return 'MEDIUM'
        elif small_ratio < 0.5:
            return 'LOW'
        else:
            return 'CRITICAL'

    def _get_crosstab_warning(self, small_cells: int, total_cells: int, empty_cells: int) -> str:
        """
        クロス集計に関する警告メッセージ

        Args:
            small_cells: 小さすぎるセル数
            total_cells: 総セル数
            empty_cells: 空セル数

        Returns:
            警告メッセージ
        """
        # 観察的記述モードの場合、警告なし
        if self.validation_mode == 'descriptive':
            return "なし（観察的記述）"

        # 推論的考察モードの場合、小セル・空セル割合で警告
        warnings = []

        small_ratio = small_cells / total_cells
        empty_ratio = empty_cells / total_cells

        if small_ratio > 0.3:
            warnings.append(f"小さいセルが多い（{small_ratio*100:.1f}%）")

        if empty_ratio > 0.5:
            warnings.append(f"空セルが多い（{empty_ratio*100:.1f}%）")

        if len(warnings) == 0:
            return "なし"

        return " / ".join(warnings)

    # ========================================
    # 4. 統合品質レポート生成
    # ========================================

    def generate_quality_report(self, df: pd.DataFrame,
                                target_columns: List[str] = None,
                                crosstab_pairs: List[Tuple[str, str]] = None) -> Dict[str, any]:
        """
        統合品質レポートを生成

        Args:
            df: 対象DataFrame
            target_columns: 検証対象カラムリスト（Noneの場合は全カラム）
            crosstab_pairs: クロス集計検証ペア

        Returns:
            統合品質レポート
        """
        # 基本統計
        basic_stats = self.validate_basic_stats(df)

        # カラムごとのサンプルサイズ検証
        if target_columns is None:
            target_columns = df.columns.tolist()

        column_validations = {}
        for col in target_columns:
            if col in df.columns:
                column_validations[col] = self.validate_sample_size(df, col)

        # クロス集計検証
        crosstab_validations = {}
        if crosstab_pairs:
            for col1, col2 in crosstab_pairs:
                key = f"{col1} × {col2}"
                crosstab_validations[key] = self.validate_crosstab(df, col1, col2)

        # 総合判定
        overall_status = self._get_overall_status(
            basic_stats,
            column_validations,
            crosstab_validations
        )

        return {
            'basic_stats': basic_stats,
            'column_validations': column_validations,
            'crosstab_validations': crosstab_validations,
            'overall_status': overall_status
        }

    def _get_overall_status(self, basic_stats: Dict,
                           column_validations: Dict,
                           crosstab_validations: Dict) -> Dict[str, any]:
        """
        総合判定を算出

        Args:
            basic_stats: 基本統計
            column_validations: カラム検証結果
            crosstab_validations: クロス集計検証結果

        Returns:
            総合判定
        """
        # 総データ数
        total_rows = basic_stats['total_rows']

        # 信頼できるカラム数
        reliable_columns = sum(1 for v in column_validations.values() if v['is_reliable'])
        total_columns = len(column_validations)

        # 信頼できるクロス集計数
        reliable_crosstabs = sum(1 for v in crosstab_validations.values() if v['is_reliable'])
        total_crosstabs = len(crosstab_validations)

        # 総合スコア（0-100）
        score = 0
        if total_rows >= 1000:
            score += 40
        elif total_rows >= 500:
            score += 30
        elif total_rows >= 100:
            score += 20
        else:
            score += 10

        if total_columns > 0:
            column_score = (reliable_columns / total_columns) * 30
            score += column_score

        if total_crosstabs > 0:
            crosstab_score = (reliable_crosstabs / total_crosstabs) * 30
            score += crosstab_score
        else:
            score += 30  # クロス集計なしの場合は満点

        # 判定
        if score >= 80:
            status = 'EXCELLENT'
        elif score >= 60:
            status = 'GOOD'
        elif score >= 40:
            status = 'ACCEPTABLE'
        else:
            status = 'POOR'

        return {
            'total_rows': total_rows,
            'reliable_columns': reliable_columns,
            'total_columns': total_columns,
            'reliable_crosstabs': reliable_crosstabs,
            'total_crosstabs': total_crosstabs,
            'quality_score': round(score, 2),
            'status': status,
            'recommendation': self._get_recommendation(status, total_rows)
        }

    def _get_recommendation(self, status: str, total_rows: int) -> str:
        """
        推奨事項を生成

        Args:
            status: 総合ステータス
            total_rows: 総データ数

        Returns:
            推奨事項
        """
        if status == 'EXCELLENT':
            return "データ品質は優れています。そのまま分析結果を使用できます。"
        elif status == 'GOOD':
            return "データ品質は良好です。一部のカラムは注意が必要ですが、全体的には信頼できます。"
        elif status == 'ACCEPTABLE':
            return "データ品質は許容範囲です。警告付きで結果を提示することを推奨します。"
        else:
            if total_rows < 100:
                return "データ数が少なすぎます。より多くのデータを収集することを強く推奨します。"
            else:
                return "データ品質に重大な問題があります。欠損データが多いか、サンプルサイズが不十分です。"

    # ========================================
    # 5. 結果出力用メソッド
    # ========================================

    def export_quality_report_csv(self, report: Dict, output_path: str):
        """
        品質レポートをCSVにエクスポート

        Args:
            report: 品質レポート
            output_path: 出力先パス
        """
        # カラム検証結果をDataFrameに変換
        column_data = []
        for col_name, validation in report['column_validations'].items():
            column_data.append({
                'カラム名': col_name,
                '有効データ数': validation['valid_count'],
                'ユニーク値数': validation['unique_values'],
                '最小グループサイズ': validation['min_group_size'],
                '信頼性レベル': validation['reliability_level'],
                '警告': validation['warning']
            })

        df_columns = pd.DataFrame(column_data)
        df_columns.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"品質レポート出力: {output_path}")

    # ========================================
    # 6. 品質フラグ直接追加メソッド（オプションC対応）
    # ========================================

    def add_quality_flags_to_aggregation(
        self,
        df: pd.DataFrame,
        count_column: str = 'カウント',
        validation_mode: str = None
    ) -> pd.DataFrame:
        """
        集計結果DataFrameに品質フラグを追加

        Args:
            df: 集計結果DataFrame
            count_column: カウント列名
            validation_mode: 検証モード（Noneの場合はインスタンスの設定を使用）

        Returns:
            品質フラグが追加されたDataFrame
        """
        df_copy = df.copy()
        mode = validation_mode if validation_mode else self.validation_mode

        # サンプルサイズ区分
        df_copy['サンプルサイズ区分'] = df_copy[count_column].apply(
            lambda x: self._get_sample_size_category(x)
        )

        # 信頼性レベル
        df_copy['信頼性レベル'] = df_copy[count_column].apply(
            lambda x: self._get_reliability_level_from_count(x, mode)
        )

        # 警告メッセージ
        df_copy['警告メッセージ'] = df_copy[count_column].apply(
            lambda x: self._get_warning_message_from_count(x, mode)
        )

        return df_copy

    def add_quality_flags_to_crosstab(
        self,
        df: pd.DataFrame,
        count_column: str = 'カウント'
    ) -> pd.DataFrame:
        """
        クロス集計結果DataFrameにセル単位の品質フラグを追加

        Args:
            df: クロス集計結果DataFrame
            count_column: カウント列名

        Returns:
            セル品質フラグが追加されたDataFrame
        """
        df_copy = df.copy()

        # セル品質情報を取得
        cell_quality = df_copy[count_column].apply(
            lambda x: self._get_cell_quality(x)
        )

        # 品質列を追加
        df_copy['セル品質'] = cell_quality.apply(lambda x: x['セル品質'])
        df_copy['警告フラグ'] = cell_quality.apply(lambda x: x['警告フラグ'])
        df_copy['警告メッセージ'] = cell_quality.apply(lambda x: x['警告メッセージ'])

        return df_copy

    def _get_sample_size_category(self, count: int) -> str:
        """
        サンプルサイズ区分を判定

        Args:
            count: サンプル数

        Returns:
            サンプルサイズ区分（VERY_SMALL/SMALL/MEDIUM/LARGE）
        """
        if count >= 100:
            return 'LARGE'
        elif count >= 30:
            return 'MEDIUM'
        elif count >= 10:
            return 'SMALL'
        else:
            return 'VERY_SMALL'

    def _get_reliability_level_from_count(self, count: int, mode: str = 'inferential') -> str:
        """
        カウント数から信頼性レベルを判定

        Args:
            count: サンプル数
            mode: 検証モード

        Returns:
            信頼性レベル
        """
        if mode == 'descriptive':
            return 'DESCRIPTIVE' if count > 0 else 'NO_DATA'

        # 推論的考察モード
        if count >= 100:
            return 'HIGH'
        elif count >= 30:
            return 'MEDIUM'
        elif count >= 10:
            return 'LOW'
        else:
            return 'CRITICAL'

    def _get_warning_message_from_count(self, count: int, mode: str = 'inferential') -> str:
        """
        カウント数から警告メッセージを生成

        Args:
            count: サンプル数
            mode: 検証モード

        Returns:
            警告メッセージ
        """
        if mode == 'descriptive':
            return 'なし（観察的記述）'

        # 推論的考察モード
        if count >= 30:
            return 'なし'
        elif count >= 10:
            return f'参考データのみ（n={count} < 30）'
        else:
            return f'推論には使用不可（n={count} < 30）'

    def _get_cell_quality(self, cell_count: int) -> Dict[str, str]:
        """
        クロス集計セルの品質を判定

        Args:
            cell_count: セルのカウント数

        Returns:
            セル品質情報（セル品質、警告フラグ、警告メッセージ）
        """
        if cell_count < 5:
            return {
                'セル品質': 'INSUFFICIENT',
                '警告フラグ': '使用不可',
                '警告メッセージ': f'セル数不足（n={cell_count} < 5）'
            }
        elif cell_count < 30:
            return {
                'セル品質': 'MARGINAL',
                '警告フラグ': '要注意',
                '警告メッセージ': f'セル数不足（n={cell_count} < 30）'
            }
        else:
            return {
                'セル品質': 'SUFFICIENT',
                '警告フラグ': 'なし',
                '警告メッセージ': 'なし'
            }
