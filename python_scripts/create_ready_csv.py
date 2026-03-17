"""
MapComplete READY CSV生成スクリプト

MapComplete_Complete_All_FIXED.csv にjob_type列とID列を追加し、
職種別のREADY CSVを生成する。

使用方法:
    python create_ready_csv.py --job_type "児童発達支援管理責任者"
    python create_ready_csv.py --job_type "歯科衛生士"
"""
import sys
import argparse
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

MAPCOMPLETE_DIR = "data/output_v2/mapcomplete_complete_sheets"


def main():
    parser = argparse.ArgumentParser(description="MapComplete READY CSV生成")
    parser.add_argument("--job_type", type=str, required=True, help="職種名")
    parser.add_argument("--id_start", type=int, default=1, help="ID開始値（デフォルト: 1）")
    args = parser.parse_args()

    src = f"{MAPCOMPLETE_DIR}/MapComplete_Complete_All_FIXED.csv"
    dst = f"{MAPCOMPLETE_DIR}/MapComplete_{args.job_type}_READY.csv"

    print(f"入力: {src}")
    print(f"出力: {dst}")
    print(f"職種: {args.job_type}")
    print()

    df = pd.read_csv(src, dtype=str, low_memory=False)
    print(f"読み込み: {len(df):,}行, 都道府県: {df.prefecture.nunique()}")

    # job_type列追加
    df["job_type"] = args.job_type

    # ID列生成
    df["id"] = range(args.id_start, args.id_start + len(df))

    # 保存
    df.to_csv(dst, index=False, encoding="utf-8-sig")

    print(f"\n完了: {len(df):,}行 → {dst}")
    print(f"都道府県: {df.prefecture.nunique()}")
    print(f"\nrow_type分布:")
    for rt, cnt in df["row_type"].value_counts().head(15).items():
        print(f"  {rt}: {cnt:,}")
    remaining = len(df["row_type"].value_counts()) - 15
    if remaining > 0:
        print(f"  ... 他{remaining}種類")


if __name__ == "__main__":
    main()
