"""
Layer A: 量的構造分析（市場のものさし）
========================================
A-1: 給与分布（べき乗分布 / パレート分析）
A-2: 法人求人集中度（ジップの法則）
A-3: 雇用形態多様性（シャノンエントロピー）

出力テーブル:
  - layer_a_salary_stats         (A-1)
  - layer_a_facility_concentration (A-2)
  - layer_a_employment_diversity   (A-3)
"""

import sqlite3
import math
import json
import time
import sys
from collections import Counter
from typing import Optional

import numpy as np
from scipy import stats

DB_PATH = r"C:/Users/fuji1/AppData/Local/Temp/rust-dashboard-deploy/data/geocoded_postings.db"

# 最小サンプル数: これ未満のグループは統計的に不安定なため除外
MIN_SAMPLE_SIZE = 10

# Zipf推定に使う最小ランク数
# N<10では対数線形回帰が不安定なため、10以上を要求する
MIN_RANKS_FOR_ZIPF = 10


# ---------------------------------------------------------------------------
# ユーティリティ関数
# ---------------------------------------------------------------------------

def compute_gini(values: list[float]) -> Optional[float]:
    """ジニ係数を計算する。

    G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
    ここで x_i は昇順ソート済み、i は 1-indexed。
    完全平等 = 0、完全不平等 = 1。

    N < MIN_SAMPLE_SIZE の場合は統計的に無意味なため None を返す。
    N < 2 の場合も None を返す（ジニ係数は定義不能）。
    """
    if not values or len(values) < 2:
        return None

    # サンプル数が少なすぎる場合は統計的に信頼できない
    if len(values) < MIN_SAMPLE_SIZE:
        return None

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)

    if total == 0:
        return 0.0

    weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2.0 * weighted_sum) / (n * total) - (n + 1) / n


def compute_shannon_entropy(counts: dict[str, int]) -> float:
    """シャノンエントロピー H = -sum(p_i * log2(p_i)) を計算する。

    単位: bits (log2)。
    注意: Python側はlog2を正とする。Rust側（analytics.rs）もlog2に統一すべき。
    lnを使うとnat単位になり、値が異なるため混在禁止。
    """
    total = sum(counts.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def compute_percentile(sorted_values: list[float], percentile: float) -> float:
    """ソート済みリストからパーセンタイルを計算する（線形補間）。"""
    if not sorted_values:
        return 0.0

    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]

    # 0-indexed位置を計算
    k = (percentile / 100.0) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return sorted_values[int(k)]

    # 線形補間
    return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)


def safe_median(sorted_values: list[float]) -> float:
    """ソート済みリストの中央値を計算する。"""
    return compute_percentile(sorted_values, 50.0)


def compute_zipf_exponent(rank_counts: list[tuple[int, int]]) -> Optional[float]:
    """ランク-頻度データからZipf指数（log-logの傾き）を推定する。

    rank_counts: [(rank, count), ...] ランク1始まり、countで降順ソート済み
    戻り値: Zipf指数（負の傾きの絶対値）。推定不可の場合None。
    """
    # count >= 2 のエントリのみ使う（count=1はノイズ）
    filtered = [(r, c) for r, c in rank_counts if c >= 2]

    if len(filtered) < MIN_RANKS_FOR_ZIPF:
        return None

    log_ranks = np.log(np.array([r for r, _ in filtered], dtype=np.float64))
    log_counts = np.log(np.array([c for _, c in filtered], dtype=np.float64))

    slope, _intercept, _r_value, _p_value, _std_err = stats.linregress(
        log_ranks, log_counts
    )

    # Zipf指数は傾きの絶対値（通常は正の値として報告）
    return abs(slope)


def compute_hhi(counts: list[int]) -> float:
    """ハーフィンダール・ハーシュマン指数を計算する。

    HHI = sum(s_i^2) ここで s_i はマーケットシェア（0-1）。
    HHI範囲: 1/N（完全分散）〜 1（独占）。
    """
    total = sum(counts)
    if total == 0:
        return 0.0

    return sum((c / total) ** 2 for c in counts)


