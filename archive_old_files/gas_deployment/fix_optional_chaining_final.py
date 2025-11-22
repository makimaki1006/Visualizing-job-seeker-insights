#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optional Chaining (?.) を完全にGAS互換の構文に変換するスクリプト
"""
import re

def fix_optional_chaining_complete(content):
    """すべてのOptional Chainingを修正（入れ子対応）"""

    # 最大10回繰り返して入れ子を完全に処理
    for iteration in range(10):
        original = content

        # パターン1: (expr)?.prop → (expr && expr.prop)
        content = re.sub(r'\(([^)]+)\)\?\.(\w+)', r'(\1 && (\1).\2)', content)

        # パターン2: obj?.prop → (obj && obj.prop)
        content = re.sub(r'(\w+)\?\.(\w+)', r'(\1 && \1.\2)', content)

        # パターン3: obj?.[key] → (obj && obj[key])
        content = re.sub(r'(\w+)\?\.\[([^\]]+)\]', r'(\1 && \1[\2])', content)

        # パターン4: (expr)?.[key] → (expr && (expr)[key])
        content = re.sub(r'\(([^)]+)\)\?\.\[([^\]]+)\]', r'(\1 && (\1)[\2])', content)

        # 変化がなければ終了
        if content == original:
            break

    return content

# ファイル読み込み
with open('map_complete_integrated.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 修正前のOptional Chaining数をカウント
original_count = len(re.findall(r'\?\.', content))
print(f'Before: {original_count} optional chaining')

# Optional Chaining修正
content = fix_optional_chaining_complete(content)

# 修正後のOptional Chaining数をカウント
remaining_count = len(re.findall(r'\?\.', content))
print(f'After: {remaining_count} optional chaining')

# ファイル書き込み
with open('map_complete_integrated.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: Optional Chaining fixed')
