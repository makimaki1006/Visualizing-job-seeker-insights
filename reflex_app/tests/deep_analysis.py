# -*- coding: utf-8 -*-
"""
5 Whys深堀り調査スクリプト

各テストの成功の定義について「なぜ成立するのか？」を5回追求します。
ファクトベースで検証し、推測は排除します。
"""

import pandas as pd
import os
import json

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "MapComplete_Complete_All_FIXED.csv"
)

def analyze_data():
    """CSVデータの徹底分析"""
    print("=" * 70)
    print("5 Whys 深堀り調査 - ファクトベース検証")
    print("=" * 70)

    df = pd.read_csv(CSV_PATH, low_memory=False)
    results = {}

    # =================================================================
    # UT-01: CSVファイルが存在する
    # =================================================================
    print("\n" + "=" * 70)
    print("UT-01: CSVファイルが存在する")
    print("=" * 70)

    file_exists = os.path.exists(CSV_PATH)
    file_size = os.path.getsize(CSV_PATH) if file_exists else 0

    print(f"\n【事実1】ファイルパス: {CSV_PATH}")
    print(f"【事実2】ファイル存在: {file_exists}")
    print(f"【事実3】ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

    print("\n5 Whys:")
    print("Q1: なぜこのテストは成功するのか？")
    print(f"A1: os.path.exists()が{file_exists}を返すため")

    print("\nQ2: なぜos.path.exists()がTrueを返すのか？")
    print(f"A2: 指定パスにファイルが物理的に存在するため")

    print("\nQ3: なぜこのファイルが存在するのか？")
    if file_exists:
        import time
        mtime = os.path.getmtime(CSV_PATH)
        mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        print(f"A3: 最終更新日時 {mod_time} に作成/更新されたため")
    else:
        print("A3: ファイルが存在しない")

    print("\nQ4: このファイルは正しいCSV形式か？")
    try:
        df_check = pd.read_csv(CSV_PATH, nrows=5)
        print(f"A4: 読み込み成功、{len(df_check.columns)}カラム存在")
    except Exception as e:
        print(f"A4: 読み込み失敗 - {e}")

    print("\nQ5: データは空でないか？")
    print(f"A5: {len(df)}行のデータが存在")

    results['UT-01'] = {
        'file_exists': file_exists,
        'file_size_bytes': file_size,
        'row_count': len(df)
    }

    # =================================================================
    # UT-02: 必須カラムが存在する
    # =================================================================
    print("\n" + "=" * 70)
    print("UT-02: 必須カラムが存在する")
    print("=" * 70)

    required_columns = ['row_type', 'prefecture', 'municipality',
                        'applicant_count', 'avg_age', 'female_ratio']

    print(f"\n【事実1】CSVの全カラム数: {len(df.columns)}")
    print(f"【事実2】必須カラム数: {len(required_columns)}")

    for col in required_columns:
        exists = col in df.columns
        non_null = df[col].notna().sum() if exists else 0
        null_pct = (1 - non_null/len(df)) * 100 if exists else 100
        print(f"  - {col}: 存在={exists}, 非NULL行={non_null}, NULL率={null_pct:.1f}%")

    print("\n5 Whys:")
    print("Q1: なぜこのテストは成功するのか？")
    missing = [c for c in required_columns if c not in df.columns]
    print(f"A1: 不足カラム={missing if missing else 'なし'}")

    print("\nQ2: これらのカラムにはデータがあるのか？")
    for col in required_columns:
        if col in df.columns:
            sample = df[col].dropna().iloc[:3].tolist() if df[col].notna().any() else []
            print(f"A2-{col}: サンプル値={sample[:3]}")

    print("\nQ3: カラム名のタイポはないか？")
    print(f"A3: 実際のカラム名リスト:\n{list(df.columns)}")

    print("\nQ4: 必須カラムの定義は正しいか？")
    print("A4: アプリで使用されるカラムとの対応確認が必要")

    print("\nQ5: ダッシュボードで実際に使われるカラムは？")
    print("A5: mapcomplete_dashboard.pyの実装を確認する必要あり")

    results['UT-02'] = {
        'total_columns': len(df.columns),
        'required_found': len([c for c in required_columns if c in df.columns]),
        'missing': missing
    }

    # =================================================================
    # UT-03: row_typeの検証
    # =================================================================
    print("\n" + "=" * 70)
    print("UT-03: すべてのrow_typeが存在する")
    print("=" * 70)

    expected_types = ['FLOW', 'GAP', 'RARITY', 'COMPETITION', 'SUMMARY']
    actual_types = df['row_type'].unique().tolist()

    print(f"\n【事実1】期待するrow_type: {expected_types}")
    print(f"【事実2】実際のrow_type: {actual_types}")

    type_counts = df['row_type'].value_counts().to_dict()
    for rt in actual_types:
        print(f"  - {rt}: {type_counts.get(rt, 0)}行")

    print("\n5 Whys:")
    print("Q1: なぜこのテストは成功するのか？")
    for rt in expected_types:
        exists = rt in actual_types
        count = type_counts.get(rt, 0)
        print(f"A1-{rt}: 存在={exists}, 行数={count}")

    missing_types = [rt for rt in expected_types if rt not in actual_types]
    extra_types = [rt for rt in actual_types if rt not in expected_types]
    print(f"\nQ2: 不足しているrow_typeは？")
    print(f"A2: {missing_types if missing_types else 'なし'}")

    print(f"\nQ3: 予期しないrow_typeは？")
    print(f"A3: {extra_types if extra_types else 'なし'}")

    print("\nQ4: 各row_typeのデータは有効か？")
    for rt in expected_types:
        if rt in actual_types:
            rt_df = df[df['row_type'] == rt]
            prefectures = rt_df['prefecture'].nunique()
            print(f"A4-{rt}: {prefectures}都道府県のデータ")

    print("\nQ5: row_typeはダッシュボードでどう使われるか？")
    print("A5: 各タブでフィルタリングに使用される")

    results['UT-03'] = {
        'expected': expected_types,
        'actual': actual_types,
        'missing': missing_types,
        'extra': extra_types,
        'counts': type_counts
    }

    # =================================================================
    # IT-05: 都道府県変更でデータが異なる
    # =================================================================
    print("\n" + "=" * 70)
    print("IT-05: 都道府県変更でデータが異なることを確認")
    print("=" * 70)

    kyoto_df = df[df['prefecture'] == '京都府']
    osaka_df = df[df['prefecture'] == '大阪府']
    mie_df = df[df['prefecture'] == '三重県']

    print(f"\n【事実1】京都府データ: {len(kyoto_df)}行")
    print(f"【事実2】大阪府データ: {len(osaka_df)}行")
    print(f"【事実3】三重県データ: {len(mie_df)}行")

    kyoto_cities = set(kyoto_df['municipality'].dropna().unique())
    osaka_cities = set(osaka_df['municipality'].dropna().unique())
    mie_cities = set(mie_df['municipality'].dropna().unique())

    print(f"\n京都府市区町村({len(kyoto_cities)}): {list(kyoto_cities)[:5]}...")
    print(f"大阪府市区町村({len(osaka_cities)}): {list(osaka_cities)[:5]}...")
    print(f"三重県市区町村({len(mie_cities)}): {list(mie_cities)[:5]}...")

    print("\n5 Whys:")
    print("Q1: なぜこのテストは成功するのか？")
    overlap_ko = kyoto_cities & osaka_cities
    print(f"A1: 京都府と大阪府の市区町村重複={len(overlap_ko)}件")

    print("\nQ2: 重複があってもデータは異なるか？")
    if overlap_ko:
        for city in list(overlap_ko)[:2]:
            k_count = len(kyoto_df[kyoto_df['municipality'] == city])
            o_count = len(osaka_df[osaka_df['municipality'] == city])
            print(f"A2-{city}: 京都府={k_count}行, 大阪府={o_count}行")
    else:
        print("A2: 重複市区町村なし")

    print("\nQ3: 数値データも異なるか？")
    if 'applicant_count' in df.columns:
        k_total = pd.to_numeric(kyoto_df['applicant_count'], errors='coerce').sum()
        o_total = pd.to_numeric(osaka_df['applicant_count'], errors='coerce').sum()
        m_total = pd.to_numeric(mie_df['applicant_count'], errors='coerce').sum()
        print(f"A3: 応募者数 - 京都府={k_total:.0f}, 大阪府={o_total:.0f}, 三重県={m_total:.0f}")

    print("\nQ4: ダッシュボードで都道府県変更時に正しくフィルタされるか？")
    print("A4: Stateの@rx.var関数で self.selected_prefecture でフィルタしている")

    print("\nQ5: 以前「三重県がずっと表示される」問題があったが、データ自体は正しいか？")
    print(f"A5: データ上は京都府({len(kyoto_df)}行)≠三重県({len(mie_df)}行)で異なる")
    print("    → 問題はデータではなく、Stateの依存関係トラッキングにあった")

    results['IT-05'] = {
        'kyoto_rows': len(kyoto_df),
        'osaka_rows': len(osaka_df),
        'mie_rows': len(mie_df),
        'kyoto_cities': len(kyoto_cities),
        'osaka_cities': len(osaka_cities),
        'mie_cities': len(mie_cities)
    }

    # =================================================================
    # IT-06: FLOWランキングTop10
    # =================================================================
    print("\n" + "=" * 70)
    print("IT-06: FLOWランキングTop10が正しく計算される")
    print("=" * 70)

    flow_df = df[df['row_type'] == 'FLOW'].copy()
    print(f"\n【事実1】FLOWデータ: {len(flow_df)}行")

    if 'net_flow' in flow_df.columns:
        flow_df['net_flow'] = pd.to_numeric(flow_df['net_flow'], errors='coerce')
        valid_net_flow = flow_df['net_flow'].notna().sum()
        print(f"【事実2】net_flow有効行: {valid_net_flow}")

        top10 = flow_df.nlargest(10, 'net_flow')
        print(f"\n【Top10 net_flow】")
        for i, row in top10.iterrows():
            print(f"  {row['prefecture']} {row['municipality']}: net_flow={row['net_flow']}")

        print("\n5 Whys:")
        print("Q1: なぜこのテストは成功するのか？")
        print(f"A1: nlargest(10)が{len(top10)}件を返すため")

        print("\nQ2: net_flow値は数値として正しいか？")
        print(f"A2: 最大={flow_df['net_flow'].max()}, 最小={flow_df['net_flow'].min()}")

        print("\nQ3: 降順ソートは正しいか？")
        values = top10['net_flow'].values
        is_sorted = all(values[i] >= values[i+1] for i in range(len(values)-1))
        print(f"A3: 降順={is_sorted}")

        print("\nQ4: ダッシュボードでこのランキングはどう使われるか？")
        print("A4: フロー分析タブで横棒グラフとして表示される")

        print("\nQ5: 全国データと都道府県フィルタ時で結果は異なるか？")
        kyoto_flow = flow_df[flow_df['prefecture'] == '京都府']
        if len(kyoto_flow) > 0:
            kyoto_top10 = kyoto_flow.nlargest(10, 'net_flow')
            print(f"A5: 全国Top10の1位={top10.iloc[0]['net_flow']:.0f}")
            if len(kyoto_top10) > 0:
                print(f"    京都府Top10の1位={kyoto_top10.iloc[0]['net_flow']:.0f}")
            else:
                print("    京都府Top10: N/A")

        results['IT-06'] = {
            'flow_rows': len(flow_df),
            'valid_net_flow': valid_net_flow,
            'top10_max': float(top10.iloc[0]['net_flow']) if len(top10) > 0 else None
        }

    # =================================================================
    # 重要な発見事項
    # =================================================================
    print("\n" + "=" * 70)
    print("重要な発見事項")
    print("=" * 70)

    # competition_indexの確認
    print("\n【調査】competition_indexカラムについて")
    if 'competition_index' in df.columns:
        print("  存在: YES")
        print(f"  非NULL行: {df['competition_index'].notna().sum()}")
    else:
        print("  存在: NO")
        print("  → KeyError 'competition_index' の原因")
        print("  → 代わりに使用可能なカラム: total_applicants")

    # gap_ratioの確認
    print("\n【調査】gap_ratioカラムについて")
    if 'gap_ratio' in df.columns:
        print("  存在: YES")
    else:
        print("  存在: NO")
        print("  → KeyError 'gap_ratio' の原因")
        print("  → 代わりに使用可能なカラム: demand_supply_ratio")
        if 'demand_supply_ratio' in df.columns:
            print(f"  demand_supply_ratio非NULL行: {df['demand_supply_ratio'].notna().sum()}")

    # 全カラムの一覧
    print("\n【全カラム一覧】")
    for i, col in enumerate(df.columns):
        non_null = df[col].notna().sum()
        print(f"  {i+1}. {col}: {non_null}行")

    # 結果をJSONで保存
    output_path = os.path.join(
        os.path.dirname(__file__),
        'deep_analysis_results.json'
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n結果をJSON保存: {output_path}")

    return results


if __name__ == "__main__":
    analyze_data()
