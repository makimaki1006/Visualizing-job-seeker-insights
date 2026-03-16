"""
Layer B v2: 「6つの問い」テキスト分析フレームワーク

text_analysis_signals.py のシグナル辞書を使い、求人テキストを6つの観点で分析する。

Q2: 定型文率分析（基盤 — 他の分析の前に定型部分を識別）
Q1: 差別化シグナル検出（オリジナル部分のみ対象）
Q3: 情報開示ギャップ（競合との比較）
Q4: 採用姿勢・トーン分析
Q5: 情報充足度スコア
Q6: ターゲティング分析（デモグラフィック + サイコグラフィック）

出力: geocoded_postings.db に6テーブルを追加
  - layer_b_template       (Q2: 定型文率)
  - layer_b_differentiation (Q1: 差別化)
  - layer_b_info_gap        (Q3: 情報開示ギャップ)
  - layer_b_tone            (Q4: トーン)
  - layer_b_info_score      (Q5: 情報充足度)
  - layer_b_targeting       (Q6: ターゲティング)

全テーブル: job_type × employment_type × prefecture × municipality で集計
  - municipality='' は都道府県全体の集計（prefectureレベル）
  - prefecture='全国', municipality='' は全国集計
"""

import os
import re
import sqlite3
import sys
import time
import unicodedata
from collections import Counter, defaultdict

import numpy as np

# シグナル辞書のインポート
from text_analysis_signals import (
    ALL_TARGETING,
    ALL_TONE,
    DIFFERENTIATION_SIGNALS,
    INFO_CHECKLIST,
    TEMPLATE_PATTERNS,
    count_signals_in_text,
    flatten_signals,
)

# ============================================================
# 定数
# ============================================================

DB_PATH = r"C:\Users\fuji1\AppData\Local\Temp\rust-dashboard-deploy\data\geocoded_postings.db"

EMPLOYMENT_TYPES = ["全体", "正職員", "パート・バイト"]

# テキスト結合対象カラム
TEXT_COLUMNS = ["headline", "job_description", "requirements", "benefits"]

# Unicode絵文字検出パターン（CJK文字を誤検出しない安全な範囲のみ）
RE_EMOJI = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\u2702-\u27B0"          # dingbats (safe range)
    "\u200d"                 # ZWJ
    "\ufe0f"                 # variation selector
    "]",
    flags=re.UNICODE,
)

# 顔文字パターン
RE_KAOMOJI = re.compile(
    r'[\(（][\s]*[;；\^＾\*\★☆>＞<＜oOTTωΦ・。゜°'
    r'ﾉノ♪♡❤✿✨⁺₊˚]+'
    r'[\s]*[\)）]'
    r'|[;；]\s*[\)）]'
    r'|\(\s*\^\s*\^\s*[♪♡]?\s*\)'
    r'|\(\s*\*\s*\^\s*[_ー]\s*\^\s*\*\s*\)'
    r'|\(\s*[>＞]\s*_\s*[<＜]\s*\)'
    r'|\(\s*T\s*[_ー]\s*T\s*\)'
    r'|\(\s*[笑泣汗]\s*\)'
)

# 定型文区間検出用（法的記述の開始パターン）
RE_LEGAL_BLOCK_START = re.compile(
    r'(?:業務の変更範囲|従事すべき業務の変更|就業場所の変更の範囲|'
    r'受動喫煙対策|受動喫煙防止|懲戒の定め|転勤の可能性|'
    r'雇用期間の定め|契約更新の可能性)'
)


# ============================================================
# テキスト前処理
# ============================================================

def combine_text_fields(row: dict) -> str:
    """複数テキストカラムを結合"""
    parts = []
    for col in TEXT_COLUMNS:
        val = row.get(col)
        if val and isinstance(val, str) and val.strip():
            parts.append(val.strip())
    return "\n".join(parts)


def split_template_original(text: str) -> tuple[str, str]:
    """テキストを定型文部分とオリジナル部分に分離

    Returns:
        (original_text, template_text)
    """
    if not text:
        return ("", "")

    lines = text.split("\n")
    original_lines = []
    template_lines = []
    in_legal_block = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 法的定型文ブロックの開始検出
        if RE_LEGAL_BLOCK_START.search(stripped):
            in_legal_block = True

        # 定型文判定
        is_template = False
        if in_legal_block:
            is_template = True
            # 法的ブロックの終了判定（空行連続または新しいセクション開始）
        else:
            # テンプレートパターンマッチ
            for _cat, patterns in TEMPLATE_PATTERNS["categories"].items():
                for pat in patterns:
                    if pat in stripped:
                        is_template = True
                        break
                if is_template:
                    break

        if is_template:
            template_lines.append(stripped)
        else:
            original_lines.append(stripped)
            # 法的ブロックのリセット（オリジナル文が来たらブロック終了）
            if in_legal_block and len(stripped) > 30:
                in_legal_block = False

    return ("\n".join(original_lines), "\n".join(template_lines))


