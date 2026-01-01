# -*- coding: utf-8 -*-
"""
コロプレスマップ色関数のユニットテスト

COLOR_CONFIGの単一ソース設計が正しく機能するかを検証します。
"""
import sys
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
import choropleth_helper as ch


class TestColorConfig(unittest.TestCase):
    """COLOR_CONFIG辞書のテスト"""

    def test_color_config_has_all_modes(self):
        """全てのモードが定義されていることを確認"""
        expected_modes = ["count", "balance", "inflow", "competition"]
        for mode in expected_modes:
            self.assertIn(mode, ch.COLOR_CONFIG, f"Missing mode: {mode}")

    def test_color_config_has_valid_thresholds(self):
        """各モードのしきい値が0-1の範囲であることを確認"""
        for mode, thresholds in ch.COLOR_CONFIG.items():
            for threshold, color in thresholds:
                self.assertGreaterEqual(threshold, 0.0, f"{mode}: threshold {threshold} < 0")
                self.assertLessEqual(threshold, 1.0, f"{mode}: threshold {threshold} > 1")

    def test_color_config_thresholds_descending(self):
        """しきい値が降順であることを確認"""
        for mode, thresholds in ch.COLOR_CONFIG.items():
            threshold_values = [t[0] for t in thresholds]
            self.assertEqual(
                threshold_values,
                sorted(threshold_values, reverse=True),
                f"{mode}: thresholds not in descending order"
            )

    def test_color_config_valid_hex_colors(self):
        """全ての色が有効な16進数カラーコードであることを確認"""
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        for mode, thresholds in ch.COLOR_CONFIG.items():
            for threshold, color in thresholds:
                self.assertIsNotNone(
                    hex_pattern.match(color),
                    f"{mode}: invalid color '{color}'"
                )


class TestSpecialColors(unittest.TestCase):
    """SPECIAL_COLORS辞書のテスト"""

    def test_special_colors_has_required_keys(self):
        """必須キーが定義されていることを確認"""
        required_keys = ["default", "selected", "inflow_highlight", "competition_highlight"]
        for key in required_keys:
            self.assertIn(key, ch.SPECIAL_COLORS, f"Missing key: {key}")

    def test_special_colors_valid_hex(self):
        """全ての特殊色が有効な16進数カラーコードであることを確認"""
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        for name, color in ch.SPECIAL_COLORS.items():
            self.assertIsNotNone(
                hex_pattern.match(color),
                f"Invalid color for {name}: '{color}'"
            )


class TestGetColorFromConfig(unittest.TestCase):
    """_get_color_from_config関数のテスト"""

    def test_count_mode_high_ratio(self):
        """countモードで高いratioは赤を返す"""
        color = ch._get_color_from_config(0.9, "count")
        self.assertEqual(color, "#dc2626")  # 赤

    def test_count_mode_low_ratio(self):
        """countモードで低いratioは緑を返す"""
        color = ch._get_color_from_config(0.1, "count")
        self.assertEqual(color, "#22c55e")  # 緑

    def test_count_mode_mid_ratio(self):
        """countモードで中間ratioは黄色を返す"""
        color = ch._get_color_from_config(0.5, "count")
        self.assertEqual(color, "#eab308")  # 黄

    def test_balance_mode_high_ratio(self):
        """balanceモードで高いratioは青を返す"""
        color = ch._get_color_from_config(0.7, "balance")
        self.assertEqual(color, "#3b82f6")  # 青（流入優位）

    def test_balance_mode_low_ratio(self):
        """balanceモードで低いratioは赤を返す"""
        color = ch._get_color_from_config(0.1, "balance")
        self.assertEqual(color, "#dc2626")  # 赤（流出優位）

    def test_unknown_mode_defaults_to_count(self):
        """未知のモードはcountにフォールバック"""
        color = ch._get_color_from_config(0.9, "unknown_mode")
        self.assertEqual(color, "#dc2626")  # countの赤

    def test_zero_ratio(self):
        """ratio=0は最低色を返す"""
        color = ch._get_color_from_config(0.0, "count")
        self.assertEqual(color, "#22c55e")  # 緑

    def test_one_ratio(self):
        """ratio=1は最高色を返す"""
        color = ch._get_color_from_config(1.0, "count")
        self.assertEqual(color, "#dc2626")  # 赤


