# -*- coding: utf-8 -*-
"""
ユニットテスト実行スクリプト

State計算プロパティの動作を検証します。
"""

import sys
import os

# パス追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest
from datetime import datetime

# CSVファイルパス
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "MapComplete_Complete_All_FIXED.csv"
)

class TestUnitDataStructure:
    """UT-01〜UT-10: データ構造の検証"""

    @pytest.fixture
    def df(self):
        """テストデータの読み込み"""
        return pd.read_csv(CSV_PATH)

    def test_ut01_csv_exists(self):
        """UT-01: CSVファイルが存在する"""
        assert os.path.exists(CSV_PATH), f"CSVファイルが見つかりません: {CSV_PATH}"
        print("✅ UT-01: CSVファイル存在確認 - PASS")

    def test_ut02_required_columns(self, df):
        """UT-02: 必須カラムが存在する"""
        required_columns = [
            'row_type', 'prefecture', 'municipality',
            'applicant_count', 'avg_age', 'female_ratio'
        ]
        missing = [col for col in required_columns if col not in df.columns]
        assert not missing, f"不足カラム: {missing}"
        print(f"✅ UT-02: 必須カラム確認 ({len(required_columns)}カラム) - PASS")

    def test_ut03_row_types(self, df):
        """UT-03: すべてのrow_typeが存在する"""
        expected_types = ['FLOW', 'GAP', 'RARITY', 'COMPETITION', 'SUMMARY']
        actual_types = df['row_type'].unique()

        for rt in expected_types:
            assert rt in actual_types, f"row_type '{rt}' が見つかりません"
        print(f"✅ UT-03: row_type確認 ({len(expected_types)}種類) - PASS")

    def test_ut04_flow_data_columns(self, df):
        """UT-04: FLOWデータに必要なカラムがある"""
        flow_df = df[df['row_type'] == 'FLOW']
        required = ['inflow', 'outflow', 'net_flow']

        for col in required:
            assert col in df.columns, f"FLOWデータに '{col}' カラムがありません"

        # 値が存在するか確認
        has_data = flow_df[required].notna().any().all()
        assert has_data, "FLOWデータに値がありません"
        print(f"✅ UT-04: FLOWデータカラム確認 - PASS")

    def test_ut05_gap_data_columns(self, df):
        """UT-05: GAPデータに必要なカラムがある"""
        gap_df = df[df['row_type'] == 'GAP']
        required = ['gap', 'demand_supply_ratio']

        for col in required:
            assert col in df.columns, f"GAPデータに '{col}' カラムがありません"

        has_data = gap_df[required].notna().any().all()
        assert has_data, "GAPデータに値がありません"
        print(f"✅ UT-05: GAPデータカラム確認 - PASS")

    def test_ut06_rarity_data_columns(self, df):
        """UT-06: RARITYデータに必要なカラムがある"""
        rarity_df = df[df['row_type'] == 'RARITY']
        required = ['rarity_score']

        for col in required:
            assert col in df.columns, f"RARITYデータに '{col}' カラムがありません"

        has_data = rarity_df[required].notna().any().all()
        assert has_data, "RARITYデータに値がありません"
        print(f"✅ UT-06: RARITYデータカラム確認 - PASS")

    def test_ut07_competition_data_columns(self, df):
        """UT-07: COMPETITIONデータに必要なカラムがある"""
        comp_df = df[df['row_type'] == 'COMPETITION']
        required = ['total_applicants']

        for col in required:
            assert col in df.columns, f"COMPETITIONデータに '{col}' カラムがありません"

        has_data = comp_df[required].notna().any().all()
        assert has_data, "COMPETITIONデータに値がありません"
        print(f"✅ UT-07: COMPETITIONデータカラム確認 - PASS")

    def test_ut08_prefecture_list(self, df):
        """UT-08: 都道府県データが存在する"""
        prefectures = df['prefecture'].dropna().unique()
        assert len(prefectures) > 0, "都道府県データがありません"
        assert len(prefectures) >= 47, f"都道府県が不足: {len(prefectures)}"
        print(f"✅ UT-08: 都道府県データ確認 ({len(prefectures)}都道府県) - PASS")

    def test_ut09_municipality_list(self, df):
        """UT-09: 市区町村データが存在する"""
        municipalities = df['municipality'].dropna().unique()
        assert len(municipalities) > 0, "市区町村データがありません"
        print(f"✅ UT-09: 市区町村データ確認 ({len(municipalities)}市区町村) - PASS")

    def test_ut10_numeric_values(self, df):
        """UT-10: 数値カラムが正しい型を持つ"""
        numeric_cols = ['applicant_count', 'avg_age', 'female_ratio']

        for col in numeric_cols:
            if col in df.columns:
                # NaN以外の値が数値であることを確認
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    try:
                        pd.to_numeric(non_null)
                    except Exception as e:
                        assert False, f"'{col}' に非数値データが含まれています: {e}"

        print(f"✅ UT-10: 数値カラム型確認 - PASS")


class TestUnitPrefectureFiltering:
    """UT-11〜UT-15: 都道府県フィルタリングの検証"""

    @pytest.fixture
    def df(self):
        return pd.read_csv(CSV_PATH)

    def test_ut11_kyoto_data_exists(self, df):
        """UT-11: 京都府のデータが存在する"""
        kyoto_df = df[df['prefecture'] == '京都府']
        assert len(kyoto_df) > 0, "京都府のデータがありません"
        print(f"✅ UT-11: 京都府データ確認 ({len(kyoto_df)}行) - PASS")

    def test_ut12_tokyo_data_exists(self, df):
        """UT-12: 東京都のデータが存在する"""
        tokyo_df = df[df['prefecture'] == '東京都']
        assert len(tokyo_df) > 0, "東京都のデータがありません"
        print(f"✅ UT-12: 東京都データ確認 ({len(tokyo_df)}行) - PASS")

    def test_ut13_osaka_data_exists(self, df):
        """UT-13: 大阪府のデータが存在する"""
        osaka_df = df[df['prefecture'] == '大阪府']
        assert len(osaka_df) > 0, "大阪府のデータがありません"
        print(f"✅ UT-13: 大阪府データ確認 ({len(osaka_df)}行) - PASS")

    def test_ut14_mie_data_exists(self, df):
        """UT-14: 三重県のデータが存在する"""
        mie_df = df[df['prefecture'] == '三重県']
        assert len(mie_df) > 0, "三重県のデータがありません"
        print(f"✅ UT-14: 三重県データ確認 ({len(mie_df)}行) - PASS")

    def test_ut15_prefecture_municipality_relation(self, df):
        """UT-15: 都道府県と市区町村の関係が正しい"""
        # 京都府の市区町村が京都府内にある
        kyoto_df = df[df['prefecture'] == '京都府']
        kyoto_cities = kyoto_df['municipality'].dropna().unique()

        # 京都市を含む市区町村（区レベル: 京都市左京区 等）が存在する
        has_kyoto_city = any('京都市' in city for city in kyoto_cities)
        assert has_kyoto_city, f"京都府に京都市関連データがありません: {list(kyoto_cities)[:5]}"
        print(f"✅ UT-15: 都道府県-市区町村関係確認 - PASS")


def run_tests():
    """すべてのユニットテストを実行"""
    print("=" * 60)
    print("ユニットテスト実行")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"CSVファイル: {CSV_PATH}")
    print("-" * 60)

    # pytestで実行
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # 最初の失敗で停止
    ])

    print("-" * 60)
    if exit_code == 0:
        print("✅ すべてのユニットテストが成功しました")
    else:
        print("❌ テストに失敗しました")

    return exit_code


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
