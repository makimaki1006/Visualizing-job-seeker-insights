"""
品質検証システムのテスト - 観察的記述 vs 推論的考察の違いを確認
"""

import pandas as pd
from data_quality_validator import DataQualityValidator

# テストデータを作成（小サンプルを含む）
data = {
    'residence_muni': ['京都市上京区'] * 500 + ['○○村'] * 1 + ['△△市'] * 50,
    'age': [30] * 300 + [40] * 200 + [50] * 1 + [60] * 50,
    'gender': ['女性'] * 400 + ['男性'] * 151
}

df = pd.DataFrame(data)

print("=" * 80)
print("テストデータ概要")
print("=" * 80)
print(f"総件数: {len(df)}件")
print(f"\n市区町村別件数:")
print(df['residence_muni'].value_counts())
print(f"\n年齢別件数:")
print(df['age'].value_counts().sort_index())
print()

# 1. 観察的記述モードで検証
print("=" * 80)
print("【1】観察的記述モード（Descriptive）")
print("=" * 80)
validator_desc = DataQualityValidator(validation_mode='descriptive')

# residence_muniの検証
result_desc = validator_desc.validate_sample_size(df, 'residence_muni')
print(f"\nカラム: residence_muni")
print(f"有効データ数: {result_desc['valid_count']}")
print(f"ユニーク値数: {result_desc['unique_values']}")
print(f"最小グループサイズ: {result_desc['min_group_size']}")
print(f"信頼性レベル: {result_desc['reliability_level']}")
print(f"警告: {result_desc['warning']}")

# ageの検証
result_desc_age = validator_desc.validate_sample_size(df, 'age')
print(f"\nカラム: age")
print(f"有効データ数: {result_desc_age['valid_count']}")
print(f"ユニーク値数: {result_desc_age['unique_values']}")
print(f"最小グループサイズ: {result_desc_age['min_group_size']}")
print(f"信頼性レベル: {result_desc_age['reliability_level']}")
print(f"警告: {result_desc_age['warning']}")

print("\n【解釈】")
print("観察的記述モードでは、サンプル数1件でも「DESCRIPTIVE」レベル。")
print("「○○村: 1件」という事実の記述は問題なし。")
print()

# 2. 推論的考察モードで検証
print("=" * 80)
print("【2】推論的考察モード（Inferential）")
print("=" * 80)
validator_inf = DataQualityValidator(validation_mode='inferential')

# residence_muniの検証
result_inf = validator_inf.validate_sample_size(df, 'residence_muni')
print(f"\nカラム: residence_muni")
print(f"有効データ数: {result_inf['valid_count']}")
print(f"ユニーク値数: {result_inf['unique_values']}")
print(f"最小グループサイズ: {result_inf['min_group_size']}")
print(f"信頼性レベル: {result_inf['reliability_level']}")
print(f"警告: {result_inf['warning']}")

# ageの検証
result_inf_age = validator_inf.validate_sample_size(df, 'age')
print(f"\nカラム: age")
print(f"有効データ数: {result_inf_age['valid_count']}")
print(f"ユニーク値数: {result_inf_age['unique_values']}")
print(f"最小グループサイズ: {result_inf_age['min_group_size']}")
print(f"信頼性レベル: {result_inf_age['reliability_level']}")
print(f"警告: {result_inf_age['warning']}")

print("\n【解釈】")
print("推論的考察モードでは、最小グループ1件は「CRITICAL」警告。")
print("「○○村（n=1）は20代が多い傾向」という推論は統計的に不適切。")
print()

# 3. 統合品質レポート生成
print("=" * 80)
print("【3】統合品質レポート")
print("=" * 80)

report_inf = validator_inf.generate_quality_report(
    df,
    target_columns=['residence_muni', 'age', 'gender']
)

overall = report_inf['overall_status']
print(f"\n総合品質スコア: {overall['quality_score']}/100点")
print(f"ステータス: {overall['status']}")
print(f"総データ数: {overall['total_rows']}件")
print(f"信頼できるカラム: {overall['reliable_columns']}/{overall['total_columns']}件")
print(f"推奨事項: {overall['recommendation']}")
print()

print("=" * 80)
print("テスト完了")
print("=" * 80)
