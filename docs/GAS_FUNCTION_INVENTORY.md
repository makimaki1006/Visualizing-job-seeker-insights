# GAS 可視化ロジック棚卸し（2025-11-01時点）

MapComplete プロトタイプへ統合する前提として、既存 Apps Script（GAS）側の機能を MECE に整理した。

---

## 1. メニュー／データ取り込み関連

| ファイル | 主な機能 | 詳細 |
| --- | --- | --- |
| `MenuIntegration.gs` | スプレッドシート UI メニュー構成 | チーム用メニュー「📊データ処理」を定義。Python 結果の自動インポート、手動アップロード、Map 表示（バブル／ヒート）、統計検定（カイ二乗／ANOVA）、ペルソナ系レポート、Phase6 flow、Phase7～10 の各ダッシュボードとデータ管理メニューを一元化。 |
| `DataServiceProvider.gs` | MapComplete・マップ系サービス提供 | - 各 GAS ダッシュボードで共通利用する `getAllVisualizationData`。<br>- MapComplete 表示 (`showMapComplete`)、旧バブル/ヒートマップ (`showMapBubble`/`showMapHeatmap`)。<br>- Google Maps API キーの保存・検証と script タグ生成。<br>- 市区町村選択状態の保存／復元 (`saveSelectedRegion` 等)。<br>- 都道府県／市区町村リストのキャッシュ化 (`getRegionOptions`)。 |
| `DataManagementUtilities.gs` | データ整合・メンテ系ツール | - `checkMapData`：マップ系データの欠損確認。<br>- `showStatsSummary`：CSV 取り込み後の統計サマリー表示。<br>- `clearAllData`：全シート初期化。<br>- `showDebugLog`：ログ閲覧。<br>- `analyzeDesiredColumns`：希望勤務地列の分析。 |
| `MapCompleteDataBridge.gs` | MapComplete Ver2 向け集約 API | - `getMapCompleteData(prefecture, municipality)` で Phase1/7/10 指標をまとめた JSON を返却。<br>- 地域選択の永続化 (`saveSelectedRegion`) と市区町村リスト生成 (`buildAvailableRegions_`) を橋渡し。<br>- 供給密度・緊急度・ペルソナ等を `buildMapCompleteCityData_()` 配下で算出。 |

---

## 2. Phase1-6 統合可視化（基礎マップ & フロー）

| 機能カテゴリ | 主な関数 | 内容 |
| --- | --- | --- |
| 地図表示（Phase1） | `showBubbleMap` / `showHeatMap` / `getMapMetricsData` | `MapMetrics.csv` と `Applicants.csv` を基に、MarkerCluster＋ヒートマップを表示。求職者数、平均年齢、男女比など基本 KPI を取得。 |
| 統計検定（Phase2） | `showChiSquareTests` / `showANOVATests` | カイ二乗・ANOVA の検定結果 CSV を読み込み、HTML ダイアログにレンダリング。 |
| ペルソナ分析（Phase3） | `showPersonaSummary` / `showPersonaDetails` / `showPersonaMapVisualization` | ペルソナサマリー、詳細リスト、地図上でのペルソナ分布表示。Leaflet マップとフィルター UI を含む。 |
| フローネットワーク（Phase6） | `showMunicipalityFlowNetworkVisualization` / `showCompleteIntegratedDashboard` | 市区町村間の移動パターンをネットワークグラフで描画。`loadMunicipalityFlowData` 等でリンク集計し、D3.js の力学レイアウトを使用。統合ダッシュボードでは Phase1～6 の KPI をタブ構成で表示。 |
| 補助関数 | `loadSheetData_`, `showNoDataAlert_`, `showHtmlDialog_` ほか | CSV シートの読み出し、エラーハンドリング、HTML サニタイズなどの共通ユーティリティ。 |

---

## 3. Phase7 高度分析（供給密度 / モビリティ / ペルソナ詳細）

| 機能カテゴリ | 主な関数 | 内容 |
| --- | --- | --- |
| 供給密度マップ | `showSupplyDensityMap` | 市区町村単位の供給スコアをスキャッターバブルとランク別サマリーで可視化。分位点計算 (`percentile`) を実装。 |
| 資格分布 | `showQualificationDistribution` | 職種別・資格レベル別の棒グラフとテーブル。 |
| 年齢×性別クロス | `showAgeGenderCrossAnalysis` | スタック棒＋セグメント円チャートで年代と性別構成を分析。 |
| モビリティ分析 | `showMobilityScoreAnalysis` | 通勤許容距離・移動スコアをヒストグラム／散布図／構成比で表示。 |
| ペルソナ詳細 | `showDetailedPersonaProfile` / `showPersonaMobilityCrossAnalysis` | ペルソナ毎の KPI、レーダーチャート、特徴カード、比較テーブル。拡張版 (`showPersonaMobilityCrossAnalysisEnhanced`) ではソート・ CSV エクスポート等が可能。 |
| Phase7統合ダッシュボード | `showPhase7CompleteDashboard` | 供給密度・資格分布・年齢／性別クロス・モビリティ・ペルソナをタブ切替で俯瞰。 |

