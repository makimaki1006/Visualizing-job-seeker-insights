# -*- coding: utf-8 -*-
"""
V3 CSV統合テストスイート

テスト項目:
1. CSVファイルの読み込み
2. row_type分布の検証
3. 必須カラムの存在確認
4. データ型の整合性
5. DashboardStateでの読み込みテスト
"""

import sys
import pandas as pd
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

def test_csv_loading():
    """テスト1: CSVファイルの読み込み"""
    print("\n" + "=" * 60)
    print("テスト1: V3 CSVファイルの読み込み")
    print("=" * 60)

    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"

    if not csv_path.exists():
        print(f"[FAIL] CSVファイルが見つかりません: {csv_path}")
        return False

    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
        print("[OK] CSVファイル読み込み成功")
        print(f"   総行数: {len(df):,}行")
        print(f"   カラム数: {len(df.columns)}カラム")
        return True
    except Exception as e:
        print(f"[FAIL] CSV読み込みエラー: {e}")
        return False


def test_row_type_distribution():
    """テスト2: row_type分布の検証"""
    print("\n" + "=" * 60)
    print("テスト2: row_type分布の検証")
    print("=" * 60)

    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)

    expected_row_types = [
        'SUMMARY', 'AGE_GENDER', 'FLOW', 'GAP',
        'COMPETITION', 'RARITY', 'URGENCY_AGE', 'URGENCY_EMPLOYMENT'
    ]

    row_type_counts = df['row_type'].value_counts()

    print("\nrow_type分布:")
    for rt in expected_row_types:
        count = row_type_counts.get(rt, 0)
        status = "[OK]" if count > 0 else "[NG]"
        print(f"  {status} {rt}: {count:,}行")

    # すべてのrow_typeが存在するか確認
    all_present = all(rt in row_type_counts.index for rt in expected_row_types)

    if all_present:
        print("\n[OK] すべてのrow_typeが存在します")
        return True
    else:
        print("\n[NG] 一部のrow_typeが欠けています")
        return False


def test_required_columns():
    """テスト3: 必須カラムの存在確認"""
    print("\n" + "=" * 60)
    print("テスト3: 必須カラムの存在確認")
    print("=" * 60)

    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)

    required_columns = [
        'row_type', 'prefecture', 'municipality',
        'category1', 'category2', 'category3',
        'applicant_count', 'avg_age',
        'male_count', 'female_count',
        'inflow', 'outflow', 'net_flow',
        'demand_count', 'supply_count', 'gap',
        'rarity_score', 'avg_urgency_score'
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"[NG] 欠けているカラム: {missing_columns}")
        return False
    else:
        print(f"[OK] すべての必須カラムが存在します（{len(required_columns)}個）")
        return True


def test_data_types():
    """テスト4: データ型の整合性"""
    print("\n" + "=" * 60)
    print("テスト4: データ型の整合性")
    print("=" * 60)

    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)

    # 数値カラムのサンプル
    numeric_columns = [
        'applicant_count', 'avg_age', 'male_count', 'female_count',
        'inflow', 'outflow', 'gap', 'rarity_score'
    ]

    all_valid = True

    for col in numeric_columns:
        if col in df.columns:
            # NaNを除外してチェック
            non_null = df[col].dropna()
            if len(non_null) > 0:
                try:
                    # 数値に変換可能かチェック
                    pd.to_numeric(non_null, errors='raise')
                    print(f"  [OK] {col}: 数値型として有効")
                except Exception as e:
                    print(f"  [NG] {col}: 数値変換エラー - {e}")
                    all_valid = False

    if all_valid:
        print("\n[OK] データ型の整合性確認完了")
        return True
    else:
        print("\n[NG] データ型に問題があります")
        return False


def test_dashboard_state_integration():
    """テスト5: DashboardStateでの読み込みテスト"""
    print("\n" + "=" * 60)
    print("テスト5: DashboardStateでの読み込みテスト")
    print("=" * 60)

    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"

    try:
        # DashboardStateのデータ読み込みロジックをシミュレート
        df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)

        # 基本的なフィルタリングテスト
        summary_data = df[df['row_type'] == 'SUMMARY']
        print(f"  SUMMARYデータ: {len(summary_data)}行")

        # 都道府県でフィルタリング
        test_prefecture = df['prefecture'].dropna().iloc[0] if len(df) > 0 else None
        if test_prefecture:
            filtered = df[df['prefecture'] == test_prefecture]
            print(f"  {test_prefecture}のデータ: {len(filtered)}行")

        # row_type別のカウント
        for rt in ['AGE_GENDER', 'FLOW', 'GAP', 'COMPETITION', 'RARITY']:
            count = len(df[df['row_type'] == rt])
            print(f"  {rt}: {count:,}行")

        print("\n[OK] DashboardState統合テスト成功")
        return True

    except Exception as e:
        print(f"\n[NG] DashboardState統合テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prefecture_municipality_coverage():
    """テスト6: 都道府県・市区町村のカバレッジ"""
    print("\n" + "=" * 60)
    print("テスト6: 都道府県・市区町村のカバレッジ")
    print("=" * 60)

    csv_path = Path(__file__).parent / "MapComplete_Complete_All_FIXED.csv"
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)

    prefectures = df['prefecture'].dropna().unique()
    municipalities = df['municipality'].dropna().unique()

    print(f"  都道府県数: {len(prefectures)}")
    print(f"  市区町村数: {len(municipalities)}")

    # サンプル表示
    print(f"\n  都道府県サンプル: {list(prefectures[:5])}")
    print(f"  市区町村サンプル: {list(municipalities[:5])}")

    if len(prefectures) > 0 and len(municipalities) > 0:
        print("\n[OK] 地域データのカバレッジ確認完了")
        return True
    else:
        print("\n[NG] 地域データが不足しています")
        return False


def run_all_tests():
    """全テスト実行"""
    print("\n" + "=" * 60)
    print("V3 CSV統合テストスイート")
    print("=" * 60)

    results = {
        "CSV読み込み": test_csv_loading(),
        "row_type分布": test_row_type_distribution(),
        "必須カラム": test_required_columns(),
        "データ型": test_data_types(),
        "DashboardState統合": test_dashboard_state_integration(),
        "地域カバレッジ": test_prefecture_municipality_coverage(),
    }

    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] ALL TESTS PASSED! V3 CSV integration is working correctly.")
    else:
        print("[NG] Some tests failed. Please check details above.")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
