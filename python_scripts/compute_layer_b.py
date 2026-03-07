"""
Layer B: 質的特徴分析（求人市場分析フレームワーク）

B-1: キーワード3層構造（TF-IDF）
  - universal: 50%超の職種に共通して出現するキーワード
  - job_type: 特定職種で高TF-IDF、他職種で低TF-IDF
  - regional: 特定都道府県で特徴的なキーワード

B-2: 条件パッケージ共起分析（has_*フラグ）
  - lift（共起度） / phi係数（相関） / support（出現率）

B-3: 原稿品質分布（エントロピー + 漢字率 + スコア）
  - 職種 x 都道府県 の品質統計とグレード分類

出力先: geocoded_postings.db に3テーブルを追加
  - layer_b_keywords
  - layer_b_cooccurrence
  - layer_b_text_quality

MeCab不使用: 正規表現ベースの日本語トークナイザ + 文字N-gram
"""

import math
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# ============================================================
# 定数
# ============================================================

DB_PATH = r"C:\Users\fuji1\AppData\Local\Temp\rust-dashboard-deploy\data\geocoded_postings.db"

# B-1 パラメータ
TFIDF_MAX_FEATURES = 3000
TFIDF_MIN_DF = 5
TFIDF_NGRAM_RANGE = (2, 3)  # 文字N-gram（2-3グラム。4以上は計算コスト大）
TFIDF_SAMPLE_SIZE = 10000   # 職種あたりの最大サンプル数（TF-IDF高速化）
TOP_KEYWORDS_PER_LAYER = 50
UNIVERSAL_THRESHOLD = 0.5  # 50%超の職種に出現で universal
TFIDF_RATIO_THRESHOLD = 2.0  # job_type特有と判定するTF-IDF比率
TOP_PREFECTURES_FOR_REGIONAL = 0  # 0 = 全都道府県で計算

# B-2 パラメータ
MIN_SUPPORT_PCT = 5.0  # フラグ出現率が5%未満のペアは除外
LIFT_UPPER = 1.5  # lift > 1.5 で正の共起
LIFT_LOWER = 0.67  # lift < 0.67 で負の共起

# B-3 パラメータ
MIN_COUNT_FOR_STATS = 10  # 統計計算の最小件数


# ============================================================
# 日本語トークナイザ（MeCab不使用）
# ============================================================

# 正規表現パターン
RE_KATAKANA = re.compile(r'[ァ-ヶー]{2,}')
RE_KANJI = re.compile(r'[一-龥]{2,6}')
RE_MIXED = re.compile(r'[一-龥]+[ァ-ヶー]+|[ァ-ヶー]+[一-龥]+')
RE_ALPHANUM = re.compile(r'[A-Za-zＡ-Ｚａ-ｚ0-9０-９]{2,}')

# ストップワード（頻出すぎて情報量が低い語）
STOPWORDS = frozenset({
    'する', 'ある', 'いる', 'なる', 'れる', 'できる',
    'こと', 'もの', 'ため', 'ところ', 'よう', 'ほう',
    'など', 'まで', 'から', 'より', 'について', 'として',
    'における', 'に対して', 'によって', 'に関する',
    'です', 'ます', 'した', 'して', 'される', 'された',
    'ください', 'いただ', 'おり', 'なお', 'また',
    '等', '及び', '以上', '以下', '未満', '程度',
})

# 装飾文字・ノイズパターン（TF-IDFキーワードから除外）
RE_NOISE = re.compile(r'^[ー\-─━┈┉┄・…。、！？\s\u3000]+$')


def japanese_tokenizer(text: str) -> list[str]:
    """正規表現ベースの日本語トークナイザ（MeCab不要）

    カタカナ語、漢字複合語、混合パターンを抽出する。
    ストップワードと装飾文字を除外し、長さ2文字以上のトークンを返す。
    """
    if not text or not isinstance(text, str):
        return []

    tokens = []

    # カタカナ語の抽出
    for m in RE_KATAKANA.finditer(text):
        token = m.group()
        if len(token) >= 2 and token not in STOPWORDS and not RE_NOISE.match(token):
            tokens.append(token)

    # 漢字複合語の抽出
    for m in RE_KANJI.finditer(text):
        token = m.group()
        if len(token) >= 2 and token not in STOPWORDS:
            tokens.append(token)

    # 混合パターン（漢字+カタカナ or カタカナ+漢字）
    for m in RE_MIXED.finditer(text):
        token = m.group()
        if len(token) >= 2 and not RE_NOISE.match(token):
            tokens.append(token)

    return tokens


def combined_analyzer(text: str) -> list[str]:
    """TfidfVectorizer用のカスタムアナライザ

    正規表現トークンと文字N-gramを組み合わせる。
    文字N-gramはTfidfVectorizer側で処理するため、
    ここでは正規表現トークンのみ返す。
    """
    return japanese_tokenizer(text)


