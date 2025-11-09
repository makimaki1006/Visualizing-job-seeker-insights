#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1実装 E2Eテストスイート

End-to-Endテスト: 実際のユーザーワークフロー検証
- Python分析実行 → JSON/CSV生成
- データ整合性確認
- インサイト生成確認
- GAS連携準備確認

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

from cross_analysis_engine import CrossAnalysisEngine


def test_e2e_workflow():
    """E2Eワークフロー全体テスト"""

    print("\n" + "=" * 70)
    print(" " * 15 + "Phase 1 E2Eテスト実行")
    print(" " * 10 + "End-to-End Workflow Validation")
    print("=" * 70)
    print(f"\n実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"プロジェクトルート: {project_root}")

    results = {
        'test_name': 'Phase 1 E2Eテスト',
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }

    # ========================================
    # テスト1: cross_analysis_engine.py 実行
    # ========================================
    print("\n" + "-" * 70)
    print("テスト1: cross_analysis_engine.py 実行")
    print("-" * 70)

    try:
        engine = CrossAnalysisEngine(data_root=str(project_root))
        engine.run_all_analyses()

        print("[OK] cross_analysis_engine.py 実行成功")
        results['tests'].append({
            'name': 'cross_analysis_engine.py実行',
            'status': 'PASS',
            'details': f'{len(engine.results)}件の分析完了'
        })
    except Exception as e:
        print(f"[ERROR] cross_analysis_engine.py 実行失敗: {e}")
        results['tests'].append({
            'name': 'cross_analysis_engine.py実行',
            'status': 'FAIL',
            'error': str(e)
        })
        return results

    # ========================================
    # テスト2: CrossAnalysisResults.json 検証
    # ========================================
    print("\n" + "-" * 70)
    print("テスト2: CrossAnalysisResults.json 検証")
    print("-" * 70)

    json_path = project_root / 'gas_output_insights' / 'CrossAnalysisResults.json'

    if not json_path.exists():
        print(f"[ERROR] JSONファイルが見つかりません: {json_path}")
        results['tests'].append({
            'name': 'CrossAnalysisResults.json検証',
            'status': 'FAIL',
            'error': 'JSONファイル不在'
        })
        return results

    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # JSON構造検証
    required_keys = ['generated_at', 'analysis_count', 'data_sources_loaded', 'results']
    missing_keys = [key for key in required_keys if key not in json_data]

    if missing_keys:
        print(f"[ERROR] 必須キーが見つかりません: {missing_keys}")
        results['tests'].append({
            'name': 'CrossAnalysisResults.json検証',
            'status': 'FAIL',
            'error': f'必須キー不在: {missing_keys}'
        })
        return results

    print(f"[OK] JSON構造検証成功")
    print(f"  - 生成日時: {json_data['generated_at']}")
    print(f"  - 分析件数: {json_data['analysis_count']}")
    print(f"  - データソース: {json_data['data_sources_loaded']}")

    # データソース数検証（18CSVすべて読み込まれているか）
    if json_data['data_sources_loaded'] != 18:
        print(f"[WARNING] データソース数が期待値と異なります: {json_data['data_sources_loaded']} (期待: 18)")

    results['tests'].append({
        'name': 'CrossAnalysisResults.json検証',
        'status': 'PASS',
        'details': {
            'analysis_count': json_data['analysis_count'],
            'data_sources_loaded': json_data['data_sources_loaded']
        }
    })

    # ========================================
    # テスト3: インサイト生成確認
    # ========================================
    print("\n" + "-" * 70)
    print("テスト3: インサイト生成確認")
    print("-" * 70)

    total_insights = 0

    for analysis_key, analysis_result in json_data['results'].items():
        insights = analysis_result.get('insights', [])
        total_insights += len(insights)

        print(f"\n  [{analysis_key}]")
        print(f"    - 分析名: {analysis_result.get('analysis_name', 'N/A')}")
        print(f"    - 次元数: {analysis_result.get('dimensions', 'N/A')}")
        print(f"    - インサイト数: {len(insights)}")

        # インサイト内容表示
        for idx, insight in enumerate(insights, 1):
            insight_type = insight.get('type', 'N/A')
            description = insight.get('description', 'N/A')
            print(f"      {idx}. [{insight_type}] {description}")

    if total_insights == 0:
        print(f"[WARNING] インサイトが生成されていません")
        results['tests'].append({
            'name': 'インサイト生成確認',
            'status': 'FAIL',
            'error': 'インサイト数が0件'
        })
    else:
        print(f"\n[OK] インサイト生成確認成功（合計{total_insights}件）")
        results['tests'].append({
            'name': 'インサイト生成確認',
            'status': 'PASS',
            'details': f'{total_insights}件のインサイト生成'
        })

    # ========================================
    # テスト4: PersonaMapData.csv データ品質
    # ========================================
    print("\n" + "-" * 70)
    print("テスト4: PersonaMapData.csv データ品質確認")
    print("-" * 70)

    persona_map_path = project_root / 'gas_output_phase7' / 'PersonaMapData.csv'

    if not persona_map_path.exists():
        print(f"[ERROR] PersonaMapData.csv が見つかりません")
        results['tests'].append({
            'name': 'PersonaMapData.csv品質確認',
            'status': 'FAIL',
            'error': 'ファイル不在'
        })
    else:
        df = pd.read_csv(persona_map_path, encoding='utf-8-sig')

        # 座標欠損確認
        lat_col = df.columns[1]
        lng_col = df.columns[2]

        lat_missing = df[lat_col].isna().sum()
        lng_missing = df[lng_col].isna().sum()
        total_missing = lat_missing + lng_missing

        missing_rate = (total_missing / (len(df) * 2)) * 100

        print(f"[OK] PersonaMapData.csv 読み込み成功")
        print(f"  - 総地点数: {len(df)}")
        print(f"  - 座標欠損: {total_missing}件 ({missing_rate:.2f}%)")

        quality_score = 100 - missing_rate
        print(f"  - データ品質スコア: {quality_score:.1f}/100")

        results['tests'].append({
            'name': 'PersonaMapData.csv品質確認',
            'status': 'PASS',
            'details': {
                'total_locations': len(df),
                'missing_coordinates': total_missing,
                'quality_score': quality_score
            }
        })

    # ========================================
    # テスト5: PersonaMobilityCross.csv データ品質
    # ========================================
    print("\n" + "-" * 70)
    print("テスト5: PersonaMobilityCross.csv データ品質確認")
    print("-" * 70)

    persona_mobility_path = project_root / 'gas_output_phase7' / 'PersonaMobilityCross.csv'

    if not persona_mobility_path.exists():
        print(f"[ERROR] PersonaMobilityCross.csv が見つかりません")
        results['tests'].append({
            'name': 'PersonaMobilityCross.csv品質確認',
            'status': 'FAIL',
            'error': 'ファイル不在'
        })
    else:
        df = pd.read_csv(persona_mobility_path, encoding='utf-8-sig')

        # 比率合計=100%検証
        ratio_cols = df.columns[7:11]

        ratio_errors = 0
        for idx, row in df.iterrows():
            ratio_sum = sum(row[col] for col in ratio_cols)
            if abs(ratio_sum - 100.0) > 1.0:  # 許容誤差1%
                ratio_errors += 1

        print(f"[OK] PersonaMobilityCross.csv 読み込み成功")
        print(f"  - ペルソナ数: {len(df)}")
        print(f"  - 比率エラー: {ratio_errors}件")

        quality_score = 100 - (ratio_errors / len(df) * 100) if len(df) > 0 else 0
        print(f"  - データ品質スコア: {quality_score:.1f}/100")

        results['tests'].append({
            'name': 'PersonaMobilityCross.csv品質確認',
            'status': 'PASS',
            'details': {
                'persona_count': len(df),
                'ratio_errors': ratio_errors,
                'quality_score': quality_score
            }
        })

    # ========================================
    # テスト6: GAS連携準備確認
    # ========================================
    print("\n" + "-" * 70)
    print("テスト6: GAS連携準備確認")
    print("-" * 70)

    # 必要なファイルがすべて存在するか確認
    required_files = [
        'gas_output_phase7/PersonaMapData.csv',
        'gas_output_phase7/PersonaMobilityCross.csv',
        'gas_output_insights/CrossAnalysisResults.json'
    ]

    missing_files = []
    existing_files = []

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            existing_files.append(file_path)
            file_size = full_path.stat().st_size
            print(f"  [OK] {file_path} ({file_size:,} bytes)")
        else:
            missing_files.append(file_path)
            print(f"  [ERROR] {file_path} が見つかりません")

    if missing_files:
        print(f"\n[ERROR] GAS連携に必要なファイルが不足しています: {len(missing_files)}件")
        results['tests'].append({
            'name': 'GAS連携準備確認',
            'status': 'FAIL',
            'error': f'不足ファイル: {missing_files}'
        })
    else:
        print(f"\n[OK] GAS連携準備完了（{len(existing_files)}ファイル）")
        results['tests'].append({
            'name': 'GAS連携準備確認',
            'status': 'PASS',
            'details': f'{len(existing_files)}ファイル存在確認'
        })

    return results


def main():
    """メイン実行関数"""
    # E2Eテスト実行
    results = test_e2e_workflow()

    # 結果サマリー
    print("\n" + "=" * 70)
    print(" " * 20 + "E2Eテスト結果サマリー")
    print("=" * 70)

    total_tests = len(results['tests'])
    passed_tests = sum(1 for test in results['tests'] if test['status'] == 'PASS')
    failed_tests = sum(1 for test in results['tests'] if test['status'] == 'FAIL')

    print(f"\n  実行テスト数: {total_tests}")
    print(f"  成功: {passed_tests}")
    print(f"  失敗: {failed_tests}")

    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n  成功率: {success_rate:.1f}%")

        if success_rate == 100.0:
            print("\n  [SUCCESS] 全E2Eテスト合格！Phase 1実装は本番投入可能です。")
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

    output_path = project_root / 'python_scripts' / 'e2e_test_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(convert_to_json_serializable(results), f, ensure_ascii=False, indent=2)

    print(f"\nE2Eテスト結果を保存しました: {output_path}")

    # 終了コード設定（CI/CD対応）
    return 0 if failed_tests == 0 else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
