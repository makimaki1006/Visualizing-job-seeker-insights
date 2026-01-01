#!/usr/bin/env python3
"""Markdown to PDF converter using Playwright"""

import markdown2
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

async def convert_md_to_pdf():
    # パス設定
    docs_dir = Path(__file__).parent
    md_file = docs_dir / "SALES_MATERIAL_20251225.md"
    html_file = docs_dir / "SALES_MATERIAL_20251225.html"
    pdf_file = docs_dir / "SALES_MATERIAL_20251225.pdf"
    screenshots_dir = docs_dir / "screenshots"

    # Markdown読み込み
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Markdown → HTML変換
    html_content = markdown2.markdown(
        md_content,
        extras=['tables', 'fenced-code-blocks', 'code-friendly']
    )

    # 画像パスを絶対パスに変換
    html_content = html_content.replace(
        'src="screenshots/',
        f'src="{screenshots_dir.as_posix()}/'
    )

    # 完全なHTMLドキュメント作成
    full_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>job_ap_analyzer_gui 営業資料</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}

        body {{
            font-family: "Yu Gothic", "Meiryo", "Hiragino Sans", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
        }}

        h1 {{
            font-size: 22pt;
            color: #1a1a2e;
            border-bottom: 3px solid #4a90a4;
            padding-bottom: 10px;
            margin-top: 25px;
            page-break-after: avoid;
        }}

        h2 {{
            font-size: 16pt;
            color: #16213e;
            border-left: 5px solid #4a90a4;
            padding-left: 15px;
            margin-top: 20px;
            page-break-after: avoid;
        }}

        h3 {{
            font-size: 13pt;
            color: #0f3460;
            margin-top: 15px;
            page-break-after: avoid;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
            font-size: 10pt;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}

        th {{
            background-color: #4a90a4;
            color: white;
        }}

        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 12px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        blockquote {{
            border-left: 4px solid #4a90a4;
            margin: 12px 0;
            color: #555;
            font-style: italic;
            background-color: #f5f5f5;
            padding: 10px 15px;
        }}

        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: "Consolas", monospace;
            font-size: 9pt;
        }}

        pre {{
            background-color: #f4f4f4;
            padding: 12px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 9pt;
        }}

        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 15px 0;
        }}

        strong {{
            color: #1a1a2e;
        }}

        ul, ol {{
            padding-left: 20px;
        }}

        li {{
            margin: 4px 0;
        }}

        /* ページ分割の最適化 */
        h1, h2, h3 {{
            page-break-after: avoid;
        }}

        table, img {{
            page-break-inside: avoid;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

    # HTMLファイル保存
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"HTML生成完了: {html_file}")

    # PlaywrightでPDF生成
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # HTMLファイルを開く
        await page.goto(f"file:///{html_file.as_posix()}")

        # PDF生成
        await page.pdf(
            path=str(pdf_file),
            format="A4",
            margin={
                "top": "1.5cm",
                "bottom": "1.5cm",
                "left": "1.5cm",
                "right": "1.5cm"
            },
            print_background=True
        )

        await browser.close()

    print(f"PDF生成完了: {pdf_file}")
    return pdf_file

if __name__ == "__main__":
    asyncio.run(convert_md_to_pdf())
