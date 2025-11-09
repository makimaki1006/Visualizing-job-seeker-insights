# GAS連携ターゲットファイル一覧

**作成日**: 2025年10月29日
**目的**: Python生成40CSVファイルとGAS連携の対応関係を明確化
**ステータス**: Phase 1-7完了、Phase 8-10要拡張

---

## 📊 Python生成CSVファイル vs GAS対応状況

### Phase 1: 基礎集計（6ファイル）

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| MapMetrics.csv | 944 | ✅ PythonCSVImporter.gs | ✅ MapVisualization.gs | ✅ 完了 |
| Applicants.csv | 7,487 | ✅ PythonCSVImporter.gs | ✅ RegionDashboard.gs | ✅ 完了 |
| DesiredWork.csv | 24,410 | ✅ PythonCSVImporter.gs | ✅ RegionDashboard.gs | ✅ 完了 |
| AggDesired.csv | 944 | ✅ PythonCSVImporter.gs | ✅ MapVisualization.gs | ✅ 完了 |
| P1_QualityReport.csv | 29 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |
| P1_QualityReport_Descriptive.csv | 29 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### Phase 2: 統計分析（3ファイル）

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| ChiSquareTests.csv | 4 | ✅ PythonCSVImporter.gs | ✅ Phase2Phase3Visualizations.gs | ✅ 完了 |
| ANOVATests.csv | 2 | ✅ PythonCSVImporter.gs | ✅ Phase2Phase3Visualizations.gs | ✅ 完了 |
| P2_QualityReport_Inferential.csv | 13 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### Phase 3: ペルソナ分析（3ファイル）

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| PersonaSummary.csv | 24 | ✅ PythonCSVImporter.gs | ✅ PersonaDifficultyChecker.gs | ✅ 完了 |
| PersonaDetails.csv | 12 | ✅ PythonCSVImporter.gs | ✅ PersonaDifficultyChecker.gs | ✅ 完了 |
| P3_QualityReport_Inferential.csv | 11 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### Phase 6: フロー分析（4ファイル）

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| MunicipalityFlowEdges.csv | 18,340 | ✅ PythonCSVImporter.gs | ✅ MunicipalityFlowNetworkViz.gs | ✅ 完了 |
| MunicipalityFlowNodes.csv | 966 | ✅ PythonCSVImporter.gs | ✅ MunicipalityFlowNetworkViz.gs | ✅ 完了 |
| ProximityAnalysis.csv | 7,417 | ✅ PythonCSVImporter.gs | ✅ RegionDashboard.gs | ✅ 完了 |
| P6_QualityReport_Inferential.csv | 21 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### Phase 7: 高度分析（6ファイル）

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| SupplyDensityMap.csv | 944 | ✅ Phase7DataImporter.gs | ✅ Phase7SupplyDensityViz.gs | ✅ 完了 |
| QualificationDistribution.csv | 462 | ✅ Phase7DataImporter.gs | ✅ Phase7QualificationDistViz.gs | ✅ 完了 |
| AgeGenderCrossAnalysis.csv | 12 | ✅ Phase7DataImporter.gs | ✅ Phase7AgeGenderCrossViz.gs | ✅ 完了 |
| MobilityScore.csv | 7,417 | ✅ Phase7DataImporter.gs | ✅ Phase7MobilityScoreViz.gs | ✅ 完了 |
| DetailedPersonaProfile.csv | 34 | ✅ Phase7DataImporter.gs | ✅ Phase7PersonaProfileViz.gs | ✅ 完了 |
| P7_QualityReport_Inferential.csv | 22 | ✅ Phase7DataImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### Phase 8: キャリア・学歴分析（6ファイル）⚠️

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| CareerDistribution.csv | 1,627 | ✅ Phase8DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| CareerAgeCross.csv | 1,696 | ✅ Phase8DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| CareerAgeCross_Matrix.csv | 1,627 | ✅ Phase8DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| GraduationYearDistribution.csv | 68 | ✅ Phase8DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| P8_QualityReport.csv | 5 | ✅ Phase8DataImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |
| P8_QualityReport_Inferential.csv | 5 | ✅ Phase8DataImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### Phase 10: 転職意欲・緊急度分析（10ファイル）⚠️

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| UrgencyDistribution.csv | 4 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyAgeCross.csv | 24 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyAgeCross_Matrix.csv | 4 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyEmploymentCross.csv | 12 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyEmploymentCross_Matrix.csv | 4 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyByMunicipality.csv | 944 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyAgeCross_ByMunicipality.csv | 2,942 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| UrgencyEmploymentCross_ByMunicipality.csv | 1,666 | ✅ Phase10DataImporter.gs | ❌ **未実装** | ⚠️ 可視化要実装 |
| P10_QualityReport.csv | 6 | ✅ Phase10DataImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |
| P10_QualityReport_Inferential.csv | 6 | ✅ Phase10DataImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

