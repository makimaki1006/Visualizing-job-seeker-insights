#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_complete_v3.py（暫定版フル分析スクリプト）

目的:
- 元CSV（results_*.csv 相当）を読み、正規化・分解・集約の基本処理を行う。
- 辞書（dims）を base+overlay で読み、未マッチは pending に出力（実行のたび育つ）。
- 正規化結果の明細CSVを出力（経験職種・資格・学歴・勤務形態・希望時期）。

注意:
- 本スクリプトは暫定版。既存の run_complete_v2_perfect.py の全Phaseを置き換えるものではありません。
- まずは項目別の正規化と構造化にフォーカスしています。
"""

import argparse
import json
import os
import re
import sys
import unicodedata as ud
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import pandas as pd
import numpy as np

from dims_manager import DimsManager


def run_v2_full_pipeline(csv_path: Path) -> Optional[Path]:
    """V2のアナライザ＋シートジェネレータを呼び出して、
    data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv を生成する。
    戻り値は生成先パス（存在しなければ None）。
    """
    try:
        # V2 Analyzer を動かす
        # Add parent directory to path for v2 import
        parent_dir = Path(__file__).parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))

        # Add python_scripts directory for v2 dependencies (data_normalizer, etc.)
        scripts_dir = Path(__file__).parent.parent.parent / 'python_scripts'
        if scripts_dir.exists() and str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        import run_complete_v2_perfect as v2
        print("[V2] Analyzer 起動…")
        analyzer = v2.PerfectJobSeekerAnalyzer(str(csv_path))
        analyzer.load_data()
        analyzer.process_data()
        analyzer.export_phase1()
        analyzer.export_phase2()
        analyzer.export_phase3()
        analyzer.export_phase6()
        analyzer.export_phase7()
        analyzer.export_phase8()
        analyzer.export_phase10()
        analyzer.export_phase12()
        analyzer.export_phase13()
        analyzer.export_phase14()
        analyzer.generate_overall_quality_report()

        # 新規パターン生成（40+フィルター、5都道府県フィルター適用済み）
        try:
            print("[V2] 新規パターンデータ生成中...")
            scripts_dir = Path(__file__).parent.parent.parent / 'python_scripts'
            if scripts_dir.exists():
                sys.path.insert(0, str(scripts_dir))
                try:
                    from generate_desired_area_pattern import generate_desired_area_pattern
                    from generate_residence_flow import generate_residence_flow
                    from generate_mobility_pattern import generate_mobility_pattern

                    print("[V2] DESIRED_AREA_PATTERN生成（40+/5都道府県フィルター）...")
                    generate_desired_area_pattern()

                    print("[V2] RESIDENCE_FLOW生成...")
                    generate_residence_flow()

                    print("[V2] MOBILITY_PATTERN生成...")
                    generate_mobility_pattern()

                    print("[V2] 新規パターン生成完了 ✅")
                except Exception as e:
                    print(f"[WARN] パターン生成エラー（スキップ）: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[WARN] python_scriptsディレクトリが見つかりません: {scripts_dir}")
        except (ValueError, IOError) as e:
            # stdout already closed or other IO error
            pass

        # V2 Generator を動かす
        print("[V2] MapComplete 統合CSV生成…")
        from generate_mapcomplete_complete_sheets import MapCompleteCompleteSheetGenerator
        gen = MapCompleteCompleteSheetGenerator()  # 既定: data/output_v2
        gen.load_all_phases()
        gen.generate_complete_sheets()

        out = Path("data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv")
        return out if out.exists() else None
    except Exception as e:
        print(f"[V2] 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return None


def select_input_file_interactively() -> Optional[Path]:
    """UIダイアログでCSVを選択（V2互換）。tkinterが無ければコンソール入力にフォールバック。"""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="解析対象のCSVを選択してください",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(Path.home()),
        )
        root.update()
        root.destroy()
        return Path(path) if path else None
    except Exception:
        # フォールバック: コンソール入力
        print("[INPUT] 解析対象のCSVパスを入力してください（例: C:\\path\\to\\file.csv）")
        s = input("> ").strip()
        return Path(s) if s else None


def select_output_dir_interactively(default_base: Optional[Path] = None) -> Path:
    """出力先ディレクトリをUIで選択。未選択時は自動で時刻付きフォルダを作成。"""
    default_base = default_base or Path.cwd()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_dir = default_base / f"v3_out_{ts}"
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        chosen = filedialog.askdirectory(title="出力先フォルダを選択してください", initialdir=str(default_base))
        root.update()
        root.destroy()
        out = Path(chosen) if chosen else auto_dir
        out.mkdir(parents=True, exist_ok=True)
        return out
    except Exception:
        # フォールバック: 自動ディレクトリ
        auto_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OUTDIR] UI未使用のため自動作成: {auto_dir}")
        return auto_dir


def norm_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    return ud.normalize("NFKC", str(s)).replace("\u3000", " ").strip()


SEP_PATTERN = re.compile(r"[、，,\|／/・\u00B7\u2027\u2219]+")


def split_tokens(s: Optional[str]) -> List[str]:
    t = norm_text(s)
    if not t:
        return []
    t = SEP_PATTERN.sub(",", t)
    return [x.strip() for x in t.split(",") if x.strip()]


YEAR_RE = re.compile(r"(?<!\d)(19|20)\d{2}(?!\d)")


def parse_graduation_year(s: Optional[str]) -> Optional[int]:
    t = norm_text(s)
    if not t:
        return None
    m = YEAR_RE.search(t)
    if m:
        try:
            return int(m.group(0))
        except Exception:
            return None
    return None


def normalize_education(text: Optional[str], dims: DimsManager) -> Tuple[Optional[str], Optional[str], Optional[int], str]:
    """学歴/専攻/卒年を柔軟に抽出。欠損許容。confidence を返す。"""
    t = norm_text(text)
    if not t:
        return None, None, None, "low"

    # レベル判定（辞書: education_levels / fields）
    level_code = dims.match("education_levels", t)
    field_code = dims.match("fields", t)
    year = parse_graduation_year(t)

    hits = sum(x is not None for x in [level_code, field_code, year])
    if hits >= 2:
        conf = "high"
    elif hits == 1:
        conf = "medium"
    else:
        conf = "low"
    return level_code, field_code, year, conf


YEARS_RE = re.compile(r"(\d+)(?:年|yr|years?)")


def _months_from_phrase(p: str) -> Tuple[Optional[int], str]:
    p = norm_text(p)
    # 10年以上 / 5年未満 / 1年未満 / N年
    if "年以上" in p:
        m = YEARS_RE.search(p)
        if m:
            y = int(m.group(1))
            return y * 12, ">=%dy" % y
        return None, ">=10y"
    if "未満" in p:
        m = YEARS_RE.search(p)
        if m:
            y = int(m.group(1))
            # 上限未満：バケットにのみ反映
            return None, f"< {y}y"
        return None, "<1y"
    m = YEARS_RE.search(p)
    if m:
        y = int(m.group(1))
        return y * 12, f"{y}y"
    return None, "unknown"


def parse_experienced_jobs(text: Optional[str], dims: DimsManager) -> List[Dict[str, object]]:
    """経験職種トークンを分解し、辞書でコード化＋期間（月/バケット）を抽出。"""
    out: List[Dict[str, object]] = []
    for tok in split_tokens(text):
        # パターン: "職種 (期間)" を想定（括弧有無は柔軟に）
        job = tok
        dur = ""
        if "(" in tok and ")" in tok:
            try:
                job = tok[: tok.index("(")].strip()
                dur = tok[tok.index("(") + 1 : tok.rindex(")")].strip()
            except Exception:
                job = tok
        code = dims.match("job_titles", job) or job  # 未マッチは原文
        months, bucket = _months_from_phrase(dur)
        out.append({"job_code": code, "months": months, "bucket": bucket})
    return out


# =============================================================
# V3 単独統合のための正規化・解析ヘルパー（V2依存撤廃）
# =============================================================

JP_PREFECTURES = [
    '北海道','青森県','岩手県','宮城県','秋田県','山形県','福島県',
    '茨城県','栃木県','群馬県','埼玉県','千葉県','東京都','神奈川県',
    '新潟県','富山県','石川県','福井県','山梨県','長野県','岐阜県',
    '静岡県','愛知県','三重県','滋賀県','京都府','大阪府','兵庫県',
    '奈良県','和歌山県','鳥取県','島根県','岡山県','広島県','山口県',
    '徳島県','香川県','愛媛県','高知県','福岡県','佐賀県','長崎県',
    '熊本県','大分県','宮崎県','鹿児島県','沖縄県'
]


def parse_age_gender_fields(row: pd.Series) -> Tuple[Optional[int], Optional[str]]:
    age = row.get('age')
    gender = row.get('gender')
    if pd.notna(age):
        try:
            age = int(float(age))
        except Exception:
            age = None
    if isinstance(gender, str):
        g = norm_text(gender)
        if g in ('男','男性','M','male','Male'):
            gender = '男性'
        elif g in ('女','女性','F','female','Female'):
            gender = '女性'
        else:
            gender = None

    if age is None or gender is None:
        ag = row.get('age_gender') or row.get('年齢性別') or ''
        t = norm_text(ag)
        if t:
            m = re.search(r"(\d+).*?(男性|女性)", t)
            if m:
                try:
                    age = int(m.group(1))
                except Exception:
                    pass
                gender = '男性' if '男性' in m.group(2) else '女性'
    return age, gender


def age_bucket_10y(age: Optional[int]) -> Optional[str]:
    if age is None or pd.isna(age):
        return None
    try:
        a = int(age)
    except Exception:
        return None
    if a < 30:
        return '20代'
    if a < 40:
        return '30代'
    if a < 50:
        return '40代'
    if a < 60:
        return '50代'
    if a < 70:
        return '60代'
    return '70歳以上'


def parse_location(text: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    t = norm_text(text)
    if not t:
        return None, None
    for pref in JP_PREFECTURES:
        if t.startswith(pref):
            muni = t[len(pref):] if len(t) > len(pref) else ''
            return pref, muni
    return None, None


def detect_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    for cand in candidates:
        for col in df.columns:
            if str(cand).lower() in str(col).lower():
                return col
    return None


def build_processed(df: pd.DataFrame, dims: DimsManager) -> pd.DataFrame:
    """rawから必要列を正規化して1テーブル化"""
    col_loc = detect_column(df, [
        'location','居住地','住所','所在地','現住所','居住エリア','居住地域',
        '現住所（都道府県+市区町村）','居住（都道府県+市区町村）'
    ])
    col_desired_area = detect_column(df, [
        'desired_area','希望勤務地','希望エリア','希望地域','第1希望勤務地','志望勤務地',
        '希望勤務地（都道府県+市区町村）'
    ])
    col_qual = detect_column(df, [
        'qualifications','資格','保有資格','免許','免許・資格','資格（カンマ区切り）'
    ])
    col_ws = detect_column(df, [
        'desired_workstyle','勤務形態','勤務形態（希望）','希望雇用形態','雇用形態（希望）'
    ])
    col_start = detect_column(df, [
        'desired_start','転職希望時期','入社希望時期','就業可能時期','転職時期','希望開始時期'
    ])
    col_emp = detect_column(df, [
        'employment_status','就業状態','就業状況','在職状況','職業状態','雇用状況'
    ])
    col_job = detect_column(df, [
        'experienced_job','desired_job','経験職種','職務経験','経験業務','経験ポジション'
    ])
    col_career = detect_column(df, [
        'career','学歴','最終学歴','卒業校','専攻','学科','コース'
    ])

    rows = []
    for idx, r in df.iterrows():
        age, gender = parse_age_gender_fields(r)
        age_bkt = age_bucket_10y(age)

        residence_pref, residence_muni = (None, None)
        if col_loc:
            residence_pref, residence_muni = parse_location(r.get(col_loc))

        desired_tokens: List[Dict[str,str]] = []
        if col_desired_area:
            text = r.get(col_desired_area)
            for tok in split_tokens(text):
                pref, muni = parse_location(tok)
                if pref:
                    desired_tokens.append({'prefecture': pref, 'municipality': muni, 'full': f"{pref}{muni}"})

        quals_list = []
        if col_qual:
            for tok in split_tokens(r.get(col_qual)):
                q = dims.match('qualifications', tok) or tok
                quals_list.append(q)
        qualification_count = len(quals_list)

        has_national = 0
        for q in quals_list:
            qt = norm_text(q)
            if any(k in qt for k in ['国家','看護師','介護福祉士','保育士','薬剤師','医師','理学療法士','作業療法士']):
                has_national = 1
                break

        employment_status = norm_text(r.get(col_emp)) if col_emp else ''
        desired_workstyle = norm_text(r.get(col_ws)) if col_ws else ''
        desired_start = norm_text(r.get(col_start)) if col_start else ''
        desired_job = norm_text(r.get(col_job)) if col_job else ''
        career_text = r.get(col_career)

        rows.append({
            'id': r.get('id') or r.get('candidate_id') or r.get('applicant_id') or idx,
            'age': age,
            'gender': gender or '',
            'age_bucket': age_bkt or '',
            'residence_pref': residence_pref or '',
            'residence_muni': residence_muni or '',
            'desired_areas': desired_tokens,
            'qualification_count': qualification_count,
            'qualifications': quals_list,
            'has_national_license': has_national,
            'employment_status': employment_status,
            'desired_workstyle': desired_workstyle,
            'desired_start': desired_start,
            'desired_job': desired_job,
            'career': norm_text(career_text),
        })

    return pd.DataFrame(rows)


def finalize_columns(df_all: pd.DataFrame) -> pd.DataFrame:
    final_cols = [
        'row_type','prefecture','municipality','category1','category2','category3',
        'applicant_count','avg_age','male_count','female_count','avg_qualifications',
        'latitude','longitude','count','avg_desired_areas','employment_rate',
        'national_license_rate','has_national_license','avg_mobility_score',
        'total_in_municipality','market_share_pct','avg_urgency_score',
        'inflow','outflow','net_flow','demand_count','supply_count','gap',
        'demand_supply_ratio','rarity_score','total_applicants','top_age_ratio',
        'female_ratio','male_ratio','top_employment_ratio','avg_qualification_count',
    ]
    for c in final_cols:
        if c not in df_all.columns:
            df_all[c] = np.nan
    return df_all[final_cols]


def safe_div(a: float, b: float) -> float:
    try:
        if b and float(b) != 0:
            return float(a) / float(b)
    except Exception:
        pass
    return 0.0


def build_rowtypes_from_processed(proc: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []

    # SUMMARY（目的地ベース）
    summary = {}
    for _, r in proc.iterrows():
        for area in r['desired_areas']:
            key = (area['prefecture'], area['municipality'])
            s = summary.setdefault(key, {
                'count': 0,
                'ages': [],
                'm': 0,
                'f': 0,
                'qual_sum': 0,
                'nat_sum': 0,
                'age_counts': {'20代':0,'30代':0,'40代':0,'50代':0,'60代':0,'70歳以上':0},
            })
            s['count'] += 1
            if r['age'] is not None:
                s['ages'].append(r['age'])
            if r['gender'] == '男性':
                s['m'] += 1
            elif r['gender'] == '女性':
                s['f'] += 1
            s['qual_sum'] += int(r['qualification_count'])
            s['nat_sum'] += int(r['has_national_license'])
            if r['age_bucket']:
                s['age_counts'][r['age_bucket']] = s['age_counts'].get(r['age_bucket'],0) + 1

    for (pref, muni), s in summary.items():
        rows.append({
            'row_type': 'SUMMARY', 'prefecture': pref, 'municipality': muni,
            'category1': '', 'category2': '', 'category3': '',
            'applicant_count': s['count'],
            'avg_age': (np.mean(s['ages']) if s['ages'] else np.nan),
            'male_count': s['m'], 'female_count': s['f'],
            'avg_qualifications': (s['qual_sum']/s['count']) if s['count']>0 else np.nan,
        })

    # AGE_GENDER（目的地ベース）
    ag = {}
    for _, r in proc.iterrows():
        for area in r['desired_areas']:
            key = (area['prefecture'], area['municipality'], r['age_bucket'], r['gender'])
            a = ag.setdefault(key, {'count': 0, 'age_sum': 0.0, 'n': 0})
            a['count'] += 1
            if r['age'] is not None:
                a['age_sum'] += float(r['age'])
                a['n'] += 1
    for (pref, muni, age_bkt, gender), a in ag.items():
        if not age_bkt or not gender:
            continue
        rows.append({
            'row_type': 'AGE_GENDER', 'prefecture': pref, 'municipality': muni,
            'category1': age_bkt, 'category2': gender, 'category3': '',
            'count': a['count'], 'avg_age': (a['age_sum']/a['n']) if a['n']>0 else np.nan,
        })

    # FLOW（居住地↔目的地）
    node = {}
    for _, r in proc.iterrows():
        origin_full = (r['residence_pref'] + r['residence_muni']) if r['residence_pref'] else ''
        for area in r['desired_areas']:
            dest_full = area['prefecture'] + area['municipality']
            if origin_full and dest_full and origin_full != dest_full:
                okey = (r['residence_pref'], r['residence_muni'])
                n = node.setdefault(okey, {'in': 0, 'out': 0})
                n['out'] += 1
                dkey = (area['prefecture'], area['municipality'])
                n2 = node.setdefault(dkey, {'in': 0, 'out': 0})
                n2['in'] += 1
    for (pref, muni), n in node.items():
        rows.append({
            'row_type': 'FLOW', 'prefecture': pref, 'municipality': muni,
            'category1': '', 'category2': '', 'category3': '',
            'inflow': n['in'], 'outflow': n['out'], 'net_flow': n['in'] - n['out'],
        })

    # GAP（需要=目的地出現数、供給=居住者数）
    demand = {}
    for _, r in proc.iterrows():
        for area in r['desired_areas']:
            key = (area['prefecture'], area['municipality'])
            demand[key] = demand.get(key, 0) + 1
    supply = {}
    for _, r in proc.iterrows():
        if r['residence_pref']:
            key = (r['residence_pref'], r['residence_muni'])
            supply[key] = supply.get(key, 0) + 1
    keys = set(list(demand.keys()) + list(supply.keys()))
    for pref, muni in keys:
        d = demand.get((pref, muni), 0)
        s = supply.get((pref, muni), 0)
        rows.append({
            'row_type': 'GAP', 'prefecture': pref, 'municipality': muni,
            'category1': '', 'category2': '', 'category3': '',
            'demand_count': d, 'supply_count': s, 'gap': d - s,
            'demand_supply_ratio': safe_div(d, s),
        })

    # COMPETITION（居住者プロファイル）
    comp = {}
    for _, r in proc.iterrows():
        if not r['residence_pref']:
            continue
        key = (r['residence_pref'], r['residence_muni'])
        c = comp.setdefault(key, {
            'total': 0, 'm': 0, 'f': 0, 'nat': 0, 'qual_sum': 0,
            'age_counts': {'20代':0,'30代':0,'40代':0,'50代':0,'60代':0,'70歳以上':0},
            'emp_counts': {},
        })
        c['total'] += 1
        if r['gender'] == '男性': c['m'] += 1
        if r['gender'] == '女性': c['f'] += 1
        c['nat'] += int(r['has_national_license'])
        c['qual_sum'] += int(r['qualification_count'])
        if r['age_bucket']:
            c['age_counts'][r['age_bucket']] = c['age_counts'].get(r['age_bucket'],0) + 1
        emp = r['employment_status'] or ''
        if emp:
            c['emp_counts'][emp] = c['emp_counts'].get(emp, 0) + 1
    # まず居住地ベースで作成
    for (pref, muni), c in comp.items():
        total = c['total'] if c['total'] else 1
        top_age_group = max(c['age_counts'], key=lambda k: c['age_counts'][k]) if c['age_counts'] else ''
        top_age_ratio = c['age_counts'].get(top_age_group, 0) / total if total else 0
        female_ratio = c['f'] / total if total else 0
        male_ratio = c['m'] / total if total else 0
        national_license_rate = c['nat'] / total if total else 0
        avg_qualification_count = c['qual_sum'] / total if total else 0
        top_emp = ''
        top_emp_ratio = 0.0
        if c['emp_counts']:
            top_emp = max(c['emp_counts'], key=lambda k: c['emp_counts'][k])
            top_emp_ratio = c['emp_counts'][top_emp] / total
        rows.append({
            'row_type': 'COMPETITION', 'prefecture': pref, 'municipality': muni,
            'category1': top_age_group, 'category2': top_emp, 'category3': '',
            'total_applicants': total, 'top_age_ratio': top_age_ratio,
            'female_ratio': female_ratio, 'male_ratio': male_ratio,
            'national_license_rate': national_license_rate,
            'top_employment_ratio': top_emp_ratio,
            'avg_qualification_count': avg_qualification_count,
        })

    # SUMMARYにある全municipalityを網羅（足りないCOMPETITIONはフォールバックで補完）
    for (pref, muni), s in summary.items():
        if (pref, muni) in comp:
            continue
        total = s['count'] if s['count'] else 0
        if total <= 0:
            total = 0
        female_ratio = (s['f']/s['count']) if s['count'] else 0
        male_ratio = (s['m']/s['count']) if s['count'] else 0
        national_license_rate = (s['nat_sum']/s['count']) if s['count'] else 0
        avg_qualification_count = (s['qual_sum']/s['count']) if s['count'] else 0
        top_age_group = max(s['age_counts'], key=lambda k: s['age_counts'][k]) if s['age_counts'] else ''
        top_age_ratio = (s['age_counts'].get(top_age_group,0)/s['count']) if s['count'] else 0
        rows.append({
            'row_type': 'COMPETITION', 'prefecture': pref, 'municipality': muni,
            'category1': top_age_group, 'category2': '', 'category3': '',
            'total_applicants': s['count'], 'top_age_ratio': top_age_ratio,
            'female_ratio': female_ratio, 'male_ratio': male_ratio,
            'national_license_rate': national_license_rate,
            'top_employment_ratio': 0.0,
            'avg_qualification_count': avg_qualification_count,
        })

    # RARITY（V2準拠）：目的地ベース（希望勤務地）× 年齢バケット × 性別 × 国家資格有無
    rarity_counts = {}
    for _, r in proc.iterrows():
        if not r['age_bucket'] or not r['gender']:
            continue
        for area in r['desired_areas']:
            key = (area['prefecture'], area['municipality'], r['age_bucket'], r['gender'], int(r['has_national_license']))
            rarity_counts[key] = rarity_counts.get(key, 0) + 1

    def rarity_rank_from_score(score: float) -> str:
        # V2のしきい値: 1/count をスコアにして閾値でランク
        # S: >=1.0 (1人のみ), A: >=0.5 (〜2人), B: >=0.2 (〜5人), C: >=0.05 (〜20人), D: その他
        if score >= 1.0:
            return 'S'
        if score >= 0.5:
            return 'A'
        if score >= 0.2:
            return 'B'
        if score >= 0.05:
            return 'C'
        return 'D'

    for (pref, muni, age_bkt, gender, has_nat), cnt in rarity_counts.items():
        score = 1.0 / float(cnt)
        rank = rarity_rank_from_score(score)
        rows.append({
            'row_type': 'RARITY', 'prefecture': pref, 'municipality': muni,
            'category1': age_bkt, 'category2': gender, 'category3': rank,
            'count': cnt, 'rarity_score': score,
            'has_national_license': has_nat,
        })

    # URGENCY（V2 Phase10相当）: 目的地ベース
    def urgency_score(bucket: Optional[str], stale: Optional[bool]) -> float:
        base = 0.0
        if bucket == 'now':
            base = 10.0
        elif bucket == '<=3m':
            base = 7.5
        elif bucket == 'consider':
            base = 2.5
        else:
            base = 0.0
        if stale:
            base *= 0.5
        return base

    urg_age = {}
    urg_emp = {}
    for _, r in proc.iterrows():
        bucket, asof, stale = parse_desired_start(r.get('desired_start'))
        score = urgency_score(bucket, stale)
        for area in r['desired_areas']:
            # 年齢クロス
            if r['age_bucket']:
                k1 = (area['prefecture'], area['municipality'], r['age_bucket'])
                s = urg_age.setdefault(k1, {'sum': 0.0, 'cnt': 0})
                s['sum'] += score
                s['cnt'] += 1
            # 就業クロス
            emp = r['employment_status'] or ''
            if emp:
                k2 = (area['prefecture'], area['municipality'], emp)
                s2 = urg_emp.setdefault(k2, {'sum': 0.0, 'cnt': 0})
                s2['sum'] += score
                s2['cnt'] += 1

    for (pref, muni, age_bkt), agg in urg_age.items():
        avg = (agg['sum']/agg['cnt']) if agg['cnt']>0 else 0.0
        rows.append({
            'row_type': 'URGENCY_AGE', 'prefecture': pref, 'municipality': muni,
            'category1': '', 'category2': age_bkt, 'category3': '',
            'count': agg['cnt'], 'avg_urgency_score': avg,
        })

    for (pref, muni, emp), agg in urg_emp.items():
        avg = (agg['sum']/agg['cnt']) if agg['cnt']>0 else 0.0
        rows.append({
            'row_type': 'URGENCY_EMPLOYMENT', 'prefecture': pref, 'municipality': muni,
            'category1': '', 'category2': emp, 'category3': '',
            'count': agg['cnt'], 'avg_urgency_score': avg,
        })

    return pd.DataFrame(rows)


def normalize_qualifications(text: Optional[str], dims: DimsManager) -> Tuple[List[Dict[str, str]], Optional[str]]:
    codes: List[Dict[str, str]] = []
    other_txt: List[str] = []
    for tok in split_tokens(text):
        base = tok
        # その他（…）は other_txt へ
        if base.startswith("その他"):
            other_txt.append(base)
            continue
        code = dims.match("qualifications", base)
        if code is None:
            # 未マッチは原文で code として保持（後で辞書に昇格可能）
            codes.append({"code": base, "family": "", "national": ""})
        else:
            # family/national は辞書に載っていれば使う。無ければ空。
            meta = dims.maps.get("qualifications", {}).get("canon", {}).get(code, {})
            codes.append({
                "code": code,
                "family": meta.get("family", ""),
                "national": meta.get("national", ""),
            })
    return codes, ("; ".join(other_txt) if other_txt else None)


def normalize_workstyle(text: Optional[str], dims: DimsManager) -> List[str]:
    out: List[str] = []
    for tok in split_tokens(text):
        code = dims.match("workstyle", tok) or tok
        out.append(code)
    # 重複排除
    return sorted(list(dict.fromkeys(out)))


ASOF_RE = re.compile(r"\((\d{4}[/-]\d{1,2}[/-]\d{1,2})時点\)")


def parse_desired_start(text: Optional[str], stale_days: int = 90) -> Tuple[Optional[str], Optional[str], Optional[bool]]:
    t = norm_text(text)
    if not t:
        return None, None, None
    # バケット
    if "今すぐ" in t:
        bucket = "now"
    elif "3ヶ月以内" in t:
        bucket = "<=3m"
    elif "機会があれば" in t:
        bucket = "consider"
    else:
        bucket = "unknown"

    asof = None
    m = ASOF_RE.search(t)
    if m:
        asof = m.group(1).replace("/", "-")
    stale = None
    try:
        if asof:
            dt = datetime.strptime(asof, "%Y-%m-%d")
            stale = (datetime.now() - dt) > timedelta(days=stale_days)
    except Exception:
        stale = None
    return bucket, asof, stale


def main():
    p = argparse.ArgumentParser(description="run_complete_v3 (暫定版) — 正規化/分解/集約の試験実装")
    p.add_argument("--input", required=False, help="入力CSV（未指定時はUIで選択/V2互換）")
    p.add_argument("--outdir", required=False, help="出力ディレクトリ（未指定時はUI選択/自動作成）")
    p.add_argument("--dims", required=False, default=str(Path(__file__).parent / "dims"), help="辞書ディレクトリ（base/overlay/pending を含む）")
    p.add_argument("--v2-mapcomplete", required=False, help="既存のV2統合CSV（MapComplete_Complete_All_FIXED.csv など）。指定時はV3統合を生成")
    p.add_argument("--auto-promote", action="store_true", help="未マッチ頻出語をoverlayに自動昇格する")
    args = p.parse_args()

    # 入力ファイル: 未指定ならUIダイアログで選択（V2互換）
    in_path: Optional[Path] = Path(args.input) if args.input else None
    if in_path is None or not in_path.exists():
        print("[UI] 入力CSVを選択します（V2互換）…")
        in_path = select_input_file_interactively()
        if in_path is None or not in_path.exists():
            print("[ERROR] 入力CSVが選択されていません。--input で指定するか、UIで選択してください。")
            return 1

    # 出力ディレクトリ: 未指定ならUIで選択、未選択時は自動作成
    out_dir: Path
    if args.outdir:
        out_dir = Path(args.outdir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        print("[UI] 出力フォルダを選択します（未選択なら自動作成）…")
        out_dir = select_output_dir_interactively(default_base=in_path.parent)

    dims = DimsManager(dims_dir=args.dims, auto_promote=args.auto_promote)

    print("[LOAD] CSV読み込み:", in_path)
    df = pd.read_csv(in_path, encoding="utf-8-sig", low_memory=False)
    total_rows = len(df)
    print(f"  [OK] {total_rows} 行 x {len(df.columns)} 列")

    # ID列の確定
    id_col = None
    for c in ["id", "candidate_id", "applicant_id"]:
        if c in df.columns:
            id_col = c
            break
    if id_col is None:
        df["row_id"] = range(1, total_rows + 1)
        id_col = "row_id"

    # 解析対象列の存在確認
    col_career = next((c for c in ["career", "education", "学歴"] if c in df.columns), None)
    col_desired_job = next((c for c in ["experienced_job", "desired_job", "経験職種"] if c in df.columns), None)
    col_qual = next((c for c in ["qualifications", "資格"] if c in df.columns), None)
    col_workstyle = next((c for c in ["desired_workstyle", "勤務形態"] if c in df.columns), None)
    col_start = next((c for c in ["desired_start", "転職希望時期"] if c in df.columns), None)

    # 出力コンテナ
    rec_jobs: List[Dict[str, object]] = []
    rec_quals: List[Dict[str, object]] = []
    rec_career: List[Dict[str, object]] = []
    rec_workstyle: List[Dict[str, object]] = []
    rec_start: List[Dict[str, object]] = []

    # 行ごと処理
    for _, row in df.iterrows():
        rid = row.get(id_col)
        # career
        if col_career:
            level_code, field_code, year, conf = normalize_education(row.get(col_career), dims)
            rec_career.append({
                "id": rid,
                "education_level_code": level_code or "",
                "education_field_code": field_code or "",
                "graduation_year": int(year) if year else "",
                "edu_confidence": conf,
            })

        # experienced_job
        if col_desired_job:
            ej = parse_experienced_jobs(row.get(col_desired_job), dims)
            for item in ej:
                rec_jobs.append({
                    "id": rid,
                    "job_code": item.get("job_code", ""),
                    "months": item.get("months"),
                    "bucket": item.get("bucket", "unknown"),
                })

        # qualifications
        if col_qual:
            quals, other = normalize_qualifications(row.get(col_qual), dims)
            for q in quals:
                rec_quals.append({
                    "id": rid,
                    "code": q.get("code", ""),
                    "family": q.get("family", ""),
                    "national": q.get("national", ""),
                })
            if other:
                rec_quals.append({"id": rid, "code": "other", "family": "", "national": other})

        # workstyle
        if col_workstyle:
            ws_codes = normalize_workstyle(row.get(col_workstyle), dims)
            for code in ws_codes:
                rec_workstyle.append({"id": rid, "workstyle_code": code})

        # desired_start
        if col_start:
            bucket, asof, stale = parse_desired_start(row.get(col_start))
            rec_start.append({
                "id": rid,
                "desired_start_bucket": bucket or "",
                "desired_start_asof": asof or "",
                "desired_start_stale": stale if stale is not None else "",
            })

    # DataFrame 化して出力（明細）
    if rec_career:
        df_career = pd.DataFrame(rec_career)
        out = out_dir / "v3_career.csv"
        df_career.to_csv(out, index=False, encoding="utf-8-sig")
        print("[OUT]", out)

    if rec_jobs:
        df_jobs = pd.DataFrame(rec_jobs)
        out = out_dir / "v3_experienced_jobs.csv"
        df_jobs.to_csv(out, index=False, encoding="utf-8-sig")
        print("[OUT]", out)

    if rec_quals:
        df_quals = pd.DataFrame(rec_quals)
        out = out_dir / "v3_qualifications.csv"
        df_quals.to_csv(out, index=False, encoding="utf-8-sig")
        print("[OUT]", out)

    if rec_workstyle:
        df_ws = pd.DataFrame(rec_workstyle)
        out = out_dir / "v3_workstyle.csv"
        df_ws.to_csv(out, index=False, encoding="utf-8-sig")
        print("[OUT]", out)

    if rec_start:
        df_start = pd.DataFrame(rec_start)
        out = out_dir / "v3_desired_start.csv"
        df_start.to_csv(out, index=False, encoding="utf-8-sig")
        print("[OUT]", out)

    # 未マッチを pending に出力、auto_promote 有効時は overlay へ昇格
    dims.flush()
    print("[DONE] 正規化/分解の暫定処理を完了しました。")

    # V2パイプライン実行（新しいフィルター適用済み）
    print("\n[V2] V2完全パイプライン実行中（40+/5都道府県フィルター適用）...")
    v2_result = run_v2_full_pipeline(in_path)

    if v2_result and v2_result.exists():
        print(f"\n[SUCCESS] V2パイプライン完了: {v2_result}")

        # 行数確認
        df_check = pd.read_csv(v2_result, encoding='utf-8-sig', low_memory=False)
        print(f"[INFO] 総行数: {len(df_check):,}行")

        # DESIRED_AREA_PATTERN行数確認
        if 'row_type' in df_check.columns:
            dap_count = len(df_check[df_check['row_type'] == 'DESIRED_AREA_PATTERN'])
            print(f"[INFO] DESIRED_AREA_PATTERN: {dap_count:,}行")

        return 0
    else:
        print("[ERROR] V2パイプラインの実行に失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
