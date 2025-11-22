# -*- coding: utf-8 -*-
"""
依存関係トラッキング修正スクリプト

@rx.var関数内で prefecture = self.selected_prefecture パターンを使用している箇所に
明示的な依存関係宣言を追加します。
"""

import re

def fix_dependency_tracking():
    file_path = "mapcomplete_dashboard/mapcomplete_dashboard.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # パターン: df = self.df の後に prefecture = self.selected_prefecture がある場合
    # 依存関係宣言を追加

    # 修正パターン1: df = self.df\n        prefecture = self.selected_prefecture\n        municipality = self.selected_municipality
    old_pattern1 = r'(        df = self\.df\n)(        prefecture = self\.selected_prefecture\n        municipality = self\.selected_municipality)'
    new_pattern1 = r'\1        # 依存関係トラッキング用\n        _ = self.selected_prefecture\n        _ = self.selected_municipality\n        \n\2'

    content = re.sub(old_pattern1, new_pattern1, content)

    # カウント
    count = len(re.findall(r'_ = self\.selected_prefecture', content))

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"修正完了: {count}箇所の依存関係宣言")

if __name__ == "__main__":
    fix_dependency_tracking()
