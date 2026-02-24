#!/usr/bin/env python3
"""
全職種横断セグメント分類レポート生成

classified_*.csv を読み込み、Tier1/2/3の分布を全職種横断で分析するレポートを出力する。
"""

import os
import sys
import io
from collections import Counter
from pathlib import Path

import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRAPING_DIR = Path(
    r"C:\Users\fuji1\OneDrive\デスクトップ\pythonスクリプト置き場\ジョブメドレースクレイピング"
)

TIER1_LABELS = {
    "A1": "完全未経験歓迎", "A2": "未経験可(資格有)", "A3": "軽度経験(1-2年)",
    "A4": "即戦力経験者", "A5": "復職・ブランク",
    "B1": "新卒・第二新卒", "B2": "若手成長層", "B3": "ミドル層",
    "B4": "シニア層", "B5": "年齢不問・幅広い",
    "C1": "フルタイム・キャリア", "C2": "WLB重視", "C3": "子育て両立",
    "C4": "Wワーク・短時間", "C5": "安定・長期就業",
    "D1": "収入アップ", "D2": "安定性・規模", "D3": "理念・やりがい",
    "D4": "職場環境", "D5": "利便性", "D6": "成長・スキルUP", "D7": "条件・待遇",
    "E1": "緊急大量採用", "E2": "積極採用", "E3": "通常採用",
    "E4": "厳選採用", "E5": "静かな募集",
}

COLS_TO_READ = [
    "tier1_experience", "tier1_career_stage", "tier1_lifestyle",
    "tier1_appeal", "tier1_urgency",
    "tier2_experience", "tier2_career_stage", "tier2_lifestyle",
    "tier2_appeal", "tier2_urgency", "tier2_combined",
    "tier3_id", "tier3_label_short", "tier3_match_score",
    "employment_type", "tags", "benefits_score",
    "required_experience_years", "annual_holidays",
]


def load_all():
    """全classified CSVを読み込み"""
    all_data = []
    job_summaries = []

    for f in sorted(os.listdir(SCRAPING_DIR)):
        if not f.startswith("classified_") or not f.endswith(".csv"):
            continue
        job_type = f.replace("classified_", "").replace("_20260215.csv", "")
        fp = SCRAPING_DIR / f

        try:
            df = pd.read_csv(fp, encoding="utf-8-sig", usecols=COLS_TO_READ, low_memory=False)
        except Exception as e:
            print(f"SKIP {job_type}: {e}", file=sys.stderr)
            continue

        df["_job_type"] = job_type
        n = len(df)
        if n == 0:
            continue

        summary = {
            "job_type": job_type,
            "count": n,
            "top_A": df["tier1_experience"].mode().iloc[0],
            "top_B": df["tier1_career_stage"].mode().iloc[0],
            "top_C": df["tier1_lifestyle"].mode().iloc[0],
            "top_D": df["tier1_appeal"].mode().iloc[0],
            "top_E": df["tier1_urgency"].mode().iloc[0],
            "A1_pct": (df["tier1_experience"] == "A1").sum() / n * 100,
            "A4_pct": (df["tier1_experience"] == "A4").sum() / n * 100,
            "A5_pct": (df["tier1_experience"] == "A5").sum() / n * 100,
            "C2_pct": (df["tier1_lifestyle"] == "C2").sum() / n * 100,
            "C4_pct": (df["tier1_lifestyle"] == "C4").sum() / n * 100,
            "D6_pct": (df["tier1_appeal"] == "D6").sum() / n * 100,
            "E2_pct": (df["tier1_urgency"] == "E2").sum() / n * 100,
            "dict_match_pct": (df["tier3_match_score"] > 0).sum() / n * 100,
            "avg_benefits": df["benefits_score"].mean(),
            "正職員_pct": (df["employment_type"] == "正職員").sum() / n * 100,
            "パート_pct": (df["employment_type"] == "パート・バイト").sum() / n * 100,
        }
        job_summaries.append(summary)
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)
    return combined, job_summaries


