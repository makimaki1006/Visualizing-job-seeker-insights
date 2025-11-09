# データパイプライン対応表（v2.2）

Pythonによる CSV 分析から GAS の可視化までを、①入力 → ②処理 → ③出力 → ④連携先 の 4 段で MECE に整理したサマリーです。個別の詳細は既存ドキュメント（例: `docs/DATA_SPECIFICATION.md`, `docs/GAS_COMPLETE_FEATURE_LIST.md` など）を参照してください。

---

## ① 入力 CSV の主要カラム

| カラム | 例 | 意味 / 備考 | Python側での扱い |
| --- | --- | --- | --- |
| `member_id` | `ID_1234` | 候補者の一意 ID | 全フェーズ共通キー。`Applicants.csv` 等に引き継ぎ |
| `page` / `card_index` | `32` / `4` | 元HTMLのページ・カード位置 | ログ用途（分析本体では未使用） |
| `age_gender` | `49歳 女性` | 年齢・性別の混在表記 | `DataNormalizer.parse_age_gender` で `age` / `gender` に分離 |
| `location` | `京都府京都市左京区` | 現住所 | 都道府県・市区町村に分割（Phase1/6の地理分析に利用） |
| `status` | `在職中` | 就業状況 | `Applicants.csv`, Phase10 クロス集計に利用 |
| `employment_status` | `契約社員` | 雇用形態 | Phase10 クロス集計に利用 |
| `desired_area` | `京都府京都市/大阪府大阪市` | 希望勤務地リスト | Phase1 希望勤務地展開、Phase6/7 の移動距離判定に利用 |
| `desired_workstyle` | `日勤のみ` | 希望勤務形態 | Phase7 詳細プロファイルに保存 |
| `desired_start` | `今すぐに` / `2025/12` | 入社希望時期 | 緊急度スコア (`urgency_score`, `urgency_score_dynamic`) を算出 |
| `desired_job` | `介護職(初任者)` | 希望職種 | Phase7 詳細プロファイル・Phase10 指標で参照 |
| `career` | `介護福祉士/専門卒` | 経歴・学歴 | 学歴レベル / 卒業年等へ正規化し Phase8 で利用 |
| `qualifications` | `介護福祉士, 実務者研修` | 資格リスト | Phase7 資格分布に利用 (`primary_qualification` などに分解) |

> 上記以外のHTML由来カラムは保持されますが、現在の処理フローでは参照していません。

---

## ② Python側の処理フロー

| ステップ | モジュール / 関数 | 主な処理内容 | 主な出力 |
| --- | --- | --- | --- |
| 正規化 | `DataNormalizer.normalize_dataframe` | 入力 CSV の正規化（住所分解、希望勤務地配列化、緊急度・資格などの算出、希望勤務地数・範囲の派生） | 正規化済み DataFrame (`self.df_normalized`) |
| 品質検証（観察モード） | `DataQualityValidator(validation_mode='descriptive')` | 欠損・サンプル数チェック、集計用途の品質判定 | `P1_QualityReport.csv`, `P8_QualityReport.csv`, `P10_QualityReport.csv`, `QualityReport_Descriptive.csv`, `OverallQualityReport.csv` |
| 品質検証（推論モード） | `DataQualityValidator(validation_mode='inferential')` | 推論用途のサンプル妥当性評価、クロス集計品質チェック | `P*_QualityReport_Inferential.csv`, `OverallQualityReport_Inferential.csv` |
| フェーズ別エクスポート | `JobMedleyAnalyzerV2.export_phase*` | Phase1/2/3/6/7/8/10 の CSV 生成、品質フラグ付与、統計量算出 | `Applicants.csv`, `ChiSquareTests.csv`, `MunicipalityFlowEdges.csv` など各フェーズ出力 |
| geocache 管理 | `JobMedleyAnalyzerV2._get_coordinates` / `save_geocache` | geocache 参照 → ヒット時は座標再利用、ミス時は都道府県中心＋決定論的オフセットで生成し JSON 追記 | `data/output_v2/geocache.json`, 生成ログ |

---

## ③ Python が生成するファイル一覧