def count_emoji(text: str) -> int:
    """Unicode絵文字の出現数"""
    return len(RE_EMOJI.findall(text))


def count_kaomoji(text: str) -> int:
    """顔文字の出現数"""
    return len(RE_KAOMOJI.findall(text))


def count_decorative_chars(text: str) -> int:
    """装飾文字（☆★♪◎♡等）のカウント"""
    count = 0
    decorative = set("☆★♪♫♬◎◇◆△▲▽▼○●□■♡♥❤✿✨⁺₊˚✓✔")
    for ch in text:
        if ch in decorative:
            count += 1
    return count


# ============================================================
# 求人ごとのスコア計算（1レコード単位）
# ============================================================

def analyze_single_posting(row: dict) -> dict:
    """1求人を6つの問いで分析し、全スコアを返す

    Args:
        row: DBから取得した1行（dict形式）

    Returns:
        各分析のスコアを含むdict
    """
    full_text = combine_text_fields(row)
    if not full_text:
        return None

    original_text, template_text = split_template_original(full_text)
    full_len = len(full_text)
    orig_len = len(original_text)
    tmpl_len = len(template_text)

    result = {
        "job_type": row["job_type"],
        "employment_type": row.get("employment_type", ""),
        "prefecture": row.get("prefecture", ""),
        "municipality": row.get("municipality", ""),
    }

    # --------------------------------------------------------
    # Q2: 定型文率
    # --------------------------------------------------------
    template_ratio = tmpl_len / full_len if full_len > 0 else 0.0
    result["q2_template_ratio"] = template_ratio
    result["q2_original_length"] = orig_len
    result["q2_template_length"] = tmpl_len
    result["q2_full_length"] = full_len

    # --------------------------------------------------------
    # Q1: 差別化シグナル（オリジナル部分のみ）
    # --------------------------------------------------------
    diff_scores = {}
    for cat_name, cat_data in DIFFERENTIATION_SIGNALS["categories"].items():
        if isinstance(cat_data, list) and cat_data and isinstance(cat_data[0], tuple):
            res = count_signals_in_text(original_text, cat_data)
            diff_scores[cat_name] = res["total_score"]
        elif isinstance(cat_data, list):
            # 文字列リストの場合
            signals = [(s, 1, "") for s in cat_data]
            res = count_signals_in_text(original_text, signals)
            diff_scores[cat_name] = res["total_score"]
    result["q1_diff_total"] = sum(diff_scores.values())
    result["q1_diff_facility"] = diff_scores.get("施設特性", 0)
    result["q1_diff_strength"] = diff_scores.get("独自の強み", 0)
    result["q1_diff_workstyle"] = diff_scores.get("働き方の多様性", 0)

    # --------------------------------------------------------
    # Q4: トーン分析
    # --------------------------------------------------------
    for tone_key, tone_dict in ALL_TONE.items():
        signals = flatten_signals(tone_dict)
        res = count_signals_in_text(full_text, signals)
        result[f"q4_{tone_key}_score"] = res["total_score"]
        result[f"q4_{tone_key}_count"] = res["signal_count"]

    # カジュアル度の追加指標（絵文字・顔文字・装飾）
    emoji_count = count_emoji(full_text)
    kaomoji_count = count_kaomoji(full_text)
    deco_count = count_decorative_chars(full_text)
    result["q4_emoji_count"] = emoji_count
    result["q4_kaomoji_count"] = kaomoji_count
    result["q4_decorative_count"] = deco_count
    # カジュアルスコアに絵文字等を加算
    result["q4_casual_score"] += emoji_count * 2 + kaomoji_count * 2

    # --------------------------------------------------------
    # Q5: 情報充足度
    # --------------------------------------------------------
    info_total = 0
    info_max = 0
    info_categories = {}
    for cat_name, cat_data in INFO_CHECKLIST["categories"].items():
        weight = cat_data["weight"]
        signals = cat_data["signals"]
        res = count_signals_in_text(full_text, signals)
        # 各カテゴリの充足度: シグナル数 / シグナル定義数 (0-1)
        coverage = min(1.0, res["signal_count"] / max(1, len(signals)))
        weighted = coverage * weight
        info_total += weighted
        info_max += weight
        info_categories[cat_name] = coverage
    result["q5_info_score"] = info_total / info_max if info_max > 0 else 0.0
    result["q5_salary_detail"] = info_categories.get("給与の具体性", 0.0)
    result["q5_work_hours"] = info_categories.get("勤務時間の明確さ", 0.0)
    result["q5_holidays"] = info_categories.get("休日の明確さ", 0.0)
    result["q5_job_detail"] = info_categories.get("業務内容の具体性", 0.0)
    result["q5_benefits"] = info_categories.get("福利厚生の開示", 0.0)
    result["q5_transparency"] = info_categories.get("職場環境の透明性", 0.0)

    # --------------------------------------------------------
    # Q3: 情報開示ギャップ（Q5のカテゴリ充足度を使う → 集計時に競合比較）
    # --------------------------------------------------------
    # 個別レベルでは Q5 の各カテゴリスコアをそのまま使用
    # 集計時に同一地域・職種の平均と比較してギャップを計算
    result["q3_info_score_raw"] = result["q5_info_score"]

    # --------------------------------------------------------
    # Q6: ターゲティング分析
    # --------------------------------------------------------
    # デモグラフィック
    for demo_key, demo_dict in ALL_TARGETING["demographic"].items():
        total_score = 0
        subcategory_scores = {}
        for sub_name, sub_data in demo_dict["subcategories"].items():
            res = count_signals_in_text(full_text, sub_data["signals"])
            subcategory_scores[sub_name] = res["total_score"]
            total_score += res["total_score"]
        result[f"q6_demo_{demo_key}_total"] = total_score
        # 最大スコアのサブカテゴリを主ターゲットとして記録
        if subcategory_scores:
            max_sub = max(subcategory_scores, key=subcategory_scores.get)
            result[f"q6_demo_{demo_key}_primary"] = max_sub if subcategory_scores[max_sub] > 0 else "不明"
        else:
            result[f"q6_demo_{demo_key}_primary"] = "不明"

    # サイコグラフィック（12次元: 成長/安定/WLB/貢献/自律/帰属/収入/利便/環境/負荷回避/合理性/理念）
    psycho_scores = {}
    for psycho_key, psycho_dict in ALL_TARGETING["psychographic"].items():
        signals = flatten_signals(psycho_dict)
        res = count_signals_in_text(full_text, signals)
        result[f"q6_psycho_{psycho_key}"] = res["total_score"]
        psycho_scores[psycho_key] = res["total_score"]

    # 上位3つのサイコグラフィックプロファイル
    top3 = sorted(psycho_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    result["q6_psycho_top1"] = top3[0][0] if len(top3) > 0 and top3[0][1] > 0 else "不明"
    result["q6_psycho_top2"] = top3[1][0] if len(top3) > 1 and top3[1][1] > 0 else "不明"
    result["q6_psycho_top3"] = top3[2][0] if len(top3) > 2 and top3[2][1] > 0 else "不明"

    return result


# ============================================================
# DB集計・格納
# ============================================================

def _emp_where(emp_type: str) -> str:
    if emp_type == "全体":
        return ""
    return " AND employment_type = ?"


def _emp_params(emp_type: str, base: tuple) -> tuple:
    if emp_type == "全体":
        return base
    return base + (emp_type,)


def fetch_postings(conn: sqlite3.Connection, job_type: str, emp_type: str) -> list[dict]:
    """指定職種・雇用形態の求人テキストを取得"""
    cols = ["job_type", "employment_type", "prefecture", "municipality"] + TEXT_COLUMNS
    col_str = ", ".join(cols)
    where = f"WHERE job_type = ?{_emp_where(emp_type)}"
    params = _emp_params(emp_type, (job_type,))

    cur = conn.cursor()
    cur.execute(f"SELECT {col_str} FROM postings {where}", params)
    rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def aggregate_scores(scores: list[dict], job_type: str, emp_type: str, prefecture: str) -> dict:
    """スコアリストを集計して統計量を算出"""
    n = len(scores)
    if n == 0:
        return None

    agg = {"job_type": job_type, "employment_type": emp_type, "prefecture": prefecture, "count": n}

    # 数値カラムの統計量を計算
    numeric_keys = [k for k in scores[0].keys() if isinstance(scores[0][k], (int, float))]
    for key in numeric_keys:
        vals = [s[key] for s in scores if isinstance(s.get(key), (int, float))]
        if vals:
            arr = np.array(vals, dtype=float)
            agg[f"{key}_mean"] = float(np.mean(arr))
            agg[f"{key}_median"] = float(np.median(arr))
            agg[f"{key}_std"] = float(np.std(arr))
            agg[f"{key}_p25"] = float(np.percentile(arr, 25))
            agg[f"{key}_p75"] = float(np.percentile(arr, 75))

    # カテゴリカルカラムの最頻値
    cat_keys = [k for k in scores[0].keys()
                if isinstance(scores[0].get(k), str) and k not in ("job_type", "employment_type", "prefecture")]
    for key in cat_keys:
        vals = [s[key] for s in scores if s.get(key) and s[key] != "不明"]
        if vals:
            counter = Counter(vals)
            agg[f"{key}_mode"] = counter.most_common(1)[0][0]
            agg[f"{key}_mode_pct"] = counter.most_common(1)[0][1] / n * 100
        else:
            agg[f"{key}_mode"] = "不明"
            agg[f"{key}_mode_pct"] = 0.0

    return agg


# ============================================================
# DDL
# ============================================================

DDL_TEMPLATE = """
CREATE TABLE IF NOT EXISTS layer_b_template (
    job_type             TEXT NOT NULL,
    employment_type      TEXT NOT NULL DEFAULT '全体',
    prefecture           TEXT NOT NULL,
    municipality         TEXT NOT NULL DEFAULT '',
    count                INTEGER NOT NULL,
    template_ratio_mean  REAL,
    template_ratio_median REAL,
    template_ratio_std   REAL,
    original_length_mean REAL,
    original_length_median REAL,
    template_length_mean REAL,
    full_length_mean     REAL,
    full_length_median   REAL
);
"""

DDL_DIFFERENTIATION = """
CREATE TABLE IF NOT EXISTS layer_b_differentiation (
    job_type              TEXT NOT NULL,
    employment_type       TEXT NOT NULL DEFAULT '全体',
    prefecture            TEXT NOT NULL,
    municipality          TEXT NOT NULL DEFAULT '',
    count                 INTEGER NOT NULL,
    diff_total_mean       REAL,
    diff_total_median     REAL,
    diff_facility_mean    REAL,
    diff_strength_mean    REAL,
    diff_workstyle_mean   REAL,
    diff_zero_pct         REAL
);
"""

DDL_INFO_GAP = """
CREATE TABLE IF NOT EXISTS layer_b_info_gap (
    job_type              TEXT NOT NULL,
    employment_type       TEXT NOT NULL DEFAULT '全体',
    prefecture            TEXT NOT NULL,
    municipality          TEXT NOT NULL DEFAULT '',
    count                 INTEGER NOT NULL,
    info_score_mean       REAL,
    info_score_median     REAL,
    salary_detail_mean    REAL,
    work_hours_mean       REAL,
    holidays_mean         REAL,
    job_detail_mean       REAL,
    benefits_mean         REAL,
    transparency_mean     REAL,
    gap_vs_national       REAL
);
"""

DDL_TONE = """
CREATE TABLE IF NOT EXISTS layer_b_tone (
    job_type              TEXT NOT NULL,
    employment_type       TEXT NOT NULL DEFAULT '全体',
    prefecture            TEXT NOT NULL,
    municipality          TEXT NOT NULL DEFAULT '',
    count                 INTEGER NOT NULL,
    urgency_score_mean    REAL,
    urgency_score_median  REAL,
    enthusiasm_score_mean REAL,
    enthusiasm_score_median REAL,
    casual_score_mean     REAL,
    casual_score_median   REAL,
    selectivity_score_mean REAL,
    selectivity_score_median REAL,
    emoji_pct             REAL,
    kaomoji_pct           REAL,
    decorative_pct        REAL
);
"""

DDL_INFO_SCORE = """
CREATE TABLE IF NOT EXISTS layer_b_info_score (
    job_type              TEXT NOT NULL,
    employment_type       TEXT NOT NULL DEFAULT '全体',
    prefecture            TEXT NOT NULL,
    municipality          TEXT NOT NULL DEFAULT '',
    count                 INTEGER NOT NULL,
    info_score_mean       REAL,
    info_score_median     REAL,
    info_score_std        REAL,
    salary_detail_mean    REAL,
    work_hours_mean       REAL,
    holidays_mean         REAL,
    job_detail_mean       REAL,
    benefits_mean         REAL,
    transparency_mean     REAL,
    grade                 TEXT NOT NULL
);
"""

DDL_TARGETING = """
CREATE TABLE IF NOT EXISTS layer_b_targeting (
    job_type              TEXT NOT NULL,
    employment_type       TEXT NOT NULL DEFAULT '全体',
    prefecture            TEXT NOT NULL,
    municipality          TEXT NOT NULL DEFAULT '',
    count                 INTEGER NOT NULL,
    demo_age_primary_mode TEXT,
    demo_age_primary_pct  REAL,
    demo_exp_primary_mode TEXT,
    demo_exp_primary_pct  REAL,
    demo_life_primary_mode TEXT,
    demo_life_primary_pct REAL,
    demo_qual_primary_mode TEXT,
    demo_qual_primary_pct REAL,
    demo_div_primary_mode TEXT,
    demo_div_primary_pct  REAL,
    psycho_top1_mode      TEXT,
    psycho_top1_pct       REAL,
    psycho_growth_mean    REAL,
    psycho_stability_mean REAL,
    psycho_wlb_mean       REAL,
    psycho_contribution_mean REAL,
    psycho_autonomy_mean  REAL,
    psycho_belonging_mean REAL,
    psycho_income_mean    REAL,
    psycho_convenience_mean REAL,
    psycho_environment_mean REAL,
    psycho_load_aversion_mean REAL,
    psycho_rationality_mean REAL,
    psycho_vision_mean    REAL
);
"""

ALL_TABLES = [
    ("layer_b_template", DDL_TEMPLATE),
    ("layer_b_differentiation", DDL_DIFFERENTIATION),
    ("layer_b_info_gap", DDL_INFO_GAP),
    ("layer_b_tone", DDL_TONE),
    ("layer_b_info_score", DDL_INFO_SCORE),
    ("layer_b_targeting", DDL_TARGETING),
]


def create_tables(conn: sqlite3.Connection, skip_drop: bool = False) -> None:
    """テーブル作成"""
    cur = conn.cursor()
    if not skip_drop:
        for tbl_name, _ in ALL_TABLES:
            cur.execute(f"DROP TABLE IF EXISTS {tbl_name}")
            print(f"  DROP TABLE {tbl_name}")

    for _, ddl in ALL_TABLES:
        cur.execute(ddl)
    conn.commit()

    # インデックス（4カラム複合）
    for tbl_name, _ in ALL_TABLES:
        idx_name = f"idx_{tbl_name}_jt_emp_pref_muni"
        cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tbl_name} (job_type, employment_type, prefecture, municipality)")
    conn.commit()
    print("  テーブル・インデックス作成完了")


