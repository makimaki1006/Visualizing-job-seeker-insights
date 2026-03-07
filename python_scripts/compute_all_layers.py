"""
A-C層 一括計算スクリプト

使い方:
  python compute_all_layers.py           # A,B,C全て実行
  python compute_all_layers.py --layer a # A層のみ
  python compute_all_layers.py --layer b # B層のみ
  python compute_all_layers.py --layer c # C層のみ
  python compute_all_layers.py --layer a b  # A+B層
  python compute_all_layers.py --verify  # 結果検証のみ
"""
import argparse
import sqlite3
import sys
import time
import os

DB_PATH = os.environ.get(
    "GEOCODED_DB_PATH",
    r"C:\Users\fuji1\AppData\Local\Temp\rust-dashboard-deploy\data\geocoded_postings.db",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_layer(name, module_name):
    """指定レイヤーの計算を実行"""
    print(f"\n{'='*60}")
    print(f"  Layer {name.upper()} 計算開始")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        mod = __import__(module_name)
        mod.main()
        elapsed = time.time() - t0
        print(f"\n  Layer {name.upper()} 完了 [{elapsed:.1f}秒]")
        return True
    except Exception as e:
        elapsed = time.time() - t0
        print(f"\n  Layer {name.upper()} エラー [{elapsed:.1f}秒]: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_results():
    """全テーブルの結果を検証し、メタデータを記録"""
    print(f"\n{'='*60}")
    print(f"  結果検証")
    print(f"{'='*60}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # メタデータテーブル作成（計算日時・行数を記録）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS layer_metadata (
            layer_name  TEXT NOT NULL,
            table_name  TEXT NOT NULL,
            row_count   INTEGER NOT NULL,
            computed_at TEXT NOT NULL,
            PRIMARY KEY (layer_name, table_name)
        )
    """)
    conn.commit()

    # テーブル名 → レイヤー名のマッピング
    _table_to_layer = {
        "layer_a_salary_stats": "A",
        "layer_a_facility_concentration": "A",
        "layer_a_employment_diversity": "A",
        "layer_b_keywords": "B",
        "layer_b_cooccurrence": "B",
        "layer_b_text_quality": "B",
        "layer_c_clusters": "C",
        "layer_c_cluster_profiles": "C",
        "layer_c_region_heatmap": "C",
    }

    # 元データ件数
    total = cur.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
    job_types = cur.execute(
        "SELECT DISTINCT job_type FROM postings ORDER BY job_type"
    ).fetchall()
    print(f"\n  元データ: {total:,}件, {len(job_types)}職種")

    # 各テーブルの検証
    expected_tables = {
        # Layer A
        "layer_a_salary_stats": "A-1 給与分布",
        "layer_a_facility_concentration": "A-2 法人集中度",
        "layer_a_employment_diversity": "A-3 雇用形態多様性",
        # Layer B
        "layer_b_keywords": "B-1 キーワード",
        "layer_b_cooccurrence": "B-2 共起パターン",
        "layer_b_text_quality": "B-3 原稿品質",
        # Layer C
        "layer_c_clusters": "C-1 クラスタ割当",
        "layer_c_cluster_profiles": "C-1 クラスタプロファイル",
        "layer_c_region_heatmap": "C-1 地域ヒートマップ",
    }

    existing_tables = set(
        r[0]
        for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    )

    print(f"\n  {'テーブル':<38} {'状態':<6} {'行数':>10}")
    print(f"  {'-'*58}")

    all_ok = True
    for table, label in expected_tables.items():
        if table in existing_tables:
            cnt = cur.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
            status = "✅" if cnt > 0 else "⚠️空"
            print(f"  {label} ({table}){' '*(38-len(label)-len(table)-3)} {status:<6} {cnt:>10,}")
            if cnt == 0:
                all_ok = False
            # メタデータ記録（行数と計算日時）
            layer_name = _table_to_layer.get(table, "?")
            cur.execute("""
                INSERT OR REPLACE INTO layer_metadata
                    (layer_name, table_name, row_count, computed_at)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
            """, (layer_name, table, cnt))
        else:
            print(f"  {label} ({table}){' '*(38-len(label)-len(table)-3)} {'❌未作成':<6}")
            all_ok = False

    conn.commit()

    # 追加検証: Layer A サンプル
    if "layer_a_salary_stats" in existing_tables:
        sample = cur.execute(
            "SELECT job_type, prefecture, salary_type, count, mean, median, gini "
            "FROM layer_a_salary_stats WHERE prefecture='全国' AND employment_type='全体' LIMIT 3"
        ).fetchall()
        if sample:
            print(f"\n  --- A-1 サンプル（全国） ---")
            for r in sample:
                print(f"    {r[0]} {r[2]}: {r[3]:,}件, 平均{r[4]:,.0f}, 中央値{r[5]:,.0f}, Gini={r[6]:.3f}")

    # 追加検証: Layer C クラスタ数
    if "layer_c_cluster_profiles" in existing_tables:
        clusters = cur.execute(
            "SELECT job_type, COUNT(*) FROM layer_c_cluster_profiles GROUP BY job_type"
        ).fetchall()
        if clusters:
            print(f"\n  --- C-1 クラスタ数 ---")
            for r in clusters:
                print(f"    {r[0]}: {r[1]}クラスタ")

    conn.close()

    print(f"\n  {'='*58}")
    if all_ok:
        print(f"  総合判定: ✅ 全テーブル正常")
    else:
        print(f"  総合判定: ⚠️ 一部テーブルに問題あり")
    print(f"  {'='*58}")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="A-C層 一括計算")
    parser.add_argument(
        "--layer",
        nargs="*",
        choices=["a", "b", "c"],
        help="計算するレイヤー（省略で全て）",
    )
    parser.add_argument("--verify", action="store_true", help="結果検証のみ")
    args = parser.parse_args()

    if args.verify:
        verify_results()
        return

    layers = args.layer if args.layer else ["a", "b", "c"]

    # sys.pathにスクリプトディレクトリを追加
    if SCRIPT_DIR not in sys.path:
        sys.path.insert(0, SCRIPT_DIR)

    print(f"{'='*60}")
    print(f"  求人市場分析フレームワーク A-C層計算")
    print(f"  DB: {DB_PATH}")
    print(f"  対象: Layer {', '.join(l.upper() for l in layers)}")
    print(f"{'='*60}")

    t_start = time.time()
    results = {}

    layer_modules = {
        "a": "compute_layer_a",
        "b": "compute_layer_b",
        "c": "compute_layer_c",
    }

    for layer in layers:
        results[layer] = run_layer(layer, layer_modules[layer])

    total_elapsed = time.time() - t_start

    # 結果サマリ
    print(f"\n{'='*60}")
    print(f"  計算完了サマリ [{total_elapsed:.1f}秒]")
    print(f"{'='*60}")
    for layer, ok in results.items():
        status = "✅ 成功" if ok else "❌ 失敗"
        print(f"  Layer {layer.upper()}: {status}")

    # 検証実行
    verify_results()


if __name__ == "__main__":
    main()