### 統合品質レポート（2ファイル）

| Python CSV | 行数 | GASインポーター | GAS可視化 | ステータス |
|-----------|------|----------------|----------|-----------|
| OverallQualityReport.csv | 75 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |
| OverallQualityReport_Inferential.csv | 75 | ✅ PythonCSVImporter.gs | ✅ QualityDashboard.gs | ✅ 完了 |

---

## 📁 GASファイル詳細分類

### 1. データインポーター（6ファイル）

| ファイル名 | サイズ | 対応Phase | 機能 | ステータス |
|-----------|--------|----------|------|-----------|
| **PythonCSVImporter.gs** | 18KB | Phase 1-3, 6 | 汎用CSVインポーター（37ファイル対応） | ✅ 動作確認済み |
| **Phase7DataImporter.gs** | 11KB | Phase 7 | Phase 7専用インポーター（6ファイル） | ✅ 動作確認済み |
| **Phase7AutoImporter.gs** | 12KB | Phase 7 | Google Drive自動インポート | ✅ 動作確認済み |
| **Phase7HTMLUploader.gs** | 6.0KB | Phase 7 | HTMLアップロード機能 | ✅ 動作確認済み |
| **Phase8DataImporter.gs** | 21KB | Phase 8 | Phase 8専用インポーター（6ファイル） | ✅ 実装済み（未テスト） |
| **Phase10DataImporter.gs** | 22KB | Phase 10 | Phase 10専用インポーター（10ファイル） | ✅ 実装済み（未テスト） |
| **UniversalPhaseUploader.gs** | 7.7KB | 全Phase | 汎用アップローダー | ✅ 補助機能 |

### 2. 可視化機能（21ファイル）

#### Phase 1-3, 6 可視化（既存実装）

| ファイル名 | サイズ | 対応Phase | 機能 | ステータス |
|-----------|--------|----------|------|-----------|
| **MapVisualization.gs** | 5.4KB | Phase 1 | バブルマップ可視化 | ✅ 動作確認済み |
| **MapDataProvider.gs** | 2.2KB | Phase 1 | 地図データプロバイダー | ✅ 動作確認済み |
| **Phase2Phase3Visualizations.gs** | 14KB | Phase 2, 3 | 統計分析・ペルソナ可視化 | ✅ 動作確認済み |
| **PersonaDifficultyChecker.gs** | 11KB | Phase 3 | ペルソナ難易度分析 | ✅ 動作確認済み |
| **PersonaMapDataVisualization.gs** | 18KB | Phase 3 | ペルソナ地図可視化 | ✅ 動作確認済み |
| **MunicipalityFlowNetworkViz.gs** | 21KB | Phase 6 | フローネットワーク可視化 | ✅ 動作確認済み |
| **RegionDashboard.gs** | 21KB | Phase 1, 6 | 地域ダッシュボード | ✅ 動作確認済み |
| **RegionStateService.gs** | 7.5KB | Phase 1, 6 | 地域状態管理 | ✅ 動作確認済み |

#### Phase 7 可視化（完全実装）

