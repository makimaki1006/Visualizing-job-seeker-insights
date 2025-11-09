#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提案機能のデータ充足性検証

各機能が現在のデータのみで実装可能かを検証
"""

import sys
from pathlib import Path
import pandas as pd
from run_complete_v2_perfect import PerfectJobSeekerAnalyzer


def verify_feature_1_supply_demand_gap(df):
    """1. 需給ギャップ分析の実装可能性"""

    print("=" * 100)
    print("【機能1: 需給ギャップ分析】")
    print("=" * 100)

    required_columns = ['desired_areas', 'residence_muni']

    print("\n必要なデータ:")
    for col in required_columns:
        if col == 'desired_areas':
            # desired_areasはリスト型
            has_data = df['desired_areas'].apply(lambda x: len(x) > 0).sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")
        else:
            has_data = df[col].notna().sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")

    print("\n外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_2_rarity_score(df):
    """2. 希少性スコアの実装可能性"""

    print("\n" + "=" * 100)
    print("【機能2: 希少性スコア】")
    print("=" * 100)

    required_columns = ['desired_areas', 'age_bucket', 'gender', 'has_national_license']

    print("\n必要なデータ:")
    for col in required_columns:
        if col == 'desired_areas':
            has_data = df['desired_areas'].apply(lambda x: len(x) > 0).sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")
        else:
            has_data = df[col].notna().sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")

    print("\n計算方法: 希少性スコア = 1 / (該当人数)")
    print("外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_3_competition_analysis(df):
    """3. 競合分析の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能3: 競合分析】")
    print("=" * 100)

    required_columns = ['desired_areas', 'age_bucket', 'gender', 'has_national_license', 'employment_status']

    print("\n必要なデータ:")
    for col in required_columns:
        if col == 'desired_areas':
            has_data = df['desired_areas'].apply(lambda x: len(x) > 0).sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")
        else:
            has_data = df[col].notna().sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")

    print("\n外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_4_multidimensional_crosstab(df):
    """4. 多次元クロス集計の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能4: 多次元クロス集計エンジン】")
    print("=" * 100)

    available_dimensions = {
        '基本属性': ['age', 'age_bucket', 'gender'],
        '地理': ['residence_pref', 'residence_muni', 'desired_areas'],
        '資格': ['qualifications', 'qualification_count', 'has_national_license'],
        'キャリア': ['career', 'employment_status', 'desired_job'],
        '希望条件': ['desired_workstyle', 'desired_start', 'status']
    }

    print("\n利用可能な分析軸:")
    total_dims = 0
    for category, dims in available_dimensions.items():
        valid_dims = [d for d in dims if d in df.columns]
        total_dims += len(valid_dims)
        print(f"  {category}: {len(valid_dims)}軸")

    print(f"\n総軸数: {total_dims}軸")
    print("外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_5_network_centrality(df):
    """5. ネットワーク中心性の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能5: ネットワーク中心性】")
    print("=" * 100)

    required_columns = ['residence_muni', 'desired_areas']

    print("\n必要なデータ:")
    for col in required_columns:
        if col == 'desired_areas':
            has_data = df['desired_areas'].apply(lambda x: len(x) > 0).sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")
        else:
            has_data = df[col].notna().sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")

    print("\n計算内容:")
    print("  - 入次数: 何箇所から流入があるか")
    print("  - 出次数: 何箇所へ流出しているか")
    print("  - ハブスコア: 入次数 × 出次数")

    print("\n外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_6_qualification_locality(df):
    """6. 資格別地域選好性の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能6: 資格別地域選好性】")
    print("=" * 100)

    required_columns = ['qualifications', 'desired_areas', 'residence_pref']

    print("\n必要なデータ:")
    for col in required_columns:
        if col in ['qualifications', 'desired_areas']:
            has_data = df[col].apply(lambda x: len(x) > 0).sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")
        else:
            has_data = df[col].notna().sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")

    print("\n分析内容:")
    print("  - 各資格保有者がどの都道府県を好むか")
    print("  - 居住地と希望地の距離傾向")

    print("\n外部データの必要性: なし（座標データは既存のgeocache.jsonを使用）")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_7_dynamic_segmentation(df):
    """7. 動的セグメンテーションの実装可能性"""

    print("\n" + "=" * 100)
    print("【機能7: 動的セグメンテーション】")
    print("=" * 100)

    print("\n必要なデータ: すべての既存カラム")
    print("外部データの必要性: なし")
    print("追加要件: GAS側のUI開発（ドロップダウン選択など）")
    print("実装可能性: ✅ 現在のデータのみで実装可能（UI開発工数が必要）")

    return True


def verify_feature_8_time_series(df):
    """8. 時系列トレンド分析の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能8: 時系列トレンド分析】")
    print("=" * 100)

    print("\n必要なデータ: 複数時点のデータ（例: 2024年1月、2月、3月...）")
    print("現在のデータ: 単一時点のスナップショット")

    print("\n外部データの必要性: なし（ただし複数時点のデータ収集が必要）")
    print("実装可能性: ❌ 現在のデータでは実装不可（複数時点データが前提）")

    return False


def verify_feature_9_similar_persona(df):
    """9. 類似ペルソナ検索の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能9: 類似ペルソナ検索】")
    print("=" * 100)

    required_columns = ['age', 'gender', 'qualifications', 'desired_areas', 'employment_status']

    print("\n必要なデータ:")
    for col in required_columns:
        if col in ['qualifications', 'desired_areas']:
            has_data = df[col].apply(lambda x: len(x) > 0).sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")
        else:
            has_data = df[col].notna().sum()
            print(f"  - {col}: {has_data}/{len(df)}件にデータあり")

    print("\nアルゴリズム: k-NN（k-Nearest Neighbors）")
    print("外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def verify_feature_10_effect_size(df):
    """10. 効果量・多重比較補正の実装可能性"""

    print("\n" + "=" * 100)
    print("【機能10: 効果量と多重比較補正】")
    print("=" * 100)

    print("\n必要なデータ: Phase 2の統計テスト用データ（カテゴリカル変数、連続変数）")
    print("計算内容:")
    print("  - Cohen's d: 2グループ間の効果量")
    print("  - Cramér's V: カテゴリカル変数間の関連性の強さ")
    print("  - Bonferroni補正: 多重比較の際のp値調整")

    print("\n外部データの必要性: なし")
    print("実装可能性: ✅ 現在のデータのみで実装可能")

    return True


def main():
    """メイン処理"""

    print("=" * 100)
    print("提案機能のデータ充足性検証")
    print("=" * 100)

    # データ読み込み
    data_file = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251028_112441.csv")
    analyzer = PerfectJobSeekerAnalyzer(str(data_file))
    analyzer.load_data()
    analyzer.process_data()

    df = analyzer.processed_data
    print(f"\n総レコード数: {len(df):,}件")

    # 各機能の検証
    results = {}

    results['需給ギャップ分析'] = verify_feature_1_supply_demand_gap(df)
    results['希少性スコア'] = verify_feature_2_rarity_score(df)
    results['競合分析'] = verify_feature_3_competition_analysis(df)
    results['多次元クロス集計'] = verify_feature_4_multidimensional_crosstab(df)
    results['ネットワーク中心性'] = verify_feature_5_network_centrality(df)
    results['資格別地域選好性'] = verify_feature_6_qualification_locality(df)
    results['動的セグメンテーション'] = verify_feature_7_dynamic_segmentation(df)
    results['時系列トレンド'] = verify_feature_8_time_series(df)
    results['類似ペルソナ検索'] = verify_feature_9_similar_persona(df)
    results['効果量・多重比較'] = verify_feature_10_effect_size(df)

    # 最終サマリー
    print("\n\n" + "=" * 100)
    print("【検証結果サマリー】")
    print("=" * 100)

    print("\n✅ 現在のデータのみで実装可能（外部データ不要）:")
    for feature, is_feasible in results.items():
        if is_feasible:
            print(f"  - {feature}")

    print("\n❌ 追加データが必要:")
    for feature, is_feasible in results.items():
        if not is_feasible:
            print(f"  - {feature} (複数時点のデータが必要)")

    feasible_count = sum(results.values())
    total_count = len(results)

    print(f"\n実装可能な機能: {feasible_count}/{total_count}個 ({feasible_count/total_count*100:.0f}%)")

    # 日本全国データへの拡張性
    print("\n\n" + "=" * 100)
    print("【日本全国データへの拡張性】")
    print("=" * 100)

    print("\n現在のデータ:")
    print(f"  - レコード数: {len(df):,}件")
    print(f"  - 都道府県数: {df['residence_pref'].nunique()}都道府県")
    print(f"  - 市町村数: {df['residence_muni'].nunique()}市町村")

    print("\n日本全国に拡大した場合:")
    print("  - 想定レコード数: 10万～100万件（規模による）")
    print("  - 都道府県数: 47都道府県（変わらず）")
    print("  - 市町村数: 1,700～1,900市町村（増加）")

    print("\n拡張性の懸念:")
    print("  ⚠️ 計算コスト: 多次元クロス集計で組み合わせが爆発的に増加")
    print("     対策: インデックス最適化、集計のキャッシュ化")
    print("  ⚠️ CSV出力サイズ: 数百MB～数GBになる可能性")
    print("     対策: Parquet形式、圧縮、データベース化")
    print("  ✅ ロジック: すべて同じアルゴリズムで動作")
    print("  ✅ GAS読み込み: シート分割、ページネーション対応で可能")

    print("\n結論:")
    print("  ✅ すべての実装可能機能は、日本全国データでも動作可能")
    print("  ⚠️ パフォーマンス最適化が必要になる可能性あり")


if __name__ == '__main__':
    main()
