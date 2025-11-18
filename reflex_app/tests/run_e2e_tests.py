# -*- coding: utf-8 -*-
"""
E2Eテスト実行スクリプト（Playwright）

実際のブラウザで操作を行い、ダッシュボードの動作を検証します。
"""

import sys
import os
import time
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

# テスト設定
BASE_URL = "http://localhost:3000"
CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "MapComplete_Complete_All_FIXED.csv"
)


async def run_e2e_tests():
    """E2Eテストを実行"""
    print("=" * 70)
    print("E2Eテスト実行（Playwright）")
    print("=" * 70)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象URL: {BASE_URL}")
    print(f"CSVファイル: {CSV_PATH}")
    print("-" * 70)

    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }

    async with async_playwright() as p:
        # ブラウザ起動
        browser = await p.chromium.launch(headless=False)  # headless=Falseで可視化
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # =================================================================
            # E2E-01: ページロード
            # =================================================================
            print("\nE2E-01: ページロード")
            try:
                await page.goto(BASE_URL, timeout=30000)
                title = await page.title()
                print(f"  タイトル: {title}")
                results['passed'] += 1
                results['tests'].append({'name': 'E2E-01', 'status': 'PASS', 'detail': f'title={title}'})
                print("  [PASS]")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-01', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # =================================================================
            # E2E-02: CSVアップロード
            # =================================================================
            print("\nE2E-02: CSVアップロード")
            try:
                # Reflexのファイルアップロードボタンを探す
                upload_button = await page.query_selector('text=CSVをアップロード')
                if upload_button:
                    # ファイル選択ダイアログをトリガー
                    async with page.expect_file_chooser() as fc_info:
                        await upload_button.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(CSV_PATH)
                    print(f"  ファイル選択: {os.path.basename(CSV_PATH)}")

                    # アップロード実行ボタンをクリック
                    await page.wait_for_timeout(1000)
                    execute_button = await page.query_selector('text=アップロード実行')
                    if execute_button:
                        await execute_button.click()
                        print("  アップロード実行クリック")

                    # アップロード完了を待つ
                    await page.wait_for_timeout(5000)

                    # データロード確認
                    body_text = await page.inner_text('body')
                    if '京都' in body_text or '東京' in body_text or '大阪' in body_text or '滋賀' in body_text:
                        results['passed'] += 1
                        results['tests'].append({'name': 'E2E-02', 'status': 'PASS', 'detail': 'CSV loaded'})
                        print("  [PASS] データロード確認")
                    else:
                        results['failed'] += 1
                        results['tests'].append({'name': 'E2E-02', 'status': 'FAIL', 'error': 'Data not loaded'})
                        print("  [FAIL] データが読み込まれていない")
                else:
                    results['failed'] += 1
                    results['tests'].append({'name': 'E2E-02', 'status': 'FAIL', 'error': 'Upload button not found'})
                    print("  [FAIL] アップロードボタンが見つからない")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-02', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # =================================================================
            # E2E-03: 都道府県選択（京都府）
            # =================================================================
            print("\nE2E-03: 都道府県選択（京都府）")
            try:
                # Reflexのカスタムドロップダウンを探す
                pref_dropdown = await page.query_selector('text=都道府県を選択')
                if pref_dropdown:
                    await pref_dropdown.click()
                    await page.wait_for_timeout(500)

                    # ドロップダウンメニューから京都府を選択
                    kyoto_option = await page.query_selector('text=京都府')
                    if kyoto_option:
                        await kyoto_option.click()
                        await page.wait_for_timeout(2000)

                        body_text = await page.inner_text('body')
                        if '京都' in body_text:
                            results['passed'] += 1
                            results['tests'].append({'name': 'E2E-03', 'status': 'PASS', 'detail': 'Kyoto selected'})
                            print("  [PASS] 京都府選択確認")
                        else:
                            results['failed'] += 1
                            results['tests'].append({'name': 'E2E-03', 'status': 'FAIL', 'error': 'Kyoto not shown'})
                            print("  [FAIL] 京都府が表示されていない")
                    else:
                        results['failed'] += 1
                        results['tests'].append({'name': 'E2E-03', 'status': 'FAIL', 'error': 'Kyoto option not found'})
                        print("  [FAIL] 京都府オプションが見つからない")
                else:
                    results['failed'] += 1
                    results['tests'].append({'name': 'E2E-03', 'status': 'FAIL', 'error': 'Prefecture dropdown not found'})
                    print("  [FAIL] 都道府県ドロップダウンが見つからない")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-03', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # =================================================================
            # E2E-04: 都道府県変更（大阪府）
            # =================================================================
            print("\nE2E-04: 都道府県変更（大阪府）")
            try:
                # 現在選択されている都道府県（京都府）をクリックしてドロップダウンを開く
                pref_current = await page.query_selector('text=京都府')
                if pref_current:
                    await pref_current.click()
                    await page.wait_for_timeout(500)

                    # 大阪府を選択
                    osaka_option = await page.query_selector('text=大阪府')
                    if osaka_option:
                        await osaka_option.click()
                        await page.wait_for_timeout(2000)

                        body_text = await page.inner_text('body')
                        if '大阪' in body_text:
                            results['passed'] += 1
                            results['tests'].append({'name': 'E2E-04', 'status': 'PASS', 'detail': 'Osaka selected'})
                            print("  [PASS] 大阪府選択確認")
                        else:
                            results['failed'] += 1
                            results['tests'].append({'name': 'E2E-04', 'status': 'FAIL', 'error': 'Osaka not shown'})
                            print("  [FAIL] 大阪府が表示されていない")
                    else:
                        results['failed'] += 1
                        results['tests'].append({'name': 'E2E-04', 'status': 'FAIL', 'error': 'Osaka option not found'})
                        print("  [FAIL] 大阪府オプションが見つからない")
                else:
                    results['failed'] += 1
                    results['tests'].append({'name': 'E2E-04', 'status': 'FAIL', 'error': 'Current prefecture not found'})
                    print("  [FAIL] 現在の都道府県が見つからない")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-04', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # =================================================================
            # E2E-05: タブ切り替え確認
            # =================================================================
            print("\nE2E-05: タブ切り替え確認")
            tabs_to_test = [
                '総合概要',
                '人材供給',
                'フロー分析',
                '需給バランス'
            ]

            tab_results = []
            for tab_name in tabs_to_test:
                try:
                    tab_element = await page.query_selector(f'text={tab_name}')
                    if tab_element:
                        await tab_element.click()
                        await page.wait_for_timeout(1000)
                        tab_results.append(f"{tab_name}: OK")
                    else:
                        tab_results.append(f"{tab_name}: Not found")
                except Exception as e:
                    tab_results.append(f"{tab_name}: Error")

            if all('OK' in r for r in tab_results):
                results['passed'] += 1
                results['tests'].append({'name': 'E2E-05', 'status': 'PASS', 'detail': tab_results})
                print(f"  [PASS] {tab_results}")
            else:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-05', 'status': 'FAIL', 'detail': tab_results})
                print(f"  [PARTIAL] {tab_results}")

            # =================================================================
            # E2E-06: グラフ要素の存在確認
            # =================================================================
            print("\nE2E-06: グラフ要素の存在確認")
            try:
                # SVGまたはcanvas要素を探す（グラフコンポーネント）
                svg_elements = await page.query_selector_all('svg')
                canvas_elements = await page.query_selector_all('canvas')

                total_graph_elements = len(svg_elements) + len(canvas_elements)

                if total_graph_elements > 0:
                    results['passed'] += 1
                    results['tests'].append({'name': 'E2E-06', 'status': 'PASS',
                                             'detail': f'svg={len(svg_elements)}, canvas={len(canvas_elements)}'})
                    print(f"  [PASS] グラフ要素: svg={len(svg_elements)}, canvas={len(canvas_elements)}")
                else:
                    results['failed'] += 1
                    results['tests'].append({'name': 'E2E-06', 'status': 'FAIL', 'error': 'No graph elements'})
                    print("  [FAIL] グラフ要素が見つからない")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-06', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # =================================================================
            # E2E-07: エラー表示の確認（エラーがないこと）
            # =================================================================
            print("\nE2E-07: エラー表示の確認")
            try:
                body_text = await page.inner_text('body')
                error_keywords = ['Error', 'KeyError', 'TypeError', 'Exception']

                has_error = any(kw in body_text for kw in error_keywords)

                if not has_error:
                    results['passed'] += 1
                    results['tests'].append({'name': 'E2E-07', 'status': 'PASS', 'detail': 'No errors'})
                    print("  [PASS] エラー表示なし")
                else:
                    results['failed'] += 1
                    found_errors = [kw for kw in error_keywords if kw in body_text]
                    results['tests'].append({'name': 'E2E-07', 'status': 'FAIL', 'error': found_errors})
                    print(f"  [FAIL] エラー検出: {found_errors}")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-07', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # =================================================================
            # E2E-08: 都道府県変更後のデータ更新確認
            # =================================================================
            print("\nE2E-08: 都道府県変更後のデータ更新確認")
            try:
                # 現在選択されている都道府県をクリック
                pref_current = await page.query_selector('text=大阪府')
                if pref_current:
                    await pref_current.click()
                    await page.wait_for_timeout(500)

                    # 三重県を選択
                    mie_option = await page.query_selector('text=三重県')
                    if mie_option:
                        await mie_option.click()
                        await page.wait_for_timeout(2000)

                        body_text = await page.inner_text('body')

                        # 三重県のデータが表示されることを確認
                        if '三重' in body_text:
                            results['passed'] += 1
                            results['tests'].append({'name': 'E2E-08', 'status': 'PASS', 'detail': 'Mie data shown'})
                            print("  [PASS] 三重県データ表示確認")
                        else:
                            results['failed'] += 1
                            results['tests'].append({'name': 'E2E-08', 'status': 'FAIL', 'error': 'Mie not shown'})
                            print("  [FAIL] 三重県が表示されていない")
                    else:
                        results['failed'] += 1
                        results['tests'].append({'name': 'E2E-08', 'status': 'FAIL', 'error': 'Mie option not found'})
                        print("  [FAIL] 三重県オプションが見つからない")
                else:
                    results['failed'] += 1
                    results['tests'].append({'name': 'E2E-08', 'status': 'FAIL', 'error': 'Current prefecture not found'})
                    print("  [FAIL] 現在の都道府県が見つからない")
            except Exception as e:
                results['failed'] += 1
                results['tests'].append({'name': 'E2E-08', 'status': 'FAIL', 'error': str(e)})
                print(f"  [FAIL] {e}")

            # スクリーンショット保存
            screenshot_path = os.path.join(
                os.path.dirname(__file__),
                'e2e_screenshot.png'
            )
            await page.screenshot(path=screenshot_path)
            print(f"\nスクリーンショット保存: {screenshot_path}")

        finally:
            await browser.close()

    # =================================================================
    # 結果サマリー
    # =================================================================
    print("\n" + "=" * 70)
    print("E2Eテスト結果サマリー")
    print("=" * 70)
    print(f"成功: {results['passed']}")
    print(f"失敗: {results['failed']}")
    print(f"合計: {results['passed'] + results['failed']}")
    print("-" * 70)

    for test in results['tests']:
        status = test['status']
        name = test['name']
        if status == 'PASS':
            print(f"  {name}: PASS - {test.get('detail', '')}")
        else:
            print(f"  {name}: FAIL - {test.get('error', test.get('detail', ''))}")

    return results


if __name__ == "__main__":
    results = asyncio.run(run_e2e_tests())

    # 終了コード設定
    if results['failed'] > 0:
        sys.exit(1)
    sys.exit(0)
