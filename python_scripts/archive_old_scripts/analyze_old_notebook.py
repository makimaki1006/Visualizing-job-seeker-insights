#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旧Jupyter Notebookの構造を解析するスクリプト
"""

import json
import sys
from pathlib import Path

# UTF-8出力を強制
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_notebook(notebook_path):
    """Jupyter Notebookの構造を解析"""

    print("=" * 80)
    print("Jupyter Notebook構造解析")
    print("=" * 80)

    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # 基本情報
    print(f"\nNotebookファイル: {Path(notebook_path).name}")
    print(f"セル数: {len(notebook.get('cells', []))}個")

    # メタデータ
    metadata = notebook.get('metadata', {})
    if 'kernelspec' in metadata:
        kernel = metadata['kernelspec']
        print(f"カーネル: {kernel.get('display_name', 'N/A')} ({kernel.get('language', 'N/A')})")

    # セル一覧
    print("\n" + "=" * 80)
    print("セル一覧（インデックス、タイプ、先頭行）")
    print("=" * 80)

    cells = notebook.get('cells', [])

    for idx, cell in enumerate(cells):
        cell_type = cell.get('cell_type', 'unknown')
        source = cell.get('source', [])

        # sourceがリストの場合は結合
        if isinstance(source, list):
            source_text = ''.join(source)
        else:
            source_text = source

        # 最初の100文字を取得
        preview = source_text[:100].replace('\n', ' ').strip()

        print(f"\n[{idx:3d}] {cell_type:10s} | {preview}...")

        # コードセルの場合、重要なキーワードをチェック
        if cell_type == 'code':
            keywords = ['import', 'def ', 'class ', 'pd.', 'plt.', 'sns.', '# Phase', '# Step']
            for keyword in keywords:
                if keyword in source_text:
                    # キーワードを含む行を抽出
                    lines = [line.strip() for line in source_text.split('\n') if keyword in line]
                    if lines:
                        print(f"      キーワード '{keyword}': {lines[0]}")

    # Markdownセルの見出しを抽出
    print("\n" + "=" * 80)
    print("Markdownセルの見出し（構造）")
    print("=" * 80)

    for idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'markdown':
            source = cell.get('source', [])
            if isinstance(source, list):
                source_text = ''.join(source)
            else:
                source_text = source

            # 見出しを抽出
            lines = source_text.split('\n')
            for line in lines:
                if line.startswith('#'):
                    print(f"[{idx:3d}] {line}")

    # コードセルの主要な関数/クラス定義を抽出
    print("\n" + "=" * 80)
    print("コードセルの主要な定義（関数/クラス）")
    print("=" * 80)

    for idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'code':
            source = cell.get('source', [])
            if isinstance(source, list):
                source_text = ''.join(source)
            else:
                source_text = source

            lines = source_text.split('\n')
            for line in lines:
                if line.strip().startswith('def ') or line.strip().startswith('class '):
                    print(f"[{idx:3d}] {line.strip()}")

    # 実行結果があるセルを確認
    print("\n" + "=" * 80)
    print("実行結果があるセル")
    print("=" * 80)

    output_count = 0
    for idx, cell in enumerate(cells):
        if cell.get('cell_type') == 'code':
            outputs = cell.get('outputs', [])
            if outputs:
                output_count += 1
                print(f"[{idx:3d}] 出力数: {len(outputs)}個")

                # 最初の出力の種類を確認
                if outputs:
                    first_output = outputs[0]
                    output_type = first_output.get('output_type', 'unknown')
                    print(f"      タイプ: {output_type}")

                    # データやテキストがあれば一部表示
                    if 'data' in first_output:
                        data_keys = list(first_output['data'].keys())
                        print(f"      データキー: {', '.join(data_keys)}")

                    if 'text' in first_output:
                        text = first_output['text']
                        if isinstance(text, list):
                            text = ''.join(text[:3])  # 最初の3行
                        else:
                            text = text[:200]
                        print(f"      テキスト: {text.strip()[:100]}...")

    print(f"\n実行結果があるセル: {output_count}/{len(cells)}個")


if __name__ == '__main__':
    notebook_path = r'C:\Users\fuji1\OneDrive\Pythonスクリプト保管\ジョブメドレーの求職者データを分析する&可視化するファイル_fixed.ipynb'
    analyze_notebook(notebook_path)
