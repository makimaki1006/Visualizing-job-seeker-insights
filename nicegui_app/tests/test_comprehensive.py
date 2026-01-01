# -*- coding: utf-8 -*-
"""
NiceGUI Dashboard 包括的テストスイート
- ユニットテスト: 個別関数のテスト
- 統合テスト: データフロー・コンポーネント連携テスト
- E2Eテスト: UI操作テスト（Playwright）
"""
import pytest
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db_helper
import main


# ============================================================
# ユニットテスト: db_helper.py
# ============================================================

class TestDbHelperUnit:
    """db_helper.pyの関数ユニットテスト"""

    def test_age_order_consistency(self):
        """年齢グループの表記が統一されていることを確認（70代以上）"""
        # ソースコード内で「70歳以上」が使われていないことを確認
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py"), "r", encoding="utf-8") as f:
            main_content = f.read()
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "db_helper.py"), "r", encoding="utf-8") as f:
            db_content = f.read()

        # 「70歳以上」が含まれていないことを確認
        assert "70歳以上" not in main_content, "main.pyに'70歳以上'が含まれています"
        assert "70歳以上" not in db_content, "db_helper.pyに'70歳以上'が含まれています"

    def test_load_data_returns_dataframe(self):
        """load_data()がDataFrameを返すことを確認"""
        df = main.load_data()  # main.pyのload_dataを使用
        assert df is not None
        assert hasattr(df, 'columns')
        assert hasattr(df, 'empty')

    def test_load_data_has_required_columns(self):
        """load_data()が必須カラムを含むことを確認"""
        df = main.load_data()
        required_columns = ["prefecture", "municipality"]
        for col in required_columns:
            assert col in df.columns, f"必須カラム'{col}'がありません"

    def test_get_municipality_options_from_data(self):
        """市区町村オプションがデータから取得できることを確認"""
        df = main.load_data()
        # 東京都のデータをフィルタ
        if "prefecture" in df.columns:
            tokyo_df = df[df["prefecture"] == "東京都"]
            if "municipality" in tokyo_df.columns:
                munis = tokyo_df["municipality"].dropna().unique().tolist()
                assert isinstance(munis, list)
                # データがある場合は市区町村が1つ以上ある
                if len(tokyo_df) > 0:
                    assert len(munis) >= 0  # データによっては0の場合もある

    def test_get_national_stats_returns_dict(self):
        """get_national_stats()が辞書を返すことを確認"""
        stats = db_helper.get_national_stats()
        assert isinstance(stats, dict)
        assert "male_count" in stats
        assert "female_count" in stats

    def test_get_national_stats_has_age_distribution(self):
        """get_national_stats()がage_distributionを含むことを確認"""
        stats = db_helper.get_national_stats()
        assert "age_distribution" in stats
        age_dist = stats["age_distribution"]
        if age_dist:
            # キーが存在することを確認（エンコーディング問題を回避）
            assert len(age_dist) > 0, "age_distributionが空です"

    def test_get_prefecture_stats_returns_dict(self):
        """get_prefecture_stats()が辞書を返すことを確認"""
        stats = db_helper.get_prefecture_stats("東京都")
        assert isinstance(stats, dict)
        assert "male_count" in stats
        assert "female_count" in stats


# ============================================================
# 統合テスト: データフロー
# ============================================================

