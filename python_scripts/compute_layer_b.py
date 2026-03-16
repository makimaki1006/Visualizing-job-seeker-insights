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

B-4: 単語共起分析（NPMI）★NEW
  - テキスト内の単語ペアの共起をNPMI（正規化相互情報量）で評価
  - 学術論文準拠: PMI/NPMI/log-likelihood ratio

出力先: geocoded_postings.db に4テーブルを追加
  - layer_b_keywords          (employment_type別)
  - layer_b_cooccurrence      (employment_type別)
  - layer_b_text_quality      (employment_type別)
  - layer_b_word_cooccurrence (employment_type別) ★NEW

雇用形態別分離: 全体/正職員/パートの3セグメントで計算
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

# 雇用形態セグメント
# "全体" = フィルタなし、"正職員" / "パート・バイト" = WHERE employment_type = ?
EMPLOYMENT_TYPES = ["全体", "正職員", "パート・バイト"]

# B-1 パラメータ
TFIDF_MAX_FEATURES = 3000
TFIDF_MIN_DF = 5
TFIDF_NGRAM_RANGE = (1, 2)  # 単語N-gram（ユニグラム+バイグラム。tokenizer使用時に有効）
TFIDF_SAMPLE_SIZE = 30000   # 職種あたりの最大サンプル数（30kで精度~98%飽和）
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

# B-4 パラメータ（単語共起分析）
B4_MIN_COOCCURRENCE = 5       # 最小共起回数
B4_MIN_NPMI = 0.15            # NPMI閾値（-1〜1、0.15以上で有意な正の共起）
B4_TOP_PAIRS_PER_SCOPE = 100  # スコープあたりの上位ペア数
B4_MIN_WORD_FREQ = 3          # 最小単語出現文書数
B4_WINDOW_SIZE = 0            # 0 = 文書全体を窓とする（文書内共起）


# ============================================================
# 類義語辞書（医療福祉ドメイン）
# ============================================================
# 表記揺れを正規形に統一することでTF-IDF・共起分析の精度を向上
# 学術論文参照: 求人広告テキストマイニングにおける同義語辞書の重要性
SYNONYM_DICT: dict[str, str] = {
    # 組織・法人の呼称
    "当社": "法人", "弊社": "法人", "自社": "法人", "当院": "法人",
    "当施設": "法人", "当園": "法人", "当法人": "法人", "当事業所": "法人",
    "弊院": "法人", "弊施設": "法人", "弊園": "法人",
    # 利用者・患者
    "ご利用者様": "利用者", "ご利用者": "利用者", "利用者様": "利用者",
    "入居者様": "入居者", "ご入居者": "入居者", "ご入居者様": "入居者",
    "患者様": "患者", "患者さん": "患者",
    "お子様": "子ども", "お子さん": "子ども", "お子さま": "子ども",
    "園児さん": "園児", "児童さん": "児童",
    # 職員・スタッフ
    "スタッフ": "職員", "社員": "職員", "メンバー": "職員",
    "従業員": "職員", "ワーカー": "職員",
    # 給与・待遇
    "お給料": "給与", "給料": "給与", "賃金": "給与",
    "お休み": "休日", "休暇": "休日",
    "手当て": "手当", "てあて": "手当",
    # 雇用形態
    "正社員": "正職員", "常勤": "正職員",
    "パートタイム": "パート", "アルバイト": "パート", "非常勤": "パート",
    # 施設種別の統一
    "老健": "介護老人保健施設", "老人保健施設": "介護老人保健施設",
    "特養": "特別養護老人ホーム", "特別養護": "特別養護老人ホーム",
    "グルホ": "グループホーム", "GH": "グループホーム",
    "デイ": "デイサービス", "通所介護": "デイサービス",
    "訪看": "訪問看護", "訪問看護ST": "訪問看護ステーション",
    "サ高住": "サービス付き高齢者向け住宅",
    "有料老人ホーム": "有料ホーム", "住宅型有料": "有料ホーム",
    "介護付き有料": "有料ホーム", "介護付有料": "有料ホーム",
    # 資格
    "准看": "准看護師", "正看": "看護師", "正看護師": "看護師",
    "ケアマネ": "ケアマネジャー", "介護支援専門員": "ケアマネジャー",
    "PT": "理学療法士", "OT": "作業療法士", "ST": "言語聴覚士",
    "管理栄養士": "管理栄養士", "栄養士": "栄養士",
    # 勤務体系
    "日勤のみ": "日勤", "日勤帯": "日勤",
    "夜勤あり": "夜勤", "夜勤専従": "夜勤",
    "シフト制": "シフト", "交代制": "シフト", "交替制": "シフト",
    # 通勤
    "マイカー通勤": "車通勤", "自家用車通勤": "車通勤",
    "マイカー": "車通勤", "車通勤可": "車通勤",
    "駐車場あり": "駐車場完備", "無料駐車場": "駐車場完備",
}


# ============================================================
# 日本語トークナイザ（janome優先、フォールバック: 正規表現）
# ============================================================

# janome形態素解析器（利用可能な場合のみ）
_JANOME_TOKENIZER = None
_USE_JANOME = False
try:
    from janome.tokenizer import Tokenizer as JanomeTokenizer
    _JANOME_TOKENIZER = JanomeTokenizer()
    _USE_JANOME = True
    print("[Layer B] janome形態素解析器を使用します（高品質TF-IDF）")
except ImportError:
    print("[Layer B] janome未インストール: 正規表現トークナイザにフォールバック（pip install janome で改善可能）")

# 正規表現パターン（フォールバック用）
RE_KATAKANA = re.compile(r'[ァ-ヶー]{2,}')
RE_KANJI = re.compile(r'[一-龥]{2,6}')
RE_MIXED = re.compile(r'[一-龥]+[ァ-ヶー]+|[ァ-ヶー]+[一-龥]+')
RE_ALPHANUM = re.compile(r'[A-Za-zＡ-Ｚａ-ｚ0-9０-９]{2,}')

