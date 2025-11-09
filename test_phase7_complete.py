#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 7完全テスト - 新機能含む

run_complete.pyのPhase 7部分を単独実行し、
新しい2つのCSV（PersonaMobilityCross, PersonaMapData）が生成されることを確認
"""

import sys
import pandas as pd
from pathlib import Path
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "python_scripts"))

from phase7_advanced_analysis import run_phase7_analysis

# 簡易マスターデータクラス
class SimpleMaster:
    """テスト用簡易マスターデータ"""
    QUALIFICATIONS = {
        '介護福祉士': ['介護福祉士'],
        '社会福祉士': ['社会福祉士'],
        '精神保健福祉士': ['精神保健福祉士'],
        '介護支援専門員': ['介護支援専門員', 'ケアマネージャー'],
        '理学療法士': ['理学療法士', 'PT'],
        '作業療法士': ['作業療法士', 'OT'],
        '言語聴覚士': ['言語聴覚士', 'ST'],
        '看護師': ['看護師', '正看護師'],
        '准看護師': ['准看護師'],
        '保育士': ['保育士'],
        '栄養士': ['栄養士', '管理栄養士'],
        '調理師': ['調理師'],
        'ヘルパー': ['ホームヘルパー', '初任者研修', '実務者研修']
    }

def main():
    """Phase 7完全テスト実行"""
    print("\n" + "=" * 80)
    print("Phase 7完全テスト開始（新機能含む）")
    print("=" * 80)

    # ステップ1: 既存データ読み込み
    print("\n[ステップ1] データ読み込み...")

    processed_path = Path("processed_data_complete.csv")
    if not processed_path.exists():
        print("[ERROR] processed_data_complete.csv が見つかりません")
        print("  まず run_complete.py を実行してください")
        return 1

    df_processed = pd.read_csv(processed_path, encoding='utf-8-sig')
    print(f"  [OK] df_processed: {len(df_processed)}行")

    # geocache読み込み
    geocache_path = Path("../geocache.json")
    if not geocache_path.exists():
        geocache_path = Path("geocache.json")

    if not geocache_path.exists():
        print("[ERROR] geocache.json が見つかりません")
        return 1

    with open(geocache_path, 'r', encoding='utf-8') as f:
        geocache = json.load(f)
    print(f"  [OK] geocache: {len(geocache)}エントリ")

    # マスターデータ
    master = SimpleMaster()
    print(f"  [OK] master: {len(master.QUALIFICATIONS)}資格カテゴリ")

    # ステップ2: DesiredWork統合（重要！）
    print("\n[ステップ2] DesiredWork統合...")

    desired_work_path = Path("gas_output_phase1/DesiredWork.csv")
    if desired_work_path.exists():
        try:
            desired_work = pd.read_csv(desired_work_path, encoding='utf-8-sig')
            print(f"  [OK] DesiredWork読み込み: {len(desired_work)}行")

            # ID型統一
            df_processed['id'] = df_processed['id'].astype(str)
            desired_work['申請者ID'] = desired_work['申請者ID'].astype(str)

            # ID_プレフィックス処理
            if desired_work['申請者ID'].iloc[0].startswith('ID_'):
                if not df_processed['id'].iloc[0].startswith('ID_'):
                    desired_work['申請者ID'] = desired_work['申請者ID'].str.replace('ID_', '', regex=False)
                    print("  [INFO] DesiredWorkのIDプレフィックス削除")

            # 申請者ごとの希望勤務地リスト作成
            desired_locs_map = {}
            for applicant_id in desired_work['申請者ID'].unique():
                locs = desired_work[
                    desired_work['申請者ID'] == applicant_id
                ]['キー'].tolist()
                desired_locs_map[applicant_id] = locs

            # df_processedに追加
            df_processed['desired_locations_keys'] = df_processed['id'].map(desired_locs_map)
            df_processed['desired_locations_keys'] = df_processed['desired_locations_keys'].apply(
                lambda x: x if isinstance(x, list) else []
            )

            with_locations = (df_processed['desired_locations_keys'].apply(len) > 0).sum()
            print(f"  [OK] 統合完了: {with_locations}/{len(df_processed)}人に希望地データあり")

        except Exception as e:
            print(f"  [WARNING] DesiredWork統合失敗: {e}")
            print("  低精度モードで続行...")
    else:
        print("  [WARNING] DesiredWork.csvが見つかりません")
        print("  低精度モードで続行...")

    # ステップ3: Phase 7分析実行
    print("\n[ステップ3] Phase 7分析実行...")

    try:
        analyzer = run_phase7_analysis(
            df=None,  # 元データは不要
            df_processed=df_processed,
            geocache=geocache,
            master=master,
            output_dir='gas_output_phase7'
        )
        print("  [OK] Phase 7分析完了")
    except Exception as e:
        print(f"  [ERROR] Phase 7分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # ステップ4: 出力ファイル検証
    print("\n[ステップ4] 出力ファイル検証...")

    output_dir = Path("gas_output_phase7")
    expected_files = [
        'SupplyDensityMap.csv',
        'QualificationDistribution.csv',
        'AgeGenderCrossAnalysis.csv',
        'MobilityScore.csv',
        'DetailedPersonaProfile.csv',
        'PersonaMobilityCross.csv',  # NEW
        'PersonaMapData.csv'          # NEW
    ]

    results = []
    for filename in expected_files:
        filepath = output_dir / filename
        if filepath.exists():
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            rows = len(df)
            cols = len(df.columns)
            results.append({
                'file': filename,
                'exists': True,
                'rows': rows,
                'cols': cols,
                'status': '[OK]'
            })
            print(f"  [OK] {filename}: {rows}行 x {cols}列")
        else:
            results.append({
                'file': filename,
                'exists': False,
                'status': '[FAIL]'
            })
            print(f"  [FAIL] {filename}: ファイルが見つかりません")

    # ステップ5: 新機能の詳細検証
    print("\n[ステップ5] 新機能詳細検証...")

    # PersonaMobilityCross.csv検証
    cross_path = output_dir / 'PersonaMobilityCross.csv'
    if cross_path.exists():
        df_cross = pd.read_csv(cross_path, encoding='utf-8-sig')
        print(f"\n  [PersonaMobilityCross.csv]")
        print(f"    行数: {len(df_cross)}行")
        print(f"    カラム: {list(df_cross.columns)}")

        # 検証項目
        checks = []
        checks.append(('ペルソナID列', 'ペルソナID' in df_cross.columns))
        checks.append(('ペルソナ名列', 'ペルソナ名' in df_cross.columns))
        checks.append(('A列', 'A' in df_cross.columns))
        checks.append(('B列', 'B' in df_cross.columns))
        checks.append(('C列', 'C' in df_cross.columns))
        checks.append(('D列', 'D' in df_cross.columns))
        checks.append(('合計列', '合計' in df_cross.columns))
        checks.append(('データ件数', 5 <= len(df_cross) <= 15))

        print("    検証:")
        for name, result in checks:
            status = "[OK]" if result else "[FAIL]"
            print(f"      {status} {name}")

        # サンプルデータ表示
        print("\n    サンプルデータ（上位3件）:")
        print(df_cross.head(3).to_string(index=False))

    # PersonaMapData.csv検証
    map_path = output_dir / 'PersonaMapData.csv'
    if map_path.exists():
        df_map = pd.read_csv(map_path, encoding='utf-8-sig')
        print(f"\n  [PersonaMapData.csv]")
        print(f"    行数: {len(df_map)}行")
        print(f"    カラム: {list(df_map.columns)}")

        # 検証項目
        checks = []
        checks.append(('市区町村列', '市区町村' in df_map.columns))
        checks.append(('緯度列', '緯度' in df_map.columns))
        checks.append(('経度列', '経度' in df_map.columns))
        checks.append(('ペルソナID列', 'ペルソナID' in df_map.columns))
        checks.append(('求職者数列', '求職者数' in df_map.columns))

        if len(df_map) > 0:
            checks.append(('座標欠損なし', df_map['緯度'].notna().all() and df_map['経度'].notna().all()))

        print("    検証:")
        for name, result in checks:
            status = "[OK]" if result else "[FAIL]"
            print(f"      {status} {name}")

        if len(df_map) > 0:
            print("\n    サンプルデータ（上位3件）:")
            print(df_map.head(3).to_string(index=False))

    # 総合結果
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)

    total = len(expected_files)
    success = sum(1 for r in results if r['exists'])

    print(f"\n  生成ファイル: {success}/{total}")
    print(f"  成功率: {success/total*100:.1f}%")

    if success == total:
        print("\n  [SUCCESS] すべてのファイルが正常に生成されました！")
        print("\n  次のステップ:")
        print("    1. GASプロジェクトに以下のファイルをアップロード:")
        print("       - Phase7PersonaMobilityCrossViz.gs")
        print("       - Phase7DataImporter.gs（更新版）")
        print("       - Phase7MenuIntegration.gs（更新版）")
        print("    2. gas_output_phase7/ の7つのCSVをGASにインポート")
        print("    3. メニューから「ペルソナ×移動許容度クロス分析」を実行")
        return 0
    else:
        print(f"\n  [FAIL] {total - success}個のファイルが生成されませんでした")
        return 1

if __name__ == '__main__':
    exit(main())