| ファイル名 | サイズ | 対応CSV | 機能 | ステータス |
|-----------|--------|---------|------|-----------|
| **Phase7SupplyDensityViz.gs** | 12KB | SupplyDensityMap.csv | 人材供給密度マップ | ✅ 動作確認済み |
| **Phase7QualificationDistViz.gs** | 8.1KB | QualificationDistribution.csv | 資格別人材分布 | ✅ 動作確認済み |
| **Phase7AgeGenderCrossViz.gs** | 11KB | AgeGenderCrossAnalysis.csv | 年齢層×性別クロス分析 | ✅ 動作確認済み |
| **Phase7MobilityScoreViz.gs** | 13KB | MobilityScore.csv | 移動許容度スコアリング | ✅ 動作確認済み |
| **Phase7PersonaProfileViz.gs** | 13KB | DetailedPersonaProfile.csv | ペルソナ詳細プロファイル | ✅ 動作確認済み |
| **Phase7PersonaMobilityCrossViz.gs** | 30KB | MobilityScore + PersonaProfile | ペルソナ×移動クロス分析 | ✅ 動作確認済み |
| **Phase7CompleteDashboard.gs** | 17KB | Phase 7全ファイル | Phase 7統合ダッシュボード | ✅ 動作確認済み |

#### Phase 8 可視化（未実装）⚠️

| 必要なファイル | 対応CSV | 機能 | ステータス |
|--------------|---------|------|-----------|
| **Phase8CareerDistributionViz.gs** | CareerDistribution.csv | キャリア分布可視化 | ❌ **要実装** |
| **Phase8CareerAgeCrossViz.gs** | CareerAgeCross.csv | キャリア×年齢クロス分析 | ❌ **要実装** |
| **Phase8CareerMatrixViewer.gs** | CareerAgeCross_Matrix.csv | キャリアマトリックス表示 | ❌ **要実装** |
| **Phase8GraduationYearViz.gs** | GraduationYearDistribution.csv | 卒業年分布可視化 | ❌ **要実装** |
| **Phase8CompleteDashboard.gs** | Phase 8全ファイル | Phase 8統合ダッシュボード | ❌ **要実装** |

#### Phase 10 可視化（未実装）⚠️

| 必要なファイル | 対応CSV | 機能 | ステータス |
|--------------|---------|------|-----------|
| **Phase10UrgencyDistributionViz.gs** | UrgencyDistribution.csv | 緊急度分布可視化 | ❌ **要実装** |
| **Phase10UrgencyAgeCrossViz.gs** | UrgencyAgeCross.csv | 緊急度×年齢クロス分析 | ❌ **要実装** |
| **Phase10UrgencyEmploymentViz.gs** | UrgencyEmploymentCross.csv | 緊急度×就業状態クロス | ❌ **要実装** |
| **Phase10UrgencyMatrixViewer.gs** | *_Matrix.csv | 緊急度マトリックス表示 | ❌ **要実装** |
| **Phase10UrgencyMapViz.gs** | UrgencyByMunicipality.csv | 市区町村別緊急度マップ | ❌ **要実装** |
| **Phase10CompleteDashboard.gs** | Phase 10全ファイル | Phase 10統合ダッシュボード | ❌ **要実装** |

### 3. 品質管理・検証（5ファイル）

| ファイル名 | サイズ | 機能 | ステータス |
|-----------|--------|------|-----------|
| **DataValidationEnhanced.gs** | 19KB | 7種類のデータ検証 | ✅ 動作確認済み |
| **QualityDashboard.gs** | 15KB | 品質ダッシュボード | ✅ 動作確認済み |
| **QualityFlagVisualization.gs** | 16KB | 品質フラグ可視化 | ✅ 動作確認済み |
| **QualityFlagMenuIntegration.gs** | 11KB | 品質フラグメニュー統合 | ✅ 動作確認済み |
| **MatrixHeatmapViewer.gs** | 13KB | マトリックスヒートマップ | ✅ 動作確認済み |