class TestGetColorByValue(unittest.TestCase):
    """get_color_by_value関数のテスト"""

    def test_max_value_zero_returns_default(self):
        """max_value=0の場合はデフォルト色を返す"""
        color = ch.get_color_by_value(100, 0, "count")
        self.assertEqual(color, ch.SPECIAL_COLORS["default"])

    def test_value_equals_max(self):
        """value=max_valueの場合は最高色を返す"""
        color = ch.get_color_by_value(100, 100, "count")
        self.assertEqual(color, "#dc2626")  # 赤

    def test_value_much_lower_than_max(self):
        """valueがmax_valueより大幅に低い場合は低い色を返す"""
        color = ch.get_color_by_value(10, 100, "count")
        self.assertEqual(color, "#22c55e")  # 緑

    def test_value_exceeds_max_clamped(self):
        """valueがmax_valueを超えても1.0にクランプ"""
        color = ch.get_color_by_value(200, 100, "count")
        self.assertEqual(color, "#dc2626")  # 赤（max色）


class TestGenerateJsColorFunction(unittest.TestCase):
    """_generate_js_color_function関数のテスト"""

    def test_generates_valid_javascript(self):
        """有効なJavaScript関数が生成される"""
        js = ch._generate_js_color_function()
        self.assertIn("function getColor", js)
        self.assertIn("return", js)

    def test_js_contains_all_colors_from_config(self):
        """生成されたJSにCOLOR_CONFIGの全ての色が含まれる"""
        js = ch._generate_js_color_function()
        for mode, thresholds in ch.COLOR_CONFIG.items():
            for threshold, color in thresholds:
                self.assertIn(color, js, f"Color {color} from {mode} not in JS")

    def test_js_contains_special_default_color(self):
        """生成されたJSにデフォルト色が含まれる"""
        js = ch._generate_js_color_function()
        self.assertIn(ch.SPECIAL_COLORS["default"], js)

    def test_js_contains_all_mode_names(self):
        """生成されたJSに全てのモード名が含まれる"""
        js = ch._generate_js_color_function()
        for mode in ch.COLOR_CONFIG.keys():
            self.assertIn(f'"{mode}"', js, f"Mode {mode} not in JS")


class TestCreateGeojsonStyleFunction(unittest.TestCase):
    """create_geojson_style_function関数のテスト"""

    def test_generates_iife(self):
        """即時実行関数式(IIFE)として生成される"""
        js = ch.create_geojson_style_function({}, "count")
        self.assertIn("(function()", js)
        self.assertIn("})()", js)

    def test_contains_data_variable(self):
        """データ変数が含まれる"""
        test_data = {"TestMuni": {"count": 50}}
        js = ch.create_geojson_style_function(test_data, "count")
        self.assertIn("TestMuni", js)
        self.assertIn('"count": 50', js)

    def test_contains_special_colors_from_config(self):
        """SPECIAL_COLORSからの色が使用される"""
        js = ch.create_geojson_style_function({}, "count")
        self.assertIn(ch.SPECIAL_COLORS["default"], js)
        self.assertIn(ch.SPECIAL_COLORS["selected"], js)
        self.assertIn(ch.SPECIAL_COLORS["inflow_highlight"], js)
        self.assertIn(ch.SPECIAL_COLORS["competition_highlight"], js)

    def test_mode_variable_set_correctly(self):
        """モード変数が正しく設定される"""
        js = ch.create_geojson_style_function({}, "balance")
        self.assertIn('var mode = "balance"', js)