def generate_report(combined, job_summaries, out_path):
    """レポート生成"""
    total = len(combined)

    with open(out_path, "w", encoding="utf-8") as out:
        def p(text=""):
            print(text)
            out.write(text + "\n")

        p("=" * 80)
        p("ジョブメドレー求人 セグメント分類レポート")
        p(f"生成日: 2026-02-15 | 全 {len(job_summaries)} 職種 | {total:,} 件")
        p("=" * 80)

        # ===== 1. 全体Tier1分布 =====
        p("\n" + "=" * 80)
        p("1. Tier1 (大分類) 全体分布")
        p("=" * 80)

        tier1_cols = [
            ("tier1_experience", "軸A: 経験レベル"),
            ("tier1_career_stage", "軸B: キャリアステージ"),
            ("tier1_lifestyle", "軸C: ライフスタイル"),
            ("tier1_appeal", "軸D: 訴求軸"),
            ("tier1_urgency", "軸E: 採用緊急度"),
        ]

        for col, label in tier1_cols:
            p(f"\n  {label}")
            dist = combined[col].value_counts().sort_index()
            for val, count in dist.items():
                pct = count / total * 100
                bar = "#" * int(pct / 2)
                lbl = TIER1_LABELS.get(val, val)
                p(f"    {val} {lbl:<18} {count:>8,} ({pct:5.1f}%) {bar}")

        # ===== 2. 職種別プロファイル =====
        p("\n" + "=" * 80)
        p("2. 職種別プロファイル (件数順, 最頻Tier1コード)")
        p("=" * 80)
        header = f"  {'職種':<26} {'件数':>7} {'A':>3} {'B':>3} {'C':>3} {'D':>3} {'E':>3} {'辞書%':>6} {'正職%':>5} {'福利':>4}"
        p(header)
        p("  " + "-" * 73)
        for s in sorted(job_summaries, key=lambda x: -x["count"]):
            p(f"  {s['job_type']:<26} {s['count']:>7,} "
              f"{s['top_A']:>3} {s['top_B']:>3} {s['top_C']:>3} "
              f"{s['top_D']:>3} {s['top_E']:>3} "
              f"{s['dict_match_pct']:>5.1f}% "
              f"{s['正職員_pct']:>4.0f}% "
              f"{s['avg_benefits']:>4.1f}")

        # ===== 3. 未経験歓迎度ランキング =====
        p("\n" + "=" * 80)
        p("3. 未経験歓迎度ランキング (A1率)")
        p("=" * 80)
        sorted_a1 = sorted(job_summaries, key=lambda x: -x["A1_pct"])
        for i, s in enumerate(sorted_a1):
            bar = "#" * int(s["A1_pct"] / 2)
            marker = ""
            if s["A1_pct"] >= 70:
                marker = " << 超未経験歓迎"
            elif s["A1_pct"] < 20:
                marker = " << 経験者重視"
            p(f"  {i+1:2d}. {s['job_type']:<26} {s['A1_pct']:5.1f}% {bar}{marker}")

        # ===== 4. 即戦力需要ランキング =====
        p("\n" + "=" * 80)
        p("4. 即戦力需要ランキング (A4率)")
        p("=" * 80)
        sorted_a4 = sorted(job_summaries, key=lambda x: -x["A4_pct"])
        for i, s in enumerate(sorted_a4[:20]):
            bar = "#" * int(s["A4_pct"])
            p(f"  {i+1:2d}. {s['job_type']:<26} {s['A4_pct']:5.1f}% {bar}")

        # ===== 5. WLB重視度ランキング =====
        p("\n" + "=" * 80)
        p("5. WLB重視度ランキング (C2率)")
        p("=" * 80)
        sorted_c2 = sorted(job_summaries, key=lambda x: -x["C2_pct"])
        for i, s in enumerate(sorted_c2):
            bar = "#" * int(s["C2_pct"] / 2)
            p(f"  {i+1:2d}. {s['job_type']:<26} {s['C2_pct']:5.1f}% {bar}")

        # ===== 6. Wワーク・短時間率ランキング =====
        p("\n" + "=" * 80)
        p("6. Wワーク・短時間率ランキング (C4率)")
        p("=" * 80)
        sorted_c4 = sorted(job_summaries, key=lambda x: -x["C4_pct"])
        for i, s in enumerate(sorted_c4[:20]):
            bar = "#" * int(s["C4_pct"] / 2)
            p(f"  {i+1:2d}. {s['job_type']:<26} {s['C4_pct']:5.1f}% {bar}")

        # ===== 7. Tier2 組み合わせ Top30 =====
        p("\n" + "=" * 80)
        p("7. Tier2 組み合わせ Top30 (全職種横断)")
        p("=" * 80)
        combined_dist = combined["tier2_combined"].value_counts()
        p(f"  ユニーク組み合わせ数: {len(combined_dist):,}\n")
        for i, (val, count) in enumerate(combined_dist.head(30).items()):
            pct = count / total * 100
            p(f"  {i+1:2d}. {val:<30} {count:>8,} ({pct:4.1f}%)")

        # ===== 8. Tier3 パターン分布 Top30 =====
        p("\n" + "=" * 80)
        p("8. Tier3 パターン分布 Top30 (全職種横断)")
        p("=" * 80)
        dict_matched = combined[combined["tier3_match_score"] > 0]
        dict_total = len(dict_matched)
        fb_total = total - dict_total
        p(f"  辞書マッチ: {dict_total:,} ({dict_total/total*100:.1f}%)")
        p(f"  フォールバック: {fb_total:,} ({fb_total/total*100:.1f}%)\n")
        tier3_dist = combined["tier3_id"].value_counts()
        for i, (val, count) in enumerate(tier3_dist.head(30).items()):
            pct = count / total * 100
            label_row = combined[combined["tier3_id"] == val].iloc[0]
            short = label_row.get("tier3_label_short", "")
            p(f"  {i+1:2d}. {val:<22} {count:>8,} ({pct:4.1f}%) [{short}]")

        # ===== 9. タグ出現頻度 =====
        p("\n" + "=" * 80)
        p("9. タグ出現頻度 Top25 (全職種横断)")
        p("=" * 80)
        all_tags = []
        for tags_str in combined["tags"].dropna():
            if tags_str:
                all_tags.extend(str(tags_str).split(","))
        tag_counter = Counter(all_tags)
        for tag, count in tag_counter.most_common(25):
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            p(f"  {tag:<20} {count:>8,} ({pct:5.1f}%) {bar}")

        # ===== 10. 雇用形態分布 =====
        p("\n" + "=" * 80)
        p("10. 雇用形態分布 (全職種横断)")
        p("=" * 80)
        emp_dist = combined["employment_type"].value_counts()
        for val, count in emp_dist.head(10).items():
            pct = count / total * 100
            bar = "#" * int(pct / 2)
            label = val if val else "(空)"
            p(f"  {label:<18} {count:>8,} ({pct:5.1f}%) {bar}")

        # ===== 11. 職種クラスタ分析 =====
        p("\n" + "=" * 80)
        p("11. 職種クラスタ分析 (Tier1最頻値による分類)")
        p("=" * 80)

        p("\n  ■ 経験レベル軸(A)")
        for code in ["A1", "A2", "A3", "A4", "A5"]:
            group = [s["job_type"] for s in job_summaries if s["top_A"] == code]
            if group:
                p(f"    {code} {TIER1_LABELS[code]}: {', '.join(group)}")

        p("\n  ■ 訴求軸(D)")
        for code in ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]:
            group = [s["job_type"] for s in job_summaries if s["top_D"] == code]
            if group:
                p(f"    {code} {TIER1_LABELS[code]}: {', '.join(group)}")

        p("\n  ■ ライフスタイル軸(C)")
        for code in ["C1", "C2", "C3", "C4", "C5"]:
            group = [s["job_type"] for s in job_summaries if s["top_C"] == code]
            if group:
                p(f"    {code} {TIER1_LABELS[code]}: {', '.join(group)}")

        # ===== 12. 職種別インサイト =====
        p("\n" + "=" * 80)
        p("12. 職種別インサイト")
        p("=" * 80)

        # 最も未経験歓迎な職種
        most_a1 = max(job_summaries, key=lambda x: x["A1_pct"])
        p(f"\n  最も未経験歓迎: {most_a1['job_type']} (A1率 {most_a1['A1_pct']:.1f}%)")

        # 最も即戦力重視な職種
        most_a4 = max(job_summaries, key=lambda x: x["A4_pct"])
        p(f"  最も即戦力重視: {most_a4['job_type']} (A4率 {most_a4['A4_pct']:.1f}%)")

        # 最もWLB重視な職種
        most_c2 = max(job_summaries, key=lambda x: x["C2_pct"])
        p(f"  最もWLB重視: {most_c2['job_type']} (C2率 {most_c2['C2_pct']:.1f}%)")

        # 最もWワーク率の高い職種
        most_c4 = max(job_summaries, key=lambda x: x["C4_pct"])
        p(f"  最もWワーク率高: {most_c4['job_type']} (C4率 {most_c4['C4_pct']:.1f}%)")

        # 最も福利厚生が充実
        most_benefits = max(job_summaries, key=lambda x: x["avg_benefits"])
        p(f"  最も福利厚生充実: {most_benefits['job_type']} (平均スコア {most_benefits['avg_benefits']:.1f})")

        # 最も正職員率の高い職種
        most_seisha = max(job_summaries, key=lambda x: x["正職員_pct"])
        p(f"  最も正職員率高: {most_seisha['job_type']} (正職員率 {most_seisha['正職員_pct']:.1f}%)")

        # 最もパート率の高い職種
        most_part = max(job_summaries, key=lambda x: x["パート_pct"])
        p(f"  最もパート率高: {most_part['job_type']} (パート率 {most_part['パート_pct']:.1f}%)")

        p("\n" + "=" * 80)
        p("レポート終了")
        p("=" * 80)

    print(f"\nレポート保存: {out_path}")


def main():
    print("データ読み込み中...")
    combined, job_summaries = load_all()
    report_path = SCRAPING_DIR / "segment_report_20260215.txt"
    generate_report(combined, job_summaries, report_path)


if __name__ == "__main__":
    main()
