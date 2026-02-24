#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全パイプライン自動実行スクリプト

全職種のギャップ補完 → 詳細スクレイピング → マージ → 分類 → DB再構築

使用例:
    # 全DASHBOARD職種の実行
    python run_full_pipeline.py

    # 特定職種のみ
    python run_full_pipeline.py --job-type "看護師/准看護師"

    # ギャップ収集+スクレイピングのみ（分類・DB構築はスキップ）
    python run_full_pipeline.py --scrape-only

    # 分類+DB構築のみ（スクレイピング済み前提）
    python run_full_pipeline.py --build-only
"""

import asyncio
import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
SCRAPING_DIR = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング"
)
SCRAPING_DIR_FEB = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング_2026_02_15"
)

# 全DASHBOARD職種
DASHBOARD_JOB_TYPES_WITH_CODES = {
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
}

CSV_NAME_MAP = {
    "看護師/准看護師": "看護師・准看護師",
    "介護職/ヘルパー": "介護職・ヘルパー",
    "管理栄養士/栄養士": "管理栄養士・栄養士",
    "調理師/調理スタッフ": "調理師・調理スタッフ",
    "放課後児童支援員・学童指導員": "放課後児童支援員・学童指導員",
}

TODAY = datetime.now().strftime("%Y%m%d")


def step_header(step_num: int, total: int, title: str):
    print(f"\n{'='*60}")
    print(f"  Step {step_num}/{total}: {title}")
    print(f"{'='*60}\n")


async def step1_collect_gap_urls(job_types: list[str], threshold: float):
    """全職種のギャップURLを収集"""
    results = {}
    for jt in job_types:
        csv_name = CSV_NAME_MAP.get(jt, jt.replace("/", "・"))
        missing_csv = SCRAPING_DIR / f"missing_urls_{csv_name}_{TODAY}.csv"

        if missing_csv.exists():
            df = pd.read_csv(missing_csv, encoding="utf-8-sig")
            logger.info(f"[スキップ] {jt}: 既存 {len(df):,} URLs")
            results[jt] = len(df)
            continue

        logger.info(f"[収集開始] {jt}")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(SCRIPT_DIR / "fill_scraping_gaps.py"),
            "--job-type", jt,
            "--threshold", str(threshold),
            "--rate-limit", "1.5",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")

        if missing_csv.exists():
            df = pd.read_csv(missing_csv, encoding="utf-8-sig")
            results[jt] = len(df)
            logger.info(f"[完了] {jt}: {len(df):,} missing URLs")
        else:
            results[jt] = 0
            # ギャップなしの場合は正常
            if "補完不要" in output or "全県がカバレッジ" in output:
                logger.info(f"[完了] {jt}: ギャップなし（全県カバレッジOK）")
            else:
                logger.warning(f"[注意] {jt}: 出力ファイルなし")

    return results


async def step2_scrape_details(job_types: list[str]):
    """missing URLsの詳細をスクレイピング"""
    results = {}
    for jt in job_types:
        csv_name = CSV_NAME_MAP.get(jt, jt.replace("/", "・"))
        missing_csv = SCRAPING_DIR / f"missing_urls_{csv_name}_{TODAY}.csv"
        gap_details_csv = SCRAPING_DIR / f"gap_details_{csv_name}_{TODAY}.csv"

        if not missing_csv.exists():
            results[jt] = 0
            continue

        if gap_details_csv.exists():
            df = pd.read_csv(gap_details_csv, encoding="utf-8-sig")
            logger.info(f"[スキップ] {jt}: 既存 {len(df):,}件")
            results[jt] = len(df)
            continue

        df_urls = pd.read_csv(missing_csv, encoding="utf-8-sig")
        url_count = len(df_urls)
        est_time = url_count * 1.5 / 5 / 60  # 5並列、1.5秒間隔
        logger.info(f"[スクレイピング開始] {jt}: {url_count:,} URLs（推定{est_time:.1f}分）")

        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(SCRIPT_DIR / "fast_detail_scraper.py"),
            "--input", str(missing_csv),
            "--output", str(gap_details_csv),
            "--concurrency", "5",
            "--rate-limit", "1.5",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if gap_details_csv.exists():
            df = pd.read_csv(gap_details_csv, encoding="utf-8-sig")
            results[jt] = len(df)
            logger.info(f"[完了] {jt}: {len(df):,}件")
        else:
            results[jt] = 0
            logger.warning(f"[失敗] {jt}")

    return results


def step3_merge_details(job_types: list[str]):
    """gap_detailsを既存details_outputにマージ"""
    for jt in job_types:
        csv_name = CSV_NAME_MAP.get(jt, jt.replace("/", "・"))
        gap_csv = SCRAPING_DIR / f"gap_details_{csv_name}_{TODAY}.csv"

        if not gap_csv.exists():
            continue

        # 既存details_output（2月版優先）
        existing_csv = SCRAPING_DIR_FEB / f"job_urls_{csv_name}_details_output.csv"
        if not existing_csv.exists():
            existing_csv = SCRAPING_DIR / f"job_urls_{csv_name}_details_output.csv"

        if not existing_csv.exists():
            logger.warning(f"[スキップ] {jt}: 既存details_output不在、gap_detailsのみ使用")
            # gap_detailsをdetails_outputとしてコピー
            gap_csv.rename(SCRAPING_DIR_FEB / f"job_urls_{csv_name}_details_output.csv")
            continue

        logger.info(f"[マージ] {jt}")
        df_old = pd.read_csv(existing_csv, encoding="utf-8-sig", encoding_errors="replace")
        df_new = pd.read_csv(gap_csv, encoding="utf-8-sig", encoding_errors="replace")

        df_merged = pd.concat([df_old, df_new], ignore_index=True)
        before = len(df_merged)
        # 雇用形態（正社員/パート/バイト等）が異なるレコードは別データとして保持
        dedup_cols = ["法人・施設名", "アクセス", "募集職種"]
        if "雇用形態" in df_merged.columns:
            dedup_cols.append("雇用形態")
        elif "employment_type" in df_merged.columns:
            dedup_cols.append("employment_type")
        df_merged = df_merged.drop_duplicates(subset=dedup_cols, keep="last")
        after = len(df_merged)

        df_merged.to_csv(existing_csv, index=False, encoding="utf-8-sig", lineterminator="\r\n")
        logger.info(f"  {len(df_old):,} + {len(df_new):,} → {after:,}件 (重複{before-after:,}件除去)")


def step4_classify():
    """classify_all_job_types.py 実行"""
    logger.info("分類パイプライン実行中...")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "classify_all_job_types.py"),
         "--output_dir", str(SCRIPT_DIR / "data" / "classified")],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR),
    )
    if proc.returncode == 0:
        logger.info("分類完了")
        # 結果概要
        classified_dir = SCRIPT_DIR / "data" / "classified"
        for f in sorted(classified_dir.glob("classified_*.csv")):
            try:
                df = pd.read_csv(f, encoding="utf-8-sig", nrows=0)
                # 行数をバイナリでカウント（高速）
                with open(f, "rb") as fh:
                    lines = sum(1 for _ in fh) - 1
                logger.info(f"  {f.name}: ~{lines:,}行")
            except Exception:
                pass
    else:
        logger.error(f"分類エラー: {proc.stderr[:500]}")
    return proc.returncode == 0


def step5_build_db():
    """build_geocoded_postings_db.py 実行"""
    logger.info("DB構築中...")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "emergency_rebuild_db.py"), "--rebuild"],
        capture_output=True, text=True, cwd=str(SCRIPT_DIR),
    )
    if proc.returncode == 0:
        logger.info("DB構築完了")
        # DB統計
        db_path = SCRIPT_DIR.parent / "rust_dashboard" / "data" / "geocoded_postings.db"
        if db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            total = conn.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
            types = conn.execute(
                "SELECT job_type, COUNT(*) FROM postings GROUP BY job_type ORDER BY COUNT(*) DESC"
            ).fetchall()
            conn.close()
            logger.info(f"  合計: {total:,}件, {len(types)}職種")
            for jt, cnt in types:
                logger.info(f"    {jt}: {cnt:,}")
    else:
        logger.error(f"DB構築エラー: {proc.stderr[:500]}")
    return proc.returncode == 0


async def main():
    parser = argparse.ArgumentParser(description="全パイプライン自動実行")
    parser.add_argument("--job-type", type=str, default=None)
    parser.add_argument("--threshold", type=float, default=80.0)
    parser.add_argument("--scrape-only", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()

    start_time = time.time()

    if args.job_type:
        job_types = [args.job_type]
    else:
        job_types = list(DASHBOARD_JOB_TYPES_WITH_CODES.keys())

    total_steps = 5
    if args.scrape_only:
        total_steps = 3
    elif args.build_only:
        total_steps = 2

    print(f"\n{'#'*60}")
    print(f"  全パイプライン実行 ({len(job_types)}職種)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    if not args.build_only:
        step_header(1, total_steps, "ギャップURL収集")
        gap_results = await step1_collect_gap_urls(job_types, args.threshold)
        total_missing = sum(gap_results.values())
        types_with_gap = sum(1 for v in gap_results.values() if v > 0)
        print(f"\n合計: {total_missing:,} missing URLs ({types_with_gap}職種にギャップ)")

        step_header(2, total_steps, "詳細スクレイピング（httpx高速版）")
        scrape_results = await step2_scrape_details(job_types)
        total_scraped = sum(scrape_results.values())
        print(f"\n合計: {total_scraped:,}件スクレイピング完了")

        step_header(3, total_steps, "details_outputマージ")
        step3_merge_details(job_types)

    if not args.scrape_only:
        step_num = 1 if args.build_only else 4
        step_header(step_num, total_steps, "セグメント分類")
        step4_classify()

        step_num = 2 if args.build_only else 5
        step_header(step_num, total_steps, "DB再構築")
        step5_build_db()

    elapsed = time.time() - start_time
    print(f"\n{'#'*60}")
    print(f"  全パイプライン完了 ({elapsed/60:.1f}分)")
    print(f"{'#'*60}")


if __name__ == "__main__":
    asyncio.run(main())
