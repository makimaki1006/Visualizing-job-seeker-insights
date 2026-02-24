# -*- coding: utf-8 -*-
"""
求人データパーシング共通モジュール

ジョブメドレーのスクレイピングCSVからデータを解析するための関数群。
generate_competitive_report.py と nicegui_app からの共有利用を想定。
"""

import re
from statistics import median, mode, StatisticsError

import pandas as pd

# 全角数字→半角変換用
ZEN_TO_HAN = str.maketrans("０１２３４５６７８９", "0123456789")

# DB統一名とスクレイピング元職種名のマッピング
JOB_TYPE_MAPPING = {
    "看護師・准看護師": "看護師",
    "介護職・ヘルパー": "介護職",
    "保育補助": "保育士",
    "幼稚園教諭": "保育士",
    "管理栄養士・栄養士": "栄養士",
    "放課後児童支援員・学童指導員": "学童支援",
    "調理師・調理スタッフ": "調理師、調理スタッフ",
    # "管理職（介護）": "介護職",  # 2026-02-17 除外（管理職データはダッシュボード対象外）
    "ケアマネジャー": "ケアマネジャー",
    "サービス提供責任者": "サービス提供責任者",
    "サービス管理責任者": "サービス管理責任者",
    "生活相談員": "生活相談員",
    "理学療法士": "理学療法士",
    "作業療法士": "作業療法士",
    "歯科衛生士": "歯科衛生士",
    "薬剤師": "薬剤師",
    "保健師": "保健師",
    "助産師": "助産師",
    "言語聴覚士": "言語聴覚士",
    "臨床検査技師": "臨床検査技師",
    "臨床工学技士": "臨床工学技士",
    "診療放射線技士": "診療放射線技士",
    "視能訓練士": "視能訓練士",
    "柔道整復師": "柔道整復師",
    "鍼灸師": "鍼灸師",
    "あん摩マッサージ指圧師": "あん摩マッサージ指圧師",
    "整体師": "整体師",
    "美容師": "美容師",
    "理容師": "理容師",
    "美容部員": "美容部員",
    "アイリスト": "アイリスト",
    "歯科技工士": "歯科技工士",
    "看護助手": "看護助手",
    "生活支援員": "生活支援員",
    "児童指導員": "児童指導員",
    "児童発達支援管理責任者": "児童発達支援管理責任者",
    "福祉用具専門相談員": "福祉用具専門相談員",
}


def normalize_number_text(text: str) -> str:
    """全角数字を半角に変換"""
    if not isinstance(text, str):
        return ""
    return text.translate(ZEN_TO_HAN)


def parse_access(access_text: str) -> tuple[str, str, str]:
    """アクセス文字列から都道府県・市区町村・住所を抽出

    Returns:
        (都道府県, 市区町村, 残りの住所)
    """
    if not isinstance(access_text, str) or not access_text.strip():
        return ("", "", "")

    text = access_text.strip()

    # 「車通勤可」「駅近(5分以内)」等のプレフィックスを除去
    text = re.sub(r"^(車通勤可|駅近\([^)]*\))\s*", "", text)
    text = re.sub(r"^(車通勤可|駅近\([^)]*\))\s*", "", text)
    text = text.strip()

    # Step 1: 都道府県を抽出（スペース有無に関わらず）
    pref_m = re.match(r"^(北海道|東京都|(?:大阪|京都)府|.{1,3}県)", text)
    if pref_m:
        pref = pref_m.group(1)
        rest = text[len(pref):].strip()

        # Step 2: 市区町村を抽出
        # 政令指定都市（XX市YY区）
        muni_m = re.match(r"^(.+?市.+?区)", rest)
        if not muni_m:
            # 郡（XX郡YY町/村）
            muni_m = re.match(r"^(.+?郡.+?[町村])", rest)
        if not muni_m:
            # 一般市区町村
            muni_m = re.match(r"^(.+?[市区町村])", rest)

        if muni_m:
            muni = muni_m.group(1)
            addr = rest[len(muni):].strip()
            return (pref, muni, addr)

        # 市区町村パターンに一致しない場合、スペース区切りで分割
        parts = rest.split(None, 1)
        if parts:
            return (pref, parts[0], parts[1] if len(parts) > 1 else "")
        return (pref, "", "")

    # 都道府県パターンに一致しない場合のフォールバック
    parts = text.split(None, 2)
    if len(parts) >= 2:
        return (parts[0], parts[1], parts[2] if len(parts) > 2 else "")

    return (text, "", "")


