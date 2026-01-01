#!/usr/bin/env python3
"""
RESIDENCE_FLOW関数の修正検証スクリプト
修正した4つの関数が正しく動作するかテスト
"""
import sys
import os
import io

# Windows環境でのUnicode出力対応
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# db_helperをインポート
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_helper import (
    get_flow_lines,
    get_inflow_sources,
    get_flow_balance,
    get_competing_areas
)

def test_get_flow_lines():
    """get_flow_lines()のテスト"""
    print("\n" + "="*60)
    print("TEST 1: get_flow_lines('東京都')")
    print("="*60)

    result = get_flow_lines("東京都")

    if not result:
        print("❌ FAIL: 結果が空")
        return False

    print(f"✅ 結果: {len(result)}件のフローライン")

    # 最初の3件を表示
    for i, line in enumerate(result[:3]):
        print(f"  [{i+1}] {line.get('from_location', 'N/A')} → {line.get('to_location', 'N/A')} (count: {line.get('count', 0)})")

    # category1が含まれていないことを確認（年齢層が地名として使われていない）
    age_groups = ['20代', '30代', '40代', '50代', '60代以上', '10代']
    for line in result:
        to_loc = line.get('to_location', '')
        if to_loc in age_groups:
            print(f"❌ FAIL: to_locationに年齢層が含まれている: {to_loc}")
            return False

    print("✅ to_locationに年齢層は含まれていない")
    return True


def test_get_inflow_sources():
    """get_inflow_sources()のテスト"""
    print("\n" + "="*60)
    print("TEST 2: get_inflow_sources('東京都', '千代田区')")
    print("="*60)

    result = get_inflow_sources("東京都", "千代田区")

    if not result:
        print("❌ FAIL: 結果が空")
        return False

    print(f"✅ 結果: {len(result)}件の流入元")

    # 最初の5件を表示
    for i, source in enumerate(result[:5]):
        print(f"  [{i+1}] {source.get('prefecture', 'N/A')} {source.get('municipality', 'N/A')}: {source.get('count', 0)}人 ({source.get('percentage', 0):.1f}%)")

    # パーセンテージの合計が100%以下であることを確認
    total_pct = sum(s.get('percentage', 0) for s in result)
    if total_pct > 101:  # 丸め誤差を考慮
        print(f"❌ FAIL: パーセンテージ合計が異常: {total_pct:.1f}%")
        return False

    print(f"✅ パーセンテージ合計: {total_pct:.1f}%")
    return True


def test_get_flow_balance():
    """get_flow_balance()のテスト"""
    print("\n" + "="*60)
    print("TEST 3: get_flow_balance('東京都')")
    print("="*60)

    result = get_flow_balance("東京都")

    if not result:
        print("X FAIL: 結果が空")
        return False

    print(f"OK 結果: {len(result)}件の市区町村")

    # 最初の5件を表示
    for i, item in enumerate(result[:5]):
        muni = item.get('municipality', 'N/A')
        inflow = item.get('inflow', 0)
        outflow = item.get('outflow', 0)
        net_flow = item.get('net_flow', 0)  # balanceではなくnet_flow
        print(f"  [{i+1}] {muni}: 流入{inflow}, 流出{outflow}, 収支{net_flow:+d}")

    # net_flowがinflow - outflowと一致することを確認
    for item in result[:10]:
        expected = item.get('inflow', 0) - item.get('outflow', 0)
        actual = item.get('net_flow', 0)  # balanceではなくnet_flow
        if expected != actual:
            print(f"X FAIL: net_flow計算が不正: {item.get('municipality')} (expected={expected}, actual={actual})")
            return False

    print("OK net_flow計算は正常")
    return True


def test_get_competing_areas():
    """get_competing_areas()のテスト"""
    print("\n" + "="*60)
    print("TEST 4: get_competing_areas('東京都', '千代田区')")
    print("="*60)

    result = get_competing_areas("東京都", "千代田区")

    if not result:
        print("❌ FAIL: 結果が空")
        return False

    print(f"✅ 結果: {len(result)}件の競合地域")

    # 最初の5件を表示
    for i, area in enumerate(result[:5]):
        target = area.get('target_municipality', 'N/A')
        count = area.get('count', 0)
        share = area.get('share', 0)
        print(f"  [{i+1}] {target}: {count}人 ({share:.1f}%)")

    # category1/category2（年齢層/性別）が地名として使われていないことを確認
    invalid_values = ['20代', '30代', '40代', '50代', '60代以上', '10代', '男性', '女性']
    for area in result:
        target = area.get('target_municipality', '')
        if target in invalid_values:
            print(f"❌ FAIL: target_municipalityに年齢層/性別が含まれている: {target}")
            return False

    print("✅ target_municipalityに年齢層/性別は含まれていない")
    return True


def main():
    """全テスト実行"""
    print("\n" + "="*60)
    print("RESIDENCE_FLOW関数 修正検証テスト")
    print("="*60)

    tests = [
        ("get_flow_lines", test_get_flow_lines),
        ("get_inflow_sources", test_get_inflow_sources),
        ("get_flow_balance", test_get_flow_balance),
        ("get_competing_areas", test_get_competing_areas),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # サマリー
    print("\n" + "="*60)
    print("テスト結果サマリー")
    print("="*60)

    passed = sum(1 for _, s in results if s)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\n結果: {passed}/{total} テスト成功")

    if passed == total:
        print("\n🎉 全テスト成功！修正は正常に機能しています。")
        return 0
    else:
        print("\n⚠️ 一部テストが失敗しました。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
