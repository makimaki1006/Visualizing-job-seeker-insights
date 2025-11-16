"""
パフォーマンス最適化のE2Eテスト

3つのゼロ除算修正が正しく動作することを確認：
1. persona_avg_qualifications_data
2. cross_age_qualification_data
3. cross_employment_qualification_data
"""

import pytest
import pandas as pd
import numpy as np
from mapcomplete_dashboard.mapcomplete_dashboard import DashboardState


class TestPerformanceOptimizations:
    """パフォーマンス最適化のテスト"""

    @pytest.fixture
    def test_df(self):
        """テスト用DataFrameを作成"""
        return pd.DataFrame({
            'row_type': ['PERSONA_MUNI', 'PERSONA_MUNI', 'EMPLOYMENT_AGE_CROSS', 'EMPLOYMENT_AGE_CROSS'],
            'prefecture': ['京都府', '京都府', '京都府', '京都府'],
            'municipality': ['京都市', '京都市', '京都市', '京都市'],
            'category1': ['ペルソナA', 'ペルソナB', '就業中', '離職中'],
            'category2': ['20代', '30代', '20代', '30代'],
            'avg_qualifications': [2.0, 3.0, 2.5, 1.5],
            'national_license_rate': [0.08, 0.12, 0.10, 0.05],
            'count': [100, 200, 150, 50]
        })

    @pytest.fixture
    def test_df_with_zero_count(self):
        """count=0を含むテスト用DataFrame"""
        return pd.DataFrame({
            'row_type': ['PERSONA_MUNI', 'PERSONA_MUNI', 'EMPLOYMENT_AGE_CROSS', 'EMPLOYMENT_AGE_CROSS'],
            'prefecture': ['京都府', '京都府', '京都府', '京都府'],
            'municipality': ['京都市', '京都市', '京都市', '京都市'],
            'category1': ['ペルソナA', 'ペルソナB', '就業中', '離職中'],
            'category2': ['20代', '30代', '20代', '30代'],
            'avg_qualifications': [2.0, 3.0, 2.5, 1.5],
            'national_license_rate': [0.08, 0.12, 0.10, 0.05],
            'count': [0, 200, 0, 50]  # ゼロを含む
        })

    def test_persona_avg_qualifications_normal(self, test_df):
        """supply_persona_qual_data: 通常ケース"""
        state = DashboardState()
        state.df = test_df
        state.is_loaded = True  # 🔧 重要: データロード済みフラグ
        state.selected_prefecture = '京都府'
        state.selected_municipality = '京都市'

        result = state.supply_persona_qual_data  # 🔧 正しいプロパティ名

        # 2つのペルソナが返される
        assert len(result) == 2
        # 降順ソートされている（ペルソナBが先）
        assert result[0]['name'] == 'ペルソナB'
        assert result[0]['avg_qual'] == 3.0
        assert result[1]['name'] == 'ペルソナA'
        assert result[1]['avg_qual'] == 2.0

    def test_persona_avg_qualifications_zero_count(self, test_df_with_zero_count):
        """supply_persona_qual_data: ゼロ除算ケース"""
        state = DashboardState()
        state.df = test_df_with_zero_count
        state.is_loaded = True  # 🔧 重要: データロード済みフラグ
        state.selected_prefecture = '京都府'
        state.selected_municipality = '京都市'

        result = state.supply_persona_qual_data  # 🔧 正しいプロパティ名

        # count=0のペルソナAはavg_qual=0になる
        assert len(result) == 2
        persona_a = [r for r in result if r['name'] == 'ペルソナA'][0]
        assert persona_a['avg_qual'] == 0.0  # ゼロ除算は0を返す

        persona_b = [r for r in result if r['name'] == 'ペルソナB'][0]
        assert persona_b['avg_qual'] == 3.0

    def test_cross_age_qualification_normal(self, test_df):
        """cross_age_qualification_data: 通常ケース"""
        state = DashboardState()
        state.df = test_df
        state.is_loaded = True  # 🔧 重要: データロード済みフラグ
        state.selected_prefecture = '京都府'
        state.selected_municipality = '京都市'

        result = state.cross_age_qualification_data

        # 2つの年齢層が返される
        assert len(result) == 2
        # 年齢順にソートされている
        assert result[0]['age'] == '20代'
        assert result[1]['age'] == '30代'

        # 加重平均が正しく計算されている
        # 20代: avg_qual=2.5, national_rate=10%
        assert result[0]['avg_qual'] == 2.5
        assert result[0]['national_rate'] == 10.0

    def test_cross_age_qualification_zero_count(self, test_df_with_zero_count):
        """cross_age_qualification_data: ゼロ除算ケース"""
        state = DashboardState()
        state.df = test_df_with_zero_count
        state.is_loaded = True  # 🔧 重要: データロード済みフラグ
        state.selected_prefecture = '京都府'
        state.selected_municipality = '京都市'

        result = state.cross_age_qualification_data

        # count=0の20代はavg_qual=0, national_rate=0になる
        age_20s = [r for r in result if r['age'] == '20代'][0]
        assert age_20s['avg_qual'] == 0.0
        assert age_20s['national_rate'] == 0.0

        age_30s = [r for r in result if r['age'] == '30代'][0]
        assert age_30s['avg_qual'] == 1.5
        assert age_30s['national_rate'] == 5.0

    def test_cross_employment_qualification_normal(self, test_df):
        """cross_employment_qualification_data: 通常ケース"""
        state = DashboardState()
        state.df = test_df
        state.is_loaded = True  # 🔧 重要: データロード済みフラグ
        state.selected_prefecture = '京都府'
        state.selected_municipality = '京都市'

        result = state.cross_employment_qualification_data

        # 2つの就業状態が返される
        assert len(result) == 2

        # 就業中と離職中のデータが存在
        employment_status = [r['employment'] for r in result]
        assert '就業中' in employment_status
        assert '離職中' in employment_status

    def test_cross_employment_qualification_zero_count(self, test_df_with_zero_count):
        """cross_employment_qualification_data: ゼロ除算ケース"""
        state = DashboardState()
        state.df = test_df_with_zero_count
        state.is_loaded = True  # 🔧 重要: データロード済みフラグ
        state.selected_prefecture = '京都府'
        state.selected_municipality = '京都市'

        result = state.cross_employment_qualification_data

        # count=0の就業中はavg_qual=0, national_rate=0になる
        employed = [r for r in result if r['employment'] == '就業中'][0]
        assert employed['avg_qual'] == 0.0
        assert employed['national_rate'] == 0.0

        unemployed = [r for r in result if r['employment'] == '離職中'][0]
        assert unemployed['avg_qual'] == 1.5
        assert unemployed['national_rate'] == 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
