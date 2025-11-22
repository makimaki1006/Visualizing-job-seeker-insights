# -*- coding: utf-8 -*-
"""元データのカラム確認スクリプト"""
import pandas as pd
from pathlib import Path

print("=" * 80)
print("元データカラム確認")
print("=" * 80)

# V3 CSV確認
v3_path = Path("MapComplete_Complete_All_FIXED.csv")
if v3_path.exists():
    print("\n【V3 CSV】")
    df_v3 = pd.read_csv(v3_path, encoding='utf-8-sig', low_memory=False, nrows=100)
    print(f"カラム数: {len(df_v3.columns)}")
    print("\nカラム一覧:")
    for i, col in enumerate(df_v3.columns, 1):
        print(f"  {i:2d}. {col}")

# 元の生CSV確認（out/results_*.csv）
out_dir = Path("C:/Users/fuji1/OneDrive/Pythonスクリプト保管/out")
if out_dir.exists():
    print(f"\n{'=' * 80}")
    print("【元の生CSV検索】")
    print("=" * 80)

    csv_files = list(out_dir.glob("results_*.csv"))

    if csv_files:
        latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
        print(f"\n最新ファイル: {latest_csv.name}")

        df_raw = pd.read_csv(latest_csv, encoding='utf-8-sig', low_memory=False, nrows=100)
        print(f"カラム数: {len(df_raw.columns)}")
        print("\nカラム一覧:")
        for i, col in enumerate(df_raw.columns, 1):
            print(f"  {i:2d}. {col}")

        # 重要カラムの存在確認
        print(f"\n{'=' * 80}")
        print("【要件に必要なカラムの存在確認】")
        print("=" * 80)

        required_cols = {
            "資格情報": ["資格", "qualification", "qualifications", "保有資格"],
            "学歴情報": ["学歴", "education", "最終学歴"],
            "希望勤務地（複数）": ["希望勤務地", "desired_work", "希望エリア", "希望市区町村"],
            "居住地": ["居住地", "residence", "現住所", "居住市区町村"],
            "通勤距離許容": ["通勤距離", "commute_distance", "移動距離", "通勤時間"],
            "年齢": ["年齢", "age"],
            "性別": ["性別", "gender", "sex"],
        }

        for category, possible_names in required_cols.items():
            found = []
            for col in df_raw.columns:
                for name in possible_names:
                    if name.lower() in col.lower():
                        found.append(col)
                        break

            if found:
                print(f"\n✅ {category}: {', '.join(found)}")
            else:
                print(f"\n❌ {category}: 該当カラムなし")

        # サンプルデータ表示（最初の3行）
        print(f"\n{'=' * 80}")
        print("【サンプルデータ（最初の3行）】")
        print("=" * 80)

        # 資格・学歴・希望勤務地・居住地関連のカラムのみ表示
        display_cols = []
        for col in df_raw.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in
                   ['資格', 'qualification', '学歴', 'education',
                    '希望', 'desired', '居住', 'residence',
                    '通勤', 'commute', '年齢', 'age', '性別', 'gender']):
                display_cols.append(col)

        if display_cols:
            print(df_raw[display_cols].head(3).to_string())
        else:
            print("関連カラムが見つかりません")

    else:
        print("元の生CSVファイルが見つかりません")
else:
    print(f"\noutディレクトリが見つかりません: {out_dir}")

print("\n" + "=" * 80)
print("確認完了")
print("=" * 80)