# ストップワード（頻出すぎて情報量が低い語）
# v3.0: 52→160語に拡張（医療福祉ドメイン + 求人共通語 + 敬語・丁寧語）
STOPWORDS = frozenset({
    # 動詞・助動詞（基本形+活用形）
    'する', 'ある', 'いる', 'なる', 'れる', 'できる',
    'いただ', 'いただき', 'いただく', 'いただけ',
    'くださ', 'ください', 'くださる',
    'ございま', 'ございます',
    'おり', 'おります', 'おりま',
    'いたし', 'いたしま', 'いたします',
    'させて', 'させていただ',
    # 形式名詞・接続
    'こと', 'もの', 'ため', 'ところ', 'よう', 'ほう',
    'など', 'まで', 'から', 'より', 'について', 'として',
    'における', 'に対して', 'によって', 'に関する',
    'にあたり', 'にあたって', 'に際し', 'に伴い',
    'とともに', 'をもって', 'に基づき', 'に応じて',
    # 助動詞・敬語
    'です', 'ます', 'した', 'して', 'される', 'された',
    'なお', 'また', 'および', 'ならびに',
    # 量・程度
    '等', '及び', '以上', '以下', '未満', '程度',
    '約', '概ね', '原則', '基本的',
    # 指示語・代名詞
    'この', 'その', 'あの', 'どの', 'これ', 'それ',
    'ここ', 'そこ', 'どこ',
    # 求人共通高頻出語（職種を問わず頻出するためTF-IDF的に無意味）
    '募集', '求人', 'スタッフ', '勤務', '施設', '業務',
    '対応', 'サービス', '担当', '歓迎', '可能', '相談',
    '仕事', '内容', '条件', '情報', '詳細', '一覧',
    '応募', '採用', '選考', '面接', '書類',
    '経験', '資格', '必要', '優遇', '不問', '問わず',
    '給与', '時給', '月給', '年収', '待遇', '福利厚生',
    '交通', 'アクセス', '最寄り', '徒歩', 'バス',
    # 時間・期間
    '時間', '分', '月', '年', '日', '曜日', '週',
    '午前', '午後', '時', '半', '休み',
    # 医療福祉ドメイン共通（職種横断で頻出）
    '介護', '看護', '医療', '福祉', '支援', 'ケア',
    '利用者', '患者', '入居者', '職員', '法人',
    '提供', '実施', '管理', '運営', '連携', '協力',
    '安心', '安全', '丁寧', '笑顔', '元気', '明るい',
    # 敬語・丁寧語のバリエーション
    'お願い', 'ご了承', 'ご確認', 'ご連絡', 'ご応募',
    'お気軽', 'お問い合わせ', 'ご相談', 'ご質問',
    'お待ち', 'お越し',
})

# 装飾文字・ノイズパターン（TF-IDFキーワードから除外）
RE_NOISE = re.compile(r'^[ー\-─━┈┉┄・…。、！？\s\u3000]+$')


# janome用: 抽出対象の品詞（名詞・動詞語幹・形容詞語幹）
_JANOME_POS_TARGETS = {'名詞', '動詞', '形容詞'}
_JANOME_POS_EXCLUDE = {'非自立', '接尾', '数', '代名詞'}


def _apply_synonym(word: str) -> str:
    """類義語辞書で正規形に変換"""
    return SYNONYM_DICT.get(word, word)


def _janome_tokenize(text: str) -> list[str]:
    """janome形態素解析による高品質トークナイザ

    名詞（一般・固有名詞・サ変接続）と動詞・形容詞の語幹を抽出。
    ストップワードと装飾文字を除外し、長さ2文字以上のトークンを返す。
    類義語辞書による正規化を適用。
    """
    tokens = []
    for token in _JANOME_TOKENIZER.tokenize(text):
        # 品詞情報: "名詞,一般,*,*" のような形式
        pos_parts = token.part_of_speech.split(',')
        pos_major = pos_parts[0]
        pos_minor = pos_parts[1] if len(pos_parts) > 1 else ''

        if pos_major not in _JANOME_POS_TARGETS:
            continue
        if pos_minor in _JANOME_POS_EXCLUDE:
            continue

        # 動詞・形容詞は原形（語幹）を使用
        if pos_major in ('動詞', '形容詞'):
            word = token.base_form if token.base_form != '*' else token.surface
        else:
            word = token.surface

        # 類義語辞書で正規化
        word = _apply_synonym(word)

        if len(word) >= 2 and word not in STOPWORDS and not RE_NOISE.match(word):
            tokens.append(word)
    return tokens


def _regex_tokenize(text: str) -> list[str]:
    """正規表現ベースの日本語トークナイザ（フォールバック用）

    カタカナ語、漢字複合語、混合パターンを抽出する。
    ストップワードと装飾文字を除外し、長さ2文字以上のトークンを返す。
    類義語辞書による正規化を適用。
    """
    tokens = []

    # カタカナ語の抽出
    for m in RE_KATAKANA.finditer(text):
        token = _apply_synonym(m.group())
        if len(token) >= 2 and token not in STOPWORDS and not RE_NOISE.match(token):
            tokens.append(token)

    # 漢字複合語の抽出
    for m in RE_KANJI.finditer(text):
        token = _apply_synonym(m.group())
        if len(token) >= 2 and token not in STOPWORDS:
            tokens.append(token)

    # 混合パターン（漢字+カタカナ or カタカナ+漢字）
    for m in RE_MIXED.finditer(text):
        token = _apply_synonym(m.group())
        if len(token) >= 2 and not RE_NOISE.match(token):
            tokens.append(token)

    return tokens


def japanese_tokenizer(text: str) -> list[str]:
    """日本語トークナイザ（janome優先、フォールバック: 正規表現）"""
    if not text or not isinstance(text, str):
        return []
    if _USE_JANOME:
        return _janome_tokenize(text)
    return _regex_tokenize(text)


def combined_analyzer(text: str) -> list[str]:
    """TfidfVectorizer用のカスタムアナライザ"""
    return japanese_tokenizer(text)


# ============================================================
# 雇用形態フィルタ用ヘルパー
# ============================================================

def _emp_type_where(emp_type: str) -> str:
    """雇用形態のWHERE句を生成（SQL結合用）"""
    if emp_type == "全体":
        return ""
    return " AND employment_type = ?"


def _emp_type_params(emp_type: str, base_params: tuple) -> tuple:
    """雇用形態パラメータを追加"""
    if emp_type == "全体":
        return base_params
    return base_params + (emp_type,)


# ============================================================
# DDL（テーブル定義） - employment_type カラム追加
# ============================================================

