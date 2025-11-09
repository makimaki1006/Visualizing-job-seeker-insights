#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 12, 13, 14のテストスクリプト

【テスト内容】
1. 小規模テストデータでPhase 12-14を実行
2. 出力CSVファイルの存在確認
3. CSVファイル構造の検証（カラム名、データ件数）
4. latitude/longitude列の存在確認（MAP統合対応）
5. 品質レポートの確認
"""

import sys
from pathlib import Path
import pandas as pd

# 実データを使用してテスト
sys.path.insert(0, str(Path(__file__).parent))
from run_complete_v2_perfect import PerfectJobSeekerAnalyzer


def test_phase12_supply_demand_gap():
    """Phase 12: 需給ギャップ分析のテスト"""
    print("\n" + "=" * 80)
    print("【Phase 12テスト: 需給ギャップ分析】")
    print("=" * 80)

    # 最新のCSVファイルを取得
    csv_path = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out")
    csv_files = sorted(csv_path.glob("results_*.csv"), reverse=True)

    if not csv_files:
        print("  ❌ テストデータが見つかりません")
        return False

    latest_csv = csv_files[0]
    print(f"  📁 使用データ: {latest_csv.name}")

    # アナライザー初期化
    analyzer = PerfectJobSeekerAnalyzer(str(latest_csv))
    analyzer.load_data()
    analyzer.process_data()

    # Phase 12実行
    try:
        analyzer.export_phase12()
    except Exception as e:
        print(f"  ❌ Phase 12実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 出力ファイルの確認
    output_path = Path("data/output_v2/phase12")
    csv_file = output_path / "SupplyDemandGap.csv"
    quality_report = output_path / "P12_QualityReport.csv"

    if not csv_file.exists():
        print(f"  ❌ SupplyDemandGap.csvが生成されていません")
        return False

    if not quality_report.exists():
        print(f"  ❌ P12_QualityReport.csvが生成されていません")
        return False

    # CSVファイルの検証
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"\n  ✅ SupplyDemandGap.csv: {len(df)}件")
    print(f"  📋 カラム: {', '.join(df.columns.tolist())}")

    # 必須カラムの確認
    required_columns = ['prefecture', 'municipality', 'location', 'demand_count',
                        'supply_count', 'demand_supply_ratio', 'gap', 'latitude', 'longitude']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"  ❌ 不足カラム: {', '.join(missing_columns)}")
        return False

    print(f"  ✅ 必須カラム: すべて存在")

    # latitude/longitude列の確認（MAP統合対応）
    has_coords = df[['latitude', 'longitude']].notna().all(axis=1).sum()
    total = len(df)
    print(f"  🗺️ 座標データ: {has_coords}/{total}件 ({has_coords/total*100:.1f}%)")

    # サンプルデータ表示
    print(f"\n  【Top 5 需給ギャップ】")
    print(df[['location', 'demand_count', 'supply_count', 'demand_supply_ratio', 'gap']].head().to_string(index=False))

    # 品質レポート確認
    report_df = pd.read_csv(quality_report, encoding='utf-8-sig')
    print(f"\n  ✅ P12_QualityReport.csv: {len(report_df)}項目")

    return True


def test_phase13_rarity_score():
    """Phase 13: 希少性スコアのテスト"""
    print("\n" + "=" * 80)
    print("【Phase 13テスト: 希少性スコア】")
    print("=" * 80)

    # 最新のCSVファイルを取得
    csv_path = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out")
    csv_files = sorted(csv_path.glob("results_*.csv"), reverse=True)

    if not csv_files:
        print("  ❌ テストデータが見つかりません")
        return False

    latest_csv = csv_files[0]
    print(f"  📁 使用データ: {latest_csv.name}")

    # アナライザー初期化
    analyzer = PerfectJobSeekerAnalyzer(str(latest_csv))
    analyzer.load_data()
    analyzer.process_data()

    # Phase 13実行
    try:
        analyzer.export_phase13()
    except Exception as e:
        print(f"  ❌ Phase 13実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 出力ファイルの確認
    output_path = Path("data/output_v2/phase13")
    csv_file = output_path / "RarityScore.csv"
    quality_report = output_path / "P13_QualityReport.csv"

    if not csv_file.exists():
        print(f"  ❌ RarityScore.csvが生成されていません")
        return False

    if not quality_report.exists():
        print(f"  ❌ P13_QualityReport.csvが生成されていません")
        return False

    # CSVファイルの検証
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"\n  ✅ RarityScore.csv: {len(df)}件")
    print(f"  📋 カラム: {', '.join(df.columns.tolist())}")

    # 必須カラムの確認
    required_columns = ['prefecture', 'municipality', 'location', 'age_bucket', 'gender',
                        'has_national_license', 'count', 'rarity_score', 'rarity_rank',
                        'latitude', 'longitude']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"  ❌ 不足カラム: {', '.join(missing_columns)}")
        return False

    print(f"  ✅ 必須カラム: すべて存在")

    # latitude/longitude列の確認（MAP統合対応）
    has_coords = df[['latitude', 'longitude']].notna().all(axis=1).sum()
    total = len(df)
    print(f"  🗺️ 座標データ: {has_coords}/{total}件 ({has_coords/total*100:.1f}%)")

    # 希少性ランク分布
    rank_dist = df['rarity_rank'].value_counts().sort_index()
    print(f"\n  【希少性ランク分布】")
    for rank, count in rank_dist.items():
        print(f"    {rank}: {count}件")

    # サンプルデータ表示（最も希少なケース）
    print(f"\n  【Top 5 最も希少なケース】")
    print(df[['location', 'age_bucket', 'gender', 'has_national_license', 'count', 'rarity_score', 'rarity_rank']].head().to_string(index=False))

    # 品質レポート確認
    report_df = pd.read_csv(quality_report, encoding='utf-8-sig')
    print(f"\n  ✅ P13_QualityReport.csv: {len(report_df)}項目")

    return True


def test_phase14_competition_profile():
    """Phase 14: 競合分析のテスト"""
    print("\n" + "=" * 80)
    print("【Phase 14テスト: 競合分析】")
    print("=" * 80)

    # 最新のCSVファイルを取得
    csv_path = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out")
    csv_files = sorted(csv_path.glob("results_*.csv"), reverse=True)

    if not csv_files:
        print("  ❌ テストデータが見つかりません")
        return False

    latest_csv = csv_files[0]
    print(f"  📁 使用データ: {latest_csv.name}")

    # アナライザー初期化
    analyzer = PerfectJobSeekerAnalyzer(str(latest_csv))
    analyzer.load_data()
    analyzer.process_data()

    # Phase 14実行
    try:
        analyzer.export_phase14()
    except Exception as e:
        print(f"  ❌ Phase 14実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 出力ファイルの確認
    output_path = Path("data/output_v2/phase14")
    csv_file = output_path / "CompetitionProfile.csv"
    quality_report = output_path / "P14_QualityReport.csv"

    if not csv_file.exists():
        print(f"  ❌ CompetitionProfile.csvが生成されていません")
        return False

    if not quality_report.exists():
        print(f"  ❌ P14_QualityReport.csvが生成されていません")
        return False

    # CSVファイルの検証
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"\n  ✅ CompetitionProfile.csv: {len(df)}件")
    print(f"  📋 カラム: {', '.join(df.columns.tolist())}")

    # 必須カラムの確認
    required_columns = ['prefecture', 'municipality', 'location', 'total_applicants',
                        'top_age_group', 'top_age_ratio', 'female_ratio', 'male_ratio',
                        'national_license_rate', 'top_employment_status', 'top_employment_ratio',
                        'avg_qualification_count', 'latitude', 'longitude']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"  ❌ 不足カラム: {', '.join(missing_columns)}")
        return False

    print(f"  ✅ 必須カラム: すべて存在")

    # latitude/longitude列の確認（MAP統合対応）
    has_coords = df[['latitude', 'longitude']].notna().all(axis=1).sum()
    total = len(df)
    print(f"  🗺️ 座標データ: {has_coords}/{total}件 ({has_coords/total*100:.1f}%)")

    # サンプルデータ表示（最も競争が激しい地域）
    print(f"\n  【Top 5 競争が激しい地域】")
    print(df[['location', 'total_applicants', 'top_age_group', 'female_ratio', 'national_license_rate']].head().to_string(index=False))

    # 品質レポート確認
    report_df = pd.read_csv(quality_report, encoding='utf-8-sig')
    print(f"\n  ✅ P14_QualityReport.csv: {len(report_df)}項目")

    return True


def main():
    """メイン処理"""
    print("=" * 80)
    print("Phase 12, 13, 14統合テスト")
    print("=" * 80)

    results = {}

    # Phase 12テスト
    results['Phase 12'] = test_phase12_supply_demand_gap()

    # Phase 13テスト
    results['Phase 13'] = test_phase13_rarity_score()

    # Phase 14テスト
    results['Phase 14'] = test_phase14_competition_profile()

    # 最終結果
    print("\n" + "=" * 80)
    print("【テスト結果サマリー】")
    print("=" * 80)

    for phase, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {phase}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ すべてのテストがPASSしました！")
    else:
        print("❌ 一部のテストがFAILしました")
    print("=" * 80)

    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