def parse_base_salary(bikou_text: str) -> str:
    """給与の備考から基本給を抽出"""
    if not isinstance(bikou_text, str):
        return ""
    text = normalize_number_text(bikou_text)

    patterns = [
        r"基本給\s*[：:\s]*[¥￥]?\s*([0-9,]+)\s*円?",
        r"基本給\s+([0-9,]+)\s*円",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).replace(",", "")
    return ""


def parse_qualification_allowance(bikou_text: str) -> str:
    """給与の備考から資格手当を抽出"""
    if not isinstance(bikou_text, str):
        return ""
    text = normalize_number_text(bikou_text)

    m = re.search(r"資格手当\s*[：:\s]*[¥￥]?\s*([0-9,]+)\s*円?", text)
    if m:
        return m.group(1).replace(",", "")
    return ""


def parse_other_allowances(bikou_text: str) -> str:
    """給与の備考から資格手当以外の手当を抽出（複数あれば / 区切り）"""
    if not isinstance(bikou_text, str):
        return ""
    text = normalize_number_text(bikou_text)

    matches = re.findall(
        r"([^\s・\n]+手当)\s*[：:\s]*[¥￥]?\s*([0-9,]+)\s*円?", text
    )

    results = []
    skip_keywords = {"資格手当", "基本給"}
    for name, amount in matches:
        if name not in skip_keywords:
            amt = amount.replace(",", "").strip()
            if amt and amt.isdigit():
                results.append(f"{name} {int(amt):,}円")

    return " / ".join(results) if results else ""


def parse_bonus(taigu_text: str, bikou_text: str) -> str:
    """待遇・給与備考から賞与情報を抽出"""
    combined = ""
    if isinstance(taigu_text, str):
        combined += taigu_text + "\n"
    if isinstance(bikou_text, str):
        combined += bikou_text
    if not combined.strip():
        return ""

    text = normalize_number_text(combined)

    # 賞与月数パターン
    m = re.search(r"賞与.*?([0-9.]+)\s*[ヶヵか箇ケ]?\s*月", text)
    if m:
        months = m.group(1)
        m2 = re.search(r"年\s*([0-9]+)\s*回", text)
        if m2:
            return f"{months}ヶ月（年{m2.group(1)}回）"
        return f"{months}ヶ月"

    if re.search(r"(賞与あり|ボーナス・賞与あり|ボーナスあり)", text):
        m2 = re.search(r"年\s*([0-9]+)\s*回", text)
        if m2:
            return f"あり（年{m2.group(1)}回）"
        return "あり"

    return ""


