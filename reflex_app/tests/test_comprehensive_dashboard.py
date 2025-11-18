# -*- coding: utf-8 -*-
"""
MapComplete Dashboard 包括的テストスイート

ユニットテスト、統合テスト、E2Eテストを10回繰り返して
実データの入稿→データ可視化のフローを徹底検証します。
"""

import sys
import os
import pandas as pd
import json
from datetime import datetime

# パス設定
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト結果格納
TEST_RESULTS = {
    "unit_tests": [],
    "integration_tests": [],
    "e2e_tests": [],
    "summary": {}
}

# =============================================================================
# テストデータ準備
# =============================================================================

def load_test_data():
    """テスト用CSVデータをロード"""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "MapComplete_Complete_All_FIXED.csv"
    )

    if not os.path.exists(csv_path):
        return None, f"CSVファイルが見つかりません: {csv_path}"

    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        return df, None
    except Exception as e:
        return None, f"CSVロードエラー: {e}"

# =============================================================================
# ユニットテスト
# =============================================================================

def test_unit_csv_structure(df):
    """UT-01: CSVデータ構造の検証"""
    required_columns = [
        'row_type', 'prefecture', 'municipality', 'category1', 'category2', 'category3',
        'applicant_count', 'avg_age', 'male_count', 'female_count', 'avg_qualifications',
        'latitude', 'longitude', 'count', 'inflow', 'outflow', 'net_flow',
        'demand_count', 'supply_count', 'gap', 'demand_supply_ratio', 'rarity_score',
        'total_applicants', 'female_ratio', 'male_ratio'
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        return False, f"欠損カラム: {missing}"
    return True, f"全{len(required_columns)}カラム存在確認"

def test_unit_row_types(df):
    """UT-02: row_typeの種類検証"""
    expected_types = ['SUMMARY', 'FLOW', 'GAP', 'RARITY', 'COMPETITION', 'PERSONA_MUNI',
                     'EMPLOYMENT_AGE_CROSS', 'URGENCY_AGE', 'URGENCY_EMPLOYMENT', 'AGE_GENDER']

    actual_types = df['row_type'].unique().tolist()
    missing = [t for t in expected_types if t not in actual_types]

    if missing:
        return False, f"欠損row_type: {missing}"
    return True, f"{len(actual_types)}種類のrow_type確認"

def test_unit_prefecture_data(df):
    """UT-03: 都道府県データの検証"""
    prefectures = df['prefecture'].dropna().unique()

    if len(prefectures) < 40:
        return False, f"都道府県数が少なすぎ: {len(prefectures)}"
    return True, f"{len(prefectures)}都道府県のデータ確認"

def test_unit_municipality_data(df):
    """UT-04: 市区町村データの検証"""
    municipalities = df['municipality'].dropna().unique()

    if len(municipalities) < 100:
        return False, f"市区町村数が少なすぎ: {len(municipalities)}"
    return True, f"{len(municipalities)}市区町村のデータ確認"

def test_unit_numeric_columns(df):
    """UT-05: 数値カラムの検証"""
    numeric_cols = ['applicant_count', 'avg_age', 'male_count', 'female_count',
                   'inflow', 'outflow', 'net_flow', 'gap', 'rarity_score']

    errors = []
    for col in numeric_cols:
        if col in df.columns:
            non_numeric = df[df[col].notna() & ~pd.to_numeric(df[col], errors='coerce').notna()]
            if len(non_numeric) > 0:
                errors.append(f"{col}: {len(non_numeric)}件の非数値")

    if errors:
        return False, "; ".join(errors)
    return True, f"{len(numeric_cols)}カラムの数値検証OK"

def test_unit_flow_data(df):
    """UT-06: FLOWデータの検証"""
    flow_df = df[df['row_type'] == 'FLOW']

    if flow_df.empty:
        return False, "FLOWデータが存在しない"

    # inflow, outflow, net_flowが存在するか
    required = ['inflow', 'outflow', 'net_flow']
    missing = [col for col in required if col not in flow_df.columns or flow_df[col].isna().all()]

    if missing:
        return False, f"FLOWデータに欠損: {missing}"
    return True, f"FLOW: {len(flow_df)}行のデータ確認"

def test_unit_gap_data(df):
    """UT-07: GAPデータの検証"""
    gap_df = df[df['row_type'] == 'GAP']

    if gap_df.empty:
        return False, "GAPデータが存在しない"

    # gap, demand_supply_ratioが存在するか
    required = ['gap', 'demand_supply_ratio']
    missing = [col for col in required if col not in gap_df.columns or gap_df[col].isna().all()]

    if missing:
        return False, f"GAPデータに欠損: {missing}"
    return True, f"GAP: {len(gap_df)}行のデータ確認"

def test_unit_rarity_data(df):
    """UT-08: RARITYデータの検証"""
    rarity_df = df[df['row_type'] == 'RARITY']

    if rarity_df.empty:
        return False, "RARITYデータが存在しない"

    # rarity_scoreが存在するか
    if 'rarity_score' not in rarity_df.columns or rarity_df['rarity_score'].isna().all():
        return False, "rarity_scoreが欠損"
    return True, f"RARITY: {len(rarity_df)}行のデータ確認"

def test_unit_competition_data(df):
    """UT-09: COMPETITIONデータの検証"""
    comp_df = df[df['row_type'] == 'COMPETITION']

    if comp_df.empty:
        return False, "COMPETITIONデータが存在しない"

    # total_applicants, female_ratioが存在するか
    required = ['total_applicants', 'female_ratio']
    missing = [col for col in required if col not in comp_df.columns or comp_df[col].isna().all()]

    if missing:
        return False, f"COMPETITIONデータに欠損: {missing}"
    return True, f"COMPETITION: {len(comp_df)}行のデータ確認"

def test_unit_summary_data(df):
    """UT-10: SUMMARYデータの検証"""
    summary_df = df[df['row_type'] == 'SUMMARY']

    if summary_df.empty:
        return False, "SUMMARYデータが存在しない"

    # applicant_count, avg_ageが存在するか
    required = ['applicant_count', 'avg_age']
    missing = [col for col in required if col not in summary_df.columns or summary_df[col].isna().all()]

    if missing:
        return False, f"SUMMARYデータに欠損: {missing}"
    return True, f"SUMMARY: {len(summary_df)}行のデータ確認"

# =============================================================================
# 統合テスト
# =============================================================================

def test_integration_prefecture_filter(df):
    """IT-01: 都道府県フィルタリングの検証"""
    prefectures = df['prefecture'].dropna().unique()

    errors = []
    for pref in prefectures[:5]:  # 最初の5都道府県でテスト
        filtered = df[df['prefecture'] == pref]
        if filtered.empty:
            errors.append(f"{pref}: データなし")
        elif len(filtered['row_type'].unique()) < 3:
            errors.append(f"{pref}: row_type種類不足")

    if errors:
        return False, "; ".join(errors)
    return True, "5都道府県のフィルタリング検証OK"

def test_integration_municipality_filter(df):
    """IT-02: 市区町村フィルタリングの検証"""
    # 京都府のデータでテスト
    kyoto_df = df[df['prefecture'] == '京都府']

    if kyoto_df.empty:
        return False, "京都府のデータが存在しない"

    municipalities = kyoto_df['municipality'].dropna().unique()

    if len(municipalities) < 5:
        return False, f"京都府の市区町村数が少なすぎ: {len(municipalities)}"

    # 最初の市区町村でフィルタリング
    first_muni = municipalities[0]
    filtered = kyoto_df[kyoto_df['municipality'] == first_muni]

    if filtered.empty:
        return False, f"{first_muni}のデータが存在しない"

    return True, f"京都府: {len(municipalities)}市区町村の確認OK"

def test_integration_flow_ranking(df):
    """IT-03: FLOWランキングデータの検証"""
    # 東京都でテスト
    tokyo_flow = df[(df['prefecture'] == '東京都') & (df['row_type'] == 'FLOW')]

    if tokyo_flow.empty:
        return False, "東京都のFLOWデータが存在しない"

    # inflow上位10を取得
    if 'inflow' not in tokyo_flow.columns:
        return False, "inflowカラムが存在しない"

    top10 = tokyo_flow.nlargest(10, 'inflow')

    if len(top10) < 10:
        return False, f"Top10が取得できない: {len(top10)}件"

    return True, f"東京都FLOW Top10: {top10['inflow'].sum():.0f}総流入"

def test_integration_gap_ranking(df):
    """IT-04: GAPランキングデータの検証"""
    # 大阪府でテスト
    osaka_gap = df[(df['prefecture'] == '大阪府') & (df['row_type'] == 'GAP')]

    if osaka_gap.empty:
        return False, "大阪府のGAPデータが存在しない"

    # gap上位10を取得
    if 'gap' not in osaka_gap.columns:
        return False, "gapカラムが存在しない"

    top10 = osaka_gap.nlargest(10, 'gap')

    if len(top10) < 10:
        return False, f"Top10が取得できない: {len(top10)}件"

    return True, f"大阪府GAP Top10: {top10['gap'].sum():.0f}総ギャップ"

def test_integration_rarity_ranking(df):
    """IT-05: RARITYランキングデータの検証"""
    # 愛知県でテスト
    aichi_rarity = df[(df['prefecture'] == '愛知県') & (df['row_type'] == 'RARITY')]

    if aichi_rarity.empty:
        return False, "愛知県のRARITYデータが存在しない"

    # rarity_score上位10を取得
    if 'rarity_score' not in aichi_rarity.columns:
        return False, "rarity_scoreカラムが存在しない"

    top10 = aichi_rarity.nlargest(10, 'rarity_score')

    if len(top10) < 10:
        return False, f"Top10が取得できない: {len(top10)}件"

    return True, f"愛知県RARITY Top10: {top10['rarity_score'].mean():.2f}平均スコア"

def test_integration_competition_ranking(df):
    """IT-06: COMPETITIONランキングデータの検証"""
    # 福岡県でテスト
    fukuoka_comp = df[(df['prefecture'] == '福岡県') & (df['row_type'] == 'COMPETITION')]

    if fukuoka_comp.empty:
        return False, "福岡県のCOMPETITIONデータが存在しない"

    # total_applicants上位10を取得
    if 'total_applicants' not in fukuoka_comp.columns:
        return False, "total_applicantsカラムが存在しない"

    top10 = fukuoka_comp.nlargest(10, 'total_applicants')

    if len(top10) < 10:
        return False, f"Top10が取得できない: {len(top10)}件"

    return True, f"福岡県COMPETITION Top10: {top10['total_applicants'].sum():.0f}総応募者"

def test_integration_cross_data(df):
    """IT-07: クロス分析データの検証"""
    cross_df = df[df['row_type'] == 'EMPLOYMENT_AGE_CROSS']

    if cross_df.empty:
        return False, "EMPLOYMENT_AGE_CROSSデータが存在しない"

    # category1, category2が存在するか
    if cross_df['category1'].isna().all() or cross_df['category2'].isna().all():
        return False, "クロス分析のカテゴリデータが欠損"

    return True, f"クロス分析: {len(cross_df)}行のデータ確認"

def test_integration_urgency_data(df):
    """IT-08: 緊急度データの検証"""
    urgency_df = df[df['row_type'].isin(['URGENCY_AGE', 'URGENCY_EMPLOYMENT'])]

    if urgency_df.empty:
        return False, "緊急度データが存在しない"

    # avg_urgency_scoreが存在するか
    if 'avg_urgency_score' not in urgency_df.columns or urgency_df['avg_urgency_score'].isna().all():
        return False, "avg_urgency_scoreが欠損"

    return True, f"緊急度: {len(urgency_df)}行のデータ確認"

def test_integration_persona_data(df):
    """IT-09: ペルソナデータの検証"""
    persona_df = df[df['row_type'] == 'PERSONA_MUNI']

    if persona_df.empty:
        return False, "PERSONA_MUNIデータが存在しない"

    # category1, countが存在するか
    if persona_df['category1'].isna().all() or persona_df['count'].isna().all():
        return False, "ペルソナのカテゴリ/カウントデータが欠損"

    return True, f"ペルソナ: {len(persona_df)}行のデータ確認"

def test_integration_data_consistency(df):
    """IT-10: データ整合性の検証"""
    # 各都道府県に最低限のrow_typeが存在するか
    prefectures = df['prefecture'].dropna().unique()

    inconsistent = []
    for pref in prefectures[:10]:  # 最初の10都道府県でテスト
        pref_df = df[df['prefecture'] == pref]
        row_types = pref_df['row_type'].unique()

        if 'SUMMARY' not in row_types:
            inconsistent.append(f"{pref}: SUMMARY欠損")

    if inconsistent:
        return False, "; ".join(inconsistent[:3])
    return True, "10都道府県のデータ整合性OK"

# =============================================================================
# E2Eテスト（データフロー検証）
# =============================================================================

def test_e2e_overview_flow(df):
    """E2E-01: 総合概要タブのデータフロー"""
    # 京都府京都市でテスト
    filtered = df[(df['prefecture'] == '京都府') & (df['municipality'] == '京都市')]

    if filtered.empty:
        return False, "京都府京都市のデータが存在しない"

    # SUMMARYデータから総求職者数を取得
    summary = filtered[filtered['row_type'] == 'SUMMARY']
    if summary.empty:
        return False, "SUMMARYデータが存在しない"

    applicants = summary['applicant_count'].sum()
    if applicants <= 0:
        return False, f"求職者数が不正: {applicants}"

    return True, f"京都府京都市: {applicants:.0f}人の求職者"

def test_e2e_supply_flow(df):
    """E2E-02: 人材供給タブのデータフロー"""
    # 東京都渋谷区でテスト
    filtered = df[(df['prefecture'] == '東京都') & (df['municipality'] == '渋谷区')]

    if filtered.empty:
        return False, "東京都渋谷区のデータが存在しない"

    # SUMMARYから性別比率を取得
    summary = filtered[filtered['row_type'] == 'SUMMARY']
    if summary.empty:
        return False, "SUMMARYデータが存在しない"

    female = summary['female_count'].sum()
    male = summary['male_count'].sum()

    if female + male <= 0:
        return False, "性別データが不正"

    female_ratio = female / (female + male) * 100
    return True, f"東京都渋谷区: 女性比率{female_ratio:.1f}%"

def test_e2e_career_flow(df):
    """E2E-03: キャリア分析タブのデータフロー"""
    # 大阪府大阪市でテスト
    filtered = df[(df['prefecture'] == '大阪府') & (df['municipality'] == '大阪市')]

    if filtered.empty:
        return False, "大阪府大阪市のデータが存在しない"

    # EMPLOYMENT_AGE_CROSSデータを確認
    cross = filtered[filtered['row_type'] == 'EMPLOYMENT_AGE_CROSS']
    if cross.empty:
        return False, "クロス分析データが存在しない"

    return True, f"大阪府大阪市: {len(cross)}件のクロス分析データ"

def test_e2e_urgency_flow(df):
    """E2E-04: 緊急度分析タブのデータフロー"""
    # 愛知県名古屋市でテスト
    filtered = df[(df['prefecture'] == '愛知県') & (df['municipality'] == '名古屋市')]

    if filtered.empty:
        return False, "愛知県名古屋市のデータが存在しない"

    # URGENCY_AGEデータを確認
    urgency = filtered[filtered['row_type'] == 'URGENCY_AGE']
    if urgency.empty:
        return False, "緊急度データが存在しない"

    avg_urgency = urgency['avg_urgency_score'].mean()
    return True, f"愛知県名古屋市: 平均緊急度スコア{avg_urgency:.2f}"

def test_e2e_persona_flow(df):
    """E2E-05: ペルソナ分析タブのデータフロー"""
    # 福岡県福岡市でテスト
    filtered = df[(df['prefecture'] == '福岡県') & (df['municipality'] == '福岡市')]

    if filtered.empty:
        return False, "福岡県福岡市のデータが存在しない"

    # PERSONA_MUNIデータを確認
    persona = filtered[filtered['row_type'] == 'PERSONA_MUNI']
    if persona.empty:
        return False, "ペルソナデータが存在しない"

    top_persona = persona.nlargest(1, 'count')['category1'].iloc[0]
    return True, f"福岡県福岡市: トップペルソナ={top_persona}"

def test_e2e_flow_analysis(df):
    """E2E-06: フロー分析タブのデータフロー"""
    # 神奈川県横浜市でテスト
    filtered = df[(df['prefecture'] == '神奈川県') & (df['municipality'] == '横浜市')]

    if filtered.empty:
        return False, "神奈川県横浜市のデータが存在しない"

    # FLOWデータを確認
    flow = filtered[filtered['row_type'] == 'FLOW']
    if flow.empty:
        return False, "FLOWデータが存在しない"

    inflow = flow['inflow'].sum()
    outflow = flow['outflow'].sum()
    return True, f"神奈川県横浜市: 流入{inflow:.0f}/流出{outflow:.0f}"

def test_e2e_gap_analysis(df):
    """E2E-07: 需給バランスタブのデータフロー"""
    # 埼玉県さいたま市でテスト
    filtered = df[(df['prefecture'] == '埼玉県') & (df['municipality'] == 'さいたま市')]

    if filtered.empty:
        return False, "埼玉県さいたま市のデータが存在しない"

    # GAPデータを確認
    gap = filtered[filtered['row_type'] == 'GAP']
    if gap.empty:
        return False, "GAPデータが存在しない"

    total_gap = gap['gap'].sum()
    return True, f"埼玉県さいたま市: 総ギャップ{total_gap:.0f}"

def test_e2e_rarity_analysis(df):
    """E2E-08: 希少人材分析タブのデータフロー"""
    # 千葉県千葉市でテスト
    filtered = df[(df['prefecture'] == '千葉県') & (df['municipality'] == '千葉市')]

    if filtered.empty:
        return False, "千葉県千葉市のデータが存在しない"

    # RARITYデータを確認
    rarity = filtered[filtered['row_type'] == 'RARITY']
    if rarity.empty:
        return False, "RARITYデータが存在しない"

    avg_rarity = rarity['rarity_score'].mean()
    return True, f"千葉県千葉市: 平均希少スコア{avg_rarity:.2f}"

def test_e2e_competition_analysis(df):
    """E2E-09: 人材プロファイルタブのデータフロー"""
    # 兵庫県神戸市でテスト
    filtered = df[(df['prefecture'] == '兵庫県') & (df['municipality'] == '神戸市')]

    if filtered.empty:
        return False, "兵庫県神戸市のデータが存在しない"

    # COMPETITIONデータを確認
    comp = filtered[filtered['row_type'] == 'COMPETITION']
    if comp.empty:
        return False, "COMPETITIONデータが存在しない"

    total_applicants = comp['total_applicants'].sum()
    return True, f"兵庫県神戸市: 総応募者{total_applicants:.0f}"

def test_e2e_prefecture_change(df):
    """E2E-10: 都道府県変更時のデータ更新フロー"""
    prefectures = ['京都府', '東京都', '大阪府', '愛知県', '福岡県']

    results = []
    for pref in prefectures:
        pref_df = df[df['prefecture'] == pref]
        if pref_df.empty:
            results.append(f"{pref}: データなし")
            continue

        # 各都道府県でSUMMARYデータを確認
        summary = pref_df[pref_df['row_type'] == 'SUMMARY']
        if summary.empty:
            results.append(f"{pref}: SUMMARYなし")
            continue

        applicants = summary['applicant_count'].sum()
        results.append(f"{pref}: {applicants:.0f}人")

    if any("データなし" in r or "SUMMARYなし" in r for r in results):
        return False, "; ".join(results)

    return True, "; ".join(results)

# =============================================================================
# テスト実行
# =============================================================================

def run_all_tests():
    """全テストを実行"""
    print("=" * 70)
    print("MapComplete Dashboard 包括的テストスイート")
    print("=" * 70)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # データロード
    print("[1/4] テストデータロード中...")
    df, error = load_test_data()

    if error:
        print(f"❌ データロード失敗: {error}")
        return False

    print(f"✅ データロード成功: {len(df)}行 x {len(df.columns)}列")
    print()

    # ユニットテスト
    print("[2/4] ユニットテスト実行中...")
    print("-" * 70)

    unit_tests = [
        ("UT-01", "CSVデータ構造", test_unit_csv_structure),
        ("UT-02", "row_type種類", test_unit_row_types),
        ("UT-03", "都道府県データ", test_unit_prefecture_data),
        ("UT-04", "市区町村データ", test_unit_municipality_data),
        ("UT-05", "数値カラム", test_unit_numeric_columns),
        ("UT-06", "FLOWデータ", test_unit_flow_data),
        ("UT-07", "GAPデータ", test_unit_gap_data),
        ("UT-08", "RARITYデータ", test_unit_rarity_data),
        ("UT-09", "COMPETITIONデータ", test_unit_competition_data),
        ("UT-10", "SUMMARYデータ", test_unit_summary_data),
    ]

    unit_passed = 0
    for test_id, test_name, test_func in unit_tests:
        passed, message = test_func(df)
        status = "✅" if passed else "❌"
        print(f"  {status} {test_id}: {test_name} - {message}")
        TEST_RESULTS["unit_tests"].append({
            "id": test_id,
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            unit_passed += 1

    print(f"\n  ユニットテスト結果: {unit_passed}/{len(unit_tests)} 成功")
    print()

    # 統合テスト
    print("[3/4] 統合テスト実行中...")
    print("-" * 70)

    integration_tests = [
        ("IT-01", "都道府県フィルタ", test_integration_prefecture_filter),
        ("IT-02", "市区町村フィルタ", test_integration_municipality_filter),
        ("IT-03", "FLOWランキング", test_integration_flow_ranking),
        ("IT-04", "GAPランキング", test_integration_gap_ranking),
        ("IT-05", "RARITYランキング", test_integration_rarity_ranking),
        ("IT-06", "COMPETITIONランキング", test_integration_competition_ranking),
        ("IT-07", "クロス分析データ", test_integration_cross_data),
        ("IT-08", "緊急度データ", test_integration_urgency_data),
        ("IT-09", "ペルソナデータ", test_integration_persona_data),
        ("IT-10", "データ整合性", test_integration_data_consistency),
    ]

    integration_passed = 0
    for test_id, test_name, test_func in integration_tests:
        passed, message = test_func(df)
        status = "✅" if passed else "❌"
        print(f"  {status} {test_id}: {test_name} - {message}")
        TEST_RESULTS["integration_tests"].append({
            "id": test_id,
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            integration_passed += 1

    print(f"\n  統合テスト結果: {integration_passed}/{len(integration_tests)} 成功")
    print()

    # E2Eテスト
    print("[4/4] E2Eテスト実行中...")
    print("-" * 70)

    e2e_tests = [
        ("E2E-01", "総合概要フロー", test_e2e_overview_flow),
        ("E2E-02", "人材供給フロー", test_e2e_supply_flow),
        ("E2E-03", "キャリア分析フロー", test_e2e_career_flow),
        ("E2E-04", "緊急度分析フロー", test_e2e_urgency_flow),
        ("E2E-05", "ペルソナ分析フロー", test_e2e_persona_flow),
        ("E2E-06", "フロー分析", test_e2e_flow_analysis),
        ("E2E-07", "需給バランス分析", test_e2e_gap_analysis),
        ("E2E-08", "希少人材分析", test_e2e_rarity_analysis),
        ("E2E-09", "人材プロファイル分析", test_e2e_competition_analysis),
        ("E2E-10", "都道府県変更フロー", test_e2e_prefecture_change),
    ]

    e2e_passed = 0
    for test_id, test_name, test_func in e2e_tests:
        passed, message = test_func(df)
        status = "✅" if passed else "❌"
        print(f"  {status} {test_id}: {test_name} - {message}")
        TEST_RESULTS["e2e_tests"].append({
            "id": test_id,
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            e2e_passed += 1

    print(f"\n  E2Eテスト結果: {e2e_passed}/{len(e2e_tests)} 成功")
    print()

    # サマリー
    total_tests = len(unit_tests) + len(integration_tests) + len(e2e_tests)
    total_passed = unit_passed + integration_passed + e2e_passed

    print("=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    print(f"  ユニットテスト:   {unit_passed}/{len(unit_tests)} 成功")
    print(f"  統合テスト:       {integration_passed}/{len(integration_tests)} 成功")
    print(f"  E2Eテスト:        {e2e_passed}/{len(e2e_tests)} 成功")
    print(f"  ─────────────────────────────")
    print(f"  合計:             {total_passed}/{total_tests} 成功 ({total_passed/total_tests*100:.1f}%)")
    print()

    # 結果保存
    TEST_RESULTS["summary"] = {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "unit_passed": unit_passed,
        "integration_passed": integration_passed,
        "e2e_passed": e2e_passed,
        "success_rate": total_passed / total_tests * 100,
        "timestamp": datetime.now().isoformat()
    }

    # JSONに保存
    result_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_results.json"
    )
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)

    print(f"テスト結果をJSONに保存: {result_path}")

    return total_passed == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