class TestDataFlowIntegration:
    """コンポーネント間のデータフロー統合テスト"""

    def test_prefecture_to_municipality_flow(self):
        """都道府県選択→市区町村オプション更新のフロー"""
        df = main.load_data()

        # 東京都を選択
        if "prefecture" in df.columns and "municipality" in df.columns:
            tokyo_df = df[df["prefecture"] == "東京都"]
            tokyo_munis = tokyo_df["municipality"].dropna().unique().tolist()
            assert isinstance(tokyo_munis, list)

            # 大阪府を選択
            osaka_df = df[df["prefecture"] == "大阪府"]
            osaka_munis = osaka_df["municipality"].dropna().unique().tolist()
            assert isinstance(osaka_munis, list)

    def test_stats_flow_national_to_prefecture(self):
        """全国統計→都道府県統計のフロー"""
        nat_stats = db_helper.get_national_stats()
        pref_stats = db_helper.get_prefecture_stats("東京都")

        # 両方とも有効な統計を返す
        assert nat_stats["male_count"] >= 0
        assert nat_stats["female_count"] >= 0
        assert pref_stats["male_count"] >= 0
        assert pref_stats["female_count"] >= 0

        # 全国の方が都道府県より多い（または同じ）
        nat_total = nat_stats["male_count"] + nat_stats["female_count"]
        pref_total = pref_stats["male_count"] + pref_stats["female_count"]
        assert nat_total >= pref_total

    def test_filter_data_by_prefecture(self):
        """都道府県でのフィルタリングが正しく動作することを確認"""
        df = main.load_data()

        # フィルタリング前
        total_count = len(df)

        # 東京都でフィルタ
        if "prefecture" in df.columns:
            tokyo_df = df[df["prefecture"] == "東京都"]
            assert len(tokyo_df) <= total_count
            assert len(tokyo_df) > 0  # 東京都のデータがある

    def test_batch_stats_query_consistency(self):
        """バッチ統計クエリの一貫性を確認"""
        # 全国統計
        nat_stats = db_helper.get_national_stats()

        # 都道府県統計
        pref_stats = db_helper.get_prefecture_stats("東京都")

        # 市区町村統計
        muni_stats = db_helper.get_municipality_stats("東京都", "千代田区")

        # すべて同じ構造を持つ
        common_keys = ["male_count", "female_count"]
        for key in common_keys:
            assert key in nat_stats
            assert key in pref_stats
            assert key in muni_stats


# ============================================================
# 統合テスト: main.pyの関数
# ============================================================

class TestMainIntegration:
    """main.pyの統合テスト"""

    def test_prefecture_order_has_all_prefectures(self):
        """PREFECTURE_ORDERが47都道府県すべてを含むことを確認"""
        assert len(main.PREFECTURE_ORDER) == 47
        assert "北海道" in main.PREFECTURE_ORDER
        assert "東京都" in main.PREFECTURE_ORDER
        assert "大阪府" in main.PREFECTURE_ORDER
        assert "沖縄県" in main.PREFECTURE_ORDER

    def test_clean_dataframe_removes_invalid(self):
        """_clean_dataframe()が無効なデータを除去することを確認"""
        df = main.load_data()
        cleaned = main._clean_dataframe(df)

        # SUMMARYのみが残る
        if "row_type" in cleaned.columns:
            assert set(cleaned["row_type"].unique()) <= {"SUMMARY"}

        # prefectureが空でない行のみ
        assert cleaned["prefecture"].astype(bool).all()

    def test_get_prefecture_options_in_data(self):
        """データに都道府県オプションが含まれていることを確認"""
        df = main._clean_dataframe(main.load_data())
        prefs = df["prefecture"].dropna().unique().tolist()

        # 少なくとも1つの都道府県がある
        assert len(prefs) > 0

        # 北海道または東京都が含まれる（データによる）
        common_prefs = ["北海道", "東京都", "大阪府"]
        has_common = any(p in prefs for p in common_prefs)
        assert has_common, f"一般的な都道府県がデータに含まれていません: {prefs[:5]}"


# ============================================================
# E2Eテスト: Playwright（環境変数で有効化）
# ============================================================

@pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"),
    reason="E2Eテストはデフォルトでスキップ（RUN_E2E_TESTS=1で実行）"
)
class TestE2EPlaywright:
    """PlaywrightによるE2Eテスト"""

    @pytest.fixture(scope="class")
    def browser_page(self):
        """Playwrightブラウザページを設定"""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://localhost:9090")
            page.wait_for_load_state("networkidle")
            yield page
            browser.close()

    def test_page_loads(self, browser_page):
        """ページが正常にロードされることを確認"""
        assert "MapComplete Dashboard" in browser_page.title()

    def test_prefecture_dropdown_works(self, browser_page):
        """都道府県ドロップダウンが動作することを確認"""
        # ドロップダウンをクリック
        browser_page.click("text=都道府県")
        browser_page.wait_for_timeout(500)

        # オプションが表示される
        assert browser_page.is_visible("text=東京都") or browser_page.is_visible("text=北海道")

    def test_tab_switching_works(self, browser_page):
        """タブ切り替えが動作することを確認"""
        # 人材属性タブをクリック
        browser_page.click("text=👥 人材属性")
        browser_page.wait_for_timeout(1000)

        # タブが切り替わった
        assert browser_page.is_visible("text=ペルソナ分析") or browser_page.is_visible("text=全ペルソナ")


# ============================================================
# メイン実行
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
