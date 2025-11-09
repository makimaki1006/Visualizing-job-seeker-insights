# シート名マッピング完全検証（2025年10月28日）

## 検証目的

PythonCSVImporter.gs、Upload_Bulk37.html、全可視化関数のシート名が完全一致しているか検証

## 🆕 最新更新（2025年10月28日）

**修正完了**: 品質レポートシート（P1_QualityReport、P8_QualityReport、P10_QualityReport）の参照実装完了

- QualityDashboard.gs: 全Phase品質レポートを統合表示 ✅
- Phase8DataImporter.gs: 観察的記述（P8_QualityReport）と推論的考察（P8_QualityInfer）の両方を読み込み ✅
- Phase10DataImporter.gs: 観察的記述（P10_QualityReport）と推論的考察（P10_QualityInfer）の両方を読み込み ✅

**残件**: ProximityAnalysisの可視化関数未実装（低優先度）

---

## マスターマッピング（PythonCSVImporter.gs: lines 27-78）

```javascript
// Phase 1: 基本データ（必須）
{name: 'MapMetrics.csv', sheetName: 'MapMetrics', required: true, phase: 1, subfolder: 'phase1'},
{name: 'Applicants.csv', sheetName: 'Applicants', required: true, phase: 1, subfolder: 'phase1'},
{name: 'DesiredWork.csv', sheetName: 'DesiredWork', required: true, phase: 1, subfolder: 'phase1'},
{name: 'AggDesired.csv', sheetName: 'AggDesired', required: true, phase: 1, subfolder: 'phase1'},
{name: 'QualityReport.csv', sheetName: 'P1_QualityReport', required: false, phase: 1, subfolder: 'phase1'},
{name: 'QualityReport_Descriptive.csv', sheetName: 'P1_QualityDesc', required: false, phase: 1, subfolder: 'phase1'},

// Phase 2: 統計的検定結果
{name: 'ChiSquareTests.csv', sheetName: 'ChiSquareTests', required: false, phase: 2, subfolder: 'phase2'},
{name: 'ANOVATests.csv', sheetName: 'ANOVATests', required: false, phase: 2, subfolder: 'phase2'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P2_QualityInfer', required: false, phase: 2, subfolder: 'phase2'},

// Phase 3: ペルソナ分析結果
{name: 'PersonaSummary.csv', sheetName: 'PersonaSummary', required: false, phase: 3, subfolder: 'phase3'},
{name: 'PersonaDetails.csv', sheetName: 'PersonaDetails', required: false, phase: 3, subfolder: 'phase3'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P3_QualityInfer', required: false, phase: 3, subfolder: 'phase3'},

// Phase 6: フロー・近接分析
{name: 'MunicipalityFlowEdges.csv', sheetName: 'Phase6_MunicipalityFlowEdges', required: false, phase: 6, subfolder: 'phase6'},
{name: 'MunicipalityFlowNodes.csv', sheetName: 'Phase6_MunicipalityFlowNodes', required: false, phase: 6, subfolder: 'phase6'},
{name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P6_QualityInfer', required: false, phase: 6, subfolder: 'phase6'},

// Phase 7: 高度分析
{name: 'SupplyDensityMap.csv', sheetName: 'Phase7_SupplyDensity', required: false, phase: 7, subfolder: 'phase7'},
{name: 'QualificationDistribution.csv', sheetName: 'Phase7_QualificationDist', required: false, phase: 7, subfolder: 'phase7'},
{name: 'AgeGenderCrossAnalysis.csv', sheetName: 'Phase7_AgeGenderCross', required: false, phase: 7, subfolder: 'phase7'},
{name: 'MobilityScore.csv', sheetName: 'Phase7_MobilityScore', required: false, phase: 7, subfolder: 'phase7'},
{name: 'DetailedPersonaProfile.csv', sheetName: 'Phase7_PersonaProfile', required: false, phase: 7, subfolder: 'phase7'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P7_QualityInfer', required: false, phase: 7, subfolder: 'phase7'},

// Phase 8: キャリア・学歴分析
{name: 'EducationDistribution.csv', sheetName: 'P8_EducationDist', required: false, phase: 8, subfolder: 'phase8'},
{name: 'EducationAgeCross.csv', sheetName: 'P8_EduAgeCross', required: false, phase: 8, subfolder: 'phase8'},
{name: 'EducationAgeCross_Matrix.csv', sheetName: 'P8_EduAgeMatrix', required: false, phase: 8, subfolder: 'phase8'},
{name: 'GraduationYearDistribution.csv', sheetName: 'P8_GradYearDist', required: false, phase: 8, subfolder: 'phase8'},
{name: 'QualityReport.csv', sheetName: 'P8_QualityReport', required: false, phase: 8, subfolder: 'phase8'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P8_QualityInfer', required: false, phase: 8, subfolder: 'phase8'},

// Phase 10: 転職意欲・緊急度分析
{name: 'UrgencyDistribution.csv', sheetName: 'P10_UrgencyDist', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyAgeCross_Matrix.csv', sheetName: 'P10_UrgencyAgeMatrix', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross.csv', sheetName: 'P10_UrgencyEmp', required: false, phase: 10, subfolder: 'phase10'},
{name: 'UrgencyEmploymentCross_Matrix.csv', sheetName: 'P10_UrgencyEmpMatrix', required: false, phase: 10, subfolder: 'phase10'},
{name: 'QualityReport.csv', sheetName: 'P10_QualityReport', required: false, phase: 10, subfolder: 'phase10'},
{name: 'QualityReport_Inferential.csv', sheetName: 'P10_QualityInfer', required: false, phase: 10, subfolder: 'phase10'},

// Root統合品質レポート
{name: 'OverallQualityReport.csv', sheetName: 'OverallQuality', required: false, phase: 0, subfolder: ''},
{name: 'OverallQualityReport_Inferential.csv', sheetName: 'OverallQualityInfer', required: false, phase: 0, subfolder: ''}
```

