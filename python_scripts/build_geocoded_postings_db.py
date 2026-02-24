"""
geocoded_postings.db 生成スクリプト

classified_*.csv (72カラム) + geocoded_addresses_all.csv
→ SQLite DB (geocoded_postings.db)

処理:
1. geocoded_addresses_all.csv からアドレスを直接デコード → address → (lat, lng) マッピング作成
2. classified CSV を読み込み、access列でジオコード情報を直接マッチング
3. SQLite に投入

注: IDチェーン(unique_addresses_all.csv)に依存しない方式。
    ISO-2022-JPアドレスを直接デコードしてマッチングする。
"""

import csv
import gzip
import glob
import os
import re
import shutil
import sqlite3
import sys
import time

# 有効な47都道府県
VALID_PREFECTURES = {
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
}

# classified CSV の最新日付のファイルを使用
CLASSIFIED_DIR = os.path.join(os.path.dirname(__file__), "data", "classified")
GEOCODED_PATH = os.path.join(os.path.dirname(__file__), "data", "geocoded_addresses_all.csv")

# 出力先
RUST_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "rust_dashboard", "data")
DB_PATH = os.path.join(RUST_DATA_DIR, "geocoded_postings.db")
GZ_PATH = DB_PATH + ".gz"

# 職種マッピング（classified CSV のファイル名 → DB用 job_type）
JOB_TYPE_MAPPING = {
    "看護師・准看護師": "看護師",
    "介護職・ヘルパー": "介護職",
    "保育士": "保育士",
    "管理栄養士・栄養士": "栄養士",
    "生活相談員": "生活相談員",
    "理学療法士": "理学療法士",
    "作業療法士": "作業療法士",
    "ケアマネジャー": "ケアマネジャー",
    "サービス管理責任者": "サービス管理責任者",
    "サービス提供責任者": "サービス提供責任者",
    "放課後児童支援員・学童指導員": "学童支援",
    "調理師・調理スタッフ": "調理師、調理スタッフ",
    "薬剤師": "薬剤師",
    "言語聴覚士": "言語聴覚士",
    "児童指導員": "児童指導員",
    "児童発達支援管理責任者": "児童発達支援管理責任者",
    "生活支援員": "生活支援員",
    "幼稚園教諭": "幼稚園教諭",
}

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,
    prefecture TEXT NOT NULL,
    municipality TEXT NOT NULL,
    facility_name TEXT,
    service_type TEXT,
    employment_type TEXT,
    salary_type TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_detail TEXT,
    headline TEXT,
    job_description TEXT,
    requirements TEXT,
    benefits TEXT,
    working_hours TEXT,
    holidays TEXT,
    education_training TEXT,
    access TEXT,
    special_holidays TEXT,
    tags TEXT,
    tier3_label_short TEXT,
    exp_qual_segment TEXT,
    hol_pattern TEXT,
    wh_shift_type TEXT,
    lat REAL,
    lng REAL,
    geocode_confidence INTEGER,
    geocode_level INTEGER
);
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_postings_job_pref ON postings(job_type, prefecture);",
    "CREATE INDEX IF NOT EXISTS idx_postings_coords ON postings(lat, lng);",
    "CREATE INDEX IF NOT EXISTS idx_postings_job_pref_muni ON postings(job_type, prefecture, municipality);",
]

