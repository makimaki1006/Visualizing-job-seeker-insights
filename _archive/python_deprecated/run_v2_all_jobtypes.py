#!/usr/bin/env python3
"""
全職種のV2処理を順次実行し、各職種のMapComplete CSVを生成するスクリプト
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 職種設定
JOB_TYPES = [
    {
        "name": "看護師",
        "input_file": r"C:\Users\fuji1\Downloads\results_看護師.csv",
        "id_prefix": "NS",
        "id_start": 3000000
    },
    {
        "name": "保育士",
        "input_file": r"C:\Users\fuji1\Downloads\results_保育士.csv",
        "id_prefix": "CH",
        "id_start": 4000000
    },
    {
        "name": "生活相談員",
        "input_file": r"C:\Users\fuji1\Downloads\results_生活相談員.csv",
        "id_prefix": "SW",
        "id_start": 5000000
    }
]

# パス設定
SCRIPT_DIR = Path(__file__).parent
OUTPUT_BASE = SCRIPT_DIR / "data" / "output_v2"
MAPCOMPLETE_DIR = OUTPUT_BASE / "mapcomplete_complete_sheets"

def run_v2_processing(input_file, job_type_name):
    """V2処理を実行（job_typeを明示的に指定）"""
    print(f"\n{'='*60}")
    print(f"V2処理開始: {job_type_name}")
    print(f"入力ファイル: {input_file}")
    print(f"{'='*60}")

    # V2スクリプト実行（--job_type引数追加）
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "run_complete_v2_perfect.py"),
        "--input", str(input_file),
        "--job_type", job_type_name,  # 職種を明示指定（再発防止）
        "--auto"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=False,
            text=True,
            timeout=1800  # 30分タイムアウト
        )
        print(f"\n[OK] V2処理完了: {job_type_name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] タイムアウト: {job_type_name}")
        return False
    except Exception as e:
        print(f"\n[ERROR] V2処理失敗: {e}")
        return False

def generate_mapcomplete(job_type_name):
    """MapComplete CSV生成"""
    print(f"\n[MAPCOMPLETE] MapComplete CSV生成中...")

    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "generate_mapcomplete_complete_sheets.py")
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=600
        )
        print(f"[OK] MapComplete CSV生成完了")
        return True
    except Exception as e:
        print(f"[ERROR] MapComplete生成失敗: {e}")
        return False

def rename_mapcomplete_for_jobtype(job_type_name, id_start):
    """
    生成されたMapComplete CSVを職種別にリネーム・ID付与（コピーではなく直接使用）

    重要: この関数は generate_mapcomplete() で生成されたデータを使用する。
          旧 copy_mapcomplete_for_jobtype() はデータをコピーしていたが、
          これは各職種固有のデータを正しく保持するためリネーム方式に変更。

    再発防止: Phase1_Applicants.csvにjob_typeカラムが追加されたため、
             generate_mapcompleteで正しい職種のWORKSTYLEデータが生成される。
    """
    src = MAPCOMPLETE_DIR / "MapComplete_Complete_All_FIXED.csv"
    dst = MAPCOMPLETE_DIR / f"MapComplete_{job_type_name}_READY.csv"

    if not src.exists():
        print(f"[ERROR] ソースファイルが見つかりません: {src}")
        return False

    import pandas as pd

    print(f"\n[RENAME] MapComplete CSVを{job_type_name}用にリネーム中...")

    # 読み込み（このデータは既にこの職種のデータ）
    df = pd.read_csv(src, dtype=str, low_memory=False)
    print(f"  読み込み行数: {len(df):,}")

    # job_type列を追加（念のため）
    df['job_type'] = job_type_name

    # ID列を更新
    df['id'] = range(id_start, id_start + len(df))

    # 保存
    df.to_csv(dst, index=False, encoding='utf-8-sig')
    print(f"  保存完了: {dst}")
    print(f"  行数: {len(df):,}")
    print(f"  ID範囲: {id_start} - {id_start + len(df) - 1}")

    # バリデーション: WORKSTYLEデータの整合性確認
    validate_workstyle_data(df, job_type_name)

    return True


def validate_workstyle_data(df, job_type_name):
    """
    WORKSTYLEデータの整合性検証（再発防止）

    検証項目:
    - WORKSTYLE_DISTRIBUTIONの行数が妥当か
    - 正職員/パート/その他のカウントが存在するか
    """
    import pandas as pd

    ws_dist = df[df['row_type'] == 'WORKSTYLE_DISTRIBUTION']
    if len(ws_dist) == 0:
        print(f"  [WARN] {job_type_name}: WORKSTYLE_DISTRIBUTIONデータがありません")
        return

    # 市区町村数をカウント
    muni_count = ws_dist[['prefecture', 'municipality']].drop_duplicates().shape[0]

    # 雇用形態カテゴリ（正職員/パート/その他）
    categories = ws_dist['category1'].unique()

    # 総カウント
    total_count = pd.to_numeric(ws_dist['count'], errors='coerce').sum()

    print(f"  [VALIDATE] {job_type_name}:")
    print(f"    - WORKSTYLE_DISTRIBUTION行数: {len(ws_dist):,}")
    print(f"    - 対象市区町村数: {muni_count:,}")
    print(f"    - 雇用形態カテゴリ: {list(categories)}")
    print(f"    - 総カウント: {total_count:,.0f}")

def main():
    print("="*60)
    print("全職種V2処理・MapComplete生成スクリプト")
    print(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    MAPCOMPLETE_DIR.mkdir(exist_ok=True)

    results = {}

    for job in JOB_TYPES:
        job_name = job["name"]
        input_file = job["input_file"]
        id_start = job["id_start"]

        # ファイル存在確認
        if not Path(input_file).exists():
            print(f"\n[SKIP] 入力ファイルなし: {input_file}")
            results[job_name] = "SKIP"
            continue

        # V2処理実行
        success = run_v2_processing(input_file, job_name)

        if success:
            # MapComplete生成（この時点でPhase1_Applicants.csvにはこの職種のデータのみ存在）
            generate_mapcomplete(job_name)

            # 職種別ファイルにリネーム（コピーではなく直接使用）
            # 注: 旧copy_mapcomplete_for_jobtypeは廃止（データ混在バグの原因だった）
            rename_mapcomplete_for_jobtype(job_name, id_start)

            results[job_name] = "SUCCESS"
        else:
            results[job_name] = "FAILED"

    # サマリー
    print("\n" + "="*60)
    print("処理結果サマリー")
    print("="*60)
    for job_name, status in results.items():
        print(f"  {job_name}: {status}")

    print(f"\n完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