# ============================================================
# メイン計算ロジック
# ============================================================

def compute_6q(conn: sqlite3.Connection, target_job_types: list[str] | None = None) -> dict[str, int]:
    """6つの問い分析を実行

    Returns:
        テーブルごとの格納行数
    """
    cur = conn.cursor()
    row_counts = {tbl: 0 for tbl, _ in ALL_TABLES}

    # 対象職種の取得
    cur.execute("SELECT DISTINCT job_type FROM postings ORDER BY job_type")
    all_job_types = [r[0] for r in cur.fetchall()]
    if target_job_types:
        all_job_types = [jt for jt in all_job_types if jt in target_job_types]

    print(f"  対象職種: {len(all_job_types)} 種")
    total_postings = 0

    for emp_type in EMPLOYMENT_TYPES:
        print(f"\n  === 雇用形態: {emp_type} ===")

        # 全国集計用のスコアキャッシュ（Q3ギャップ計算用）
        national_info_scores = {}  # job_type -> list of info_score

        for jt_idx, job_type in enumerate(all_job_types, 1):
            t0 = time.time()
            postings = fetch_postings(conn, job_type, emp_type)
            n = len(postings)
            if n == 0:
                continue

            # 個別スコア計算
            scores = []
            for row in postings:
                s = analyze_single_posting(row)
                if s:
                    scores.append(s)

            if not scores:
                continue

            total_postings += len(scores)

            # 全国集計用にinfo_scoreを蓄積
            info_vals = [s["q5_info_score"] for s in scores]
            national_info_scores[job_type] = info_vals
            national_mean = float(np.mean(info_vals))

            # 都道府県リスト取得
            prefectures = sorted(set(s["prefecture"] for s in scores if s.get("prefecture")))

            # 3段階スコープ: 全国 → 都道府県 → 市区町村
            # (prefecture, municipality, scores) のリストを構築
            scopes = [("全国", "", scores)]  # 全国集計

            for pref in prefectures:
                pref_scores = [s for s in scores if s["prefecture"] == pref]
                if pref_scores:
                    scopes.append((pref, "", pref_scores))  # 都道府県集計

                    # 市区町村集計
                    munis = sorted(set(
                        s["municipality"] for s in pref_scores
                        if s.get("municipality") and s["municipality"].strip()
                    ))
                    for muni in munis:
                        muni_scores = [s for s in pref_scores if s.get("municipality") == muni]
                        if muni_scores:
                            scopes.append((pref, muni, muni_scores))

            for scope_pref, scope_muni, scope_scores in scopes:
                if len(scope_scores) < 3:
                    continue

                n_scope = len(scope_scores)

                # --- Q2: 定型文率 ---
                tr = [s["q2_template_ratio"] for s in scope_scores]
                ol = [s["q2_original_length"] for s in scope_scores]
                tl = [s["q2_template_length"] for s in scope_scores]
                fl = [s["q2_full_length"] for s in scope_scores]
                cur.execute(
                    "INSERT INTO layer_b_template VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (job_type, emp_type, scope_pref, scope_muni, n_scope,
                     float(np.mean(tr)), float(np.median(tr)), float(np.std(tr)),
                     float(np.mean(ol)), float(np.median(ol)),
                     float(np.mean(tl)),
                     float(np.mean(fl)), float(np.median(fl)))
                )
                row_counts["layer_b_template"] += 1

                # --- Q1: 差別化 ---
                dt = [s["q1_diff_total"] for s in scope_scores]
                df = [s["q1_diff_facility"] for s in scope_scores]
                ds = [s["q1_diff_strength"] for s in scope_scores]
                dw = [s["q1_diff_workstyle"] for s in scope_scores]
                zero_pct = sum(1 for x in dt if x == 0) / n_scope * 100
                cur.execute(
                    "INSERT INTO layer_b_differentiation VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (job_type, emp_type, scope_pref, scope_muni, n_scope,
                     float(np.mean(dt)), float(np.median(dt)),
                     float(np.mean(df)), float(np.mean(ds)), float(np.mean(dw)),
                     zero_pct)
                )
                row_counts["layer_b_differentiation"] += 1

                # --- Q5: 情報充足度 ---
                isc = [s["q5_info_score"] for s in scope_scores]
                sal = [s["q5_salary_detail"] for s in scope_scores]
                wh = [s["q5_work_hours"] for s in scope_scores]
                hol = [s["q5_holidays"] for s in scope_scores]
                jd = [s["q5_job_detail"] for s in scope_scores]
                ben = [s["q5_benefits"] for s in scope_scores]
                trn = [s["q5_transparency"] for s in scope_scores]
                mean_isc = float(np.mean(isc))
                # グレード判定（実データ分布に基づく: 全体平均~0.12）
                if mean_isc >= 0.20:
                    grade = "A"
                elif mean_isc >= 0.14:
                    grade = "B"
                elif mean_isc >= 0.10:
                    grade = "C"
                else:
                    grade = "D"
                cur.execute(
                    "INSERT INTO layer_b_info_score VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (job_type, emp_type, scope_pref, scope_muni, n_scope,
                     mean_isc, float(np.median(isc)), float(np.std(isc)),
                     float(np.mean(sal)), float(np.mean(wh)),
                     float(np.mean(hol)), float(np.mean(jd)),
                     float(np.mean(ben)), float(np.mean(trn)),
                     grade)
                )
                row_counts["layer_b_info_score"] += 1

                # --- Q3: 情報開示ギャップ（全国平均との差） ---
                gap_vs_national = mean_isc - national_mean if scope_pref != "全国" else 0.0
                cur.execute(
                    "INSERT INTO layer_b_info_gap VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (job_type, emp_type, scope_pref, scope_muni, n_scope,
                     mean_isc, float(np.median(isc)),
                     float(np.mean(sal)), float(np.mean(wh)),
                     float(np.mean(hol)), float(np.mean(jd)),
                     float(np.mean(ben)), float(np.mean(trn)),
                     gap_vs_national)
                )
                row_counts["layer_b_info_gap"] += 1

                # --- Q4: トーン ---
                urg = [s["q4_urgency_score"] for s in scope_scores]
                ent = [s["q4_enthusiasm_score"] for s in scope_scores]
                cas = [s["q4_casual_score"] for s in scope_scores]
                sel = [s["q4_selectivity_score"] for s in scope_scores]
                emj_pct = sum(1 for s in scope_scores if s["q4_emoji_count"] > 0) / n_scope * 100
                kao_pct = sum(1 for s in scope_scores if s["q4_kaomoji_count"] > 0) / n_scope * 100
                dec_pct = sum(1 for s in scope_scores if s["q4_decorative_count"] > 0) / n_scope * 100
                cur.execute(
                    "INSERT INTO layer_b_tone VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (job_type, emp_type, scope_pref, scope_muni, n_scope,
                     float(np.mean(urg)), float(np.median(urg)),
                     float(np.mean(ent)), float(np.median(ent)),
                     float(np.mean(cas)), float(np.median(cas)),
                     float(np.mean(sel)), float(np.median(sel)),
                     emj_pct, kao_pct, dec_pct)
                )
                row_counts["layer_b_tone"] += 1

                # --- Q6: ターゲティング ---
                # デモグラフィック最頻値（5次元: 年齢/経験/ライフステージ/資格/ダイバーシティ）
                demo_counters = {}
                for dk in ["age", "experience", "lifestage", "qualification", "diversity"]:
                    key = f"q6_demo_{dk}_primary"
                    demo_counters[dk] = Counter(
                        s[key] for s in scope_scores if s.get(key) and s[key] != "不明"
                    )
                top1_modes = Counter(s["q6_psycho_top1"] for s in scope_scores if s["q6_psycho_top1"] != "不明")

                def mode_and_pct(counter, total):
                    if counter:
                        mode, cnt = counter.most_common(1)[0]
                        return mode, cnt / total * 100
                    return "不明", 0.0

                age_mode, age_pct = mode_and_pct(demo_counters["age"], n_scope)
                exp_mode, exp_pct = mode_and_pct(demo_counters["experience"], n_scope)
                life_mode, life_pct = mode_and_pct(demo_counters["lifestage"], n_scope)
                qual_mode, qual_pct = mode_and_pct(demo_counters["qualification"], n_scope)
                div_mode, div_pct = mode_and_pct(demo_counters["diversity"], n_scope)
                top1_mode, top1_pct = mode_and_pct(top1_modes, n_scope)

                # サイコグラフィック平均スコア（12次元）
                psycho_means = {}
                for pk in ["growth", "stability", "wlb", "contribution",
                           "autonomy", "belonging", "income", "convenience",
                           "environment", "load_aversion", "rationality", "vision"]:
                    vals = [s[f"q6_psycho_{pk}"] for s in scope_scores]
                    psycho_means[pk] = float(np.mean(vals))

                cur.execute(
                    "INSERT INTO layer_b_targeting VALUES ("
                    + ",".join(["?"] * 29) + ")",
                    (job_type, emp_type, scope_pref, scope_muni, n_scope,
                     age_mode, age_pct,
                     exp_mode, exp_pct,
                     life_mode, life_pct,
                     qual_mode, qual_pct,
                     div_mode, div_pct,
                     top1_mode, top1_pct,
                     psycho_means["growth"], psycho_means["stability"],
                     psycho_means["wlb"], psycho_means["contribution"],
                     psycho_means["autonomy"], psycho_means["belonging"],
                     psycho_means["income"], psycho_means["convenience"],
                     psycho_means["environment"],
                     psycho_means["load_aversion"], psycho_means["rationality"],
                     psycho_means["vision"])
                )
                row_counts["layer_b_targeting"] += 1

            # 進捗表示
            n_munis = sum(1 for p, m, _ in scopes if m)  # 市区町村スコープ数
            elapsed = time.time() - t0
            print(f"    [{jt_idx}/{len(all_job_types)}] {job_type} ({emp_type}): "
                  f"{len(scores)} 件, {len(prefectures)} 県, {n_munis} 市区町村, {elapsed:.1f}秒")

            # バッチコミット（職種ごと）
            if jt_idx % 3 == 0:
                conn.commit()

        conn.commit()

    print(f"\n  分析した求人総数: {total_postings:,}")
    return row_counts


