# -*- coding: utf-8 -*-
"""
UIで表示されたデータとデータベースの実際の値を照合するスクリプト
main.pyと同じロジックでデータを取得して比較する
"""
import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import main  # main.pyのロジックを使用

# テストした5パターンのUI表示値
UI_VALUES = {
    ("東京都", "千代田区"): {"求職者数": 2026, "平均年齢": 46.9, "男性": 700, "女性": 1326},
    ("東京都", "新宿区"): {"求職者数": 4055, "平均年齢": 46.0, "男性": 1484, "女性": 2571},
    ("東京都", "大田区"): {"求職者数": 3769, "平均年齢": None, "男性": 1321, "女性": 2447},
    ("東京都", "八王子市"): {"求職者数": 1693, "平均年齢": 48.2, "男性": 619, "女性": 1074},
    ("京都府", "京都市中京区"): {"求職者数": 880, "平均年齢": 46.6, "男性": 314, "女性": 566},
}

def verify_municipality_data():
    """各市区町村のデータをmain.pyと同じロジックで取得して比較"""
    print("=" * 80)
    print("データベース値 vs UI表示値 検証レポート")
    print("(main.pyと同じロジック: load_data -> _clean_dataframe -> filter)")
    print("=" * 80)

    # main.pyと同じ方法でデータ取得
    df = main._clean_dataframe(main.load_data())
    print(f"\n[INFO] Loaded DataFrame: {len(df):,} rows")
    print(f"[INFO] Columns: {list(df.columns)}")

    # avg_age列の確認
    if "avg_age" in df.columns:
        print(f"[INFO] avg_age column exists: non-null count = {df['avg_age'].notna().sum()}")
    else:
        print("[WARN] avg_age column NOT found!")

    all_match = True
    results = []

    for (pref, muni), ui_vals in UI_VALUES.items():
        print(f"\n[{pref} {muni}]")
        print("-" * 60)

        # main.pyと同じフィルタリングロジック
        filtered = df.copy()
        filtered = filtered[filtered["prefecture"] == pref]
        filtered = filtered[filtered["municipality"] == muni]

        # main.pyと同じ計算ロジック
        db_total = int(main.safe_sum(filtered, "applicant_count")) if "applicant_count" in filtered.columns else len(filtered)
        db_male = int(main.safe_sum(filtered, "male_count")) if "male_count" in filtered.columns else 0
        db_female = int(main.safe_sum(filtered, "female_count")) if "female_count" in filtered.columns else 0
        db_avg_age = round(main.safe_mean(filtered, "avg_age"), 1) if "avg_age" in filtered.columns else None

        ui_total = ui_vals["求職者数"]
        ui_male = ui_vals["男性"]
        ui_female = ui_vals["女性"]
        ui_avg_age = ui_vals["平均年齢"]

        # 求職者数比較
        match_total = "OK" if db_total == ui_total else "NG"
        if db_total != ui_total:
            all_match = False
        print(f"  求職者数: DB={db_total:,} vs UI={ui_total:,} [{match_total}]")

        # 男性数比較
        match_male = "OK" if db_male == ui_male else "NG"
        if db_male != ui_male:
            all_match = False
        print(f"  男性数:   DB={db_male:,} vs UI={ui_male:,} [{match_male}]")

        # 女性数比較
        match_female = "OK" if db_female == ui_female else "NG"
        if db_female != ui_female:
            all_match = False
        print(f"  女性数:   DB={db_female:,} vs UI={ui_female:,} [{match_female}]")

        # 平均年齢比較
        if ui_avg_age is None:
            print(f"  平均年齢: DB={db_avg_age} vs UI=データなし [SKIP]")
        elif db_avg_age is None or db_avg_age == 0:
            print(f"  平均年齢: DB={db_avg_age} vs UI={ui_avg_age} [NG - DBから取得不可]")
            all_match = False
        else:
            match_age = "OK" if abs(float(db_avg_age) - float(ui_avg_age)) < 0.15 else "NG"
            if match_age == "NG":
                all_match = False
            print(f"  平均年齢: DB={db_avg_age:.1f} vs UI={ui_avg_age:.1f} [{match_age}]")

        # フィルタ結果の詳細
        print(f"  [DEBUG] filtered rows: {len(filtered)}")
        if len(filtered) > 0 and "avg_age" in filtered.columns:
            ages = filtered["avg_age"].dropna()
            if len(ages) > 0:
                print(f"  [DEBUG] avg_age values in filtered: {ages.tolist()[:5]}...")

        results.append({
            "pref": pref,
            "muni": muni,
            "db_total": db_total,
            "ui_total": ui_total,
            "db_male": db_male,
            "ui_male": ui_male,
            "db_female": db_female,
            "ui_female": ui_female,
            "db_avg_age": db_avg_age,
            "ui_avg_age": ui_avg_age,
        })

    print("\n" + "=" * 80)
    if all_match:
        print("結果: 全データ一致!")
    else:
        print("結果: 不一致があります。詳細を確認してください。")
    print("=" * 80)

    # サマリーテーブル
    print("\n[Summary Table]")
    print("-" * 120)
    print(f"{'場所':<25} {'DB合計':>10} {'UI合計':>10} {'DB男':>8} {'UI男':>8} {'DB女':>8} {'UI女':>8} {'DB年齢':>8} {'UI年齢':>8} {'結果':>6}")
    print("-" * 120)
    for r in results:
        loc = f"{r['pref']} {r['muni']}"
        all_ok = (r['db_total'] == r['ui_total'] and
                  r['db_male'] == r['ui_male'] and
                  r['db_female'] == r['ui_female'])
        if r['ui_avg_age'] is not None and r['db_avg_age'] is not None:
            all_ok = all_ok and abs(r['db_avg_age'] - r['ui_avg_age']) < 0.15
        ok = "OK" if all_ok else "NG"
        db_age_str = f"{r['db_avg_age']:.1f}" if r['db_avg_age'] else "-"
        ui_age_str = f"{r['ui_avg_age']:.1f}" if r['ui_avg_age'] else "-"
        print(f"{loc:<25} {r['db_total']:>10,} {r['ui_total']:>10,} {r['db_male']:>8,} {r['ui_male']:>8,} {r['db_female']:>8,} {r['ui_female']:>8,} {db_age_str:>8} {ui_age_str:>8} {ok:>6}")
    print("-" * 120)

    return all_match

if __name__ == "__main__":
    verify_municipality_data()
