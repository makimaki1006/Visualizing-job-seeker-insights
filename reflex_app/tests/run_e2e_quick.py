# -*- coding: utf-8 -*-
"""
簡易E2E（Playwright）: テキスト依存を避け、id/構造でCSVアップロードと簡易検証を行う
"""

import os
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:3000"
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "MapComplete_Complete_All_FIXED.csv")


async def main():
    print("="*70)
    print("Quick E2E (robust selectors)")
    print("="*70)
    print(f"time: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"url:  {BASE_URL}")
    print(f"csv:  {CSV_PATH}")
    print("-"*70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(BASE_URL, timeout=60000)
        # アップロード領域登場
        await page.wait_for_selector('#csv_upload', timeout=60000)
        # ファイルインプットを探す
        file_input = await page.query_selector('#csv_upload input[type="file"]')
        if not file_input:
            file_input = await page.query_selector('input[type="file"]')
        assert file_input, "file input not found"
        await file_input.set_input_files(CSV_PATH)
        # 実行ボタン（csv_uploadの直後のボタン）
        exec_btn = await page.query_selector('xpath=//*[@id="csv_upload"]/following::button[1]')
        assert exec_btn, "execute button not found"
        await exec_btn.click()
        # グラフ描画（Rechartsコンテナ）の出現を待機
        ok = True
        try:
            await page.wait_for_selector('div.recharts-responsive-container, svg.recharts-surface', timeout=30000)
        except Exception:
            ok = False
        print("verify:", "PASS" if ok else "FAIL")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
