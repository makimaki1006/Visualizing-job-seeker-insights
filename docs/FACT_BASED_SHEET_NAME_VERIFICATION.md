# ファクトベース シート名完全検証（2025年10月28日）

## 検証方針

**従来の誤り**: PythonCSVImporter.gsとUpload_Bulk37.htmlだけを比較
**正しい検証**: **実際に参照される全GASロジック**とマッピング定義を突合

---

## 検証結果サマリー

| 項目 | 結果 |
|------|------|
| PythonCSVImporter.gsで定義されているシート数 | 37個 |
| 実際にGASファイルで参照されているシート数 | 27個（_PythonMetadata除く） |
| **定義されているが未使用のシート数** | ~~10個~~ → **7個**（3個修正済み） ✅ |
| **使用されているが未定義のシート数** | **0個** ✅ |
| **修正完了日** | **2025年10月28日** 🆕 |

---

## 詳細検証

### ✅ 正常に使用されているシート（27個）

| シート名 | 参照元ファイル | 参照行番号 | Phase |
|---------|--------------|----------|-------|
| MapMetrics | MapVisualization.gs | 37 | 1 |
| Applicants | MapVisualization.gs, PersonaDifficultyChecker.gs, PythonCSVImporter.gs | 84, 19, 283 | 1 |
| DesiredWork | MapVisualization.gs, PythonCSVImporter.gs | 170, 290 | 1 |
| AggDesired | DataValidationEnhanced.gs, PythonCSVImporter.gs | 226, 495, 297 | 1 |
| ChiSquareTests | Phase2Phase3Visualizations.gs | 13 | 2 |
| ANOVATests | Phase2Phase3Visualizations.gs | 129 | 2 |
| PersonaSummary | Phase2Phase3Visualizations.gs, PersonaDifficultyChecker.gs | 244, 17 | 3 |
| PersonaDetails | Phase2Phase3Visualizations.gs, PersonaDifficultyChecker.gs | 352, 18 | 3 |
| Phase6_MunicipalityFlowEdges | MunicipalityFlowNetworkViz.gs | 69 | 6 |
| Phase6_MunicipalityFlowNodes | MunicipalityFlowNetworkViz.gs | 90 | 6 |
| Phase7_SupplyDensity | Phase7SupplyDensityViz.gs | 51 | 7 |
| Phase7_QualificationDist | Phase7QualificationDistViz.gs | 50 | 7 |
| Phase7_AgeGenderCross | Phase7AgeGenderCrossViz.gs | 50 | 7 |
| Phase7_MobilityScore | Phase7MobilityScoreViz.gs | 51 | 7 |
| Phase7_PersonaProfile | Phase7PersonaProfileViz.gs | 50 | 7 |
| P8_EducationDist | Phase8DataImporter.gs | 14 | 8 |
| P8_EduAgeCross | Phase8DataImporter.gs | 39 | 8 |
| P8_EduAgeMatrix | Phase8DataImporter.gs | 67 | 8 |
| P8_GradYearDist | Phase8DataImporter.gs | 87 | 8 |
| P8_QualityInfer | Phase8DataImporter.gs | 111 | 8 |
| P10_UrgencyDist | Phase10DataImporter.gs | 14 | 10 |
| P10_UrgencyAge | Phase10DataImporter.gs | 40 | 10 |
| P10_UrgencyAgeMatrix | MatrixHeatmapViewer.gs | 285 | 10 |
| P10_UrgencyEmp | Phase10DataImporter.gs | 88 | 10 |
| P10_UrgencyEmpMatrix | MatrixHeatmapViewer.gs | 292 | 10 |
| P10_QualityInfer | Phase10DataImporter.gs | 116 | 10 |
| OverallQualityInfer | QualityDashboard.gs | 23 | 0 |

**ステータス**: ✅ すべて正常に参照されている

---

### ⚠️ 定義されているが未使用のシート（10個）

#### 1. ProximityAnalysis（Phase 6）

**定義**: PythonCSVImporter.gs:47
```javascript
{name: 'ProximityAnalysis.csv', sheetName: 'ProximityAnalysis', required: false, phase: 6, subfolder: 'phase6'}
```

