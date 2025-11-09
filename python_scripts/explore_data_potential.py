#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データの潜在的価値を探索するスクリプト

既存のデータから、まだ活用されていない次元や関係性を発見する
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict
from run_complete_v2_perfect import PerfectJobSeekerAnalyzer


def explore_data_dimensions(analyzer):
    """データの次元を探索"""

    print("=" * 100)
    print("【データ次元の探索】")
    print("=" * 100)

    df = analyzer.processed_data

    # 利用可能な次元をリストアップ
    dimensions = {
        '基本属性': ['age', 'age_bucket', 'gender'],
        '地理': ['residence_pref', 'residence_muni', 'desired_areas'],
        '資格・スキル': ['qualifications', 'qualification_count', 'has_national_license'],
        'キャリア': ['career', 'employment_status', 'desired_job'],
        '希望条件': ['desired_workstyle', 'desired_start', 'status']
    }

    print("\n【利用可能な分析軸】")
    for category, dims in dimensions.items():
        print(f"\n■ {category}")
        for dim in dims:
            if dim in df.columns:
                if dim == 'desired_areas' or dim == 'qualifications':
                    unique_count = "リスト型"
                else:
                    unique_count = df[dim].nunique()
                print(f"  - {dim}: {unique_count}種類")

    # 多次元クロス集計の可能性を検証
    print("\n\n" + "=" * 100)
    print("【多次元クロス集計の可能性】")
    print("=" * 100)

    # 3次元クロス集計のサンプル
    print("\n【3次元: 市町村 × 年齢層 × 性別】")

    # 希望勤務地を展開
    desired_munis = []
    for idx, row in df.iterrows():
        for area in row['desired_areas']:
            desired_munis.append({
                'target_muni': area['full'],
                'age_bucket': row['age_bucket'],
                'gender': row['gender'],
                'has_national_license': row['has_national_license'],
                'qualification_count': row['qualification_count'],
                'employment_status': row['employment_status'],
                'residence_pref': row['residence_pref']
            })

    desired_df = pd.DataFrame(desired_munis)

    # 3次元集計
    cross3d = desired_df.groupby(['target_muni', 'age_bucket', 'gender']).size().reset_index(name='count')
    cross3d = cross3d.sort_values('count', ascending=False)

    print(f"  - 総組み合わせ数: {len(cross3d):,}通り")
    print(f"  - 上位10組み合わせ:")
    print(cross3d.head(10).to_string(index=False))

    # 4次元クロス集計
    print("\n【4次元: 市町村 × 年齢層 × 性別 × 国家資格有無】")
    cross4d = desired_df.groupby(['target_muni', 'age_bucket', 'gender', 'has_national_license']).size().reset_index(name='count')
    cross4d = cross4d.sort_values('count', ascending=False)

    print(f"  - 総組み合わせ数: {len(cross4d):,}通り")
    print(f"  - 上位10組み合わせ:")
    print(cross4d.head(10).to_string(index=False))

    # 5次元クロス集計
    print("\n【5次元: 市町村 × 年齢層 × 性別 × 国家資格 × 就業状況】")
    cross5d = desired_df.groupby(['target_muni', 'age_bucket', 'gender', 'has_national_license', 'employment_status']).size().reset_index(name='count')
    cross5d = cross5d.sort_values('count', ascending=False)

    print(f"  - 総組み合わせ数: {len(cross5d):,}通り")
    print(f"  - 上位10組み合わせ:")
    print(cross5d.head(10).to_string(index=False))

    return desired_df


def explore_rarity_score(desired_df):
    """希少性スコアの算出"""

    print("\n\n" + "=" * 100)
    print("【希少性スコアの算出】")
    print("=" * 100)

    print("\n希少な組み合わせ（人材確保が困難な可能性）を特定")

    # 市町村 × 年齢層 × 性別 × 国家資格の組み合わせで集計
    rarity = desired_df.groupby(['target_muni', 'age_bucket', 'gender', 'has_national_license']).size().reset_index(name='count')

    # 希少性スコア = 1 / count（人数が少ないほど高スコア）
    rarity['rarity_score'] = 1 / rarity['count']
    rarity = rarity.sort_values('rarity_score', ascending=False)

    print(f"\n【最も希少な組み合わせ（上位20）】")
    print(rarity.head(20).to_string(index=False))

    # 逆に、最も競合が激しい組み合わせ
    print(f"\n【最も競合が激しい組み合わせ（下位10）】")
    print(rarity.tail(10).to_string(index=False))

    return rarity


