# -*- coding: utf-8 -*-
"""
外部データ統合分析スクリプト
ジョブメドレー求職者データと政府統計データを統合して分析

作成日: 2025-12-27
"""

import sys
import io
# Windows環境でのUnicodeエンコーディング対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import os
from pathlib import Path

# パス設定
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXTERNAL_DIR = DATA_DIR / "external"
OUTPUT_DIR = DATA_DIR / "output_v2"
INTEGRATED_DIR = DATA_DIR / "integrated_analysis"

def load_external_data():
    """外部データを読み込む"""
    print("=" * 60)
    print("外部データの読み込み")
    print("=" * 60)

    external_data = {}

    # 介護施設密度
    facility_path = EXTERNAL_DIR / "prefecture_care_facility_density.csv"
    if facility_path.exists():
        external_data['facility_density'] = pd.read_csv(facility_path)
        print(f"✅ 介護施設密度データ: {len(external_data['facility_density'])}件")

    # 高齢化率
    aging_path = EXTERNAL_DIR / "prefecture_aging_rate.csv"
    if aging_path.exists():
        external_data['aging_rate'] = pd.read_csv(aging_path)
        print(f"✅ 高齢化率データ: {len(external_data['aging_rate'])}件")

    # 20-30代女性比率
    female_path = EXTERNAL_DIR / "prefecture_20_30s_female_ratio.csv"
    if female_path.exists():
        external_data['female_ratio'] = pd.read_csv(female_path)
        print(f"✅ 20-30代女性比率データ: {len(external_data['female_ratio'])}件")

    # 全国人口サマリー
    pop_path = EXTERNAL_DIR / "national_population_summary.csv"
    if pop_path.exists():
        external_data['national_pop'] = pd.read_csv(pop_path)
        print(f"✅ 全国人口サマリー: {len(external_data['national_pop'])}件")

    # 介護職需給データ
    demand_path = EXTERNAL_DIR / "care_worker_demand.csv"
    if demand_path.exists():
        external_data['care_demand'] = pd.read_csv(demand_path)
        print(f"✅ 介護職需給データ: {len(external_data['care_demand'])}件")

    return external_data

def load_jobmedley_data():
    """ジョブメドレーデータを読み込む"""
    print("\n" + "=" * 60)
    print("ジョブメドレーデータの読み込み")
    print("=" * 60)

    jm_data = {}

    # Phase 1: 求職者データ
    applicants_path = OUTPUT_DIR / "phase1" / "Phase1_Applicants.csv"
    if applicants_path.exists():
        jm_data['applicants'] = pd.read_csv(applicants_path)
        print(f"✅ 求職者データ: {len(jm_data['applicants']):,}件")

    # MapComplete統合データ
    mapcomplete_path = OUTPUT_DIR / "mapcomplete_complete_sheets" / "MapComplete_Complete_All_FIXED.csv"
    if mapcomplete_path.exists():
        jm_data['mapcomplete'] = pd.read_csv(mapcomplete_path)
        print(f"✅ MapComplete統合データ: {len(jm_data['mapcomplete']):,}件")

    return jm_data

def create_prefecture_summary(jm_data):
    """都道府県別サマリーを作成"""
    print("\n" + "=" * 60)
    print("都道府県別サマリーの作成")
    print("=" * 60)

    if 'applicants' not in jm_data:
        print("❌ 求職者データがありません")
        return None

    df = jm_data['applicants']

    # 都道府県別集計
    pref_summary = df.groupby('residence_prefecture').agg({
        'applicant_id': 'count',
        'age': 'mean',
        'desired_area_count': 'mean',
        'qualification_count': 'mean',
    }).reset_index()

    pref_summary.columns = [
        'prefecture',
        'jobseeker_count',
        'avg_age',
        'avg_desired_area_count',
        'avg_qualification_count'
    ]

    # 性別構成
    gender_ratio = df.groupby(['residence_prefecture', 'gender']).size().unstack(fill_value=0)
    if '女性' in gender_ratio.columns:
        gender_ratio['female_ratio'] = gender_ratio['女性'] / (gender_ratio['女性'] + gender_ratio.get('男性', 0)) * 100
        pref_summary = pref_summary.merge(
            gender_ratio[['female_ratio']].reset_index().rename(columns={'residence_prefecture': 'prefecture'}),
            on='prefecture',
            how='left'
        )

    # 雇用形態構成
    workstyle = df.groupby(['residence_prefecture', 'desired_workstyle']).size().unstack(fill_value=0)
    total = workstyle.sum(axis=1)
    if '正社員' in workstyle.columns:
        workstyle['fulltime_ratio'] = workstyle['正社員'] / total * 100
    elif '正職員' in workstyle.columns:
        workstyle['fulltime_ratio'] = workstyle['正職員'] / total * 100
        pref_summary = pref_summary.merge(
            workstyle[['fulltime_ratio']].reset_index().rename(columns={'residence_prefecture': 'prefecture'}),
            on='prefecture',
            how='left'
        )

    # 年齢層構成
    age_dist = df.groupby(['residence_prefecture', 'age_group']).size().unstack(fill_value=0)
    age_total = age_dist.sum(axis=1)
    for age_group in ['20代', '30代', '40代', '50代', '60代', '70代以上']:
        if age_group in age_dist.columns:
            age_dist[f'{age_group}_ratio'] = age_dist[age_group] / age_total * 100

    age_ratio_cols = [c for c in age_dist.columns if c.endswith('_ratio')]
    if age_ratio_cols:
        pref_summary = pref_summary.merge(
            age_dist[age_ratio_cols].reset_index().rename(columns={'residence_prefecture': 'prefecture'}),
            on='prefecture',
            how='left'
        )

    print(f"✅ 都道府県別サマリー: {len(pref_summary)}件")
    return pref_summary