### 4. メニュー統合（6ファイル）

| ファイル名 | サイズ | 対応Phase | 機能 | ステータス |
|-----------|--------|----------|------|-----------|
| **MenuIntegration.gs** | 14KB | Phase 1-6 | 基本メニュー統合 | ✅ 動作確認済み |
| **Phase7MenuIntegration.gs** | 8.6KB | Phase 7 | Phase 7メニュー | ✅ 動作確認済み |
| **Phase7CompleteMenuIntegration.gs** | 8.7KB | Phase 7 | Phase 7完全版メニュー | ✅ 動作確認済み |
| **CompleteMenuIntegration.gs** | 7.1KB | Phase 1-7 | 統合メニュー | ✅ 動作確認済み |
| **Phase8MenuIntegration.gs** | - | Phase 8 | Phase 8メニュー | ❌ **要実装** |
| **Phase10MenuIntegration.gs** | - | Phase 10 | Phase 10メニュー | ❌ **要実装** |

### 5. 統合ダッシュボード（2ファイル）

| ファイル名 | サイズ | 対応Phase | 機能 | ステータス |
|-----------|--------|----------|------|-----------|
| **CompleteIntegratedDashboard.gs** | 37KB | Phase 1-7 | 完全統合ダッシュボード | ✅ 動作確認済み |
| **AllPhasesCompleteDashboard.gs** | - | Phase 1-10 | 全Phase統合ダッシュボード | ❌ **要実装** |

### 6. HTMLファイル（10ファイル）

| ファイル名 | 対応機能 | ステータス |
|-----------|---------|-----------|
| **Upload_Enhanced.html** | 高速CSVアップロード | ✅ 動作確認済み |
| **Phase7Upload.html** | Phase 7 HTMLアップロード | ✅ 動作確認済み |
| **Phase7BatchUpload.html** | Phase 7一括アップロード | ✅ 動作確認済み |
| **PhaseUpload.html** | 汎用Phaseアップロード | ✅ 動作確認済み |
| **PersonaDifficultyCheckerUI.html** | ペルソナ難易度UI | ✅ 動作確認済み |
| **BubbleMap.html** | バブルマップUI | ✅ 動作確認済み |
| **HeatMap.html** | ヒートマップUI | ✅ 動作確認済み |
| **MapComplete.html** | 地図完全版UI | ✅ 動作確認済み |
| **RegionalDashboard.html** | 地域ダッシュボードUI | ✅ 動作確認済み |
| **QualityFlagDemoUI.html** | 品質フラグデモUI | ✅ 動作確認済み |

### 7. 補助ファイル（3ファイル）

| ファイル名 | サイズ | 機能 | ステータス |
|-----------|--------|------|-----------|
| **GoogleMapsAPIConfig.gs** | 5.7KB | Google Maps API設定 | ✅ 動作確認済み |
| **Phase7DirectUploader.gs** | 6.4KB | Phase 7直接アップロード | ✅ 動作確認済み |
| **MapVisualization_Fixed.gs** | 5.8KB | 地図可視化（修正版） | ✅ 動作確認済み |

---

## 🎯 必要なGASファイル実装リスト

### 優先度: 🔴 高（必須）

#### Phase 8 可視化ファイル（5個）

1. **Phase8CareerDistributionViz.gs** ⚠️ 未実装
   - 機能: 1,627種類のキャリア分布を棒グラフで表示
   - 参考: Phase7QualificationDistViz.gs（同様の分布表示）
   - 必要チャート: Column Chart（上位20キャリア）

2. **Phase8CareerAgeCrossViz.gs** ⚠️ 未実装
   - 機能: キャリア×年齢層のクロス分析
   - 参考: Phase7AgeGenderCrossViz.gs
   - 必要チャート: Grouped Bar Chart

3. **Phase8CareerMatrixViewer.gs** ⚠️ 未実装
   - 機能: CareerAgeCross_Matrix.csv（1,627行 x 6列）をヒートマップ表示
   - 参考: MatrixHeatmapViewer.gs
   - 必要チャート: Table with Color Formatting

