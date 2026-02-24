#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ジオコーディング準備スクリプト

classified CSVの最新版から住所を抽出し、
未ジオコード住所のリストをCSIS用に出力する。
"""

import csv
import glob
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CLASSIFIED_DIR = os.path.join(DATA_DIR, 'classified')
UNIQUE_PATH = os.path.join(DATA_DIR, 'unique_addresses_all.csv')
GEOCODED_PATH = os.path.join(DATA_DIR, 'geocoded_addresses_all.csv')
NEW_ADDR_PATH = os.path.join(DATA_DIR, 'new_addresses_for_geocoding.csv')

PREFS = [
    '北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県',
    '茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県',
    '新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県',
    '静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県',
    '奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県',
    '徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県',
    '熊本県','大分県','宮崎県','鹿児島県','沖縄県',
]


def normalize_address(addr):
    if not addr:
        return ''
    addr = addr.strip()
    addr = addr.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    addr = re.sub(r'\s+', ' ', addr)
    return addr


def extract_address(access_raw):
    """access列から都道府県名始まりの住所部分を抽出"""
    if not access_raw or not isinstance(access_raw, str):
        return None
    s = access_raw.strip()
    if not s:
        return None
    for pref in PREFS:
        idx = s.find(pref)
        if idx >= 0:
            return s[idx:]
    return None


def get_latest_classified():
    """各職種の最新日付classified CSVを取得"""
    pattern = re.compile(r'classified_(.+)_(\d{8})\.csv$')
    latest = {}
    for fpath in glob.glob(os.path.join(CLASSIFIED_DIR, 'classified_*_*.csv')):
        fname = os.path.basename(fpath)
        m = pattern.match(fname)
        if not m or 'sample' in fname:
            continue
        name, date = m.group(1), m.group(2)
        if name not in latest or date > latest[name][1]:
            latest[name] = (fpath, date)
    return latest


def extract_all_addresses(latest):
    """全classified CSVから住所を抽出"""
    all_addrs = set()
    total_rows = 0
    addr_found = 0

    for name, (fpath, date) in sorted(latest.items()):
        count = 0
        found = 0
        with open(fpath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                count += 1
                access = row.get('access', '')
                addr = extract_address(access)
                if addr:
                    norm = normalize_address(addr)
                    if norm:
                        all_addrs.add(norm)
                        found += 1
        total_rows += count
        addr_found += found
        pct = found / count * 100 if count > 0 else 0
        print(f"  {name} ({date}): {count:,}行, 住所{found:,} ({pct:.1f}%)")

    return all_addrs, total_rows, addr_found


def load_geocoded_addresses():
    """geocoded_addresses_all.csvからジオコード済み住所をデコード"""
    tail_pat = re.compile(rb',"([^"]+)","([^"]+)","([^"]+)","([^"]+)"\s*$')
    geocoded_addrs = set()
    geo_total = 0
    geo_success = 0
    decode_success = 0

    with open(GEOCODED_PATH, 'rb') as f:
        f.readline()  # skip header
        for line in f:
            if not line.strip():
                continue
            geo_total += 1
            m = tail_pat.search(line)
            if not m:
                continue
            try:
                conf = int(m.group(3))
                if conf <= 0:
                    continue
                geo_success += 1
            except (ValueError, TypeError):
                continue

            # address部分をISO-2022-JPデコード
            comma_pos = line.index(b',')
            rest = line[comma_pos + 1:]
            # LocName以降を除去
            loc_match = re.search(rb',"[^"]*","[^"]*","[^"]*","[^"]*"\s*$', rest)
            if loc_match:
                addr_part = rest[:loc_match.start()]
                try:
                    decoded = addr_part.decode('iso-2022-jp').strip().strip('"')
                    norm = normalize_address(decoded)
                    if norm:
                        geocoded_addrs.add(norm)
                        decode_success += 1
                except (UnicodeDecodeError, LookupError):
                    pass

    print(f"  geocoded総行数: {geo_total:,}")
    print(f"  ジオコード成功(conf>0): {geo_success:,}")
    print(f"  住所デコード成功: {decode_success:,}")
    return geocoded_addrs


def main():
    start = time.time()

    # Step 1
    print("=" * 60)
    print("[Step 1/5] 最新classified CSV特定")
    latest = get_latest_classified()
    print(f"  対象職種: {len(latest)}種")

    # Step 2
    print(f"\n[Step 2/5] 住所抽出")
    all_addrs, total_rows, addr_found = extract_all_addresses(latest)
    print(f"\n  合計: {total_rows:,}行, 住所: {addr_found:,} ({addr_found/total_rows*100:.1f}%)")
    print(f"  ユニーク住所: {len(all_addrs):,}")

    # Step 3
    print(f"\n[Step 3/5] unique_addresses_all.csv 再生成")
    sorted_addrs = sorted(all_addrs)
    with open(UNIQUE_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'address'])
        for i, addr in enumerate(sorted_addrs, 1):
            writer.writerow([i, addr])
    print(f"  -> {len(sorted_addrs):,}件 保存")

    # Step 4
    print(f"\n[Step 4/5] 既存geocoded差分抽出")
    geocoded_addrs = load_geocoded_addresses()
    already = all_addrs & geocoded_addrs
    new_addrs = all_addrs - geocoded_addrs
    print(f"  ジオコード済み: {len(already):,} ({len(already)/len(all_addrs)*100:.1f}%)")
    print(f"  未ジオコード: {len(new_addrs):,}")

    # Step 5
    print(f"\n[Step 5/5] CSIS用CSV出力")
    sorted_new = sorted(new_addrs)
    with open(NEW_ADDR_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'address'])
        for i, addr in enumerate(sorted_new, 1):
            writer.writerow([i, addr])
    print(f"  -> {len(sorted_new):,}件 保存: {NEW_ADDR_PATH}")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"完了 ({elapsed:.1f}秒)")
    print(f"{'='*60}")
    print(f"  classified合計:      {total_rows:,}行")
    print(f"  ユニーク住所:        {len(all_addrs):,}")
    print(f"  ジオコード済み:      {len(already):,} ({len(already)/len(all_addrs)*100:.1f}%)")
    print(f"  CSIS要アップロード:  {len(sorted_new):,}")
    print(f"\n  出力ファイル:")
    print(f"    unique:  {UNIQUE_PATH}")
    print(f"    新規:    {NEW_ADDR_PATH}")


if __name__ == '__main__':
    main()
