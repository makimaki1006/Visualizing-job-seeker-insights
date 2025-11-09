#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新規実装したマスタCSV生成のテストスクリプト

テスト対象:
1. QualificationMaster.csv
2. PrefectureMaster.csv
3. EmploymentStatusMaster.csv
4. PersonaByMunicipality_WithResidence.csv
5. QualificationDistributionByMunicipality.csv
"""

import sys
from pathlib import Path
import pandas as pd

# run_complete_v2_perfect.pyをインポート
from run_complete_v2_perfect import PerfectJobSeekerAnalyzer


def test_master_csv_generation():
    """マスタCSV生成のテスト"""

    print("=" * 80)
    print("新規マスタCSV生成テスト開始")
    print("=" * 80)

    # 1. データファイルのパス
    data_file = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251028_112441.csv")
    if not data_file.exists():
        print(f"❌ エラー: データファイルが見つかりません: {data_file}")
        return False

    print(f"\n✅ データファイル確認: {data_file.name}")

    # 2. アナライザー初期化
    print("\n[1/4] PerfectJobSeekerAnalyzer初期化中...")
    analyzer = PerfectJobSeekerAnalyzer(str(data_file))

    # 3. データ読み込み
    print("[2/4] データ読み込み中...")
    analyzer.load_data()
    print(f"  ✅ {len(analyzer.df)}件のレコードを読み込みました")

    # 4. データ処理
    print("[3/4] データ処理中...")
    analyzer.process_data()
    print(f"  ✅ {len(analyzer.processed_data)}件のレコードを処理しました")

    # 5. Phase 1エクスポート（新しいマスタCSVを含む）
    print("[4/4] Phase 1エクスポート（マスタCSV生成）中...")
    output_dir = Path("data/output_v2_test/phase1")
    analyzer.export_phase1(str(output_dir))

    # 6. 生成されたCSVファイルの確認
    print("\n" + "=" * 80)
    print("生成されたCSVファイルの検証")
    print("=" * 80)

    expected_files = {
        'Applicants.csv': '申請者基本情報（完全版）',
        'DesiredWork.csv': '希望勤務地詳細',
        'AggDesired.csv': '市町村別集計データ',
        'MapMetrics.csv': '地図表示用データ',
        'QualificationMaster.csv': '資格マスタ',
        'PrefectureMaster.csv': '都道府県マスタ（居住地）',
        'EmploymentStatusMaster.csv': '就業状況マスタ',
        'PersonaByMunicipality_WithResidence.csv': '市町村×居住地×ペルソナ',
        'QualificationDistributionByMunicipality.csv': '市町村×資格分布'
    }

    all_files_ok = True

    for filename, description in expected_files.items():
        file_path = output_dir / filename
        if file_path.exists():
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            print(f"\n✅ {filename}")
            print(f"   説明: {description}")
            print(f"   件数: {len(df)}件")
            print(f"   カラム数: {len(df.columns)}個")
            print(f"   カラム一覧: {', '.join(df.columns.tolist())}")

            # 先頭3行をプレビュー表示
            if len(df) > 0:
                print(f"\n   【データプレビュー（先頭3行）】")
                print(df.head(3).to_string(index=False))
        else:
            print(f"\n❌ {filename} - ファイルが見つかりません")
            all_files_ok = False

    # 7. 特定のマスタCSVの詳細検証
    print("\n" + "=" * 80)
    print("新規マスタCSVの詳細検証")
    print("=" * 80)

    # 7-1. QualificationMaster.csv
    qual_master_path = output_dir / 'QualificationMaster.csv'
    if qual_master_path.exists():
        qual_df = pd.read_csv(qual_master_path, encoding='utf-8-sig')
        print("\n[QualificationMaster.csv 詳細]")
        print(f"  総資格数: {len(qual_df)}種類")
        print(f"  国家資格数: {qual_df['is_national_license'].sum()}種類")
        print(f"  一般資格数: {(~qual_df['is_national_license']).sum()}種類")
        print(f"\n  上位5資格:")
        print(qual_df.head(5)[['qualification_name', 'applicant_count', 'is_national_license', 'avg_age']].to_string(index=False))

    # 7-2. PrefectureMaster.csv
    pref_master_path = output_dir / 'PrefectureMaster.csv'
    if pref_master_path.exists():
        pref_df = pd.read_csv(pref_master_path, encoding='utf-8-sig')
        print("\n[PrefectureMaster.csv 詳細]")
        print(f"  総都道府県数: {len(pref_df)}都道府県")
        print(f"  総市町村数: {pref_df['municipality_count'].sum()}市町村")
        print(f"\n  上位5都道府県:")
        print(pref_df.head(5)[['prefecture', 'applicant_count', 'municipality_count']].to_string(index=False))

    # 7-3. EmploymentStatusMaster.csv
    emp_master_path = output_dir / 'EmploymentStatusMaster.csv'
    if emp_master_path.exists():
        emp_df = pd.read_csv(emp_master_path, encoding='utf-8-sig')
        print("\n[EmploymentStatusMaster.csv 詳細]")
        print(f"  就業状況カテゴリ数: {len(emp_df)}種類")
        print(f"\n  全カテゴリ:")
        print(emp_df[['employment_status', 'applicant_count']].to_string(index=False))

    # 7-4. PersonaByMunicipality_WithResidence.csv
    persona_res_path = output_dir / 'PersonaByMunicipality_WithResidence.csv'
    if persona_res_path.exists():
        persona_res_df = pd.read_csv(persona_res_path, encoding='utf-8-sig')
        print("\n[PersonaByMunicipality_WithResidence.csv 詳細]")
        print(f"  総レコード数: {len(persona_res_df)}件")
        print(f"  対象市町村数: {persona_res_df['target_municipality'].nunique()}市町村")
        print(f"  居住都道府県数: {persona_res_df['residence_prefecture'].nunique()}都道府県")
        print(f"\n  サンプル（上位5件）:")
        sample_cols = ['target_municipality', 'age_group', 'gender', 'has_national_license',
                      'residence_prefecture', 'count', 'avg_age']
        print(persona_res_df.head(5)[sample_cols].to_string(index=False))

    # 7-5. QualificationDistributionByMunicipality.csv
    qual_dist_path = output_dir / 'QualificationDistributionByMunicipality.csv'
    if qual_dist_path.exists():
        qual_dist_df = pd.read_csv(qual_dist_path, encoding='utf-8-sig')
        print("\n[QualificationDistributionByMunicipality.csv 詳細]")
        print(f"  総レコード数: {len(qual_dist_df)}件")
        print(f"  対象市町村数: {qual_dist_df['target_municipality'].nunique()}市町村")
        print(f"  資格種類数: {qual_dist_df['qualification_name'].nunique()}種類")
        print(f"\n  サンプル（上位5件）:")
        sample_cols = ['target_municipality', 'qualification_name', 'applicant_count',
                      'avg_age', 'employment_rate']
        print(qual_dist_df.head(5)[sample_cols].to_string(index=False))

    # 8. 最終結果
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)

    if all_files_ok:
        print("✅ すべてのCSVファイルが正常に生成されました")
        print(f"\n出力先: {output_dir.absolute()}")
        return True
    else:
        print("❌ 一部のCSVファイルが生成されませんでした")
        return False


if __name__ == '__main__':
    success = test_master_csv_generation()
    sys.exit(0 if success else 1)