INSERT_SQL = """
INSERT INTO postings (
    job_type, prefecture, municipality, facility_name, service_type,
    employment_type, salary_type, salary_min, salary_max, salary_detail,
    headline, job_description, requirements, benefits, working_hours,
    holidays, education_training, access, special_holidays, tags,
    tier3_label_short, exp_qual_segment, hol_pattern, wh_shift_type,
    lat, lng, geocode_confidence, geocode_level
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def safe_int(val, default=0):
    """文字列を安全にintに変換"""
    if not val or val == "":
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def normalize_address(addr):
    """住所の正規化（マッチング用）: 全角→半角数字、空白統一"""
    if not addr:
        return ""
    addr = addr.strip()
    # 全角数字→半角
    addr = addr.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    # 連続空白→1つ
    addr = re.sub(r"\s+", " ", addr)
    return addr


def build_address_to_geocode_map(geocoded_path):
    """geocoded_addresses_all.csv から address → (lat, lng, conf, level) の辞書を作成

    ISO-2022-JPエンコードされたアドレスを直接デコードしてマッチングする。
    IDチェーンに依存しないため、unique_addresses_all.csv の再生成で壊れない。

    行末の5フィールド(LocName,fX,fY,iConf,iLvl)は常にクォート済みなので、
    正規表現で行末から抽出し、残りをアドレスとしてデコードする。
    """
    print(f"  読み込み: {geocoded_path}")
    addr_to_geo = {}
    errors = 0
    # 末尾5フィールド: ,"LocName","fX","fY","iConf","iLvl"
    tail5_pattern = re.compile(
        rb',"[^"]*","([^"]+)","([^"]+)","([^"]+)","([^"]+)"\s*$'
    )

    with open(geocoded_path, "rb") as f:
        f.readline()  # ヘッダスキップ
        for line in f:
            if not line.strip():
                continue
            # 行末から5フィールド抽出
            m = tail5_pattern.search(line)
            if not m:
                errors += 1
                continue
            try:
                fx = float(m.group(1))   # 経度
                fy = float(m.group(2))   # 緯度
                conf = int(m.group(3))
                lvl = int(m.group(4))
            except (ValueError, TypeError):
                errors += 1
                continue
            if conf <= 0 or fx == 0 or fy == 0:
                continue

            # アドレス部分 = 最初のカンマ後 ～ 末尾5フィールド前
            comma_pos = line.index(b",")
            addr_bytes = line[comma_pos + 1:m.start()].strip(b'"')
            try:
                addr = addr_bytes.decode("iso-2022-jp").strip().strip('"')
                norm = normalize_address(addr)
                if norm:
                    # 複数エントリがある場合、高いconfidenceを優先
                    existing = addr_to_geo.get(norm)
                    if existing is None or conf > existing[2]:
                        addr_to_geo[norm] = (fy, fx, conf, lvl)  # lat=fY, lng=fX
            except (UnicodeDecodeError, LookupError):
                errors += 1

    print(f"  → {len(addr_to_geo):,} 件のアドレス→座標マッピング（conf > 0）")
    if errors > 0:
        print(f"  [注意] {errors:,} 件のパース/デコードエラー（スキップ）")
    return addr_to_geo


def get_latest_classified_files(classified_dir):
    """各職種の最新日付のclassified CSVを取得"""
    all_files = glob.glob(os.path.join(classified_dir, "classified_*_*.csv"))
    latest = {}
    pattern = re.compile(r"classified_(.+)_(\d{8})\.csv$")
    for fpath in all_files:
        fname = os.path.basename(fpath)
        m = pattern.match(fname)
        if not m:
            continue
        job_name = m.group(1)
        date_str = m.group(2)
        # sampleファイルは除外
        if "sample" in job_name:
            continue
        if job_name not in latest or date_str > latest[job_name][1]:
            latest[job_name] = (fpath, date_str)
    return {k: v[0] for k, v in latest.items()}


def process_classified_files(classified_files, addr_to_geo, conn):
    """classified CSV を処理してDBに投入"""
    cursor = conn.cursor()
    total_inserted = 0
    total_skipped_no_coord = 0
    total_skipped_bad_pref = 0
    total_rows = 0

    for job_name, fpath in sorted(classified_files.items()):
        if job_name not in JOB_TYPE_MAPPING:
            print(f"\n  スキップ: {job_name}（マッピング対象外）")
            continue
        db_job_type = JOB_TYPE_MAPPING[job_name]
        print(f"\n  処理中: {job_name} → {db_job_type}")
        print(f"    ファイル: {os.path.basename(fpath)}")

        rows_inserted = 0
        rows_skipped = 0
        rows_bad_pref = 0
        batch = []

        with open(fpath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                access = row.get("access", "")
                norm_addr = normalize_address(access)

                # アドレス直接マッチング（IDチェーン不要）
                lat, lng, conf, lvl = None, None, None, None
                if norm_addr:
                    geo = addr_to_geo.get(norm_addr)
                    if geo:
                        lat, lng, conf, lvl = geo

                if lat is None:
                    rows_skipped += 1
                    total_skipped_no_coord += 1
                    continue

                # 都道府県バリデーション（gapデータのパース不良を除外）
                prefecture = row.get("prefecture", "")
                if prefecture not in VALID_PREFECTURES:
                    rows_bad_pref += 1
                    total_skipped_bad_pref += 1
                    continue

                batch.append((
                    db_job_type,
                    prefecture,
                    row.get("municipality", ""),
                    row.get("facility_name", ""),
                    row.get("service_type", ""),
                    row.get("employment_type", ""),
                    row.get("salary_type", ""),
                    safe_int(row.get("salary_min")),
                    safe_int(row.get("salary_max")),
                    row.get("salary_detail", ""),
                    row.get("headline", ""),
                    row.get("job_description", "")[:500] if row.get("job_description") else "",
                    row.get("requirements", ""),
                    row.get("benefits", "")[:300] if row.get("benefits") else "",
                    row.get("working_hours", ""),
                    row.get("holidays", ""),
                    row.get("education_training", ""),
                    access,
                    row.get("special_holidays", ""),
                    row.get("tags", ""),
                    row.get("tier3_label_short", ""),
                    row.get("exp_qual_segment", ""),
                    row.get("hol_pattern", ""),
                    row.get("wh_shift_type", ""),
                    lat,
                    lng,
                    conf,
                    lvl,
                ))
                rows_inserted += 1

                if len(batch) >= 5000:
                    cursor.executemany(INSERT_SQL, batch)
                    batch.clear()

        if batch:
            cursor.executemany(INSERT_SQL, batch)
        conn.commit()

        total_inserted += rows_inserted
        skip_parts = [f"座標なし: {rows_skipped:,}"]
        if rows_bad_pref > 0:
            skip_parts.append(f"都道府県不正: {rows_bad_pref:,}")
        print(f"    → 投入: {rows_inserted:,} 件, スキップ({', '.join(skip_parts)})")

    return total_inserted, total_skipped_no_coord, total_skipped_bad_pref, total_rows


def compress_db(db_path, gz_path):
    """DBをgzip圧縮"""
    print(f"\n  gzip圧縮: {db_path} → {gz_path}")
    with open(db_path, "rb") as f_in:
        with gzip.open(gz_path, "wb", compresslevel=6) as f_out:
            shutil.copyfileobj(f_in, f_out)
    orig_size = os.path.getsize(db_path)
    gz_size = os.path.getsize(gz_path)
    ratio = gz_size / orig_size * 100
    print(f"  → 元: {orig_size / 1024 / 1024:.1f} MB → 圧縮: {gz_size / 1024 / 1024:.1f} MB ({ratio:.1f}%)")


def main():
    start_time = time.time()
    print("=" * 60)
    print("geocoded_postings.db 生成スクリプト")
    print("=" * 60)

    # 出力ディレクトリ確認
    os.makedirs(RUST_DATA_DIR, exist_ok=True)

    # Step 1: address → geocode マッピング（IDチェーン不要、アドレス直接マッチング）
    print("\n[Step 1/3] アドレス→座標マッピング構築")
    addr_to_geo = build_address_to_geocode_map(GEOCODED_PATH)

    # Step 2: classified CSV → DB
    print("\n[Step 2/3] classified CSV 読み込み → DB投入")
    classified_files = get_latest_classified_files(CLASSIFIED_DIR)
    print(f"  対象職種: {len(classified_files)} 種")
    for name in sorted(classified_files.keys()):
        print(f"    - {name}: {os.path.basename(classified_files[name])}")

    # DB作成
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()

    total_inserted, total_skipped, total_bad_pref, total_rows = process_classified_files(
        classified_files, addr_to_geo, conn
    )

    # インデックス作成
    print("\n  インデックス作成中...")
    for sql in CREATE_INDEX_SQL:
        conn.execute(sql)
    conn.commit()
    conn.close()

    # Step 3: gzip圧縮
    print("\n[Step 3/3] gzip圧縮")
    compress_db(DB_PATH, GZ_PATH)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("完了サマリー")
    print("=" * 60)
    print(f"  総CSV行数:       {total_rows:,}")
    print(f"  DB投入行数:       {total_inserted:,}")
    print(f"  座標なしスキップ: {total_skipped:,}")
    print(f"  都道府県不正スキップ: {total_bad_pref:,}")
    print(f"  座標カバー率:     {total_inserted / total_rows * 100:.1f}%" if total_rows > 0 else "  N/A")
    print(f"  DB ファイル:      {DB_PATH}")
    print(f"  GZ ファイル:      {GZ_PATH}")
    print(f"  処理時間:         {elapsed:.1f} 秒")


if __name__ == "__main__":
    main()
