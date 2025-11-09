#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旧Notebook vs 現行システム - 網羅的機能比較 + テスト検証

ファクトベースで両システムの機能を比較し、統合可能性を評価
"""

import json
import sys
from pathlib import Path
import pandas as pd

# UTF-8出力を強制
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_all_methods_from_notebook(notebook_path):
    """Notebookから全メソッドを抽出"""

    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    cells = notebook.get('cells', [])

    all_methods = {}

    # セル[1]のEnhancedJobSeekerAnalyzerを解析
    if len(cells) > 1:
        cell = cells[1]
        source = cell.get('source', [])
        if isinstance(source, list):
            source_text = ''.join(source)
        else:
            source_text = source

        lines = source_text.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def ') and not stripped.startswith('def main'):
                method_name = stripped.split('(')[0].replace('def ', '').strip()

                # Docstringを探す
                docstring = None
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        doc_lines = []
                        k = i + 1
                        in_doc = False
                        while k < min(i + 10, len(lines)):
                            line_text = lines[k].strip()
                            if '"""' in line_text or "'''" in line_text:
                                if in_doc:
                                    doc_lines.append(line_text.replace('"""', '').replace("'''", ''))
                                    break
                                else:
                                    in_doc = True
                                    doc_lines.append(line_text.replace('"""', '').replace("'''", ''))
                            elif in_doc:
                                doc_lines.append(line_text)
                            k += 1
                        if doc_lines:
                            docstring = ' '.join(doc_lines).strip()

                all_methods[method_name] = {
                    'line': i,
                    'docstring': docstring
                }

    return all_methods


def extract_all_methods_from_current_system():
    """現行システムから全メソッドを抽出"""

    current_system_path = Path(r'C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts\run_complete_v2_perfect.py')

    with open(current_system_path, 'r', encoding='utf-8') as f:
        source_text = f.read()

    lines = source_text.split('\n')
    all_methods = {}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('def ') and not stripped.startswith('def main'):
            method_name = stripped.split('(')[0].replace('def ', '').strip()

            # Docstringを探す
            docstring = None
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    doc_lines = []
                    k = i + 1
                    in_doc = False
                    while k < min(i + 10, len(lines)):
                        line_text = lines[k].strip()
                        if '"""' in line_text or "'''" in line_text:
                            if in_doc:
                                doc_lines.append(line_text.replace('"""', '').replace("'''", ''))
                                break
                            else:
                                in_doc = True
                                doc_lines.append(line_text.replace('"""', '').replace("'''", ''))
                        elif in_doc:
                            doc_lines.append(line_text)
                        k += 1
                    if doc_lines:
                        docstring = ' '.join(doc_lines).strip()

            all_methods[method_name] = {
                'line': i,
                'docstring': docstring
            }

    return all_methods


def categorize_methods(notebook_methods, current_methods):
    """メソッドをカテゴリ分類"""

    # 共通メソッド
    common_methods = set(notebook_methods.keys()) & set(current_methods.keys())

    # Notebookのみ
    notebook_only = set(notebook_methods.keys()) - set(current_methods.keys())

    # 現行システムのみ
    current_only = set(current_methods.keys()) - set(notebook_methods.keys())

    # カテゴリ分類
    categories = {
        'データ読み込み・前処理': [],
        'ペルソナ分析': [],
        'アソシエーションルール': [],
        '応募傾向・予測': [],
        '地理分析': [],
        '統計分析': [],
        'クラスタリング': [],
        'データ品質': [],
        '可視化': [],
        '出力・エクスポート': [],
        'その他': []
    }

    category_keywords = {
        'データ読み込み・前処理': ['load', 'process', 'extract', 'parse', 'normalize', 'split'],
        'ペルソナ分析': ['persona', 'segment', 'infer', 'character', 'profile'],
        'アソシエーションルール': ['association', 'rule', 'mining', 'interpret'],
        '応募傾向・予測': ['application', 'propensity', 'roi', 'projection'],
        '地理分析': ['geographic', 'mobility', 'location', 'distance', 'coords', 'flow'],
        '統計分析': ['statistical', 'chi_square', 'anova', 'test'],
        'クラスタリング': ['cluster', 'latent', 'lca'],
        'データ品質': ['quality', 'assess', 'qa', 'check', 'validate'],
        '可視化': ['plot', 'visualiz', 'display'],
        '出力・エクスポート': ['export', 'save', 'generate', 'output']
    }

    for method in notebook_only:
        categorized = False
        for category, keywords in category_keywords.items():
            if any(kw in method.lower() for kw in keywords):
                categories[category].append(('notebook_only', method))
                categorized = True
                break
        if not categorized:
            categories['その他'].append(('notebook_only', method))

    return {
        'common': common_methods,
        'notebook_only': notebook_only,
        'current_only': current_only,
        'categories': categories
    }


