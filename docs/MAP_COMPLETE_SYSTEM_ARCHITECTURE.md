# MapComplete システム アーキテクチャ（MECE整理, 2025-11-01）

本ドキュメントは Python 分析出力 → Google スプレッドシート → Apps Script サービス → HTML フロントエンドのデータフローを MECE に整理し、実際に参照されている `.gs` / `.html` ファイルとその相関を記録する。アーカイブや未使用バックアップは対象外。

---

## 1. 全体像

```
run_complete_v2_perfect.py
        │
        ├─ python_scripts/data/output_v2/phase*/*.csv  （UTF-8, Phase接頭辞）
        │
        ├─ UnifiedDataImporter.gs / DataImportAndValidation.gs
        │        └─ PhaseX_* シートへロード（例: Phase7_SupplyDensity）
        │
        ├─ QualityAndRegionDashboards.gs / MapCompleteDataBridge.gs
        │        └─ fetchPhaseX関数で地域別データを集約（品質フラグ含む）
        │
        ├─ DataServiceProvider.gs / RegionStateService.gs
        │        └─ MapComplete/旧マップUIへのデータ提供, 地域選択保存
        │
        └─ HTML（MapComplete.html, BubbleMap.html, HeatMap.html, Upload_Enhanced.html, など）
                 └─ スプレッドシートメニュー経由で起動
```

---

## 2. Python 出力とシート名の対応表

| フェーズ | Python CSV 出力（`python_scripts/data/output_v2`） | 想定シート名（取り込み後） | 参照モジュール |
| --- | --- | --- | --- |
| Phase 1 基礎集計 | `phase1/MapMetrics.csv`<br>`phase1/AggDesired.csv`<br>`phase1/Applicants.csv` | `Phase1_MapMetrics`<br>`Phase1_AggDesired`<br>`Phase1_Applicants` | `fetchPhase1Metrics`（QualityAndRegionDashboards.gs）<br>`getMapMetricsData`（Phase1-6UnifiedVisualizations.gs）<br>`getAllVisualizationData`（DataServiceProvider.gs） |
| Phase 2 統計 | `phase2/ChiSquare*.csv`<br>`phase2/ANOVA*.csv` | `Phase2_ChiSquare`<br>`Phase2_ANOVA` | `fetchPhase2Stats`（QualityAndRegionDashboards.gs） |
| Phase 3 ペルソナ | `phase3/PersonaSummary.csv`<br>`phase3/PersonaDetails.csv` | `Phase3_PersonaSummary`<br>`Phase3_PersonaDetails` | `fetchPhase3Persona`（QualityAndRegionDashboards.gs）<br>`showPersonaSummary/Details`（Phase1-6UnifiedVisualizations.gs） |
| Phase 6 フロー | `phase6/FlowEdges.csv`<br>`phase6/FlowNodes.csv` | `Phase6_FlowEdges`<br>`Phase6_FlowNodes` | `showMunicipalityFlowNetworkVisualization`（Phase1-6UnifiedVisualizations.gs） |
| Phase 7 供給/ペルソナ詳細 | `phase7/SupplyDensityMap.csv`<br>`phase7/QualificationDistribution.csv`<br>`phase7/AgeGenderCrossAnalysis.csv`<br>`phase7/MobilityScore.csv`<br>`phase7/DetailedPersonaProfile.csv` | `Phase7_SupplyDensity`<br>`Phase7_QualificationDist`<br>`Phase7_AgeGenderCross`<br>`Phase7_MobilityScore`<br>`Phase7_PersonaProfile` | `fetchPhase7Supply`（QualityAndRegionDashboards.gs）<br>`MapCompleteDataBridge.buildMapCompleteCityData_` |
| Phase 8 キャリア/学歴 | `phase8/CareerDistribution.csv`<br>`phase8/EducationDist.csv`<br>`phase8/GradYearDist.csv` ほか | `Phase8_CareerDistribution`<br>`Phase8_EducationDist`<br>`Phase8_GradYearDist` 等 | `fetchPhase8Education`（QualityAndRegionDashboards.gs）<br>`Phase8UnifiedVisualizations.gs` |
| Phase 10 緊急度 | `phase10/UrgencyDistribution.csv`<br>`phase10/UrgencyAgeCross*.csv`<br>`phase10/UrgencyEmploymentCross*.csv`<br>`phase10/UrgencyByMunicipality.csv` | `Phase10_UrgDist`<br>`Phase10_UrgAge`<br>`Phase10_UrgAge_Matrix`<br>`Phase10_UrgEmp` など（UnifiedDataImporter で定義） | `fetchPhase10Urgency`（QualityAndRegionDashboards.gs）<br>`MapCompleteDataBridge.buildMapCompleteCityData_`<br>`Phase10UnifiedVisualizations.gs` |
| 品質レポート | `OverallQualityReport*.csv`<br>`phase*/P*_QualityReport*.csv` | `OverallQualityReport` 等（Phase接頭辞版） | `QualityAndRegionDashboards.gs`（品質ダッシュボード）<br>`MapCompleteDataBridge`（品質ステータス抽出） |