| フェーズ | ファイル | 主なカラム / 用途 | GAS 側シート |
| --- | --- | --- | --- |
| Phase1 (基礎集計) | `Applicants.csv` | `member_id`, `age`, `gender`, `residence_pref`, `employment_status`, `urgency_score` | `Applicants` |
|  | `DesiredWork.csv` | `申請者ID`, `希望勤務地_都道府県`, `希望勤務地_市区町村`, `キー` | `DesiredWork` |
|  | `AggDesired.csv` | 希望勤務地集計 + 品質フラグ | `AggDesired` |
|  | `MapMetrics.csv` | 座標付き集計（緯度・経度・信頼性） | `MapMetrics` |
|  | `P1_QualityReport.csv` / `QualityReport_Descriptive.csv` | 観察モード品質指標 | `P1_QualityReport`, `P1_QualityDesc` |
| Phase2 (統計検定) | `ChiSquareTests.csv` | カイ二乗検定結果、p値、効果量 | `ChiSquareTests` |
|  | `ANOVATests.csv` | 分散分析結果 | `ANOVATests` |
|  | `P2_QualityReport_Inferential.csv` | 推論モード品質 | `P2_QualityInfer` |
| Phase3 (ペルソナ分析) | `PersonaSummary.csv` | クラスタ別指標 | `PersonaSummary` |
|  | `PersonaDetails.csv` | 個票＋クラスタメタ | `PersonaDetails` |
|  | `P3_QualityReport_Inferential.csv` | 推論モード品質 | `P3_QualityInfer` |
| Phase6 (フロー分析) | `MunicipalityFlowEdges.csv` | 居住地→希望地エッジ、件数・距離区分 | `Phase6_MunicipalityFlowEdges` |
|  | `MunicipalityFlowNodes.csv` | ノード係数（入出度等） | `Phase6_MunicipalityFlowNodes` |
|  | `ProximityAnalysis.csv` | 近接性サマリー | `ProximityAnalysis` |
|  | `P6_QualityReport_Inferential.csv` | 推論モード品質 | `P6_QualityInfer` |
| Phase7 (高度分析) | `SupplyDensityMap.csv`, `QualificationDistribution.csv`, `AgeGenderCrossAnalysis.csv`, `MobilityScore.csv`, `DetailedPersonaProfile.csv` | 供給密度、資格分布、年齢×性別クロス、移動許容度、詳細プロファイル | `Phase7_*` 各シート |
|  | `P7_QualityReport_Inferential.csv` | 推論モード品質 | `P7_QualityInfer` |
| Phase8 (学歴分析) | `EducationDistribution.csv`, `EducationAgeCross.csv`, `EducationAgeCross_Matrix.csv`, `GraduationYearDistribution.csv` | 学歴×年齢クロスなど | `P8_EducationDist`, `P8_EduAgeCross`, `P8_EduAgeMatrix`, `P8_GradYearDist` |
|  | `P8_QualityReport.csv` / `P8_QualityReport_Inferential.csv` | 観察 / 推論モード品質 | `P8_QualityReport`, `P8_QualityInfer` |
| Phase10 (緊急度分析) | `UrgencyDistribution.csv`, `UrgencyAgeCross.csv`, `UrgencyEmploymentCross.csv`, `UrgencyDesiredWorkCross.csv`, `UrgencyAgeCross_Matrix.csv`, `UrgencyEmploymentCross_Matrix.csv` | 全体集計 + 市区町村別の緊急度分布・クロス指標（ByMunicipality ファイルで提供） | `P10_UrgencyDist`, `P10_UrgencyAge`, `P10_UrgencyEmp`, `P10_UrgencyDesired`, `P10_UrgencyAgeMatrix`, `P10_UrgencyEmpMatrix` |
|  | `P10_QualityReport.csv` / `P10_QualityReport_Inferential.csv` | 観察 / 推論モード品質 | `P10_QualityReport`, `P10_QualityInfer` |
| 共通 (ルート) | `OverallQualityReport.csv` / `OverallQualityReport_Inferential.csv` | 全カラムを対象にした品質レポート | `OverallQuality`, `OverallQualityInfer` |

---

## ④ GAS 側コンポーネント

### ④-1. インポート／連携レイヤ

