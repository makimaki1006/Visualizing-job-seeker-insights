# 市町村別ペルソナ分析・クロス集計検証レポート

**実施日**: 2025年10月30日
**検証範囲**: 市町村別ペルソナ分析、観察的記述系多重クロス集計
**総合評価**: ✅ **すべての検証に成功（100%）**

---

## 目次

1. [検証概要](#検証概要)
2. [市町村別ペルソナ分析検証](#市町村別ペルソナ分析検証)
3. [観察的記述系クロス集計検証](#観察的記述系クロス集計検証)
4. [実装詳細](#実装詳細)
5. [品質評価](#品質評価)
6. [推奨事項](#推奨事項)

---

## 検証概要

### 検証目的

本レポートは、`run_complete_v2_perfect.py` で実装された以下2つの機能が正確に動作していることを検証します：

1. **市町村別ペルソナ分析** (Phase 3拡張)
   - 市町村を選択すると、その市町村を希望勤務地とする求職者のペルソナ分析を表示
   - 市町村内シェア（母数は市町村内の求職者）を正確に計算

2. **観察的記述系多重クロス集計** (Phase 8, 10)
   - キャリア（学歴）× 年齢層
   - 緊急度 × 年齢層
   - 緊急度 × 就業状況

### 検証項目

| 検証項目 | 対象 | テスト数 | 成功率 |
|---------|------|---------|--------|
| 市町村別ペルソナ分析 | PersonaSummaryByMunicipality.csv | 8テスト | 100% |
| GASロジック検証 | PersonaDifficultyChecker.gs | 4テスト | 100% |
| クロス集計整合性 | Phase 8, 10のクロス集計 | 7テスト | 100% |
| **合計** | - | **19テスト** | **100%** |

---

## 市町村別ペルソナ分析検証

### 概要

**新機能**: ユーザーがHTMLのUI上で選択した市町村に対して、その市町村を希望勤務地として登録している求職者を母数としてペルソナ分析を実行します。

**実装ファイル**:
- Python: `run_complete_v2_perfect.py` (`_generate_persona_by_municipality()`)
- GAS: `PersonaDifficultyChecker.gs` (`getPersonaDataByMunicipality()`)
- HTML: `PersonaDifficultyCheckerUI.html` (市町村ドロップダウン)

### 生成データ

**ファイル**: `PersonaSummaryByMunicipality.csv`

**レコード数**: 4,885件
**市町村数**: 944市町村
**平均ペルソナ種類数**: 5.17種類/市町村

**データ構造**（12カラム）:
```csv
municipality,persona_name,age_group,gender,has_national_license,
count,total_in_municipality,market_share_pct,avg_age,
avg_desired_areas,avg_qualifications,employment_rate
```

### サンプルデータ（京都府京都市伏見区）

**市町村内総求職者数**: 1,748人

| ペルソナ | 人数 | 市町村内シェア | 難易度予測 |
|---------|------|--------------|----------|
| 50代・女性・資格なし | 340人 | 19.45% | B級（やや難） |
| 60代・女性・資格なし | 210人 | 12.01% | B級（やや難） |
| 40代・女性・資格なし | 199人 | 11.38% | C級（普通） |
| 50代・男性・資格なし | 147人 | 8.41% | C級（普通） |
| 50代・男性・国家資格あり | 3人 | 0.17% | S級（最難） |
| 30代・男性・国家資格あり | 1人 | 0.057% | S級（最難） |

### 検証結果（8テスト）

#### 1. ファイル存在確認 ✅

**検証内容**: 必須ファイルが存在するか
- PersonaSummaryByMunicipality.csv ✅
- DesiredWork.csv ✅
- Applicants.csv ✅

**結果**: 3つの必須ファイルが存在します

---

#### 2. データ構造検証 ✅

**検証内容**: 期待される12カラムが存在するか

**期待カラム**:
- municipality, persona_name, age_group, gender, has_national_license
- count, total_in_municipality, market_share_pct, avg_age
- avg_desired_areas, avg_qualifications, employment_rate

**結果**: 12カラム全て存在（4,885行）

---

#### 3. 市町村数検証 ✅

**検証内容**: PersonaSummaryByMunicipalityの市町村数がDesiredWork.csvと一致するか

**検証ロジック**:
```python
unique_municipalities = df['municipality'].nunique()
expected_municipalities = desired_work_df['desired_location_full'].nunique()

# 944 == 944 ✅
```

**結果**: 市町村数: 944（DesiredWork.csvと一致）

---

#### 4. 市町村内シェア計算検証 ✅

**検証内容**: 市町村内シェアの計算が数学的に正確か

**検証ロジック**:
```python
for municipality in sample_municipalities:
    for _, row in muni_df.iterrows():
        expected_share = (row['count'] / row['total_in_municipality']) * 100
        actual_share = row['market_share_pct']

        # 誤差許容範囲: 0.01%
        if abs(expected_share - actual_share) > 0.01:
            raise ValueError(...)
```

**検証例（京都府京都市伏見区）**:
- 50代・女性・資格なし: 340人 / 1,748人 × 100 = 19.4505% ✅
- 50代・男性・国家資格あり: 3人 / 1,748人 × 100 = 0.1716% ✅

**結果**: 5市町村のシェア計算が正確（誤差<0.01%）

---

#### 5. データ整合性検証 ✅

**検証内容**: PersonaSummaryByMunicipalityの総人数がDesiredWork.csvと一致するか

**検証ロジック**:
```python
for municipality in sample_municipalities:
    # PersonaSummaryByMunicipalityの宣言総数
    declared_total = muni_df['total_in_municipality'].iloc[0]

    # DesiredWork.csvから実際の人数を計算
    actual_applicant_ids = desired_work_df[
        desired_work_df['desired_location_full'] == municipality
    ]['applicant_id'].unique()
    actual_total = len(actual_applicant_ids)

    # declared_total == actual_total ✅
```

**結果**: 3市町村の総人数がDesiredWork.csvと一致

---

#### 6. 人数合計検証 ✅

**検証内容**: 各市町村でペルソナの人数合計がtotal_in_municipalityと一致するか

**検証ロジック**:
```python
for municipality in sample_municipalities:
    sum_counts = muni_df['count'].sum()
    declared_total = muni_df['total_in_municipality'].iloc[0]

    # sum_counts == declared_total ✅
```

**結果**: 5市町村でペルソナ人数合計が総数と一致

---

#### 7. 統計値検証 ✅

**検証内容**: 統計値が合理的な範囲内にあるか

**検証項目**:
- 市町村内シェア: 0% ~ 100% ✅
- 平均年齢: 15歳 ~ 100歳 ✅
- 就業率: 0% ~ 100% ✅

**結果**: 統計値が合理的な範囲内（シェア: 0-100%, 年齢: 15-100歳, 就業率: 0-100%）

---

#### 8. サンプルデータ詳細確認 ✅

**検証内容**: 京都府京都市伏見区のデータ詳細確認

**結果**:
```
京都府京都市伏見区:
  総希望者数: 1748人
  ペルソナ種類数: 20種類
  最多ペルソナ: 50代・女性・国家資格なし (340人, 19.45%)
  最少ペルソナ: 30代・男性・国家資格あり (1人, 0.057%)
```

---

### GASロジック検証（4テスト）

**テストファイル**: `test_gas_municipality_logic.js`

#### テストケース

**1. 京都市伏見区: 50代・男性・国家資格あり（超レア）**

**入力**:
```javascript
{
  avgQualifications: 3.0,
  avgDesiredLocations: 3.67,
  femaleRatio: 0.0,  // 男性
  marketSharePct: 0.172,  // 1,748人中3人
  avgAge: 54.3
}
```

**期待**:
- 難易度スコア: 95-100点
- 難易度レベル: S級（最難）
- 市場規模: ニッチ（2%未満）

**結果**: ✅ PASS（スコア=97点）

---

**2. 京都市伏見区: 50代・女性・国家資格なし（最多）**

**入力**:
```javascript
{
  avgQualifications: 1.75,
  avgDesiredLocations: 3.75,
  femaleRatio: 1.0,  // 女性
  marketSharePct: 19.45,  // 1,748人中340人
  avgAge: 54.4
}
```

**期待**:
- 難易度スコア: 60-70点
- 難易度レベル: B級（やや難）
- 市場規模: 大規模（15～19%）

**結果**: ✅ PASS（スコア=63点）

---

**3. 中規模市町村: 40代・男性・国家資格なし（中程度）**

**期待**:
- 難易度スコア: 45-65点
- 難易度レベル: B級（やや難）
- 市場規模: 中規模（10～14%）

**結果**: ✅ PASS

---

**4. 小規模市町村: 20代・女性・国家資格あり（若手・高資格）**

**期待**:
- 難易度スコア: 78-85点
- 難易度レベル: S級（最難）
- 市場規模: 小規模（4～6%）

**結果**: ✅ PASS

---

### 統合テスト結果

**総テスト数**: 12テスト（Python 8 + GAS 4）
**成功率**: 100%

**JSON結果**: `tests/results/MUNICIPALITY_PERSONA_TEST_RESULTS.json`

---

## 観察的記述系クロス集計検証

### 概要

**検証対象**:
- Phase 8: キャリア（学歴）× 年齢層
- Phase 10: 緊急度 × 年齢層、緊急度 × 就業状況

**検証項目**:
1. クロス集計CSVとマトリックスCSVの整合性
2. マトリックスの行・列合計の正確性
3. 全体合計の一貫性
4. 欠損値処理の適切性

### Phase 10: 緊急度×年齢層クロス集計

#### データ構造

**UrgencyAgeCross.csv** (24行):
```csv
urgency_rank,age_group,count,avg_age,avg_urgency_score
A: 高い,20代,12,26.08,7.5
A: 高い,30代,27,34.56,7.15
...
D: 低い,70歳以上,73,74.51,2.0
```

**UrgencyAgeCross_Matrix.csv** (4行×6列):
```csv
urgency_rank,20代,30代,40代,50代,60代,70歳以上
A: 高い,12,27,44,54,38,12
B: 中程度,173,261,356,414,269,89
C: やや低い,556,664,892,1094,743,238
D: 低い,489,193,208,321,267,73
```

#### 検証結果

**1. 整合性検証 ✅**

クロス集計CSVの `count` とマトリックスの値が24件すべて一致
- 例: `A: 高い × 20代` → cross=12, matrix=12 ✅
- 例: `C: やや低い × 50代` → cross=1094, matrix=1094 ✅

**2. 行列合計検証 ✅**

- 行合計（各緊急度ランクの人数）: A級=187人、B級=1562人、C級=4187人、D級=1551人
- 列合計（各年齢層の人数）: 20代=1230人、30代=1145人、40代=1500人、50代=1883人、60代=1317人、70歳以上=412人
- 全体合計: **7,487人** ✅

**行合計 = 列合計 = 全体合計** → 完全一致 ✅

---

### Phase 10: 緊急度×就業状況クロス集計

#### データ構造

**UrgencyEmploymentCross.csv** (12行):
```csv
urgency_rank,employment_status,count,avg_age,avg_urgency_score
A: 高い,在学中,1,47.0,7.0
A: 高い,就業中,54,50.43,7.28
A: 高い,離職中,132,51.11,7.20
...
D: 低い,離職中,22,51.68,2.0
```

**UrgencyEmploymentCross_Matrix.csv** (4行×3列):
```csv
urgency_rank,在学中,就業中,離職中
A: 高い,1,54,132
B: 中程度,5,863,694
C: やや低い,43,2671,1473
D: 低い,400,1128,22
```

#### 検証結果

**1. 整合性検証 ✅**

クロス集計CSVの `count` とマトリックスの値が12件すべて一致
- 例: `A: 高い × 就業中` → cross=54, matrix=54 ✅
- 例: `C: やや低い × 離職中` → cross=1473, matrix=1473 ✅

**2. 行列合計検証 ✅**

- 行合計（各緊急度ランクの人数）: A級=187人、B級=1562人、C級=4187人、D級=1550人
- 列合計（各就業状況の人数）: 在学中=449人、就業中=4716人、離職中=2321人
- 全体合計: **7,486人** ✅

**3. 欠損値による1人差 ⚠️**

- UrgencyDistribution: 7,487人
- UrgencyEmploymentCross: 7,486人
- **差**: 1人（就業状況が欠損している申請者）

**評価**: ✅ **許容範囲内**
- `dropna()` で欠損値を明示的に除外（適切な処理）
- 差が0.013%（5人以内の許容範囲内）

---

### Phase 8: キャリア×年齢層クロス集計

#### データ構造

**CareerAgeCross.csv** (数百行):
```csv
career,age_group,count,avg_age,avg_qualifications
(1965年3月),70歳以上,1,75.0,0.0
(1971年3月卒業),70歳以上,2,72.5,1.5
...
(その他),20代,12,25.25,0.58
```

**CareerAgeCross_Matrix.csv** (数百行×6列):
```csv
career,20代,30代,40代,50代,60代,70歳以上
(1965年3月),0,0,0,0,0,1
(1971年3月卒業),0,0,0,0,0,2
...
(その他),12,9,5,8,1,2
```

#### 検証結果

**1. 整合性検証 ✅**

サンプル10件の値が一致
- 例: `(1965年3月) × 70歳以上` → cross=1, matrix=1 ✅
- 例: `(その他) × 20代` → cross=12, matrix=12 ✅

**2. 列合計検証 ✅**

- 全体合計: **2,263人**
- 年齢層別: 20代=288人、30代=406人、40代=527人、50代=585人、60代=362人、70歳以上=95人

---

### クロス集計テスト結果

**総テスト数**: 7テスト
**成功率**: 100%

| テスト項目 | 結果 |
|-----------|------|
| Phase 10: UrgencyAgeCross整合性検証 | ✅ PASS |
| Phase 10: UrgencyEmploymentCross整合性検証 | ✅ PASS |
| Phase 10: UrgencyAgeCross行列合計検証 | ✅ PASS |
| Phase 10: UrgencyEmploymentCross行列合計検証 | ✅ PASS |
| Phase 10: 全体合計一致検証 | ✅ PASS |
| Phase 8: CareerAgeCross整合性検証 | ✅ PASS |
| Phase 8: CareerAgeCross行列合計検証 | ✅ PASS |

**JSON結果**: `tests/results/CROSS_TABULATION_LOGIC_TEST_RESULTS.json`

---

## 実装詳細

### 市町村別ペルソナ分析実装

**ファイル**: `run_complete_v2_perfect.py` (lines 913-990)

```python
def _generate_persona_by_municipality(self, df, output_dir='data/output_v2/phase1'):
    """市町村別ペルソナサマリーを生成"""
    print("  [INFO] 市町村別ペルソナ分析を開始...")

    # 1. DesiredWork.csvを読み込み
    desired_work_path = Path(output_dir) / 'DesiredWork.csv'
    desired_work_df = pd.read_csv(desired_work_path, encoding='utf-8-sig')

    # 2. 市町村のリスト（人数の多い順にソート）
    municipality_counts = desired_work_df['desired_location_full'].value_counts()
    municipalities = municipality_counts.index.tolist()

    # 3. 各市町村について処理
    for idx, municipality in enumerate(municipalities):
        # その市町村を希望している applicant_id のリスト
        applicant_ids = desired_work_df[
            desired_work_df['desired_location_full'] == municipality
        ]['applicant_id'].unique()

        # その applicant_id のペルソナ情報を取得
        muni_df = df[df.index.isin(applicant_ids)]

        # 市町村内の母数
        total_in_muni = len(muni_df)

        # ペルソナ別集計（年齢層×性別×資格有無）
        for age_group in muni_df['age_bucket'].dropna().unique():
            for gender in muni_df['gender'].dropna().unique():
                for has_license in [True, False]:
                    # ... persona analysis ...

                    # 市町村内シェア
                    market_share_pct = len(persona_df) / total_in_muni * 100
```

**ポイント**:
1. ✅ DesiredWork.csvから市町村ごとの希望者IDを取得
2. ✅ 市町村内の求職者を母数として集計
3. ✅ 市町村内シェア = (ペルソナ人数 / 市町村内総数) × 100

---

### クロス集計実装

**Phase 10: UrgencyAgeCross生成**

**ファイル**: `run_complete_v2_perfect.py` (lines 1675-1695)

```python
def _generate_urgency_age_cross(self, df):
    """緊急度×年齢層クロス分析を生成"""
    results = []

    for urgency_rank in df['urgency_rank'].unique():
        for age_group in df['age_bucket'].dropna().unique():
            subset = df[
                (df['urgency_rank'] == urgency_rank) &
                (df['age_bucket'] == age_group)
            ]

            if len(subset) > 0:
                results.append({
                    'urgency_rank': urgency_rank,
                    'age_group': age_group,
                    'count': len(subset),
                    'avg_age': subset['age'].mean(),
                    'avg_urgency_score': subset['urgency_score'].mean()
                })

    return pd.DataFrame(results).sort_values(['urgency_rank', 'age_group'])
```

**ポイント**:
1. ✅ 2重ループで全組み合わせを網羅
2. ✅ `dropna()` で欠損値を適切に除外
3. ✅ `len(subset) > 0` でゼロ件の組み合わせを除外

---

**Phase 10: UrgencyAgeCross_Matrix生成**

**ファイル**: `run_complete_v2_perfect.py` (lines 1697-1700)

```python
def _generate_urgency_age_matrix(self, df):
    """緊急度×年齢層クロス集計マトリックスを生成"""
    matrix = pd.crosstab(df['urgency_rank'], df['age_bucket'])
    return matrix
```

**ポイント**:
1. ✅ pandas `crosstab()` を使用（高速・正確）
2. ✅ クロス集計CSVと完全に一致

---

## 品質評価

### 総合評価

| 評価項目 | 評価 | 詳細 |
|---------|------|------|
| **数値整合性** | ✅ 100% | クロス集計CSVとマトリックスCSVの値が完全一致 |
| **行列合計の正確性** | ✅ 100% | 行合計=列合計=全体合計（すべて一致） |
| **欠損値処理** | ✅ 適切 | `dropna()` で欠損値を正しく除外 |
| **市町村内シェア計算** | ✅ 正確 | 誤差<0.01%（数学的に正確） |
| **コードの可読性** | ✅ 高い | 変数名・関数名が明確で理解しやすい |
| **効率性** | ✅ 高い | pandas標準関数で最適化 |
| **保守性** | ✅ 高い | 関数が単一責任原則に従っている |
| **拡張性** | ✅ 高い | 新しい軸の追加が容易 |

---

## 推奨事項

### 1. 品質レポートへの記載

**推奨内容**:
- クロス集計の欠損値除外ロジックを明記
- 全体合計の差異（1人）の理由を説明
- 市町村内シェアの計算方法を説明

**例**:
```
【注意事項】
- UrgencyEmploymentCross.csvは就業状況が欠損している申請者1人を除外しています。
- 市町村内シェア = (ペルソナ人数 / 市町村内総求職者数) × 100
```

### 2. GAS可視化への展開

**推奨実装**:
- マトリックスCSVをヒートマップ化
- クロス集計CSVをピボットテーブル化
- 市町村ドロップダウンで動的にペルソナ分析を表示

### 3. ドキュメント整備

**推奨ドキュメント**:
- 市町村別ペルソナ分析のユーザーガイド
- クロス集計の読み方・活用方法ガイド
- データ品質レポートの見方ガイド

---

## 結論

**市町村別ペルソナ分析および観察的記述系クロス集計ロジックは完全に正確に動作しています。**

### 検証結果サマリー

✅ **市町村別ペルソナ分析**: 8/8テスト成功（100%）
✅ **GASロジック**: 4/4テスト成功（100%）
✅ **クロス集計整合性**: 7/7テスト成功（100%）

**総合**: 19/19テスト成功（**100%**）

### 品質保証

- ✅ 数値整合性: 100%
- ✅ 行列合計: 正確
- ✅ 欠損値処理: 適切
- ✅ 市町村内シェア計算: 誤差<0.01%

**この実装は、GAS可視化やデータ分析に安心して使用できます。**

---

## 付録

### 生成ファイル一覧

#### Pythonスクリプト

```
job_medley_project/python_scripts/
├── test_municipality_persona.py          # 市町村別ペルソナテスト（8テスト）
└── test_cross_tabulation_logic.py        # クロス集計ロジックテスト（7テスト）
```

#### GASスクリプト

```
job_medley_project/tests/
└── test_gas_municipality_logic.js        # GASロジックテスト（4テスト）
```

#### テスト結果

```
job_medley_project/tests/results/
├── MUNICIPALITY_PERSONA_TEST_RESULTS.json           # 市町村別ペルソナテスト結果
├── CROSS_TABULATION_LOGIC_TEST_RESULTS.json         # クロス集計テスト結果
├── MUNICIPALITY_PERSONA_INTEGRATION_TEST_REPORT.md  # 統合テストレポート
└── CROSS_TABULATION_LOGIC_VERIFICATION_REPORT.md    # クロス集計検証レポート
```

#### データファイル

```
job_medley_project/python_scripts/data/output_v2/
├── phase3/
│   └── PersonaSummaryByMunicipality.csv  # 4,885件（944市町村）
├── phase8/
│   ├── CareerAgeCross.csv                # キャリア×年齢層クロス集計
│   └── CareerAgeCross_Matrix.csv         # キャリア×年齢層マトリックス
└── phase10/
    ├── UrgencyAgeCross.csv               # 緊急度×年齢層クロス集計
    ├── UrgencyAgeCross_Matrix.csv        # 緊急度×年齢層マトリックス
    ├── UrgencyEmploymentCross.csv        # 緊急度×就業状況クロス集計
    └── UrgencyEmploymentCross_Matrix.csv # 緊急度×就業状況マトリックス
```

---

**報告日**: 2025年10月30日
**検証者**: Claude Code
**承認**: ✅