---

## 4. Phase8 キャリア・学歴分析

| 機能カテゴリ | 主な関数 | 内容 |
| --- | --- | --- |
| キャリア分布 | `showCareerDistribution` | キャリア Top100 構成比や KPI を棒グラフ＋テーブルで表示。 |
| キャリア × 年齢クロス | `showCareerAgeCross` / `showCareerAgeMatrix` | 年齢帯とのクロス集計（棒グラフ／ヒートマップ）。 |
| 卒業年分布 | `showGraduationYearDistribution` | 卒業年推移をライン＋エリアチャートで可視化。 |
| Phase8統合ダッシュボード | `showPhase8CompleteDashboard` | 上記指標をまとめたタブ構成のダッシュボード。 |

---

## 5. Phase10 緊急度・転職意欲分析

| 機能カテゴリ | 主な関数 | 内容 |
| --- | --- | --- |
| 緊急度分布 | `showUrgencyDistribution` | A〜D ランク分布、スコア平均、テーブル。 |
| 緊急度 × 年齢／就業状態 | `showUrgencyAgeCross` / `showUrgencyEmploymentCross` | 年齢帯・就業状態と緊急度ランクのクロス分析。 |
| 緊急度ヒートマップ | `showUrgencyAgeMatrix` / `showUrgencyEmploymentMatrixHeatmap` | マトリクスをヒートマップで表示。 |
| 市区町村別緊急度 | `showUrgencyByMunicipality` | 市区町村別のスコアを散布図＆ランキングで表示。 |
| Phase10統合ダッシュボード | `showPhase10CompleteDashboard` | 分布／クロス／マトリクス／地域別をタブ切替で俯瞰。 |

---

## 6. 品質・地域ダッシュボード（横断指標）

| ファイル | 主な機能 |
| --- | --- |
| `QualityAndRegionDashboards.gs` | - `showQualityDashboard`：Phase1〜10 の品質レポートを比較するダッシュボード。<br>- 各 Phase のデータを横断的に取得する `fetchPhaseX` 系関数（Phase1/2/3/7/8/10）で地域別に抽出。<br>- 地図上の品質フラグ表示（`createMarkersWithQualityFlags` 等）。<br>- 交差集計テーブルに品質スコアを埋め込むヘルパ (`renderCrossTabTableWithQualityFlags`)。<br>- 地域コンテキスト解決 (`resolveRegionContext`) とフィルタリング処理。 |

---

## 7. 既知の欠損／未統合項目（MapComplete プロトタイプ視点）

1. **MapComplete Ver2 とのデータ連携**  
   - `MapCompleteDataBridge.gs` は追加済みだが、HTML 側の `loadData()` から `google.script.run.getMapCompleteData` をまだ呼び出していない。プルダウン・マーカー操作と GAS 側 API の往復を実装する。  
2. **メニューと関数名の突き合わせ**  
   - 旧版メニュー（`MenuIntegration.gs.bak2`）で使用していた `showFlowAnalysis` / `showProximityAnalysis` などが、現行ファイルでは `showMunicipalityFlowNetworkVisualization` 等へ置き換わっている。ユーザー報告の「関数が見つからない」エラーが再発しないよう、最新版メニュー項目と実装関数を照合し、不要なメニューを整理する。  
3. **Phase7/8/10 ダッシュボードのデータずれ**  
   - `Phase7UnifiedVisualizations.gs` / `Phase8UnifiedVisualizations.gs` / `Phase10UnifiedVisualizations.gs` 内で Phase 接頭辞付きシートを前提とした箇所の再点検が未完。`urgencyDist.reduce is not a function` 等の実行時エラーが残っている。  
4. **品質フラグ／警告表示**  
   - Quality Dashboard の警告ロジック（`getMarkerColor` など）をサイドバー情報へ組み込み、危険な地域を一目で把握できるようにする。  
5. **文字化け解消**  
   - CSV 読み込み時に日本語が化ける問題が残っている。`Utilities.parseCsv` や `UTF-8 (BOM)` の明示指定を統一し、GAS → HTML のエンコーディングを揃える。 |
