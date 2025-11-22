"""
失敗したテストのデバッグスクリプト
"""

import pandas as pd
import sys
import io

# Windows環境でのUTF-8エンコーディング設定
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

csv_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts\data\output_v2\mapcomplete_complete_sheets\MapComplete_Complete_All_FIXED.csv"

df = pd.read_csv(csv_path, low_memory=False)

print("=" * 80)
print("🔍 失敗したテストのデバッグ")
print("=" * 80)

# 三重県データ
prefecture = '三重県'

print(f"\n都道府県: {prefecture}")
print(f"総データ数: {len(df)}")

# RARITYデータ確認
print("\n" + "=" * 80)
print("❌ ユニットテスト5: rarity_*_ranking計算（失敗原因調査）")
print("=" * 80)

rarity_data = df[(df['row_type'] == 'RARITY') & (df['prefecture'] == prefecture)]
print(f"\nRARITYデータ総数: {len(rarity_data)}")

if len(rarity_data) > 0:
    print("\nRARITYデータのカラム一覧:")
    print(rarity_data.columns.tolist())

    print("\nhas_national_licenseカラムの値の種類:")
    if 'has_national_license' in rarity_data.columns:
        print(rarity_data['has_national_license'].value_counts())
        print(f"\nデータ型: {rarity_data['has_national_license'].dtype}")

        # Trueの件数
        national_count = len(rarity_data[rarity_data['has_national_license'] == True])
        nonnational_count = len(rarity_data[rarity_data['has_national_license'] == False])

        print(f"\n国家資格あり (True): {national_count}件")
        print(f"国家資格なし (False): {nonnational_count}件")

        # サンプルデータ表示
        if national_count > 0:
            print("\n国家資格あり サンプルデータ（最初の3件）:")
            print(rarity_data[rarity_data['has_national_license'] == True][['category1', 'category2', 'category3', 'chi_square', 'rarity_score']].head(3))
        else:
            print("\n⚠️ 国家資格ありのデータが0件です")
            print("\n全RARITYデータのhas_national_license値:")
            print(rarity_data[['category1', 'category2', 'has_national_license']].head(10))
    else:
        print("⚠️ has_national_licenseカラムが存在しません")
        print("\n存在するカラム:")
        for col in rarity_data.columns:
            print(f"  - {col}")

# COMPETITIONデータ確認
print("\n" + "=" * 80)
print("❌ ユニットテスト6: competition_*_ranking計算（失敗原因調査）")
print("=" * 80)

competition_data = df[(df['row_type'] == 'COMPETITION') & (df['prefecture'] == prefecture)]
print(f"\nCOMPETITIONデータ総数: {len(competition_data)}")

if len(competition_data) > 0:
    print("\nCOMPETITIONデータのカラム一覧:")
    print(competition_data.columns.tolist())

    print("\nサンプルデータ（最初の3件）:")
    print(competition_data.head(3))

    # 必要なカラムの存在確認
    required_cols = ['national_license_rate', 'age_median', 'sample_count']
    print("\n必要なカラムの存在確認:")
    for col in required_cols:
        exists = col in competition_data.columns
        status = "✅" if exists else "❌"
        print(f"  {status} {col}: {'存在' if exists else '存在しない'}")

        if exists:
            # データ型と値の範囲を表示
            print(f"      データ型: {competition_data[col].dtype}")
            print(f"      最小値: {competition_data[col].min()}")
            print(f"      最大値: {competition_data[col].max()}")
            print(f"      欠損値: {competition_data[col].isna().sum()}件")
else:
    print("⚠️ COMPETITIONデータが0件です")

print("\n" + "=" * 80)
print("🎯 デバッグ完了")
print("=" * 80)