# ---------------------------------------------------------------------------
# A-1: 給与分布統計
# ---------------------------------------------------------------------------

def compute_a1_salary(conn: sqlite3.Connection) -> int:
    """A-1: 給与分布統計を計算し layer_a_salary_stats テーブルに書き込む。

    戻り値: 挿入行数
    """
    print("=" * 60)
    print("A-1: 給与分布統計（べき乗分布 / パレート分析）")
    print("=" * 60)

    cur = conn.cursor()

    # テーブル再作成（冪等性）
    cur.execute("DROP TABLE IF EXISTS layer_a_salary_stats")
    cur.execute("""
        CREATE TABLE layer_a_salary_stats (
            job_type            TEXT NOT NULL,
            prefecture          TEXT NOT NULL,
            salary_type         TEXT NOT NULL,
            employment_type     TEXT NOT NULL,
            count               INTEGER NOT NULL,
            mean                REAL,
            median              REAL,
            p25                 REAL,
            p75                 REAL,
            p90                 REAL,
            std                 REAL,
            gini                REAL,
            has_salary_range_pct REAL,
            salary_range_median REAL
        )
    """)

    # salary_min > 0 かつ salary_type が空でないデータを取得
    cur.execute("""
        SELECT job_type, prefecture, salary_type, employment_type, salary_min, salary_max
        FROM postings
        WHERE salary_min > 0
          AND salary_type != ''
          AND salary_type IS NOT NULL
    """)
    rows = cur.fetchall()
    print(f"  対象データ: {len(rows):,} 件（salary_min > 0 かつ salary_type非空）")

    # データをグループ化するための辞書構築
    # キー: (job_type, prefecture_or_全国, salary_type, employment_type_or_全体)
    # 値: [(salary_min, salary_max), ...]

    # 3パターンのグループを同時に構築
    # パターン1: job_type × "全国" × salary_type × "全体"
    # パターン2: job_type × prefecture × salary_type × "全体" (count >= 10)
    # パターン3: job_type × "全国" × salary_type × employment_type

    groups: dict[tuple[str, str, str, str], list[tuple[int, int]]] = {}

    for job_type, pref, sal_type, emp_type, sal_min, sal_max in rows:
        emp_type = emp_type if emp_type else ""

        # パターン1: 全国 × 全体
        key1 = (job_type, "全国", sal_type, "全体")
        groups.setdefault(key1, []).append((sal_min, sal_max))

        # パターン2: 都道府県 × 全体
        key2 = (job_type, pref, sal_type, "全体")
        groups.setdefault(key2, []).append((sal_min, sal_max))

        # パターン3: 全国 × 雇用形態（空文字を除外）
        if emp_type:
            key3 = (job_type, "全国", sal_type, emp_type)
            groups.setdefault(key3, []).append((sal_min, sal_max))

    # 統計計算・挿入
    insert_sql = """
        INSERT INTO layer_a_salary_stats
        (job_type, prefecture, salary_type, employment_type,
         count, mean, median, p25, p75, p90, std, gini,
         has_salary_range_pct, salary_range_median)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    insert_rows = []
    skipped = 0

    for (jt, pref, st, et), data_list in groups.items():
        n = len(data_list)
        if n < MIN_SAMPLE_SIZE:
            skipped += 1
            continue

        # salary_min のリスト（ソート済み）
        sal_mins = sorted(v[0] for v in data_list)

        # percentile系統計は外れ値に頑健なため元データで計算
        mean_val = sum(sal_mins) / n
        median_val = safe_median(sal_mins)
        p25_val = compute_percentile(sal_mins, 25.0)
        p75_val = compute_percentile(sal_mins, 75.0)
        p90_val = compute_percentile(sal_mins, 90.0)

        # 外れ値除外（IQR法: Q1-1.5*IQR 〜 Q3+1.5*IQR）
        # Gini係数とstdは外れ値に非常に敏感なため、フィルタ済みデータで計算
        iqr = p75_val - p25_val
        lower_bound = p25_val - 1.5 * iqr
        upper_bound = p75_val + 1.5 * iqr
        sal_mins_filtered = [v for v in sal_mins if lower_bound <= v <= upper_bound]

        # フィルタ後のサンプル数チェック
        if len(sal_mins_filtered) < MIN_SAMPLE_SIZE:
            skipped += 1
            continue

        # 標準偏差（サンプル標準偏差: /(n-1) ベッセル補正）- フィルタ済みデータ
        n_filtered = len(sal_mins_filtered)
        mean_filtered = sum(sal_mins_filtered) / n_filtered
        variance = sum((x - mean_filtered) ** 2 for x in sal_mins_filtered) / (n_filtered - 1)
        std_val = math.sqrt(variance)

        # ジニ係数 - フィルタ済みデータ（外れ値に敏感なため）
        gini_val = compute_gini(sal_mins_filtered)

        # salary_max の分析
        ranges = [v[1] - v[0] for v in data_list if v[1] > 0]
        has_range_pct = (len(ranges) / n) * 100.0 if n > 0 else 0.0
        range_median = safe_median(sorted(ranges)) if ranges else None

        insert_rows.append((
            jt, pref, st, et,
            n,
            round(mean_val, 1),
            round(median_val, 1),
            round(p25_val, 1),
            round(p75_val, 1),
            round(p90_val, 1),
            round(std_val, 1),
            round(gini_val, 4) if gini_val is not None else None,
            round(has_range_pct, 1),
            round(range_median, 1) if range_median is not None else None,
        ))

    cur.executemany(insert_sql, insert_rows)

    # インデックス作成
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_a1_jt_pref
        ON layer_a_salary_stats (job_type, prefecture)
    """)
    conn.commit()

    total_inserted = len(insert_rows)
    print(f"  挿入行数: {total_inserted:,}")
    print(f"  スキップ（n < {MIN_SAMPLE_SIZE}）: {skipped:,}")

    # サマリー出力
    cur.execute("""
        SELECT job_type, salary_type, count, mean, median, gini
        FROM layer_a_salary_stats
        WHERE prefecture = '全国' AND employment_type = '全体'
        ORDER BY job_type, salary_type
    """)
    print("\n  --- 全国サマリー（全体）---")
    print(f"  {'職種':<20s} {'給与種別':<6s} {'件数':>8s} {'平均':>10s} {'中央値':>10s} {'Gini':>6s}")
    print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*10} {'-'*10} {'-'*6}")
    for row in cur.fetchall():
        jt, st, cnt, mn, md, gini = row
        print(f"  {jt:<20s} {st:<6s} {cnt:>8,d} {mn:>10,.0f} {md:>10,.0f} {gini:>6.3f}")

    return total_inserted