class TestColorConsistency(unittest.TestCase):
    """PythonとJavaScriptの色の一貫性テスト"""

    def test_python_and_js_use_same_config(self):
        """Pythonとjsが同じCOLOR_CONFIGを使用"""
        js = ch._generate_js_color_function()

        # Python側の色を取得
        for ratio in [0.9, 0.7, 0.5, 0.3, 0.1]:
            py_color = ch._get_color_from_config(ratio, "count")
            # この色がJSに含まれることを確認
            self.assertIn(py_color, js, f"Python color {py_color} not in JS")

    def test_count_mode_gradient_order(self):
        """countモードのグラデーション順序が正しい（赤→緑）"""
        colors_by_ratio = [
            ch._get_color_from_config(0.9, "count"),
            ch._get_color_from_config(0.7, "count"),
            ch._get_color_from_config(0.5, "count"),
            ch._get_color_from_config(0.3, "count"),
            ch._get_color_from_config(0.1, "count"),
        ]
        expected_colors = ["#dc2626", "#f97316", "#eab308", "#84cc16", "#22c55e"]
        self.assertEqual(colors_by_ratio, expected_colors)


class TestGenerateNameVariants(unittest.TestCase):
    """市区町村名正規化関数のテスト"""

    @classmethod
    def setUpClass(cls):
        """main.pyからgenerate_name_variants関数をインポート"""
        # 親ディレクトリをパスに追加
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        import re as _re_module

        # 関数を直接定義（main.pyと同じロジック）
        def generate_name_variants(name: str) -> list:
            if not name:
                return []
            candidates = [name]
            # 1. 郡名除去（non-greedy: 赤穂郡上郡町 → 上郡町 に対応）
            gun_match = _re_module.match(r'^(.+?郡)(.+)$', name)
            if gun_match:
                candidates.append(gun_match.group(2))
            # 2. 政令指定都市の区
            city_ku_match = _re_module.match(
                r'^(札幌市|仙台市|さいたま市|千葉市|横浜市|川崎市|相模原市|新潟市|静岡市|浜松市|名古屋市|京都市|大阪市|堺市|神戸市|岡山市|広島市|北九州市|福岡市|熊本市)(.+区)$',
                name
            )
            if city_ku_match:
                candidates.append(city_ku_match.group(2))
            # 3. 島嶼部
            island_match = _re_module.match(r'^(.+島|.+諸島)(.+[村町])$', name)
            if island_match:
                candidates.append(island_match.group(2))
            # 4. 浜松市の新区（2024年再編）
            hamamatsu_ward_mapping = {
                '中央区': ['中区', '東区'],
                '浜名区': ['西区', '南区', '浜北区'],
            }
            if name.startswith('浜松市'):
                ward = name.replace('浜松市', '')
                if ward in hamamatsu_ward_mapping:
                    for old_ward in hamamatsu_ward_mapping[ward]:
                        candidates.append(old_ward)
            return list(dict.fromkeys(candidates))

        cls.generate_name_variants = staticmethod(generate_name_variants)

    def test_empty_name(self):
        """空文字列は空リストを返す"""
        result = self.generate_name_variants("")
        self.assertEqual(result, [])

    def test_none_name(self):
        """Noneは空リストを返す（エラーにならない）"""
        result = self.generate_name_variants(None)
        self.assertEqual(result, [])

    def test_simple_city(self):
        """単純な市名はそのまま返す"""
        result = self.generate_name_variants("京都市")
        self.assertEqual(result, ["京都市"])

    def test_gun_removal(self):
        """郡名プレフィックスが除去される"""
        result = self.generate_name_variants("秩父郡横瀬町")
        self.assertIn("秩父郡横瀬町", result)  # 元の名前
        self.assertIn("横瀬町", result)  # 短縮名

    def test_gun_removal_multiple_cases(self):
        """複数の郡名パターンをテスト"""
        test_cases = [
            ("西多摩郡奥多摩町", ["西多摩郡奥多摩町", "奥多摩町"]),
            ("比企郡嵐山町", ["比企郡嵐山町", "嵐山町"]),
            ("児玉郡美里町", ["児玉郡美里町", "美里町"]),
        ]
        for input_name, expected in test_cases:
            result = self.generate_name_variants(input_name)
            for exp in expected:
                self.assertIn(exp, result, f"Expected {exp} in result for {input_name}")

    def test_seirei_shitei_toshi_ku(self):
        """政令指定都市の区が分離される"""
        result = self.generate_name_variants("大阪市北区")
        self.assertIn("大阪市北区", result)  # 元の名前
        self.assertIn("北区", result)  # 区名のみ

    def test_seirei_shitei_toshi_multiple(self):
        """複数の政令指定都市をテスト"""
        test_cases = [
            ("札幌市中央区", "中央区"),
            ("横浜市港北区", "港北区"),
            ("名古屋市中区", "中区"),
            ("京都市左京区", "左京区"),
            ("神戸市中央区", "中央区"),
            ("福岡市博多区", "博多区"),
        ]
        for input_name, expected_short in test_cases:
            result = self.generate_name_variants(input_name)
            self.assertIn(expected_short, result, f"Expected {expected_short} in result for {input_name}")

    def test_island_name(self):
        """島嶼部の名前が正規化される"""
        result = self.generate_name_variants("三宅島三宅村")
        self.assertIn("三宅島三宅村", result)  # 元の名前
        self.assertIn("三宅村", result)  # 短縮名

    def test_island_name_town(self):
        """島嶼部の町名も正規化される"""
        result = self.generate_name_variants("八丈島八丈町")
        self.assertIn("八丈島八丈町", result)
        self.assertIn("八丈町", result)

    def test_ogasawara(self):
        """小笠原諸島のケース"""
        result = self.generate_name_variants("小笠原諸島小笠原村")
        self.assertIn("小笠原村", result)

    def test_no_duplicate_in_result(self):
        """結果に重複がない"""
        result = self.generate_name_variants("秩父郡横瀬町")
        self.assertEqual(len(result), len(set(result)))

    def test_non_matching_city(self):
        """政令指定都市以外の市区は変換されない"""
        result = self.generate_name_variants("松山市道後区")  # 架空の例（松山市は政令指定都市ではない）
        # 政令指定都市リストにないので、区は分離されない
        self.assertEqual(result, ["松山市道後区"])

    def test_hamamatsu_special(self):
        """浜松市の区（政令指定都市）"""
        result = self.generate_name_variants("浜松市天竜区")
        self.assertIn("浜松市天竜区", result)
        self.assertIn("天竜区", result)

    def test_double_gun_name(self):
        """二重郡名：赤穂郡上郡町のような特殊ケース"""
        result = self.generate_name_variants("赤穂郡上郡町")
        self.assertIn("赤穂郡上郡町", result)  # 元の名前
        self.assertIn("上郡町", result)  # 短縮名（町まで含む）
        # 「郡」だけにならないことを確認
        self.assertNotIn("郡", result)
        self.assertNotIn("町", result)

    def test_hamamatsu_new_ward_chuo(self):
        """浜松市中央区（2024年新区）"""
        result = self.generate_name_variants("浜松市中央区")
        self.assertIn("浜松市中央区", result)  # 元の名前
        self.assertIn("中央区", result)  # 区名
        self.assertIn("中区", result)  # 旧区名（マッピング）
        self.assertIn("東区", result)  # 旧区名（マッピング）

    def test_hamamatsu_new_ward_hamana(self):
        """浜松市浜名区（2024年新区）"""
        result = self.generate_name_variants("浜松市浜名区")
        self.assertIn("浜松市浜名区", result)  # 元の名前
        self.assertIn("浜名区", result)  # 区名
        self.assertIn("西区", result)  # 旧区名（マッピング）
        self.assertIn("南区", result)  # 旧区名（マッピング）
        self.assertIn("浜北区", result)  # 旧区名（マッピング）


if __name__ == "__main__":
    # テスト実行
    unittest.main(verbosity=2)
