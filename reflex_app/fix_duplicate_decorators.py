"""
重複した@rx.varデコレータを削除するスクリプト
"""

import re

def fix_duplicate_decorators():
    """重複した@rx.varデコレータを削除"""

    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    # ファイルを読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 削除する行番号（0-indexed）
    lines_to_remove = [
        2094,  # gap_surplus_ranking前の重複
        2137,  # gap_ratio_ranking前の重複
        2306,  # rarity_national_license_ranking前の重複
        2350,  # competition_national_license_ranking前の重複
        2394,  # competition_qualification_ranking前の重複
        2737,  # competition_female_ratio_ranking前の重複
        2988,  # urgency_retirement_age_ranking前の重複
        3034,  # urgency_employed_ranking前の重複
        3080,  # urgency_unemployed_ranking前の重複
    ]

    # 削除する行を-1でマーク（行番号は1-indexedなので-1）
    for line_num in lines_to_remove:
        # 実際の行番号（1-indexed）から配列インデックス（0-indexed）への変換
        idx = line_num - 1
        if idx < len(lines) and "@rx.var" in lines[idx]:
            print(f"削除: 行 {line_num}: {lines[idx].strip()}")
            lines[idx] = ""  # 空行に置換（削除）

    # ファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"\nDONE: {len(lines_to_remove)} duplicate decorators removed")

if __name__ == "__main__":
    fix_duplicate_decorators()