# ---------------------------------------------------------------------------
# A-2: 法人求人集中度
# ---------------------------------------------------------------------------

def compute_a2_facility(conn: sqlite3.Connection) -> int:
    """A-2: 法人求人集中度（Zipfの法則）を計算し
    layer_a_facility_concentration テーブルに書き込む。

    戻り値: 挿入行数
    """
    print("\n" + "=" * 60)
    print("A-2: 法人求人集中度（ジップの法則）")
    print("=" * 60)

    cur = conn.cursor()

    # テーブル再作成
    cur.execute("DROP TABLE IF EXISTS layer_a_facility_concentration")
    cur.execute("""
        CREATE TABLE layer_a_facility_concentration (
            job_type            TEXT NOT NULL,
            prefecture          TEXT NOT NULL,
            total_postings      INTEGER NOT NULL,
            unique_facilities   INTEGER NOT NULL,
            top1_name           TEXT,
            top1_count          INTEGER,
            top1_pct            REAL,
            top5_pct            REAL,
            top10_pct           REAL,
            top20_pct           REAL,
            hhi                 REAL,
            zipf_exponent       REAL
        )
    """)

    # 施設名が有効なデータのみ対象
    cur.execute("""
        SELECT job_type, prefecture, facility_name
        FROM postings
        WHERE facility_name IS NOT NULL
          AND facility_name != ''
    """)
    rows = cur.fetchall()
    print(f"  対象データ: {len(rows):,} 件（facility_name非空）")

    # グループ化: (job_type, prefecture) → [facility_name, ...]
    groups: dict[tuple[str, str], list[str]] = {}
    national: dict[str, list[str]] = {}

    for jt, pref, fac in rows:
        # 都道府県別
        key = (jt, pref)
        groups.setdefault(key, []).append(fac)

        # 全国集計
        national.setdefault(jt, []).append(fac)

    def _compute_concentration_row(
        job_type: str, prefecture: str, facility_names: list[str]
    ) -> Optional[tuple]:
        """1グループ分の集中度指標を計算する。"""
        total = len(facility_names)
        if total < MIN_SAMPLE_SIZE:
            return None

        counter = Counter(facility_names)
        ranked = counter.most_common()  # [(name, count), ...]
        unique_count = len(ranked)

        top1_name = ranked[0][0] if ranked else None
        top1_count = ranked[0][1] if ranked else 0
        top1_pct = (top1_count / total) * 100.0

        # topN累積割合
        def _top_n_pct(n: int) -> float:
            top_sum = sum(c for _, c in ranked[:n])
            return (top_sum / total) * 100.0

        top5_pct = _top_n_pct(5)
        top10_pct = _top_n_pct(10)
        top20_pct = _top_n_pct(20)

        # HHI
        counts_list = [c for _, c in ranked]
        hhi = compute_hhi(counts_list)

        # Zipf指数
        rank_counts = [(i + 1, c) for i, (_, c) in enumerate(ranked)]
        zipf_exp = compute_zipf_exponent(rank_counts)

        return (
            job_type, prefecture, total, unique_count,
            top1_name, top1_count,
            round(top1_pct, 2),
            round(top5_pct, 2),
            round(top10_pct, 2),
            round(top20_pct, 2),
            round(hhi, 6),
            round(zipf_exp, 4) if zipf_exp is not None else None,
        )

    insert_sql = """
        INSERT INTO layer_a_facility_concentration
        (job_type, prefecture, total_postings, unique_facilities,
         top1_name, top1_count, top1_pct, top5_pct, top10_pct, top20_pct,
         hhi, zipf_exponent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    insert_rows = []
    skipped = 0

    # 全国集計
    for jt, fac_list in national.items():
        row = _compute_concentration_row(jt, "全国", fac_list)
        if row:
            insert_rows.append(row)
        else:
            skipped += 1

    # 都道府県別
    processed_prefs = 0
    for (jt, pref), fac_list in groups.items():
        row = _compute_concentration_row(jt, pref, fac_list)
        if row:
            insert_rows.append(row)
            processed_prefs += 1
        else:
            skipped += 1

    cur.executemany(insert_sql, insert_rows)

    # インデックス作成
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_a2_jt_pref
        ON layer_a_facility_concentration (job_type, prefecture)
    """)
    conn.commit()

    total_inserted = len(insert_rows)
    print(f"  挿入行数: {total_inserted:,}")
    print(f"  スキップ（n < {MIN_SAMPLE_SIZE}）: {skipped:,}")

    # サマリー出力
    cur.execute("""
        SELECT job_type, total_postings, unique_facilities,
               top1_pct, top5_pct, top10_pct, hhi, zipf_exponent
        FROM layer_a_facility_concentration
        WHERE prefecture = '全国'
        ORDER BY job_type
    """)
    print("\n  --- 全国サマリー ---")
    print(f"  {'職種':<20s} {'求人数':>8s} {'施設数':>8s} {'Top1%':>6s} {'Top5%':>6s} "
          f"{'Top10%':>7s} {'HHI':>8s} {'Zipf':>6s}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*6} {'-'*6} {'-'*7} {'-'*8} {'-'*6}")
    for row in cur.fetchall():
        jt, total, unique, t1, t5, t10, hhi, zipf = row
        zipf_str = f"{zipf:>6.3f}" if zipf is not None else "  N/A "
        print(f"  {jt:<20s} {total:>8,d} {unique:>8,d} {t1:>6.2f} {t5:>6.2f} "
              f"{t10:>7.2f} {hhi:>8.5f} {zipf_str}")

    return total_inserted


