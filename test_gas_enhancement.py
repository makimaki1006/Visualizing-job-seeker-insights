#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GAS改良機能テストスクリプト

新しく追加した2つのCSV生成機能をテスト:
1. PersonaMobilityCross.csv - ペルソナ×移動許容度クロス分析
2. PersonaMapData.csv - ペルソナ地図データ（座標付き）
"""

import sys
import pandas as pd
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "python_scripts"))

from phase7_advanced_analysis import Phase7AdvancedAnalyzer
import json

def load_test_data():
    """テスト用データ読み込み"""
    print("=" * 60)
    print("テストデータ読み込み中...")
    print("=" * 60)

    # 既存のPhase 7出力を読み込み
    phase7_dir = Path("gas_output_phase7")

    # MobilityScore.csv（必須）
    mobility_score_path = phase7_dir / "MobilityScore.csv"
    if not mobility_score_path.exists():
        print(f"[ERROR] {mobility_score_path} が見つかりません")
        return None, None, None

    mobility_score = pd.read_csv(mobility_score_path, encoding='utf-8-sig')
    print(f"  [OK] MobilityScore.csv: {len(mobility_score)}行")

    # processed_data_complete.csv（必須）
    processed_path = Path("processed_data_complete.csv")
    if not processed_path.exists():
        print(f"[ERROR] {processed_path} が見つかりません")
        return None, None, None

    df_processed = pd.read_csv(processed_path, encoding='utf-8-sig')
    print(f"  [OK] processed_data_complete.csv: {len(df_processed)}行")

    # geocache.json（必須）
    geocache_path = Path("../geocache.json")
    if not geocache_path.exists():
        geocache_path = Path("geocache.json")

    if not geocache_path.exists():
        print(f"[ERROR] geocache.json が見つかりません")
        print("  探索パス:")
        print(f"    - {Path('geocache.json').absolute()}")
        print(f"    - {Path('../geocache.json').absolute()}")
        return None, None, None

    with open(geocache_path, 'r', encoding='utf-8') as f:
        geocache = json.load(f)
    print(f"  [OK] geocache.json: {len(geocache)}エントリ")

    return df_processed, mobility_score, geocache

def test_persona_mobility_cross(analyzer):
    """ペルソナ×移動許容度クロス分析テスト"""
    print("\n" + "=" * 60)
    print("テスト1: ペルソナ×移動許容度クロス分析")
    print("=" * 60)

    # mobility_scoreをresultsに設定
    analyzer.results['mobility_score'] = pd.read_csv(
        "gas_output_phase7/MobilityScore.csv",
        encoding='utf-8-sig'
    )

    result = analyzer._generate_persona_mobility_cross()

    if result is None or len(result) == 0:
        print("  [FAIL] データ生成失敗")
        return False

    print(f"  [OK] 生成行数: {len(result)}行")
    print(f"  [OK] カラム: {list(result.columns)}")
    print("\n  サンプルデータ:")
    print(result.head().to_string())

    # CSV出力
    output_path = Path("gas_output_phase7/PersonaMobilityCross.csv")
    result.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n  [OK] 出力完了: {output_path}")

    # 検証
    checks = []
    checks.append(("ペルソナID列存在", 'ペルソナID' in result.columns))
    checks.append(("ペルソナ名列存在", 'ペルソナ名' in result.columns))
    checks.append(("Aレベル列存在", 'A' in result.columns))
    checks.append(("Bレベル列存在", 'B' in result.columns))
    checks.append(("Cレベル列存在", 'C' in result.columns))
    checks.append(("Dレベル列存在", 'D' in result.columns))
    checks.append(("合計列存在", '合計' in result.columns))
    checks.append(("データ件数妥当", 5 <= len(result) <= 15))

    print("\n  検証結果:")
    all_pass = True
    for check_name, check_result in checks:
        status = "[OK]" if check_result else "[FAIL]"
        print(f"    {status} {check_name}")
        if not check_result:
            all_pass = False

    return all_pass

def test_persona_map_data(analyzer):
    """ペルソナ地図データテスト"""
    print("\n" + "=" * 60)
    print("テスト2: ペルソナ地図データ（座標付き）")
    print("=" * 60)

    result = analyzer._generate_persona_map_data()

    if result is None or len(result) == 0:
        print("  [FAIL] データ生成失敗")
        return False

    print(f"  [OK] 生成行数: {len(result)}行")
    print(f"  [OK] カラム: {list(result.columns)}")
    print("\n  サンプルデータ:")
    print(result.head().to_string())

    # CSV出力
    output_path = Path("gas_output_phase7/PersonaMapData.csv")
    result.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n  [OK] 出力完了: {output_path}")

    # 検証
    checks = []
    checks.append(("市区町村列存在", '市区町村' in result.columns))
    checks.append(("緯度列存在", '緯度' in result.columns))
    checks.append(("経度列存在", '経度' in result.columns))
    checks.append(("ペルソナID列存在", 'ペルソナID' in result.columns))
    checks.append(("ペルソナ名列存在", 'ペルソナ名' in result.columns))
    checks.append(("求職者数列存在", '求職者数' in result.columns))
    checks.append(("座標欠損なし", result['緯度'].notna().all() and result['経度'].notna().all()))
    checks.append(("データ件数妥当", 100 <= len(result) <= 500))

    print("\n  検証結果:")
    all_pass = True
    for check_name, check_result in checks:
        status = "[OK]" if check_result else "[FAIL]"
        print(f"    {status} {check_name}")
        if not check_result:
            all_pass = False

    return all_pass

def main():
    """メインテスト実行"""
    print("\n")
    print("=" * 60)
    print("GAS改良機能テスト開始")
    print("=" * 60)

    # データ読み込み
    df_processed, mobility_score, geocache = load_test_data()

    if df_processed is None:
        print("\n[FAIL] テストデータ読み込み失敗")
        return 1

    # Analyzerインスタンス作成（dfとmasterはNoneでOK）
    analyzer = Phase7AdvancedAnalyzer(
        df=None,
        df_processed=df_processed,
        geocache=geocache,
        master=None
    )

    # テスト実行
    test1_pass = test_persona_mobility_cross(analyzer)
    test2_pass = test_persona_map_data(analyzer)

    # 総合結果
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"  テスト1（クロス分析）: {'[PASS]' if test1_pass else '[FAIL]'}")
    print(f"  テスト2（地図データ）: {'[PASS]' if test2_pass else '[FAIL]'}")

    if test1_pass and test2_pass:
        print("\n[SUCCESS] すべてのテストに合格しました！")
        print("\n生成されたファイル:")
        print("  - gas_output_phase7/PersonaMobilityCross.csv")
        print("  - gas_output_phase7/PersonaMapData.csv")
        return 0
    else:
        print("\n[FAIL] 一部のテストが失敗しました")
        return 1

if __name__ == '__main__':
    exit(main())
