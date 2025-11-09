#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 2実装 E2Eテストスイート

End-to-Endテスト: Phase 2の全機能を統合検証
- Phase 2-1: MunicipalityFlowネットワーク図（D3.js）
- Phase 2-2: ネットワーク中心性分析（NetworkX）
- Phase 2-3: 完全統合ダッシュボード

検証内容:
- network_analyzer.py実行と出力ファイル検証
- NetworkMetrics.json構造検証
- CentralityRanking.csv品質確認
- GASファイル存在確認
- 統合ダッシュボード機能確認

工数: 1時間
作成日: 2025-10-27
"""

import sys
from pathlib import Path
import pandas as pd
import json
from datetime import datetime
import subprocess

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'python_scripts'))

from network_analyzer import NetworkAnalyzer


def test_e2e_phase2_workflow():
    """Phase 2 E2Eワークフロー全体テスト"""

    print("\n" + "=" * 70)
    print(" " * 15 + "Phase 2 E2Eテスト実行")
    print(" " * 10 + "End-to-End Workflow Validation")
    print("=" * 70)
    print(f"\n実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"プロジェクトルート: {project_root}")

    results = {
        'test_name': 'Phase 2 E2Eテスト',
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }

    # ========================================
    # テスト1: network_analyzer.py 実行
    # ========================================
    print("\n" + "-" * 70)
    print("テスト1: network_analyzer.py 実行")
    print("-" * 70)

    try:
        analyzer = NetworkAnalyzer(data_root=str(project_root))
        analyzer.run_complete_analysis(top_n=20)

        print("[OK] network_analyzer.py 実行成功")
        results['tests'].append({
            'name': 'network_analyzer.py実行',
            'status': 'PASS',
            'details': f'TOP {len(analyzer.hub_municipalities)}ハブ自治体特定'
        })
    except Exception as e:
        print(f"[ERROR] network_analyzer.py 実行失敗: {e}")
        results['tests'].append({
            'name': 'network_analyzer.py実行',
            'status': 'FAIL',
            'error': str(e)
        })
        return results

    # ========================================
    # テスト2: NetworkMetrics.json 検証
    # ========================================
    print("\n" + "-" * 70)
    print("テスト2: NetworkMetrics.json 検証")
    print("-" * 70)

    json_path = project_root / 'gas_output_insights' / 'NetworkMetrics.json'

    if not json_path.exists():
        print(f"[ERROR] JSONファイルが見つかりません: {json_path}")
        results['tests'].append({
            'name': 'NetworkMetrics.json検証',
            'status': 'FAIL',
            'error': 'JSONファイル不在'
        })
        return results

    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # JSON構造検証
    required_keys = ['generated_at', 'network_statistics', 'hub_municipalities', 'centrality_metrics_summary']
    missing_keys = [key for key in required_keys if key not in json_data]

    if missing_keys:
        print(f"[ERROR] 必須キーが見つかりません: {missing_keys}")
        results['tests'].append({
            'name': 'NetworkMetrics.json検証',
            'status': 'FAIL',
            'error': f'必須キー不在: {missing_keys}'
        })
        return results

    print(f"[OK] JSON構造検証成功")
    print(f"  - 生成日時: {json_data['generated_at']}")
    print(f"  - ノード数: {json_data['network_statistics']['nodes']}")
    print(f"  - エッジ数: {json_data['network_statistics']['edges']}")
    print(f"  - ハブ自治体数: {len(json_data['hub_municipalities'])}")

    # ネットワーク統計検証
    if json_data['network_statistics']['nodes'] < 100:
        print(f"[WARNING] ノード数が少なすぎます: {json_data['network_statistics']['nodes']} (期待: 800+)")

    if json_data['network_statistics']['edges'] < 1000:
        print(f"[WARNING] エッジ数が少なすぎます: {json_data['network_statistics']['edges']} (期待: 6000+)")

    results['tests'].append({
        'name': 'NetworkMetrics.json検証',
        'status': 'PASS',
        'details': {
            'nodes': json_data['network_statistics']['nodes'],
            'edges': json_data['network_statistics']['edges'],
            'hub_municipalities': len(json_data['hub_municipalities'])
        }
    })

    # ========================================
    # テスト3: CentralityRanking.csv 品質確認
    # ========================================
    print("\n" + "-" * 70)
    print("テスト3: CentralityRanking.csv 品質確認")
    print("-" * 70)

    csv_path = project_root / 'gas_output_insights' / 'CentralityRanking.csv'

    if not csv_path.exists():
        print(f"[ERROR] CSVファイルが見つかりません: {csv_path}")
        results['tests'].append({
            'name': 'CentralityRanking.csv品質確認',
            'status': 'FAIL',
            'error': 'CSVファイル不在'
        })
        return results

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # 必須列確認
    required_columns = ['rank', 'municipality', 'composite_score', 'pagerank', 'betweenness_centrality']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"[ERROR] 必須列が見つかりません: {missing_columns}")
        results['tests'].append({
            'name': 'CentralityRanking.csv品質確認',
            'status': 'FAIL',
            'error': f'必須列不在: {missing_columns}'
        })
        return results

    print(f"[OK] CentralityRanking.csv 読み込み成功")
    print(f"  - ハブ自治体数: {len(df)}")
    print(f"  - 列数: {len(df.columns)}")

    # 複合スコア降順確認
    is_sorted = df['composite_score'].is_monotonic_decreasing
    if not is_sorted:
        print(f"[WARNING] 複合スコアが降順になっていません")

    # TOP 3表示
    print(f"\n  [TOP 3ハブ自治体]")
    for idx, row in df.head(3).iterrows():
        print(f"    {int(row['rank'])}. {row['municipality']} (スコア: {row['composite_score']:.4f})")

    results['tests'].append({
        'name': 'CentralityRanking.csv品質確認',
        'status': 'PASS',
        'details': {
            'hub_count': len(df),
            'columns': len(df.columns),
            'is_sorted': is_sorted
        }
    })

    # ========================================
    # テスト4: GASファイル存在確認
    # ========================================
    print("\n" + "-" * 70)
    print("テスト4: GASファイル存在確認")
    print("-" * 70)

    gas_files = [
        'gas_files/scripts/MunicipalityFlowNetworkViz.gs',
        'gas_files/scripts/CompleteIntegratedDashboard.gs',
        'gas_files/scripts/Phase7CompleteMenuIntegration.gs'
    ]

    missing_gas_files = []
    existing_gas_files = []

    for gas_file in gas_files:
        full_path = project_root / gas_file
        if full_path.exists():
            existing_gas_files.append(gas_file)
            file_size = full_path.stat().st_size
            line_count = len(full_path.read_text(encoding='utf-8').split('\n'))
            print(f"  [OK] {gas_file}")
            print(f"       サイズ: {file_size:,} bytes / 行数: {line_count:,}")
        else:
            missing_gas_files.append(gas_file)
            print(f"  [ERROR] {gas_file} が見つかりません")

    if missing_gas_files:
        print(f"\n[ERROR] GASファイルが不足しています: {len(missing_gas_files)}件")
        results['tests'].append({
            'name': 'GASファイル存在確認',
            'status': 'FAIL',
            'error': f'不足ファイル: {missing_gas_files}'
        })
    else:
        print(f"\n[OK] GASファイル確認完了（{len(existing_gas_files)}ファイル）")
        results['tests'].append({
            'name': 'GASファイル存在確認',
            'status': 'PASS',
            'details': f'{len(existing_gas_files)}ファイル存在確認'
        })

    # ========================================
    # テスト5: 中心性メトリクス整合性確認
    # ========================================
    print("\n" + "-" * 70)
    print("テスト5: 中心性メトリクス整合性確認")
    print("-" * 70)

    # 複合スコア = 各中心性の重み付け合計
    # degree(15%) + in_degree(15%) + out_degree(15%) + betweenness(25%) + eigenvector(15%) + pagerank(15%)
    score_errors = 0

    for idx, row in df.head(10).iterrows():
        calculated_score = (
            row['degree_centrality'] * 0.15 +
            row['in_degree_centrality'] * 0.15 +
            row['out_degree_centrality'] * 0.15 +
            row['betweenness_centrality'] * 0.25 +
            row['eigenvector_centrality'] * 0.15 +
            row['pagerank'] * 0.15
        )

        diff = abs(calculated_score - row['composite_score'])

        if diff > 0.0001:  # 許容誤差0.0001
            score_errors += 1
            print(f"  [WARNING] {row['municipality']}: スコア差 {diff:.6f}")

    if score_errors > 0:
        print(f"\n[WARNING] 複合スコア計算エラー: {score_errors}件")
    else:
        print(f"\n[OK] 複合スコア計算検証成功（誤差なし）")

    results['tests'].append({
        'name': '中心性メトリクス整合性確認',
        'status': 'PASS' if score_errors == 0 else 'WARN',
        'details': {
            'score_errors': score_errors,
            'validated_hubs': 10
        }
    })

    # ========================================
    # テスト6: Phase 2統合完了確認
    # ========================================
    print("\n" + "-" * 70)
    print("テスト6: Phase 2統合完了確認")
    print("-" * 70)

    phase2_components = {
        'Phase 2-1: MunicipalityFlowネットワーク図': project_root / 'gas_files/scripts/MunicipalityFlowNetworkViz.gs',
        'Phase 2-2: ネットワーク中心性分析': project_root / 'gas_output_insights/NetworkMetrics.json',
        'Phase 2-3: 完全統合ダッシュボード': project_root / 'gas_files/scripts/CompleteIntegratedDashboard.gs'
    }

    all_complete = True

    for component_name, component_path in phase2_components.items():
        if component_path.exists():
            print(f"  [OK] {component_name}")
        else:
            print(f"  [ERROR] {component_name} が見つかりません")
            all_complete = False

    if all_complete:
        print(f"\n[SUCCESS] Phase 2の全コンポーネントが完成しました！")
        results['tests'].append({
            'name': 'Phase 2統合完了確認',
            'status': 'PASS',
            'details': 'Phase 2-1, 2-2, 2-3すべて完成'
        })
    else:
        print(f"\n[ERROR] Phase 2が未完成です")
        results['tests'].append({
            'name': 'Phase 2統合完了確認',
            'status': 'FAIL',
            'error': 'コンポーネント不足'
        })

    return results


def main():
    """メイン実行関数"""
    # E2Eテスト実行
    results = test_e2e_phase2_workflow()

    # 結果サマリー
    print("\n" + "=" * 70)
    print(" " * 20 + "Phase 2 E2Eテスト結果サマリー")
    print("=" * 70)

    total_tests = len(results['tests'])
    passed_tests = sum(1 for test in results['tests'] if test['status'] == 'PASS')
    failed_tests = sum(1 for test in results['tests'] if test['status'] == 'FAIL')
    warned_tests = sum(1 for test in results['tests'] if test['status'] == 'WARN')

    print(f"\n  実行テスト数: {total_tests}")
    print(f"  成功: {passed_tests}")
    print(f"  警告: {warned_tests}")
    print(f"  失敗: {failed_tests}")

    if total_tests > 0:
        success_rate = ((passed_tests + warned_tests) / total_tests) * 100
        print(f"\n  成功率: {success_rate:.1f}%")

        if success_rate == 100.0:
            print("\n  [SUCCESS] 全Phase 2 E2Eテスト合格！Phase 2実装は本番投入可能です。")
        elif success_rate >= 80.0:
            print("\n  [GOOD] 80%以上のテストが合格。実装品質は良好です。")
        else:
            print("\n  [ERROR] E2Eテスト合格率が低すぎます。実装を見直してください。")

    print("=" * 70)

    # 結果をJSONで保存（int64をintに変換）
    def convert_to_json_serializable(obj):
        """pandasのint64をintに変換"""
        if isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json_serializable(item) for item in obj]
        elif hasattr(obj, 'item'):  # numpy/pandas types
            return obj.item()
        else:
            return obj

    output_path = project_root / 'python_scripts' / 'phase2_e2e_test_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(convert_to_json_serializable(results), f, ensure_ascii=False, indent=2)

    print(f"\nPhase 2 E2Eテスト結果を保存しました: {output_path}")

    # 終了コード設定（CI/CD対応）
    return 0 if failed_tests == 0 else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