**参照箇所**:
- DataValidationEnhanced.gs:156（検証ロジックのみ）
- MenuIntegration.gs:34（コメントアウト: `// 未実装`）

**問題**: 可視化関数が未実装
**影響**: インポートされるが、ユーザーは表示できない（無駄なシート）
**推奨**: 可視化関数 `showProximityAnalysis()` を実装するか、required: falseを維持

#### 2. 品質レポート系シート（9個）

| シート名 | Phase | 使用状況 |
|---------|-------|---------|
| P1_QualityDesc | 1 | QualityDashboard.gs:30で参照 ✅ |
| P1_QualityReport | 1 | **未使用** ❌ |
| P2_QualityInfer | 2 | QualityDashboard.gs:31で参照 ✅ |
| P3_QualityInfer | 3 | QualityDashboard.gs:32で参照 ✅ |
| P6_QualityInfer | 6 | QualityDashboard.gs:33で参照 ✅ |
| P7_QualityInfer | 7 | QualityDashboard.gs:34で参照 ✅ |
| P8_QualityReport | 8 | **未使用** ❌ |
| P8_QualityInfer | 8 | Phase8DataImporter.gs:111で参照 ✅ |
| P10_QualityReport | 10 | **未使用** ❌ |
| P10_QualityInfer | 10 | Phase10DataImporter.gs:116で参照 ✅ |

**分析**:
- **QualityReport.csv（観察的記述用）**: Phase 1, 8, 10で生成されるが、**P1_QualityReportのみ未使用**
- **QualityReport_Inferential.csv（推論的考察用）**: すべてのPhaseで生成され、QualityDashboard.gsまたは各PhaseDataImporter.gsで参照されている ✅

**問題**:
1. **P1_QualityReport**がインポートされるが、どこでも参照されていない
2. **P8_QualityReport、P10_QualityReport**も未使用

**推奨**:
- P1_QualityReportをQualityDashboard.gsに追加
- P8_QualityReport、P10_QualityReportをPhase8DataImporter.gs、Phase10DataImporter.gsに追加
- または、QualityReport.csvのインポート自体を停止（QualityReport_Inferential.csvのみで十分）

---

### ✅ 使用されているが未定義のシート（0個）

**結果**: すべての使用シートがPythonCSVImporter.gsで定義されている

---

## 重大な不一致の発見

### ❌ Upload_Bulk37.htmlとPythonCSVImporter.gsの不一致（修正済み）

**修正前**:
- Upload_Bulk37.html: `'UrgencyAgeCross.csv': { phase: 10, sheet: 'P10_UrgencyAgeCross' }`
- PythonCSVImporter.gs: `{name: 'UrgencyAgeCross.csv', sheetName: 'P10_UrgencyAge'}`

**実際の参照**: Phase10DataImporter.gs:40で `P10_UrgencyAge` を使用

**修正済み**: Upload_Bulk37.htmlを `P10_UrgencyAge` に修正

---

## MenuIntegration.gsのメニュー定義と実装の一致確認

### Phase 8メニュー（lines 40-44）

| メニュー項目 | 関数名 | シート名 | 実装状況 |
|------------|--------|---------|---------|
| 📊 学歴分布グラフ | showPhase8EducationDistribution | P8_EducationDist | ✅ 実装済み |
| 🔥 学歴×年齢ヒートマップ | showPhase8EducationAgeMatrixHeatmap | P8_EduAgeMatrix | ✅ 実装済み（MatrixHeatmapViewer.gs） |
| 🎯 統合ダッシュボード | showPhase8Dashboard | 複数シート | ✅ 実装済み（Phase8DataImporter.gs） |

### Phase 10メニュー（lines 47-52）

| メニュー項目 | 関数名 | シート名 | 実装状況 |
|------------|--------|---------|---------|
| 📊 緊急度分布グラフ | showPhase10UrgencyDistribution | P10_UrgencyDist | ✅ 実装済み |
| 🔥 緊急度×年齢ヒートマップ | showPhase10UrgencyAgeMatrixHeatmap | P10_UrgencyAgeMatrix | ✅ 実装済み（MatrixHeatmapViewer.gs:285） |
| 🔥 緊急度×就業状態ヒートマップ | showPhase10UrgencyEmploymentMatrixHeatmap | P10_UrgencyEmpMatrix | ✅ 実装済み（MatrixHeatmapViewer.gs:292） |
| 🎯 統合ダッシュボード | showPhase10Dashboard | 複数シート | ✅ 実装済み（Phase10DataImporter.gs） |

