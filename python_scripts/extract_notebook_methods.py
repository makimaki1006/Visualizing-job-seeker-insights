#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jupyter Notebookから主要メソッドを抽出して比較するスクリプト
"""

import json
import sys
from pathlib import Path

# UTF-8出力を強制
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_methods_from_notebook(notebook_path):
    """Notebookから主要メソッドを抽出"""

    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    cells = notebook.get('cells', [])

    print("=" * 100)
    print("旧Jupyter Notebook vs 現在のrun_complete_v2_perfect.py 機能比較")
    print("=" * 100)

    # セル[1]のEnhancedJobSeekerAnalyzerを解析
    if len(cells) > 1:
        cell = cells[1]
        source = cell.get('source', [])
        if isinstance(source, list):
            source_text = ''.join(source)
        else:
            source_text = source

        print("\n[旧Notebookの EnhancedJobSeekerAnalyzer クラスの主要メソッド]")
        print("=" * 100)

        # メソッド定義を抽出
        lines = source_text.split('\n')
        current_method = None
        method_info = {}

        for i, line in enumerate(lines):
            stripped = line.strip()

            # メソッド定義を検出
            if stripped.startswith('def '):
                # 前のメソッドの情報を保存
                if current_method:
                    method_info[current_method]['end_line'] = i - 1

                # 新しいメソッドを記録
                method_name = stripped.split('(')[0].replace('def ', '').strip()
                current_method = method_name

                # メソッドシグネチャ全体を取得（複数行にわたる可能性がある）
                method_sig = stripped
                j = i + 1
                while j < len(lines) and ':' not in lines[j - i + 1]:
                    method_sig += ' ' + lines[j].strip()
                    j += 1

                method_info[method_name] = {
                    'signature': method_sig,
                    'start_line': i,
                    'end_line': None,
                    'docstring': None
                }

                # Docstringを探す
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        # Docstringの終了を探す
                        doc_lines = []
                        k = i + 1
                        in_doc = False
                        while k < min(i + 20, len(lines)):  # 最大20行まで
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
                            method_info[method_name]['docstring'] = ' '.join(doc_lines).strip()

        # 現在のrun_complete_v2_perfect.pyにはない、旧Notebookのみの機能を抽出
        unique_methods = [
            '_create_application_propensity_model',
            '_latent_class_analysis',
            '_analyze_segment_evidence',
            '_association_rule_mining',
            '_association_rule_mining_advanced',
            '_association_rule_mining_simple',
            '_interpret_rules',
            '_generate_evidence_based_personas',
            '_infer_segment_characteristics',
            '_generate_evidence_based_name',
            '_generate_evidence_based_strategies',
            '_calculate_confidence_level',
            '_calculate_roi_projections',
            'generate_strategic_insights',
            '_gender_relative_location_intent',
            '_qa_checks',
            '_display_enhanced_summary'
        ]

        print("\n【旧Notebookにのみ存在する高度な分析機能】")
        print("-" * 100)

        for method_name in unique_methods:
            if method_name in method_info:
                info = method_info[method_name]
                print(f"\n✨ {method_name}")
                print(f"   シグネチャ: {info['signature'][:100]}...")
                if info['docstring']:
                    print(f"   説明: {info['docstring'][:150]}...")

        # 機能カテゴリ別にグループ化
        print("\n\n" + "=" * 100)
        print("機能カテゴリ別分類")
        print("=" * 100)

        categories = {
            'ペルソナ分析': [
                '_generate_evidence_based_personas',
                '_infer_segment_characteristics',
                '_generate_evidence_based_name',
                '_generate_evidence_based_strategies',
                '_calculate_confidence_level'
            ],
            'アソシエーションルールマイニング': [
                '_association_rule_mining',
                '_association_rule_mining_advanced',
                '_association_rule_mining_simple',
                '_interpret_rules'
            ],
            '応募傾向・予測モデル': [
                '_create_application_propensity_model',
                '_calculate_roi_projections',
                '_latent_class_analysis',
                '_analyze_segment_evidence'
            ],
            '地理分析': [
                '_gender_relative_location_intent'
            ],
            '品質保証・レポート': [
                '_qa_checks',
                '_display_enhanced_summary'
            ],
            '戦略的インサイト': [
                'generate_strategic_insights'
            ]
        }

        for category, methods in categories.items():
            print(f"\n【{category}】")
            print("-" * 100)
            for method_name in methods:
                if method_name in method_info:
                    info = method_info[method_name]
                    status = "✅ 実装あり"
                    print(f"  {status} {method_name}")
                    if info['docstring']:
                        print(f"      → {info['docstring'][:100]}...")

        # run_complete_v2_perfect.pyとの統合可能性を評価
        print("\n\n" + "=" * 100)
        print("統合可能性評価")
        print("=" * 100)

        integration_assessment = {
            '高優先度（即座に統合すべき）': [
                ('_generate_evidence_based_personas', 'エビデンスベースのペルソナ生成は現在のPhase 3の強化に直結'),
                ('_association_rule_mining_advanced', '資格×職種×年齢層の関連性発見に有用'),
                ('_calculate_roi_projections', '採用ROI予測は実務的価値が高い')
            ],
            '中優先度（検討価値あり）': [
                ('_create_application_propensity_model', '応募傾向予測モデル、ただし統計的妥当性要確認'),
                ('_latent_class_analysis', '潜在クラス分析、サンプルサイズ依存'),
                ('_qa_checks', 'データ品質チェック強化、現行システムと重複可能性あり')
            ],
            '低優先度（現状で代替可能）': [
                ('_gender_relative_location_intent', '性別×地域分析、Phase 3/7で代替可能'),
                ('_display_enhanced_summary', '表示機能、GAS側で実装済み')
            ]
        }

        for priority, items in integration_assessment.items():
            print(f"\n【{priority}】")
            print("-" * 100)
            for method_name, reason in items:
                print(f"  🔹 {method_name}")
                print(f"      理由: {reason}")


if __name__ == '__main__':
    notebook_path = r'C:\Users\fuji1\OneDrive\Pythonスクリプト保管\ジョブメドレーの求職者データを分析する&可視化するファイル_fixed.ipynb'
    extract_methods_from_notebook(notebook_path)
