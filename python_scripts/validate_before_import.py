"""
人口データインポート前セルフレビュースクリプト

READY CSVのデータが既存職種と同等の品質かを検証する。
turso_sync.py import の前に必ず実行すること。

使用方法:
    python validate_before_import.py "MapComplete_児童発達支援管理責任者_READY.csv"
"""
import sys
import os
import argparse
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

# 既存職種の参考値（READY CSVから取得した実績値）
# applicant_count合計 / 入力データ行数 の比率が1.0〜2.0の範囲なら正常
# （居住地ベースでカウントされるため1.0前後が正常、希望勤務地ベースだと5〜10倍になり異常）
EXPECTED_RATIO_RANGE = (0.5, 3.0)

MAPCOMPLETE_DIR = os.path.join(os.path.dirname(__file__), "data", "output_v2", "mapcomplete_complete_sheets")


def load_existing_job_type_stats():
    """既存READY CSVから職種別の統計を取得"""
    stats = {}
    if not os.path.exists(MAPCOMPLETE_DIR):
        return stats

    for f in os.listdir(MAPCOMPLETE_DIR):
        if f.startswith("MapComplete_") and f.endswith("_READY.csv") and "Complete_All" not in f:
            job_type = f.replace("MapComplete_", "").replace("_READY.csv", "")
            try:
                df = pd.read_csv(os.path.join(MAPCOMPLETE_DIR, f), dtype=str, low_memory=False)
                summary = df[df["row_type"] == "SUMMARY"]
                pref_summary = summary[summary["municipality"].isna() | (summary["municipality"] == "")]
                muni_summary = summary[summary["municipality"].notna() & (summary["municipality"] != "")]

                pref_total = pd.to_numeric(pref_summary["applicant_count"], errors="coerce").sum()
                muni_total = pd.to_numeric(muni_summary["applicant_count"], errors="coerce").sum()

                stats[job_type] = {
                    "total_rows": len(df),
                    "summary_rows": len(summary),
                    "pref_applicant_total": pref_total,
                    "muni_applicant_total": muni_total,
                    "row_types": len(df["row_type"].unique()),
                    "prefectures": df["prefecture"].nunique(),
                }
            except Exception:
                pass
    return stats


