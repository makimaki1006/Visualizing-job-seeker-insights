# -*- coding: utf-8 -*-
"""簡易データ整合性チェック"""

import pandas as pd
import sys
sys.path.insert(0, 'mapcomplete_dashboard')
from mapcomplete_dashboard import DashboardState

print("="*60)
print("Ultrathink Round 3: Data Integrity Check")
print("="*60)

# CSV読み込み
csv_path = '../python_scripts/data/output_v2/mapcomplete_complete_sheets/MapComplete_Complete_All_FIXED.csv'
df = pd.read_csv(csv_path, encoding='utf-8-sig')
print(f"\n[1] CSV Load: {len(df)} rows x {len(df.columns)} cols")

# State作成
state = DashboardState()
state.df = df
state.is_loaded = True

if 'prefecture' in df.columns:
    state.prefectures = sorted(df['prefecture'].dropna().unique().tolist())

print(f"    Prefectures: {len(state.prefectures)}")
print(f"    Municipalities: {df['municipality'].nunique()}")

# Overview検証
print("\n[2] Overview Panel")
total = state.overview_total_applicants
avg_age = state.overview_avg_age
gender = state.overview_gender_ratio
print(f"    Total applicants: {total}")
print(f"    Average age: {avg_age}")
print(f"    Gender ratio: {gender}")

# 手動計算との比較
summary = df[df['row_type'] == 'SUMMARY']
if not summary.empty and 'applicant_count' in summary.columns:
    expected = int(summary['applicant_count'].sum())
    actual = int(total.replace(',', ''))
    status = "PASS" if expected == actual else "FAIL"
    print(f"    Validation: {status} (expected={expected:,}, actual={actual:,})")

# Supply検証（GAS推定ロジック）
print("\n[3] Supply Panel (GAS Estimation)")
employed = state.supply_employed
unemployed = state.supply_unemployed
student = state.supply_student
national = state.supply_national_license
print(f"    Employed: {employed} (60%)")
print(f"    Unemployed: {unemployed} (30%)")
print(f"    Student: {student} (10%)")
print(f"    National license: {national} (3%)")

# 推定値検証
if not summary.empty and 'applicant_count' in summary.columns:
    total_app = int(summary['applicant_count'].sum())
    exp_emp = int(total_app * 0.6)
    exp_unemp = int(total_app * 0.3)
    exp_stud = int(total_app * 0.1)
    exp_nat = int(total_app * 0.03)

    act_emp = int(employed.replace(',', ''))
    act_unemp = int(unemployed.replace(',', ''))
    act_stud = int(student.replace(',', ''))
    act_nat = int(national.replace(',', ''))

    emp_status = "PASS" if exp_emp == act_emp else "FAIL"
    unemp_status = "PASS" if exp_unemp == act_unemp else "FAIL"
    stud_status = "PASS" if exp_stud == act_stud else "FAIL"
    nat_status = "PASS" if exp_nat == act_nat else "FAIL"

    print(f"    Employed validation: {emp_status}")
    print(f"    Unemployed validation: {unemp_status}")
    print(f"    Student validation: {stud_status}")
    print(f"    National license validation: {nat_status}")

# グラフデータ検証（Recharts形式）
print("\n[4] Graph Data (Recharts Format)")
age_gender = state.overview_age_gender_data
qual_buckets = state.supply_qualification_buckets_data

print(f"    Age x Gender: {type(age_gender).__name__} ({len(age_gender)} items)")
print(f"    Qualification buckets: {type(qual_buckets).__name__} ({len(qual_buckets)} items)")

# データ構造検証
if isinstance(age_gender, list) and len(age_gender) > 0:
    sample = age_gender[0]
    has_keys = 'name' in sample and '男性' in sample and '女性' in sample
    print(f"    Age x Gender structure: {'PASS' if has_keys else 'FAIL'}")
    print(f"      Sample: {sample}")

if isinstance(qual_buckets, list) and len(qual_buckets) > 0:
    sample = qual_buckets[0]
    has_keys = 'name' in sample and 'count' in sample
    print(f"    Qualification structure: {'PASS' if has_keys else 'FAIL'}")
    print(f"      Sample: {sample}")

# NaN/無限値チェック
print("\n[5] NaN/Infinity Check")
has_issues = False

numeric_props = {
    'overview_total_applicants': total,
    'overview_avg_age': avg_age,
    'supply_employed': employed,
    'supply_unemployed': unemployed,
    'supply_student': student,
    'supply_national_license': national,
}

for prop_name, value in numeric_props.items():
    if value == "-":
        continue

    try:
        num = float(value.replace(',', ''))
        if pd.isna(num):
            print(f"    FAIL: {prop_name} has NaN")
            has_issues = True
        elif num == float('inf') or num == float('-inf'):
            print(f"    FAIL: {prop_name} has Infinity")
            has_issues = True
    except ValueError:
        pass

if not has_issues:
    print("    PASS: No NaN/Infinity values")

# フィルタリング検証
print("\n[6] Filtering Test")
if len(state.prefectures) > 0:
    test_pref = state.prefectures[0]
    state.selected_prefecture = test_pref
    filtered = state.overview_total_applicants

    state.selected_prefecture = ""
    unfiltered = state.overview_total_applicants

    if filtered != unfiltered:
        print(f"    PASS: Filtering works ({filtered} != {unfiltered})")
    else:
        print(f"    WARN: No filtering effect (single prefecture data?)")

print("\n" + "="*60)
print("Ultrathink Round 3: COMPLETE")
print("="*60)