DDL_KEYWORDS = """
CREATE TABLE IF NOT EXISTS layer_b_keywords (
    job_type        TEXT NOT NULL,
    employment_type TEXT NOT NULL DEFAULT '全体',
    prefecture      TEXT NOT NULL,
    layer           TEXT NOT NULL,
    keyword         TEXT NOT NULL,
    tfidf_score     REAL NOT NULL,
    doc_freq        INTEGER NOT NULL,
    doc_freq_pct    REAL NOT NULL,
    rank            INTEGER NOT NULL
);
"""

DDL_COOCCURRENCE = """
CREATE TABLE IF NOT EXISTS layer_b_cooccurrence (
    job_type            TEXT NOT NULL,
    employment_type     TEXT NOT NULL DEFAULT '全体',
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
    employment_type       TEXT NOT NULL DEFAULT '全体',
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

DDL_WORD_COOCCURRENCE = """
CREATE TABLE IF NOT EXISTS layer_b_word_cooccurrence (
    job_type        TEXT NOT NULL,
    employment_type TEXT NOT NULL DEFAULT '全体',
    prefecture      TEXT NOT NULL,
    word_a          TEXT NOT NULL,
    word_b          TEXT NOT NULL,
    cooccurrence    INTEGER NOT NULL,
    pmi             REAL NOT NULL,
    npmi            REAL NOT NULL,
    freq_a          INTEGER NOT NULL,
    freq_b          INTEGER NOT NULL,
    n_docs          INTEGER NOT NULL
);
"""

IDX_KEYWORDS = "CREATE INDEX IF NOT EXISTS idx_keywords_jt_emp_pref ON layer_b_keywords (job_type, employment_type, prefecture);"
IDX_COOCCURRENCE = "CREATE INDEX IF NOT EXISTS idx_cooccur_jt_emp_pref ON layer_b_cooccurrence (job_type, employment_type, prefecture);"
IDX_TEXT_QUALITY = "CREATE INDEX IF NOT EXISTS idx_tqual_jt_emp_pref ON layer_b_text_quality (job_type, employment_type, prefecture);"
IDX_WORD_COOCCURRENCE = "CREATE INDEX IF NOT EXISTS idx_wcooccur_jt_emp_pref ON layer_b_word_cooccurrence (job_type, employment_type, prefecture);"


# ============================================================
# B-1: キーワード3層構造
# ============================================================

def compute_b1_keywords(conn: sqlite3.Connection, target_job_types: list[str] | None = None) -> int:
    """B-1: TF-IDF キーワード3層構造を計算して layer_b_keywords に格納

    雇用形態別（全体/正職員/パート）に計算する。

    Args:
        target_job_types: 対象職種リスト（Noneで全職種）

    Returns:
        格納した行数
    """
    cur = conn.cursor()
    total_inserted = 0

    for emp_type in EMPLOYMENT_TYPES:
        print(f"\n  B-1 [{emp_type}]: 処理開始...")
        emp_where = _emp_type_where(emp_type)

        # 職種一覧
        cur.execute(
            f"SELECT DISTINCT job_type FROM postings WHERE 1=1{emp_where} ORDER BY job_type",
            (emp_type,) if emp_type != "全体" else ()
        )
        job_types = [r[0] for r in cur.fetchall()]
        if target_job_types:
            job_types = [jt for jt in job_types if jt in target_job_types]
        if not job_types:
            print(f"  B-1 [{emp_type}]: 対象職種なし、スキップ")
            continue
        print(f"  B-1 [{emp_type}]: {len(job_types)} 職種を処理")

        # 全職種のテキストを収集
        import random
        random.seed(42)
        jt_docs = {}
        jt_total_docs = {}
        for jt in job_types:
            cur.execute(
                f"SELECT job_description FROM postings "
                f"WHERE job_type = ?{emp_where} AND job_description IS NOT NULL AND job_description != ''",
                _emp_type_params(emp_type, (jt,))
            )
            docs = [r[0] for r in cur.fetchall()]
            jt_total_docs[jt] = len(docs)
            if len(docs) > TFIDF_SAMPLE_SIZE:
                docs = random.sample(docs, TFIDF_SAMPLE_SIZE)
            if docs:
                jt_docs[jt] = docs
            print(f"    {jt}: {jt_total_docs[jt]} 件中 {len(docs)} 件使用", flush=True)

        if not jt_docs:
            continue

        # --- ステップ1: 職種ごとにTF-IDFを計算 ---
        print(f"  B-1 [{emp_type}]: TF-IDF計算中...")
        jt_tfidf_scores = {}
        jt_doc_freq = {}
        jt_doc_count = {}

        for idx_jt, (jt, docs) in enumerate(jt_docs.items()):
            t_start = time.time()
            jt_doc_count[jt] = len(docs)
            min_df = min(TFIDF_MIN_DF, max(2, len(docs) // 100))

            # TfidfVectorizer（tokenizer指定でngram_rangeが有効になる）
            scores = {}
            doc_freqs = {}
            try:
                vec = TfidfVectorizer(
                    tokenizer=japanese_tokenizer,
                    token_pattern=None,  # tokenizer使用時はtoken_patternを無効化
                    ngram_range=TFIDF_NGRAM_RANGE,
                    max_features=TFIDF_MAX_FEATURES,
                    min_df=min_df,
                    max_df=0.95,
                    sublinear_tf=True,
                )
                tfidf_matrix = vec.fit_transform(docs)
                feature_names = vec.get_feature_names_out()

                for col_idx in range(tfidf_matrix.shape[1]):
                    col = tfidf_matrix.getcol(col_idx)
                    nnz = col.nnz
                    if nnz > 0:
                        scores[feature_names[col_idx]] = float(col.sum() / nnz)
                        doc_freqs[feature_names[col_idx]] = nnz
            except ValueError:
                pass

            # 手動集計で補完
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
        print(f"  B-1 [{emp_type}]: キーワード3層分類中...")

        all_keywords = set()
        for scores in jt_tfidf_scores.values():
            all_keywords.update(scores.keys())

        keyword_jt_presence = {}
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

            universal_kws = []
            job_type_kws = []

            for kw, score in scores.items():
                presence = keyword_jt_presence.get(kw, set())
                presence_ratio = len(presence) / total_jt

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
                    job_type_kws.append((kw, score, df, df_pct))

            universal_kws.sort(key=lambda x: x[1], reverse=True)
            job_type_kws.sort(key=lambda x: x[1], reverse=True)

            for rank, (kw, score, df, df_pct) in enumerate(universal_kws[:TOP_KEYWORDS_PER_LAYER], 1):
                rows_to_insert.append((jt, emp_type, "全国", "universal", kw, score, df, df_pct, rank))

            for rank, (kw, score, df, df_pct) in enumerate(job_type_kws[:TOP_KEYWORDS_PER_LAYER], 1):
                rows_to_insert.append((jt, emp_type, "全国", "job_type", kw, score, df, df_pct, rank))

        # --- ステップ3: 都道府県別 regional キーワード ---
        jt_national_doc_freq_pct = {}
        for jt in job_types:
            total = jt_doc_count.get(jt, 1)
            jt_national_doc_freq_pct[jt] = {
                kw: (df / total * 100) for kw, df in jt_doc_freq.get(jt, {}).items()
            }

        print(f"  B-1 [{emp_type}]: 都道府県別 regional キーワード計算中...")

        for jt in job_types:
            if TOP_PREFECTURES_FOR_REGIONAL > 0:
                cur.execute(
                    f"SELECT prefecture, COUNT(*) as cnt FROM postings "
                    f"WHERE job_type = ?{emp_where} GROUP BY prefecture ORDER BY cnt DESC LIMIT ?",
                    _emp_type_params(emp_type, (jt,)) + (TOP_PREFECTURES_FOR_REGIONAL,)
                )
            else:
                cur.execute(
                    f"SELECT prefecture, COUNT(*) as cnt FROM postings "
                    f"WHERE job_type = ?{emp_where} GROUP BY prefecture ORDER BY cnt DESC",
                    _emp_type_params(emp_type, (jt,))
                )
            top_prefs = [(r[0], r[1]) for r in cur.fetchall()]

            national_df_pct = jt_national_doc_freq_pct.get(jt, {})
            national_scores = jt_tfidf_scores.get(jt, {})

            for pref, pref_count in top_prefs:
                if pref_count < MIN_COUNT_FOR_STATS:
                    continue

                sample_limit = min(pref_count, TFIDF_SAMPLE_SIZE)
                cur.execute(
                    f"SELECT job_description FROM postings "
                    f"WHERE job_type = ? AND prefecture = ?{emp_where} "
                    f"AND job_description IS NOT NULL AND job_description != '' "
                    f"ORDER BY RANDOM() LIMIT ?",
                    _emp_type_params(emp_type, (jt, pref)) + (sample_limit,)
                )
                pref_docs = [r[0] for r in cur.fetchall()]
                if len(pref_docs) < TFIDF_MIN_DF:
                    continue

                pref_scores = {}
                pref_doc_freqs = {}
                try:
                    pref_vec = TfidfVectorizer(
                        tokenizer=japanese_tokenizer,
                        token_pattern=None,  # tokenizer使用時はtoken_patternを無効化
                        ngram_range=TFIDF_NGRAM_RANGE,
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

                regional_kws = []
                for kw, pref_score in pref_scores.items():
                    pref_df = pref_doc_freqs.get(kw, 0)
                    pref_df_pct = pref_df / len(pref_docs) * 100

                    nat_df_pct = national_df_pct.get(kw, 0)
                    nat_score = national_scores.get(kw, 0)

                    if nat_df_pct > 0:
                        df_ratio = pref_df_pct / nat_df_pct
                        if df_ratio >= 1.5:
                            regional_kws.append((kw, pref_score, pref_df, pref_df_pct))
                    elif nat_score == 0 and pref_df >= 3:
                        regional_kws.append((kw, pref_score, pref_df, pref_df_pct))
                    elif nat_score > 0 and pref_score / nat_score >= 2.0:
                        regional_kws.append((kw, pref_score, pref_df, pref_df_pct))

                regional_kws.sort(key=lambda x: x[1], reverse=True)
                for rank, (kw, score, df, df_pct) in enumerate(regional_kws[:TOP_KEYWORDS_PER_LAYER], 1):
                    rows_to_insert.append((jt, emp_type, pref, "regional", kw, score, df, df_pct, rank))

            print(f"    {jt}: regional キーワード完了 ({len(top_prefs)} 県)")

        # DB格納
        cur.executemany(
            "INSERT INTO layer_b_keywords "
            "(job_type, employment_type, prefecture, layer, keyword, tfidf_score, doc_freq, doc_freq_pct, rank) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows_to_insert
        )
        conn.commit()
        print(f"  B-1 [{emp_type}]: {len(rows_to_insert)} 行を格納")
        total_inserted += len(rows_to_insert)

    return total_inserted


# ============================================================
# B-2: 条件パッケージ共起分析
# ============================================================

def _compute_cooccurrence_for_scope(
    flag_matrix: np.ndarray,
    has_cols: list,
    jt: str,
    emp_type: str,
    scope_name: str,
) -> list:
    """指定スコープ（全国 or 都道府県）でフラグ共起分析を実行"""
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
            jt, emp_type, scope_name,
            has_cols[i], has_cols[j],
            int(cooc), float(expected),
            float(lift), float(phi), float(support_pct)
        ))

    return rows


def compute_b2_cooccurrence(conn: sqlite3.Connection, target_job_types: list[str] | None = None) -> int:
    """B-2: has_*フラグの共起分析（lift, phi係数）

    雇用形態別（全体/正職員/パート）に計算する。

    Args:
        target_job_types: 対象職種リスト（Noneで全職種）

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

    flag_cols_sql = ", ".join([f'"{c}"' for c in has_cols])
    total_inserted = 0

    for emp_type in EMPLOYMENT_TYPES:
        print(f"\n  B-2 [{emp_type}]: 処理開始...")
        emp_where = _emp_type_where(emp_type)

        cur.execute(
            f"SELECT DISTINCT job_type FROM postings WHERE 1=1{emp_where} ORDER BY job_type",
            (emp_type,) if emp_type != "全体" else ()
        )
        job_types = [r[0] for r in cur.fetchall()]
        if target_job_types:
            job_types = [jt for jt in job_types if jt in target_job_types]

        rows_to_insert = []

        for jt in job_types:
            # --- 全国スコープ ---
            cur.execute(
                f"SELECT {flag_cols_sql} FROM postings WHERE job_type = ?{emp_where}",
                _emp_type_params(emp_type, (jt,))
            )
            data = cur.fetchall()
            n = len(data)
            if n < MIN_COUNT_FOR_STATS:
                continue

            flag_matrix = np.array(data, dtype=np.float64)
            national_rows = _compute_cooccurrence_for_scope(flag_matrix, has_cols, jt, emp_type, "全国")
            rows_to_insert.extend(national_rows)
            print(f"    {jt}（全国）: {n} 件, {len(national_rows)} ペア検出")

            # --- 都道府県別スコープ ---
            cur.execute(
                f"SELECT DISTINCT prefecture FROM postings "
                f"WHERE job_type = ?{emp_where} AND prefecture IS NOT NULL AND prefecture != '' "
                f"ORDER BY prefecture",
                _emp_type_params(emp_type, (jt,))
            )
            prefectures = [r[0] for r in cur.fetchall()]

            for pref in prefectures:
                cur.execute(
                    f"SELECT {flag_cols_sql} FROM postings WHERE job_type = ? AND prefecture = ?{emp_where}",
                    _emp_type_params(emp_type, (jt, pref))
                )
                pref_data = cur.fetchall()
                if len(pref_data) < MIN_COUNT_FOR_STATS:
                    continue

                pref_matrix = np.array(pref_data, dtype=np.float64)
                pref_rows = _compute_cooccurrence_for_scope(pref_matrix, has_cols, jt, emp_type, pref)
                rows_to_insert.extend(pref_rows)

        # DB格納
        cur.executemany(
            "INSERT INTO layer_b_cooccurrence "
            "(job_type, employment_type, prefecture, flag_a, flag_b, "
            "cooccurrence_count, expected_count, lift, phi_coefficient, support_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows_to_insert
        )
        conn.commit()
        print(f"  B-2 [{emp_type}]: {len(rows_to_insert)} 行を格納")
        total_inserted += len(rows_to_insert)

    return total_inserted