def explore_supply_demand_gap(desired_df, analyzer):
    """需給ギャップ分析"""

    print("\n\n" + "=" * 100)
    print("【需給ギャップ分析】")
    print("=" * 100)

    df = analyzer.processed_data

    # 各市町村への「需要」（何人が希望しているか）
    demand = desired_df.groupby('target_muni').size().reset_index(name='demand_count')

    # 各市町村からの「供給」（何人が居住しているか）
    supply = df.groupby('residence_muni').size().reset_index(name='supply_count')
    supply.columns = ['target_muni', 'supply_count']

    # 需給マッチング
    gap = pd.merge(demand, supply, on='target_muni', how='outer').fillna(0)
    gap['demand_supply_ratio'] = gap['demand_count'] / (gap['supply_count'] + 1)  # ゼロ除算回避
    gap['gap'] = gap['demand_count'] - gap['supply_count']

    gap = gap.sort_values('demand_supply_ratio', ascending=False)

    print("\n【需要過多の市町村（需要 >> 供給）】")
    print("  ※ 外部から人材を集める必要がある地域")
    print(gap.head(15).to_string(index=False))

    print("\n【供給過多の市町村（供給 >> 需要）】")
    print("  ※ 居住者が外部に流出している地域")
    gap_supply_over = gap.sort_values('demand_supply_ratio', ascending=True)
    print(gap_supply_over.head(15).to_string(index=False))

    return gap


def explore_qualification_locality(desired_df):
    """資格別の地域選好性分析"""

    print("\n\n" + "=" * 100)
    print("【資格別の地域選好性分析】")
    print("=" * 100)

    print("\n特定の資格を持つ人が、どの都道府県を好む傾向があるか")

    # desired_dfに資格情報を追加する必要があるため、元データと結合
    # （簡略化のため、ここでは資格×市町村の分析は省略し、概念を示す）

    print("\n【分析イメージ】")
    print("  例: 「看護師資格保有者の60%は東京・神奈川・埼玉を希望」")
    print("  例: 「調理師資格保有者は地元志向が強く、居住地と希望地が一致する率が80%」")
    print("  例: 「保育士資格保有者は20km圏内の勤務地を希望する傾向（平均移動距離12km）」")

    print("\n  → これを全資格×全市町村で算出すれば、資格別の移動傾向が明確になる")


def explore_competition_analysis(desired_df):
    """競合分析：同じ市町村を希望する求職者の特性"""

    print("\n\n" + "=" * 100)
    print("【競合分析】")
    print("=" * 100)

    print("\n各市町村で「誰と競合するか」を分析")

    # 上位5市町村を抽出
    top_munis = desired_df['target_muni'].value_counts().head(5).index

    for muni in top_munis:
        muni_data = desired_df[desired_df['target_muni'] == muni]

        print(f"\n【{muni}】を希望する求職者の特性")
        print(f"  - 総数: {len(muni_data)}人")
        print(f"\n  年齢層分布:")
        age_dist = muni_data['age_bucket'].value_counts()
        for age, count in age_dist.items():
            print(f"    {age}: {count}人 ({count/len(muni_data)*100:.1f}%)")

        print(f"\n  性別分布:")
        gender_dist = muni_data['gender'].value_counts()
        for gender, count in gender_dist.items():
            print(f"    {gender}: {count}人 ({count/len(muni_data)*100:.1f}%)")

        print(f"\n  国家資格保有率: {muni_data['has_national_license'].mean():.1%}")

        print(f"\n  就業状況:")
        emp_dist = muni_data['employment_status'].value_counts()
        for emp, count in emp_dist.items():
            print(f"    {emp}: {count}人 ({count/len(muni_data)*100:.1f}%)")


