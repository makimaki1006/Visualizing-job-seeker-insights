# -*- coding: utf-8 -*-
"""
Phase 1-6可視化ファイル統合スクリプト
"""
import os
import re

# 統合対象ファイル
FILES = [
    ('MapVisualization.gs', '地図可視化（バブル・ヒートマップ）'),
    ('Phase2Phase3Visualizations.gs', '統計分析・ペルソナ可視化'),
    ('MunicipalityFlowNetworkViz.gs', '自治体間フロー分析'),
    ('PersonaMapDataVisualization.gs', 'ペルソナマップデータ可視化'),
    ('MatrixHeatmapViewer.gs', 'マトリックスヒートマップ'),
    ('CompleteIntegratedDashboard.gs', '統合ダッシュボード（Phase 1-6）'),
]

# 統合ファイルヘッダー
HEADER = """/**
 * Phase 1-6 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. 地図可視化（バブル・ヒートマップ）
 * 2. 統計分析・ペルソナ可視化
 * 3. 自治体間フロー分析
 * 4. ペルソナマップデータ可視化
 * 5. マトリックスヒートマップ
 * 6. 統合ダッシュボード（Phase 1-6）
 */

"""

def remove_header_comment(content):
    """先頭のコメントブロック（/**...*/）を削除"""
    # マルチラインコメントを削除
    pattern = r'^/\*\*.*?\*/\s*'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    return content.lstrip()

def create_unified_file():
    """統合ファイルを作成"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'Phase1-6UnifiedVisualizations.gs')

    with open(output_path, 'w', encoding='utf-8') as outfile:
        # ヘッダー書き込み
        outfile.write(HEADER)

        # 各ファイルの内容を追加
        for i, (filename, title) in enumerate(FILES, 1):
            filepath = os.path.join(script_dir, filename)

            if not os.path.exists(filepath):
                print(f'警告: {filename} が見つかりません')
                continue

            # セクション見出し
            separator = f'// {"━" * 40}\n// {i}. {title}\n// {"━" * 40}\n\n'
            outfile.write(separator)

            # ファイル内容読み込み
            with open(filepath, 'r', encoding='utf-8') as infile:
                content = infile.read()

            # 先頭コメント削除
            content = remove_header_comment(content)

            # 書き込み
            outfile.write(content)
            outfile.write('\n\n')

            print(f'追加: {filename}')

    print(f'\n統合完了: {output_path}')

    # ファイルサイズ確認
    size_kb = os.path.getsize(output_path) / 1024
    print(f'ファイルサイズ: {size_kb:.2f} KB')

if __name__ == '__main__':
    create_unified_file()