def validate(csv_path):
    """READY CSVのセルフレビュー"""
    errors = []
    warnings = []

    print("=" * 60)
    print("人口データインポート前セルフレビュー")
    print("=" * 60)
    print(f"対象: {csv_path}")
    print()

    # 1. ファイル読み込み
    df = pd.read_csv(csv_path, dtype=str, low_memory=False)
    job_type = df["job_type"].iloc[0] if "job_type" in df.columns else "不明"
    print(f"職種: {job_type}")
    print(f"行数: {len(df):,}")
    print()

    # 2. 既存職種との比較
    print("[CHECK 1] 既存職種との比較")
    existing = load_existing_job_type_stats()
    if existing:
        summary = df[df["row_type"] == "SUMMARY"]
        pref_summary = summary[summary["municipality"].isna() | (summary["municipality"] == "")]
        muni_summary = summary[summary["municipality"].notna() & (summary["municipality"] != "")]
        pref_total = pd.to_numeric(pref_summary["applicant_count"], errors="coerce").sum()
        muni_total = pd.to_numeric(muni_summary["applicant_count"], errors="coerce").sum()

        print(f"  本職種:")
        print(f"    都道府県SUMMARY合計: {pref_total:,.0f}")
        print(f"    市区町村SUMMARY合計: {muni_total:,.0f}")
        print(f"    比率(市区町村/都道府県): {muni_total/pref_total:.1f}x" if pref_total > 0 else "")
        print()

        # 既存職種の比率を計算
        print(f"  既存職種の参考値:")
        for jt, st in sorted(existing.items()):
            if st["pref_applicant_total"] > 0:
                ratio = st["muni_applicant_total"] / st["pref_applicant_total"]
                print(f"    {jt}: 都道府県={st['pref_applicant_total']:,.0f}, 市区町村={st['muni_applicant_total']:,.0f}, 比率={ratio:.1f}x")

        # 比率チェック: 居住地ベース(1.0x)と希望勤務地ベース(15-60x)を分離
        # 居住地ベース職種のみ参照（2026-03-17以降に処理された職種）
        if pref_total > 0:
            my_ratio = muni_total / pref_total

            # 居住地ベース: 比率が0.8〜1.5の範囲
            # 希望勤務地ベース: 比率が10以上
            residence_based = [(jt, st["muni_applicant_total"] / st["pref_applicant_total"])
                               for jt, st in existing.items()
                               if st["pref_applicant_total"] > 0
                               and st["muni_applicant_total"] / st["pref_applicant_total"] < 3.0]
            desired_based = [(jt, st["muni_applicant_total"] / st["pref_applicant_total"])
                             for jt, st in existing.items()
                             if st["pref_applicant_total"] > 0
                             and st["muni_applicant_total"] / st["pref_applicant_total"] >= 3.0]

            if residence_based:
                print(f"\n  居住地ベース職種: {', '.join(jt for jt, _ in residence_based)}")
            if desired_based:
                print(f"  希望勤務地ベース職種（旧データ）: {', '.join(jt for jt, _ in desired_based)}")

            # 新職種の比率が居住地ベースの範囲外ならエラー
            if my_ratio > 3.0:
                errors.append(
                    f"市区町村/都道府県比率が異常: {my_ratio:.1f}x（居住地ベースなら1.0x前後が正常）"
                    f"→ 希望勤務地ベースでカウントされている可能性"
                )
            elif my_ratio < 0.5:
                warnings.append(f"市区町村/都道府県比率が低い: {my_ratio:.1f}x（データ欠損の可能性）")
    else:
        print("  既存READY CSVなし（比較スキップ）")
    print()

    # 3. 行数の妥当性
    print("[CHECK 2] 行数の妥当性")
    if existing:
        existing_rows = [st["total_rows"] for st in existing.values()]
        avg_rows = sum(existing_rows) / len(existing_rows)
        min_rows = min(existing_rows)
        max_rows = max(existing_rows)
        print(f"  本職種: {len(df):,}行")
        print(f"  既存範囲: {min_rows:,} ~ {max_rows:,}（平均: {avg_rows:,.0f}）")
        if len(df) > max_rows * 1.5:
            errors.append(f"行数が既存最大の1.5倍超: {len(df):,} > {max_rows * 1.5:,.0f}")
        elif len(df) < min_rows * 0.5:
            warnings.append(f"行数が既存最小の半分未満: {len(df):,} < {min_rows * 0.5:,.0f}")
    print()

    # 4. 都道府県数
    print("[CHECK 3] 都道府県数")
    pref_count = df["prefecture"].nunique()
    print(f"  {pref_count}県")
    if pref_count != 47:
        errors.append(f"都道府県数が47でない: {pref_count}")
    print()

    # 5. サンプルデータの妥当性（上位市区町村のapplicant_count）
    print("[CHECK 4] 上位市区町村のapplicant_count")
    summary = df[(df["row_type"] == "SUMMARY") & (df["municipality"].notna()) & (df["municipality"] != "")]
    summary_ac = summary.copy()
    summary_ac["ac"] = pd.to_numeric(summary_ac["applicant_count"], errors="coerce")
    top5 = summary_ac.nlargest(5, "ac")
    for _, r in top5.iterrows():
        print(f"  {r['prefecture']}/{r['municipality']}: {r['applicant_count']}")
    print()

    # 6. データ汚染チェック（前回職種のデータ混入検出）
    print("[CHECK 5] データ汚染チェック")
    if existing:
        current_rt = df["row_type"].value_counts().to_dict()
        suspect_types = ["RESIDENCE_FLOW", "QUALIFICATION_DETAIL", "QUALIFICATION_PERSONA"]
        contamination_found = False
        for jt, st in existing.items():
            if jt == job_type:
                continue
            other_path = os.path.join(MAPCOMPLETE_DIR, f"MapComplete_{jt}_READY.csv")
            if not os.path.exists(other_path):
                continue
            try:
                other_df = pd.read_csv(other_path, dtype=str, low_memory=False)
                other_rt = other_df["row_type"].value_counts().to_dict()
                matches = [rt for rt in suspect_types
                           if current_rt.get(rt, 0) == other_rt.get(rt, 0) and current_rt.get(rt, 0) > 0]
                if len(matches) >= 2:
                    warnings.append(
                        f"データ汚染の疑い: {jt}と {', '.join(matches)} の行数が完全一致"
                        f" → generate_residence_flow.py/generate_qualification_detail.pyが未再生成の可能性"
                    )
                    contamination_found = True
            except Exception:
                pass
        if not contamination_found:
            print("  汚染なし [OK]")
    else:
        print("  既存READY CSVなし（スキップ）")
    print()

    # 7. 結果
    print("=" * 60)
    if errors:
        print(f"[NG] セルフレビュー失敗: {len(errors)}件のエラー")
        for e in errors:
            print(f"  [ERROR] {e}")
        print()
        print("このCSVはインポートしないでください。")
        print("データ生成ロジックの確認が必要です。")
    else:
        print("[OK] セルフレビュー通過")

    if warnings:
        print(f"\n警告: {len(warnings)}件")
        for w in warnings:
            print(f"  [WARN] {w}")

    print("=" * 60)
    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(description="人口データインポート前セルフレビュー")
    parser.add_argument("csv_path", help="READY CSVファイルのパス")
    args = parser.parse_args()

    ok = validate(args.csv_path)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