| ファイル | 役割 | 参照/生成シート | 対応する Python 出力 |
| --- | --- | --- | --- |
| `gas_files_production/html/Upload_Bulk37.html` | ローカル 37ファイル一括アップロード UI | `google.script.run.importSingleCSVFromHTML` 経由でシート作成 | Stage③の全CSV/JSON |
| `gas_files_production/scripts/PythonCSVImporter.gs` | Drive 上の CSV を `_PythonMetadata` で管理しつつシートへ流し込む中核ロジック | `MapMetrics`, `Applicants`, `DesiredWork`, `AggDesired` など 30シート超 | Stage③ 全ファイル（QualityReport 系含む） |
| `gas_files_production/scripts/Phase7DataImporter.gs` | Phase7 CSV 一括ロードと品質検証 | `Phase7_*`, `P7_QualityInfer` | Phase7 出力 |
| `gas_files_production/scripts/Phase8DataImporter.gs` | Phase8 CSV / 品質レポート読込ヘルパー | `P8_EducationDist`, `P8_EduAgeCross`, `P8_QualityReport`, `P8_QualityInfer` | Phase8 出力 |
| `gas_files_production/scripts/Phase10DataImporter.gs` | Phase10 CSV / 品質レポート読込ヘルパー | `P10_UrgencyDist`, `P10_UrgencyAge`, `P10_UrgencyEmp`, `P10_UrgencyDesired`, `P10_UrgencyDist_Muni`, `P10_UrgencyAge_Muni`, `P10_UrgencyEmp_Muni`, `P10_QualityReport`, `P10_QualityInfer` | Phase10 出力 |
| `gas_files_production/scripts/DataValidationEnhanced.gs` | 各 Phase の期待ファイル存在チェック、品質レポートの警告表示 | `_PythonMetadata`, Phase1 シート群 | Stage③ ファイル群 |

### ④-2. 可視化・ダッシュボードレイヤ

| ファイル | 役割 | 参照シート | 主な Python 出力 |
| --- | --- | --- | --- |
| `MapVisualization.gs` / `Phase7SupplyDensityViz.gs` / `Phase7QualificationDistViz.gs` / `Phase7AgeGenderCrossViz.gs` / `Phase7MobilityScoreViz.gs` / `Phase7PersonaProfileViz.gs` | 地図・グラフ描画とメニュー連携 | `MapMetrics`, `Phase7_*` | Phase1, Phase7 CSV |
| `MunicipalityFlowNetworkViz.gs` | 居住地→希望地ネットワーク描画 | `Phase6_MunicipalityFlowEdges`, `Phase6_MunicipalityFlowNodes` | Phase6 CSV |
| `MatrixHeatmapViewer.gs` | クロス集計ヒートマップ | `EducationAgeCross_Matrix`, `UrgencyAgeCross_Matrix`, `UrgencyEmploymentCross_Matrix` | Phase8 / Phase10 CSV（全体集計、互換維持） |
| `Phase2Phase3Visualizations.gs` | 統計検定・ペルソナ結果の表示 | `ChiSquareTests`, `ANOVATests`, `PersonaSummary`, `PersonaDetails` | Phase2 / Phase3 CSV |
| `PersonaDifficultyChecker.gs` | ペルソナ難易度 UI | `PersonaSummary`, `PersonaDetails`, `Applicants` | Phase1 / Phase3 CSV |
| `QualityDashboard.gs` | 観察 / 推論品質の集約ダッシュボード | `P1_QualityReport`, `P1_QualityDesc`, `P2_QualityInfer`, `…`, `OverallQuality`, `OverallQualityInfer` | 新規 `P*_QualityReport.csv` / `OverallQualityReport.csv` を含む全品質ファイル |
| `Phase7CompleteDashboard.gs` / `Phase7CompleteMenuIntegration.gs` など | Phase7 メニュー統合・UI | `Phase7_*`, `P7_QualityInfer` | Phase7 出力一式 |

---

### 補足

- `P*_QualityReport.csv`（観察モード）を Phase1/8/10/Overall でも生成するように Python を更新済みです。GAS 側マッピング（`PythonCSVImporter.gs`, `Upload_Bulk37.html`, `QualityDashboard.gs`）と整合しています。
- geocache ミス時も決定論的に座標が補完されるため、`MapMetrics.csv` は常に緯度・経度を保持し、GAS 地図描画が途切れません。
