# -*- coding: utf-8 -*-
"""
更新トリガー参照追加スクリプト

全ての@rx.var関数で update_counter を参照し、
都道府県/市区町村変更時に強制的に再計算されるようにします。
"""

import re

def fix_update_trigger():
    file_path = "mapcomplete_dashboard/mapcomplete_dashboard.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # パターン: 依存関係トラッキング用の後に update_counter参照を追加
    # _ = self.selected_prefecture
    # _ = self.selected_municipality
    # → _ = self.update_counter を追加

    old_pattern = r'(        # 依存関係トラッキング用\n        _ = self\.selected_prefecture\n        _ = self\.selected_municipality\n)'
    new_pattern = r'\1        _ = self.update_counter\n'

    content = re.sub(old_pattern, new_pattern, content)

    # パターン2: df = self.df の直後に update_counter参照を追加（既存の依存関係宣言がない場合）
    # if not self.is_loaded or self.df is None:
    #     return ...
    # df = self.df
    # → _ = self.update_counter を追加

    old_pattern2 = r'(        if not self\.is_loaded or self\.df is None:\n            return [^\n]+\n\n        df = self\.df\n)'
    new_pattern2 = r'\1        _ = self.update_counter  # 更新トリガー\n'

    # この置換は既に依存関係宣言があるものには適用しない
    # 既に _ = self.selected_prefecture がある行を除外

    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # パターン検出: df = self.df の行
        if '        df = self.df' in line and i > 0:
            # 次の行をチェック
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # 既に依存関係宣言がない場合のみ追加
                if '_ = self.' not in next_line and 'prefecture = self.selected_prefecture' in next_line:
                    new_lines.append('        _ = self.update_counter  # 更新トリガー')

        i += 1

    content = '\n'.join(new_lines)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 確認
    count = len(re.findall(r'_ = self\.update_counter', content))
    print(f"修正完了: {count}箇所のupdate_counter参照")

if __name__ == "__main__":
    fix_update_trigger()