def verify_results(conn: sqlite3.Connection) -> None:
    """格納結果を検証"""
    cur = conn.cursor()
    print("\n=== 検証結果 ===")

    for tbl_name, _ in ALL_TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {tbl_name}")
        count = cur.fetchone()[0]
        print(f"  {tbl_name}: {count:,} 行")

    # 雇用形態別
    print("\n  雇用形態別行数:")
    for tbl_name, _ in ALL_TABLES:
        cur.execute(f"SELECT employment_type, COUNT(*) FROM {tbl_name} GROUP BY employment_type")
        for emp, cnt in cur.fetchall():
            print(f"    {tbl_name} [{emp}]: {cnt:,}")

    # Q2 サンプル: 定型文率の職種比較
    cur.execute("""
        SELECT job_type, template_ratio_mean, original_length_mean
        FROM layer_b_template
        WHERE prefecture = '全国' AND employment_type = '全体'
        ORDER BY template_ratio_mean DESC LIMIT 5
    """)
    rows = cur.fetchall()
    if rows:
        print("\n  Q2 定型文率 Top5（全体・全国）:")
        for jt, tr, ol in rows:
            print(f"    {jt}: 定型文率={tr:.1%}, オリジナル平均長={ol:.0f}文字")

    # Q4 サンプル: トーン比較
    cur.execute("""
        SELECT job_type, urgency_score_mean, enthusiasm_score_mean,
               casual_score_mean, selectivity_score_mean, emoji_pct
        FROM layer_b_tone
        WHERE prefecture = '全国' AND employment_type = '全体'
        ORDER BY urgency_score_mean DESC LIMIT 5
    """)
    rows = cur.fetchall()
    if rows:
        print("\n  Q4 緊急度 Top5（全体・全国）:")
        for jt, urg, ent, cas, sel, emj in rows:
            print(f"    {jt}: 緊急={urg:.1f}, 歓迎={ent:.1f}, カジュアル={cas:.1f}, "
                  f"選別={sel:.1f}, 絵文字率={emj:.1f}%")

    # Q5 サンプル: 情報充足度
    cur.execute("""
        SELECT job_type, info_score_mean, grade,
               salary_detail_mean, job_detail_mean, transparency_mean
        FROM layer_b_info_score
        WHERE prefecture = '全国' AND employment_type = '全体'
        ORDER BY info_score_mean DESC LIMIT 5
    """)
    rows = cur.fetchall()
    if rows:
        print("\n  Q5 情報充足度 Top5（全体・全国）:")
        for jt, isc, gr, sal, jd, trn in rows:
            print(f"    {jt}: スコア={isc:.3f} [{gr}], 給与={sal:.2f}, "
                  f"業務={jd:.2f}, 透明性={trn:.2f}")

    # Q6 サンプル: ターゲティング
    cur.execute("""
        SELECT job_type, demo_age_primary_mode, demo_exp_primary_mode,
               psycho_top1_mode, psycho_wlb_mean, psycho_growth_mean
        FROM layer_b_targeting
        WHERE prefecture = '全国' AND employment_type = '全体'
        ORDER BY job_type
    """)
    rows = cur.fetchall()
    if rows:
        print("\n  Q6 ターゲティング（全体・全国）:")
        for jt, age, exp, psy, wlb, grw in rows:
            print(f"    {jt}: 年齢={age}, 経験={exp}, 心理={psy}, "
                  f"WLB={wlb:.1f}, 成長={grw:.1f}")

    # Q1 サンプル: 差別化
    cur.execute("""
        SELECT job_type, diff_total_mean, diff_facility_mean,
               diff_strength_mean, diff_workstyle_mean, diff_zero_pct
        FROM layer_b_differentiation
        WHERE prefecture = '全国' AND employment_type = '全体'
        ORDER BY diff_total_mean DESC LIMIT 5
    """)
    rows = cur.fetchall()
    if rows:
        print("\n  Q1 差別化 Top5（全体・全国）:")
        for jt, tot, fac, strn, ws, zp in rows:
            print(f"    {jt}: 合計={tot:.1f}, 施設={fac:.1f}, 強み={strn:.1f}, "
                  f"働き方={ws:.1f}, ゼロ率={zp:.1f}%")

    # 正職員 vs パート比較
    print("\n  === 正職員 vs パート・バイト 比較（全国）===")
    for emp in ["正職員", "パート・バイト"]:
        cur.execute("""
            SELECT job_type, urgency_score_mean, casual_score_mean, info_score_mean
            FROM layer_b_tone t
            JOIN layer_b_info_score i USING (job_type, employment_type, prefecture)
            WHERE t.prefecture = '全国' AND t.employment_type = ?
            ORDER BY job_type LIMIT 5
        """, (emp,))
        rows = cur.fetchall()
        if rows:
            print(f"\n  [{emp}]:")
            for jt, urg, cas, isc in rows:
                print(f"    {jt}: 緊急={urg:.1f}, カジュアル={cas:.1f}, 情報充足={isc:.3f}")


