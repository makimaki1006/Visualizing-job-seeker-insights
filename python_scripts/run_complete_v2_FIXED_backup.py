"""
新データ形式（results_*.csv）対応の統合実行スクリプト - 修正版
Phase 1-3, 6-7, 8, 10を実装

【修正内容】
- カイ二乗検定: 希望勤務地数の代わりに「性別×年齢層」「就業状態×年齢層」を追加
- デバッグログ追加
- エラーハンドリング強化
"""

# 元のコードをインポート
import sys
from pathlib import Path

# run_complete_v2.pyと同じディレクトリにあることを前提
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from run_complete_v2 import *

# JobMedleyAnalyzerV2を継承して修正版を作成
class JobMedleyAnalyzerV2Fixed(JobMedleyAnalyzerV2):
    """
    JobMedleyAnalyzerV2の修正版
    カイ二乗検定の実装を改善
    """

    def _run_chi_square_tests(self, df):
        """
        カイ二乗検定を実施（修正版）

        【修正内容】
        - 全員が希望勤務地ありの場合、代わりに「性別×年齢層」「就業状態×年齢層」を検定
        - デバッグログ追加
        - 検定不可の理由をログ出力
        """
        results = []

        # データフィルタリング
        df_filtered = df[(df['gender'].notna()) & (df['gender'] != '') &
                        (df['年齢層'].notna()) & (df['年齢層'] != '')]

        print(f"  フィルタ後のデータ件数: {len(df_filtered)}")

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
                print(f"            理由: 全員が希望勤務地ありまたはなしの可能性")
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

        # 【新規追加】パターン3: 性別 × 年齢層
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

        # 【新規追加】パターン4: 就業状態 × 年齢層
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


# メイン実行
if __name__ == "__main__":
    print("=" * 80)
    print("ジョブメドレー求職者データ分析 v2.1 - 修正版")
    print("新データ形式対応（全Phase実装）")
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

    # 修正版アナライザーを使用
    analyzer = JobMedleyAnalyzerV2Fixed(csv_path)
    analyzer.load_data()

    # Phase 1-10実行
    analyzer.export_phase1()
    analyzer.export_phase2()
    analyzer.export_phase3()
    analyzer.export_phase6()
    analyzer.export_phase7()
    analyzer.export_phase8()
    analyzer.export_phase10()

    # 統合品質レポート
    analyzer.generate_overall_quality_report()

    print()
    print("=" * 80)
    print("全フェーズ完了")
    print("=" * 80)