# ============================================================
# B-3: 原稿品質分布
# ============================================================

def compute_b3_text_quality(conn: sqlite3.Connection, target_job_types: list[str] | None = None) -> int:
    """B-3: テキスト品質統計を職種x都道府県で計算

    雇用形態別（全体/正職員/パート）に計算する。

    Args:
        target_job_types: 対象職種リスト（Noneで全職種）

    Returns:
        格納した行数
    """
    cur = conn.cursor()
    total_inserted = 0

    for emp_type in EMPLOYMENT_TYPES:
        print(f"\n  B-3 [{emp_type}]: 処理開始...")
        emp_where = _emp_type_where(emp_type)

        cur.execute(
            f"SELECT DISTINCT job_type FROM postings WHERE 1=1{emp_where} ORDER BY job_type",
            (emp_type,) if emp_type != "全体" else ()
        )
        job_types = [r[0] for r in cur.fetchall()]
        if target_job_types:
            job_types = [jt for jt in job_types if jt in target_job_types]

        cur.execute("SELECT DISTINCT prefecture FROM postings ORDER BY prefecture")
        prefectures = [r[0] for r in cur.fetchall()]

        rows_to_insert = []
        all_composite_scores = []

        for jt in job_types:
            scope_list = [("全国", None)] + [(p, p) for p in prefectures]

            for scope_name, pref_filter in scope_list:
                if pref_filter:
                    cur.execute(
                        f"SELECT text_entropy, kanji_ratio, content_richness_score, "
                        f"benefits_score, LENGTH(job_description) "
                        f"FROM postings "
                        f"WHERE job_type = ? AND prefecture = ?{emp_where} "
                        f"AND job_description IS NOT NULL AND job_description != ''",
                        _emp_type_params(emp_type, (jt, pref_filter))
                    )
                else:
                    cur.execute(
                        f"SELECT text_entropy, kanji_ratio, content_richness_score, "
                        f"benefits_score, LENGTH(job_description) "
                        f"FROM postings "
                        f"WHERE job_type = ?{emp_where} "
                        f"AND job_description IS NOT NULL AND job_description != ''",
                        _emp_type_params(emp_type, (jt,))
                    )

                data = cur.fetchall()
                count = len(data)
                if count < MIN_COUNT_FOR_STATS:
                    continue

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

                nonzero_entropy = entropy_arr[entropy_arr > 0]
                nonzero_kanji = kanji_arr[kanji_arr > 0]

                def safe_stats(arr_in):
                    if len(arr_in) == 0:
                        return None, None, None, None, None
                    return (
                        float(np.mean(arr_in)),
                        float(np.median(arr_in)),
                        float(np.std(arr_in, ddof=1)) if len(arr_in) > 1 else 0.0,
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

                e_norm = (e_mean / 8.0) if e_mean is not None else 0
                k_norm = k_mean if k_mean is not None else 0
                q_norm = q_mean / 10.0
                b_norm = b_mean / 32.0
                composite = (e_norm + k_norm + q_norm + b_norm) / 4.0

                all_composite_scores.append((jt, scope_name, composite, count,
                                              e_mean, e_med, e_std, e_p25, e_p75,
                                              k_mean, k_med, k_std,
                                              q_mean, q_med, b_mean, b_med,
                                              d_mean, d_med))

            print(f"    {jt}: 品質統計計算完了")

        # グレード判定
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
                    jt, emp_type, scope_name, count,
                    e_mean, e_med, e_std, e_p25, e_p75,
                    k_mean, k_med, k_std,
                    q_mean, q_med, b_mean, b_med,
                    d_mean, d_med, grade
                ))

        # DB格納
        cur.executemany(
            "INSERT INTO layer_b_text_quality "
            "(job_type, employment_type, prefecture, count, "
            "entropy_mean, entropy_median, entropy_std, entropy_p25, entropy_p75, "
            "kanji_ratio_mean, kanji_ratio_median, kanji_ratio_std, "
            "quality_score_mean, quality_score_median, "
            "benefits_score_mean, benefits_score_median, "
            "desc_length_mean, desc_length_median, grade) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows_to_insert
        )
        conn.commit()
        if all_composite_scores:
            print(f"  B-3 [{emp_type}]: {len(rows_to_insert)} 行を格納 "
                  f"(グレード閾値: A>={q75:.3f}, B>={q50:.3f}, C>={q25:.3f})")
        total_inserted += len(rows_to_insert)

    return total_inserted


