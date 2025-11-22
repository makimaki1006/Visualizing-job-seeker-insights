#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optional Chaining (?.) を GAS互換の構文に変換するスクリプト
"""
import re

def fix_optional_chaining(content):
    """Optional Chainingをすべて修正"""

    # パターン1: obj?.prop
    content = re.sub(r'(\w+)\?\.(\w+)', r'(\1 && \1.\2)', content)

    # パターン2: obj?.[key]
    content = re.sub(r'(\w+)\?\.\[([^\]]+)\]', r'(\1 && \1[\2])', content)

    # パターン3: obj?.prop?.nested
    # 複数回実行して入れ子のOptional Chainingを処理
    for _ in range(5):
        # obj && obj.prop?.nested → obj && obj.prop && obj.prop.nested
        content = re.sub(
            r'\((\w+) && \1\.(\w+)\)\?\.(\w+)',
            r'(\1 && \1.\2 && \1.\2.\3)',
            content
        )

    return content

# ファイル読み込み
with open('map_complete_integrated.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 修正前のOptional Chaining数をカウント
original_count = len(re.findall(r'\?\.', content))
print(f'修正前: {original_count}箇所のOptional Chaining検出')

# Optional Chaining修正
content = fix_optional_chaining(content)

# 修正後のOptional Chaining数をカウント
remaining_count = len(re.findall(r'\?\.', content))
print(f'修正後: {remaining_count}箇所のOptional Chaining残存')

# ファイル書き込み
with open('map_complete_integrated.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Optional Chaining修正完了')