**ステータス**: ✅ メニュー項目と実装が完全一致

---

## 未実装メニュー項目

### Phase 6（lines 32-36）

```javascript
// .addItem('🏘️ 移動パターン分析', 'showProximityAnalysis') // 未実装
```

**シート**: ProximityAnalysis
**ステータス**: ❌ 未実装（コメントアウト済み）
**推奨**: 実装するか、シート自体を削除

---

## 最終結論（2025年10月28日更新）

### ✅ 一致している項目

1. **Phase 1-10の主要シート**: すべてマッピング定義と実使用が一致
2. **Upload_Bulk37.html**: 修正済み、PythonCSVImporter.gsと完全一致
3. **メニュー項目**: すべて実装済み関数と一致
4. **品質レポートシート**: P1_QualityReport、P8_QualityReport、P10_QualityReportの参照実装完了 🆕

### ⚠️ 要対応項目（2025年10月28日更新）

1. **ProximityAnalysis**: 可視化関数未実装（showProximityAnalysis未実装）- 残件 ⚠️
2. ~~**P1_QualityReport**: インポートされるが未使用~~ - FIXED ✅
3. ~~**P8_QualityReport、P10_QualityReport**: インポートされるが未使用~~ - FIXED ✅

### 推奨アクション

#### ✅ 完了した対応（2025年10月28日実施）

1. **P1_QualityReportをQualityDashboard.gsに追加** - COMPLETED ✅
   - QualityDashboard.gs:30に追加済み
   - `{name: 'P1_QualityReport', phase: 1, label: 'Phase 1: 基礎集計（観察的記述）'}`

2. **P8_QualityReportをPhase8DataImporter.gsに追加** - COMPLETED ✅
   - loadPhase8QualityReport()をリファクタリング
   - P8_QualityReportとP8_QualityInferの両方を読み込む
   - 戻り値: `{descriptive: {...}, inferential: {...}}`
   - 共通関数loadQualityReportFromSheet()を作成

3. **P10_QualityReportをPhase10DataImporter.gsに追加** - COMPLETED ✅
   - loadPhase10QualityReport()をリファクタリング
   - P10_QualityReportとP10_QualityInferの両方を読み込む
   - 戻り値: `{descriptive: {...}, inferential: {...}}`
   - Phase8と同じloadQualityReportFromSheet()を使用
   - generatePhase10DashboardHTML()で両方のレポートを表示

#### 中優先度

3. **showProximityAnalysis()を実装**
   - ProximityAnalysis.csvを可視化する関数を追加
   - MenuIntegration.gs:34のコメントアウトを解除

#### 低優先度（将来対応）

4. **OverallQuality（Root品質レポート）の活用検討**
   - 現在OverallQualityInferのみ使用
   - OverallQualityも表示するか検討

---

## 検証プロセスの改善

### 従来の誤った方法

```
PythonCSVImporter.gs ⇄ Upload_Bulk37.html
（この2つだけを比較）
```

### 正しい方法（ファクトベース）

```
PythonCSVImporter.gs（定義）
    ↓ 突合
実際のGASファイル（使用）
    ├─ MapVisualization.gs
    ├─ Phase2Phase3Visualizations.gs
    ├─ Phase7*.gs (5ファイル)
    ├─ Phase8DataImporter.gs
    ├─ Phase10DataImporter.gs
    ├─ MatrixHeatmapViewer.gs
    ├─ QualityDashboard.gs
    ├─ DataValidationEnhanced.gs
    └─ PersonaDifficultyChecker.gs
```

---

**検証日**: 2025年10月28日
**検証方法**: 全GASファイルの `getSheetByName()` を抽出し、PythonCSVImporter.gsと突合
**ステータス**: ✅ 主要シートは完全一致、⚠️ 3シート未使用
**次回検証予定**: 2025年11月28日