# ---------------------------------------------------------------------------
# A-3: 雇用形態多様性
# ---------------------------------------------------------------------------

def compute_a3_diversity(conn: sqlite3.Connection) -> int:
    """A-3: 雇用形態多様性（シャノンエントロピー）を計算し
    layer_a_employment_diversity テーブルに書き込む。

    戻り値: 挿入行数
    """
    print("\n" + "=" * 60)
    print("A-3: 雇用形態多様性（シャノンエントロピー）")
    print("=" * 60)

    cur = conn.cursor()

    # テーブル再作成
    cur.execute("DROP TABLE IF EXISTS layer_a_employment_diversity")
    cur.execute("""
        CREATE TABLE layer_a_employment_diversity (
            job_type            TEXT NOT NULL,
            prefecture          TEXT NOT NULL,
            total_postings      INTEGER NOT NULL,
            n_types             INTEGER NOT NULL,
            shannon_entropy     REAL,
            max_entropy         REAL,
            evenness            REAL,
            dominant_type       TEXT,
            dominant_pct        REAL,
            type_distribution   TEXT
        )
    """)

    # employment_type が有効なデータのみ対象
    cur.execute("""
        SELECT job_type, prefecture, employment_type
        FROM postings
        WHERE employment_type IS NOT NULL
          AND employment_type != ''
    """)
    rows = cur.fetchall()
    print(f"  対象データ: {len(rows):,} 件（employment_type非空）")

    # グループ化
    groups: dict[tuple[str, str], list[str]] = {}
    national: dict[str, list[str]] = {}

    for jt, pref, emp in rows:
        groups.setdefault((jt, pref), []).append(emp)
        national.setdefault(jt, []).append(emp)

    def _compute_diversity_row(
        job_type: str, prefecture: str, emp_types: list[str]
    ) -> Optional[tuple]:
        """1グループ分の多様性指標を計算する。"""
        total = len(emp_types)
        if total < MIN_SAMPLE_SIZE:
            return None

        counter = Counter(emp_types)
        n_types = len(counter)

        # シャノンエントロピー
        entropy = compute_shannon_entropy(dict(counter))

        # 最大エントロピー
        max_ent = math.log2(n_types) if n_types > 1 else 0.0

        # 均等度
        evenness = (entropy / max_ent) if max_ent > 0 else 0.0

        # 支配的雇用形態
        dominant = counter.most_common(1)[0]
        dominant_type = dominant[0]
        dominant_pct = (dominant[1] / total) * 100.0

        # 分布JSON
        distribution = {
            emp: round((cnt / total) * 100.0, 2)
            for emp, cnt in counter.most_common()
        }

        return (
            job_type, prefecture, total, n_types,
            round(entropy, 4),
            round(max_ent, 4),
            round(evenness, 4),
            dominant_type,
            round(dominant_pct, 2),
            json.dumps(distribution, ensure_ascii=False),
        )

    insert_sql = """
        INSERT INTO layer_a_employment_diversity
        (job_type, prefecture, total_postings, n_types,
         shannon_entropy, max_entropy, evenness,
         dominant_type, dominant_pct, type_distribution)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    insert_rows = []
    skipped = 0

    # 全国集計
    for jt, emp_list in national.items():
        row = _compute_diversity_row(jt, "全国", emp_list)
        if row:
            insert_rows.append(row)
        else:
            skipped += 1

    # 都道府県別
    for (jt, pref), emp_list in groups.items():
        row = _compute_diversity_row(jt, pref, emp_list)
        if row:
            insert_rows.append(row)
        else:
            skipped += 1

    cur.executemany(insert_sql, insert_rows)

    # インデックス作成
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_a3_jt_pref
        ON layer_a_employment_diversity (job_type, prefecture)
    """)
    conn.commit()

    total_inserted = len(insert_rows)
    print(f"  挿入行数: {total_inserted:,}")
    print(f"  スキップ（n < {MIN_SAMPLE_SIZE}）: {skipped:,}")

    # サマリー出力
    cur.execute("""
        SELECT job_type, total_postings, n_types,
               shannon_entropy, evenness, dominant_type, dominant_pct
        FROM layer_a_employment_diversity
        WHERE prefecture = '全国'
        ORDER BY job_type
    """)
    print("\n  --- 全国サマリー ---")
    print(f"  {'職種':<20s} {'求人数':>8s} {'種別数':>4s} {'Shannon':>8s} "
          f"{'均等度':>6s} {'支配的':>12s} {'割合%':>6s}")
    print(f"  {'-'*20} {'-'*8} {'-'*4} {'-'*8} {'-'*6} {'-'*12} {'-'*6}")
    for row in cur.fetchall():
        jt, total, nt, se, ev, dom, dom_pct = row
        print(f"  {jt:<20s} {total:>8,d} {nt:>4d} {se:>8.4f} "
              f"{ev:>6.3f} {dom:>12s} {dom_pct:>6.1f}")

    return total_inserted


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    """メインエントリポイント。全Layer A分析を実行する。"""
    sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 60)
    print("Layer A: 量的構造分析（市場のものさし）")
    print(f"DB: {DB_PATH}")
    print("=" * 60)

    start_time = time.time()

    # DB接続
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"[エラー] DB接続失敗: {e}")
        sys.exit(1)

    # 基本情報表示
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM postings")
    total_rows = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT job_type) FROM postings")
    n_job_types = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT prefecture) FROM postings")
    n_prefs = cur.fetchone()[0]
    print(f"\n  postingsテーブル: {total_rows:,} 件")
    print(f"  職種数: {n_job_types}, 都道府県数: {n_prefs}")

    # 各分析を実行
    results = {}

    try:
        results["A-1"] = compute_a1_salary(conn)
    except Exception as e:
        print(f"\n[エラー] A-1 給与分布統計の計算中にエラー: {e}")
        import traceback
        traceback.print_exc()
        results["A-1"] = 0

    try:
        results["A-2"] = compute_a2_facility(conn)
    except Exception as e:
        print(f"\n[エラー] A-2 法人集中度の計算中にエラー: {e}")
        import traceback
        traceback.print_exc()
        results["A-2"] = 0

    try:
        results["A-3"] = compute_a3_diversity(conn)
    except Exception as e:
        print(f"\n[エラー] A-3 雇用形態多様性の計算中にエラー: {e}")
        import traceback
        traceback.print_exc()
        results["A-3"] = 0

    conn.close()

    elapsed = time.time() - start_time

    # 最終サマリー
    print("\n" + "=" * 60)
    print("実行完了サマリー")
    print("=" * 60)
    print(f"  A-1 給与分布統計:     {results['A-1']:>6,d} 行")
    print(f"  A-2 法人求人集中度:   {results['A-2']:>6,d} 行")
    print(f"  A-3 雇用形態多様性:   {results['A-3']:>6,d} 行")
    print(f"  合計:                 {sum(results.values()):>6,d} 行")
    print(f"  処理時間:             {elapsed:.1f} 秒")
    print(f"  出力先: {DB_PATH}")


if __name__ == "__main__":
    main()