def explore_network_centrality(desired_df, analyzer):
    """ネットワーク分析：どの市町村が人材フローの中心か"""

    print("\n\n" + "=" * 100)
    print("【ネットワーク中心性分析】")
    print("=" * 100)

    df = analyzer.processed_data

    # 居住地 → 希望勤務地のフローを集計
    flows = []
    for idx, row in df.iterrows():
        residence = row['residence_muni']
        if pd.isna(residence):
            continue
        for area in row['desired_areas']:
            flows.append({
                'source': residence,
                'target': area['municipality'] if area['municipality'] else area['prefecture'],
                'count': 1
            })

    flows_df = pd.DataFrame(flows)
    flows_agg = flows_df.groupby(['source', 'target']).size().reset_index(name='flow_count')

    # 各市町村の入次数（何箇所から流入があるか）
    in_degree = flows_agg.groupby('target')['source'].nunique().reset_index(name='in_degree')
    in_degree.columns = ['municipality', 'in_degree']
    in_degree = in_degree.sort_values('in_degree', ascending=False)

    print("\n【入次数（多様な地域から人材が集まる市町村）】")
    print("  ※ 人材吸引力が高い地域")
    print(in_degree.head(20).to_string(index=False))

    # 各市町村の出次数（何箇所へ流出しているか）
    out_degree = flows_agg.groupby('source')['target'].nunique().reset_index(name='out_degree')
    out_degree.columns = ['municipality', 'out_degree']
    out_degree = out_degree.sort_values('out_degree', ascending=False)

    print("\n【出次数（多様な地域へ人材が流出する市町村）】")
    print("  ※ 人材供給源として重要な地域")
    print(out_degree.head(20).to_string(index=False))

    # 媒介中心性の簡易版（どの市町村を経由すると効率的か）
    print("\n【ハブ市町村（入次数 × 出次数が高い）】")
    hub = pd.merge(in_degree, out_degree, on='municipality', how='outer').fillna(0)
    hub['hub_score'] = hub['in_degree'] * hub['out_degree']
    hub = hub.sort_values('hub_score', ascending=False)
    print(hub.head(20).to_string(index=False))