# ============================================================
# DDL（テーブル定義）
# ============================================================

DDL_KEYWORDS = """
CREATE TABLE IF NOT EXISTS layer_b_keywords (
    job_type      TEXT NOT NULL,
    prefecture    TEXT NOT NULL,
    layer         TEXT NOT NULL,
    keyword       TEXT NOT NULL,
    tfidf_score   REAL NOT NULL,
    doc_freq      INTEGER NOT NULL,
    doc_freq_pct  REAL NOT NULL,
    rank          INTEGER NOT NULL
);
"""

DDL_COOCCURRENCE = """
CREATE TABLE IF NOT EXISTS layer_b_cooccurrence (
    job_type            TEXT NOT NULL,
    prefecture          TEXT NOT NULL,
    flag_a              TEXT NOT NULL,
    flag_b              TEXT NOT NULL,
    cooccurrence_count  INTEGER NOT NULL,
    expected_count      REAL NOT NULL,
    lift                REAL NOT NULL,
    phi_coefficient     REAL NOT NULL,
    support_pct         REAL NOT NULL
);
"""

DDL_TEXT_QUALITY = """
CREATE TABLE IF NOT EXISTS layer_b_text_quality (
    job_type              TEXT NOT NULL,
    prefecture            TEXT NOT NULL,
    count                 INTEGER NOT NULL,
    entropy_mean          REAL,
    entropy_median        REAL,
    entropy_std           REAL,
    entropy_p25           REAL,
    entropy_p75           REAL,
    kanji_ratio_mean      REAL,
    kanji_ratio_median    REAL,
    kanji_ratio_std       REAL,
    quality_score_mean    REAL,
    quality_score_median  REAL,
    benefits_score_mean   REAL,
    benefits_score_median REAL,
    desc_length_mean      REAL,
    desc_length_median    REAL,
    grade                 TEXT NOT NULL
);
"""

IDX_KEYWORDS = "CREATE INDEX IF NOT EXISTS idx_keywords_jt_pref ON layer_b_keywords (job_type, prefecture);"
IDX_COOCCURRENCE = "CREATE INDEX IF NOT EXISTS idx_cooccur_jt_pref ON layer_b_cooccurrence (job_type, prefecture);"
IDX_TEXT_QUALITY = "CREATE INDEX IF NOT EXISTS idx_tqual_jt_pref ON layer_b_text_quality (job_type, prefecture);"


# ============================================================
# B-1: キーワード3層構造
# ============================================================

