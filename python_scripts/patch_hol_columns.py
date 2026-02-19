#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存classified CSVにhol_*カラムをパッチ追加するスクリプト

parse_holidays()を適用してhol_pattern, hol_weekday_off, hol_specialを追加する。
"""

import sys
import time
from pathlib import Path

import pandas as pd

# parse_holidays を再利用
sys.path.insert(0, str(Path(__file__).parent))
from job_medley_analyzer import parse_holidays

CLASSIFIED_DIR = Path(__file__).parent / "data" / "classified"


def patch_csv(csv_path: Path) -> int:
    """1つのCSVにhol_*カラムを追加"""
    t0 = time.time()
    print(f"  {csv_path.name} ...", end="", flush=True)

    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)

    # 既にhol_patternがあればスキップ
    if "hol_pattern" in df.columns:
        print(f" スキップ（既存）")
        return 0

    # holidays列がなければ空カラムだけ追加
    if "holidays" not in df.columns:
        df["hol_pattern"] = ""
        df["hol_weekday_off"] = ""
        df["hol_special"] = ""
    else:
        results = df["holidays"].apply(parse_holidays)
        df["hol_pattern"] = results.apply(lambda x: x["hol_pattern"])
        df["hol_weekday_off"] = results.apply(lambda x: x["hol_weekday_off"])
        df["hol_special"] = results.apply(lambda x: x["hol_special"])

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    elapsed = time.time() - t0
    print(f" {len(df):,}行 ({elapsed:.1f}s)")
    return len(df)


def main():
    csvs = sorted(CLASSIFIED_DIR.glob("classified_*_20260217.csv"))
    if not csvs:
        print("[ERROR] classified CSVが見つかりません")
        sys.exit(1)

    print(f"対象: {len(csvs)}ファイル")
    total = 0
    t_total = time.time()

    for csv_path in csvs:
        total += patch_csv(csv_path)

    print(f"\n完了: {total:,}行, {time.time() - t_total:.1f}s")


if __name__ == "__main__":
    main()
