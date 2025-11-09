# -*- coding: utf-8 -*-
"""
Phase 7可視化ファイル統合スクリプト
"""
import os
import re

# 統合対象ファイル
FILES = [
    ('Phase7SupplyDensityViz.gs', '人材供給密度マップ'),
    ('Phase7QualificationDistViz.gs', '資格別人材分布'),
    ('Phase7AgeGenderCrossViz.gs', '年齢層×性別クロス分析'),
    ('Phase7MobilityScoreViz.gs', '移動許容度スコアリング'),
    ('Phase7PersonaProfileViz.gs', 'ペルソナ詳細プロファイル'),
    ('Phase7PersonaMobilityCrossViz.gs', 'ペルソナ×移動許容度クロス分析'),
    ('Phase7CompleteDashboard.gs', 'Phase 7統合ダッシュボード'),
]

# 統合ファイルヘッダー
HEADER = """/**
 * Phase 7 統合可視化ファイル
 *
 * このファイルには以下の可視化機能がすべて含まれています:
 * 1. 人材供給密度マップ
 * 2. 資格別人材分布
 * 3. 年齢層×性別クロス分析
 * 4. 移動許容度スコアリング
 * 5. ペルソナ詳細プロファイル
 * 6. ペルソナ×移動許容度クロス分析
 * 7. Phase 7統合ダッシュボード
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
    output_path = os.path.join(script_dir, 'Phase7UnifiedVisualizations.gs')

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