# ============================================================
# B-4: 単語共起分析（NPMI）★NEW
# ============================================================

def _compute_word_cooccurrence_for_docs(
    docs: list[str],
    jt: str,
    emp_type: str,
    scope_name: str,
) -> list:
    """文書集合から単語共起ペアをNPMI付きで計算

    PMI(x,y) = log2(P(x,y) / (P(x) * P(y)))
    NPMI(x,y) = PMI(x,y) / -log2(P(x,y))  → [-1, 1]に正規化

    Returns:
        挿入用タプルのリスト
    """
    n_docs = len(docs)
    if n_docs < MIN_COUNT_FOR_STATS:
        return []

    # 2パス方式: パス1で全文書のword_doc_freqを計算してからパス2でペアカウント
    # （1パスだと初期文書でword_doc_freqが不足し、ペアが欠落するバグがあった）

    # パス1: 全文書のトークン集合を保持しつつ単語文書頻度を計算
    word_doc_freq = Counter()  # 単語の文書出現数
    doc_token_sets: list[list[str]] = []  # 各文書のソート済みトークンリスト

    for doc in docs:
        tokens = set(japanese_tokenizer(doc))
        if len(tokens) < 2:
            doc_token_sets.append([])
            continue
        for t in tokens:
            word_doc_freq[t] += 1
        doc_token_sets.append(sorted(tokens))

    # パス2: B4_MIN_WORD_FREQを満たす単語のペアのみカウント
    pair_doc_freq = Counter()  # ペアの共起文書数

    for sorted_tokens in doc_token_sets:
        if len(sorted_tokens) < 2:
            continue
        # 頻度フィルタを通過する単語のみ抽出
        frequent_tokens = [t for t in sorted_tokens if word_doc_freq[t] >= B4_MIN_WORD_FREQ]
        for i in range(len(frequent_tokens)):
            for j in range(i + 1, len(frequent_tokens)):
                pair_doc_freq[(frequent_tokens[i], frequent_tokens[j])] += 1

    # NPMI計算
    rows = []
    for (w_a, w_b), cooc in pair_doc_freq.items():
        if cooc < B4_MIN_COOCCURRENCE:
            continue

        freq_a = word_doc_freq[w_a]
        freq_b = word_doc_freq[w_b]

        # 最小文書頻度チェック
        if freq_a < B4_MIN_WORD_FREQ or freq_b < B4_MIN_WORD_FREQ:
            continue

        p_a = freq_a / n_docs
        p_b = freq_b / n_docs
        p_ab = cooc / n_docs

        if p_a == 0 or p_b == 0 or p_ab == 0:
            continue

        pmi = math.log2(p_ab / (p_a * p_b))
        npmi = pmi / (-math.log2(p_ab)) if p_ab < 1.0 else 0.0

        if npmi < B4_MIN_NPMI:
            continue

        rows.append((
            jt, emp_type, scope_name,
            w_a, w_b,
            cooc, round(pmi, 4), round(npmi, 4),
            freq_a, freq_b, n_docs
        ))

    # NPMIの降順でソートし上位のみ返す
    rows.sort(key=lambda x: x[7], reverse=True)  # npmi列でソート
    return rows[:B4_TOP_PAIRS_PER_SCOPE]