def compute_b1_keywords(conn: sqlite3.Connection) -> int:
    """B-1: TF-IDF キーワード3層構造を計算して layer_b_keywords に格納

    処理手順:
    1. 全職種で文字N-gram TF-IDFを計算（全国レベル）
    2. 職種間のTF-IDFスコア比較で3層分類
    3. 上位5都道府県で regional キーワードを計算

    Returns:
        格納した行数
    """
    cur = conn.cursor()

    # 職種一覧
    cur.execute("SELECT DISTINCT job_type FROM postings ORDER BY job_type")
    job_types = [r[0] for r in cur.fetchall()]
    print(f"  B-1: {len(job_types)} 職種を処理")

    # 全職種のテキストを収集（職種ごとにまとめる。大量の場合はサンプリング）
    import random
    random.seed(42)
    jt_docs = {}  # {job_type: [text, ...]}
    jt_total_docs = {}  # {job_type: 実際のドキュメント総数}
    for jt in job_types:
        cur.execute(
            "SELECT job_description FROM postings "
            "WHERE job_type = ? AND job_description IS NOT NULL AND job_description != ''",
            (jt,)
        )
        docs = [r[0] for r in cur.fetchall()]
        jt_total_docs[jt] = len(docs)
        if len(docs) > TFIDF_SAMPLE_SIZE:
            docs = random.sample(docs, TFIDF_SAMPLE_SIZE)
        if docs:
            jt_docs[jt] = docs
        print(f"    {jt}: {jt_total_docs[jt]} 件中 {len(docs)} 件使用", flush=True)

    if not jt_docs:
        print("  B-1: 対象テキストなし、スキップ")
        return 0

    # --- ステップ1: 職種ごとにTF-IDFを計算 ---
    # 方式A: TfidfVectorizerにカスタムアナライザ（正規表現トークン）を使用
    # 方式B: 正規表現トークン手動集計 → 簡易TF-IDF
    # 両方を組み合わせて高品質なキーワードを抽出
    print("  B-1: TF-IDF計算中（正規表現トークン + TfidfVectorizer）...")
    jt_tfidf_scores = {}  # {job_type: {keyword: avg_score}}
    jt_doc_freq = {}  # {job_type: {keyword: doc_count}}
    jt_doc_count = {}  # {job_type: total_docs}

    for idx_jt, (jt, docs) in enumerate(jt_docs.items()):
        t_start = time.time()
        jt_doc_count[jt] = len(docs)
        min_df = min(TFIDF_MIN_DF, max(2, len(docs) // 100))

        # 方式A: TfidfVectorizer（カスタムアナライザ = 正規表現トークン）
        scores = {}
        doc_freqs = {}
        try:
            vec = TfidfVectorizer(
                analyzer=japanese_tokenizer,
                max_features=TFIDF_MAX_FEATURES,
                min_df=min_df,
                max_df=0.95,
                sublinear_tf=True,
            )
            tfidf_matrix = vec.fit_transform(docs)
            feature_names = vec.get_feature_names_out()

            # 列ごとの平均TF-IDFスコアを一括計算（高速化）
            # 非ゼロ要素の平均
            for col_idx in range(tfidf_matrix.shape[1]):
                col = tfidf_matrix.getcol(col_idx)
                nnz = col.nnz
                if nnz > 0:
                    scores[feature_names[col_idx]] = float(col.sum() / nnz)
                    doc_freqs[feature_names[col_idx]] = nnz
        except ValueError:
            pass

        # 方式B: 正規表現トークン手動集計（方式Aで漏れた語を補完）
        token_counter = Counter()
        token_doc_counter = Counter()
        for doc in docs:
            doc_tokens = set(japanese_tokenizer(doc))
            for t in doc_tokens:
                token_doc_counter[t] += 1
            token_counter.update(japanese_tokenizer(doc))

        total_tokens = max(1, sum(token_counter.values()))
        for token, doc_cnt in token_doc_counter.items():
            if doc_cnt >= min_df and token not in scores:
                tf = token_counter[token] / total_tokens
                idf = math.log(len(docs) / max(1, doc_cnt)) + 1.0
                score = tf * idf
                scores[token] = score
                doc_freqs[token] = doc_cnt

        jt_tfidf_scores[jt] = scores
        jt_doc_freq[jt] = doc_freqs
        elapsed = time.time() - t_start
        print(f"    [{idx_jt+1}/{len(jt_docs)}] {jt}: {len(scores)} keywords ({elapsed:.1f}s)")

    # --- ステップ2: 3層分類 ---
    print("  B-1: キーワード3層分類中...")

    # 全キーワードの職種出現率を計算
    all_keywords = set()
    for scores in jt_tfidf_scores.values():
        all_keywords.update(scores.keys())

    keyword_jt_presence = {}  # {keyword: set of job_types}
    for kw in all_keywords:
        present_in = set()
        for jt in job_types:
            if kw in jt_tfidf_scores.get(jt, {}):
                present_in.add(jt)
        keyword_jt_presence[kw] = present_in

    rows_to_insert = []
    total_jt = len(job_types)

    for jt in job_types:
        scores = jt_tfidf_scores.get(jt, {})
        doc_freqs = jt_doc_freq.get(jt, {})
        total_docs = jt_doc_count.get(jt, 0)
        if not scores or total_docs == 0:
            continue

        # 各キーワードを分類
        universal_kws = []
        job_type_kws = []

        for kw, score in scores.items():
            presence = keyword_jt_presence.get(kw, set())
            presence_ratio = len(presence) / total_jt

            # 他職種での平均スコア
            other_scores = [
                jt_tfidf_scores[ojt].get(kw, 0)
                for ojt in job_types if ojt != jt and ojt in jt_tfidf_scores
            ]
            avg_other = np.mean(other_scores) if other_scores else 0

            df = doc_freqs.get(kw, 0)
            df_pct = (df / total_docs * 100) if total_docs > 0 else 0

            if presence_ratio > UNIVERSAL_THRESHOLD:
                universal_kws.append((kw, score, df, df_pct))
            elif avg_other > 0 and score / avg_other >= TFIDF_RATIO_THRESHOLD:
                job_type_kws.append((kw, score, df, df_pct))
            elif avg_other == 0 and score > 0:
                # 他職種に出現しない → job_type特有
                job_type_kws.append((kw, score, df, df_pct))

        # ソートしてtop N
        universal_kws.sort(key=lambda x: x[1], reverse=True)
        job_type_kws.sort(key=lambda x: x[1], reverse=True)

        for rank, (kw, score, df, df_pct) in enumerate(universal_kws[:TOP_KEYWORDS_PER_LAYER], 1):
            rows_to_insert.append((jt, "全国", "universal", kw, score, df, df_pct, rank))

        for rank, (kw, score, df, df_pct) in enumerate(job_type_kws[:TOP_KEYWORDS_PER_LAYER], 1):
            rows_to_insert.append((jt, "全国", "job_type", kw, score, df, df_pct, rank))

    # --- ステップ3: 都道府県別 regional キーワード ---
    # 全国レベルのドキュメント出現率を事前計算
    jt_national_doc_freq_pct = {}  # {job_type: {keyword: doc_freq%}}
    for jt in job_types:
        total = jt_doc_count.get(jt, 1)
        jt_national_doc_freq_pct[jt] = {
            kw: (df / total * 100) for kw, df in jt_doc_freq.get(jt, {}).items()
        }

    print("  B-1: 都道府県別 regional キーワード計算中...")

    for jt in job_types:
        # 全都道府県を取得（TOP_PREFECTURES_FOR_REGIONAL=0 で制限なし）
        if TOP_PREFECTURES_FOR_REGIONAL > 0:
            cur.execute(
                "SELECT prefecture, COUNT(*) as cnt FROM postings "
                "WHERE job_type = ? GROUP BY prefecture ORDER BY cnt DESC LIMIT ?",
                (jt, TOP_PREFECTURES_FOR_REGIONAL)
            )
        else:
            cur.execute(
                "SELECT prefecture, COUNT(*) as cnt FROM postings "
                "WHERE job_type = ? GROUP BY prefecture ORDER BY cnt DESC",
                (jt,)
            )
        top_prefs = [(r[0], r[1]) for r in cur.fetchall()]

        national_df_pct = jt_national_doc_freq_pct.get(jt, {})
        national_scores = jt_tfidf_scores.get(jt, {})

        for pref, pref_count in top_prefs:
            if pref_count < MIN_COUNT_FOR_STATS:
                continue

            # 都道府県のテキストをサンプリング（高速化）
            sample_limit = min(pref_count, TFIDF_SAMPLE_SIZE)
            cur.execute(
                "SELECT job_description FROM postings "
                "WHERE job_type = ? AND prefecture = ? "
                "AND job_description IS NOT NULL AND job_description != '' "
                "LIMIT ?",
                (jt, pref, sample_limit)
            )
            pref_docs = [r[0] for r in cur.fetchall()]
            if len(pref_docs) < TFIDF_MIN_DF:
                continue

            # TfidfVectorizerで都道府県レベルのTF-IDFを計算
            pref_scores = {}
            pref_doc_freqs = {}
            try:
                pref_vec = TfidfVectorizer(
                    analyzer=japanese_tokenizer,
                    max_features=TFIDF_MAX_FEATURES,
                    min_df=max(2, len(pref_docs) // 100),
                    max_df=0.95,
                    sublinear_tf=True,
                )
                pref_tfidf = pref_vec.fit_transform(pref_docs)
                pref_features = pref_vec.get_feature_names_out()

                for col_idx in range(pref_tfidf.shape[1]):
                    col = pref_tfidf.getcol(col_idx)
                    nnz = col.nnz
                    if nnz > 0:
                        pref_scores[pref_features[col_idx]] = float(col.sum() / nnz)
                        pref_doc_freqs[pref_features[col_idx]] = nnz
            except ValueError:
                continue

            # regional キーワード判定:
            # 1. 都道府県での出現率が全国平均より有意に高い
            # 2. または全国に出現しない地域特有語
            regional_kws = []
            for kw, pref_score in pref_scores.items():
                pref_df = pref_doc_freqs.get(kw, 0)
                pref_df_pct = pref_df / len(pref_docs) * 100

                nat_df_pct = national_df_pct.get(kw, 0)
                nat_score = national_scores.get(kw, 0)

                # 条件1: 都道府県の出現率が全国の1.5倍以上
                if nat_df_pct > 0:
                    df_ratio = pref_df_pct / nat_df_pct
                    if df_ratio >= 1.5:
                        regional_kws.append((kw, pref_score, pref_df, pref_df_pct))
                # 条件2: 全国にない、都道府県特有（3件以上出現）
                elif nat_score == 0 and pref_df >= 3:
                    regional_kws.append((kw, pref_score, pref_df, pref_df_pct))
                # 条件3: TF-IDFスコアが全国の2倍以上
                elif nat_score > 0 and pref_score / nat_score >= 2.0:
                    regional_kws.append((kw, pref_score, pref_df, pref_df_pct))

            regional_kws.sort(key=lambda x: x[1], reverse=True)
            for rank, (kw, score, df, df_pct) in enumerate(regional_kws[:TOP_KEYWORDS_PER_LAYER], 1):
                rows_to_insert.append((jt, pref, "regional", kw, score, df, df_pct, rank))

        print(f"    {jt}: regional キーワード完了 ({len(top_prefs)} 県)")

    # DB格納
    cur.executemany(
        "INSERT INTO layer_b_keywords "
        "(job_type, prefecture, layer, keyword, tfidf_score, doc_freq, doc_freq_pct, rank) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows_to_insert
    )
    conn.commit()
    print(f"  B-1: {len(rows_to_insert)} 行を格納")
    return len(rows_to_insert)


# ============================================================
# B-2: 条件パッケージ共起分析
# ============================================================

def _compute_cooccurrence_for_scope(
    flag_matrix: np.ndarray,
    has_cols: list,
    jt: str,
    scope_name: str,
) -> list:
    """指定スコープ（全国 or 都道府県）でフラグ共起分析を実行

    Returns:
        挿入用タプルのリスト
    """
    n = len(flag_matrix)
    if n < MIN_COUNT_FOR_STATS:
        return []

    flag_means = flag_matrix.mean(axis=0)
    flag_counts = flag_matrix.sum(axis=0)

    valid_flags = [
        i for i, mean in enumerate(flag_means)
        if mean * 100 >= MIN_SUPPORT_PCT
    ]

    rows = []
    for i, j in combinations(valid_flags, 2):
        p_a = flag_means[i]
        p_b = flag_means[j]
        if p_a == 0 or p_b == 0:
            continue

        cooc = np.sum(flag_matrix[:, i] * flag_matrix[:, j])
        p_ab = cooc / n

        expected = p_a * p_b * n
        if expected == 0:
            continue

        lift = p_ab / (p_a * p_b) if (p_a * p_b) > 0 else 0

        if LIFT_LOWER <= lift <= LIFT_UPPER:
            continue

        n_a = flag_counts[i]
        n_b = flag_counts[j]
        denom = math.sqrt(n_a * n_b * (n - n_a) * (n - n_b))
        phi = (n * cooc - n_a * n_b) / denom if denom > 0 else 0

        support_pct = p_ab * 100

        rows.append((
            jt, scope_name,
            has_cols[i], has_cols[j],
            int(cooc), float(expected),
            float(lift), float(phi), float(support_pct)
        ))

    return rows


def compute_b2_cooccurrence(conn: sqlite3.Connection) -> int:
    """B-2: has_*フラグの共起分析（lift, phi係数）

    全国 + 全都道府県で職種ごとに計算。
    support > 5% かつ (lift > 1.5 OR lift < 0.67) のペアのみ格納。

    Returns:
        格納した行数
    """
    cur = conn.cursor()

    # has_*フラグのカラム名を動的取得
    cur.execute("PRAGMA table_info(postings)")
    all_cols = cur.fetchall()
    has_cols = [c[1] for c in all_cols if c[1].startswith("has_")]
    print(f"  B-2: {len(has_cols)} 個の has_* フラグを検出")

    if len(has_cols) < 2:
        print("  B-2: フラグ数不足、スキップ")
        return 0

    # 職種一覧
    cur.execute("SELECT DISTINCT job_type FROM postings ORDER BY job_type")
    job_types = [r[0] for r in cur.fetchall()]

    # フラグカラムのSQL
    flag_cols_sql = ", ".join([f'"{c}"' for c in has_cols])

    rows_to_insert = []

    for jt in job_types:
        # --- 全国スコープ ---
        cur.execute(
            f"SELECT {flag_cols_sql} FROM postings WHERE job_type = ?",
            (jt,)
        )
        data = cur.fetchall()
        n = len(data)
        if n < MIN_COUNT_FOR_STATS:
            print(f"    {jt}: {n} 件（{MIN_COUNT_FOR_STATS}件未満）、スキップ")
            continue

        flag_matrix = np.array(data, dtype=np.float64)
        national_rows = _compute_cooccurrence_for_scope(flag_matrix, has_cols, jt, "全国")
        rows_to_insert.extend(national_rows)
        print(f"    {jt}（全国）: {n} 件, {len(national_rows)} ペア検出")

        # --- 都道府県別スコープ ---
        cur.execute(
            "SELECT DISTINCT prefecture FROM postings "
            "WHERE job_type = ? AND prefecture IS NOT NULL AND prefecture != '' "
            "ORDER BY prefecture",
            (jt,)
        )
        prefectures = [r[0] for r in cur.fetchall()]

        for pref in prefectures:
            cur.execute(
                f"SELECT {flag_cols_sql} FROM postings WHERE job_type = ? AND prefecture = ?",
                (jt, pref)
            )
            pref_data = cur.fetchall()
            if len(pref_data) < MIN_COUNT_FOR_STATS:
                continue

            pref_matrix = np.array(pref_data, dtype=np.float64)
            pref_rows = _compute_cooccurrence_for_scope(pref_matrix, has_cols, jt, pref)
            rows_to_insert.extend(pref_rows)

        pref_total = len(rows_to_insert) - len(national_rows)
        print(f"    {jt}（都道府県別）: {len(prefectures)} 県, {pref_total} ペア追加")

    # DB格納
    cur.executemany(
        "INSERT INTO layer_b_cooccurrence "
        "(job_type, prefecture, flag_a, flag_b, "
        "cooccurrence_count, expected_count, lift, phi_coefficient, support_pct) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows_to_insert
    )
    conn.commit()
    print(f"  B-2: {len(rows_to_insert)} 行を格納")
    return len(rows_to_insert)


# ============================================================
# B-3: 原稿品質分布
# ============================================================

def compute_b3_text_quality(conn: sqlite3.Connection) -> int:
    """B-3: テキスト品質統計を職種x都道府県で計算

    エントロピー、漢字率、充実度スコア、特典スコア、文字数の統計量を算出。
    複合スコアに基づくグレード（A/B/C/D）を判定。

    Returns:
        格納した行数
    """
    cur = conn.cursor()

    # 全職種 x 全都道府県 + 全国の組み合わせ
    cur.execute("SELECT DISTINCT job_type FROM postings ORDER BY job_type")
    job_types = [r[0] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT prefecture FROM postings ORDER BY prefecture")
    prefectures = [r[0] for r in cur.fetchall()]

    rows_to_insert = []

    # 複合スコア計算用: 全体の分布を把握（グレード閾値決定のため）
    all_composite_scores = []

    # 全職種 x (全国 + 各都道府県) で計算
    total_combos = len(job_types) * (1 + len(prefectures))
    processed = 0

    for jt in job_types:
        # 全国 + 各都道府県 を処理
        scope_list = [("全国", None)] + [(p, p) for p in prefectures]

        for scope_name, pref_filter in scope_list:
            if pref_filter:
                cur.execute(
                    "SELECT text_entropy, kanji_ratio, content_richness_score, "
                    "benefits_score, LENGTH(job_description) "
                    "FROM postings "
                    "WHERE job_type = ? AND prefecture = ? "
                    "AND job_description IS NOT NULL AND job_description != ''",
                    (jt, pref_filter)
                )
            else:
                cur.execute(
                    "SELECT text_entropy, kanji_ratio, content_richness_score, "
                    "benefits_score, LENGTH(job_description) "
                    "FROM postings "
                    "WHERE job_type = ? "
                    "AND job_description IS NOT NULL AND job_description != ''",
                    (jt,)
                )

            data = cur.fetchall()
            count = len(data)
            if count < MIN_COUNT_FOR_STATS:
                continue

            # numpy配列に変換（NULLは0扱い）
            arr = np.array(
                [(
                    r[0] if r[0] is not None else 0.0,
                    r[1] if r[1] is not None else 0.0,
                    r[2] if r[2] is not None else 0,
                    r[3] if r[3] is not None else 0,
                    r[4] if r[4] is not None else 0,
                ) for r in data],
                dtype=np.float64
            )

            entropy_arr = arr[:, 0]
            kanji_arr = arr[:, 1]
            quality_arr = arr[:, 2]
            benefits_arr = arr[:, 3]
            desc_len_arr = arr[:, 4]

            # エントロピーが0のレコードは除外して統計計算
            nonzero_entropy = entropy_arr[entropy_arr > 0]
            nonzero_kanji = kanji_arr[kanji_arr > 0]

            # 統計量計算（安全なフォールバック付き）
            def safe_stats(arr_in):
                """配列の統計量を安全に計算（空配列対応）"""
                if len(arr_in) == 0:
                    return None, None, None, None, None
                return (
                    float(np.mean(arr_in)),
                    float(np.median(arr_in)),
                    float(np.std(arr_in, ddof=1)),
                    float(np.percentile(arr_in, 25)),
                    float(np.percentile(arr_in, 75)),
                )

            e_mean, e_med, e_std, e_p25, e_p75 = safe_stats(
                nonzero_entropy if len(nonzero_entropy) > 0 else entropy_arr
            )
            k_mean, k_med, k_std, _, _ = safe_stats(
                nonzero_kanji if len(nonzero_kanji) > 0 else kanji_arr
            )

            q_mean = float(np.mean(quality_arr))
            q_med = float(np.median(quality_arr))
            b_mean = float(np.mean(benefits_arr))
            b_med = float(np.median(benefits_arr))
            d_mean = float(np.mean(desc_len_arr))
            d_med = float(np.median(desc_len_arr))

            # 複合スコア: エントロピー(正規化) + 漢字率 + 充実度(正規化) + 特典(正規化)
            # 各指標を0-1に正規化して合算
            e_norm = (e_mean / 8.0) if e_mean is not None else 0  # max entropy ~ 8
            k_norm = k_mean if k_mean is not None else 0
            q_norm = q_mean / 10.0  # max quality = 10
            b_norm = b_mean / 32.0  # max benefits = 32 (BENEFITS_PATTERNSの定義数)
            composite = (e_norm + k_norm + q_norm + b_norm) / 4.0

            all_composite_scores.append((jt, scope_name, composite, count,
                                          e_mean, e_med, e_std, e_p25, e_p75,
                                          k_mean, k_med, k_std,
                                          q_mean, q_med, b_mean, b_med,
                                          d_mean, d_med))

            processed += 1

        # 進捗表示（職種単位）
        print(f"    {jt}: 品質統計計算完了")

    # --- グレード判定 ---
    # 複合スコアの四分位数でA/B/C/Dを判定
    if all_composite_scores:
        composites = np.array([s[2] for s in all_composite_scores])
        q75 = float(np.percentile(composites, 75))
        q50 = float(np.percentile(composites, 50))
        q25 = float(np.percentile(composites, 25))

        for (jt, scope_name, composite, count,
             e_mean, e_med, e_std, e_p25, e_p75,
             k_mean, k_med, k_std,
             q_mean, q_med, b_mean, b_med,
             d_mean, d_med) in all_composite_scores:

            if composite >= q75:
                grade = "A"
            elif composite >= q50:
                grade = "B"
            elif composite >= q25:
                grade = "C"
            else:
                grade = "D"

            rows_to_insert.append((
                jt, scope_name, count,
                e_mean, e_med, e_std, e_p25, e_p75,
                k_mean, k_med, k_std,
                q_mean, q_med, b_mean, b_med,
                d_mean, d_med, grade
            ))

    # DB格納
    cur.executemany(
        "INSERT INTO layer_b_text_quality "
        "(job_type, prefecture, count, "
        "entropy_mean, entropy_median, entropy_std, entropy_p25, entropy_p75, "
        "kanji_ratio_mean, kanji_ratio_median, kanji_ratio_std, "
        "quality_score_mean, quality_score_median, "
        "benefits_score_mean, benefits_score_median, "
        "desc_length_mean, desc_length_median, grade) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows_to_insert
    )
    conn.commit()
    print(f"  B-3: {len(rows_to_insert)} 行を格納 (グレード閾値: A>={q75:.3f}, B>={q50:.3f}, C>={q25:.3f})")
    return len(rows_to_insert)


# ============================================================
# メイン
# ============================================================

def create_tables(conn: sqlite3.Connection) -> None:
    """テーブルを DROP & CREATE（冪等性のため毎回再作成）"""
    cur = conn.cursor()
    for table_name in ["layer_b_keywords", "layer_b_cooccurrence", "layer_b_text_quality"]:
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        print(f"  DROP TABLE {table_name}")

    cur.execute(DDL_KEYWORDS)
    cur.execute(DDL_COOCCURRENCE)
    cur.execute(DDL_TEXT_QUALITY)
    conn.commit()
    print("  テーブル作成完了")


def create_indexes(conn: sqlite3.Connection) -> None:
    """インデックスを作成"""
    cur = conn.cursor()
    cur.execute(IDX_KEYWORDS)
    cur.execute(IDX_COOCCURRENCE)
    cur.execute(IDX_TEXT_QUALITY)
    conn.commit()
    print("  インデックス作成完了")


def deduplicate_tables(conn: sqlite3.Connection) -> None:
    """重複データを除去（並行プロセスによる重複書き込み対策）"""
    cur = conn.cursor()
    print("\n  重複チェック...")

    # B-1: (job_type, prefecture, layer, keyword) で重複除去
    cur.execute("""
        DELETE FROM layer_b_keywords WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_keywords
            GROUP BY job_type, prefecture, layer, keyword
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_keywords: {cur.rowcount} 重複行を削除")

    # B-2: (job_type, prefecture, flag_a, flag_b) で重複除去
    cur.execute("""
        DELETE FROM layer_b_cooccurrence WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_cooccurrence
            GROUP BY job_type, prefecture, flag_a, flag_b
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_cooccurrence: {cur.rowcount} 重複行を削除")

    # B-3: (job_type, prefecture) で重複除去
    cur.execute("""
        DELETE FROM layer_b_text_quality WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_text_quality
            GROUP BY job_type, prefecture
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_text_quality: {cur.rowcount} 重複行を削除")

    conn.commit()
    print("  重複チェック完了")


def verify_results(conn: sqlite3.Connection) -> None:
    """格納結果を検証して表示"""
    cur = conn.cursor()
    print("\n=== 検証結果 ===")

    for table in ["layer_b_keywords", "layer_b_cooccurrence", "layer_b_text_quality"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count} 行")

    # B-1 検証: 層別の行数
    cur.execute(
        "SELECT layer, COUNT(*), COUNT(DISTINCT job_type) "
        "FROM layer_b_keywords GROUP BY layer"
    )
    print("\n  B-1 層別:")
    for layer, cnt, jt_cnt in cur.fetchall():
        print(f"    {layer}: {cnt} 行 ({jt_cnt} 職種)")

    # B-2 検証: 職種別ペア数
    cur.execute(
        "SELECT job_type, COUNT(*) FROM layer_b_cooccurrence GROUP BY job_type ORDER BY COUNT(*) DESC LIMIT 5"
    )
    print("\n  B-2 上位5職種:")
    for jt, cnt in cur.fetchall():
        print(f"    {jt}: {cnt} ペア")

    # B-3 検証: グレード分布
    cur.execute(
        "SELECT grade, COUNT(*) FROM layer_b_text_quality GROUP BY grade ORDER BY grade"
    )
    print("\n  B-3 グレード分布:")
    for grade, cnt in cur.fetchall():
        print(f"    {grade}: {cnt}")

    # B-1 サンプル: 看護師のjob_type特有キーワード上位5
    cur.execute(
        "SELECT keyword, tfidf_score, doc_freq_pct FROM layer_b_keywords "
        "WHERE job_type = '看護師' AND layer = 'job_type' AND prefecture = '全国' "
        "ORDER BY rank LIMIT 5"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-1 サンプル（看護師 job_type特有 Top5）:")
        for kw, score, pct in rows:
            print(f"    {kw}: score={score:.4f}, doc_freq={pct:.1f}%")

    # B-2 サンプル: 最大liftペア上位5
    cur.execute(
        "SELECT job_type, flag_a, flag_b, lift, phi_coefficient "
        "FROM layer_b_cooccurrence ORDER BY lift DESC LIMIT 5"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-2 サンプル（最大lift Top5）:")
        for jt, fa, fb, lift, phi in rows:
            print(f"    {jt}: {fa} x {fb} → lift={lift:.2f}, phi={phi:.3f}")

    # B-3 サンプル: グレードA の全国レベル
    cur.execute(
        "SELECT job_type, entropy_mean, quality_score_mean, benefits_score_mean, grade "
        "FROM layer_b_text_quality WHERE prefecture = '全国' AND grade = 'A' "
        "ORDER BY quality_score_mean DESC LIMIT 5"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-3 サンプル（グレードA 全国 Top5）:")
        for jt, ent, qual, ben, grade in rows:
            print(f"    {jt}: entropy={ent:.3f}, quality={qual:.1f}, benefits={ben:.1f}")


def main() -> None:
    """メインエントリポイント"""
    # UTF-8出力設定（Windows cp932エラー防止）
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # バックグラウンド実行時はstdoutが再設定不可の場合がある

    # 全printを即時出力にするため、グローバルprintをオーバーライド
    import builtins
    import io
    _original_print = builtins.print

    def flush_print(*args, **kwargs):
        kwargs.setdefault('flush', True)
        try:
            _original_print(*args, **kwargs)
        except UnicodeEncodeError:
            # cp932で出力できない文字を含む場合、ASCII化して出力
            safe_args = []
            for a in args:
                if isinstance(a, str):
                    safe_args.append(a.encode('ascii', errors='replace').decode('ascii'))
                else:
                    safe_args.append(a)
            _original_print(*safe_args, **kwargs)

    builtins.print = flush_print

    print("=" * 60)
    print("Layer B: 質的特徴分析")
    print(f"  DB: {DB_PATH}")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"エラー: DB ファイルが見つかりません: {DB_PATH}")
        sys.exit(1)

    start_time = time.time()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    # WALモードで書き込み性能向上
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB
    # 排他ロックで他プロセスの干渉を防止
    conn.execute("BEGIN EXCLUSIVE")
    conn.commit()
    print("  DB排他ロック取得完了")

    try:
        # テーブル再作成
        print("\n[1/5] テーブル作成...")
        create_tables(conn)

        # B-1: キーワード3層構造
        print("\n[2/5] B-1: キーワード3層構造（TF-IDF）...")
        t1 = time.time()
        b1_count = compute_b1_keywords(conn)
        print(f"  完了: {time.time() - t1:.1f}秒")

        # B-2: 条件パッケージ共起
        print("\n[3/5] B-2: 条件パッケージ共起分析...")
        t2 = time.time()
        b2_count = compute_b2_cooccurrence(conn)
        print(f"  完了: {time.time() - t2:.1f}秒")

        # B-3: 原稿品質分布
        print("\n[4/5] B-3: 原稿品質分布...")
        t3 = time.time()
        b3_count = compute_b3_text_quality(conn)
        print(f"  完了: {time.time() - t3:.1f}秒")

        # 重複除去（並行プロセス対策）
        print("\n[5/6] 重複除去...")
        deduplicate_tables(conn)

        # インデックス作成
        print("\n[6/6] インデックス作成...")
        create_indexes(conn)

        # 検証
        verify_results(conn)

        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"全処理完了: {elapsed:.1f}秒")
        print(f"  B-1 keywords:     {b1_count:>8,} 行")
        print(f"  B-2 cooccurrence: {b2_count:>8,} 行")
        print(f"  B-3 text_quality: {b3_count:>8,} 行")
        print(f"  合計:             {b1_count + b2_count + b3_count:>8,} 行")
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
