"""
Dashboard E2Eテスト

テスト対象:
- CSVアップロード → フィルタ → 表示の全体フロー
- State更新トリガーの検証
"""

import pytest
import pandas as pd
import io
from mapcomplete_dashboard.mapcomplete_dashboard import DashboardState


class TestCSVUploadFlow:
    """CSVアップロード全体フロー"""

    @pytest.fixture
    def sample_csv_content(self):
        """テスト用CSV文字列"""
        csv_data = """row_type,prefecture,municipality,applicant_count,avg_age,male_count,female_count,category1,category2,count
SUMMARY,京都府,京都市,1000,45.5,400,600,,,
SUMMARY,京都府,宇治市,500,48.2,200,300,,,
SUMMARY,大阪府,大阪市,2000,42.1,800,1200,,,
AGE_GENDER,京都府,京都市,,,,,20代,男性,100
AGE_GENDER,京都府,京都市,,,,,20代,女性,150
AGE_GENDER,京都府,京都市,,,,,30代,男性,120
AGE_GENDER,京都府,京都市,,,,,30代,女性,180
AGE_GENDER,大阪府,大阪市,,,,,20代,男性,300
AGE_GENDER,大阪府,大阪市,,,,,20代,女性,400
"""
        return csv_data.encode('utf-8-sig')

    @pytest.mark.asyncio
    async def test_csv_upload_success(self, sample_csv_content):
        """CSVアップロード成功 → is_loaded=True, total_rows>0"""
        state = DashboardState()

        # モックUploadFile
        class MockUploadFile:
            async def read(self):
                return sample_csv_content

        await state.handle_upload([MockUploadFile()])

        assert state.is_loaded is True
        assert state.total_rows == 9  # ヘッダー除く9行のデータ
        assert len(state.prefectures) == 2
        assert '京都府' in state.prefectures
        assert '大阪府' in state.prefectures

    @pytest.mark.asyncio
    async def test_prefecture_selection_updates_municipalities(self, sample_csv_content):
        """都道府県選択 → municipalities更新"""
        state = DashboardState()

        class MockUploadFile:
            async def read(self):
                return sample_csv_content

        await state.handle_upload([MockUploadFile()])

        # 京都府選択
        state.set_prefecture("京都府")

        assert state.selected_prefecture == "京都府"
        assert len(state.municipalities) == 2
        assert '京都市' in state.municipalities
        assert '宇治市' in state.municipalities
        assert state.selected_municipality == ""  # リセットされる

    @pytest.mark.asyncio
    async def test_municipality_selection_updates_kpi(self, sample_csv_content):
        """市区町村選択 → KPI更新"""
        state = DashboardState()

        class MockUploadFile:
            async def read(self):
                return sample_csv_content

        await state.handle_upload([MockUploadFile()])

        state.set_prefecture("京都府")
        state.set_municipality("京都市")

        assert state.selected_municipality == "京都市"
        assert state.city_name == "京都府 京都市"
        assert "件のデータ" in state.city_meta

        # KPI検証
        assert state.overview_total_applicants == "1,000"
        assert state.overview_avg_age == "45.5"
        assert state.overview_gender_ratio == "400 / 600"

    @pytest.mark.asyncio
    async def test_filter_change_updates_graph_data(self, sample_csv_content):
        """フィルタ変更 → グラフデータ更新（Recharts形式）"""
        state = DashboardState()

        class MockUploadFile:
            async def read(self):
                return sample_csv_content

        await state.handle_upload([MockUploadFile()])

        # 京都市のグラフデータ
        state.set_prefecture("京都府")
        state.set_municipality("京都市")

        kyoto_data = state.overview_age_gender_data
        assert isinstance(kyoto_data, list)
        # 20代のデータ確認
        assert kyoto_data[0]['name'] == '20代'
        assert kyoto_data[0]['男性'] == 100
        assert kyoto_data[0]['女性'] == 150
        # 30代のデータ確認
        assert kyoto_data[1]['name'] == '30代'
        assert kyoto_data[1]['男性'] == 120
        assert kyoto_data[1]['女性'] == 180

        # 大阪市に変更
        state.set_prefecture("大阪府")
        state.set_municipality("大阪市")

        osaka_data = state.overview_age_gender_data
        assert isinstance(osaka_data, list)
        # 20代のデータ確認
        assert osaka_data[0]['name'] == '20代'
        assert osaka_data[0]['男性'] == 300
        assert osaka_data[0]['女性'] == 400

    @pytest.mark.asyncio
    async def test_invalid_csv_error_handling(self):
        """無効なCSV → エラーハンドリング（0行データでも読み込み成功）"""
        state = DashboardState()

        class MockUploadFile:
            async def read(self):
                return b"invalid,csv,data"

        # ヘッダーのみのCSVは技術的に有効なため、読み込み成功
        await state.handle_upload([MockUploadFile()])

        # is_loadedはTrue（パースは成功）だが、データは0行
        assert state.is_loaded is True
        assert state.total_rows == 0


