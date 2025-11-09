#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高優先度メソッドの実装コードを抽出
"""

import json
import sys
from pathlib import Path

# UTF-8出力を強制
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_method_code(source_text, method_name):
    """特定のメソッドのコードを抽出"""

    lines = source_text.split('\n')
    method_lines = []
    in_method = False
    indent_level = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # メソッド定義を検出
        if stripped.startswith(f'def {method_name}('):
            in_method = True
            indent_level = len(line) - len(line.lstrip())
            method_lines.append(line)
            continue

        # メソッド内の処理
        if in_method:
            # インデントが元のレベル以下になったら終了
            if line.strip() and not line.startswith(' ' * (indent_level + 1)):
                # ただし、空行やコメント行は除外
                if line.strip() and not line.strip().startswith('#'):
                    break

            method_lines.append(line)

    return '\n'.join(method_lines)


def main():
    notebook_path = r'C:\Users\fuji1\OneDrive\Pythonスクリプト保管\ジョブメドレーの求職者データを分析する&可視化するファイル_fixed.ipynb'

    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    cells = notebook.get('cells', [])

    if len(cells) > 1:
        cell = cells[1]
        source = cell.get('source', [])
        if isinstance(source, list):
            source_text = ''.join(source)
        else:
            source_text = source

        print("=" * 100)
        print("高優先度メソッドの実装コード抽出")
        print("=" * 100)

        high_priority_methods = [
            '_generate_evidence_based_personas',
            '_association_rule_mining_advanced',
            '_calculate_roi_projections',
            '_infer_segment_characteristics',
            '_generate_evidence_based_name',
            '_generate_evidence_based_strategies',
            '_calculate_confidence_level'
        ]

        for method_name in high_priority_methods:
            print(f"\n\n{'=' * 100}")
            print(f"【{method_name}】")
            print('=' * 100)

            code = extract_method_code(source_text, method_name)

            if code:
                # コード行数をカウント
                code_lines = [l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]
                print(f"\n実装行数: {len(code_lines)}行（コメント除く）")
                print(f"\n{code}")
            else:
                print(f"\n❌ メソッドが見つかりませんでした")

        # 依存関係のチェック
        print("\n\n" + "=" * 100)
        print("依存関係分析")
        print("=" * 100)

        # importステートメントを抽出
        import_lines = []
        for line in source_text.split('\n')[:200]:  # 最初の200行
            if 'import ' in line and not line.strip().startswith('#'):
                import_lines.append(line.strip())

        print("\n【必要なライブラリ】")
        print("-" * 100)
        for imp in import_lines[:30]:  # 最初の30個
            print(f"  {imp}")

        # mlxtendの使用状況
        if 'mlxtend' in source_text:
            print("\n\n【mlxtend使用状況】")
            print("-" * 100)
            mlxtend_lines = [line.strip() for line in source_text.split('\n') if 'mlxtend' in line.lower()]
            for line in mlxtend_lines[:10]:
                print(f"  {line}")


if __name__ == '__main__':
    main()