def compute_b4_word_cooccurrence(conn: sqlite3.Connection, target_job_types: list[str] | None = None) -> int:
    """B-4: テキスト内単語共起分析（NPMI）

    求人原稿テキスト内の単語ペアの共起をNPMI（正規化相互情報量）で評価。
    雇用形態別（全体/正職員/パート）× 職種 × (全国 + 各都道府県) で計算。

    学術論文参照:
    - 「単語共起関係を用いた求人情報の分析事例について」
    - 「求人広告にみられるモチベーションに類する語の共起ネットワーク」

    Args:
        target_job_types: 対象職種リスト（Noneで全職種）

    Returns:
        格納した行数
    """
    cur = conn.cursor()
    import random
    random.seed(42)
    total_inserted = 0

    for emp_type in EMPLOYMENT_TYPES:
        print(f"\n  B-4 [{emp_type}]: 単語共起分析開始...")
        emp_where = _emp_type_where(emp_type)

        cur.execute(
            f"SELECT DISTINCT job_type FROM postings WHERE 1=1{emp_where} ORDER BY job_type",
            (emp_type,) if emp_type != "全体" else ()
        )
        job_types = [r[0] for r in cur.fetchall()]
        if target_job_types:
            job_types = [jt for jt in job_types if jt in target_job_types]

        rows_to_insert = []

        for jt in job_types:
            t_start = time.time()

            # --- 全国スコープ ---
            cur.execute(
                f"SELECT job_description FROM postings "
                f"WHERE job_type = ?{emp_where} "
                f"AND job_description IS NOT NULL AND job_description != ''",
                _emp_type_params(emp_type, (jt,))
            )
            all_docs = [r[0] for r in cur.fetchall()]
            if len(all_docs) > TFIDF_SAMPLE_SIZE:
                all_docs_sample = random.sample(all_docs, TFIDF_SAMPLE_SIZE)
            else:
                all_docs_sample = all_docs

            national_rows = _compute_word_cooccurrence_for_docs(
                all_docs_sample, jt, emp_type, "全国"
            )
            rows_to_insert.extend(national_rows)

            # --- 都道府県別スコープ（上位10県のみ、計算コスト抑制） ---
            cur.execute(
                f"SELECT prefecture, COUNT(*) as cnt FROM postings "
                f"WHERE job_type = ?{emp_where} "
                f"AND prefecture IS NOT NULL AND prefecture != '' "
                f"GROUP BY prefecture ORDER BY cnt DESC LIMIT 10",
                _emp_type_params(emp_type, (jt,))
            )
            top_prefs = [(r[0], r[1]) for r in cur.fetchall()]

            for pref, pref_count in top_prefs:
                if pref_count < MIN_COUNT_FOR_STATS * 5:  # 共起分析はデータ量が必要
                    continue

                sample_limit = min(pref_count, TFIDF_SAMPLE_SIZE)
                cur.execute(
                    f"SELECT job_description FROM postings "
                    f"WHERE job_type = ? AND prefecture = ?{emp_where} "
                    f"AND job_description IS NOT NULL AND job_description != '' "
                    f"ORDER BY RANDOM() LIMIT ?",
                    _emp_type_params(emp_type, (jt, pref)) + (sample_limit,)
                )
                pref_docs = [r[0] for r in cur.fetchall()]
                pref_rows = _compute_word_cooccurrence_for_docs(
                    pref_docs, jt, emp_type, pref
                )
                rows_to_insert.extend(pref_rows)

            elapsed = time.time() - t_start
            print(f"    {jt}: {len(all_docs)} 件, {len(national_rows)} 全国ペア "
                  f"+ {len(top_prefs)} 県 ({elapsed:.1f}s)")

        # DB格納
        cur.executemany(
            "INSERT INTO layer_b_word_cooccurrence "
            "(job_type, employment_type, prefecture, "
            "word_a, word_b, cooccurrence, pmi, npmi, freq_a, freq_b, n_docs) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows_to_insert
        )
        conn.commit()
        print(f"  B-4 [{emp_type}]: {len(rows_to_insert)} 行を格納")
        total_inserted += len(rows_to_insert)

    return total_inserted


