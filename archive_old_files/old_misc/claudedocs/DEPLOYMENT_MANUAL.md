# デプロイ手順書

**作成日**: 2025-10-27
**対象**: ジョブメドレー求職者データ分析プロジェクト（全Phase実装版）
**前提**: Python 3.8+、Google Apps Script環境

---

## 目次

1. [環境準備](#1-環境準備)
2. [Pythonセットアップ](#2-pythonセットアップ)
3. [Google Apps Scriptセットアップ](#3-google-apps-scriptセットアップ)
4. [Google Maps API設定](#4-google-maps-api設定)
5. [初回データ処理実行](#5-初回データ処理実行)
6. [GASへのCSVインポート](#6-gasへのcsvインポート)
7. [動作確認](#7-動作確認)
8. [トラブルシューティング](#8-トラブルシューティング)
9. [ロールバック手順](#9-ロールバック手順)

---

## 1. 環境準備

### 1.1. 必要なツール

- **Python**: 3.8以上（推奨: 3.10+）
- **pip**: 最新版
- **Googleアカウント**: Google Apps Script利用可能
- **Google Maps API**: APIキー取得済み

### 1.2. プロジェクトディレクトリ構成確認

```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\
├── python_scripts/
│   ├── run_complete.py
│   ├── phase7_advanced_analysis.py
│   ├── network_analyzer.py                 # Phase 2実装時
│   ├── cross_analysis_engine.py            # Phase 1実装時
│   └── auto_report_generator.py            # Phase 3実装時
├── gas_files/
│   ├── scripts/
│   │   ├── GoogleMapsAPIConfig.gs
│   │   ├── DataValidationEnhanced.gs
│   │   ├── PersonaDifficultyChecker.gs
│   │   ├── MenuIntegration.gs
│   │   ├── PythonCSVImporter.gs
│   │   ├── PersonaMapDataVisualization.gs    # Phase 1実装時
│   │   ├── Phase7PersonaMobilityCrossViz.gs  # Phase 1実装時
│   │   ├── MunicipalityFlowNetworkViz.gs     # Phase 2実装時
│   │   ├── CompleteIntegratedDashboard.gs    # Phase 2実装時
│   │   ├── MapMetricsHeatmap.gs              # Phase 3実装時
│   │   └── DesiredWorkSearchUI.gs            # Phase 3実装時
│   └── html/
│       ├── PersonaDifficultyCheckerUI.html
│       └── Upload_Enhanced.html
├── requirements.txt
├── geocache.json
└── claudedocs/
    ├── DEPLOYMENT_MANUAL.md                   # このファイル
    ├── COMPLETE_IMPLEMENTATION_PLAN.md
    ├── PHASE2_3_DETAILED_DESIGN.md
    └── IMPLEMENTATION_ULTRATHINK_REVIEW.md
```

---

## 2. Pythonセットアップ

### 2.1. requirements.txt インストール

```bash
# プロジェクトディレクトリに移動
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project"

# 依存ライブラリインストール
pip install -r requirements.txt
```

**インストール内容**:
- pandas (>=1.5.0)
- numpy (>=1.23.0)
- scikit-learn (>=1.1.0)
- networkx (>=2.8.0)
- matplotlib (>=3.5.0)
- seaborn (>=0.12.0)
- scipy (>=1.9.0)
- pytest (>=7.1.0)
- pytest-cov (>=3.0.0)
- pylint (>=2.14.0)
- black (>=22.6.0)
- jsonschema (>=4.0.0)

### 2.2. インストール確認

```bash
# Pythonバージョン確認
python --version
# 出力例: Python 3.10.11

# パッケージ確認
pip list | grep pandas
pip list | grep networkx
```

**期待される出力**:
```
pandas         1.5.3
networkx       2.8.8
```

---

## 3. Google Apps Scriptセットアップ

### 3.1. Googleスプレッドシート作成

1. Google Driveにアクセス
2. 「新規」→「Googleスプレッドシート」→「空白のスプレッドシート」
3. ファイル名を「ジョブメドレー求職者データ分析」に変更

### 3.2. GASエディタを開く

1. スプレッドシートメニュー: 「拡張機能」→「Apps Script」
2. 新規プロジェクトが開く

### 3.3. GASファイルアップロード

#### **必須ファイル（Phase 0: 基盤）**

以下のファイルを順番にGASプロジェクトに追加:

**スクリプトファイル（.gs）**:
1. `GoogleMapsAPIConfig.gs` - APIキー管理（最優先）
2. `DataValidationEnhanced.gs` - データ検証機能
3. `PersonaDifficultyChecker.gs` - ペルソナ難易度分析
4. `MenuIntegration.gs` - メニュー統合
5. `PythonCSVImporter.gs` - CSVインポート機能

**HTMLファイル（.html）**:
1. `PersonaDifficultyCheckerUI.html` - ペルソナ難易度UI
2. `Upload_Enhanced.html` - 高速CSVアップロードUI

#### **Phase 1実装後に追加**:
- `PersonaMapDataVisualization.gs` - 地図可視化
- `Phase7PersonaMobilityCrossViz.gs` - ペルソナ×移動性クロス可視化

#### **Phase 2実装後に追加**:
- `MunicipalityFlowNetworkViz.gs` - フローネットワーク図
- `CompleteIntegratedDashboard.gs` - 統合ダッシュボード

#### **Phase 3実装後に追加**:
- `MapMetricsHeatmap.gs` - ヒートマップ
- `DesiredWorkSearchUI.gs` - DesiredWork検索UI

### 3.4. GASファイル追加方法

1. GASエディタ左側の「ファイル」アイコン（+）をクリック
2. **スクリプトファイル追加**: 「スクリプト」を選択 → ファイル名入力（拡張子なし）
3. **HTMLファイル追加**: 「HTML」を選択 → ファイル名入力（拡張子なし）
4. ローカルファイルの内容をコピー&ペースト
5. 「保存」（Ctrl+S）

### 3.5. プロジェクト名設定

1. GASエディタ左上「無題のプロジェクト」をクリック
2. 「ジョブメドレーデータ分析GAS」に変更

---

## 4. Google Maps API設定

### 4.1. Google Cloud Console でAPIキー取得

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクト作成: 「プロジェクトを選択」→「新しいプロジェクト」
3. プロジェクト名: 「job-medley-analysis」
4. 「APIとサービス」→「ライブラリ」→「Maps JavaScript API」を検索
5. 「有効にする」をクリック
6. 「認証情報」→「認証情報を作成」→「APIキー」
7. APIキーをコピー（例: `AIzaSyAbc123...`）

### 4.2. GAS Script PropertiesにAPIキー設定

#### **方法1: GAS UIから設定（推奨）**

1. GASエディタ左側の「⚙️ プロジェクトの設定」をクリック
2. 「スクリプト プロパティ」セクションまでスクロール
3. 「スクリプト プロパティを追加」をクリック
4. **プロパティ名**: `GOOGLE_MAPS_API_KEY`
5. **値**: 取得したAPIキー（例: `AIzaSyAbc123...`）
6. 「スクリプト プロパティを保存」をクリック

#### **方法2: GAS関数から設定（初回のみ）**

1. GASエディタで `GoogleMapsAPIConfig.gs` を開く
2. `setGoogleMapsAPIKey()` 関数を以下のように編集:

```javascript
function setGoogleMapsAPIKey(apiKey) {
  const properties = PropertiesService.getScriptProperties();
  properties.setProperty('GOOGLE_MAPS_API_KEY', 'YOUR_ACTUAL_API_KEY_HERE');
  Logger.log('Google Maps APIキーを設定しました');
}
```

3. 実際のAPIキーを貼り付け
4. GASエディタ上部の「実行」ボタンをクリック → `setGoogleMapsAPIKey` を選択
5. 初回実行時、権限の承認を求められるので「承認」
6. **セキュリティのため、実行後はコード内のAPIキーを削除**

### 4.3. APIキー設定確認

1. GASエディタで `GoogleMapsAPIConfig.gs` を開く
2. `checkAPIKeyStatus()` 関数を実行
3. アラートダイアログに「✅ Google Maps APIキーが設定されています」と表示されればOK

**期待される表示**:
```
✅ Google Maps APIキーが設定されています

マスク済みキー: AIzaSyAbc1...3xyz
キー長: 39文字

セキュリティのため、完全なキーは表示されません。
```

---

## 5. 初回データ処理実行

### 5.1. 生CSVファイル準備

ジョブメドレーから提供された生CSVファイルを以下のディレクトリに配置:

```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\
```

**必要なファイル**:
- `applicants.csv` - 申請者基本情報
- `desired_work_locations.csv` - 希望勤務地情報
- その他関連CSVファイル

### 5.2. run_complete.py 実行

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管"
python run_complete.py
```

**実行内容**:
1. GUIでCSVファイル選択ダイアログ表示
2. Phase 1-7のCSVファイル生成
3. geocache.jsonの更新（ジオコーディング結果キャッシュ）

**処理時間**: 約3-5分（初回実行時、ジオコーディングキャッシュがない場合）

### 5.3. 出力確認

以下のディレクトリが生成されていることを確認:

```
gas_output_phase1/
├── MapMetrics.csv          # 座標付き基礎集計（4列）
├── Applicants.csv          # 申請者情報
├── DesiredWork.csv         # 希望勤務地詳細（1.3MB）
└── AggDesired.csv          # 集計データ

gas_output_phase2/
├── ChiSquareTests.csv      # カイ二乗検定結果
└── ANOVATests.csv          # ANOVA検定結果

gas_output_phase3/
├── PersonaSummary.csv      # ペルソナサマリー
└── PersonaDetails.csv      # ペルソナ詳細

gas_output_phase6/
├── MunicipalityFlowEdges.csv  # 自治体間フローエッジ（321KB）
├── MunicipalityFlowNodes.csv  # 自治体間フローノード
└── ProximityAnalysis.csv      # 移動パターン分析

gas_output_phase7/
├── PersonaMapData.csv              # ペルソナ地図データ（座標付き、792行）
├── PersonaMobilityCross.csv        # ペルソナ×移動性クロス
├── PersonaQualificationCross.csv   # ペルソナ×資格クロス
├── TopDestinations.csv             # TOP希望勤務地
├── SegmentComparison.csv           # セグメント比較
├── MobilityRankDistribution.csv    # 移動性ランク分布
└── QualificationRateSegments.csv   # 資格保有率セグメント

geocache.json  # ジオコーディングキャッシュ（1,901件）
```

**重要な検証ポイント**:
- `PersonaMapData.csv` の行数が **792行** であること（0行の場合はgeocache問題）
- `PersonaMobilityCross.csv` の分布が現実的であること（全Dランクの場合はデータ統合問題）

---

## 6. GASへのCSVインポート

### 6.1. Googleスプレッドシートを開く

前述の手順で作成した「ジョブメドレー求職者データ分析」スプレッドシートを開く。

### 6.2. GASメニューから「Python結果CSVを取り込み」実行

1. スプレッドシートメニュー: 「📊 データ処理」→「🐍 Python連携」→「📥 Python結果CSVを取り込み」
2. ファイル選択ダイアログが表示される
3. 以下のディレクトリを順番に指定:

#### **Phase 1データ取り込み**:
- `gas_output_phase1` フォルダを指定
- 4ファイルがインポートされる:
  - Phase1_MapMetrics
  - Phase1_Applicants
  - Phase1_DesiredWork
  - Phase1_AggDesired

#### **Phase 2データ取り込み**:
- `gas_output_phase2` フォルダを指定
- 2ファイルがインポートされる:
  - Phase2_ChiSquareTests
  - Phase2_ANOVATests

#### **Phase 3データ取り込み**:
- `gas_output_phase3` フォルダを指定
- 2ファイルがインポートされる:
  - Phase3_PersonaSummary
  - Phase3_PersonaDetails

#### **Phase 6データ取り込み**:
- `gas_output_phase6` フォルダを指定
- 3ファイルがインポートされる:
  - Phase6_MunicipalityFlowEdges
  - Phase6_MunicipalityFlowNodes
  - Phase6_ProximityAnalysis

#### **Phase 7データ取り込み**:
- `gas_output_phase7` フォルダを指定
- 7ファイルがインポートされる:
  - Phase7_PersonaMapData
  - Phase7_PersonaMobilityCross
  - Phase7_PersonaQualificationCross
  - Phase7_TopDestinations
  - Phase7_SegmentComparison
  - Phase7_MobilityRankDistribution
  - Phase7_QualificationRateSegments

### 6.3. インポート完了確認

スプレッドシート下部のシートタブを確認し、以下の18シートが存在することを確認:

**Phase 1（4シート）**:
- Phase1_MapMetrics
- Phase1_Applicants
- Phase1_DesiredWork
- Phase1_AggDesired

**Phase 2（2シート）**:
- Phase2_ChiSquareTests
- Phase2_ANOVATests

**Phase 3（2シート）**:
- Phase3_PersonaSummary
- Phase3_PersonaDetails

**Phase 6（3シート）**:
- Phase6_MunicipalityFlowEdges
- Phase6_MunicipalityFlowNodes
- Phase6_ProximityAnalysis

**Phase 7（7シート）**:
- Phase7_PersonaMapData
- Phase7_PersonaMobilityCross
- Phase7_PersonaQualificationCross
- Phase7_TopDestinations
- Phase7_SegmentComparison
- Phase7_MobilityRankDistribution
- Phase7_QualificationRateSegments

**合計**: 18シート

---

## 7. 動作確認

### 7.1. データ検証レポート実行

1. スプレッドシートメニュー: 「📊 データ処理」→「データ管理」→「✅ データ検証レポート」
2. 検証レポートダイアログが表示される

**期待される結果**:
- **総合スコア**: 100/100点
- **7種類の検証**:
  - ✅ データ整合性検証: 合格
  - ✅ 型チェック: 合格
  - ✅ NULL値チェック: 合格
  - ✅ 範囲検証: 合格
  - ✅ 重複検証: 合格
  - ✅ カラム名検証: 合格
  - ✅ エンコーディング検証: 合格

### 7.2. 統計サマリー確認

1. スプレッドシートメニュー: 「📊 データ処理」→「データ管理」→「📊 統計サマリー」
2. 統計サマリーダイアログが表示される

**期待される表示**:
```
📊 統計サマリー

総申請者数: X,XXX名
総自治体数: XXX箇所
ペルソナ数: X個
平均年齢: XX.X歳
女性比率: XX.X%
資格保有率: XX.X%
```

### 7.3. ペルソナ難易度確認（Phase 0機能）

1. スプレッドシートメニュー: 「📊 データ処理」→「📈 統計分析・ペルソナ」→「🎯 ペルソナ難易度確認」
2. ペルソナ難易度UIが表示される
3. 6軸フィルター（年齢、性別、資格、エリア、通勤時間、雇用形態）で絞り込み可能

**期待される表示**:
- ペルソナリスト（7-10個）
- 各ペルソナの難易度（A-Eランク）
- 申請者数、平均年齢、女性比率、資格保有率

### 7.4. Phase 1機能動作確認（Phase 1実装後）

#### **PersonaMapData地図可視化**

1. スプレッドシートメニュー: 「📊 データ処理」→「🗺️ Phase 7高度分析」→「🗺️ PersonaMapData地図可視化」
2. Google Maps上に792地点のマーカーが表示される
3. MarkerClustererでクラスター表示される
4. マーカークリック → ペルソナ詳細ポップアップ表示

**期待される表示**:
- 地図中心: 日本全国
- マーカー数: 792個
- クラスター数: 約50-100個（ズームレベルによる）
- ポップアップ例:
  ```
  ペルソナ: 若年層・女性・資格なし
  申請者数: 123名
  平均年齢: 27.5歳
  女性比率: 78.2%
  資格保有率: 12.3%
  ```

#### **PersonaMobilityCross拡張版**

1. スプレッドシートメニュー: 「📊 データ処理」→「🗺️ Phase 7高度分析」→「🚗 PersonaMobilityCross可視化」
2. ペルソナ別移動性ランク分布のグラフが表示される

**期待される分布**:
- A-Eランクの現実的な分布（全Dランクではない）
- 例: Segment 4 → A: 63.4%, B: 18.2%, C: 12.5%, D: 5.6%, E: 0.3%

### 7.5. Phase 2機能動作確認（Phase 2実装後）

#### **MunicipalityFlowネットワーク図**

1. スプレッドシートメニュー: 「📊 データ処理」→「🌊 フロー・移動パターン分析」→「🔀 自治体間フロー分析」
2. Sankeyダイアグラムが表示される（TOP 100エッジ）

**期待される表示**:
- エッジ数: 100本（フィルター適用前: 数千本）
- 自治体名がノードとして表示
- エッジの太さが移動人数に比例

#### **全Phase統合ダッシュボード**

1. スプレッドシートメニュー: 「📊 データ処理」→「📊 統合ビュー」→「🎯 全Phase統合ダッシュボード」
2. タブ切り替えで各Phase機能にアクセス可能

**期待される表示**:
- タブ: 概要、地図、フロー、ペルソナ、Phase 7、統計テスト
- 遅延ロード（初回クリック時にデータ読み込み）

### 7.6. Phase 3機能動作確認（Phase 3実装後）

#### **MapMetricsヒートマップ**

1. スプレッドシートメニュー: 「📊 データ処理」→「🗺️ 地図表示」→「🔥 MapMetricsヒートマップ」
2. Google Maps Heatmap Layerで申請者密度が可視化される

**期待される表示**:
- ヒートマップレイヤー表示
- 高密度エリア: 赤色
- 低密度エリア: 青色
- 凡例表示

#### **DesiredWork詳細検索UI**

1. スプレッドシートメニュー: 「📊 データ処理」→「🔍 データ確認」→「🔍 DesiredWork詳細検索」
2. フィルター機能付き検索UIが表示される

**期待される表示**:
- フィルター: 都道府県、市区町村、年齢範囲、性別、資格
- ページネーション: 100件/ページ
- 検索結果リアルタイム更新

---

## 8. トラブルシューティング

### 8.1. APIキー設定エラー

**エラー**: 「Google Maps APIキーが設定されていません」

**原因**: Script PropertiesにAPIキーが設定されていない

**解決方法**:
1. GASエディタ左側の「⚙️ プロジェクトの設定」をクリック
2. 「スクリプト プロパティ」セクションを確認
3. `GOOGLE_MAPS_API_KEY` が設定されているか確認
4. 設定されていない場合は「4. Google Maps API設定」を再実施

### 8.2. PersonaMapData.csv が0行生成される

**エラー**: PersonaMapData.csvが0行、または「座標が見つからない地域: 793件」

**原因**: geocache.jsonのキー形式とresidence_muniのキー形式が一致していない

**解決方法**:
1. `geocache.json` の存在を確認
2. geocacheのキー形式を確認（例: "東京都新宿区"）
3. `phase7_advanced_analysis.py` の座標取得ロジックを確認（lines 809-830）
4. 修正版を実行: `python run_complete.py`

**期待される結果**:
```
[INFO] 座標が見つからない地域: 1件
PersonaMapData.csv: 792行生成（99.9%成功）
```

### 8.3. PersonaMobilityCross.csv が全Dランク100%

**エラー**: すべてのペルソナがDランク100%（現実的ではない分布）

**原因**: DesiredWork.csv統合がPhase 7分析前に実施されていない

**解決方法**:
1. `test_phase7_complete.py` のDesiredWork統合ロジックを確認（lines 74-115）
2. `run_complete.py` 実行前にDesiredWork.csvが存在することを確認
3. 再実行: `python run_complete.py`

**期待される結果**:
```
PersonaMobilityCross.csv:
- A: 2.9%
- B: 1.5%
- C: 16.8%
- D: 78.8%
（現実的な分布）
```

### 8.4. CSVインポート時「ファイルが見つかりません」

**エラー**: CSVインポート時にファイルが見つからない

**原因**: Pythonスクリプト実行が完了していない、またはファイルパスが間違っている

**解決方法**:
1. `python run_complete.py` を再実行
2. `gas_output_phase1` フォルダが存在することを確認
3. 必須4ファイルが存在することを確認:
   - MapMetrics.csv
   - Applicants.csv
   - DesiredWork.csv
   - AggDesired.csv
4. GASのファイル選択ダイアログで正しいディレクトリを指定

### 8.5. Google Maps API読み込みエラー

**エラー**: 「Google Maps APIの読み込みに失敗しました」

**原因**: APIキーが無効、またはAPI制限設定

**解決方法**:
1. Google Cloud Consoleで「Maps JavaScript API」が有効化されているか確認
2. APIキーの使用状況を確認（日次上限に達していないか）
3. APIキーの制限設定を確認（HTTPリファラー制限が厳しすぎないか）
4. 必要に応じてAPIキーを再生成

### 8.6. 「メモリ不足」エラー（GAS）

**エラー**: GAS実行時に「メモリ制限を超えました」

**原因**: DesiredWork.csv（1.3MB）等の大規模データを一括読み込み

**解決方法**:
1. サンプリング版関数を使用（例: `loadDesiredWorkDataSampled(5000)`）
2. ページネーション実装を確認
3. データを分割してインポート

### 8.7. 「実行時間超過」エラー（GAS）

**エラー**: GAS実行時に「最大実行時間（6分）を超えました」

**原因**: 複雑な処理（ネットワーク図生成等）の実行時間が長い

**解決方法**:
1. TOP100エッジフィルターを適用（`loadMunicipalityFlowEdges()` で実装済み）
2. 遅延ロード実装を確認（統合ダッシュボード）
3. 必要に応じて処理を分割

---

## 9. ロールバック手順

### 9.1. GASスクリプトのロールバック

1. GASエディタ左上の「時計アイコン」（バージョン管理）をクリック
2. 過去のバージョンを選択
3. 「復元」をクリック

### 9.2. Googleスプレッドシートのロールバック

1. スプレッドシートメニュー: 「ファイル」→「変更履歴」→「変更履歴を表示」
2. 過去のバージョンを選択
3. 「この版を復元」をクリック

### 9.3. Pythonスクリプトのロールバック

Gitを使用している場合:

```bash
# コミット履歴確認
git log --oneline

# 特定のコミットに戻る
git checkout <commit-hash>

# またはリセット
git reset --hard <commit-hash>
```

Gitを使用していない場合:
- バックアップから復元

### 9.4. データクリア（緊急時）

すべてのデータをクリアして再スタート:

1. スプレッドシートメニュー: 「📊 データ処理」→「データ管理」→「🧹 全データクリア」
2. 確認ダイアログで「はい」を選択
3. すべてのPhaseシート（18シート）が削除される
4. 「6. GASへのCSVインポート」から再実施

---

## 10. 定期メンテナンス

### 10.1. geocache.json バックアップ（月次推奨）

```bash
# geocache.jsonをバックアップ
cp geocache.json "geocache_backup_$(date +%Y%m%d).json"
```

**理由**: ジオコーディングキャッシュ（1,901件）の喪失を防ぐため

### 10.2. データ検証レポート実行（週次推奨）

1. スプレッドシートメニュー: 「📊 データ処理」→「データ管理」→「✅ データ検証レポート」
2. スコアが100/100点であることを確認
3. スコアが低い場合は原因を調査

### 10.3. Python依存ライブラリ更新（四半期推奨）

```bash
# 最新版を確認
pip list --outdated

# requirements.txtを更新（慎重に）
pip install --upgrade pandas numpy scikit-learn networkx matplotlib scipy

# 更新後テスト実行
python COMPREHENSIVE_TEST_SUITE.py
```

---

## 11. サポート情報

### 11.1. ドキュメント参照

- **完全実装計画**: `claudedocs/COMPLETE_IMPLEMENTATION_PLAN.md`
- **Phase 2-3詳細設計**: `claudedocs/PHASE2_3_DETAILED_DESIGN.md`
- **UltraThinkレビュー**: `claudedocs/IMPLEMENTATION_ULTRATHINK_REVIEW.md`

### 11.2. よくある質問（FAQ）

**Q1: Google Maps API の料金はかかりますか？**
A1: Maps JavaScript APIは月間$200の無料枠があります。通常の使用では無料枠内に収まりますが、geocache.jsonを活用することでAPI呼び出しを最小化しています。

**Q2: Phase 1実装はいつ完了しますか？**
A2: Phase 1実装は約10-12時間を見積もっています。PersonaMapData地図（4時間）、PersonaMobilityCross拡張（3時間）、3次元クロス分析（3時間）、テスト（2時間）の順に実装します。

**Q3: 本番環境へのデプロイ前に必須の確認事項は？**
A3: 以下を確認してください:
- データ検証レポート: 100/100点
- PersonaMapData.csv: 792行生成
- PersonaMobilityCross.csv: 現実的な分布
- Google Maps APIキー: Script Propertiesに設定済み
- 全18シートがGoogleスプレッドシートにインポート済み

**Q4: エラーが発生した場合の最初の対処方法は？**
A4: まず「8. トラブルシューティング」セクションを参照してください。該当するエラーがない場合は、GASエディタの「実行ログ」（表示 → ログ）を確認し、エラーメッセージを特定してください。

---

## 12. デプロイチェックリスト

Phase 0（基盤）デプロイ前の最終確認:

- [ ] Python 3.8以上インストール済み
- [ ] requirements.txt インストール完了
- [ ] Googleスプレッドシート作成完了
- [ ] GASファイル5個アップロード完了（GoogleMapsAPIConfig.gs, DataValidationEnhanced.gs, PersonaDifficultyChecker.gs, MenuIntegration.gs, PythonCSVImporter.gs）
- [ ] HTMLファイル2個アップロード完了（PersonaDifficultyCheckerUI.html, Upload_Enhanced.html）
- [ ] Google Maps APIキー取得完了
- [ ] Script PropertiesにAPIキー設定完了（`checkAPIKeyStatus()` で確認）
- [ ] `python run_complete.py` 実行完了（18 CSVファイル生成）
- [ ] PersonaMapData.csv = 792行生成（0行でない）
- [ ] PersonaMobilityCross.csv = 現実的な分布（全Dランクでない）
- [ ] geocache.json = 1,901件存在
- [ ] 全18シートをGoogleスプレッドシートにインポート完了
- [ ] データ検証レポート = 100/100点
- [ ] ペルソナ難易度確認UIが正常動作
- [ ] 統計サマリーが正常表示

Phase 1デプロイ前の追加確認:

- [ ] PersonaMapDataVisualization.gs アップロード完了
- [ ] Phase7PersonaMobilityCrossViz.gs アップロード完了
- [ ] cross_analysis_engine.py 実装完了
- [ ] PersonaMapData地図で792マーカー表示確認
- [ ] PersonaMobilityCross拡張版グラフ表示確認
- [ ] 3次元クロス分析結果CSV出力確認
- [ ] Phase 1ユニットテスト合格
- [ ] Phase 1統合テスト合格

---

**デプロイ完了後、本ドキュメントを保存し、定期的に参照してください。**
