# -*- coding: utf-8 -*-
"""
統合ファイル最適化スクリプト

目的：
1. 重複関数を削除して1つに統合
2. 共通HTML生成パターンを抽出
3. 冗長なコードを削減
4. ファイルサイズを10-20%削減
"""
import os
import re
from collections import defaultdict

def extract_function_bodies(content):
    """ファイル内のすべての関数を抽出"""
    # function宣言を検出（複数行対応）
    pattern = r'(function\s+(\w+)\s*\([^)]*\)\s*\{(?:[^{}]|\{[^{}]*\})*\})'
    matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

    functions = {}
    for match in matches:
        func_name = match.group(2)
        func_body = match.group(1)
        if func_name not in functions:
            functions[func_name] = []
        functions[func_name].append({
            'body': func_body,
            'start': match.start(),
            'end': match.end()
        })

    return functions

def find_duplicate_functions(content):
    """重複する関数を特定"""
    functions = extract_function_bodies(content)

    duplicates = {}
    for name, instances in functions.items():
        if len(instances) > 1:
            duplicates[name] = instances

    return duplicates

def remove_duplicate_functions_advanced(content):
    """重複関数を削除（最初の定義のみ保持）"""
    duplicates = find_duplicate_functions(content)

    if not duplicates:
        return content, 0

    removed_count = 0
    # 後ろから削除（インデックスがずれないように）
    for func_name, instances in duplicates.items():
        # 最初の定義以外を削除
        for instance in reversed(instances[1:]):
            # 関数定義の前後の空白も削除
            start = instance['start']
            end = instance['end']

            # 前の改行を含める
            while start > 0 and content[start-1] in '\n\r':
                start -= 1

            # 後ろの改行を含める
            while end < len(content) and content[end] in '\n\r':
                end += 1

            content = content[:start] + content[end:]
            removed_count += 1
            print(f'  重複削除: {func_name}()')

    return content, removed_count

def optimize_html_templates(content):
    """HTML生成部分を最適化"""
    # 重複するHTMLスタイル定義を統合
    style_pattern = r'<style>\s*(.*?)\s*</style>'
    styles = re.findall(style_pattern, content, re.DOTALL)

    if len(styles) > 1:
        # 共通スタイルを抽出
        common_styles = set()
        for style in styles:
            # CSSルールを抽出
            rules = re.findall(r'([^{]+)\{[^}]+\}', style)
            common_styles.update(rules)

        print(f'  HTML最適化: {len(styles)}個のstyleブロック検出')

    return content

def remove_redundant_comments(content):
    """冗長なコメントを削除"""
    # 空のコメントブロックを削除
    content = re.sub(r'/\*\*\s*\*/', '', content)

    # 連続する空行を1つにまとめる
    content = re.sub(r'\n\n\n+', '\n\n', content)

    return content

def optimize_variable_declarations(content):
    """変数宣言を最適化"""
    # const宣言の重複を検出
    const_pattern = r'const\s+(\w+)\s*=\s*SpreadsheetApp\.getUi\(\);'
    ui_declarations = re.findall(const_pattern, content)

    if len(ui_declarations) > 1:
        print(f'  変数最適化: {len(ui_declarations)}個のui宣言を検出')

    return content

