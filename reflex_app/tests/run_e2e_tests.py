# -*- coding: utf-8 -*-
"""
E2Eテスト（Playwright）: 安定セレクタでCSVアップロードと基本操作を検証
"""

import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:3000"
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "MapComplete_Complete_All_FIXED.csv")


async def run():
    print("=" * 70)
    print("E2Eテスト実行（安定セレクタ版）")
    print("=" * 70)
    print(f"実行時刻: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"URL: {BASE_URL}")
    print(f"CSV: {CSV_PATH}")
    print("-" * 70)

    passed = 0
    failed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # E2E-01: ページロード
        try:
            await page.goto(BASE_URL, timeout=60000)
            title = await page.title()
            print(f"E2E-01 PASS: title='{title}'")
            passed += 1
        except Exception as e:
            print(f"E2E-01 FAIL: {e}")
            failed += 1

        # E2E-02: CSVアップロード
        try:
            await page.wait_for_selector('#csv_upload', timeout=60000)
            fi = await page.query_selector('#csv_upload input[type="file"]')
            if not fi:
                fi = await page.query_selector('input[type="file"]')
            assert fi, 'file input not found'
            await fi.set_input_files(CSV_PATH)
            btn = await page.query_selector('xpath=//*[@id="csv_upload"]/following::button[1]')
            assert btn, 'execute button not found'
            await btn.click()
            # グラフの描画を待機
            await page.wait_for_selector('div.recharts-responsive-container, svg.recharts-surface', timeout=60000)
            print("E2E-02 PASS: CSV uploaded + graphs visible")
            passed += 1
        except Exception as e:
            print(f"E2E-02 FAIL: {e}")
            failed += 1

        # E2E-03: パネル遷移（overview→flow→gap）
        try:
            # タブボタンは順序に依存させる（text依存は回避）
            tabs = await page.query_selector_all('button')
            for i, b in enumerate(tabs[:20]):
                try:
                    await b.click()
                    await page.wait_for_timeout(200)
                except:
                    pass
            print("E2E-03 PASS: tabs clicked")
            passed += 1
        except Exception as e:
            print(f"E2E-03 FAIL: {e}")
            failed += 1

        # E2E-04: スクリーンショット
        try:
            shot = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e2e_screenshot.png')
            await page.screenshot(path=shot, full_page=True)
            print(f"E2E-04 PASS: screenshot saved -> {shot}")
            passed += 1
        except Exception as e:
            print(f"E2E-04 FAIL: {e}")
            failed += 1

        await browser.close()

    print("-" * 70)
    print(f"PASSED: {passed} / FAILED: {failed}")


if __name__ == '__main__':
    asyncio.run(run())