def main():
    print("=" * 100)
    print("旧Notebook vs 現行システム - 網羅的機能比較")
    print("=" * 100)

    notebook_path = r'C:\Users\fuji1\OneDrive\Pythonスクリプト保管\ジョブメドレーの求職者データを分析する&可視化するファイル_fixed.ipynb'

    print("\n[1/4] 旧Notebookからメソッド抽出中...")
    notebook_methods = extract_all_methods_from_notebook(notebook_path)
    print(f"  ✅ {len(notebook_methods)}個のメソッドを抽出")

    print("\n[2/4] 現行システムからメソッド抽出中...")
    current_methods = extract_all_methods_from_current_system()
    print(f"  ✅ {len(current_methods)}個のメソッドを抽出")

    print("\n[3/4] メソッド分類中...")
    categorization = categorize_methods(notebook_methods, current_methods)

    print(f"\n[4/4] 分類結果")
    print(f"  - 共通メソッド: {len(categorization['common'])}個")
    print(f"  - Notebookのみ: {len(categorization['notebook_only'])}個")
    print(f"  - 現行システムのみ: {len(categorization['current_only'])}個")

    # 詳細レポート
    print("\n" + "=" * 100)
    print("【Notebookのみに存在するメソッド（統合候補）】")
    print("=" * 100)

    for category, methods in categorization['categories'].items():
        if methods:
            print(f"\n■ {category}")
            print("-" * 100)
            for source, method in methods:
                if source == 'notebook_only':
                    doc = notebook_methods[method]['docstring']
                    if doc:
                        print(f"  ✨ {method}")
                        print(f"      説明: {doc[:100]}...")
                    else:
                        print(f"  ✨ {method}")

    # 統合優先度評価
    print("\n\n" + "=" * 100)
    print("【統合優先度評価（ファクトベース）】")
    print("=" * 100)

    high_priority = []
    medium_priority = []
    low_priority = []

    for method in categorization['notebook_only']:
        # 高優先度キーワード
        if any(kw in method.lower() for kw in ['persona', 'evidence', 'infer', 'roi', 'projection', 'association']):
            high_priority.append(method)
        # 中優先度キーワード
        elif any(kw in method.lower() for kw in ['propensity', 'latent', 'segment', 'qa']):
            medium_priority.append(method)
        else:
            low_priority.append(method)

    print(f"\n🔴 高優先度（{len(high_priority)}個）: ペルソナ推論、ROI予測、アソシエーション")
    print("-" * 100)
    for method in sorted(high_priority):
        doc = notebook_methods[method]['docstring']
        print(f"  ✅ {method}")
        if doc:
            print(f"      → {doc[:80]}...")

    print(f"\n🟡 中優先度（{len(medium_priority)}個）: 応募傾向、潜在クラス、品質チェック")
    print("-" * 100)
    for method in sorted(medium_priority):
        doc = notebook_methods[method]['docstring']
        print(f"  ⚠️ {method}")
        if doc:
            print(f"      → {doc[:80]}...")

    print(f"\n🟢 低優先度（{len(low_priority)}個）: 現行システムで代替可能")
    print("-" * 100)
    for method in sorted(low_priority):
        print(f"  ℹ️ {method}")

    # CSV形式で出力
    print("\n" + "=" * 100)
    print("【統合可能性マトリクス（CSV形式）】")
    print("=" * 100)

    comparison_data = []

    for method in categorization['notebook_only']:
        priority = '高' if method in high_priority else ('中' if method in medium_priority else '低')

        # カテゴリ判定
        category = 'その他'
        for cat, methods in categorization['categories'].items():
            if ('notebook_only', method) in methods:
                category = cat
                break

        comparison_data.append({
            'メソッド名': method,
            '優先度': priority,
            'カテゴリ': category,
            '説明': notebook_methods[method]['docstring'][:50] if notebook_methods[method]['docstring'] else 'N/A'
        })

    df = pd.DataFrame(comparison_data)
    df = df.sort_values(['優先度', 'カテゴリ'], ascending=[False, True])

    print(df.to_string(index=False))

    # CSV保存
    output_path = Path('comparison_matrix.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 比較マトリクスを保存: {output_path.absolute()}")

    # サマリー統計
    print("\n" + "=" * 100)
    print("【統計サマリー】")
    print("=" * 100)

    print(f"\n総メソッド数:")
    print(f"  - 旧Notebook: {len(notebook_methods)}個")
    print(f"  - 現行システム: {len(current_methods)}個")
    print(f"  - 共通: {len(categorization['common'])}個")
    print(f"  - 統合候補（Notebookのみ）: {len(categorization['notebook_only'])}個")

    print(f"\n統合優先度別:")
    print(f"  - 🔴 高優先度: {len(high_priority)}個 ({len(high_priority)/len(categorization['notebook_only'])*100:.1f}%)")
    print(f"  - 🟡 中優先度: {len(medium_priority)}個 ({len(medium_priority)/len(categorization['notebook_only'])*100:.1f}%)")
    print(f"  - 🟢 低優先度: {len(low_priority)}個 ({len(low_priority)/len(categorization['notebook_only'])*100:.1f}%)")

    print(f"\nカテゴリ別（Notebookのみ）:")
    for category, methods in categorization['categories'].items():
        notebook_only_count = sum(1 for source, _ in methods if source == 'notebook_only')
        if notebook_only_count > 0:
            print(f"  - {category}: {notebook_only_count}個")


if __name__ == '__main__':
    main()