---

## 検証結果

### ✅ Upload_Bulk37.html (lines 106-160)

| ファイル名 | シート名 | 一致 |
|----------|---------|------|
| MapMetrics.csv | MapMetrics | ✅ |
| Applicants.csv | Applicants | ✅ |
| DesiredWork.csv | DesiredWork | ✅ |
| AggDesired.csv | AggDesired | ✅ |
| ChiSquareTests.csv | ChiSquareTests | ✅ |
| ANOVATests.csv | ANOVATests | ✅ |
| PersonaSummary.csv | PersonaSummary | ✅ |
| PersonaDetails.csv | PersonaDetails | ✅ |
| ProximityAnalysis.csv | ProximityAnalysis | ✅ |

**ステータス**: ✅ 完全一致（修正済み）

---

### ✅ MapVisualization.gs

| 関数 | 行番号 | シート名 | 一致 |
|------|-------|---------|------|
| getMapMetricsData() | 37 | MapMetrics | ✅ |
| getApplicantsStats() | 84 | Applicants | ✅ |
| getDesiredWorkTop10() | 170 | DesiredWork | ✅ |

**ステータス**: ✅ 完全一致

---

### ✅ Phase2Phase3Visualizations.gs

| 関数 | 行番号 | シート名 | 一致 |
|------|-------|---------|------|
| showChiSquareTests() | 13 | ChiSquareTests | ✅ |
| showANOVATests() | 129 | ANOVATests | ✅ |
| showPersonaSummary() | 244 | PersonaSummary | ✅ |
| showPersonaDetails() | 352 | PersonaDetails | ✅ |

**ステータス**: ✅ 完全一致

---

### ✅ PersonaDifficultyChecker.gs

| 行番号 | シート名 | 一致 |
|-------|---------|------|
| 17 | PersonaSummary | ✅ |
| 18 | PersonaDetails | ✅ |
| 19 | Applicants | ✅ |

**ステータス**: ✅ 完全一致

---

### ✅ MunicipalityFlowNetworkViz.gs

| 行番号 | シート名 | 一致 |
|-------|---------|------|
| 69 | Phase6_MunicipalityFlowEdges | ✅ |
| 90 | Phase6_MunicipalityFlowNodes | ✅ |

**ステータス**: ✅ 完全一致

---

### ✅ Phase7関連（5ファイル）

| ファイル | 行番号 | シート名 | 一致 |
|---------|-------|---------|------|
| Phase7SupplyDensityViz.gs | 51 | Phase7_SupplyDensity | ✅ |
| Phase7QualificationDistViz.gs | 50 | Phase7_QualificationDist | ✅ |
| Phase7AgeGenderCrossViz.gs | 50 | Phase7_AgeGenderCross | ✅ |
| Phase7MobilityScoreViz.gs | 51 | Phase7_MobilityScore | ✅ |
| Phase7PersonaProfileViz.gs | 50 | Phase7_PersonaProfile | ✅ |

