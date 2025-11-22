"""
最終的なデコレータ修正スクリプト
問題: gap_surplus_ranking等がEventHandlerとして認識される
解決: 正しく@rx.var(cache=False)デコレータを設定
"""

import re

def fix_final_decorators():
    """すべてのランキング関数のデコレータを完全に修正"""

    file_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py"

    # ファイルを読み込み
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修正が必要な関数のリスト（名前と行番号）
    functions_to_fix = [
        "flow_inflow_ranking",
        "flow_outflow_ranking",
        "flow_netflow_ranking",
        "gap_shortage_ranking",
        "gap_surplus_ranking",
        "gap_ratio_ranking",
        "rarity_national_license_ranking",
        "competition_national_license_ranking",
        "competition_qualification_ranking",
        "competition_female_ratio_ranking",
        "urgency_retirement_age_ranking",
        "urgency_employed_ranking",
        "urgency_unemployed_ranking"
    ]

    for func_name in functions_to_fix:
        # 正規表現パターンを作成
        # @rx.var行がある場合とない場合の両方に対応
        pattern = rf'(\s*)(@rx\.var.*?\n)?(\s*def {func_name}\(self.*?\):)'

        # 正しいデコレータ付きの関数定義に置換
        replacement = r'\1    @rx.var(cache=False)\n\1    def ' + func_name + r'(self) -> List[Dict[str, Any]]:'

        # 置換実行
        old_content = content
        content = re.sub(pattern, replacement, content)

        if old_content != content:
            print(f"Fixed: {func_name}")
        else:
            print(f"Not found or already correct: {func_name}")

    # ファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("\nAll decorator fixes completed!")
    print("Next steps:")
    print("1. Run: reflex run")
    print("2. Check http://localhost:3000")
    print("3. Test horizontal bar charts in all tabs")

if __name__ == "__main__":
    fix_final_decorators()