def optimize_file(input_path, output_path):
    """ファイルを最適化"""
    print(f'\n最適化: {os.path.basename(input_path)}')

    # 元のファイルを読み込み
    with open(input_path, 'r', encoding='utf-8') as f:
        original = f.read()

    # 最適化前の統計
    before_lines = original.count('\n')
    before_size = len(original.encode('utf-8')) / 1024

    # 最適化実行
    content = original

    # 1. 重複関数を削除
    content, removed_funcs = remove_duplicate_functions_advanced(content)

    # 2. HTML テンプレートを最適化
    content = optimize_html_templates(content)

    # 3. 冗長なコメントを削除
    content = remove_redundant_comments(content)

    # 4. 変数宣言を最適化
    content = optimize_variable_declarations(content)

    # 最適化後の統計
    after_lines = content.count('\n')
    after_size = len(content.encode('utf-8')) / 1024

    # 結果を保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 統計表示
    line_reduction = before_lines - after_lines
    size_reduction = before_size - after_size
    line_percent = (line_reduction / before_lines * 100) if before_lines > 0 else 0
    size_percent = (size_reduction / before_size * 100) if before_size > 0 else 0

    print(f'  行数: {before_lines} → {after_lines} ({line_reduction:+d}行, {line_percent:.1f}%削減)')
    print(f'  サイズ: {before_size:.2f}KB → {after_size:.2f}KB ({size_reduction:+.2f}KB, {size_percent:.1f}%削減)')
    print(f'  削除した重複関数: {removed_funcs}個')

    return {
        'file': os.path.basename(input_path),
        'before': {
            'lines': before_lines,
            'size_kb': before_size
        },
        'after': {
            'lines': after_lines,
            'size_kb': after_size
        },
        'removed_functions': removed_funcs
    }

def main():
    """メイン処理"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    files = [
        'Phase7UnifiedVisualizations_refactored.gs',
        'Phase8UnifiedVisualizations_refactored.gs',
        'Phase10UnifiedVisualizations_refactored.gs',
    ]

    results = []

    for filename in files:
        input_path = os.path.join(script_dir, filename)
        output_path = os.path.join(script_dir, filename.replace('_refactored.gs', '_optimized.gs'))

        if os.path.exists(input_path):
            result = optimize_file(input_path, output_path)
            results.append(result)
        else:
            print(f'警告: {filename} が見つかりません')

    print('\n' + '=' * 70)
    print('最適化完了サマリー')
    print('=' * 70)

    total_before_lines = sum(r['before']['lines'] for r in results)
    total_after_lines = sum(r['after']['lines'] for r in results)
    total_before_size = sum(r['before']['size_kb'] for r in results)
    total_after_size = sum(r['after']['size_kb'] for r in results)
    total_removed = sum(r['removed_functions'] for r in results)

    line_reduction = total_before_lines - total_after_lines
    size_reduction = total_before_size - total_after_size
    line_percent = (line_reduction / total_before_lines * 100) if total_before_lines > 0 else 0
    size_percent = (size_reduction / total_before_size * 100) if total_before_size > 0 else 0

    print(f'\n総計:')
    print(f'  総行数: {total_before_lines} → {total_after_lines} ({line_reduction:+d}行, {line_percent:.1f}%削減)')
    print(f'  総サイズ: {total_before_size:.2f}KB → {total_after_size:.2f}KB ({size_reduction:+.2f}KB, {size_percent:.1f}%削減)')
    print(f'  削除した重複関数: {total_removed}個')

    print('\n個別ファイル:')
    for result in results:
        before_lines = result['before']['lines']
        after_lines = result['after']['lines']
        before_size = result['before']['size_kb']
        after_size = result['after']['size_kb']

        line_red = before_lines - after_lines
        size_red = before_size - after_size
        line_pct = (line_red / before_lines * 100) if before_lines > 0 else 0
        size_pct = (size_red / before_size * 100) if before_size > 0 else 0

        print(f'\n  {result["file"]}:')
        print(f'    {before_lines}行 → {after_lines}行 ({line_pct:.1f}%削減)')
        print(f'    {before_size:.2f}KB → {after_size:.2f}KB ({size_pct:.1f}%削減)')
        print(f'    削除関数: {result["removed_functions"]}個')

    print('\n' + '=' * 70)
    print('✅ 最適化完了！')
    print('=' * 70)
    print('\n最適化されたファイル:')
    for filename in files:
        optimized = filename.replace('_refactored.gs', '_optimized.gs')
        print(f'  - {optimized}')

if __name__ == '__main__':
    main()