def parse_annual_holidays(kyujitsu_text: str) -> str:
    """休日テキストから年間休日数を抽出"""
    if not isinstance(kyujitsu_text, str):
        return ""
    text = normalize_number_text(kyujitsu_text)

    patterns = [
        r"年間休日\s*[：:\s]*([0-9]+)\s*日?",
        r"年間休日数\s*[：:\s]*([0-9]+)\s*日?",
        r"年間休日([0-9]+)\s*日",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return ""


EMPLOYMENT_TYPE_NORMALIZE = {
    "正職員": "正社員",
    "正社員": "正社員",
    "パート・バイト": "パート・バイト",
    "パート": "パート・バイト",
    "バイト": "パート・バイト",
    "アルバイト": "パート・バイト",
    "契約職員": "契約職員",
    "契約社員": "契約職員",
    "業務委託": "業務委託",
    "派遣": "派遣",
    "非常勤": "パート・バイト",
    "常勤": "正社員",
}


def clean_employment_type(emp_type: str) -> str:
    """雇用形態から【】を除去し、正規化して返す。無効値は空文字"""
    if not isinstance(emp_type, str):
        return ""
    cleaned = emp_type.replace("【", "").replace("】", "").strip()
    return EMPLOYMENT_TYPE_NORMALIZE.get(cleaned, "")


def truncate_text(text: str, max_len: int = 60) -> str:
    """長いテキストを切り詰め"""
    if not isinstance(text, str):
        return ""
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text


def map_job_type(source_job_type: str) -> str:
    """スクレイピング元の職種名をDB統一名に変換"""
    return JOB_TYPE_MAPPING.get(source_job_type, source_job_type)


def format_yen(value) -> str:
    """数値を通貨表示に変換"""
    try:
        v = int(float(value))
        return f"{v:,}"
    except (ValueError, TypeError):
        return "-"


def escape_html(text: str) -> str:
    """HTMLエスケープ"""
    if not isinstance(text, str):
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def compute_salary_statistics(df: pd.DataFrame) -> dict:
    """月給下限・上限の統計を計算

    Args:
        df: 給与_下限, 給与_上限 カラムを持つDataFrame
    Returns:
        件数, 月給下限/上限の中央値・平均値・最頻値
    """
    stats = {}
    count = len(df)
    stats["件数"] = count

    for col_name, label in [("給与_下限", "月給下限"), ("給与_上限", "月給上限")]:
        if col_name not in df.columns:
            stats[f"{label}_中央値"] = "-"
            stats[f"{label}_平均値"] = "-"
            stats[f"{label}_最頻値"] = "-"
            continue

        values = pd.to_numeric(df[col_name], errors="coerce").dropna()
        # 月給として妥当な範囲（5万以上）のみ統計に含める（時給データを除外）
        int_values = [int(v) for v in values if v >= 50000]
        if not int_values:
            stats[f"{label}_中央値"] = "-"
            stats[f"{label}_平均値"] = "-"
            stats[f"{label}_最頻値"] = "-"
            continue

        stats[f"{label}_中央値"] = f"{int(median(int_values)):,}円"
        stats[f"{label}_平均値"] = f"{int(sum(int_values) / len(int_values)):,}円"

        # 最頻値（1万円単位で丸め）
        rounded = [round(v / 10000) * 10000 for v in int_values]
        try:
            mode_val = mode(rounded)
            stats[f"{label}_最頻値"] = f"{int(mode_val):,}円"
        except StatisticsError:
            stats[f"{label}_最頻値"] = "-"

    return stats


def parse_expected_annual_income(nenshu_text: str) -> int | None:
    """想定年収テキストから金額を抽出（万円単位→円に変換）

    例: "想定年収 350万円〜450万円" → 3500000 (下限値)
        "350" → 3500000
    """
    if not isinstance(nenshu_text, str) or not nenshu_text.strip():
        return None
    text = normalize_number_text(nenshu_text)

    # "350万円〜450万円" パターン
    m = re.search(r"([0-9,]+)\s*万\s*円?", text)
    if m:
        try:
            return int(m.group(1).replace(",", "")) * 10000
        except ValueError:
            pass

    # 純粋な数値（既にCSVで万円単位の場合）
    m = re.search(r"^([0-9,]+)$", text.strip())
    if m:
        try:
            val = int(m.group(1).replace(",", ""))
            # 100以上1000未満なら万円単位と判断
            if 100 <= val < 1000:
                return val * 10000
            # 100万以上なら円単位と判断
            elif val >= 1000000:
                return val
        except ValueError:
            pass

    return None


def check_inexperienced_ok(youken_text: str, kangei_text: str = "") -> bool:
    """応募要件・歓迎要件から未経験OKかどうかを判定

    「未経験可」「未経験OK」「未経験歓迎」等のキーワードで判定。
    """
    combined = ""
    if isinstance(youken_text, str):
        combined += youken_text
    if isinstance(kangei_text, str):
        combined += " " + kangei_text

    if not combined.strip():
        return False

    keywords = ["未経験可", "未経験OK", "未経験ok", "未経験歓迎", "未経験者歓迎",
                "未経験の方", "経験不問", "経験問わず"]
    return any(kw in combined for kw in keywords)


def parse_work_hours_summary(kinmu_text: str) -> str:
    """勤務時間テキストから要約を抽出

    長いテキストから最初の勤務時間パターンを抽出して短縮。
    """
    if not isinstance(kinmu_text, str) or not kinmu_text.strip():
        return ""
    text = normalize_number_text(kinmu_text)

    # "8:30～17:30" のようなパターンを抽出
    m = re.search(r"([0-9]{1,2})[：:]([0-9]{2})\s*[～〜ー-]\s*([0-9]{1,2})[：:]([0-9]{2})", text)
    if m:
        return f"{m.group(1)}:{m.group(2)}-{m.group(3)}:{m.group(4)}"

    # "日勤のみ" "夜勤あり" 等のキーワード
    keywords_found = []
    for kw in ["日勤のみ", "夜勤あり", "夜勤なし", "残業なし", "残業ほぼなし"]:
        if kw in text:
            keywords_found.append(kw)
    if keywords_found:
        return " ".join(keywords_found)

    return truncate_text(text, 40)


# ダッシュボード対象の17職種（main.pyのJOB_TYPE_OPTIONSと同期）
DASHBOARD_JOB_TYPES = [
    "介護職", "看護師", "保育士", "栄養士", "生活相談員",
    "理学療法士", "作業療法士", "ケアマネジャー", "サービス管理責任者",
    "サービス提供責任者", "学童支援", "調理師、調理スタッフ",
    "薬剤師", "言語聴覚士", "児童指導員", "児童発達支援管理責任者", "生活支援員",
]


def is_dashboard_job_type(source_job_type: str) -> bool:
    """スクレイピング職種名がダッシュボード対象かどうかを判定"""
    if source_job_type == "管理職（介護）":
        return False
    db_name = map_job_type(source_job_type)
    return db_name in DASHBOARD_JOB_TYPES


def load_and_process_csv(csv_path) -> pd.DataFrame:
    """スクレイピングCSVを読み込み、解析カラムを追加"""
    from pathlib import Path
    csv_path = Path(csv_path)

    df = pd.read_csv(csv_path, encoding="utf-8-sig", low_memory=False)
    df = df.dropna(how="all")

    # アクセスから都道府県・市区町村を抽出
    parsed = df["アクセス"].apply(parse_access)
    df["_都道府県"] = parsed.apply(lambda x: x[0])
    df["_市区町村"] = parsed.apply(lambda x: x[1])
    df["_住所"] = parsed.apply(lambda x: x[2])
    df["_エリア"] = df["_都道府県"] + " " + df["_市区町村"]

    # 雇用形態クリーン
    df["_雇用形態"] = df["給与_雇用形態"].apply(clean_employment_type)

    # 基本給
    df["_基本給"] = df["給与の備考"].apply(parse_base_salary)

    # 資格手当
    df["_資格手当"] = df["給与の備考"].apply(parse_qualification_allowance)

    # その他手当
    df["_他手当"] = df["給与の備考"].apply(parse_other_allowances)

    # 賞与
    df["_賞与"] = df.apply(
        lambda row: parse_bonus(
            row.get("待遇", ""), row.get("給与の備考", "")
        ),
        axis=1,
    )

    # 年間休日
    df["_年間休日"] = df["休日"].apply(parse_annual_holidays)

    return df