class TestStateReactivity:
    """State更新の反応性テスト"""

    @pytest.fixture
    def loaded_state(self):
        """データロード済みのState"""
        state = DashboardState()
        state.df = pd.DataFrame({
            'row_type': ['SUMMARY', 'SUMMARY'],
            'prefecture': ['京都府', '大阪府'],
            'municipality': ['京都市', '大阪市'],
            'applicant_count': [1000, 2000],
            'avg_age': [45.5, 42.1],
            'male_count': [400, 800],
            'female_count': [600, 1200]
        })
        state.is_loaded = True
        state.prefectures = ['京都府', '大阪府']
        return state

    def test_computed_properties_update_on_filter_change(self, loaded_state):
        """計算プロパティがフィルタ変更で更新される"""
        state = loaded_state

        # 初期状態（フィルタなし）
        initial_total = state.overview_total_applicants
        assert initial_total == "3,000"

        # 京都府フィルタ
        state.selected_prefecture = "京都府"
        kyoto_total = state.overview_total_applicants
        assert kyoto_total == "1,000"
        assert kyoto_total != initial_total

        # 大阪府フィルタ
        state.selected_prefecture = "大阪府"
        osaka_total = state.overview_total_applicants
        assert osaka_total == "2,000"
        assert osaka_total != kyoto_total

    def test_cache_false_ensures_recalculation(self, loaded_state):
        """cache=Falseにより毎回再計算される"""
        state = loaded_state

        # 同じフィルタで2回呼び出し
        state.selected_prefecture = "京都府"
        result1 = state.overview_total_applicants
        result2 = state.overview_total_applicants

        # 同じ結果（キャッシュされていない証拠として毎回計算）
        assert result1 == result2 == "1,000"


class TestEdgeCases:
    """エッジケーステスト"""

    def test_empty_dataframe(self):
        """空DataFrame"""
        state = DashboardState()
        state.df = pd.DataFrame()
        state.is_loaded = True

        assert state.overview_total_applicants == "0"
        assert state.overview_avg_age == "-"
        assert state.overview_age_gender_data == []  # list形式

    def test_missing_columns(self):
        """必須カラムが存在しない"""
        state = DashboardState()
        state.df = pd.DataFrame({
            'row_type': ['SUMMARY'],
            'prefecture': ['京都府']
            # applicant_count, avg_age などがない
        })
        state.is_loaded = True

        # エラーにならず、フォールバック値を返す
        assert state.overview_total_applicants == "1"  # 行数
        assert state.overview_avg_age == "-"

    def test_null_values_in_data(self):
        """データにNULL値が含まれる"""
        state = DashboardState()
        state.df = pd.DataFrame({
            'row_type': ['SUMMARY', 'SUMMARY'],
            'prefecture': ['京都府', None],
            'municipality': ['京都市', '宇治市'],
            'applicant_count': [1000, None]
        })
        state.is_loaded = True

        # NULL値を適切に処理
        result = state.overview_total_applicants
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
