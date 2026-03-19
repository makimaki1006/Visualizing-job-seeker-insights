#!/usr/bin/env python3
"""
職種別データ処理パイプライン

使用方法:
    python process_job_type.py --job_type "看護師" --input "path/to/results_看護師.csv"

処理フロー:
    1. 入力CSV読み込み
    2. V2/V3分析実行（Phase 1-14）
    3. MapComplete統合シート生成
    4. job_type列追加
    5. Tursoインポート（オプション）
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import pandas as pd
import shutil
from datetime import datetime

# 職種とプレフィックスのマッピング
JOB_TYPE_PREFIX_MAP = {
    "介護職": "",
    "看護師": "NS",
    "保育士": "CH",
    "生活相談員": "SW",
    "栄養士": "DT",
    "管理栄養士": "DT",
    "栄養士、管理栄養士": "DT",
}

def run_v2_analysis(input_csv: str, job_type: str):
    """V2分析を実行"""
    print(f"\n{'='*60}")
    print(f"[Step 1] V2/V3分析実行: {job_type}")
    print(f"{'='*60}")

    # V2スクリプトを実行
    cmd = [
        sys.executable,
        "run_complete_v2_perfect.py",
        "--input", input_csv
    ]

    print(f"コマンド: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent,
        capture_output=False
    )

    if result.returncode != 0:
        print(f"[ERROR] V2分析が失敗しました (exit code: {result.returncode})")
        return False

    print("[OK] V2分析完了")
    return True

def run_mapcomplete_generation(job_type: str):
    """MapComplete統合シート生成"""
    print(f"\n{'='*60}")
    print(f"[Step 2] MapComplete統合シート生成: {job_type}")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        "generate_mapcomplete_complete_sheets.py"
    ]

    print(f"コマンド: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=Path(__file__).parent,
        capture_output=False
    )

    if result.returncode != 0:
        print(f"[ERROR] MapComplete生成が失敗しました (exit code: {result.returncode})")
        return False

    print("[OK] MapComplete生成完了")
    return True

def add_job_type_column(job_type: str, id_prefix: str):
    """job_type列とIDプレフィックスを追加"""
    print(f"\n{'='*60}")
    print(f"[Step 3] job_type列とIDプレフィックス追加")
    print(f"{'='*60}")

    # ファイルパス
    base_path = Path(__file__).parent / "data" / "output_v2" / "mapcomplete_complete_sheets"
    input_file = base_path / "MapComplete_Complete_All_FIXED.csv"
    output_file = base_path / f"MapComplete_{job_type}_READY.csv"

    if not input_file.exists():
        print(f"[ERROR] ファイルが見つかりません: {input_file}")
        return None

    print(f"入力ファイル: {input_file}")
    df = pd.read_csv(input_file, dtype=str, low_memory=False)
    print(f"読み込み行数: {len(df):,}")

    # job_type列を追加
    df['job_type'] = job_type
    print(f"job_type列追加: '{job_type}'")

    # IDプレフィックスを追加
    if 'id' not in df.columns:
        df['id'] = range(1, len(df) + 1)

    if id_prefix:
        print(f"IDプレフィックス追加: {id_prefix}_")
        df['id'] = df['id'].apply(lambda x: f"{id_prefix}_{x}" if not str(x).startswith(id_prefix) else x)

    # 保存
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"出力ファイル: {output_file}")
    print(f"出力行数: {len(df):,}")

    # サンプル確認
    print(f"\nサンプルID (先頭5件):")
    for i, id_val in enumerate(df['id'].head(5)):
        print(f"  {i+1}: {id_val}")

    return str(output_file)

def run_turso_import(csv_path: str, job_type: str, id_prefix: str, dry_run: bool = False):
    """Tursoインポート実行"""
    print(f"\n{'='*60}")
    print(f"[Step 4] Tursoインポート: {job_type}")
    print(f"{'='*60}")

    nicegui_app_dir = Path(__file__).parent.parent / "nicegui_app"
    import_script = nicegui_app_dir / "turso_job_type_import.py"

    if not import_script.exists():
        print(f"[ERROR] インポートスクリプトが見つかりません: {import_script}")
        return False

    cmd = [
        sys.executable,
        str(import_script),
        "--job_type", job_type,
        "--id_prefix", id_prefix,
        "--csv_path", csv_path
    ]

    if dry_run:
        cmd.append("--dry_run")

    print(f"コマンド: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=nicegui_app_dir,
        capture_output=False
    )

    if result.returncode != 0:
        print(f"[ERROR] Tursoインポートが失敗しました (exit code: {result.returncode})")
        return False

    print("[OK] Tursoインポート完了")
    return True

def main():
    parser = argparse.ArgumentParser(description='職種別データ処理パイプライン')
    parser.add_argument('--job_type', type=str, required=True,
                        help='職種名 (例: 看護師, 保育士)')
    parser.add_argument('--input', type=str, required=True,
                        help='入力CSVファイルのパス')
    parser.add_argument('--skip_v2', action='store_true',
                        help='V2分析をスキップ（既に実行済みの場合）')
    parser.add_argument('--skip_mapcomplete', action='store_true',
                        help='MapComplete生成をスキップ')
    parser.add_argument('--skip_turso', action='store_true',
                        help='Tursoインポートをスキップ')
    parser.add_argument('--dry_run', action='store_true',
                        help='ドライラン（インポートを実行しない）')
    args = parser.parse_args()

    job_type = args.job_type
    input_csv = args.input
    id_prefix = JOB_TYPE_PREFIX_MAP.get(job_type, '')

    print("=" * 60)
    print(f"職種別データ処理パイプライン")
    print(f"  職種: {job_type}")
    print(f"  入力: {input_csv}")
    print(f"  IDプレフィックス: {id_prefix or '(なし)'}")
    print(f"  ドライラン: {args.dry_run}")
    print("=" * 60)

    start_time = datetime.now()

    # Step 1: V2分析
    if not args.skip_v2:
        if not run_v2_analysis(input_csv, job_type):
            print("[ABORT] V2分析で失敗しました")
            sys.exit(1)
    else:
        print("[SKIP] V2分析をスキップ")

    # Step 2: MapComplete生成
    if not args.skip_mapcomplete:
        if not run_mapcomplete_generation(job_type):
            print("[ABORT] MapComplete生成で失敗しました")
            sys.exit(1)
    else:
        print("[SKIP] MapComplete生成をスキップ")

    # Step 3: job_type列追加
    ready_csv = add_job_type_column(job_type, id_prefix)
    if not ready_csv:
        print("[ABORT] job_type列追加で失敗しました")
        sys.exit(1)

    # Step 4: Tursoインポート
    if not args.skip_turso:
        if not run_turso_import(ready_csv, job_type, id_prefix, args.dry_run):
            print("[ABORT] Tursoインポートで失敗しました")
            sys.exit(1)
    else:
        print("[SKIP] Tursoインポートをスキップ")

    # 完了
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    print(f"[完了] 職種別データ処理パイプライン")
    print(f"  職種: {job_type}")
    print(f"  処理時間: {elapsed}")
    print(f"  出力ファイル: {ready_csv}")
    print("=" * 60)

if __name__ == "__main__":
    main()