**ステータス**: ✅ 完全一致

---

### ✅ Phase8DataImporter.gs

| 行番号 | シート名 | 一致 |
|-------|---------|------|
| 14 | P8_EducationDist | ✅ |
| 39 | P8_EduAgeCross | ✅ |
| 67 | P8_EduAgeMatrix | ✅ |
| 87 | P8_GradYearDist | ✅ |
| 124 | P8_QualityReport（観察的記述） | ✅ 🆕 |
| 129 | P8_QualityInfer（推論的考察） | ✅ |

**ステータス**: ✅ 完全一致
**更新**: loadPhase8QualityReport()をリファクタリング（2025年10月28日）
- P8_QualityReportとP8_QualityInferの両方を読み込み
- 戻り値: `{descriptive: {...}, inferential: {...}}`

---

### ✅ Phase10DataImporter.gs

| 行番号 | シート名 | 一致 |
|-------|---------|------|
| 14 | P10_UrgencyDist | ✅ |
| 40 | P10_UrgencyAge | ✅ |
| 68 | P10_UrgencyAgeMatrix | ✅ |
| 88 | P10_UrgencyEmp | ✅ |
| 123 | P10_QualityReport（観察的記述） | ✅ 🆕 |
| 129 | P10_QualityInfer（推論的考察） | ✅ |

**ステータス**: ✅ 完全一致
**更新**: loadPhase10QualityReport()をリファクタリング（2025年10月28日）
- P10_QualityReportとP10_QualityInferの両方を読み込み
- 戻り値: `{descriptive: {...}, inferential: {...}}`
- generatePhase10DashboardHTML()で両方のレポートを表示

---

### ✅ QualityDashboard.gs

| 行番号 | シート名 | 一致 |
|-------|---------|------|
| 23 | OverallQualityInfer | ✅ |
| 30 | P1_QualityReport | ✅ 🆕 |
| 31 | P1_QualityDesc | ✅ |
| 32 | P2_QualityInfer | ✅ 🆕 |
| 33 | P3_QualityInfer | ✅ 🆕 |
| 34 | P6_QualityInfer | ✅ 🆕 |
| 35 | P7_QualityInfer | ✅ 🆕 |
| 36 | P8_QualityReport | ✅ 🆕 |
| 37 | P8_QualityInfer | ✅ |
| 38 | P10_QualityReport | ✅ 🆕 |
| 39 | P10_QualityInfer | ✅ |

**ステータス**: ✅ 完全一致
**更新**: 全Phase品質レポートを統合表示（2025年10月28日）
- P1_QualityReport、P8_QualityReport、P10_QualityReportを追加
- P2, P3, P6, P7のQualityInferも追加（完全性確保）
- 観察的記述と推論的考察を明確に区別

---

### ✅ DataValidationEnhanced.gs

| 行番号 | シート名 | 一致 |
|-------|---------|------|
| 225, 283, 446 | MapMetrics | ✅ |
| 226, 495 | AggDesired | ✅ |
| 282 | Applicants | ✅ |

**ステータス**: ✅ 完全一致

---

## 総合検証結果

### ✅ すべてのファイルで完全一致

| カテゴリ | ファイル数 | 一致数 | 不一致数 |
|---------|----------|-------|---------|
| インポート処理 | 2 | 2 | 0 |
| 可視化関数 | 12 | 12 | 0 |
| データ検証 | 1 | 1 | 0 |
| **合計** | **15** | **15** | **0** |

---

## 検証済みシート名リスト（全37シート）

### Phase 1（6シート）
- MapMetrics
- Applicants
- DesiredWork
- AggDesired
- P1_QualityReport
- P1_QualityDesc

### Phase 2（3シート）
- ChiSquareTests
- ANOVATests
- P2_QualityInfer

### Phase 3（3シート）
- PersonaSummary
- PersonaDetails
- P3_QualityInfer

### Phase 6（4シート）
- Phase6_MunicipalityFlowEdges
- Phase6_MunicipalityFlowNodes
- ProximityAnalysis
- P6_QualityInfer

### Phase 7（6シート）
- Phase7_SupplyDensity
- Phase7_QualificationDist
- Phase7_AgeGenderCross
- Phase7_MobilityScore
- Phase7_PersonaProfile
- P7_QualityInfer