def main() -> None:
    """メインエントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Layer B v2: 6つの問いテキスト分析")
    parser.add_argument(
        "--job-type", nargs="+", metavar="JT",
        help="対象職種（複数指定可、省略で全職種）例: --job-type 介護職 看護師",
    )
    args = parser.parse_args()
    target_jt = args.job_type

    # UTF-8出力設定
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    import builtins
    _original_print = builtins.print

    def flush_print(*a, **kw):
        kw.setdefault("flush", True)
        try:
            _original_print(*a, **kw)
        except UnicodeEncodeError:
            safe = [str(x).encode("ascii", errors="replace").decode("ascii") if isinstance(x, str) else x for x in a]
            _original_print(*safe, **kw)

    builtins.print = flush_print

    print("=" * 60)
    print("Layer B v2: 「6つの問い」テキスト分析フレームワーク")
    print(f"  DB: {DB_PATH}")
    print(f"  雇用形態: {EMPLOYMENT_TYPES}")
    if target_jt:
        print(f"  対象職種: {target_jt}")
    else:
        print("  対象職種: 全職種")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"エラー: DB が見つかりません: {DB_PATH}")
        sys.exit(1)

    start_time = time.time()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")

    try:
        # テーブル作成
        if not target_jt:
            print("\n[1/4] テーブル作成（全再作成）...")
            create_tables(conn, skip_drop=False)
        else:
            print("\n[1/4] テーブル作成（対象職種のみ削除）...")
            create_tables(conn, skip_drop=True)
            for tbl_name, _ in ALL_TABLES:
                for jt in target_jt:
                    conn.execute(f"DELETE FROM [{tbl_name}] WHERE job_type = ?", (jt,))
            conn.commit()
            print(f"  対象職種の既存データを削除済み")

        # 6Q 計算
        print("\n[2/4] 6つの問い分析...")
        t1 = time.time()
        row_counts = compute_6q(conn, target_jt)
        print(f"  計算完了: {time.time() - t1:.1f}秒")

        # コミット
        print("\n[3/4] コミット...")
        conn.commit()

        # 検証
        print("\n[4/4] 検証...")
        verify_results(conn)

        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"全処理完了: {elapsed:.1f}秒")
        total = 0
        for tbl_name, _ in ALL_TABLES:
            cnt = row_counts[tbl_name]
            print(f"  {tbl_name:30s}: {cnt:>8,} 行")
            total += cnt
        print(f"  {'合計':30s}: {total:>8,} 行")
        print(f"{'=' * 60}")

    except Exception as exc:
        conn.rollback()
        print(f"\nエラー発生: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
