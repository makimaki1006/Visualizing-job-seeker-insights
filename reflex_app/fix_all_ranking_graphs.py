"""
全横棒グラフ（ランキング）修正スクリプト - 完全版

問題: すべてのランキング関数が市区町村選択を要求しているが、
      都道府県レベルで市区町村のランキングを表示すべき

修正方針:
1. 都道府県が選択されたら、その都道府県内の市区町村TOP10を表示
2. 市区町村が選択されたら、その市区町村に絞って表示
3. 色盲対応カラーパレットを適用

対象関数:
- flow_inflow_ranking, flow_outflow_ranking, flow_netflow_ranking
- gap_shortage_ranking, gap_surplus_ranking, gap_ratio_ranking
- rarity_national_license_ranking
- competition_national_license_ranking, competition_qualification_ranking, competition_female_ratio_ranking
"""

import re

def generate_fixed_ranking_function(func_name, row_type, sort_column, ascending=False, label_format=None, value_format="int"):
    """
    ランキング関数の修正版を生成

    Args:
        func_name: 関数名
        row_type: フィルタするrow_type
        sort_column: ソートに使うカラム名
        ascending: 昇順でソートするか
        label_format: ラベルのフォーマット（特殊な場合）
        value_format: 値のフォーマット（int, float, percent）
    """

    # 値のフォーマット処理
    if value_format == "int":
        value_line = "int(row.get('{0}', 0)) if pd.notna(row.get('{0}')) else 0".format(sort_column)
    elif value_format == "float":
        value_line = "float(row.get('{0}', 0)) if pd.notna(row.get('{0}')) else 0".format(sort_column)
    elif value_format == "percent":
        value_line = "float(row.get('{0}', 0) * 100) if pd.notna(row.get('{0}')) else 0".format(sort_column)
    else:
        value_line = "row.get('{0}', 0)".format(sort_column)

    # ラベルのフォーマット処理
    if label_format == "qualification":
        label_line = """qualification = str(row.get('category1', '')).strip()
                if qualification:
                    result.append({
                        "name": qualification,
                        "value": """ + value_line + """
                    })"""
    elif label_format == "competition_qual":
        label_line = """qualification = str(row.get('qualification', '')).strip()
                if qualification:
                    result.append({
                        "name": qualification,
                        "value": """ + value_line + """
                    })"""
    else:
        label_line = """result.append({
                "name": str(row.get('municipality', '不明')),
                "value": """ + value_line + """
            })"""

    template = f'''    @rx.var(cache=False)
    def {func_name}(self) -> List[Dict[str, Any]]:
        """ランキング Top 10（横棒グラフ用）"""
        if not self.is_loaded or self.df is None:
            return []

        df = self.df
        prefecture = self.selected_prefecture
        municipality = self.selected_municipality

        if not prefecture:
            return []

        # データをフィルタ
        if municipality:
            # 市区町村が選択されている場合
            filtered = df[
                (df['row_type'] == '{row_type}') &
                (df['prefecture'] == prefecture) &
                (df['municipality'] == municipality)
            ].copy()
        else:
            # 都道府県のみ選択されている場合
            filtered = df[
                (df['row_type'] == '{row_type}') &
                (df['prefecture'] == prefecture) &
                (df['municipality'].notna())
            ].copy()

        if filtered.empty:
            return []

        # ソート
        filtered = filtered.sort_values('{sort_column}', ascending={ascending}).head(10)

        result = []
        for _, row in filtered.iterrows():
            {label_line}

        return result'''

    # インデントを調整
    if label_format in ["qualification", "competition_qual"]:
        template = template.replace("{label_line}", label_line)
    else:
        template = template.replace("            {label_line}", label_line)

    return template

def fix_all_ranking_functions():
    """すべてのランキング関数を修正"""

    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    # 読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 修正する関数のリスト
    functions_to_fix = [
        # Flow関連
        ("flow_inflow_ranking", "FLOW", "inflow", False, None, "int"),
        ("flow_outflow_ranking", "FLOW", "outflow", False, None, "int"),
        ("flow_netflow_ranking", "FLOW", "net_flow", False, None, "int"),

        # Gap関連
        ("gap_shortage_ranking", "GAP", "gap", True, None, "int"),  # 負の値（不足）を昇順で
        ("gap_surplus_ranking", "GAP", "gap", False, None, "int"),  # 正の値（余剰）を降順で
        ("gap_ratio_ranking", "GAP", "gap_ratio", False, None, "float"),

        # Rarity関連 - 特殊処理が必要
        ("rarity_national_license_ranking", "RARITY", "rarity_score", False, "qualification", "float"),

        # Competition関連 - 特殊処理が必要
        ("competition_national_license_ranking", "COMPETITION", "competition_index", False, "competition_qual", "float"),
        ("competition_qualification_ranking", "COMPETITION", "competition_index", False, "competition_qual", "float"),
        ("competition_female_ratio_ranking", "COMPETITION", "female_ratio", False, None, "percent"),
    ]

    # 各関数を探して置換
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        replaced = False

        for func_info in functions_to_fix:
            func_name = func_info[0]
            if f"def {func_name}(self)" in line:
                print(f"修正中: {func_name}")

                # 既存の関数を削除（次の def まで）
                j = i + 1
                indent_level = len(line) - len(line.lstrip())
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() and not next_line.startswith(' ' * (indent_level + 1)):
                        if next_line.strip().startswith('def ') or next_line.strip().startswith('@'):
                            break
                    j += 1

                # 新しい関数を生成
                new_func = generate_fixed_ranking_function(*func_info)
                new_lines.append(new_func + '\n')

                i = j - 1  # 次の関数の直前まで進める
                replaced = True
                break

        if not replaced:
            new_lines.append(line)

        i += 1

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("\n全ランキング関数の修正が完了しました")
    print("修正された関数:")
    for func_info in functions_to_fix:
        print(f"  - {func_info[0]}")

if __name__ == "__main__":
    fix_all_ranking_functions()