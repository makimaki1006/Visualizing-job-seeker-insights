#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobMedley掲載数 vs DB収録数 比較検証

各都道府県の検索結果ページ1を取得し、「X件の求人」から総件数を抽出。
DB収録数と比較してカバレッジを算出する。

使用例:
    python verify_coverage.py --job-type "看護師/准看護師"
    python verify_coverage.py --job-type "サービス管理責任者"
    python verify_coverage.py --all-anomaly
"""

import asyncio
import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path

import httpx

# 設定
BASE_URL = "https://job-medley.com"

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

# DB職種名マッピング（classified名 → DB名）
DB_NAME_MAP = {
    "看護師/准看護師": "看護師",
    "介護職/ヘルパー": "介護職",
    "管理栄養士/栄養士": "栄養士",
    "調理師/調理スタッフ": "調理師、調理スタッフ",
    "放課後児童支援員・学童指導員": "学童支援",
}

DB_PATH = Path(__file__).parent.parent / "rust_dashboard" / "data" / "geocoded_postings.db"


def extract_total_count(html: str) -> int:
    """検索結果HTMLから総件数を抽出"""
    # パターン1: React Queryキャッシュ内の "total":XXXX
    match = re.search(r'"total"\s*:\s*(\d+)', html)
    if match:
        return int(match.group(1))
    # パターン2: "X件の求人" テキスト
    match = re.search(r'([\d,]+)\s*件', html)
    if match:
        return int(match.group(1).replace(',', ''))
    return 0


def get_db_counts(job_type: str) -> dict[str, int]:
    """DB内の都道府県別件数を取得"""
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


async def check_coverage(job_type: str, rate_limit: float = 1.5):
    """1職種の全都道府県カバレッジを検証"""
    job_code = JOB_TYPE_CODES.get(job_type)
    if not job_code:
        print(f"不明な職種: {job_type}")
        return None

    db_counts = get_db_counts(job_type)
    db_name = DB_NAME_MAP.get(job_type, job_type)

    results = []
    total_jm = 0
    total_db = 0

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
        for pref_name, pref_code in PREFECTURE_CODES.items():
            url = f"{BASE_URL}/{job_code}/pref{pref_code}/"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    jm_count = extract_total_count(resp.text)
                else:
                    jm_count = -1
            except Exception as e:
                jm_count = -1

            db_count = db_counts.get(pref_name, 0)
            total_jm += max(jm_count, 0)
            total_db += db_count

            results.append({
                "pref": pref_name,
                "jm": jm_count,
                "db": db_count,
            })

            # 進捗表示（同一行上書き）
            sys.stdout.write(f"\r  {pref_name} ... {jm_count:,}件")
            sys.stdout.flush()

            await asyncio.sleep(rate_limit)

    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()

    # 結果表示
    print(f"\n=== {job_type} ({db_name}) カバレッジ検証 ===")
    print(f"{'県':>8} {'JM掲載':>8} {'DB収録':>8} {'カバー率':>8} {'判定':>6}")
    print("-" * 45)

    gaps = []
    for r in results:
        jm = r["jm"]
        db = r["db"]
        if jm > 0:
            rate = db / jm * 100
            if rate < 50:
                judge = "⚠低"
            elif rate < 80:
                judge = "△"
            else:
                judge = ""
        elif jm == 0:
            rate = 0
            judge = "JM=0"
        else:
            rate = -1
            judge = "ERR"

        print(f"{r['pref']:>8} {jm:>8,} {db:>8,} {rate:>7.1f}% {judge}")

        if jm > 0 and rate < 80:
            gaps.append(r)

    print("-" * 45)
    overall_rate = (total_db / total_jm * 100) if total_jm > 0 else 0
    print(f"{'合計':>8} {total_jm:>8,} {total_db:>8,} {overall_rate:>7.1f}%")

    if gaps:
        print(f"\n⚠ カバー率80%未満の県: {len(gaps)}県")
        for g in sorted(gaps, key=lambda x: x["db"] / max(x["jm"], 1)):
            rate = g["db"] / g["jm"] * 100
            diff = g["jm"] - g["db"]
            print(f"  {g['pref']}: JM {g['jm']:,} vs DB {g['db']:,} ({rate:.0f}%, -{diff:,}件不足)")

    return {
        "job_type": job_type,
        "total_jm": total_jm,
        "total_db": total_db,
        "rate": overall_rate,
        "gap_count": len(gaps),
        "gaps": gaps,
    }


async def main():
    parser = argparse.ArgumentParser(description="JobMedley掲載数 vs DB収録数 検証")
    parser.add_argument("--job-type", type=str, default="看護師/准看護師",
                       help="検証する職種（config.pyの名前）")
    parser.add_argument("--rate-limit", type=float, default=1.5,
                       help="リクエスト間隔（秒）")
    parser.add_argument("--all-anomaly", action="store_true",
                       help="異常検出された主要職種を全て検証")
    args = parser.parse_args()

    if args.all_anomaly:
        # 人口比で異常が多かった職種
        targets = [
            "看護師/准看護師",
            "サービス管理責任者",
            "サービス提供責任者",
            "児童指導員",
        ]
    else:
        targets = [args.job_type]

    all_results = []
    for jt in targets:
        result = await check_coverage(jt, rate_limit=args.rate_limit)
        if result:
            all_results.append(result)
        if len(targets) > 1:
            print()

    if len(all_results) > 1:
        print("\n=== 全体サマリー ===")
        for r in all_results:
            print(f"  {r['job_type']}: JM {r['total_jm']:,} vs DB {r['total_db']:,} "
                  f"({r['rate']:.1f}%, {r['gap_count']}県に欠落)")


if __name__ == "__main__":
    asyncio.run(main())
