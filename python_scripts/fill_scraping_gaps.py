#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
スクレイピングギャップ補完スクリプト

verify_coverage.pyの結果に基づき、カバレッジ80%未満の県のURLを再収集し、
既存データとの差分（未取得URL）を特定する。

使用例:
    # 看護師の欠落県のURL収集＋差分分析
    python fill_scraping_gaps.py --job-type "看護師/准看護師" --threshold 80

    # 介護職の欠落県
    python fill_scraping_gaps.py --job-type "介護職/ヘルパー" --threshold 80

    # 確認のみ（URL収集しない）
    python fill_scraping_gaps.py --job-type "看護師/准看護師" --dry-run

出力:
    SCRAPING_DIR/missing_urls_{職種名}_{日付}.csv  （未取得URL一覧）
"""

import asyncio
import argparse
import csv
import logging
import math
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# === 設定 ===
BASE_URL = "https://job-medley.com"
ITEMS_PER_PAGE = 30

SCRAPING_DIR = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング"
)
SCRAPING_DIR_FEB = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング_2026_02_15"
)
DB_PATH = Path(__file__).parent.parent / "rust_dashboard" / "data" / "geocoded_postings.db"

JOB_TYPE_CODES = {
    "看護師/准看護師": "ans",
    "介護職/ヘルパー": "hh",
    "保育士": "cw",
    "ケアマネジャー": "cm",
    "作業療法士": "ot",
    "理学療法士": "pt",
    "歯科衛生士": "dh",
    "管理栄養士/栄養士": "nrd",
    "生活相談員": "la",
    "サービス提供責任者": "km",
    "サービス管理責任者": "dcm",
    "調理師/調理スタッフ": "ck",
    "薬剤師": "apo",
    "言語聴覚士": "st",
    "児童指導員": "apl",
    "児童発達支援管理責任者": "nm",
    "生活支援員": "ls",
    "幼稚園教諭": "kt",
    "放課後児童支援員・学童指導員": "asc",
}

PREFECTURE_CODES = {
    "北海道": "01", "青森県": "02", "岩手県": "03", "宮城県": "04",
    "秋田県": "05", "山形県": "06", "福島県": "07", "茨城県": "08",
    "栃木県": "09", "群馬県": "10", "埼玉県": "11", "千葉県": "12",
    "東京都": "13", "神奈川県": "14", "新潟県": "15", "富山県": "16",
    "石川県": "17", "福井県": "18", "山梨県": "19", "長野県": "20",
    "岐阜県": "21", "静岡県": "22", "愛知県": "23", "三重県": "24",
    "滋賀県": "25", "京都府": "26", "大阪府": "27", "兵庫県": "28",
    "奈良県": "29", "和歌山県": "30", "鳥取県": "31", "島根県": "32",
    "岡山県": "33", "広島県": "34", "山口県": "35", "徳島県": "36",
    "香川県": "37", "愛媛県": "38", "高知県": "39", "福岡県": "40",
    "佐賀県": "41", "長崎県": "42", "熊本県": "43", "大分県": "44",
    "宮崎県": "45", "鹿児島県": "46", "沖縄県": "47",
}

DB_NAME_MAP = {
    "看護師/准看護師": "看護師",
    "介護職/ヘルパー": "介護職",
    "管理栄養士/栄養士": "栄養士",
    "調理師/調理スタッフ": "調理師、調理スタッフ",
    "放課後児童支援員・学童指導員": "学童支援",
}


def build_page_url(job_code: str, pref_code: str, page: int) -> str:
    """検索結果ページURL生成"""
    if page <= 1:
        return f"{BASE_URL}/{job_code}/pref{pref_code}/"
    return f"{BASE_URL}/{job_code}/pref{pref_code}/?page={page}"


def extract_total_count(html: str) -> int:
    """検索結果HTMLから総件数を抽出"""
    match = re.search(r'"total"\s*:\s*(\d+)', html)
    if match:
        return int(match.group(1))
    match = re.search(r'([\d,]+)\s*件', html)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0


def extract_urls_from_page(html: str, job_code: str) -> list[str]:
    """ページHTMLから求人URLを抽出"""
    pattern = rf'href="(/{re.escape(job_code)}/\d+/)"'
    urls = re.findall(pattern, html)
    full_urls = []
    seen = set()
    for path in urls:
        url = f"{BASE_URL}{path}"
        if "ref_target=campaign" not in url and url not in seen:
            seen.add(url)
            full_urls.append(url)
    return full_urls


def get_jm_counts(job_code: str) -> dict[str, int]:
    """verify_coverageの結果キャッシュ用（実際はリアルタイム取得）"""
    # ここでは使わない、identify_gapsで取得
    return {}


def get_db_counts(job_type: str) -> dict[str, int]:
    """DB内の都道府県別件数"""
    db_name = DB_NAME_MAP.get(job_type, job_type)
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(str(DB_PATH))
    result = {}
    for row in conn.execute(
        "SELECT prefecture, COUNT(*) FROM postings WHERE job_type=? GROUP BY prefecture",
        (db_name,),
    ):
        result[row[0]] = row[1]
    conn.close()
    return result


def load_existing_urls(job_type: str) -> set[str]:
    """既存のURL CSV + details_output CSVからスクレイピング済みURLを収集"""
    existing = set()
    csv_name = job_type.replace("/", "・")

    # 既存URL CSV
    url_csv = SCRAPING_DIR / f"job_urls_{csv_name}.csv"
    if url_csv.exists():
        try:
            df = pd.read_csv(url_csv, encoding="utf-8-sig")
            if "URL" in df.columns:
                existing.update(df["URL"].dropna().tolist())
        except Exception as e:
            logger.warning(f"URL CSV読み込みエラー: {e}")

    logger.info(f"既存URL数: {len(existing):,}")
    return existing


async def identify_gaps(
    job_type: str, threshold: float, rate_limit: float
) -> list[dict]:
    """JM掲載数 vs DB件数を比較してギャップ県を特定"""
    job_code = JOB_TYPE_CODES.get(job_type)
    if not job_code:
        return []

    db_counts = get_db_counts(job_type)
    gaps = []

    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        },
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        for pref_name, pref_code in PREFECTURE_CODES.items():
            url = f"{BASE_URL}/{job_code}/pref{pref_code}/"
            try:
                resp = await client.get(url)
                jm_count = extract_total_count(resp.text) if resp.status_code == 200 else 0
            except Exception:
                jm_count = 0

            db_count = db_counts.get(pref_name, 0)
            rate = (db_count / jm_count * 100) if jm_count > 0 else 100

            if rate < threshold:
                gaps.append({
                    "pref_name": pref_name,
                    "pref_code": pref_code,
                    "jm_count": jm_count,
                    "db_count": db_count,
                    "rate": rate,
                    "missing": jm_count - db_count,
                })

            sys.stdout.write(f"\r  {pref_name}: JM={jm_count:,} DB={db_count:,} ({rate:.0f}%)")
            sys.stdout.flush()
            await asyncio.sleep(rate_limit)

    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()
    return gaps


async def collect_urls_for_prefecture(
    client: httpx.AsyncClient,
    job_code: str,
    pref_name: str,
    pref_code: str,
    rate_limit: float,
) -> list[str]:
    """1県の全ページからURLを収集"""
    first_url = build_page_url(job_code, pref_code, 1)
    try:
        resp = await client.get(first_url)
        if resp.status_code != 200:
            return []
        html = resp.text
    except Exception:
        return []

    total_count = extract_total_count(html)
    if total_count == 0:
        return []

    total_pages = math.ceil(total_count / ITEMS_PER_PAGE)
    all_urls = extract_urls_from_page(html, job_code)
    seen = set(all_urls)

    for page in range(2, total_pages + 1):
        await asyncio.sleep(rate_limit)
        page_url = build_page_url(job_code, pref_code, page)
        try:
            resp = await client.get(page_url)
            if resp.status_code == 200:
                page_urls = extract_urls_from_page(resp.text, job_code)
                for u in page_urls:
                    if u not in seen:
                        seen.add(u)
                        all_urls.append(u)
        except Exception:
            continue

        sys.stdout.write(f"\r    {pref_name}: page {page}/{total_pages} ({len(all_urls)} URLs)")
        sys.stdout.flush()

    sys.stdout.write(f"\r    {pref_name}: {len(all_urls)} URLs (全{total_pages}ページ完了)          \n")
    sys.stdout.flush()
    return all_urls


async def fill_gaps(job_type: str, threshold: float, rate_limit: float, dry_run: bool):
    """メイン処理: ギャップ県のURL収集→差分分析→missing CSV出力"""
    job_code = JOB_TYPE_CODES.get(job_type)
    if not job_code:
        print(f"不明な職種: {job_type}")
        return

    csv_name = job_type.replace("/", "・")

    # Step 1: ギャップ県の特定
    print(f"\n=== Step 1: ギャップ県特定 ({job_type}) ===")
    gaps = await identify_gaps(job_type, threshold, rate_limit)

    if not gaps:
        print("全県がカバレッジ閾値以上。補完不要。")
        return

    gaps.sort(key=lambda x: x["rate"])
    total_missing = sum(g["missing"] for g in gaps)
    est_pages = sum(math.ceil(g["jm_count"] / ITEMS_PER_PAGE) for g in gaps)
    est_time = est_pages * rate_limit

    print(f"\nカバレッジ{threshold}%未満: {len(gaps)}県, 推定不足 {total_missing:,}件")
    print(f"推定ページ数: {est_pages}, 推定時間: {est_time/60:.1f}分")
    print()
    for g in gaps:
        print(f"  {g['pref_name']}: JM {g['jm_count']:,} vs DB {g['db_count']:,} "
              f"({g['rate']:.0f}%, -{g['missing']:,}件)")

    if dry_run:
        print("\n[dry-run] URL収集はスキップ")
        return

    # Step 2: 既存URL読み込み
    print(f"\n=== Step 2: 既存URL読み込み ===")
    existing_urls = load_existing_urls(job_type)

    # Step 3: ギャップ県のURL収集
    print(f"\n=== Step 3: ギャップ県URL収集 ({len(gaps)}県) ===")
    newly_collected = {}

    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        },
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        for g in gaps:
            urls = await collect_urls_for_prefecture(
                client, job_code, g["pref_name"], g["pref_code"], rate_limit
            )
            newly_collected[g["pref_name"]] = urls
            await asyncio.sleep(rate_limit)

    # Step 4: 差分分析
    print(f"\n=== Step 4: 差分分析 ===")
    all_new_urls = []
    for pref_name, urls in newly_collected.items():
        new_urls = [u for u in urls if u not in existing_urls]
        all_new_urls.extend([(pref_name, u) for u in new_urls])
        found = len(urls)
        missing = len(new_urls)
        print(f"  {pref_name}: 収集{found:,} - 既存{found - missing:,} = 新規{missing:,}")

    print(f"\n新規URL合計: {len(all_new_urls):,}")

    if not all_new_urls:
        print("新規URLなし。既存URLカバレッジは十分です。")
        print("※ classifiedまたはDB投入段階での欠落の可能性があります。")
        return

    # Step 5: missing URLs CSV出力
    print(f"\n=== Step 5: missing URLs CSV出力 ===")
    today = datetime.now().strftime("%Y%m%d")
    out_path = SCRAPING_DIR / f"missing_urls_{csv_name}_{today}.csv"

    hh_name = job_type.replace("/", "・")
    rows = []
    for pref_name, url in all_new_urls:
        pref_code = int(PREFECTURE_CODES[pref_name])
        rows.append({
            "hh_code": job_code,
            "hh_name": hh_name,
            "pref_code": pref_code,
            "pref_name": pref_name,
            "page": 0,
            "URL": url,
        })

    df = pd.DataFrame(rows)
    columns = ["hh_code", "hh_name", "pref_code", "pref_name", "page", "URL"]
    df = df[columns]
    df.to_csv(out_path, index=False, encoding="utf-8-sig", lineterminator="\r\n")
    print(f"保存: {out_path}")
    print(f"  {len(rows):,} URLs ({len(newly_collected)}県)")

    # サマリー
    print(f"\n=== サマリー ===")
    print(f"  職種: {job_type}")
    print(f"  ギャップ県: {len(gaps)}県")
    print(f"  新規URL: {len(all_new_urls):,}")
    print(f"  出力: {out_path.name}")
    print(f"\n次のステップ:")
    print(f"  1. 詳細スクレイピング: scrape_jobmedley.py で {out_path.name} を入力")
    print(f"  2. 分類: classify_all_job_types.py で再分類")
    print(f"  3. DB再構築: build_geocoded_postings_db.py")


def main():
    parser = argparse.ArgumentParser(description="スクレイピングギャップ補完")
    parser.add_argument("--job-type", type=str, default="看護師/准看護師",
                       help="対象職種")
    parser.add_argument("--threshold", type=float, default=80.0,
                       help="カバレッジ閾値（%%、デフォルト80）")
    parser.add_argument("--rate-limit", type=float, default=1.5,
                       help="リクエスト間隔（秒）")
    parser.add_argument("--dry-run", action="store_true",
                       help="ギャップ特定のみ（URL収集しない）")
    args = parser.parse_args()

    asyncio.run(fill_gaps(
        job_type=args.job_type,
        threshold=args.threshold,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
