"""
DashboardState ユニットテスト

テスト対象:
- _get_filtered_df(): フィルタリングロジック
- overview_*(): 計算プロパティ
"""

import pytest
import pandas as pd
from mapcomplete_dashboard.mapcomplete_dashboard import DashboardState


class TestGetFilteredDf:
    """_get_filtered_df() のテスト"""

    @pytest.fixture
    def sample_df(self):
        """テスト用サンプルデータ"""
        return pd.DataFrame({
            'row_type': ['SUMMARY', 'SUMMARY', 'AGE_GENDER', 'AGE_GENDER'],
            'prefecture': ['京都府', '京都府', '大阪府', '大阪府'],
            'municipality': ['京都市', '宇治市', '大阪市', '堺市'],
            'applicant_count': [100, 50, 200, 75],
            'avg_age': [45.0, 48.0, 42.0, 50.0],
            'male_count': [40, 20, 80, 30],
            'female_count': [60, 30, 120, 45],
            'category1': [None, None, '20代', '30代'],
            'category2': [None, None, '男性', '女性'],
            'count': [0, 0, 50, 75]
        })

    def test_no_filter_returns_all(self, sample_df):
        """フィルタなし → 全データ返却"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state._get_filtered_df()

        assert len(result) == 4
        assert result.equals(sample_df)

    def test_prefecture_filter(self, sample_df):
        """都道府県フィルタ → 該当都道府県のみ"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True
        state.selected_prefecture = "京都府"

        result = state._get_filtered_df()

        assert len(result) == 2
        assert all(result['prefecture'] == '京都府')

    def test_prefecture_and_municipality_filter(self, sample_df):
        """都道府県+市区町村フィルタ → 該当市区町村のみ"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True
        state.selected_prefecture = "京都府"
        state.selected_municipality = "京都市"

        result = state._get_filtered_df()

        assert len(result) == 1
        assert result.iloc[0]['municipality'] == '京都市'

    def test_nonexistent_prefecture_returns_empty(self, sample_df):
        """存在しない都道府県 → 空DataFrame"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True
        state.selected_prefecture = "東京都"

        result = state._get_filtered_df()

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)

    def test_none_df_returns_empty(self):
        """df=None → 空DataFrame"""
        state = DashboardState()
        state.df = None

        result = state._get_filtered_df()

        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)


class TestOverviewTotalApplicants:
    """overview_total_applicants のテスト"""

    @pytest.fixture
    def sample_df(self):
        """テスト用サンプルデータ"""
        return pd.DataFrame({
            'row_type': ['SUMMARY', 'SUMMARY', 'AGE_GENDER'],
            'prefecture': ['京都府', '京都府', '京都府'],
            'municipality': ['京都市', '宇治市', '京都市'],
            'applicant_count': [100, 50, 0]
        })

    def test_summary_data_exists(self, sample_df):
        """SUMMARYデータあり → applicant_count合計"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.overview_total_applicants

        assert result == "150"

    def test_summary_data_with_filter(self, sample_df):
        """フィルタ適用 → フィルタ後の合計"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True
        state.selected_municipality = "京都市"

        result = state.overview_total_applicants

        assert result == "100"

    def test_no_summary_data_returns_row_count(self):
        """SUMMARYデータなし → 全行数"""
        df = pd.DataFrame({
            'row_type': ['AGE_GENDER', 'AGE_GENDER'],
            'prefecture': ['京都府', '京都府'],
            'municipality': ['京都市', '京都市']
        })
        state = DashboardState()
        state.df = df
        state.is_loaded = True

        result = state.overview_total_applicants

        assert result == "2"

    def test_empty_data_returns_zero(self):
        """データなし → "0" """
        state = DashboardState()
        state.df = pd.DataFrame()
        state.is_loaded = True

        result = state.overview_total_applicants

        assert result == "0"

    def test_not_loaded_returns_dash(self):
        """df未ロード → "-" """
        state = DashboardState()
        state.is_loaded = False

        result = state.overview_total_applicants

        assert result == "-"


