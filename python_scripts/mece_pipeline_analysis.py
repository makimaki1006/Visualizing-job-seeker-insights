"""
MECE分析: CSVデータ→Python→アウトプットの全工程
潜在的な問題を体系的に特定
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List

# テストデータ読み込み
csv_path = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251027_180947.csv"

print("=" * 80)
print("MECE分析: データパイプライン全体")
print("=" * 80)
print()

# ========================================
# STAGE 1: 入力段階（Input Stage）
# ========================================

print("【STAGE 1】入力段階（Input Stage）")
print("-" * 80)

issues_stage1 = []

# 1-1. CSVファイル読み込み
print("\n[1-1] CSVファイル読み込み")
try:
    df_raw = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"  [OK] 読み込み成功: {len(df_raw)}行 x {len(df_raw.columns)}列")
    print(f"  カラム: {list(df_raw.columns)}")
except Exception as e:
    print(f"   読み込み失敗: {e}")
    issues_stage1.append({
        'category': 'ファイル読み込み',
        'issue': f'CSV読み込みエラー: {e}',
        'severity': 'CRITICAL'
    })

# 1-2. エンコーディング検証
print("\n[1-2] エンコーディング検証")
print("   現在: utf-8-sig固定")
print("   問題: 他のエンコーディング（Shift-JIS, EUC-JP）に非対応")
issues_stage1.append({
    'category': 'エンコーディング',
    'issue': 'utf-8-sig固定のため、Shift-JISやEUC-JPのCSVは読み込めない',
    'severity': 'MEDIUM',
    'recommendation': 'エンコーディング自動検出（chardetライブラリ）の導入を検討'
})

# 1-3. データ型検証
print("\n[1-3] データ型検証")
print(f"  データ型一覧:")
for col, dtype in df_raw.dtypes.items():
    print(f"    {col}: {dtype}")

# 数値として扱うべきカラムが文字列になっていないか
expected_numeric = ['page', 'card_index']
for col in expected_numeric:
    if col in df_raw.columns:
        if df_raw[col].dtype == 'object':
            print(f"   {col}が文字列型です（数値型が期待される）")
            issues_stage1.append({
                'category': 'データ型',
                'issue': f'{col}カラムが文字列型（数値型が期待される）',
                'severity': 'LOW',
                'recommendation': 'pd.to_numeric()で変換'
            })

print(f"\n Stage 1完了: {len(issues_stage1)}件の問題検出")

# ========================================
# STAGE 2: データ正規化段階（Normalization Stage）
# ========================================

print("\n" + "=" * 80)
print("【STAGE 2】データ正規化段階（Normalization Stage）")
print("-" * 80)

issues_stage2 = []

# 2-1. age_gender分離
print("\n[2-1] age_gender分離")
from data_normalizer import DataNormalizer
normalizer = DataNormalizer()

age_gender_samples = df_raw['age_gender'].head(5).tolist()
print(f"  サンプル: {age_gender_samples}")

failed_parse = 0
for sample in df_raw['age_gender']:
    parsed = normalizer.parse_age_gender(sample)
    if parsed['age'] is None and sample and str(sample).strip() != '':
        failed_parse += 1

if failed_parse > 0:
    print(f"   パース失敗: {failed_parse}件")
    issues_stage2.append({
        'category': 'age_gender分離',
        'issue': f'{failed_parse}件のage_genderをパースできませんでした',
        'severity': 'MEDIUM',
        'recommendation': '正規表現パターンの拡張が必要'
    })
else:
    print(f"   パース成功: 全件")

# 2-2. location分離
print("\n[2-2] location分離")
location_samples = df_raw['location'].head(5).tolist()
print(f"  サンプル: {location_samples}")

# 都道府県パターン検証
prefecture_pattern = r'^([^都道府県]+[都道府県])'
failed_location = 0
for sample in df_raw['location']:
    parsed = normalizer.parse_location(sample)
    if parsed['prefecture'] is None and sample and str(sample).strip() != '':
        failed_location += 1

if failed_location > 0:
    print(f"   パース失敗: {failed_location}件")
    issues_stage2.append({
        'category': 'location分離',
        'issue': f'{failed_location}件のlocationをパースできませんでした',
        'severity': 'MEDIUM',
        'recommendation': '都道府県パターンの拡張（例: "東京都"以外のケース）'
    })
else:
    print(f"   パース成功: 全件")

# 2-3. desired_area展開
print("\n[2-3] desired_area展開")
desired_area_samples = df_raw['desired_area'].head(3).tolist()
print(f"  サンプル: {desired_area_samples}")

# カンマ区切りパースの検証
problematic_areas = []
for sample in df_raw['desired_area'].head(100):
    if pd.notna(sample):
        parsed = normalizer.parse_desired_area(sample)
        # カンマ区切り数と実際のパース結果数が一致するか
        expected_count = len(str(sample).split(','))
        actual_count = len(parsed)
        if expected_count != actual_count and actual_count > 0:
            problematic_areas.append(sample)

if problematic_areas:
    print(f"   パース不一致: {len(problematic_areas)}件")
    print(f"    例: {problematic_areas[:2]}")
    issues_stage2.append({
        'category': 'desired_area展開',
        'issue': f'{len(problematic_areas)}件でカンマ区切り数とパース結果数が不一致',
        'severity': 'LOW',
        'recommendation': 'カンマ区切りパースの精度向上'
    })
else:
    print(f"   パース一致: 全件")

# 2-4. desired_job、qualifications、careerパース
print("\n[2-4] desired_job、qualifications、careerパース")

# desired_jobサンプル
if 'desired_job' in df_raw.columns:
    desired_job_samples = df_raw['desired_job'].dropna().head(3).tolist()
    print(f"  desired_jobサンプル: {desired_job_samples}")

# qualificationsサンプル
if 'qualifications' in df_raw.columns:
    qual_samples = df_raw['qualifications'].dropna().head(3).tolist()
    print(f"  qualificationsサンプル: {qual_samples}")

# careerサンプル
if 'career' in df_raw.columns:
    career_samples = df_raw['career'].dropna().head(3).tolist()
    print(f"  careerサンプル: {career_samples}")

    # career parseエラー検証
    failed_career = 0
    for sample in df_raw['career'].head(100):
        if pd.notna(sample):
            parsed = normalizer.parse_career(sample)
            # 学歴レベルが "その他" になる割合を確認
            if parsed['level'] == 'その他' and '大学' not in str(sample):
                failed_career += 1

    if failed_career > 0:
        print(f"   career parse: {failed_career}件が「その他」に分類")
        issues_stage2.append({
            'category': 'career parse',
            'issue': f'{failed_career}件のcareerが「その他」に分類されました',
            'severity': 'LOW',
            'recommendation': '学歴パターンの拡張（専門学校の変種など）'
        })

print(f"\n Stage 2完了: {len(issues_stage2)}件の問題検出")

# ========================================
# STAGE 3: データ変換段階（Transformation Stage）
# ========================================

print("\n" + "=" * 80)
print("【STAGE 3】データ変換段階（Transformation Stage）")
print("-" * 80)

issues_stage3 = []

# 3-1. 年齢層分類
print("\n[3-1] 年齢層分類")
df_normalized = normalizer.normalize_dataframe(df_raw)

# 年齢層の境界値確認
age_bins = [0, 29, 39, 49, 59, 100]
print(f"  年齢層境界値: {age_bins}")

# 年齢層が正しく分類されるか
df_normalized['年齢層'] = pd.cut(
    df_normalized['age'],
    bins=age_bins,
    labels=['20代以下', '30代', '40代', '50代', '60代以上']
)

print(f"  年齢層分布:")
print(df_normalized['年齢層'].value_counts().sort_index())

# 境界値の問題
print(f"\n   境界値の扱い:")
print(f"    29歳 → {pd.cut([29], bins=age_bins, labels=['20代以下', '30代', '40代', '50代', '60代以上'])[0]}")
print(f"    30歳 → {pd.cut([30], bins=age_bins, labels=['20代以下', '30代', '40代', '50代', '60代以上'])[0]}")
print(f"   29歳が「20代以下」、30歳が「30代」→ これは意図した挙動か？")

issues_stage3.append({
    'category': '年齢層分類',
    'issue': '年齢層の境界値定義が曖昧（29歳 vs 30歳の扱い）',
    'severity': 'LOW',
    'recommendation': '境界値の定義を明確化（例: 20-29歳、30-39歳など）'
})

# 3-2. 希望勤務地数の計算
print("\n[3-2] 希望勤務地数の計算")
df_normalized['希望勤務地数'] = df_normalized['desired_area'].apply(
    lambda x: len(str(x).split(',')) if pd.notna(x) and str(x).strip() != '' else 0
)

print(f"  希望勤務地数の分布:")
print(df_normalized['希望勤務地数'].describe())

# 最大値の妥当性チェック
max_desired = df_normalized['希望勤務地数'].max()
if max_desired > 100:
    print(f"   最大値が異常に大きい: {max_desired}箇所")
    print(f"    該当レコード:")
    outlier_record = df_normalized[df_normalized['希望勤務地数'] == max_desired].iloc[0]
    print(f"      member_id: {outlier_record['member_id']}")
    print(f"      desired_area: {outlier_record['desired_area'][:100]}...")

    issues_stage3.append({
        'category': '希望勤務地数',
        'issue': f'最大値が異常に大きい（{max_desired}箇所）',
        'severity': 'MEDIUM',
        'recommendation': '外れ値の除外または上限設定（例: 50箇所以上は50に丸める）'
    })

print(f"\n Stage 3完了: {len(issues_stage3)}件の問題検出")

# ========================================
# STAGE 4: データ検証段階（Validation Stage）
# ========================================

print("\n" + "=" * 80)
print("【STAGE 4】データ検証段階（Validation Stage）")
print("-" * 80)

issues_stage4 = []

# 4-1. 品質検証モードの適切性
print("\n[4-1] 品質検証モードの適切性")
from data_quality_validator import DataQualityValidator

validator_descriptive = DataQualityValidator(validation_mode='descriptive')
validator_inferential = DataQualityValidator(validation_mode='inferential')

print(f"  検証モード:")
print(f"    descriptive: 観察的記述用（サンプルサイズ制約なし）")
print(f"    inferential: 推論的考察用（最小30件/グループ、100件/全体）")

# 4-2. 閾値の妥当性
print("\n[4-2] 閾値の妥当性")
print(f"  現在の閾値:")
print(f"    MIN_SAMPLE_TOTAL: {validator_inferential.MIN_SAMPLE_TOTAL}件")
print(f"    MIN_SAMPLE_GROUP: {validator_inferential.MIN_SAMPLE_GROUP}件")
print(f"    MIN_SAMPLE_CROSS: {validator_inferential.MIN_SAMPLE_CROSS}件")

# 統計学的な根拠
print(f"\n   統計学的根拠:")
print(f"    中心極限定理: n≥30で正規分布に近似")
print(f"    カイ二乗検定: 期待度数≥5が推奨")
print(f"    t検定: 各グループn≥30が理想")
print(f"   現在の閾値は統計学的に妥当")

# 4-3. 欠損値処理の一貫性
print("\n[4-3] 欠損値処理の一貫性")

missing_handling = {
    'age': 'そのまま（欠損扱い）',
    'gender': 'そのまま（欠損扱い）',
    'desired_area': '「なし」を空リストに変換',
    'qualifications': 'そのまま（欠損扱い）',
    'urgency_score': '0（未記載）に変換'
}

print(f"  欠損値処理:")
for col, handling in missing_handling.items():
    print(f"    {col}: {handling}")

print(f"\n   問題: 欠損値の扱いが一貫していない")
issues_stage4.append({
    'category': '欠損値処理',
    'issue': '欠損値の扱いが一貫していない（NaNのまま vs 0に変換 vs 空リスト）',
    'severity': 'MEDIUM',
    'recommendation': '欠損値処理ポリシーを統一（例: すべてNaNのまま、または明示的なデフォルト値）'
})

print(f"\n Stage 4完了: {len(issues_stage4)}件の問題検出")

# ========================================
# STAGE 5: 分析段階（Analysis Stage）
# ========================================

print("\n" + "=" * 80)
print("【STAGE 5】分析段階（Analysis Stage）")
print("-" * 80)

issues_stage5 = []

# 5-1. Phase 2: カイ二乗検定（すでに発見済み）
print("\n[5-1] Phase 2: カイ二乗検定")
print("   既知の問題:")
print("    - 全員が希望勤務地を持つため、従来パターンが実行不可")
print("    - run_complete_v2_FIXED.pyで解決済み")

# 5-2. geocache処理
print("\n[5-2] geocache処理")
print("   現在の実装:")
print("    - キャッシュヒット: geocache.jsonから座標取得")
print("    - キャッシュミス: (None, None)を返す（Google Maps API呼び出しなし）")

geocache_path = Path(r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\output_v2\geocache.json")
if geocache_path.exists():
    with open(geocache_path, 'r', encoding='utf-8') as f:
        geocache = json.load(f)
    print(f"  geocacheサイズ: {len(geocache)}件")

    # 必要な地域が全てキャッシュされているか
    unique_locations = df_normalized['residence_muni'].nunique()
    cache_coverage = len(geocache) / unique_locations if unique_locations > 0 else 0
    print(f"  カバレッジ: {cache_coverage*100:.1f}%（{len(geocache)}/{unique_locations}）")

    if cache_coverage < 0.9:
        print(f"   カバレッジ不足: 地図表示時に一部の地域が表示されない可能性")
        issues_stage5.append({
            'category': 'geocache',
            'issue': f'geocacheのカバレッジ不足（{cache_coverage*100:.1f}%）',
            'severity': 'MEDIUM',
            'recommendation': 'Google Maps APIを使用してキャッシュミス時に自動取得'
        })
else:
    print(f"   geocache.jsonが存在しません")
    issues_stage5.append({
        'category': 'geocache',
        'issue': 'geocache.jsonが存在しない',
        'severity': 'HIGH',
        'recommendation': 'geocache.jsonを事前生成、またはAPIキー設定'
    })

# 5-3. クラスタリング（Phase 3）
print("\n[5-3] クラスタリング（Phase 3）")
print("   現在の実装:")
print("    - 特徴量: 年齢、性別、年齢層、希望勤務地数（4次元）")
print("    - アルゴリズム: K-means（5クラスタ固定）")
print("    - 初期化: random_state=42（再現性あり）")

print(f"\n   潜在的な問題:")
print(f"    1. クラスタ数が固定（5個）→ データ規模に応じて調整が必要")
print(f"    2. 特徴量が限定的 → urgency_score、education_levelなども考慮可能")
print(f"    3. スケーリングなし → 年齢（16-92）と性別（0-1）のスケール差")

issues_stage5.append({
    'category': 'クラスタリング',
    'issue': 'クラスタ数が固定（5個）、特徴量が限定的、スケーリングなし',
    'severity': 'MEDIUM',
    'recommendation': '1. エルボー法でクラスタ数を最適化 2. 特徴量を増やす 3. StandardScalerで正規化'
})

# 5-4. 年齢層のハードコーディング
print("\n[5-4] 年齢層のハードコーディング")
print("   年齢層定義が複数箇所に分散:")
print("    - Phase 2/3/8/10: [0, 29, 39, 49, 59, 100] → 5区分")
print("    - Phase 7: [0, 30, 45, 60, 100] → 4区分")

print(f"\n   問題: 年齢層定義が統一されていない")
issues_stage5.append({
    'category': '年齢層定義',
    'issue': '年齢層定義がPhaseごとに異なる（5区分 vs 4区分）',
    'severity': 'MEDIUM',
    'recommendation': '年齢層定義を設定ファイルまたはクラス定数に統一'
})

print(f"\n Stage 5完了: {len(issues_stage5)}件の問題検出")

# ========================================
# STAGE 6: 出力段階（Output Stage）
# ========================================

print("\n" + "=" * 80)
print("【STAGE 6】出力段階（Output Stage）")
print("-" * 80)

issues_stage6 = []

# 6-1. ファイルパス管理
print("\n[6-1] ファイルパス管理")
print("   現在の実装:")
print("    self.output_dir = csv_path.parent.parent / 'job_medley_project' / 'data' / 'output_v2'")

csv_path_obj = Path(csv_path)
output_dir = csv_path_obj.parent.parent / "job_medley_project" / "data" / "output_v2"
print(f"  実際のパス: {output_dir}")
print(f"  存在: {output_dir.exists()}")

print(f"\n   問題: パス生成ロジックが複雑")
print(f"    - csv_path.parent.parent が正しいディレクトリを指すとは限らない")
print(f"    - CSVファイルの場所によって出力先が変わる")

issues_stage6.append({
    'category': 'ファイルパス管理',
    'issue': '出力ディレクトリのパス生成ロジックが複雑で、CSVファイルの場所に依存',
    'severity': 'MEDIUM',
    'recommendation': '出力ディレクトリを絶対パスまたは設定ファイルで指定'
})

# 6-2. 上書き保護
print("\n[6-2] 上書き保護")
print("   現在の実装:")
print("    - 既存ファイルがあっても上書き（警告なし）")
print("    - タイムスタンプ付きバックアップなし")

print(f"\n   問題: 既存データが意図せず上書きされる")
issues_stage6.append({
    'category': '上書き保護',
    'issue': '既存ファイルの上書き保護がない',
    'severity': 'LOW',
    'recommendation': 'タイムスタンプ付きバックアップ、または上書き確認プロンプト'
})

# 6-3. 出力ファイル数の管理
print("\n[6-3] 出力ファイル数の管理")
expected_files = {
    'phase1': 4,  # Applicants, DesiredWork, AggDesired, MapMetrics
    'phase2': 2,  # ChiSquareTests, ANOVATests
    'phase3': 2,  # PersonaSummary, PersonaDetails
    'phase6': 3,  # MunicipalityFlowEdges, MunicipalityFlowNodes, ProximityAnalysis
    'phase7': 5,  # SupplyDensity, Qualification, AgeGender, Mobility, Persona
    'phase8': 3,  # EducationDistribution, EducationAgeCross, GraduationYear
    'phase10': 3  # UrgencyDistribution, UrgencyAgeCross, UrgencyEmploymentCross
}

print(f"  期待ファイル数:")
for phase, count in expected_files.items():
    print(f"    {phase}: {count}ファイル")

total_expected = sum(expected_files.values())
print(f"  合計: {total_expected}ファイル（品質レポート除く）")

print(f"\n   実際の出力ファイル数を確認する仕組みなし")
issues_stage6.append({
    'category': '出力ファイル数',
    'issue': '期待される出力ファイル数と実際の出力ファイル数を検証する仕組みがない',
    'severity': 'LOW',
    'recommendation': '実行後に出力ファイル数を検証し、不足があれば警告'
})

print(f"\n Stage 6完了: {len(issues_stage6)}件の問題検出")

# ========================================
# 総合レポート
# ========================================

print("\n" + "=" * 80)
print("【総合レポート】")
print("=" * 80)

all_issues = (
    issues_stage1 +
    issues_stage2 +
    issues_stage3 +
    issues_stage4 +
    issues_stage5 +
    issues_stage6
)

print(f"\n総問題数: {len(all_issues)}件")

# 重要度別集計
severity_counts = {}
for issue in all_issues:
    severity = issue.get('severity', 'UNKNOWN')
    severity_counts[severity] = severity_counts.get(severity, 0) + 1

print(f"\n重要度別:")
for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
    count = severity_counts.get(severity, 0)
    if count > 0:
        print(f"  {severity}: {count}件")

# カテゴリ別集計
category_counts = {}
for issue in all_issues:
    category = issue.get('category', 'UNKNOWN')
    category_counts[category] = category_counts.get(category, 0) + 1

print(f"\nカテゴリ別:")
for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {category}: {count}件")

# 優先対応リスト（CRITICAL + HIGH）
print(f"\n【優先対応リスト】（CRITICAL + HIGH）")
priority_issues = [i for i in all_issues if i.get('severity') in ['CRITICAL', 'HIGH']]
if priority_issues:
    for i, issue in enumerate(priority_issues, 1):
        print(f"\n{i}. [{issue['severity']}] {issue['category']}")
        print(f"   問題: {issue['issue']}")
        print(f"   推奨: {issue.get('recommendation', '未定義')}")
else:
    print("  なし（重大な問題は検出されませんでした）")

# 全問題リスト
print(f"\n【全問題リスト】")
for i, issue in enumerate(all_issues, 1):
    print(f"\n{i}. [{issue['severity']}] {issue['category']}")
    print(f"   問題: {issue['issue']}")
    print(f"   推奨: {issue.get('recommendation', '未定義')}")

print("\n" + "=" * 80)
print("MECE分析完了")
print("=" * 80)