> ※ `UnifiedDataImporter.gs` の `FILE_TO_SHEET_MAP` で CSV → シート名のマッピングが明示されている。取り込み後はすべて Phase 接頭辞付きタブで統一。

---

## 3. Apps Script (.gs) モジュール整理

| 区分 | ファイル | 主な責務 | 主要エントリーポイント |
| --- | --- | --- | --- |
| メニュー統合 | `MenuIntegration.gs` | スプレッドシート UI メニュー「📊データ処理」を構築（インポート、マップ、統計、Phase7/8/10等） | `onOpen` |
| データサービス | `DataServiceProvider.gs` | MapComplete旧UIのデータ供給 (`getAllVisualizationData`)、Google Maps API管理、地域選択保存 (`saveSelectedRegion`) | `showMapComplete`<br>`showMapBubble`<br>`showMapHeatmap` |
| 地域状態 | `RegionStateService.gs` | `saveSelectedRegion`/`loadSelectedRegion` の低レベル実装、都道府県・市区町村一覧取得 | Menu・Map連携 |
| MapComplete Ver2 集約 | `MapCompleteDataBridge.gs` | Phase1/3/7/8/10 の指標・クロス集計を集約し、品質ステータスと `cross_insights` を含む JSON を返すモジュール | `getMapCompleteData` |
| インポート／検証 | `UnifiedDataImporter.gs`<br>`DataImportAndValidation.gs` | CSV取り込み、タブ生成、取り込みダイアログ (`PhaseUpload.html`) | `importPythonCSVDialog` など |
| データ管理ユーティリティ | `DataManagementUtilities.gs` | `checkMapData`, `showStatsSummary`, `clearAllData`, `analyzeDesiredColumns` | メニュー終盤の管理項目 |
| Phase1-6ダッシュボード | `Phase1-6UnifiedVisualizations.gs` | バブル・ヒートマップ、統計可視化、フローネットワーク、統合ダッシュボード | `showBubbleMap`他 |
| Phase7/8/10ダッシュボード | `Phase7UnifiedVisualizations.gs`<br>`Phase8UnifiedVisualizations.gs`<br>`Phase10UnifiedVisualizations.gs` | 各PhaseのHTMLダイアログ生成とチャート描画 | メニューからの `showPhase7...` 等 |
| 品質・地域横断 | `QualityAndRegionDashboards.gs` | `fetchPhaseX` 関数（マップ接頭辞シートから地域別抽出）、品質フラグダッシュボード | `showQualityDashboard` |
| 補助系 | `PersonaDifficultyChecker.gs`（診断UI）<br>`Phase7DataManagement.gs`（Drive連携）<br>`MapVisualization.gs`（旧Leaflet表示） | 各メニュー項目から呼び出し | 該当 `show*` 関数 |

---

## 4. HTML テンプレートの使用状況

| ファイル | 呼び出し元 | 用途 / 備考 |
| --- | --- | --- |
| `MapComplete.html` | `DataServiceProvider.showMapCompleteLegacy`（オプション） | 旧MapCompleteダイアログ（フォールバック用）。 |
| `map_complete_prototype_Ver2.html` | `DataServiceProvider.showMapComplete` | Ver2 UI（クロス分析/品質バッジ対応）を表示するメインダイアログ。 |
| `BubbleMap.html` / `HeatMap.html` | `Phase1-6UnifiedVisualizations.showBubbleMap/HeatMap` | Phase1の地図可視化（バブル/ヒート）。 |
| `Upload_Enhanced.html` | `MenuIntegration.showEnhancedUploadDialog` | ブラウザ内CSVアップロードコンポーネント。 |
| `Phase7Upload.html` / `Phase7BatchUpload.html` / `PhaseUpload.html` | `Phase7DataManagement.gs` / `DataImportAndValidation.gs` | Phase7専用アップロード／統合インポートのダイアログ。 |
| `PersonaDifficultyCheckerUI.html` | `PersonaDifficultyChecker.gs` | ペルソナ難易度診断ダイアログ。 |
| `map_complete_prototype_Ver2.html` | **現時点では Apps Script から未参照**（手動で `HtmlService.createHtmlOutputFromFile` されていない）| 右サイドバー版 MapComplete プロトタイプ。最新改修済み。 |
| `MapComplete_prototype.html` / `MapComplete_v2.html` など | 未使用（テスト用プロトタイプ） | 旧試作版。 |
| `QualityFlagDemoUI.html` / `RegionalDashboard.html` | Quality系デモ／旧地域ダッシュボードで利用（メニュー内ショートカットあり） |

> **現在**：`showMapComplete` は `map_complete_prototype_Ver2.html` を既定で起動し、旧 UI は `showMapCompleteLegacy` としてフォールバックで参照可能。

---

## 5. CSV ↔ シート ↔ GAS 関数の相関表（抜粋）