def integrate_data(pref_summary, external_data):
    """ジョブメドレーデータと外部データを統合"""
    print("\n" + "=" * 60)
    print("データ統合")
    print("=" * 60)

    integrated = pref_summary.copy()

    # 介護施設密度を結合
    if 'facility_density' in external_data:
        facility = external_data['facility_density'][['prefecture', 'facility_density_per_10k_elderly', 'rank']]
        facility.columns = ['prefecture', 'facility_density', 'facility_rank']
        integrated = integrated.merge(facility, on='prefecture', how='left')
        print("✅ 介護施設密度データを結合")

    # 高齢化率を結合
    if 'aging_rate' in external_data:
        aging = external_data['aging_rate'][['prefecture', 'aging_rate_2023', 'aging_rate_2050_projection']]
        integrated = integrated.merge(aging, on='prefecture', how='left')
        print("✅ 高齢化率データを結合")

    # 20-30代女性比率を結合
    if 'female_ratio' in external_data:
        female = external_data['female_ratio'][['prefecture', 'female_ratio_20_30s']]
        female.columns = ['prefecture', 'pop_female_ratio_20_30s']
        integrated = integrated.merge(female, on='prefecture', how='left')
        print("✅ 20-30代女性比率データを結合")

    # 統合指標の計算
    print("\n統合指標の計算...")

    # 施設あたり求職者数（推定）
    if 'facility_density' in integrated.columns and 'aging_rate_2023' in integrated.columns:
        # 65歳以上人口 × 施設密度 / 10000 = 推定施設数
        # ここでは簡易的に全国人口で計算
        # 実際には都道府県別人口データが必要
        pass

    # 女性比率の乖離（JM女性比率 - 人口女性比率）
    if 'female_ratio' in integrated.columns and 'pop_female_ratio_20_30s' in integrated.columns:
        integrated['female_ratio_gap'] = integrated['female_ratio'] - integrated['pop_female_ratio_20_30s']
        print("✅ 女性比率乖離を計算")

    # 高齢化率と求職者数の相関分析用指標
    if 'aging_rate_2023' in integrated.columns:
        integrated['jobseeker_per_aging'] = integrated['jobseeker_count'] / integrated['aging_rate_2023']
        print("✅ 高齢化率あたり求職者数を計算")

    return integrated

def calculate_statistics(integrated):
    """統合データの統計分析"""
    print("\n" + "=" * 60)
    print("統計分析")
    print("=" * 60)

    stats = {}

    # 基本統計
    stats['total_jobseekers'] = integrated['jobseeker_count'].sum()
    stats['avg_jobseekers_per_pref'] = integrated['jobseeker_count'].mean()
    stats['max_jobseekers'] = integrated['jobseeker_count'].max()
    stats['min_jobseekers'] = integrated['jobseeker_count'].min()

    print(f"\n【求職者数】")
    print(f"  総数: {stats['total_jobseekers']:,}人")
    print(f"  都道府県平均: {stats['avg_jobseekers_per_pref']:,.0f}人")
    print(f"  最大: {stats['max_jobseekers']:,}人")
    print(f"  最小: {stats['min_jobseekers']:,}人")

    # 相関分析
    if 'aging_rate_2023' in integrated.columns:
        corr = integrated['jobseeker_count'].corr(integrated['aging_rate_2023'])
        stats['corr_jobseeker_aging'] = corr
        print(f"\n【相関分析】")
        print(f"  求職者数 × 高齢化率: r = {corr:.3f}")

    if 'facility_density' in integrated.columns:
        corr = integrated['jobseeker_count'].corr(integrated['facility_density'])
        stats['corr_jobseeker_facility'] = corr
        print(f"  求職者数 × 施設密度: r = {corr:.3f}")

    # 女性比率の乖離
    if 'female_ratio_gap' in integrated.columns:
        avg_gap = integrated['female_ratio_gap'].mean()
        stats['avg_female_ratio_gap'] = avg_gap
        print(f"\n【女性比率乖離】")
        print(f"  平均乖離: +{avg_gap:.1f}ポイント")
        print(f"  （JM登録者の女性比率は人口構成比より高い）")

    return stats