4. **Phase8GraduationYearViz.gs** ⚠️ 未実装
   - 機能: 卒業年分布（1957-2030）をタイムライン表示
   - 参考: なし（新規機能）
   - 必要チャート: Line Chart / Area Chart

5. **Phase8CompleteDashboard.gs** ⚠️ 未実装
   - 機能: Phase 8の4つの可視化を統合表示
   - 参考: Phase7CompleteDashboard.gs
   - 必要機能: タブ切り替え、データフィルタリング

#### Phase 10 可視化ファイル（6個）

1. **Phase10UrgencyDistributionViz.gs** ⚠️ 未実装
   - 機能: 4つの緊急度ランク（A-D）分布をPie Chartで表示
   - 参考: Phase7QualificationDistViz.gs
   - 必要チャート: Pie Chart + Bar Chart

2. **Phase10UrgencyAgeCrossViz.gs** ⚠️ 未実装
   - 機能: 緊急度×年齢層（24パターン）のクロス分析
   - 参考: Phase7AgeGenderCrossViz.gs
   - 必要チャート: Grouped Column Chart

3. **Phase10UrgencyEmploymentViz.gs** ⚠️ 未実装
   - 機能: 緊急度×就業状態（12パターン）のクロス分析
   - 参考: Phase7AgeGenderCrossViz.gs
   - 必要チャート: Stacked Bar Chart

4. **Phase10UrgencyMatrixViewer.gs** ⚠️ 未実装
   - 機能: UrgencyAgeCross_Matrix.csv（4行 x 6列）をヒートマップ表示
   - 参考: MatrixHeatmapViewer.gs
   - 必要チャート: Table with Color Formatting

5. **Phase10UrgencyMapViz.gs** ⚠️ 未実装
   - 機能: 市区町村別緊急度（944件）を地図で色分け表示
   - 参考: Phase7SupplyDensityViz.gs
   - 必要チャート: Geo Chart / Color-coded Map

6. **Phase10CompleteDashboard.gs** ⚠️ 未実装
   - 機能: Phase 10の5つの可視化を統合表示
   - 参考: Phase7CompleteDashboard.gs
   - 必要機能: タブ切り替え、データフィルタリング

### 優先度: 🟡 中（推奨）

#### メニュー統合ファイル（2個）

1. **Phase8MenuIntegration.gs** ⚠️ 未実装
   - 機能: Phase 8の5つの可視化をメニューに追加
   - 参考: Phase7MenuIntegration.gs
   - 必要機能: サブメニュー「📊 Phase 8: キャリア・学歴分析」

2. **Phase10MenuIntegration.gs** ⚠️ 未実装
   - 機能: Phase 10の6つの可視化をメニューに追加
   - 参考: Phase7MenuIntegration.gs
   - 必要機能: サブメニュー「📊 Phase 10: 転職意欲・緊急度分析」

#### 統合ダッシュボード（1個）

1. **AllPhasesCompleteDashboard.gs** ⚠️ 未実装
   - 機能: Phase 1-10の全可視化を統合表示
   - 参考: CompleteIntegratedDashboard.gs（Phase 1-7のみ）
   - 必要機能: Phase選択、タブ切り替え、統合レポート

### 優先度: 🟢 低（オプション）

#### 補助ファイル（2個）

1. **Phase8DataValidator.gs**
   - 機能: Phase 8データの妥当性検証
   - 参考: DataValidationEnhanced.gs

2. **Phase10DataValidator.gs**
   - 機能: Phase 10データの妥当性検証
   - 参考: DataValidationEnhanced.gs

---

## 📊 実装進捗サマリー