### Phase 8（6シート）
- P8_EducationDist
- P8_EduAgeCross
- P8_EduAgeMatrix
- P8_GradYearDist
- P8_QualityReport
- P8_QualityInfer

### Phase 10（7シート）
- P10_UrgencyDist
- P10_UrgencyAge
- P10_UrgencyAgeMatrix
- P10_UrgencyEmp
- P10_UrgencyEmpMatrix
- P10_QualityReport
- P10_QualityInfer

### Root（2シート）
- OverallQuality
- OverallQualityInfer

---

## 修正履歴

### 2025年10月28日（午前）: Upload_Bulk37.html修正

**修正前（不一致）**:
- MapMetrics.csv → P1_MapMetrics ❌
- Applicants.csv → P1_Applicants ❌
- DesiredWork.csv → P1_DesiredWork ❌
- AggDesired.csv → P1_AggDesired ❌
- ChiSquareTests.csv → P2_ChiSquare ❌
- ANOVATests.csv → P2_ANOVA ❌
- PersonaSummary.csv → P3_PersonaSummary ❌
- PersonaDetails.csv → P3_PersonaDetails ❌
- ProximityAnalysis.csv → P6_Proximity ❌

**修正後（一致）**:
- MapMetrics.csv → MapMetrics ✅
- Applicants.csv → Applicants ✅
- DesiredWork.csv → DesiredWork ✅
- AggDesired.csv → AggDesired ✅
- ChiSquareTests.csv → ChiSquareTests ✅
- ANOVATests.csv → ANOVATests ✅
- PersonaSummary.csv → PersonaSummary ✅
- PersonaDetails.csv → PersonaDetails ✅
- ProximityAnalysis.csv → ProximityAnalysis ✅

---

### 2025年10月28日（午後）: 品質レポートシート参照実装 🆕

**修正内容**:

1. **QualityDashboard.gs（lines 29-40）**
   - P1_QualityReport、P8_QualityReport、P10_QualityReportを追加
   - P2, P3, P6, P7のQualityInferも追加（完全性確保）
   - 全Phase品質レポートを統合表示

2. **Phase8DataImporter.gs（lines 105-169）**
   - loadPhase8QualityReport()をリファクタリング
   - P8_QualityReportとP8_QualityInferの両方を読み込み
   - 戻り値構造変更: `{descriptive: {...}, inferential: {...}}`
   - 共通関数loadQualityReportFromSheet()を作成

3. **Phase10DataImporter.gs（lines 110-174、467-544）**
   - loadPhase10QualityReport()をリファクタリング
   - P10_QualityReportとP10_QualityInferの両方を読み込み
   - 戻り値構造変更: `{descriptive: {...}, inferential: {...}}`
   - generatePhase10DashboardHTML()で両方のレポートを表示

**効果**:
- 未使用シート数: 10個 → 7個（3個修正）
- 観察的記述と推論的考察を明確に区別
- データ品質の透明性向上

---

## 今後のルール

### 1. シート名変更時の必須確認ファイル

シート名を変更する場合、以下**すべて**を確認・修正:

1. **PythonCSVImporter.gs** (requiredFiles配列)
2. **Upload_Bulk37.html** (FILE_MAPPING)
3. **該当するPhaseの可視化関数** (getSheetByName)
4. **DataValidationEnhanced.gs** (検証関数)

### 2. 新Phase追加時の必須作業

1. PythonCSVImporter.gsにマッピング追加
2. Upload_Bulk37.htmlにマッピング追加
3. 可視化関数作成時にシート名を確認
4. このドキュメントを更新

### 3. 定期的な一致確認

- 月1回、このドキュメントを使って全シート名の一致を確認
- 不一致があれば即座に修正

---

**作成日**: 2025年10月28日
**検証者**: Claude
**ステータス**: ✅ 完全一致確認済み
**次回検証予定**: 2025年11月28日
\n- [2025-10-29] ǋL: P10_UrgencyDesired V[giUrgencyDesiredWorkCross.csvjǉAPythonCSVImporter/Upload_Bulk37 mapping XVς݁B
- [2025-10-29] 追記: P10_UrgencyDesired シート（UrgencyDesiredWorkCross.csv）を追加し、PythonCSVImporter/Upload_Bulk37 のマッピングを更新済み。