| 領域 | CSVファイル | シート名 | 主要GAS関数 | HTML/UI |
| --- | --- | --- | --- | --- |
| 地図メトリクス | `phase1/MapMetrics.csv` | `Phase1_MapMetrics` | `fetchPhase1Metrics`（QualityAndRegionDashboards）<br>`getMapMetricsData`（Phase1-6UnifiedVisualizations） | `MapComplete.html`（旧）<br>`map_complete_prototype_Ver2.html`（プロトタイプ） |
| 希望勤務地詳細 | `phase1/AggDesired.csv` | `Phase1_AggDesired` | `fetchPhase1Metrics`（品質・地域チェック） | 同上 |
| 供給密度 | `phase7/SupplyDensityMap.csv` | `Phase7_SupplyDensity` | `fetchPhase7Supply` → `MapCompleteDataBridge` | MapComplete（旧/Ver2）<br>Phase7ダッシュボード |
| 年齢×性別クロス | `phase7/AgeGenderCrossAnalysis.csv` | `Phase7_AgeGenderCross` | `fetchPhase7Supply` → `MapCompleteDataBridge` | MapComplete（Ver2 overview/supplyタブ） |
| 詳細ペルソナ | `phase7/DetailedPersonaProfile.csv` | `Phase7_PersonaProfile` | `buildPersonaTop_`（MapCompleteDataBridge） | MapComplete Ver2 ペルソナタブ |
| 緊急度分布 | `phase10/UrgencyDistribution.csv` | `Phase10_UrgDist` | `fetchPhase10Urgency` → `MapCompleteDataBridge` | MapComplete Ver2 緊急度タブ<br>Phase10ダッシュボード |
| 緊急度×年齢 | `phase10/UrgencyAgeCross.csv` | `Phase10_UrgAge` | `fetchPhase10Urgency` | 同上 |
| 緊急度×就業 | `phase10/UrgencyEmploymentCross.csv` | `Phase10_UrgEmp` | `fetchPhase10Urgency` | 同上 |
| 品質レポート | `OverallQualityReport.csv` 他 | `OverallQualityReport`/`PhaseX_QualityReport` | `extractQualityIssues_`（MapCompleteDataBridge）<br>`showQualityDashboard` | MapComplete Ver2 品質バッジ<br>品質ダッシュボード |

---

## 6. 確認結果と留意点

1. **実際に呼び出されている HTML**  
   - メニューで呼ばれるのは `MapComplete.html`, `BubbleMap.html`, `HeatMap.html`, `Upload_Enhanced.html`, `Phase7Upload.html`, `PhaseUpload.html`, `PersonaDifficultyCheckerUI.html` 等。  
   - `map_complete_prototype_Ver2.html` はまだ `HtmlService.createHtmlOutputFromFile` されておらず、現時点ではデプロイ外。`MapCompleteDataBridge.gs` もこの新UIからの利用を前提としているため、本番適用には `DataServiceProvider.showMapComplete` の切替が必要。

2. **GASモジュールの相互依存**  
- 旧MapComplete UI (`MapComplete.html`) は `showMapCompleteLegacy` から利用でき、従来通り `getAllVisualizationData()` を参照する。  
   - 品質ダッシュボードや `fetchPhaseX` を利用するロジックは `QualityAndRegionDashboards.gs` に集約。`MapCompleteDataBridge` も同関数群に依存している。

3. **Phase10 定義のギャップ**  
   - `QualityAndRegionDashboards.gs` の `REGION_DASHBOARD_SHEETS` は Phase10 の定義が欠落しており、`fetchPhase10Urgency` 利用時に undefined になる恐れがある。MapComplete Ver2 で Phase10 データを利用する際は補完が必須。

4. **Python 出力エンコード**  
   - CSV 先頭に BOM が含まれるため、`MapCompleteDataBridge` 内で `sanitizeString_` を通じて BOM/ゼロ幅スペースを除去する対応を実装済み。Apps Script 側の読み込み (`Utilities.parseCsv`) でも UTF-8 指定を徹底すること。

5. **品質バッジのデータソース**  
   - MapComplete Ver2 UI は `quality` フィールドを受け取り、カラー＋メッセージで表示する。品質レポートシートへ適切にフラグが書き込まれているか、CSV → シート取り込みで確認が必要。

---

## 7. 今後の推奨アクション

1. **UI切替の決定**  
   - MapComplete を Ver2 UI に切り替える場合、`DataServiceProvider.showMapComplete` の参照を `map_complete_prototype_Ver2.html` へ変更し、既存UIとの共存ポリシーを決定する。

2. **Phase10 シート定義の補完**  
   - `REGION_DASHBOARD_SHEETS` に Phase10 のキーを追加し、`fetchPhase10Urgency` の安定動作を保証する。

3. **インポートフローの検証**  
   - `UnifiedDataImporter` が Phase10/Phase7 の増えた CSV（ByMunicipality 等）を適切にマッピングしているかを再確認し、不要なCSVは除外ルールを整備する。

4. **ドキュメント一元化**  
   - 本アーキテクチャドキュメントをベースに、開発者向けハンドブック（例: README 追補）へリンクし、今後の擦り合わせの起点とする。

---

以上。現在稼働中のファイル・データパイプラインを MECE に整理した。追加調査や統合に際しては本表を参照のこと。***