def propose_new_features():
    """新機能提案サマリー"""

    print("\n\n" + "=" * 100)
    print("【新機能提案サマリー】")
    print("=" * 100)

    proposals = {
        '1. 多次元クロス集計エンジン': {
            '現状': '2次元（市町村×ペルソナ）',
            '提案': '3-5次元のOLAP的集計（市町村×年齢×性別×資格×就業状況×居住地）',
            '価値': '任意の切り口でデータを見られる柔軟性',
            '工数': '2日',
            '出力': 'MultiDimensionalCrossTab.csv（ピボット可能な形式）'
        },
        '2. 希少性スコア': {
            '現状': '人数のみ表示',
            '提案': '希少な組み合わせを定量化（採用難易度の指標）',
            '価値': '「この条件の人材は希少」が一目でわかる',
            '工数': '0.5日',
            '出力': 'RarityScore.csv'
        },
        '3. 需給ギャップ分析': {
            '現状': 'なし',
            '提案': '市町村ごとの需要（希望者数）と供給（居住者数）のギャップ',
            '価値': '「外部から人材を集める必要がある地域」が明確に',
            '工数': '0.5日',
            '出力': 'SupplyDemandGap.csv'
        },
        '4. 資格別地域選好性': {
            '現状': 'Phase 7で資格分布のみ',
            '提案': '各資格保有者が好む都道府県・移動距離の傾向',
            '価値': '「看護師は50km圏内、調理師は20km圏内」など実務的知見',
            '工数': '1日',
            '出力': 'QualificationLocalityPreference.csv'
        },
        '5. 競合分析': {
            '現状': 'なし',
            '提案': '同じ市町村を希望する求職者の詳細プロファイル',
            '価値': '「この市町村では30代女性が多く競合する」',
            '工数': '0.5日',
            '出力': 'CompetitionProfile.csv'
        },
        '6. ネットワーク中心性': {
            '現状': 'Phase 6でフロー集計のみ',
            '提案': '入次数・出次数・ハブスコアで人材フローの中心地を特定',
            '価値': 'どの市町村が人材ハブか（東京、大阪など）',
            '工数': '1日',
            '出力': 'NetworkCentrality.csv'
        },
        '7. 動的セグメンテーション': {
            '現状': '固定セグメント（年齢層×性別×資格）',
            '提案': 'ユーザーが任意の条件でセグメント作成（GAS UI）',
            '価値': 'インタラクティブな分析が可能',
            '工数': '2日（GAS側実装含む）',
            '出力': 'DynamicSegmentation API（GAS関数）'
        },
        '8. 時系列トレンド分析': {
            '現状': 'なし（静的データ）',
            '提案': '複数時点のデータを比較（求職者の希望変化）',
            '価値': '「夏に東京希望が増える」など季節性の発見',
            '工数': '1.5日',
            '条件': '複数時点のデータが必要',
            '出力': 'TrendAnalysis.csv'
        },
        '9. 類似ペルソナ検索': {
            '現状': 'なし',
            '提案': '「この人と似た特性の人は、どこで働きたいか」をk-NNで検索',
            '価値': '個別の求職者に対するレコメンデーション',
            '工数': '1.5日',
            '出力': 'SimilarPersonaRecommendation API（GAS関数）'
        },
        '10. 効果量と多重比較補正': {
            '現状': 'Phase 2でp値のみ',
            '提案': 'Cohen\'s d、Cramér\'s V、Bonferroni補正',
            '価値': '統計的有意性だけでなく、実務的意義も評価',
            '工数': '0.5日',
            '出力': 'EnhancedStatisticalTests.csv（Phase 2拡張）'
        }
    }

    print("\n【提案一覧】")
    for i, (title, details) in enumerate(proposals.items(), 1):
        print(f"\n{title}")
        print("-" * 100)
        for key, value in details.items():
            print(f"  {key}: {value}")

    # 優先度評価
    print("\n\n" + "=" * 100)
    print("【優先度評価】")
    print("=" * 100)

    print("\n🔴 高優先度（即効性×実務価値が高い）")
    print("  1. 需給ギャップ分析（0.5日）")
    print("     → 「外部から人材を集める必要がある地域」が即座にわかる")
    print("\n  2. 希少性スコア（0.5日）")
    print("     → 採用難易度の定量化、実務判断に直結")
    print("\n  3. 競合分析（0.5日）")
    print("     → 各市町村での競合状況を把握、戦略立案に有用")

    print("\n🟡 中優先度（データ活用の深化）")
    print("  4. 多次元クロス集計エンジン（2日）")
    print("     → 柔軟なデータ探索が可能になる基盤")
    print("\n  5. ネットワーク中心性（1日）")
    print("     → 人材フローの構造を理解")
    print("\n  6. 資格別地域選好性（1日）")
    print("     → 資格ごとの移動傾向を把握")

    print("\n🟢 低優先度（条件付き・長期的）")
    print("  7. 動的セグメンテーション（2日）")
    print("     → GAS UI開発が必要、やや大掛かり")
    print("\n  8. 時系列トレンド分析（1.5日）")
    print("     → 複数時点のデータが前提")
    print("\n  9. 類似ペルソナ検索（1.5日）")
    print("     → 機械学習的アプローチ、やや高度")


def main():
    """メイン処理"""

    print("=" * 100)
    print("データの潜在的価値探索")
    print("=" * 100)

    # データ読み込み
    data_file = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251028_112441.csv")
    analyzer = PerfectJobSeekerAnalyzer(str(data_file))
    analyzer.load_data()
    analyzer.process_data()

    print(f"\n総レコード数: {len(analyzer.processed_data):,}件")

    # 1. データ次元の探索
    desired_df = explore_data_dimensions(analyzer)

    # 2. 希少性スコア
    rarity = explore_rarity_score(desired_df)

    # 3. 需給ギャップ分析
    gap = explore_supply_demand_gap(desired_df, analyzer)

    # 4. 資格別地域選好性（概念説明）
    explore_qualification_locality(desired_df)

    # 5. 競合分析
    explore_competition_analysis(desired_df)

    # 6. ネットワーク中心性
    explore_network_centrality(desired_df, analyzer)

    # 7. 新機能提案
    propose_new_features()


if __name__ == '__main__':
    main()
