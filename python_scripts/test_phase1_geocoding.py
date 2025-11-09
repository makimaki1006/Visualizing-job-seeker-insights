"""
Phase 1.5: ジオコーチング機能のチェック。
`run_complete_v2_perfect.PerfectJobSeekerAnalyzer` を使って
MapMetrics.csv が正しく生成されるか手動検証するためのスクリプト。

pytest から呼び出される場合は何も実行しない（__main__ ガード）。
"""

from pathlib import Path
from run_complete_v2_perfect import PerfectJobSeekerAnalyzer


def main() -> None:
    # 最新のテスト用データパス（環境に合わせて差し替え）
    csv_path = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251028_112441.csv")

    if not csv_path.exists():
        print(f"エラー: ファイルが見つかりません: {csv_path}")
        return

    print("=" * 80)
    print("Phase 1.5: ジオコーチング機能チェック")
    print("=" * 80)
    print()

    analyzer = PerfectJobSeekerAnalyzer(str(csv_path))
    analyzer.load_data()
    analyzer.export_phase1()

    print()
    print("=" * 80)
    print("Phase 1 完了 - MapMetrics.csv を確認")
    print("=" * 80)

    output_dir = Path("data/output_v2/phase1")
    map_metrics_path = output_dir / "MapMetrics.csv"

    if not map_metrics_path.exists():
        print("\nエラー: MapMetrics.csv が生成されませんでした")
        return

    import pandas as pd

    df = pd.read_csv(map_metrics_path, encoding="utf-8-sig")
    print("\nMapMetrics.csv 生成成功:")
    print(f"  総件数: {len(df)}件")
    print(f"  座標あり: {df['緯度'].notna().sum()}件")
    print(f"  座標なし: {df['緯度'].isna().sum()}件")

    print("\n【サンプルデータ（上位5件）】")
    print(df.head(5).to_string())

    df_no_coords = df[df["緯度"].isna()]
    if len(df_no_coords) > 0:
        print("\n【座標が取得できなかった地域（上位5件）】")
        print(df_no_coords[["都道府県", "市区町村", "キー", "希望件数"]].head(5).to_string())


if __name__ == "__main__":
    main()
