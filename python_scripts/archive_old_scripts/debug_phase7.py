"""Phase 7データ生成デバッグスクリプト"""
import pandas as pd
from pathlib import Path
import sys

# run_complete_v2.pyをインポート
from run_complete_v2 import SimpleJobSeekerAnalyzer

def debug_phase7(filepath):
    """Phase 7のデータ生成プロセスをデバッグ"""
    print("=" * 60)
    print("  Phase 7データ生成デバッグ")
    print("=" * 60)

    # データ読み込みと処理
    analyzer = SimpleJobSeekerAnalyzer(filepath)
    analyzer.load_data()
    analyzer.process_data()

    # processed_dataの確認
    print(f"\n[DEBUG] processed_data shape: {analyzer.processed_data.shape}")
    print(f"[DEBUG] processed_data columns: {list(analyzer.processed_data.columns)}")
    print(f"\n[DEBUG] residence_pref exists: {'residence_pref' in analyzer.processed_data.columns}")
    print(f"[DEBUG] residence_muni exists: {'residence_muni' in analyzer.processed_data.columns}")

    if 'residence_pref' in analyzer.processed_data.columns and 'residence_muni' in analyzer.processed_data.columns:
        # 市町村の一意な組み合わせ数を確認
        unique_locations = analyzer.processed_data.groupby(['residence_pref', 'residence_muni']).size()
        print(f"\n[DEBUG] Unique (prefecture, municipality) combinations: {len(unique_locations)}")
        print(f"\n[DEBUG] Top 10 locations:")
        print(unique_locations.sort_values(ascending=False).head(10))

        # 年齢層と性別の組み合わせを確認
        print(f"\n[DEBUG] age_bucket unique values: {analyzer.processed_data['age_bucket'].unique()}")
        print(f"[DEBUG] gender unique values: {analyzer.processed_data['gender'].unique()}")

        # Phase7データ生成をテスト
        print(f"\n[DEBUG] Testing Phase7 AgeGenderCross generation...")
        age_gender_cross_data = []

        for (residence_pref, residence_muni), location_group in analyzer.processed_data.groupby(['residence_pref', 'residence_muni']):
            for age_bucket in ['20代', '30代', '40代', '50代', '60代', '70歳以上']:
                for gender in ['男性', '女性']:
                    segment_data = location_group[
                        (location_group['age_bucket'] == age_bucket) &
                        (location_group['gender'] == gender)
                    ]

                    if len(segment_data) > 0:
                        age_gender_cross_data.append({
                            'location': f"{residence_pref}{residence_muni}",
                            'prefecture': residence_pref,
                            'municipality': residence_muni,
                            'age_group': age_bucket,
                            'gender': gender,
                            'count': len(segment_data)
                        })

        print(f"\n[DEBUG] Generated {len(age_gender_cross_data)} AgeGenderCross records")

        if len(age_gender_cross_data) > 0:
            df = pd.DataFrame(age_gender_cross_data)
            print(f"\n[DEBUG] First 20 records:")
            print(df.head(20))

            # 市町村別件数を確認
            location_counts = df.groupby(['prefecture', 'municipality']).size()
            print(f"\n[DEBUG] Records per (prefecture, municipality):")
            print(location_counts.head(10))
        else:
            print("\n[ERROR] No AgeGenderCross records generated!")
    else:
        print("\n[ERROR] residence_pref or residence_muni column not found in processed_data!")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = 'C:/Users/fuji1/OneDrive/Pythonスクリプト保管/out/results_20251027_180947.csv'

    debug_phase7(filepath)
