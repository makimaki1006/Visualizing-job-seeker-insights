# ジョブメドレープロジェクト 完全ワークフローガイド

**バージョン**: 2.2 (Phase 6統合版)
**最終更新**: 2025年10月30日
**ステータス**: 本番運用可能 ✅

---

## 📋 目次

1. [システム全体像](#システム全体像)
2. [エンドツーエンドフロー](#エンドツーエンドフロー)
3. [Python処理フロー](#python処理フロー)
4. [GASインポートフロー](#gasインポートフロー)
5. [GAS可視化フロー](#gas可視化フロー)
6. [Phase 6統合後の変更点](#phase-6統合後の変更点)
7. [トラブルシューティング](#トラブルシューティング)

---

## システム全体像

### 🎯 プロジェクトの目的

ジョブメドレーの求職者データを包括的に分析し、Google Apps Script（GAS）と連携して可視化するエンドツーエンドシステム。

### 📊 主要コンポーネント

```
┌─────────────────────────────────────────────────────────────┐
│                     データソース                              │
│  ・生CSV（ジョブメドレー求職者データ）                          │
│  ・results_*.csv（新形式、13カラム簡易形式）                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                  Python処理層                                 │
│  ・run_complete.py（旧形式、Phase 1-7対応）                    │
│  ・run_complete_v2.py（新形式、Phase 1-10対応、品質検証統合）   │
│  ・data_normalizer.py（表記ゆれ正規化）                        │
│  ・data_quality_validator.py（品質検証）                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│               Phase別CSVファイル生成                           │
│  Phase 1: 基礎集計（4ファイル）                                │
│  Phase 2: 統計分析（2ファイル）                                │
│  Phase 3: ペルソナ分析（2ファイル）                             │
│  Phase 6: フロー分析（3ファイル）                              │
│  Phase 7: 高度分析（5ファイル）                                │
│  Phase 8: キャリア・学歴分析（4ファイル）                        │
│  Phase 10: 転職意欲・緊急度分析（5ファイル）                    │
│  品質レポート: QualityReport_*.csv（各Phase）                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                GASインポート層                                 │
│  方法1: HTMLアップロード（最も簡単）✨                          │
│  方法2: クイックインポート（Google Drive）                      │
│  方法3: Python結果CSVを取り込み（Phase 1-6）                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│            Google Spreadsheet（データ保存）                    │
│  シート構成: Phase1-10ごとに独立シート                          │
│  データ検証: 7種類の拡張検証機能                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                 GAS可視化層                                   │
│  ・10個のGSファイル（Phase 6統合後）                            │
│  ・10個のHTMLファイル（UI）                                    │
│  ・Google Charts API（グラフ描画）                             │
│  ・Google Maps API（地図表示）                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                  最終アウトプット                              │
│  ・地図可視化（バブル、ヒートマップ）                            │
│  ・統計分析結果（カイ二乗、ANOVA）                              │
│  ・ペルソナ分析（難易度判定）                                   │
│  ・フロー分析（自治体間移動）                                   │
│  ・高度分析（供給密度、資格分布、年齢×性別、移動許容度）           │
│  ・キャリア・学歴分析                                          │
│  ・転職意欲・緊急度分析                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## エンドツーエンドフロー

### 🚀 標準フロー（推奨）

#### ステップ1: データ準備

```
生CSVファイル（ジョブメドレー）
  │
  └─ 格納場所: C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\
     ├─ results_20251027_180947.csv（最新データ、13カラム）
     ├─ results_20251027_180743.csv（バックアップ）
     └─ その他のバックアップ
```

#### ステップ2: Python処理実行

**v2統合実行（推奨）** 🆕

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete_v2_perfect.py
```

**処理内容**:
1. GUIでCSVファイル選択（新形式 results_*.csv）
2. データ正規化（表記ゆれ自動修正）
3. Phase 1-10のすべてのCSVファイル生成
4. 品質検証レポート自動生成（Descriptive + Inferential）

**出力先**:
```
data/output_v2/
├── phase1/（6ファイル）
│   ├── Applicants.csv
│   ├── DesiredWork.csv
│   ├── AggDesired.csv
│   ├── MapMetrics.csv
│   ├── QualityReport.csv
│   └── QualityReport_Descriptive.csv
├── phase2/（3ファイル）
│   ├── ChiSquareTests.csv
│   ├── ANOVATests.csv
│   └── QualityReport_Inferential.csv
├── phase3/（3ファイル）
│   ├── PersonaSummary.csv
│   ├── PersonaDetails.csv
│   └── QualityReport_Inferential.csv
├── phase6/（4ファイル）
│   ├── MunicipalityFlowEdges.csv
│   ├── MunicipalityFlowNodes.csv
│   ├── ProximityAnalysis.csv
│   └── QualityReport_Inferential.csv
├── phase7/（6ファイル）
│   ├── SupplyDensityMap.csv
│   ├── QualificationDistribution.csv
│   ├── AgeGenderCrossAnalysis.csv
│   ├── MobilityScore.csv
│   ├── DetailedPersonaProfile.csv
│   └── QualityReport_Inferential.csv
├── phase8/（6ファイル）
│   ├── EducationDistribution.csv
│   ├── EducationAgeCross.csv
│   ├── EducationAgeCross_Matrix.csv
│   ├── GraduationYearDistribution.csv
│   ├── QualityReport.csv
│   └── QualityReport_Inferential.csv
├── phase10/（7ファイル）
│   ├── UrgencyDistribution.csv
│   ├── UrgencyAgeCross.csv
│   ├── UrgencyAgeCross_Matrix.csv
│   ├── UrgencyEmploymentCross.csv
│   ├── UrgencyEmploymentCross_Matrix.csv
│   ├── QualityReport.csv
│   └── QualityReport_Inferential.csv
├── OverallQualityReport_Inferential.csv
├── OverallQualityReport.csv
└── geocache.json
```

**合計**: 37ファイル | **品質スコア**: 82.86/100 (EXCELLENT) ✅

#### ステップ3: GASインポート

**Phase 1-6のインポート** (Python結果CSVを取り込み)

```
Google Spreadsheet
  │
  └─ メニュー: 📊 データ処理 → 🐍 Python連携 → 📥 Python結果CSVを取り込み
     │
     └─ 自動処理:
        ├─ data/output_v2/phase1/*.csv → Phase1シート
        ├─ data/output_v2/phase2/*.csv → Phase2シート
        ├─ data/output_v2/phase3/*.csv → Phase3シート
        └─ data/output_v2/phase6/*.csv → Phase6シート
```

**Phase 7-10のインポート** (HTMLアップロード、推奨) ✨

```
Google Spreadsheet
  │
  └─ メニュー: 📊 データ処理 → 📈 Phase 7高度分析 → 📥 データインポート → 📤 HTMLアップロード（最も簡単）
     │
     └─ 手動操作:
        1. 5つのCSVファイルをドラッグ&ドロップ
           ├─ SupplyDensityMap.csv
           ├─ QualificationDistribution.csv
           ├─ AgeGenderCrossAnalysis.csv
           ├─ MobilityScore.csv
           └─ DetailedPersonaProfile.csv
        2. 「アップロード開始」をクリック
        3. 自動でPhase 7シートが作成される
```

**Phase 8のインポート**

```
同様にHTMLアップロードまたはクイックインポート
  ├─ EducationDistribution.csv
  ├─ EducationAgeCross.csv
  └─ GraduationYearDistribution.csv
```

**Phase 10のインポート**

```
同様にHTMLアップロードまたはクイックインポート
  ├─ UrgencyDistribution.csv
  ├─ UrgencyAgeCross.csv
  └─ UrgencyEmploymentCross.csv
```

#### ステップ4: GAS可視化

**Phase 1-6可視化**

```
Google Spreadsheet
  │
  ├─ 地図表示（バブル）
  │  └─ メニュー: 📊 データ処理 → 🗺️ 地図表示（バブル）
  │
  ├─ 地図表示（ヒートマップ）
  │  └─ メニュー: 📊 データ処理 → 📍 地図表示（ヒートマップ）
  │
  ├─ カイ二乗検定結果
  │  └─ メニュー: 📊 データ処理 → 📈 統計分析・ペルソナ → 🔬 カイ二乗検定結果
  │
  ├─ ペルソナ難易度確認
  │  └─ メニュー: 📊 データ処理 → 📈 統計分析・ペルソナ → 🎯 ペルソナ難易度確認
  │
  └─ フロー・移動統合ビュー
     └─ メニュー: 📊 データ処理 → 🌊 フロー・移動パターン分析 → 🎯 フロー・移動統合ビュー
```

**Phase 7可視化（推奨: 統合ダッシュボード）** ✨

```
Google Spreadsheet
  │
  └─ メニュー: 📊 データ処理 → 📈 Phase 7高度分析 → 🎯 完全統合ダッシュボード
     │
     └─ 表示内容:
        ├─ タブ1: 人材供給密度マップ
        ├─ タブ2: 資格別人材分布
        ├─ タブ3: 年齢層×性別クロス分析
        ├─ タブ4: 移動許容度スコアリング
        ├─ タブ5: ペルソナ詳細プロファイル
        └─ タブ6: データ検証結果
```

**Phase 8可視化**

```
Google Spreadsheet
  │
  └─ メニュー: 📊 データ処理 → 📊 Phase 8学歴・キャリア → 各種分析
```

**Phase 10可視化**

```
Google Spreadsheet
  │
  └─ メニュー: 📊 データ処理 → 💼 Phase 10転職意欲 → 各種分析
```

---

## Python処理フロー

### 📊 run_complete_v2_perfect.py（新形式、完全版、推奨）

```python
# 1. ファイル選択（GUI）
┌──────────────────────────┐
│ tkinter GUIダイアログ      │
│ ファイル選択:             │
│ results_*.csv            │
└────────┬─────────────────┘
         │
         ↓
# 2. データ読み込み
┌──────────────────────────┐
│ CSVファイル読み込み        │
│ ・UTF-8エンコーディング    │
│ ・13カラム簡易形式        │
└────────┬─────────────────┘
         │
         ↓
# 3. データ正規化（表記ゆれ対応）
┌──────────────────────────┐
│ data_normalizer.py       │
│ ・キャリア正規化          │
│ ・学歴正規化             │
│ ・希望職種正規化          │
│ ・雇用形態正規化          │
│ ・緊急度正規化           │
└────────┬─────────────────┘
         │
         ↓
# 4. ジオコーディング
┌──────────────────────────┐
│ Google Maps API         │
│ ・市区町村 → 緯度経度    │
│ ・キャッシュ利用         │
│   (geocache.json)       │
└────────┬─────────────────┘
         │
         ↓
# 5. Phase 1-10処理
┌──────────────────────────┐
│ Phase 1: 基礎集計        │
│ ・申請者基本情報         │
│ ・希望勤務地詳細         │
│ ・集計データ             │
│ ・MapMetrics（座標付き） │
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│ Phase 2: 統計分析        │
│ ・カイ二乗検定           │
│ ・ANOVA検定             │
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│ Phase 3: ペルソナ分析    │
│ ・K-Meansクラスタリング  │
│ ・難易度スコア算出       │
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│ Phase 6: フロー分析      │
│ ・自治体間移動パターン    │
│ ・近接性分析             │
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│ Phase 7: 高度分析        │
│ ・人材供給密度マップ      │
│ ・資格別人材分布         │
│ ・年齢×性別クロス分析    │
│ ・移動許容度スコアリング  │
│ ・ペルソナ詳細プロファイル│
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│ Phase 8: キャリア・学歴  │
│ ・学歴分布               │
│ ・学歴×年齢クロス分析    │
│ ・卒業年分布             │
└────────┬─────────────────┘
         │
         ↓
┌──────────────────────────┐
│ Phase 10: 転職意欲      │
│ ・緊急度分布             │
│ ・緊急度×年齢クロス分析  │
│ ・緊急度×雇用形態クロス  │
└────────┬─────────────────┘
         │
         ↓
# 6. 品質検証
┌──────────────────────────┐
│ data_quality_validator.py│
│ ・観察的記述モード       │
│   (Descriptive)         │
│ ・推論的考察モード       │
│   (Inferential)         │
│ ・品質スコア算出         │
│   (0-100点)             │
└────────┬─────────────────┘
         │
         ↓
# 7. CSVファイル出力
┌──────────────────────────┐
│ data/output_v2/          │
│ ・各PhaseのCSVファイル    │
│ ・品質レポート           │
│ ・統合品質レポート       │
└──────────────────────────┘
```

### 品質検証システム（v2.1新機能）

```
┌─────────────────────────────────────────────────┐
│          データ品質検証システム                    │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│     観察的記述モード（Descriptive）                │
│  ・用途: 事実の記述（集計値・件数・割合の提示）      │
│  ・最小サンプル: 1件でもOK                        │
│  ・制約: 「傾向」「差異」の言葉は使用不可           │
│  ・適用Phase: Phase 1（基礎集計）                 │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│     推論的考察モード（Inferential）               │
│  ・用途: 傾向分析（クロス集計・関係性の推論）       │
│  ・最小サンプル: グループ30件以上、全体100件以上   │
│  ・制約: サンプル数不足は警告表示                  │
│  ・適用Phase: Phase 2, 3, 6, 7, 8, 10           │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│           品質スコア（0-100点）                   │
│  ・80-100: EXCELLENT（そのまま使用可能）          │
│  ・60-79: GOOD（一部注意が必要）                  │
│  ・40-59: ACCEPTABLE（警告付きで提示推奨）        │
│  ・0-39: POOR（追加データ収集推奨）               │
└─────────────────────────────────────────────────┘
```

---

## GASインポートフロー

### 方法1: HTMLアップロード（最も簡単）✨

```
┌──────────────────────────────────────────────┐
│  Google Spreadsheet                          │
│  メニュー: Phase 7高度分析 → HTMLアップロード  │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  PhaseUpload.html                            │
│  ・ドラッグ&ドロップ対応                       │
│  ・複数ファイル一括アップロード                 │
│  ・プログレスバー表示                          │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  JavaScript処理                              │
│  1. ファイル読み込み（FileReader API）         │
│  2. CSVパース（BOM除去、行分割）               │
│  3. GASサーバーに送信（google.script.run）     │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  DataImportAndValidation.gs                  │
│  importCSVToSheet(sheetName, csvData)        │
│  1. シート作成または既存シートクリア            │
│  2. CSVデータをシートに書き込み                │
│  3. ヘッダー行のフォーマット適用                │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  Google Spreadsheet                          │
│  Phase 7シート作成完了                        │
└──────────────────────────────────────────────┘
```

### 方法2: クイックインポート（Google Drive）

```
┌──────────────────────────────────────────────┐
│  Google Drive                                │
│  gas_output_phase7フォルダにCSVアップロード    │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  Google Spreadsheet                          │
│  メニュー: Phase 7高度分析 → クイックインポート │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  Phase7AutoImporter.gs                       │
│  quickImport()                               │
│  1. Google Driveフォルダ検索                  │
│  2. CSVファイル取得                           │
│  3. 各ファイルを対応シートにインポート          │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  Google Spreadsheet                          │
│  Phase 7シート作成完了                        │
└──────────────────────────────────────────────┘
```

### 方法3: Python結果CSVを取り込み（Phase 1-6）

```
┌──────────────────────────────────────────────┐
│  Google Spreadsheet                          │
│  メニュー: Python連携 → Python結果CSVを取り込み│
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  PythonCSVImporter.gs                        │
│  importAllPythonResults()                    │
│  1. data/output_v2/phase[1-6]/*.csvを検索    │
│  2. 各ファイルを対応シートにインポート          │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  Google Spreadsheet                          │
│  Phase 1-6シート作成完了                      │
└──────────────────────────────────────────────┘
```

---

## GAS可視化フロー

### Phase 6統合後のファイル構成（10ファイル）

```
gas_files/scripts/
├── Phase1-6UnifiedVisualizations.gs   (109 KB, 3,550行)
│   ├─ 地図表示（バブル、ヒートマップ）
│   ├─ 統計分析（カイ二乗、ANOVA）
│   ├─ ペルソナ分析（サマリー、詳細）
│   ├─ フロー分析（自治体間移動）
│   ├─ ペルソナマップデータ
│   ├─ マトリックスヒートマップ
│   └─ 統合ダッシュボード（Phase 1-6）
│
├── Phase7UnifiedVisualizations.gs     (101 KB, 3,514行)
│   ├─ 人材供給密度マップ
│   ├─ 資格別人材分布
│   ├─ 年齢層×性別クロス分析
│   ├─ 移動許容度スコアリング
│   ├─ ペルソナ詳細プロファイル
│   └─ 完全統合ダッシュボード（6タブ）
│
├── Phase8UnifiedVisualizations.gs     (65 KB, 2,224行)
│   ├─ 学歴分布
│   ├─ 学歴×年齢クロス分析
│   └─ 卒業年分布
│
├── Phase10UnifiedVisualizations.gs    (92 KB, 2,940行)
│   ├─ 緊急度分布
│   ├─ 緊急度×年齢クロス分析
│   └─ 緊急度×雇用形態クロス分析
│
├── DataServiceProvider.gs              (17 KB, 573行)
│   ├─ 地域選択肢取得（getRegionOptions）
│   ├─ 都道府県別市区町村取得（getMunicipalitiesForPrefecture）
│   └─ 選択地域保存（saveSelectedRegion）
│
├── QualityAndRegionDashboards.gs      (56 KB, 1,658行)
│   ├─ Phase 1基礎集計データ取得（fetchPhase1Metrics）
│   ├─ Phase 2統計解析データ取得（fetchPhase2Stats）
│   ├─ Phase 3ペルソナ分析データ取得（fetchPhase3Persona）
│   ├─ Phase 7高度分析データ取得（fetchPhase7Supply）
│   ├─ Phase 8学歴・キャリア分析データ取得（fetchPhase8Education）
│   └─ Phase 10転職意欲分析データ取得（fetchPhase10Urgency）
│
├── DataImportAndValidation.gs         (48 KB, 1,437行)
│   ├─ Python結果CSVインポート
│   ├─ 汎用Phaseアップローダー
│   └─ データ検証機能（7種類）
│
├── UnifiedDataImporter.gs              (52 KB)
│   └─ Phase 7-10データインポート
│
├── PersonaDifficultyChecker.gs
│   └─ ペルソナ難易度分析（6軸フィルター）
│
└── MenuIntegration.gs
    └─ メニュー統合（全Phase統合メニュー）
```

### HTMLファイル構成（10ファイル）

```
gas_files/html/
├── BubbleMap.html                    # 地図バブル表示
│   └─ 呼び出し関数: Phase1-6UnifiedVisualizations.gs
│      ├─ getMapMetricsData()
│      ├─ getApplicantsStats()
│      └─ getDesiredWorkTop10()
│
├── HeatMap.html                      # ヒートマップ表示
│   └─ 呼び出し関数: Phase1-6UnifiedVisualizations.gs
│
├── MapComplete.html                  # 統合地図表示
│   └─ 呼び出し関数: Phase1-6UnifiedVisualizations.gs
│
├── RegionalDashboard.html            # 地域別ダッシュボード
│   ├─ 呼び出し関数（データサービス）: DataServiceProvider.gs
│   │  ├─ getRegionOptions()
│   │  ├─ getMunicipalitiesForPrefecture()
│   │  └─ saveSelectedRegion()
│   └─ 呼び出し関数（ダッシュボード）: QualityAndRegionDashboards.gs
│      ├─ fetchPhase1Metrics()
│      ├─ fetchPhase2Stats()
│      ├─ fetchPhase3Persona()
│      ├─ fetchPhase7Supply()
│      ├─ fetchPhase8Education()
│      └─ fetchPhase10Urgency()
│
├── PhaseUpload.html                  # 汎用CSVアップローダー
│   └─ 呼び出し関数: DataImportAndValidation.gs
│      └─ importCSVToSheet()
│
├── QualityFlagDemoUI.html            # 品質フラグ可視化デモ
│   └─ 静的HTMLページ（GAS呼び出しなし）
│
├── Phase7Upload.html                 # Phase 7 HTMLアップロード
│   └─ 呼び出し関数: Phase7UnifiedVisualizations.gs
│
├── Phase7BatchUpload.html            # Phase 7バッチアップロード
│   └─ 呼び出し関数: Phase7UnifiedVisualizations.gs
│
├── PersonaDifficultyCheckerUI.html   # ペルソナ難易度分析UI
│   └─ 呼び出し関数: PersonaDifficultyChecker.gs
│
└── Upload_Enhanced.html              # 高速CSVアップローダー
    └─ 呼び出し関数: DataImportAndValidation.gs
```

### 可視化実行フロー

#### Phase 1-6可視化

```
ユーザー操作
  │
  └─ メニュー選択: 📊 データ処理 → 🗺️ 地図表示（バブル）
     │
     ↓
MenuIntegration.gs
  │
  └─ showBubbleMap()
     │
     ↓
Phase1-6UnifiedVisualizations.gs
  │
  ├─ loadSheetData_("MapMetrics", 5)
  │  └─ SpreadsheetApp.getActiveSpreadsheet().getSheetByName("MapMetrics")
  │
  ├─ getMapMetricsData()
  │  └─ MapMetricsシートからデータ取得 → JSON形式
  │
  └─ showHtmlDialog_(html, "地図表示（バブル）", 1400, 900)
     │
     ↓
BubbleMap.html
  │
  ├─ Google Maps API初期化
  │  └─ new google.maps.Map()
  │
  ├─ google.script.run.getMapMetricsData()
  │  └─ GAS関数呼び出し
  │
  ├─ google.script.run.getApplicantsStats()
  │  └─ 統計情報取得
  │
  ├─ google.script.run.getDesiredWorkTop10()
  │  └─ TOP10データ取得
  │
  └─ 地図にバブルマーカー表示
     ├─ google.maps.Circle（バブル）
     ├─ サイドバーに統計情報表示
     └─ TOP10リスト表示
```

#### Phase 7可視化（統合ダッシュボード）

```
ユーザー操作
  │
  └─ メニュー選択: 📊 データ処理 → 📈 Phase 7高度分析 → 🎯 完全統合ダッシュボード
     │
     ↓
MenuIntegration.gs
  │
  └─ showPhase7CompleteDashboard()
     │
     ↓
Phase7UnifiedVisualizations.gs
  │
  ├─ loadAllPhase7Data()
  │  ├─ loadSheetData_("SupplyDensityMap", 7)
  │  ├─ loadSheetData_("QualificationDistribution", 5)
  │  ├─ loadSheetData_("AgeGenderCrossAnalysis", 6)
  │  ├─ loadSheetData_("MobilityScore", 8)
  │  └─ loadSheetData_("DetailedPersonaProfile", 12)
  │
  ├─ createCompleteDashboard(data)
  │  └─ HTML生成（6タブ構成）
  │     ├─ タブ1: 人材供給密度マップ
  │     ├─ タブ2: 資格別人材分布
  │     ├─ タブ3: 年齢層×性別クロス分析
  │     ├─ タブ4: 移動許容度スコアリング
  │     ├─ タブ5: ペルソナ詳細プロファイル
  │     └─ タブ6: データ検証結果
  │
  └─ showHtmlDialog_(html, "Phase 7完全統合ダッシュボード", 1400, 900)
     │
     ↓
統合ダッシュボードHTML（動的生成）
  │
  ├─ Google Charts API読み込み
  │  └─ google.charts.load('current', {'packages':['corechart', 'table', 'geochart']})
  │
  ├─ タブ切り替え機能
  │  └─ JavaScript（タブクリックイベント）
  │
  └─ 各タブでグラフ描画
     ├─ タブ1: GeoChart（地図）
     ├─ タブ2: BarChart（棒グラフ）
     ├─ タブ3: ColumnChart（縦棒グラフ）
     ├─ タブ4: ScatterChart（散布図）
     ├─ タブ5: Table（テーブル）
     └─ タブ6: Table（検証結果）
```

---

## Phase 6統合後の変更点

### 🔄 ファイル数の変化

| 段階 | ファイル数 | 削減数 | 累計削減率 |
|------|-----------|--------|-----------|
| **統合前** | 53ファイル | - | - |
| Phase 1-2完了 | 32ファイル | -21 | 40% |
| Phase 3-4完了 | 32ファイル | 0 | 40%（品質向上） |
| Phase 5完了 | 21ファイル | -11 | 60% |
| **Phase 6完了（最終）** | **10ファイル** | **-11** | **81%** 🎉 |

### 📦 Phase 6で統合されたファイル（15個 → 4個）

#### グループ1: Phase 1-6可視化（6個 → 1個）

**統合前**:
- MapVisualization.gs
- Phase2Phase3Visualizations.gs
- MunicipalityFlowNetworkViz.gs
- PersonaMapDataVisualization.gs
- MatrixHeatmapViewer.gs
- CompleteIntegratedDashboard.gs

**統合後**:
- **Phase1-6UnifiedVisualizations.gs** (109 KB, 3,550行)

#### グループ2: データサービス（3個 → 1個）

**統合前**:
- MapDataProvider.gs
- GoogleMapsAPIConfig.gs
- RegionStateService.gs

**統合後**:
- **DataServiceProvider.gs** (17 KB, 573行)

#### グループ3: 品質・ダッシュボード（3個 → 1個）

**統合前**:
- QualityDashboard.gs
- QualityFlagVisualization.gs
- RegionDashboard.gs

**統合後**:
- **QualityAndRegionDashboards.gs** (56 KB, 1,658行)

#### グループ4: データインポート・検証（3個 → 1個）

**統合前**:
- PythonCSVImporter.gs
- UniversalPhaseUploader.gs
- DataValidationEnhanced.gs

**統合後**:
- **DataImportAndValidation.gs** (48 KB, 1,437行)

### ✅ HTML-GS互換性

**Phase 6統合後も、すべてのHTMLファイルは変更不要**

理由:
1. ✅ すべての関数が適切に統合ファイルに移動されている
2. ✅ 関数シグネチャ（引数・戻り値）が変更されていない
3. ✅ 関数名が変更されていない
4. ✅ HTMLから見たAPI仕様が完全に保たれている

詳細は [HTML_GAS_INTEGRATION_VERIFICATION.md](./HTML_GAS_INTEGRATION_VERIFICATION.md) を参照。

### 🎯 品質スコアの向上

| ファイル | リファクタリング前 | リファクタリング後 | 向上幅 |
|---------|------------------|------------------|--------|
| Phase1-6UnifiedVisualizations.gs | 70 | 95 | +25 |
| DataServiceProvider.gs | 75 | 96 | +21 |
| QualityAndRegionDashboards.gs | 75 | 96 | +21 |
| DataImportAndValidation.gs | 80 | 96 | +16 |
| **平均** | **75** | **95.75** | **+20.75** |

---

## トラブルシューティング

### ❌ 問題: Python実行時に「モジュールが見つかりません」エラー

**原因**: 必要なライブラリがインストールされていない

**解決方法**:
```bash
pip install pandas numpy scikit-learn matplotlib seaborn
```

### ❌ 問題: GASインポート時に「シートが見つかりません」エラー

**原因**: Python処理が完了していない、またはファイルパスが間違っている

**解決方法**:
1. `python run_complete_v2.py` を実行
2. `data/output_v2/phase1/` フォルダが生成されたことを確認
3. 必須ファイルが存在することを確認

### ❌ 問題: HTMLアップロード時に「CSVファイルを選択してください」エラー

**原因**: CSV以外のファイルを選択した

**解決方法**:
1. 拡張子が `.csv` のファイルのみを選択
2. ファイル名が正しいことを確認（例: SupplyDensityMap.csv）

### ❌ 問題: GAS可視化で「データがありません」エラー

**原因**: データインポートが完了していない

**解決方法**:
1. メニュー: `📊 データ処理` → `データ管理` → `🔍 データ確認`
2. 該当Phaseのシートにデータが存在するか確認
3. データがない場合は、再度インポート処理を実行

### ❌ 問題: 品質スコアが低い（40点未満）

**原因**: サンプルサイズが不足している

**解決方法**:
1. 品質レポート（QualityReport_*.csv）を確認
2. 警告メッセージを確認
3. 必要に応じて追加データを収集
4. 観察的記述として扱う（傾向分析には使用しない）

---

## 📚 関連ドキュメント

### Python関連
- [run_complete_v2.py](../python_scripts/run_complete_v2.py) - v2統合実行スクリプト
- [data_normalizer.py](../python_scripts/data_normalizer.py) - データ正規化モジュール
- [data_quality_validator.py](../python_scripts/data_quality_validator.py) - 品質検証モジュール
- [DATA_USAGE_GUIDELINES.md](./DATA_USAGE_GUIDELINES.md) - データ利用ガイドライン

### GAS関連
- [GAS_FILE_FINAL_REPORT.md](./GAS_FILE_FINAL_REPORT.md) - Phase 1-6統合レポート
- [PHASE6_REFACTORING_REPORT.md](./PHASE6_REFACTORING_REPORT.md) - Phase 6リファクタリング詳細
- [HTML_GAS_INTEGRATION_VERIFICATION.md](./HTML_GAS_INTEGRATION_VERIFICATION.md) - HTML-GS統合検証
- [GAS_COMPLETE_FEATURE_LIST.md](./GAS_COMPLETE_FEATURE_LIST.md) - GAS完全機能一覧（50ページ）

### テスト関連
- [TEST_RESULTS_COMPREHENSIVE.json](./TEST_RESULTS_COMPREHENSIVE.json) - Phase 1-6テスト結果
- [TEST_RESULTS_2025-10-26_FINAL.md](./TEST_RESULTS_2025-10-26_FINAL.md) - Phase 7テスト結果
- [GAS_E2E_TEST_REPORT.md](./GAS_E2E_TEST_REPORT.md) - GAS E2Eテスト結果

---

**最終更新**: 2025年10月30日
**作成者**: Claude Code (Sonnet 4.5)