| カテゴリ | 実装済み | 未実装 | 合計 | 進捗率 |
|---------|---------|--------|------|--------|
| データインポーター | 6 | 0 | 6 | 100% ✅ |
| Phase 1-7 可視化 | 15 | 0 | 15 | 100% ✅ |
| Phase 8 可視化 | 0 | 5 | 5 | 0% ❌ |
| Phase 10 可視化 | 0 | 6 | 6 | 0% ❌ |
| 品質管理 | 5 | 0 | 5 | 100% ✅ |
| メニュー統合 | 4 | 2 | 6 | 67% ⚠️ |
| 統合ダッシュボード | 1 | 1 | 2 | 50% ⚠️ |
| HTMLファイル | 10 | 0 | 10 | 100% ✅ |
| **合計** | **41** | **14** | **55** | **75%** |

---

## 🔄 推奨実装順序

### ステップ1: Phase 8可視化（5ファイル）

1. Phase8CareerDistributionViz.gs（キャリア分布）
2. Phase8GraduationYearViz.gs（卒業年）
3. Phase8CareerAgeCrossViz.gs（クロス分析）
4. Phase8CareerMatrixViewer.gs（マトリックス）
5. Phase8CompleteDashboard.gs（統合ダッシュボード）

**参考ファイル**: Phase7QualificationDistViz.gs, Phase7CompleteDashboard.gs

### ステップ2: Phase 10可視化（6ファイル）

1. Phase10UrgencyDistributionViz.gs（緊急度分布）
2. Phase10UrgencyAgeCrossViz.gs（緊急度×年齢）
3. Phase10UrgencyEmploymentViz.gs（緊急度×就業状態）
4. Phase10UrgencyMatrixViewer.gs（マトリックス）
5. Phase10UrgencyMapViz.gs（地図表示）
6. Phase10CompleteDashboard.gs（統合ダッシュボード）

**参考ファイル**: Phase7AgeGenderCrossViz.gs, Phase7SupplyDensityViz.gs, Phase7CompleteDashboard.gs

### ステップ3: メニュー統合（2ファイル）

1. Phase8MenuIntegration.gs
2. Phase10MenuIntegration.gs

**参考ファイル**: Phase7MenuIntegration.gs

### ステップ4: 統合ダッシュボード（1ファイル）

1. AllPhasesCompleteDashboard.gs（Phase 1-10統合）

**参考ファイル**: CompleteIntegratedDashboard.gs

---

## 📝 ファイル命名規則

### 可視化ファイル

```
Phase{N}{DataType}Viz.gs

例:
- Phase8CareerDistributionViz.gs
- Phase10UrgencyDistributionViz.gs
```

### ダッシュボードファイル

```
Phase{N}CompleteDashboard.gs

例:
- Phase8CompleteDashboard.gs
- Phase10CompleteDashboard.gs
```

### メニュー統合ファイル

```
Phase{N}MenuIntegration.gs

例:
- Phase8MenuIntegration.gs
- Phase10MenuIntegration.gs
```

---

## 🎨 Google Chartsタイプ対応表

| データ種類 | 推奨チャート | GASコード例 |
|-----------|-------------|-----------|
| 分布（カテゴリ別） | Column Chart | `Charts.newColumnChart()` |
| 分布（割合） | Pie Chart | `Charts.newPieChart()` |
| クロス分析（2軸） | Grouped Bar Chart | `Charts.newBarChart().setStacked(false)` |
| マトリックス | Table with Color | `Charts.newTableChart()` + ConditionalFormatRule |
| 時系列 | Line Chart | `Charts.newLineChart()` |
| 地図 | Geo Chart | `Charts.newGeoChart()` |

---

## 次のアクション

### Phase 8, 10 GAS連携実装タスク

1. **Phase 8可視化**: 5ファイル作成（約2-3時間）
2. **Phase 10可視化**: 6ファイル作成（約3-4時間）
3. **メニュー統合**: 2ファイル作成（約30分）
4. **統合ダッシュボード**: 1ファイル作成（約1時間）
5. **テスト**: E2Eテスト実行（約1時間）

**合計予想時間**: 約8-10時間

---

**ドキュメント作成日**: 2025年10月29日
**作成者**: Claude Code (Sonnet 4.5)
**ステータス**: Phase 8, 10のGAS実装計画完成