# ============================================================
# メイン
# ============================================================

def create_tables(conn: sqlite3.Connection, skip_drop: bool = False) -> None:
    """テーブルを CREATE（skip_drop=Falseなら事前にDROP）"""
    cur = conn.cursor()
    if not skip_drop:
        for table_name in [
            "layer_b_keywords", "layer_b_cooccurrence",
            "layer_b_text_quality", "layer_b_word_cooccurrence"
        ]:
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"  DROP TABLE {table_name}")

    # CREATE IF NOT EXISTS なので skip_drop=True でも安全
    cur.execute(DDL_KEYWORDS)
    cur.execute(DDL_COOCCURRENCE)
    cur.execute(DDL_TEXT_QUALITY)
    cur.execute(DDL_WORD_COOCCURRENCE)
    conn.commit()
    print("  テーブル作成完了")


def create_indexes(conn: sqlite3.Connection) -> None:
    """インデックスを作成"""
    cur = conn.cursor()
    cur.execute(IDX_KEYWORDS)
    cur.execute(IDX_COOCCURRENCE)
    cur.execute(IDX_TEXT_QUALITY)
    cur.execute(IDX_WORD_COOCCURRENCE)
    conn.commit()
    print("  インデックス作成完了")


def deduplicate_tables(conn: sqlite3.Connection) -> None:
    """重複データを除去（並行プロセスによる重複書き込み対策）"""
    cur = conn.cursor()
    print("\n  重複チェック...")

    # B-1: (job_type, employment_type, prefecture, layer, keyword) で重複除去
    cur.execute("""
        DELETE FROM layer_b_keywords WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_keywords
            GROUP BY job_type, employment_type, prefecture, layer, keyword
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_keywords: {cur.rowcount} 重複行を削除")

    # B-2: (job_type, employment_type, prefecture, flag_a, flag_b) で重複除去
    cur.execute("""
        DELETE FROM layer_b_cooccurrence WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_cooccurrence
            GROUP BY job_type, employment_type, prefecture, flag_a, flag_b
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_cooccurrence: {cur.rowcount} 重複行を削除")

    # B-3: (job_type, employment_type, prefecture) で重複除去
    cur.execute("""
        DELETE FROM layer_b_text_quality WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_text_quality
            GROUP BY job_type, employment_type, prefecture
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_text_quality: {cur.rowcount} 重複行を削除")

    # B-4: (job_type, employment_type, prefecture, word_a, word_b) で重複除去
    cur.execute("""
        DELETE FROM layer_b_word_cooccurrence WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM layer_b_word_cooccurrence
            GROUP BY job_type, employment_type, prefecture, word_a, word_b
        )
    """)
    if cur.rowcount > 0:
        print(f"    layer_b_word_cooccurrence: {cur.rowcount} 重複行を削除")

    conn.commit()
    print("  重複チェック完了")


def verify_results(conn: sqlite3.Connection) -> None:
    """格納結果を検証して表示"""
    cur = conn.cursor()
    print("\n=== 検証結果 ===")

    for table in [
        "layer_b_keywords", "layer_b_cooccurrence",
        "layer_b_text_quality", "layer_b_word_cooccurrence"
    ]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table}: {count} 行")

    # 雇用形態別の行数
    print("\n  雇用形態別行数:")
    for table in ["layer_b_keywords", "layer_b_cooccurrence",
                   "layer_b_text_quality", "layer_b_word_cooccurrence"]:
        cur.execute(
            f"SELECT employment_type, COUNT(*) FROM {table} GROUP BY employment_type ORDER BY employment_type"
        )
        for emp, cnt in cur.fetchall():
            print(f"    {table} [{emp}]: {cnt}")

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
        "SELECT job_type, COUNT(*) FROM layer_b_cooccurrence "
        "WHERE employment_type = '全体' GROUP BY job_type ORDER BY COUNT(*) DESC LIMIT 5"
    )
    print("\n  B-2 上位5職種（全体）:")
    for jt, cnt in cur.fetchall():
        print(f"    {jt}: {cnt} ペア")

    # B-3 検証: グレード分布
    cur.execute(
        "SELECT grade, COUNT(*) FROM layer_b_text_quality "
        "WHERE employment_type = '全体' GROUP BY grade ORDER BY grade"
    )
    print("\n  B-3 グレード分布（全体）:")
    for grade, cnt in cur.fetchall():
        print(f"    {grade}: {cnt}")

    # B-4 検証: 上位NPMIペア
    cur.execute(
        "SELECT job_type, word_a, word_b, npmi, cooccurrence "
        "FROM layer_b_word_cooccurrence "
        "WHERE employment_type = '全体' AND prefecture = '全国' "
        "ORDER BY npmi DESC LIMIT 10"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-4 サンプル（全体・全国 NPMI Top10）:")
        for jt, wa, wb, npmi, cooc in rows:
            print(f"    {jt}: {wa} × {wb} → NPMI={npmi:.3f} (共起={cooc})")

    # B-1 サンプル: 看護師のjob_type特有キーワード上位5
    cur.execute(
        "SELECT keyword, tfidf_score, doc_freq_pct FROM layer_b_keywords "
        "WHERE job_type = '看護師' AND layer = 'job_type' AND prefecture = '全国' "
        "AND employment_type = '全体' "
        "ORDER BY rank LIMIT 5"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-1 サンプル（看護師 job_type特有 Top5）:")
        for kw, score, pct in rows:
            print(f"    {kw}: score={score:.4f}, doc_freq={pct:.1f}%")

    # B-1 雇用形態比較: 正職員 vs パートのキーワード差異
    for emp in ["正職員", "パート"]:
        cur.execute(
            "SELECT keyword, tfidf_score FROM layer_b_keywords "
            "WHERE job_type = '看護師' AND layer = 'job_type' AND prefecture = '全国' "
            "AND employment_type = ? "
            "ORDER BY rank LIMIT 3",
            (emp,)
        )
        rows = cur.fetchall()
        if rows:
            print(f"\n  B-1 看護師 job_type特有 [{emp}] Top3:")
            for kw, score in rows:
                print(f"    {kw}: score={score:.4f}")

    # B-2 サンプル: 最大liftペア上位5
    cur.execute(
        "SELECT job_type, flag_a, flag_b, lift, phi_coefficient "
        "FROM layer_b_cooccurrence WHERE employment_type = '全体' ORDER BY lift DESC LIMIT 5"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-2 サンプル（最大lift Top5、全体）:")
        for jt, fa, fb, lift, phi in rows:
            print(f"    {jt}: {fa} x {fb} → lift={lift:.2f}, phi={phi:.3f}")

    # B-3 サンプル: グレードA の全国レベル
    cur.execute(
        "SELECT job_type, entropy_mean, quality_score_mean, benefits_score_mean, grade "
        "FROM layer_b_text_quality WHERE prefecture = '全国' AND grade = 'A' "
        "AND employment_type = '全体' "
        "ORDER BY quality_score_mean DESC LIMIT 5"
    )
    rows = cur.fetchall()
    if rows:
        print("\n  B-3 サンプル（グレードA 全国 Top5、全体）:")
        for jt, ent, qual, ben, grade in rows:
            print(f"    {jt}: entropy={ent:.3f}, quality={qual:.1f}, benefits={ben:.1f}")


def main() -> None:
    """メインエントリポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Layer B: 質的特徴分析")
    parser.add_argument(
        "--job-type", nargs="+", metavar="JT",
        help="対象職種（複数指定可、省略で全職種）例: --job-type 介護職 看護師",
    )
    args, _ = parser.parse_known_args()
    target_jt = args.job_type  # None or list[str]

    # UTF-8出力設定（Windows cp932エラー防止）
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # 全printを即時出力にするため、グローバルprintをオーバーライド
    import builtins
    _original_print = builtins.print

    def flush_print(*args, **kwargs):
        kwargs.setdefault('flush', True)
        try:
            _original_print(*args, **kwargs)
        except UnicodeEncodeError:
            safe_args = []
            for a in args:
                if isinstance(a, str):
                    safe_args.append(a.encode('ascii', errors='replace').decode('ascii'))
                else:
                    safe_args.append(a)
            _original_print(*safe_args, **kwargs)

    builtins.print = flush_print

    print("=" * 60)
    print("Layer B: 質的特徴分析（雇用形態別分離対応 v3.0）")
    print(f"  DB: {DB_PATH}")
    print(f"  雇用形態セグメント: {EMPLOYMENT_TYPES}")
    if target_jt:
        print(f"  対象職種: {target_jt}")
    else:
        print("  対象職種: 全職種")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"エラー: DB ファイルが見つかりません: {DB_PATH}")
        sys.exit(1)

    start_time = time.time()

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB
    conn.execute("BEGIN EXCLUSIVE")
    conn.commit()
    print("  DB排他ロック取得完了")

    try:
        # テーブル再作成（職種指定時はDROPせず既存データに追記）
        if not target_jt:
            print("\n[1/7] テーブル作成（全テーブル再作成）...")
            create_tables(conn, skip_drop=False)
        else:
            print("\n[1/7] テーブル作成（既存テーブル維持、対象職種データのみ削除）...")
            create_tables(conn, skip_drop=True)
            # 指定職種の既存データだけ削除して再計算
            for tbl in ["layer_b_keywords", "layer_b_cooccurrence",
                        "layer_b_text_quality", "layer_b_word_cooccurrence"]:
                for jt in target_jt:
                    conn.execute(f"DELETE FROM [{tbl}] WHERE job_type = ?", (jt,))
            conn.commit()
            print(f"  対象職種の既存データを削除済み")

        # B-1: キーワード3層構造
        print("\n[2/7] B-1: キーワード3層構造（TF-IDF + 類義語辞書）...")
        t1 = time.time()
        b1_count = compute_b1_keywords(conn, target_jt)
        print(f"  完了: {time.time() - t1:.1f}秒")

        # B-2: 条件パッケージ共起
        print("\n[3/7] B-2: 条件パッケージ共起分析...")
        t2 = time.time()
        b2_count = compute_b2_cooccurrence(conn, target_jt)
        print(f"  完了: {time.time() - t2:.1f}秒")

        # B-3: 原稿品質分布
        print("\n[4/7] B-3: 原稿品質分布...")
        t3 = time.time()
        b3_count = compute_b3_text_quality(conn, target_jt)
        print(f"  完了: {time.time() - t3:.1f}秒")

        # B-4: 単語共起分析
        print("\n[5/7] B-4: 単語共起分析（NPMI）...")
        t4 = time.time()
        b4_count = compute_b4_word_cooccurrence(conn, target_jt)
        print(f"  完了: {time.time() - t4:.1f}秒")

        # 重複除去
        print("\n[6/7] 重複除去...")
        deduplicate_tables(conn)

        # インデックス作成
        print("\n[7/7] インデックス作成...")
        create_indexes(conn)

        # 検証
        verify_results(conn)

        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"全処理完了: {elapsed:.1f}秒")
        print(f"  B-1 keywords:          {b1_count:>8,} 行")
        print(f"  B-2 cooccurrence:      {b2_count:>8,} 行")
        print(f"  B-3 text_quality:      {b3_count:>8,} 行")
        print(f"  B-4 word_cooccurrence: {b4_count:>8,} 行")
        print(f"  合計:                  {b1_count + b2_count + b3_count + b4_count:>8,} 行")
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
