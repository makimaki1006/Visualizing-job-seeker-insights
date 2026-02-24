#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高速求人詳細スクレイパー（httpx版）

JobMedleyのHTMLに埋め込まれたJSON（jobOffer/customer/facility）を
httpxで取得し、既存details_outputフォーマットと互換のCSVを出力する。
Playwright不要で10-50倍高速。

使用例:
    # missing URLsを入力してスクレイピング
    python fast_detail_scraper.py --input missing_urls_看護師・准看護師_20260223.csv

    # 出力先を指定
    python fast_detail_scraper.py --input missing.csv --output new_details.csv

    # 並列度を指定（デフォルト5）
    python fast_detail_scraper.py --input missing.csv --concurrency 3
"""

import asyncio
import argparse
import csv
import json
import logging
import re
import sys
import time
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# 出力カラム（既存フォーマットと完全互換）
OUTPUT_COLUMNS = [
    "募集職種", "仕事内容", "診療科目・サービス形態",
    "給与", "給与_雇用形態", "給与_区分", "給与_範囲", "給与_下限", "給与_上限",
    "給与の備考", "想定年収",
    "待遇", "教育体制・研修", "勤務時間", "休日", "長期休暇・特別休暇",
    "応募要件",
    "法人・施設名", "アクセス", "施設・サービス形態",
    "営業時間", "休業日", "スタッフ構成", "設立年月日", "施設規模",
    "歓迎要件", "bottom_text",
]

SCRAPING_DIR = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング_2026_02_15"
)

# jobCategoryId → 職種名マッピング
JOB_CATEGORY_MAP = {
    1: "介護職/ヘルパー", 2: "歯科衛生士", 3: "看護師/准看護師",
    4: "保育士", 5: "薬剤師", 6: "ケアマネジャー",
    7: "生活相談員", 8: "理学療法士", 9: "作業療法士",
    10: "言語聴覚士", 11: "管理栄養士/栄養士", 12: "サービス提供責任者",
    13: "サービス管理責任者", 14: "児童指導員", 15: "児童発達支援管理責任者",
    16: "生活支援員", 17: "調理師/調理スタッフ", 18: "幼稚園教諭",
    19: "放課後児童支援員・学童指導員",
}


def _extract_json_object(html: str, key_pattern: str) -> dict | None:
    """HTML内のJSON objectをブレースマッチングで抽出

    key_pattern: '"jobOffer":' のような "キー": パターン
    """
    # パターン位置を検索（末尾の { は除去して検索）
    search_key = key_pattern.rstrip("{").rstrip()
    idx = html.find(search_key)
    if idx < 0:
        return None
    # キーの後の最初の { を見つける（idxから探して確実に捕捉）
    start = html.find("{", idx)
    if start < 0:
        return None

    depth = 0
    for i, ch in enumerate(html[start:start + 100000]):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(html[start : start + i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _parse_salary(salary_etc: str) -> dict:
    """salaryEtcから給与情報を解析"""
    result = {"雇用形態": "", "区分": "", "範囲": "", "下限": "", "上限": "", "想定年収": ""}

    if not salary_etc:
        return result

    # 雇用形態
    for emp in ["正社員", "パート・バイト", "契約社員", "派遣"]:
        if emp in salary_etc:
            result["雇用形態"] = emp
            break

    # 区分（月給/時給/年俸/日給）
    for kubun in ["月給", "時給", "年俸", "日給"]:
        if kubun in salary_etc:
            result["区分"] = kubun
            break

    # 金額範囲: "200,000円〜300,000円" or "200000〜300000"
    m = re.search(r"(\d[\d,]{2,7})\s*円?\s*[〜～~ー―\-]\s*(\d[\d,]{2,7})", salary_etc)
    if m:
        lo = m.group(1).replace(",", "")
        hi = m.group(2).replace(",", "")
        result["下限"] = lo
        result["上限"] = hi
        result["範囲"] = f"{lo}〜{hi}"
    else:
        # 単一金額
        m = re.search(r"(\d[\d,]{2,7})\s*円", salary_etc)
        if m:
            val = m.group(1).replace(",", "")
            result["下限"] = val
            result["上限"] = val
            result["範囲"] = val

    # 想定年収
    m = re.search(r"想定年収.*?(\d[\d,]{2,10})\s*円?\s*[〜～~\-]\s*(\d[\d,]{2,10})", salary_etc)
    if m:
        lo = m.group(1).replace(",", "")
        hi = m.group(2).replace(",", "")
        result["想定年収"] = f"{lo}〜{hi}"
    else:
        m = re.search(r"年収.*?(\d[\d,]{5,10})\s*円", salary_etc)
        if m:
            result["想定年収"] = m.group(1).replace(",", "")

    return result


def _find_jm_job_offer(html: str) -> dict | None:
    """HTML内の全 "jobOffer":{ を走査し、"type":"JMJobOffer" を持つものを返す"""
    idx = 0
    while True:
        idx = html.find('"jobOffer":{', idx)
        if idx < 0:
            break
        obj = _extract_json_object(html[idx:], '"jobOffer":{')
        if obj and obj.get("type") == "JMJobOffer":
            return obj
        idx += 1
    return None


def extract_detail(html: str) -> dict:
    """HTMLからjobOffer/customer/facility JSONを抽出してレコード化"""
    record = {col: "" for col in OUTPUT_COLUMNS}

    # jobOffer JSON（"type":"JMJobOffer"を含む正しいオブジェクトを取得）
    offer = _find_jm_job_offer(html)
    if not offer:
        return record

    # customer JSON
    customer = _extract_json_object(html, '"customer":{')
    # facility JSON
    facility = _extract_json_object(html, '"facility":{')

    # jobOfferからマッピング
    job_title = offer.get("jobTitle", "")
    if not job_title:
        # jobTitleが空の場合、jobCategoryIdから職種名を補完
        cat_id = offer.get("jobCategoryId")
        job_title = JOB_CATEGORY_MAP.get(cat_id, "")
    record["募集職種"] = job_title
    record["仕事内容"] = offer.get("jobContent", "")
    record["給与の備考"] = offer.get("salaryEtc", "")
    record["待遇"] = offer.get("welfarePrograms", "")
    record["教育体制・研修"] = offer.get("training", "")
    record["勤務時間"] = offer.get("officeHoursConditions", "")
    record["休日"] = offer.get("holiday", "")
    record["長期休暇・特別休暇"] = offer.get("specialHoliday", "")
    record["応募要件"] = offer.get("required", "")
    record["歓迎要件"] = offer.get("preferred", "")
    record["bottom_text"] = offer.get("appealBody", "")

    # 給与解析
    salary = _parse_salary(offer.get("salaryEtc", ""))
    record["給与"] = offer.get("salaryEtc", "")
    record["給与_雇用形態"] = salary["雇用形態"]
    record["給与_区分"] = salary["区分"]
    record["給与_範囲"] = salary["範囲"]
    record["給与_下限"] = salary["下限"]
    record["給与_上限"] = salary["上限"]
    record["想定年収"] = salary["想定年収"]

    # customerからマッピング
    if customer:
        record["法人・施設名"] = customer.get("name", "")

    # facilityからマッピング
    if facility:
        record["アクセス"] = facility.get("access", "")
        record["営業時間"] = facility.get("openTime", "")
        record["休業日"] = facility.get("holiday", "")
        record["スタッフ構成"] = facility.get("staffInfo", "")
        record["施設規模"] = ""
        # 施設規模: capacity, numberOfBeds から
        cap = facility.get("capacity")
        beds = facility.get("numberOfBeds")
        if beds:
            record["施設規模"] = f"病床数{beds}"
        elif cap:
            record["施設規模"] = f"定員{cap}"
        # 設立年月日
        year = facility.get("establishYear")
        month = facility.get("establishMonth")
        if year:
            record["設立年月日"] = f"{year}年{month}月" if month else f"{year}年"

    # 診療科目・サービス形態: facilityFormのサービスを探す
    # HTML内のserviceTypes/servicesを確認
    services_match = re.search(r'"services":\[(.*?)\]', html[:50000])
    if services_match:
        try:
            services = json.loads("[" + services_match.group(1) + "]")
            svc_names = [s.get("name", "") for s in services if isinstance(s, dict)]
            record["診療科目・サービス形態"] = "、".join(svc_names)
        except (json.JSONDecodeError, TypeError):
            pass

    return record


async def scrape_urls(
    urls: list[str],
    output_path: Path,
    concurrency: int = 5,
    rate_limit: float = 1.5,
):
    """URLリストを並列スクレイピングしてCSV出力"""
    total = len(urls)
    logger.info(f"対象URL: {total:,}件, 並列度: {concurrency}")

    results = []
    semaphore = asyncio.Semaphore(concurrency)
    completed = 0
    errors = 0
    start_time = time.time()

    async with httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
        },
        timeout=30.0,
        follow_redirects=True,
    ) as client:

        async def fetch_one(url: str) -> dict:
            nonlocal completed, errors
            async with semaphore:
                await asyncio.sleep(rate_limit)
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        record = extract_detail(resp.text)
                    else:
                        record = {col: "" for col in OUTPUT_COLUMNS}
                        errors += 1
                except Exception as e:
                    record = {col: "" for col in OUTPUT_COLUMNS}
                    errors += 1

                completed += 1
                if completed % 50 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (total - completed) / rate if rate > 0 else 0
                    sys.stdout.write(
                        f"\r  進捗: {completed:,}/{total:,} "
                        f"({completed/total*100:.0f}%) "
                        f"エラー: {errors} "
                        f"速度: {rate:.1f}件/秒 "
                        f"残り: {eta:.0f}秒"
                    )
                    sys.stdout.flush()

                return record

        tasks = [fetch_one(url) for url in urls]
        results = await asyncio.gather(*tasks)

    sys.stdout.write("\n")
    sys.stdout.flush()

    # CSV出力
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, lineterminator="\r\n")
        writer.writeheader()
        non_empty = 0
        for r in results:
            writer.writerow(r)
            # 仕事内容またはアクセスがあれば成功とみなす
            if r.get("仕事内容") or r.get("アクセス"):
                non_empty += 1

    elapsed = time.time() - start_time
    logger.info(f"完了: {total:,}件 → {non_empty:,}件取得成功 ({errors}件エラー)")
    logger.info(f"時間: {elapsed:.0f}秒 ({elapsed/60:.1f}分)")
    logger.info(f"出力: {output_path}")
    return non_empty


def merge_details(
    existing_csv: Path, new_csv: Path, output_csv: Path
):
    """既存details_outputと新規データをマージ"""
    import pandas as pd

    dfs = []
    if existing_csv.exists():
        df_old = pd.read_csv(existing_csv, encoding="utf-8-sig", encoding_errors="replace")
        dfs.append(df_old)
        logger.info(f"既存: {len(df_old):,}件 ({existing_csv.name})")

    if new_csv.exists():
        df_new = pd.read_csv(new_csv, encoding="utf-8-sig", encoding_errors="replace")
        dfs.append(df_new)
        logger.info(f"新規: {len(df_new):,}件 ({new_csv.name})")

    if not dfs:
        logger.warning("マージするデータがありません")
        return 0

    df_merged = pd.concat(dfs, ignore_index=True)
    # 重複除去（雇用形態が異なるレコードは別データとして保持）
    before = len(df_merged)
    dedup_cols = ["法人・施設名", "アクセス", "募集職種"]
    if "雇用形態" in df_merged.columns:
        dedup_cols.append("雇用形態")
    elif "employment_type" in df_merged.columns:
        dedup_cols.append("employment_type")
    df_merged = df_merged.drop_duplicates(subset=dedup_cols, keep="last")
    after = len(df_merged)
    if before != after:
        logger.info(f"重複除去: {before:,} → {after:,} ({before - after:,}件除去)")

    df_merged.to_csv(output_csv, index=False, encoding="utf-8-sig", lineterminator="\r\n")
    logger.info(f"マージ出力: {output_csv} ({after:,}件)")
    return after


async def main():
    parser = argparse.ArgumentParser(description="高速求人詳細スクレイパー")
    parser.add_argument("--input", type=str, required=True, help="入力URL CSV")
    parser.add_argument("--output", type=str, default=None, help="出力CSV")
    parser.add_argument("--concurrency", type=int, default=5, help="並列度")
    parser.add_argument("--rate-limit", type=float, default=1.5, help="リクエスト間隔（秒）")
    parser.add_argument("--merge-with", type=str, default=None,
                       help="マージ先の既存details_output CSV")
    parser.add_argument("--limit", type=int, default=0, help="処理件数制限（テスト用）")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        # SCRAPING_DIRからの相対パスを試す
        for d in [Path("."), SCRAPING_DIR, SCRAPING_DIR.parent / "ジョブメドレースクレイピング"]:
            if (d / args.input).exists():
                input_path = d / args.input
                break

    if not input_path.exists():
        logger.error(f"入力ファイルが見つかりません: {input_path}")
        return

    # URL読み込み
    import pandas as pd
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    urls = df["URL"].dropna().unique().tolist()
    urls = [u for u in urls if "ref_target=campaign" not in u]

    if args.limit > 0:
        urls = urls[:args.limit]

    logger.info(f"入力: {input_path.name} ({len(urls):,} URLs)")

    # 出力先
    if args.output:
        output_path = Path(args.output)
    else:
        stem = input_path.stem.replace("missing_urls_", "gap_details_")
        output_path = input_path.parent / f"{stem}.csv"

    # スクレイピング実行
    count = await scrape_urls(
        urls, output_path,
        concurrency=args.concurrency,
        rate_limit=args.rate_limit,
    )

    # マージ
    if args.merge_with:
        merge_path = Path(args.merge_with)
        merged_output = merge_path  # 上書き
        merge_details(merge_path, output_path, merged_output)


if __name__ == "__main__":
    asyncio.run(main())
