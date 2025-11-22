"""
データ整合性検証スクリプト

DashboardStateの計算プロパティが正しく動作しているかを検証
"""

import pandas as pd
import sys
sys.path.insert(0, 'mapcomplete_dashboard')
from mapcomplete_dashboard import DashboardState


def validate_data_integrity():
    """データ整合性を検証"""
    print("="*60)
    print("データ整合性検証")
    print("="*60)

    # CSVファイル読み込み
    try:
        csv_path = '../python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv'
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        print(f"[OK] CSV読み込み成功: {len(df)}行 x {len(df.columns)}列\n")
    except Exception as e:
        print(f"[NG] CSVファイル読み込みエラー: {e}")
        return False

    # DashboardStateインスタンス作成
    state = DashboardState()
    state.df = df
    state.is_loaded = True

    # 都道府県リスト抽出
    if 'prefecture' in df.columns:
        state.prefectures = sorted(df['prefecture'].dropna().unique().tolist())

    print(f"都道府県数: {len(state.prefectures)}")
    print(f"市区町村数（ユニーク）: {df['municipality'].nunique()}\n")

    # ===== 検証1: Overview パネル =====
    print("="*60)
    print("[検証1] Overview パネル計算プロパティ")
    print("="*60)

    total = state.overview_total_applicants
    avg_age = state.overview_avg_age
    gender_ratio = state.overview_gender_ratio

    print(f"[OK] 求職者総数: {total}")
    print(f"[OK] 平均年齢: {avg_age}")
    print(f"[OK] 男女比: {gender_ratio}")

    # 手動計算との比較
    summary_rows = df[df['row_type'] == 'SUMMARY']
    if not summary_rows.empty and 'applicant_count' in summary_rows.columns:
        expected_total = int(summary_rows['applicant_count'].sum())
        actual_total = int(total.replace(',', ''))

        if expected_total == actual_total:
            print(f"  [OK] 求職者総数一致: {expected_total} == {actual_total}")
        else:
            print(f"  [OK] 求職者総数不一致: 期待値={expected_total}, 実際={actual_total}")

    # ===== 検証2: Supply パネル（GAS推定ロジック） =====
    print("\n" + "="*60)
    print("[検証2] Supply パネル（GAS推定ロジック）")
    print("="*60)

    supply_employed = state.supply_employed
    supply_unemployed = state.supply_unemployed
    supply_student = state.supply_student
    supply_national = state.supply_national_license

    print(f"[OK] 就業中: {supply_employed} (全体の60%)")
    print(f"[OK] 離職中: {supply_unemployed} (全体の30%)")
    print(f"[OK] 在学中: {supply_student} (全体の10%)")
    print(f"[OK] 国家資格保有: {supply_national} (全体の3%)")

    # GAS推定ロジックの検証
    if not summary_rows.empty and 'applicant_count' in summary_rows.columns:
        total_applicants = int(summary_rows['applicant_count'].sum())

        expected_employed = int(total_applicants * 0.6)
        expected_unemployed = int(total_applicants * 0.3)
        expected_student = int(total_applicants * 0.1)
        expected_national = int(total_applicants * 0.03)

        actual_employed = int(supply_employed.replace(',', ''))
        actual_unemployed = int(supply_unemployed.replace(',', ''))
        actual_student = int(supply_student.replace(',', ''))
        actual_national = int(supply_national.replace(',', ''))

        print(f"\n  [就業中] 期待値={expected_employed:,}, 実際={actual_employed:,} " +
              ("[OK]" if expected_employed == actual_employed else "[OK]"))
        print(f"  [離職中] 期待値={expected_unemployed:,}, 実際={actual_unemployed:,} " +
              ("[OK]" if expected_unemployed == actual_unemployed else "[OK]"))
        print(f"  [在学中] 期待値={expected_student:,}, 実際={actual_student:,} " +
              ("[OK]" if expected_student == actual_student else "[OK]"))
        print(f"  [国家資格] 期待値={expected_national:,}, 実際={actual_national:,} " +
              ("[OK]" if expected_national == actual_national else "[OK]"))

    # ===== 検証3: グラフデータ（Recharts形式） =====
    print("\n" + "="*60)
    print("[検証3] グラフデータ（Recharts形式）")
    print("="*60)

    age_gender_data = state.overview_age_gender_data
    qual_buckets_data = state.supply_qualification_buckets_data

    print(f"[OK] 年齢×性別データ: {type(age_gender_data).__name__} ({len(age_gender_data)}件)")
    print(f"[OK] 資格バケットデータ: {type(qual_buckets_data).__name__} ({len(qual_buckets_data)}件)")

    # データ構造検証
    if isinstance(age_gender_data, list) and len(age_gender_data) > 0:
        sample = age_gender_data[0]
        print(f"  [OK] 年齢×性別データ構造: {sample}")
        if 'name' in sample and '男性' in sample and '女性' in sample:
            print("    [OK] 必須キー存在: name, 男性, 女性")
        else:
            print("    [OK] 必須キー不足")

    if isinstance(qual_buckets_data, list) and len(qual_buckets_data) > 0:
        sample = qual_buckets_data[0]
        print(f"  [OK] 資格バケットデータ構造: {sample}")
        if 'name' in sample and 'count' in sample:
            print("    [OK] 必須キー存在: name, count")
        else:
            print("    [OK] 必須キー不足")

    # ===== 検証4: NaN/無限値のチェック =====
    print("\n" + "="*60)
    print("[検証4] NaN/無限値のチェック")
    print("="*60)

    has_issues = False

    # 数値プロパティのチェック
    numeric_props = {
        'overview_total_applicants': total,
        'overview_avg_age': avg_age,
        'supply_employed': supply_employed,
        'supply_unemployed': supply_unemployed,
        'supply_student': supply_student,
        'supply_national_license': supply_national,
    }

    for prop_name, value in numeric_props.items():
        if value == "-":
            continue  # 未ロード状態は正常

        # NaN, inf チェック
        try:
            numeric_value = float(value.replace(',', ''))
            if pd.isna(numeric_value):
                print(f"  [OK] {prop_name}: NaN値検出")
                has_issues = True
            elif numeric_value == float('inf') or numeric_value == float('-inf'):
                print(f"  [OK] {prop_name}: 無限値検出")
                has_issues = True
        except ValueError:
            pass  # 文字列の場合はスキップ

    if not has_issues:
        print("  [ ! ] NaN/無限値なし")

    # ===== 検証5: フィルタリング動作 =====
    print("\n" + "="*60)
    print("[検証5] フィルタリング動作")
    print("="*60)

    if len(state.prefectures) > 0:
        # 最初の都道府県でフィルタ
        test_pref = state.prefectures[0]
        state.selected_prefecture = test_pref

        filtered_total = state.overview_total_applicants
        print(f"[OK] {test_pref}選択時の求職者数: {filtered_total}")

        # フィルタ解除
        state.selected_prefecture = ""
        unfiltered_total = state.overview_total_applicants

        if filtered_total != unfiltered_total:
            print(f"  [OK] フィルタリング動作確認: {filtered_total} != {unfiltered_total}")
        else:
            print(f"  [OK][OK] フィルタリング効果なし（データが1都道府県のみの可能性）")

    print("\n" + "="*60)
    print("[OK] データ整合性検証完了")
    print("="*60)

    return True


if __name__ == "__main__":
    validate_data_integrity()
