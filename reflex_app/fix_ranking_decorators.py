"""
ランキング関数に@rx.varデコレータを正しく追加するスクリプト
重複削除スクリプトが削除しすぎた問題を修正
"""

def fix_ranking_decorators():
    """ランキング関数に@rx.varデコレータを追加"""

    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    # ファイルを読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 修正が必要な関数と行番号（1-indexed）
    functions_to_fix = [
        (2051, "gap_shortage_ranking"),
        (2095, "gap_surplus_ranking"),  # 2094が空になったので2095
        (2138, "gap_ratio_ranking"),    # 2137が空になったので2138
        (2307, "rarity_national_license_ranking"),  # 2306が空になったので2307
        (2351, "competition_national_license_ranking"),  # 2350が空になったので2351
        (2395, "competition_qualification_ranking"),  # 2394が空になったので2395
        (2738, "competition_female_ratio_ranking"),  # 2737が空になったので2738
        (2989, "urgency_retirement_age_ranking"),  # 2988が空になったので2989
        (3035, "urgency_employed_ranking"),  # 3034が空になったので3035
        (3081, "urgency_unemployed_ranking"),  # 3080が空になったので3081
    ]

    # 各関数の前に@rx.var(cache=False)を追加
    for line_num, func_name in functions_to_fix:
        idx = line_num - 1  # 0-indexed

        # 現在の行を確認
        if idx < len(lines) and f"def {func_name}" in lines[idx]:
            # 前の行が空行かどうか確認
            if idx > 0 and lines[idx-1].strip() == "":
                # 空行を@rx.varに置き換え
                lines[idx-1] = "    @rx.var(cache=False)\n"
                print(f"Fixed: {func_name} at line {line_num-1}")
            else:
                # 新しい行を挿入
                lines.insert(idx, "    @rx.var(cache=False)\n")
                print(f"Inserted decorator for: {func_name} at line {line_num}")

    # ファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"\nDONE: Fixed decorators for {len(functions_to_fix)} ranking functions")

if __name__ == "__main__":
    fix_ranking_decorators()