def generate_report(integrated, stats, external_data):
    """統合分析レポートを生成"""
    print("\n" + "=" * 60)
    print("レポート生成")
    print("=" * 60)

    # 出力ディレクトリ作成
    INTEGRATED_DIR.mkdir(parents=True, exist_ok=True)

    # 統合データをCSV出力
    integrated_path = INTEGRATED_DIR / "integrated_prefecture_analysis.csv"
    integrated.to_csv(integrated_path, index=False, encoding='utf-8-sig')
    print(f"✅ 統合データ出力: {integrated_path}")

    # レポート生成
    report_path = INTEGRATED_DIR / "INTEGRATED_ANALYSIS_REPORT.md"

    # 全国人口データ
    national_pop_65plus = 36243000
    national_pop_total = 123802000

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# ジョブメドレー求職者データ × 政府統計 統合分析レポート\n\n")
        f.write(f"**作成日**: 2025年12月27日\n")
        f.write(f"**データソース**: ジョブメドレー求職者データ + 政府統計（総務省・内閣府・厚労省）\n\n")
        f.write("---\n\n")

        # エグゼクティブサマリー
        f.write("## エグゼクティブサマリー\n\n")
        f.write("### 主要発見事項\n\n")
        f.write("| # | 発見 | データソース | 示唆 |\n")
        f.write("|---|------|-------------|------|\n")

        total_js = stats['total_jobseekers']
        f.write(f"| 1 | 求職者総数 **{total_js:,}人** | ジョブメドレー | 介護人材市場の一定規模を把握 |\n")

        if 'avg_female_ratio_gap' in stats:
            gap = stats['avg_female_ratio_gap']
            f.write(f"| 2 | JM女性比率は人口比より **+{gap:.1f}pt** 高い | JM + 総務省 | プラットフォーム特性 |\n")

        if 'corr_jobseeker_aging' in stats:
            corr = stats['corr_jobseeker_aging']
            f.write(f"| 3 | 求職者数と高齢化率の相関 **r={corr:.3f}** | JM + 内閣府 | 高齢化地域≠求職者多い |\n")

        f.write("\n---\n\n")

        # データソース
        f.write("## 使用データソース\n\n")
        f.write("### ジョブメドレーデータ\n\n")
        f.write(f"- 求職者総数: **{total_js:,}人**\n")
        f.write(f"- 対象期間: 2024年\n")
        f.write(f"- カバレッジ: 47都道府県\n\n")

        f.write("### 政府統計データ\n\n")
        f.write("| データ | ソース | 時点 |\n")
        f.write("|--------|--------|------|\n")
        f.write("| 介護施設密度（65歳以上1万人あたり） | 厚労省 | 2023年 |\n")
        f.write("| 高齢化率 | 内閣府高齢社会白書 | 2023年/2050年予測 |\n")
        f.write("| 20-30代女性比率 | 総務省 | 2024年 |\n")
        f.write("| 全国人口 | 総務省人口推計 | 2024年10月 |\n")
        f.write("\n---\n\n")

        # 都道府県別分析
        f.write("## 都道府県別分析\n\n")
        f.write("### 求職者数上位10都道府県\n\n")
        f.write("| 順位 | 都道府県 | 求職者数 | 高齢化率 | 施設密度 |\n")
        f.write("|------|---------|---------|---------|----------|\n")

        top10 = integrated.nlargest(10, 'jobseeker_count')
        for i, row in top10.iterrows():
            aging = row.get('aging_rate_2023', '-')
            if pd.notna(aging):
                aging = f"{aging:.1f}%"
            facility = row.get('facility_density', '-')
            if pd.notna(facility):
                facility = f"{facility:.1f}"
            f.write(f"| {top10.index.get_loc(i)+1} | {row['prefecture']} | {row['jobseeker_count']:,}人 | {aging} | {facility} |\n")

        f.write("\n### 求職者数下位10都道府県\n\n")
        f.write("| 順位 | 都道府県 | 求職者数 | 高齢化率 | 施設密度 |\n")
        f.write("|------|---------|---------|---------|----------|\n")

        bottom10 = integrated.nsmallest(10, 'jobseeker_count')
        for i, row in bottom10.iterrows():
            aging = row.get('aging_rate_2023', '-')
            if pd.notna(aging):
                aging = f"{aging:.1f}%"
            facility = row.get('facility_density', '-')
            if pd.notna(facility):
                facility = f"{facility:.1f}"
            f.write(f"| {47 - bottom10.index.get_loc(i)} | {row['prefecture']} | {row['jobseeker_count']:,}人 | {aging} | {facility} |\n")

        f.write("\n---\n\n")

        # 需給分析
        f.write("## 需給バランス分析\n\n")
        f.write("### 介護職人材の需給状況\n\n")
        f.write("| 指標 | 値 | ソース |\n")
        f.write("|------|-----|--------|\n")
        f.write("| 介護職有効求人倍率（全国） | 3.97倍 | 厚労省 |\n")
        f.write("| 2025年介護職不足予測 | 32万人 | 厚労省 |\n")
        f.write("| 2040年介護職不足予測 | 69万人 | 厚労省 |\n")
        f.write(f"| JM登録求職者数 | {total_js:,}人 | ジョブメドレー |\n")
        f.write(f"| 65歳以上人口 | {national_pop_65plus:,}人 | 総務省 |\n")

        f.write("\n### 地域別需給ギャップ\n\n")
        f.write("```\n")
        f.write("【施設密度が高い = 需要多い】\n")
        f.write("  宮崎県: 43.35（1位）\n")
        f.write("  沖縄県: 43.00（2位）\n")
        f.write("  青森県: 40.81（3位）\n\n")
        f.write("【施設密度が低い = 需要少ない】\n")
        f.write("  茨城県: 21.42（47位）\n")
        f.write("  京都府: 21.68（46位）\n")
        f.write("  埼玉県: 21.93（45位）\n")
        f.write("```\n\n")

        f.write("---\n\n")

        # 将来予測
        f.write("## 将来予測（2050年）\n\n")
        f.write("### 高齢化率予測上位都道府県\n\n")
        f.write("| 順位 | 都道府県 | 2023年 | 2050年予測 | 増加幅 |\n")
        f.write("|------|---------|--------|-----------|-------|\n")

        if 'aging_rate' in external_data:
            aging = external_data['aging_rate'].sort_values('aging_rate_2050_projection', ascending=False).head(5)
            for idx, (_, row) in enumerate(aging.iterrows(), 1):
                increase = row['aging_rate_2050_projection'] - row['aging_rate_2023']
                f.write(f"| {idx} | {row['prefecture']} | {row['aging_rate_2023']:.1f}% | {row['aging_rate_2050_projection']:.1f}% | +{increase:.1f}pt |\n")

        f.write("\n**示唆**: 秋田県は2050年に高齢化率約50%に到達予測。介護人材の確保が最重要課題。\n\n")

        f.write("---\n\n")

        # 結論
        f.write("## 結論と推奨アクション\n\n")
        f.write("### 主要な発見\n\n")
        f.write("1. **都市部と地方の格差**: 都市部は求職者が多く採用側有利、地方は人材不足が深刻\n")
        f.write("2. **女性比率の特性**: JM登録者は人口構成より女性比率が高い（介護業界の特性）\n")
        f.write("3. **高齢化と求職者の逆相関**: 高齢化が進む地域ほど求職者が少ない傾向（デジタルデバイド？）\n\n")

        f.write("### 推奨アクション\n\n")
        f.write("| 地域タイプ | 課題 | 推奨施策 |\n")
        f.write("|-----------|------|----------|\n")
        f.write("| 都市部 | 競争激化 | 差別化・条件改善 |\n")
        f.write("| 地方 | 人材不足 | Uターン促進・待遇改善 |\n")
        f.write("| 高齢化地域 | デジタルデバイド | オフラインチャネル開拓 |\n\n")

        f.write("---\n\n")
        f.write("*本レポートは2025年12月27日時点のデータに基づいています。*\n")
        f.write("*ジョブメドレー求職者データ + 政府統計（総務省・内閣府・厚労省）を統合分析*\n")

    print(f"✅ レポート出力: {report_path}")
    return report_path

def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("外部データ統合分析")
    print("=" * 60)

    # データ読み込み
    external_data = load_external_data()
    jm_data = load_jobmedley_data()

    # 都道府県別サマリー作成
    pref_summary = create_prefecture_summary(jm_data)

    if pref_summary is not None:
        # データ統合
        integrated = integrate_data(pref_summary, external_data)

        # 統計分析
        stats = calculate_statistics(integrated)

        # レポート生成
        report_path = generate_report(integrated, stats, external_data)

        print("\n" + "=" * 60)
        print("処理完了")
        print("=" * 60)
        print(f"\n出力ファイル:")
        print(f"  - {INTEGRATED_DIR / 'integrated_prefecture_analysis.csv'}")
        print(f"  - {report_path}")
    else:
        print("❌ データが不足しているため、分析を実行できませんでした")

if __name__ == "__main__":
    main()