class TestOverviewAgeGenderData:
    """overview_age_gender_data のテスト"""

    @pytest.fixture
    def sample_df(self):
        """テスト用サンプルデータ"""
        return pd.DataFrame({
            'row_type': ['AGE_GENDER', 'AGE_GENDER', 'AGE_GENDER', 'AGE_GENDER'],
            'prefecture': ['京都府', '京都府', '京都府', '京都府'],
            'municipality': ['京都市', '京都市', '京都市', '京都市'],
            'category1': ['20代', '20代', '30代', '30代'],
            'category2': ['男性', '女性', '男性', '女性'],
            'count': [50, 60, 80, 90]
        })

    def test_complete_data_returns_valid_list(self, sample_df):
        """完全データ → 正しいlist形式（Recharts対応）"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.overview_age_gender_data

        assert isinstance(result, list)
        assert len(result) == 6  # 全年齢層（20代〜70歳以上）
        # 20代データ確認
        assert result[0]['name'] == '20代'
        assert result[0]['男性'] == 50
        assert result[0]['女性'] == 60
        # 30代データ確認
        assert result[1]['name'] == '30代'
        assert result[1]['男性'] == 80
        assert result[1]['女性'] == 90
        # 他の年齢層は0（データなし）
        assert result[2]['name'] == '40代'
        assert result[2]['男性'] == 0
        assert result[2]['女性'] == 0

    def test_missing_age_group_fills_zero(self):
        """一部年齢層欠損 → 0で補完"""
        df = pd.DataFrame({
            'row_type': ['AGE_GENDER', 'AGE_GENDER'],
            'prefecture': ['京都府', '京都府'],
            'municipality': ['京都市', '京都市'],
            'category1': ['20代', '20代'],
            'category2': ['男性', '女性'],
            'count': [50, 60]
        })

        state = DashboardState()
        state.df = df
        state.is_loaded = True

        result = state.overview_age_gender_data

        # 20代のみデータがある
        assert len(result) == 6  # 全年齢層
        assert result[0]['name'] == '20代'
        assert result[0]['男性'] == 50
        assert result[0]['女性'] == 60
        # 30代以降は0
        assert result[1]['name'] == '30代'
        assert result[1]['男性'] == 0
        assert result[1]['女性'] == 0

    def test_no_age_gender_data_returns_empty_array(self):
        """AGE_GENDERデータなし → [] """
        df = pd.DataFrame({
            'row_type': ['SUMMARY'],
            'prefecture': ['京都府']
        })

        state = DashboardState()
        state.df = df
        state.is_loaded = True

        result = state.overview_age_gender_data

        assert result == []

    def test_not_loaded_returns_empty_array(self):
        """df未ロード → [] """
        state = DashboardState()
        state.is_loaded = False

        result = state.overview_age_gender_data

        assert result == []


class TestSupplyPanel:
    """supply パネルのテスト（GAS推定ロジック準拠）"""

    @pytest.fixture
    def sample_df(self):
        """テスト用サンプルデータ"""
        return pd.DataFrame({
            'row_type': ['SUMMARY', 'SUMMARY'],
            'prefecture': ['京都府', '京都府'],
            'municipality': ['京都市', '宇治市'],
            'applicant_count': [1000, 500],
            'avg_qualifications': [0.94, 0.89]
        })

    def test_supply_employed_60_percent(self, sample_df):
        """就業中 = 全体の60%"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.supply_employed

        assert result == "900"  # 1500 * 0.6 = 900

    def test_supply_unemployed_30_percent(self, sample_df):
        """離職中 = 全体の30%"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.supply_unemployed

        assert result == "450"  # 1500 * 0.3 = 450

    def test_supply_student_10_percent(self, sample_df):
        """在学中 = 全体の10%"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.supply_student

        assert result == "150"  # 1500 * 0.1 = 150

    def test_supply_national_license_3_percent(self, sample_df):
        """国家資格保有者 = 全体の3%"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.supply_national_license

        assert result == "45"  # 1500 * 0.03 = 45

    def test_supply_with_filter(self, sample_df):
        """フィルタ適用後の供給データ"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True
        state.selected_municipality = "京都市"

        # 京都市のみ (1000人)
        assert state.supply_employed == "600"  # 1000 * 0.6
        assert state.supply_unemployed == "300"  # 1000 * 0.3
        assert state.supply_student == "100"  # 1000 * 0.1

    def test_supply_avg_qualifications(self, sample_df):
        """平均資格保有数"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.supply_avg_qualifications

        # 平均: (0.94 + 0.89) / 2 = 0.915
        assert result == "0.92"  # 小数点2位四捨五入

    def test_supply_qualification_buckets_data(self, sample_df):
        """資格バケット分布データ（GAS推定ロジック・Recharts形式）"""
        state = DashboardState()
        state.df = sample_df
        state.is_loaded = True

        result = state.supply_qualification_buckets_data

        # 合計1500人の場合:
        # 資格なし: 20% = 300
        # 1資格: 30% = 450
        # 2資格: 25% = 375
        # 3資格以上: 25% = 375
        assert isinstance(result, list)
        assert len(result) == 4
        assert result[0] == {'name': '資格なし', 'count': 300}
        assert result[1] == {'name': '1資格', 'count': 450}
        assert result[2] == {'name': '2資格', 'count': 375}
        assert result[3] == {'name': '3資格以上', 'count': 375}

    def test_supply_empty_data_returns_zero(self):
        """データなし → "0" """
        state = DashboardState()
        state.df = pd.DataFrame()
        state.is_loaded = True

        assert state.supply_employed == "0"
        assert state.supply_unemployed == "0"
        assert state.supply_student == "0"
        assert state.supply_national_license == "0"
        assert state.supply_avg_qualifications == "-"
        assert state.supply_qualification_buckets_data == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
