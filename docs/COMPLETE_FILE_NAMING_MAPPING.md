# 完全版ファイル命名規則とGAS受け入れマッピング

**作成日**: 2025年10月29日
**目的**: 全Phaseのファイル命名規則とGAS側の受け入れ規則を1つずつ丁寧に確認・整理

---

## 📊 現状分析

### ファイル生成状況（実際の確認結果）

```
✅ Phase別ファイル（P{Phase}_*.csv）: 既に生成されている
❌ 旧形式ファイル（QualityReport*.csv）: まだ残存している（重複問題）
```

---

## 📁 Phase 1: 基礎集計（6ファイル → 4ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase1/
├── Applicants.csv                    ✅ メインファイル
├── DesiredWork.csv                   ✅ メインファイル
├── AggDesired.csv                    ✅ メインファイル
├── MapMetrics.csv                    ✅ メインファイル
├── P1_QualityReport.csv              ✅ Phase別版（NEW）
├── QualityReport.csv                 ❌ 旧形式（削除予定）
└── QualityReport_Descriptive.csv     ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase1/
├── Applicants.csv                         ✅ 変更なし
├── DesiredWork.csv                        ✅ 変更なし
├── AggDesired.csv                         ✅ 変更なし
├── MapMetrics.csv                         ✅ 変更なし
├── P1_QualityReport.csv                   ✅ 総合品質レポート
└── P1_QualityReport_Descriptive.csv       ✅ 観察的記述品質レポート（新規生成）
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 1: 基本データ（必須）
{name: 'MapMetrics.csv', sheetName: 'MapMetrics', required: true, phase: 1, subfolder: 'phase1'},
{name: 'Applicants.csv', sheetName: 'Applicants', required: true, phase: 1, subfolder: 'phase1'},
{name: 'DesiredWork.csv', sheetName: 'DesiredWork', required: true, phase: 1, subfolder: 'phase1'},
{name: 'AggDesired.csv', sheetName: 'AggDesired', required: true, phase: 1, subfolder: 'phase1'},
{name: 'QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
{name: 'QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},
```

#### 修正後

```javascript
// Phase 1: 基本データ（必須）
{name: 'MapMetrics.csv', sheetName: 'MapMetrics', required: true, phase: 1, subfolder: 'phase1'},
{name: 'Applicants.csv', sheetName: 'Applicants', required: true, phase: 1, subfolder: 'phase1'},
{name: 'DesiredWork.csv', sheetName: 'DesiredWork', required: true, phase: 1, subfolder: 'phase1'},
{name: 'AggDesired.csv', sheetName: 'AggDesired', required: true, phase: 1, subfolder: 'phase1'},
{name: 'P1_QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
{name: 'P1_QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},
```

### Phase 1ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `Applicants.csv` | `Applicants` | - | ✅ | 申請者基本情報 |
| 2 | `DesiredWork.csv` | `DesiredWork` | - | ✅ | 希望勤務地詳細 |
| 3 | `AggDesired.csv` | `AggDesired` | - | ✅ | 集計データ |
| 4 | `MapMetrics.csv` | `MapMetrics` | - | ✅ | 地図表示用（座標付き） |
| 5 | `P1_QualityReport.csv` | `P1_QualityReport` | 総合 | ⬜ | 総合品質レポート |
| 6 | `P1_QualityReport_Descriptive.csv` | `P1_QualityDesc` | 観察的記述 | ⬜ | 観察的記述品質レポート |

**変更点**:
- ✅ `QualityReport.csv` → `P1_QualityReport.csv`（ファイル名変更）
- ✅ `QualityReport_Descriptive.csv` → `P1_QualityReport_Descriptive.csv`（ファイル名変更）
- ⚠️ シート名は変更なし

---

## 📁 Phase 2: 統計分析（4ファイル → 3ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase2/
├── ChiSquareTests.csv                ✅ メインファイル
├── ANOVATests.csv                    ✅ メインファイル
├── P2_QualityReport_Inferential.csv  ✅ Phase別版（NEW）
└── QualityReport_Inferential.csv     ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase2/
├── ChiSquareTests.csv                ✅ 変更なし
├── ANOVATests.csv                    ✅ 変更なし
└── P2_QualityReport_Inferential.csv  ✅ 推論的考察品質レポート
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 2: 統計的検定結果
{name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', required: false, phase: 2, subfolder: 'phase2'},
{name: 'ANOVATests.csv', sheetName: 'ANOVATests', required: false, phase: 2, subfolder: 'phase2'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},
```

#### 修正後

```javascript
// Phase 2: 統計的検定結果
{name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', required: false, phase: 2, subfolder: 'phase2'},
{name: 'ANOVATests.csv', sheetName: 'ANOVATests', required: false, phase: 2, subfolder: 'phase2'},
{name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},
```

### Phase 2ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `ChiSquareTests.csv` | `ChiSquareTests` | - | ⬜ | カイ二乗検定結果 |
| 2 | `ANOVATests.csv` | `ANOVATests` | - | ⬜ | ANOVA検定結果 |
| 3 | `P2_QualityReport_Inferential.csv` | `P2_QualityInfer` | 推論的考察 | ⬜ | 推論的考察品質レポート |

**変更点**:
- ✅ `QualityReport_Inferential.csv` → `P2_QualityReport_Inferential.csv`（ファイル名変更）
- ⚠️ シート名は変更なし

---

## 📁 Phase 3: ペルソナ分析（4ファイル → 3ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase3/
├── PersonaSummary.csv                ✅ メインファイル
├── PersonaDetails.csv                ✅ メインファイル
├── P3_QualityReport_Inferential.csv  ✅ Phase別版（NEW）
└── QualityReport_Inferential.csv     ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase3/
├── PersonaSummary.csv                ✅ 変更なし
├── PersonaDetails.csv                ✅ 変更なし
└── P3_QualityReport_Inferential.csv  ✅ 推論的考察品質レポート
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 3: ペルソナ分析結果
{name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', required: false, phase: 3, subfolder: 'phase3'},
{name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', required: false, phase: 3, subfolder: 'phase3'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},
```

#### 修正後

```javascript
// Phase 3: ペルソナ分析結果
{name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', required: false, phase: 3, subfolder: 'phase3'},
{name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', required: false, phase: 3, subfolder: 'phase3'},
{name: 'P3_QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},
```

### Phase 3ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `PersonaSummary.csv` | `PersonaSummary` | - | ⬜ | ペルソナサマリー |
| 2 | `PersonaDetails.csv` | `PersonaDetails` | - | ⬜ | ペルソナ詳細 |
| 3 | `P3_QualityReport_Inferential.csv` | `P3_QualityInfer` | 推論的考察 | ⬜ | 推論的考察品質レポート |

**変更点**:
- ✅ `QualityReport_Inferential.csv` → `P3_QualityReport_Inferential.csv`（ファイル名変更）
- ⚠️ シート名は変更なし

---

## 📁 Phase 6: フロー分析（5ファイル → 4ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase6/
├── MunicipalityFlowEdges.csv         ✅ メインファイル
├── MunicipalityFlowNodes.csv         ✅ メインファイル
├── ProximityAnalysis.csv             ✅ メインファイル
├── P6_QualityReport_Inferential.csv  ✅ Phase別版（NEW）
└── QualityReport_Inferential.csv     ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase6/
├── MunicipalityFlowEdges.csv         ✅ 変更なし
├── MunicipalityFlowNodes.csv         ✅ 変更なし
├── ProximityAnalysis.csv             ✅ 変更なし
└── P6_QualityReport_Inferential.csv  ✅ 推論的考察品質レポート
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 6: フロー・近接分析
{name: 'MunicipalityFlowEdges.csv', sheetName: 'FlowEdges', required: false, phase: 6, subfolder: 'phase6'},
{name: 'MunicipalityFlowNodes.csv', sheetName: 'FlowNodes', required: false, phase: 6, subfolder: 'phase6'},
{name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},
```

#### 修正後

```javascript
// Phase 6: フロー・近接分析
{name: 'MunicipalityFlowEdges.csv', sheetName: 'FlowEdges', required: false, phase: 6, subfolder: 'phase6'},
{name: 'MunicipalityFlowNodes.csv', sheetName: 'FlowNodes', required: false, phase: 6, subfolder: 'phase6'},
{name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'},
{name: 'P6_QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},
```

### Phase 6ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `MunicipalityFlowEdges.csv` | `FlowEdges` | - | ⬜ | 自治体間フローエッジ |
| 2 | `MunicipalityFlowNodes.csv` | `FlowNodes` | - | ⬜ | 自治体間フローノード |
| 3 | `ProximityAnalysis.csv` | `ProximityAnalysis` | - | ⬜ | 移動パターン分析 |
| 4 | `P6_QualityReport_Inferential.csv` | `P6_QualityInfer` | 推論的考察 | ⬜ | 推論的考察品質レポート |

**変更点**:
- ✅ `QualityReport_Inferential.csv` → `P6_QualityReport_Inferential.csv`（ファイル名変更）
- ⚠️ シート名は変更なし

---

## 📁 Phase 7: 高度分析（7ファイル → 6ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase7/
├── SupplyDensityMap.csv              ✅ メインファイル
├── QualificationDistribution.csv     ✅ メインファイル
├── AgeGenderCrossAnalysis.csv        ✅ メインファイル
├── MobilityScore.csv                 ✅ メインファイル
├── DetailedPersonaProfile.csv        ✅ メインファイル
├── P7_QualityReport_Inferential.csv  ✅ Phase別版（NEW）
└── QualityReport_Inferential.csv     ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase7/
├── SupplyDensityMap.csv              ✅ 変更なし
├── QualificationDistribution.csv     ✅ 変更なし
├── AgeGenderCrossAnalysis.csv        ✅ 変更なし
├── MobilityScore.csv                 ✅ 変更なし
├── DetailedPersonaProfile.csv        ✅ 変更なし
└── P7_QualityReport_Inferential.csv  ✅ 推論的考察品質レポート
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 7: 高度分析
{name: 'SupplyDensityMap.csv', sheetName: 'P7_SupplyDensity', required: false, phase: 7, subfolder: 'phase7'},
{name: 'QualificationDistribution.csv', sheetName: 'P7_Qualification', required: false, phase: 7, subfolder: 'phase7'},
{name: 'AgeGenderCrossAnalysis.csv', sheetName: 'P7_AgeGenderCross', required: false, phase: 7, subfolder: 'phase7'},
{name: 'MobilityScore.csv', sheetName: 'P7_MobilityScore', required: false, phase: 7, subfolder: 'phase7'},
{name: 'DetailedPersonaProfile.csv', sheetName: 'P7_PersonaProfile', required: false, phase: 7, subfolder: 'phase7'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},
```

#### 修正後

```javascript
// Phase 7: 高度分析
{name: 'SupplyDensityMap.csv', sheetName: 'P7_SupplyDensity', required: false, phase: 7, subfolder: 'phase7'},
{name: 'QualificationDistribution.csv', sheetName: 'P7_Qualification', required: false, phase: 7, subfolder: 'phase7'},
{name: 'AgeGenderCrossAnalysis.csv', sheetName: 'P7_AgeGenderCross', required: false, phase: 7, subfolder: 'phase7'},
{name: 'MobilityScore.csv', sheetName: 'P7_MobilityScore', required: false, phase: 7, subfolder: 'phase7'},
{name: 'DetailedPersonaProfile.csv', sheetName: 'P7_PersonaProfile', required: false, phase: 7, subfolder: 'phase7'},
{name: 'P7_QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},
```

### Phase 7ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `SupplyDensityMap.csv` | `P7_SupplyDensity` | - | ⬜ | 人材供給密度マップ |
| 2 | `QualificationDistribution.csv` | `P7_Qualification` | - | ⬜ | 資格別人材分布 |
| 3 | `AgeGenderCrossAnalysis.csv` | `P7_AgeGenderCross` | - | ⬜ | 年齢層×性別クロス分析 |
| 4 | `MobilityScore.csv` | `P7_MobilityScore` | - | ⬜ | 移動許容度スコアリング |
| 5 | `DetailedPersonaProfile.csv` | `P7_PersonaProfile` | - | ⬜ | ペルソナ詳細プロファイル |
| 6 | `P7_QualityReport_Inferential.csv` | `P7_QualityInfer` | 推論的考察 | ⬜ | 推論的考察品質レポート |

**変更点**:
- ✅ `QualityReport_Inferential.csv` → `P7_QualityReport_Inferential.csv`（ファイル名変更）
- ⚠️ シート名は変更なし

---

## 📁 Phase 8: キャリア・学歴分析（8ファイル → 6ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase8/
├── EducationDistribution.csv         ✅ メインファイル
├── EducationAgeCross.csv             ✅ メインファイル
├── EducationAgeCross_Matrix.csv      ✅ メインファイル
├── GraduationYearDistribution.csv    ✅ メインファイル
├── P8_QualityReport.csv              ✅ Phase別版（NEW）
├── P8_QualityReport_Inferential.csv  ✅ Phase別版（NEW）
├── QualityReport.csv                 ❌ 旧形式（削除予定）
└── QualityReport_Inferential.csv     ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase8/
├── EducationDistribution.csv         ✅ 変更なし
├── EducationAgeCross.csv             ✅ 変更なし
├── EducationAgeCross_Matrix.csv      ✅ 変更なし
├── GraduationYearDistribution.csv    ✅ 変更なし
├── P8_QualityReport.csv              ✅ 総合品質レポート
└── P8_QualityReport_Inferential.csv  ✅ 推論的考察品質レポート
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 8: キャリア・学歴分析
{name: 'EducationDistribution.csv', sheetName: 'P8_EducationDist', required: false, phase: 8, subfolder: 'phase8'},
{name: 'EducationAgeCross.csv', sheetName: 'P8_EduAgeCross', required: false, phase: 8, subfolder: 'phase8'},
{name: 'EducationAgeCross_Matrix.csv', sheetName: 'P8_EduAgeMatrix', required: false, phase: 8, subfolder: 'phase8'},
{name: 'GraduationYearDistribution.csv', sheetName: 'P8_GradYearDist', required: false, phase: 8, subfolder: 'phase8'},
{name: 'QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},
```

#### 修正後

```javascript
// Phase 8: キャリア・学歴分析
{name: 'EducationDistribution.csv', sheetName: 'P8_EducationDist', required: false, phase: 8, subfolder: 'phase8'},
{name: 'EducationAgeCross.csv', sheetName: 'P8_EduAgeCross', required: false, phase: 8, subfolder: 'phase8'},
{name: 'EducationAgeCross_Matrix.csv', sheetName: 'P8_EduAgeMatrix', required: false, phase: 8, subfolder: 'phase8'},
{name: 'GraduationYearDistribution.csv', sheetName: 'P8_GradYearDist', required: false, phase: 8, subfolder: 'phase8'},
{name: 'P8_QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
{name: 'P8_QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},
```

### Phase 8ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `EducationDistribution.csv` | `P8_EducationDist` | - | ⬜ | 学歴分布 |
| 2 | `EducationAgeCross.csv` | `P8_EduAgeCross` | - | ⬜ | 学歴×年齢クロス集計 |
| 3 | `EducationAgeCross_Matrix.csv` | `P8_EduAgeMatrix` | - | ⬜ | 学歴×年齢マトリクス |
| 4 | `GraduationYearDistribution.csv` | `P8_GradYearDist` | - | ⬜ | 卒業年分布 |
| 5 | `P8_QualityReport.csv` | `P8_QualityReport` | 総合 | ⬜ | 総合品質レポート |
| 6 | `P8_QualityReport_Inferential.csv` | `P8_QualityInfer` | 推論的考察 | ⬜ | 推論的考察品質レポート |

**変更点**:
- ✅ `QualityReport.csv` → `P8_QualityReport.csv`（ファイル名変更）
- ✅ `QualityReport_Inferential.csv` → `P8_QualityReport_Inferential.csv`（ファイル名変更）
- ⚠️ シート名は変更なし

---

## 📁 Phase 10: 転職意欲・緊急度分析（12ファイル → 10ファイルに削減予定）

### 現状のファイル構成

```
data/output_v2/phase10/
├── UrgencyDistribution.csv                ✅ メインファイル
├── UrgencyDistribution_ByMunicipality.csv ✅ メインファイル
├── UrgencyAgeCross.csv                    ✅ メインファイル
├── UrgencyAgeCross_ByMunicipality.csv     ✅ メインファイル
├── UrgencyAgeCross_Matrix.csv             ✅ メインファイル
├── UrgencyEmploymentCross.csv             ✅ メインファイル
├── UrgencyEmploymentCross_ByMunicipality.csv ✅ メインファイル
├── UrgencyEmploymentCross_Matrix.csv      ✅ メインファイル
├── P10_QualityReport.csv                  ✅ Phase別版（NEW）
├── P10_QualityReport_Inferential.csv      ✅ Phase別版（NEW）
├── QualityReport.csv                      ❌ 旧形式（削除予定）
└── QualityReport_Inferential.csv          ❌ 旧形式（削除予定）
```

### 提案後のファイル構成

```
data/output_v2/phase10/
├── UrgencyDistribution.csv                ✅ 変更なし
├── UrgencyDistribution_ByMunicipality.csv ✅ 変更なし
├── UrgencyAgeCross.csv                    ✅ 変更なし
├── UrgencyAgeCross_ByMunicipality.csv     ✅ 変更なし
├── UrgencyAgeCross_Matrix.csv             ✅ 変更なし
├── UrgencyEmploymentCross.csv             ✅ 変更なし
├── UrgencyEmploymentCross_ByMunicipality.csv ✅ 変更なし
├── UrgencyEmploymentCross_Matrix.csv      ✅ 変更なし
├── P10_QualityReport.csv                  ✅ 総合品質レポート
└── P10_QualityReport_Inferential.csv      ✅ 推論的考察品質レポート
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前）

```javascript
// Phase 10: 転職意欲・緊急度分析
{name: 'UrgencyDistribution.csv', sheetName: 'P10_UrgencyDist', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross_Matrix.csv', sheetName: 'P10_UrgencyAgeMatrix', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross.csv', sheetName: 'P10_UrgencyEmp', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross_Matrix.csv', sheetName: 'P10_UrgencyEmpMatrix', required: false, phase: 10, subfolder: 'phase10'},
{name: 'QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},
```

#### 修正後

```javascript
// Phase 10: 転職意欲・緊急度分析
{name: 'UrgencyDistribution.csv', sheetName: 'P10_UrgencyDist', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyDistribution_ByMunicipality.csv', sheetName: 'P10_UrgencyDistByMuni', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross_ByMunicipality.csv', sheetName: 'P10_UrgencyAgeByMuni', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross_Matrix.csv', sheetName: 'P10_UrgencyAgeMatrix', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross.csv', sheetName: 'P10_UrgencyEmp', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross_ByMunicipality.csv', sheetName: 'P10_UrgencyEmpByMuni', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross_Matrix.csv', sheetName: 'P10_UrgencyEmpMatrix', required: false, phase: 10, subfolder: 'phase10'},
{name: 'P10_QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
{name: 'P10_QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},
```

### Phase 10ファイル詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `UrgencyDistribution.csv` | `P10_UrgencyDist` | - | ⬜ | 緊急度分布（全体） |
| 2 | `UrgencyDistribution_ByMunicipality.csv` | `P10_UrgencyDistByMuni` | - | ⬜ | 緊急度分布（市区町村別） |
| 3 | `UrgencyAgeCross.csv` | `P10_UrgencyAge` | - | ⬜ | 緊急度×年齢クロス集計 |
| 4 | `UrgencyAgeCross_ByMunicipality.csv` | `P10_UrgencyAgeByMuni` | - | ⬜ | 緊急度×年齢クロス（市区町村別） |
| 5 | `UrgencyAgeCross_Matrix.csv` | `P10_UrgencyAgeMatrix` | - | ⬜ | 緊急度×年齢マトリクス |
| 6 | `UrgencyEmploymentCross.csv` | `P10_UrgencyEmp` | - | ⬜ | 緊急度×就業状態クロス集計 |
| 7 | `UrgencyEmploymentCross_ByMunicipality.csv` | `P10_UrgencyEmpByMuni` | - | ⬜ | 緊急度×就業状態クロス（市区町村別） |
| 8 | `UrgencyEmploymentCross_Matrix.csv` | `P10_UrgencyEmpMatrix` | - | ⬜ | 緊急度×就業状態マトリクス |
| 9 | `P10_QualityReport.csv` | `P10_QualityReport` | 総合 | ⬜ | 総合品質レポート |
| 10 | `P10_QualityReport_Inferential.csv` | `P10_QualityInfer` | 推論的考察 | ⬜ | 推論的考察品質レポート |

**変更点**:
- ✅ `QualityReport.csv` → `P10_QualityReport.csv`（ファイル名変更）
- ✅ `QualityReport_Inferential.csv` → `P10_QualityReport_Inferential.csv`（ファイル名変更）
- ✅ `_ByMunicipality` ファイル3つを GAS受け入れリストに追加（漏れていた）
- ⚠️ シート名は変更なし

---

## 📁 統合品質レポート（ルート直下）

### 現状のファイル構成

```
data/output_v2/
├── OverallQualityReport.csv              ✅ 総合品質レポート
└── OverallQualityReport_Inferential.csv  ✅ 推論的考察統合レポート
```

### 提案後のファイル構成

```
data/output_v2/
├── OverallQualityReport.csv              ✅ 変更なし
└── OverallQualityReport_Inferential.csv  ✅ 変更なし
```

### GAS受け入れ規則（PythonCSVImporter.gs）

#### 現状（修正前・修正後とも同じ）

```javascript
// Root統合品質レポート
{name: 'OverallQualityReport.csv', sheetName: 'OverallQuality', required: false, phase: 0, subfolder: ''},
{name: 'OverallQualityReport_Inferential.csv', sheetName: 'OverallQualityInfer', required: false, phase: 0, subfolder: ''}
```

### 統合品質レポート詳細マッピング

| # | Pythonファイル名（修正後） | GASシート名 | 検証モード | 必須 | 備考 |
|---|-------------------------|-----------|----------|------|------|
| 1 | `OverallQualityReport.csv` | `OverallQuality` | 総合 | ⬜ | 全Phase統合品質レポート |
| 2 | `OverallQualityReport_Inferential.csv` | `OverallQualityInfer` | 推論的考察 | ⬜ | 全Phase推論的考察統合レポート |

**変更点**:
- ✅ 変更なし（既にPhase別プレフィックスなしで一意）

---

## 📊 全体サマリー

### ファイル数の変化

| Phase | 現状ファイル数 | 修正後ファイル数 | 削減数 | 削減率 |
|-------|-------------|----------------|-------|--------|
| Phase 1 | 7 | 6 | -1 | 14% |
| Phase 2 | 4 | 3 | -1 | 25% |
| Phase 3 | 4 | 3 | -1 | 25% |
| Phase 6 | 5 | 4 | -1 | 20% |
| Phase 7 | 7 | 6 | -1 | 14% |
| Phase 8 | 8 | 6 | -2 | 25% |
| Phase 10 | 12 | 10 | -2 | 17% |
| Root | 2 | 2 | 0 | 0% |
| **合計** | **49** | **40** | **-9** | **18%** |

**注**: Phase 10で`_ByMunicipality`ファイル3つをGAS受け入れに追加したため、実際のGAS受け入れファイル数は40→43に増加

### 修正が必要なファイル数

| 対象 | ファイル数 | 内容 |
|------|----------|------|
| **Python側** | 12ファイル | Phase別プレフィックスのみ生成するよう修正 |
| **GAS側** | 15行 | `PythonCSVImporter.gs`のファイル名を修正 |
| **削除対象** | 9ファイル | 旧形式ファイルを削除 |

### GASシート名（変更なし）

```
✅ すべてのシート名は既にPhase別プレフィックス付き
✅ ファイル名のみを修正すればOK
```

---

## 🔧 GAS側の完全修正コード

### PythonCSVImporter.gs の requiredFiles 配列（25-78行目）

```javascript
var requiredFiles = [
  // Phase 1: 基本データ（必須）
  {name: 'MapMetrics.csv', sheetName: 'MapMetrics', required: true, phase: 1, subfolder: 'phase1'},
  {name: 'Applicants.csv', sheetName: 'Applicants', required: true, phase: 1, subfolder: 'phase1'},
  {name: 'DesiredWork.csv', sheetName: 'DesiredWork', required: true, phase: 1, subfolder: 'phase1'},
  {name: 'AggDesired.csv', sheetName: 'AggDesired', required: true, phase: 1, subfolder: 'phase1'},
  {name: 'P1_QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
  {name: 'P1_QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},

  // Phase 2: 統計的検定結果
  {name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', required: false, phase: 2, subfolder: 'phase2'},
  {name: 'ANOVATests.csv', sheetName: 'ANOVATests', required: false, phase: 2, subfolder: 'phase2'},
  {name: 'P2_QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},

  // Phase 3: ペルソナ分析結果
  {name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', required: false, phase: 3, subfolder: 'phase3'},
  {name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', required: false, phase: 3, subfolder: 'phase3'},
  {name: 'P3_QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},

  // Phase 6: フロー・近接分析
  {name: 'MunicipalityFlowEdges.csv', sheetName: 'FlowEdges', required: false, phase: 6, subfolder: 'phase6'},
  {name: 'MunicipalityFlowNodes.csv', sheetName: 'FlowNodes', required: false, phase: 6, subfolder: 'phase6'},
  {name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'},
  {name: 'P6_QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},

  // Phase 7: 高度分析
  {name: 'SupplyDensityMap.csv', sheetName: 'P7_SupplyDensity', required: false, phase: 7, subfolder: 'phase7'},
  {name: 'QualificationDistribution.csv', sheetName: 'P7_Qualification', required: false, phase: 7, subfolder: 'phase7'},
  {name: 'AgeGenderCrossAnalysis.csv', sheetName: 'P7_AgeGenderCross', required: false, phase: 7, subfolder: 'phase7'},
  {name: 'MobilityScore.csv', sheetName: 'P7_MobilityScore', required: false, phase: 7, subfolder: 'phase7'},
  {name: 'DetailedPersonaProfile.csv', sheetName: 'P7_PersonaProfile', required: false, phase: 7, subfolder: 'phase7'},
  {name: 'P7_QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},

  // Phase 8: キャリア・学歴分析
  {name: 'EducationDistribution.csv', sheetName: 'P8_EducationDist', required: false, phase: 8, subfolder: 'phase8'},
  {name: 'EducationAgeCross.csv', sheetName: 'P8_EduAgeCross', required: false, phase: 8, subfolder: 'phase8'},
  {name: 'EducationAgeCross_Matrix.csv', sheetName: 'P8_EduAgeMatrix', required: false, phase: 8, subfolder: 'phase8'},
  {name: 'GraduationYearDistribution.csv', sheetName: 'P8_GradYearDist', required: false, phase: 8, subfolder: 'phase8'},
  {name: 'P8_QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
  {name: 'P8_QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},

  // Phase 10: 転職意欲・緊急度分析
  {name: 'UrgencyDistribution.csv', sheetName: 'P10_UrgencyDist', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyDistribution_ByMunicipality.csv', sheetName: 'P10_UrgencyDistByMuni', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyAgeCross_ByMunicipality.csv', sheetName: 'P10_UrgencyAgeByMuni', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyAgeCross_Matrix.csv', sheetName: 'P10_UrgencyAgeMatrix', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyEmploymentCross.csv', sheetName: 'P10_UrgencyEmp', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyEmploymentCross_ByMunicipality.csv', sheetName: 'P10_UrgencyEmpByMuni', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'UrgencyEmploymentCross_Matrix.csv', sheetName: 'P10_UrgencyEmpMatrix', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'P10_QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
  {name: 'P10_QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},

  // Root統合品質レポート
  {name: 'OverallQualityReport.csv', sheetName: 'OverallQuality', required: false, phase: 0, subfolder: ''},
  {name: 'OverallQualityReport_Inferential.csv', sheetName: 'OverallQualityInfer', required: false, phase: 0, subfolder: ''}
];
```

**修正箇所**: 15行（品質レポート12行 + Phase 10追加3行）

---

## ✅ 最終チェックリスト

### Python側の確認

- [ ] Phase 1: `P1_QualityReport.csv`, `P1_QualityReport_Descriptive.csv` を生成
- [ ] Phase 2: `P2_QualityReport_Inferential.csv` を生成
- [ ] Phase 3: `P3_QualityReport_Inferential.csv` を生成
- [ ] Phase 6: `P6_QualityReport_Inferential.csv` を生成
- [ ] Phase 7: `P7_QualityReport_Inferential.csv` を生成
- [ ] Phase 8: `P8_QualityReport.csv`, `P8_QualityReport_Inferential.csv` を生成
- [ ] Phase 10: `P10_QualityReport.csv`, `P10_QualityReport_Inferential.csv` を生成
- [ ] 旧形式ファイル（`QualityReport*.csv`）を生成しない

### GAS側の確認

- [ ] `PythonCSVImporter.gs` の15行を修正
- [ ] Phase 10の`_ByMunicipality`ファイル3つを追加
- [ ] 全43ファイルのマッピングが正しい
- [ ] シート名に変更がないことを確認

### 動作確認

- [ ] Pythonスクリプト実行 → 40ファイル生成確認
- [ ] GASインポート実行 → 43シート作成確認
- [ ] 品質ダッシュボード表示確認
- [ ] ファイル名の一意性確認（ドラッグ&ドロップ）

---

## 📚 関連ドキュメント

- **FILE_NAMING_FIX_PROPOSAL.md**: Python側の修正提案
- **GAS_MODIFICATION_CHECKLIST.md**: GAS側の修正チェックリスト
- **QUALITY_REPORT_NAMING_STRATEGY.md**: Phase別命名戦略
- **DATA_FLOW_CORRELATION.md**: データフロー全体図
