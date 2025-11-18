# -*- coding: utf-8 -*-
"""
統合テスト実行スクリプト

データフィルタリング・ランキング計算・集計機能の連携を検証します。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest
from datetime import datetime

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "MapComplete_Complete_All_FIXED.csv"
)


class TestIntegrationFiltering:
    """IT-01〜IT-05: フィルタリング統合テスト"""

    @pytest.fixture
    def df(self):
        return pd.read_csv(CSV_PATH, low_memory=False)

    def test_it01_prefecture_filter_kyoto(self, df):
        """IT-01: 京都府フィルタリングが正しく動作する"""
        filtered = df[df['prefecture'] == '京都府']
        assert len(filtered) > 0, "京都府データが空"

        # すべてのrow_typeが含まれる
        row_types = filtered['row_type'].unique()
        assert len(row_types) >= 3, f"row_typeが不足: {row_types}"
        print(f"IT-01 PASS: 京都府 {len(filtered)}行, row_types={list(row_types)}")

    def test_it02_prefecture_filter_tokyo(self, df):
        """IT-02: 東京都フィルタリングが正しく動作する"""
        filtered = df[df['prefecture'] == '東京都']
        assert len(filtered) > 0, "東京都データが空"

        row_types = filtered['row_type'].unique()
        assert len(row_types) >= 3, f"row_typeが不足: {row_types}"
        print(f"IT-02 PASS: 東京都 {len(filtered)}行, row_types={list(row_types)}")

    def test_it03_municipality_filter(self, df):
        """IT-03: 市区町村フィルタリングが正しく動作する"""
        # 京都府のデータを取得
        kyoto_df = df[df['prefecture'] == '京都府']
        municipalities = kyoto_df['municipality'].dropna().unique()

        # 最初の市区町村でフィルタ
        if len(municipalities) > 0:
            first_muni = municipalities[0]
            filtered = kyoto_df[kyoto_df['municipality'] == first_muni]
            assert len(filtered) > 0, f"{first_muni}データが空"
            print(f"IT-03 PASS: {first_muni} {len(filtered)}行")
        else:
            pytest.skip("市区町村データなし")

    def test_it04_all_prefectures_filter(self, df):
        """IT-04: 全都道府県（すべて）フィルタリングが正しく動作する"""
        # 全データを使用（フィルタなし）
        total_rows = len(df)
        assert total_rows > 0, "全データが空"

        # 各row_typeのデータが存在
        for rt in ['FLOW', 'GAP', 'RARITY', 'COMPETITION']:
            count = len(df[df['row_type'] == rt])
            assert count > 0, f"{rt}データが空"

        print(f"IT-04 PASS: 全データ {total_rows}行")

    def test_it05_prefecture_change_data_differs(self, df):
        """IT-05: 都道府県変更でデータが異なることを確認"""
        kyoto_df = df[df['prefecture'] == '京都府']
        osaka_df = df[df['prefecture'] == '大阪府']

        # 行数が異なる（または同じでも内容が異なる）
        kyoto_count = len(kyoto_df)
        osaka_count = len(osaka_df)

        # 市区町村リストが異なる
        kyoto_cities = set(kyoto_df['municipality'].dropna().unique())
        osaka_cities = set(osaka_df['municipality'].dropna().unique())

        assert kyoto_cities != osaka_cities, "京都府と大阪府の市区町村が同じ"
        print(f"IT-05 PASS: 京都府{kyoto_count}行, 大阪府{osaka_count}行, 市区町村異なる")


class TestIntegrationRanking:
    """IT-06〜IT-10: ランキング統合テスト"""

    @pytest.fixture
    def df(self):
        return pd.read_csv(CSV_PATH, low_memory=False)

    def test_it06_flow_ranking_top10(self, df):
        """IT-06: FLOWランキングTop10が正しく計算される"""
        flow_df = df[df['row_type'] == 'FLOW'].copy()

        if 'net_flow' in flow_df.columns and len(flow_df) > 0:
            # net_flowでソート
            flow_df['net_flow'] = pd.to_numeric(flow_df['net_flow'], errors='coerce')
            top10 = flow_df.nlargest(10, 'net_flow')

            assert len(top10) <= 10, f"Top10が10件を超えている: {len(top10)}"
            assert len(top10) > 0, "Top10が空"

            # 降順になっていることを確認
            values = top10['net_flow'].values
            assert all(values[i] >= values[i+1] for i in range(len(values)-1)), "ソート順が不正"
            print(f"IT-06 PASS: FLOWランキングTop10 ({len(top10)}件)")
        else:
            pytest.skip("net_flowデータなし")

    def test_it07_gap_ranking_top10(self, df):
        """IT-07: GAPランキングTop10が正しく計算される"""
        gap_df = df[df['row_type'] == 'GAP'].copy()

        if 'gap' in gap_df.columns and len(gap_df) > 0:
            gap_df['gap'] = pd.to_numeric(gap_df['gap'], errors='coerce')
            top10 = gap_df.nlargest(10, 'gap')

            assert len(top10) <= 10
            assert len(top10) > 0
            print(f"IT-07 PASS: GAPランキングTop10 ({len(top10)}件)")
        else:
            pytest.skip("gapデータなし")

    def test_it08_rarity_ranking_top10(self, df):
        """IT-08: RARITYランキングTop10が正しく計算される"""
        rarity_df = df[df['row_type'] == 'RARITY'].copy()

        if 'rarity_score' in rarity_df.columns and len(rarity_df) > 0:
            rarity_df['rarity_score'] = pd.to_numeric(rarity_df['rarity_score'], errors='coerce')
            top10 = rarity_df.nlargest(10, 'rarity_score')

            assert len(top10) <= 10
            assert len(top10) > 0
            print(f"IT-08 PASS: RARITYランキングTop10 ({len(top10)}件)")
        else:
            pytest.skip("rarity_scoreデータなし")

    def test_it09_competition_ranking_top10(self, df):
        """IT-09: COMPETITIONランキングTop10が正しく計算される"""
        comp_df = df[df['row_type'] == 'COMPETITION'].copy()

        if 'total_applicants' in comp_df.columns and len(comp_df) > 0:
            comp_df['total_applicants'] = pd.to_numeric(comp_df['total_applicants'], errors='coerce')
            top10 = comp_df.nlargest(10, 'total_applicants')

            assert len(top10) <= 10
            assert len(top10) > 0
            print(f"IT-09 PASS: COMPETITIONランキングTop10 ({len(top10)}件)")
        else:
            pytest.skip("total_applicantsデータなし")

    def test_it10_filtered_ranking(self, df):
        """IT-10: フィルタ済みデータでランキングが正しく計算される"""
        # 京都府でフィルタ
        kyoto_df = df[df['prefecture'] == '京都府']
        flow_df = kyoto_df[kyoto_df['row_type'] == 'FLOW'].copy()

        if 'net_flow' in flow_df.columns and len(flow_df) > 0:
            flow_df['net_flow'] = pd.to_numeric(flow_df['net_flow'], errors='coerce')
            top10 = flow_df.nlargest(10, 'net_flow')

            # 全件が京都府であることを確認
            all_kyoto = all(top10['prefecture'] == '京都府')
            assert all_kyoto, "フィルタ外のデータが含まれている"
            print(f"IT-10 PASS: 京都府FLOWランキング ({len(top10)}件)")
        else:
            pytest.skip("京都府FLOWデータなし")


class TestIntegrationAggregation:
    """IT-11〜IT-15: 集計統合テスト"""

    @pytest.fixture
    def df(self):
        return pd.read_csv(CSV_PATH, low_memory=False)

    def test_it11_summary_data(self, df):
        """IT-11: SUMMARYデータが正しく集計されている"""
        summary_df = df[df['row_type'] == 'SUMMARY']

        if len(summary_df) > 0:
            # applicant_countが存在し、値がある
            if 'applicant_count' in summary_df.columns:
                total = pd.to_numeric(summary_df['applicant_count'], errors='coerce').sum()
                assert total > 0, "applicant_count合計が0"
                print(f"IT-11 PASS: SUMMARY applicant_count合計={total}")
            else:
                pytest.skip("applicant_countカラムなし")
        else:
            pytest.skip("SUMMARYデータなし")

    def test_it12_avg_age_calculation(self, df):
        """IT-12: 平均年齢が正しく計算されている"""
        if 'avg_age' in df.columns:
            ages = pd.to_numeric(df['avg_age'].dropna(), errors='coerce')
            valid_ages = ages[(ages > 18) & (ages < 100)]

            assert len(valid_ages) > 0, "有効な年齢データがない"

            # 平均値が妥当な範囲内
            mean_age = valid_ages.mean()
            assert 20 < mean_age < 60, f"平均年齢が異常: {mean_age}"
            print(f"IT-12 PASS: 平均年齢={mean_age:.1f}歳")
        else:
            pytest.skip("avg_ageカラムなし")

    def test_it13_female_ratio_range(self, df):
        """IT-13: 女性比率が0-100%の範囲内"""
        if 'female_ratio' in df.columns:
            ratios = pd.to_numeric(df['female_ratio'].dropna(), errors='coerce')

            # 0-1の範囲または0-100の範囲をチェック
            if ratios.max() <= 1:
                # 0-1形式
                assert ratios.min() >= 0, f"女性比率が負: {ratios.min()}"
                assert ratios.max() <= 1, f"女性比率が1超: {ratios.max()}"
            else:
                # 0-100形式
                assert ratios.min() >= 0, f"女性比率が負: {ratios.min()}"
                assert ratios.max() <= 100, f"女性比率が100超: {ratios.max()}"

            print(f"IT-13 PASS: 女性比率範囲 {ratios.min():.2f}-{ratios.max():.2f}")
        else:
            pytest.skip("female_ratioカラムなし")

    def test_it14_category_aggregation(self, df):
        """IT-14: カテゴリ別集計が正しく動作する"""
        if 'category1' in df.columns:
            categories = df['category1'].dropna().unique()
            assert len(categories) > 0, "カテゴリデータがない"

            # 各カテゴリにデータがある
            for cat in categories[:5]:  # 最初の5カテゴリをチェック
                count = len(df[df['category1'] == cat])
                assert count > 0, f"カテゴリ{cat}のデータがない"

            print(f"IT-14 PASS: {len(categories)}カテゴリ")
        else:
            pytest.skip("category1カラムなし")

    def test_it15_cross_prefecture_comparison(self, df):
        """IT-15: 都道府県間比較が正しく動作する"""
        prefectures = df['prefecture'].dropna().unique()

        # 少なくとも2つの都道府県で比較
        if len(prefectures) >= 2:
            pref1_count = len(df[df['prefecture'] == prefectures[0]])
            pref2_count = len(df[df['prefecture'] == prefectures[1]])

            assert pref1_count > 0 and pref2_count > 0
            print(f"IT-15 PASS: {prefectures[0]}={pref1_count}行, {prefectures[1]}={pref2_count}行")
        else:
            pytest.skip("比較する都道府県が不足")


def run_tests():
    """すべての統合テストを実行"""
    print("=" * 60)
    print("統合テスト実行")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",
    ])

    print("-" * 60)
    if exit_code == 0:
        print("All integration tests passed")
    else:
        print("Some tests failed")

    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
