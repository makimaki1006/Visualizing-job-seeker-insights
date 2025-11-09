# コードリファレンス

ジョブメドレー求職者データ分析プロジェクトの全コード詳細説明。

---

## 📁 Pythonスクリプト

### run_complete.py

**ファイルパス**: `job_medley_project/python_scripts/run_complete.py`

**役割**: 統合実行スクリプト（エントリーポイント）

**主要関数**:

#### `main()`
```python
def main():
```
- **目的**: GUIファイル選択→データ処理→Phase別エクスポートの統合実行
- **処理フロー**:
  1. `select_csv_file()`でGUIファイル選択
  2. `AdvancedJobSeekerAnalyzer`インスタンス作成
  3. Phase 1, 2, 3, 6のデータエクスポート実行
- **依存関係**: `test_phase6_temp`モジュールからインポート
- **実行コマンド**: `python run_complete.py`

#### `select_csv_file()`
```python
from test_phase6_temp import select_csv_file
```
- **目的**: tkinterによるGUIファイル選択ダイアログ表示
- **戻り値**: 選択されたCSVファイルの絶対パス
- **例外**: ファイル未選択時にValueError

**エクスポート順序**:
```python
analyzer.export_phase1_data(output_dir="gas_output_phase1")
analyzer.export_phase2_data(output_dir="gas_output_phase2")
analyzer.export_phase3_data(output_dir="gas_output_phase3", n_clusters=5)
analyzer.export_phase6_data(output_dir="gas_output_phase6")
```

---

### test_phase6_temp.py

**ファイルパス**: `job_medley_project/python_scripts/test_phase6_temp.py`

**役割**: Phase 1-6の分析エンジン（ライブラリ的役割）

**重要注記**: ファイル名は`test_phase6_temp.py`だが、実際にはPhase 1, 2, 3, 6すべての処理を担当。Phase 4, 5は設計上存在しない。

---

#### クラス構成

##### `MasterData`
```python
class MasterData:
```
- **目的**: マスターデータの一元管理
- **属性**:
  - `都道府県一覧`: 日本の都道府県リスト
  - `政令指定都市マッピング`: 区レベルデータ保持用
  - その他マスターデータ

##### `AdvancedJobSeekerAnalyzer`
```python
class AdvancedJobSeekerAnalyzer:
```
- **目的**: 求職者データの包括的分析
- **初期化パラメータ**:
  - `filepath`: 入力CSVファイルパス
  - `api_key`: Google Maps APIキー（オプション）
- **メソッド数**: 30以上

---

#### コアメソッド

##### `__init__(self, filepath, api_key=None)`
- **目的**: Analyzerの初期化、データ読み込み、前処理
- **処理内容**:
  1. CSVファイル読み込み
  2. ジオコーディングキャッシュ読み込み
  3. 基本データ処理実行

##### `load_geocache(self)`
- **目的**: `geocache.json`からキャッシュ読み込み（1,901件）
- **効果**: Google Maps API呼び出し削減（コスト削減・高速化）

##### `save_geocache(self)`
- **目的**: ジオコーディング結果をキャッシュファイルに保存

##### `process_data(self)`
- **目的**: データ前処理のオーケストレーション
- **呼び出しメソッド**:
  - `_extract_basic_info()`
  - `_process_desired_work()`
  - その他前処理メソッド

##### `_extract_basic_info(self, df)`
- **目的**: 基本情報抽出（ID, 性別, 年齢, 居住地等）
- **出力**: 申請者基本情報DataFrame

##### `_process_desired_work(self, df)`
- **目的**: 希望勤務地データ処理
- **処理内容**:
  1. 住所パース（正規表現使用）
  2. 市区町村レベルデータ抽出
  3. 区レベル粒度保持（京都市伏見区、京都市右京区を個別保持）

##### `_extract_municipality(self, address)`
- **目的**: 日本語住所から市区町村を抽出
- **正規表現パターン**:
  ```python
  r'(.+?市.+?区|.+?(?:市|区|町|村|郡))(.+?(?:町|村))?'
  ```
- **例**:
  - 入力: `"京都府京都市西京区"`
  - 出力: `"京都府京都市西京区"` （都道府県名保持）

---

#### Phase別エクスポートメソッド

##### `export_phase1_data(self, output_dir='gas_output_phase1')`
- **目的**: Phase 1（基礎集計）CSVファイル生成
- **出力ファイル**:
  1. **MapMetrics.csv** - 地図表示用データ（座標付き）
     - データ生成失敗の可能性（現状空ファイル）
  2. **Applicants.csv** - 申請者基本情報
     - カラム: `ID,性別,年齢,年齢バケット,居住地_都道府県,居住地_市区町村`
     - データあり（例: `ID_1,女性,50,50代,栃木県,宇都宮市`）
  3. **DesiredWork.csv** - 希望勤務地詳細
     - データ生成失敗の可能性（現状空ファイル）
  4. **AggDesired.csv** - 集計データ
     - カラム: `都道府県,市区町村,キー,カウント`
     - データあり
- **エンコーディング**: UTF-8 with BOM

##### `export_phase2_data(self, output_dir='gas_output_phase2')`
- **目的**: Phase 2（統計分析）CSVファイル生成
- **出力ファイル**:
  1. **ChiSquareTests.csv** - カイ二乗検定結果
     - データ生成失敗の可能性（現状空ファイル）
  2. **ANOVATests.csv** - ANOVA検定結果
     - カラム構造不明（要確認）

##### `export_phase3_data(self, output_dir='gas_output_phase3', n_clusters=5)`
- **目的**: Phase 3（ペルソナ分析）CSVファイル生成
- **パラメータ**:
  - `n_clusters`: クラスタリング数（デフォルト5）
- **出力ファイル**:
  1. **PersonaSummary.csv** - ペルソナサマリー
     - カラム: `segment_id,segment_name,count,percentage,avg_age,female_ratio,avg_qualifications,top_prefecture,avg_desired_locations,top_prefectures_all`
     - データあり（例: `0,若年層地元密着型,205,21.9,27.3,0.72,0,,0.0,`）
  2. **PersonaDetails.csv** - ペルソナ詳細
     - カラム構造不明（要確認）

##### `export_phase6_data(self, output_dir='gas_output_phase6')`
- **目的**: Phase 6（フロー・移動パターン分析）CSVファイル生成
- **出力ファイル**:
  1. **MunicipalityFlowEdges.csv** - 自治体間フローエッジ
     - カラム: `Source_Municipality,Target_Municipality,Flow_Count`
     - データあり（例: `京都府亀岡市,京都府京都市西京区,2`）
  2. **MunicipalityFlowNodes.csv** - 自治体間フローノード
     - カラム構造不明（要確認）
  3. **ProximityAnalysis.csv** - 移動パターン分析
     - カラム: `proximity_bucket,Count,Avg_Distance_km,Median_Distance_km`
     - データあり（例: `0-10km,47,4.6,4.7`）

---

#### 分析メソッド（Phase 6）

##### `_analyze_flow(self)`
- **目的**: 自治体間人材フロー分析
- **処理内容**:
  1. 居住地と希望勤務地のペア作成
  2. フロー頻度集計
  3. エッジ・ノードデータ生成

##### `_calculate_proximity(self, lat1, lng1, lat2, lng2)`
- **目的**: 2地点間の距離計算（Haversine公式）
- **単位**: キロメートル
- **戻り値**: 距離（km）

##### `_proximity_analysis(self)`
- **目的**: 移動パターン分析（距離バケット別集計）
- **バケット**: 0-10km, 10-20km, 20-50km, 50-100km, 100km+

---

#### ユーティリティメソッド

##### `_ensure_directory(self, path)`
- **目的**: ディレクトリ存在確認、無ければ作成
- **使用箇所**: すべてのエクスポートメソッド

##### `_export_csv(self, df, filename, output_dir)`
- **目的**: UTF-8 with BOMでCSVエクスポート
- **処理内容**:
  1. ディレクトリ作成
  2. CSVファイル書き込み
  3. ログ出力

---

### COMPREHENSIVE_TEST_SUITE.py

**ファイルパス**: `job_medley_project/python_scripts/COMPREHENSIVE_TEST_SUITE.py`

**役割**: MECEテストスイート（40テスト）

**主要関数**:

#### `main()`
- **目的**: 40件のテスト実行とレポート生成
- **テスト構成**:
  - Phase 1: Python正規表現テスト（10回）
  - Phase 2: データ生成テスト（10回）
  - Phase 3: GAS関数ユニットテスト（10回）
  - Phase 4: 統合テスト（10回）
  - Phase 5: E2Eテスト（10回）

#### `run_regex_tests()`
- **目的**: 住所パース正規表現の検証
- **テストケース**: 京都市西京区、東京都千代田区等

#### `run_data_generation_tests()`
- **目的**: CSV生成ロジックの検証
- **確認項目**: ファイル存在、カラム数、データ型

#### `run_gas_unit_tests()`
- **目的**: GAS関数のモック検証
- **注記**: 実際のGAS環境では実行不可

#### `run_integration_tests()`
- **目的**: Python-GAS間のデータフロー検証

#### `run_e2e_tests()`
- **目的**: エンドツーエンドシナリオ検証

**出力ファイル**:
- `TEST_RESULTS_COMPREHENSIVE.json`
- `test_output.txt`

---

## 📁 GASスクリプト

### MenuIntegration.gs

**ファイルパス**: `job_medley_project/gas_files/scripts/MenuIntegration.gs`

**役割**: Googleスプレッドシートメニュー統合

**関数一覧**:

#### `onOpen()`
```javascript
function onOpen() {
```
- **目的**: スプレッドシート起動時のメニュー構築
- **トリガー**: スプレッドシート開封時に自動実行
- **処理内容**:
  1. メニュー「📊 データ処理」作成
  2. サブメニュー追加（高速CSVインポート、Python連携、地図表示等）
  3. データ管理機能追加

#### `showEnhancedUploadDialog()`
```javascript
function showEnhancedUploadDialog() {
```
- **目的**: 高速CSVアップロードUI表示
- **表示HTML**: `Upload_Enhanced.html`
- **呼び出し元**: メニュー「⚡ 高速CSVインポート（推奨）」

#### `importPythonCSVDialog()`
```javascript
function importPythonCSVDialog() {
```
- **目的**: Python結果CSVインポートダイアログ表示
- **呼び出し元**: メニュー「📥 Python結果CSVを取り込み」

---

### PythonCSVImporter.gs

**ファイルパス**: `job_medley_project/gas_files/scripts/PythonCSVImporter.gs`

**役割**: Python処理結果のCSV/JSONインポート

**関数一覧**:

#### `batchImportPythonResults()`
```javascript
function batchImportPythonResults() {
```
- **目的**: Phase 1-6のCSVファイル一括インポート
- **読み込みファイル**:
  - Phase 1: MapMetrics.csv, Applicants.csv, DesiredWork.csv, AggDesired.csv
  - Phase 2: ChiSquareTests.csv, ANOVATests.csv
  - Phase 3: PersonaSummary.csv, PersonaDetails.csv
  - Phase 6: MunicipalityFlowEdges.csv, MunicipalityFlowNodes.csv, ProximityAnalysis.csv
- **処理フロー**:
  1. 各ファイルの存在確認
  2. CSV→シート変換
  3. 検証実行

#### `processCSVFile(file, ss, sheetName)`
```javascript
function processCSVFile(file, ss, sheetName) {
```
- **目的**: CSVファイルをスプレッドシートに変換
- **パラメータ**:
  - `file`: DriveAppのFileオブジェクト
  - `ss`: Spreadsheetオブジェクト
  - `sheetName`: 作成するシート名
- **処理内容**:
  1. CSV文字列読み込み
  2. 行・カラム分割
  3. シート作成・データ書き込み

#### `processJSONFile(file, ss)`
```javascript
function processJSONFile(file, ss) {
```
- **目的**: JSONファイルをスプレッドシートに変換
- **対象**: `gas_map_data.json`（オプション）
- **処理内容**:
  1. JSON解析
  2. オブジェクト構造をテーブル変換
  3. シート書き込み

#### `validateImportedData(ss)`
```javascript
function validateImportedData(ss) {
```
- **目的**: インポート後のデータ検証
- **検証項目**:
  - 必須シートの存在確認
  - カラム数チェック
  - データ型検証

#### `showPythonReport()`
```javascript
function showPythonReport() {
```
- **目的**: Python処理結果のサマリーレポート表示
- **表示内容**:
  - インポート成功/失敗件数
  - データ品質スコア
  - エラー詳細

#### `importSinglePythonCSV(fileName)`
```javascript
function importSinglePythonCSV(fileName) {
```
- **目的**: 個別CSVファイルのインポート
- **使用ケース**: 特定Phaseの再インポート

---

### DataValidationEnhanced.gs

**ファイルパス**: `job_medley_project/gas_files/scripts/DataValidationEnhanced.gs`

**役割**: 拡張データ検証機能（7種類）

**関数一覧**:

#### `validateDataTypes(sheet, sheetName)`
```javascript
function validateDataTypes(sheet, sheetName) {
```
- **目的**: データ型検証
- **検証内容**:
  - 数値カラムが数値型か
  - 文字列カラムが文字列型か
  - 日付カラムが日付型か

#### `validateCoordinates(sheet)`
```javascript
function validateCoordinates(sheet) {
```
- **目的**: 座標範囲検証（日本国内）
- **緯度範囲**: 24.0～46.0
- **経度範囲**: 122.0～154.0

#### `validateColumnCount(sheet, sheetName)`
```javascript
function validateColumnCount(sheet, sheetName) {
```
- **目的**: カラム数検証
- **期待値**:
  - Applicants: 6カラム
  - MapMetrics: 不明（データ生成失敗の可能性）
  - PersonaSummary: 10カラム

#### `detectDuplicateKeys(sheet, keyColumn, sheetName)`
```javascript
function detectDuplicateKeys(sheet, keyColumn, sheetName) {
```
- **目的**: 重複キー検出
- **対象**: ID, segment_id等のPrimary Key

#### `validateAggregation(ss)`
```javascript
function validateAggregation(ss) {
```
- **目的**: 集計値整合性検証
- **検証内容**:
  - AggDesired.csvの合計値とApplicants.csvの行数が一致するか

#### `validateForeignKeys(ss)`
```javascript
function validateForeignKeys(ss) {
```
- **目的**: 外部キー整合性検証
- **検証内容**:
  - DesiredWork.csvのApplicant_IDがApplicants.csvに存在するか

#### `validateWardLevelGranularity(sheet)`
```javascript
function validateWardLevelGranularity(sheet) {
```
- **目的**: 区レベル粒度検証
- **検証内容**:
  - 京都市伏見区、京都市右京区が個別に保持されているか
  - 市レベルに集約されていないか

#### `validateImportedDataEnhanced(ss)`
```javascript
function validateImportedDataEnhanced(ss) {
```
- **目的**: 7種類の検証を統合実行
- **戻り値**: 検証結果オブジェクト（100点満点）

#### `showValidationReport()`
```javascript
function showValidationReport() {
```
- **目的**: データ検証レポートUI表示
- **表示内容**:
  - 検証スコア（0-100点）
  - 検証項目別結果
  - エラー詳細

---

### PersonaDifficultyChecker.gs

**ファイルパス**: `job_medley_project/gas_files/scripts/PersonaDifficultyChecker.gs`

**役割**: ペルソナ難易度分析バックエンド

**関数一覧**:

#### `showPersonaDifficultyChecker()`
```javascript
function showPersonaDifficultyChecker() {
```
- **目的**: ペルソナ難易度UI表示
- **表示HTML**: `PersonaDifficultyCheckerUI.html`

#### `getPersonaDataForDifficulty()`
```javascript
function getPersonaDataForDifficulty() {
```
- **目的**: PersonaSummaryシートからデータ取得
- **戻り値**: ペルソナ配列（JSON）

#### `calculateDifficultyScore(params)`
```javascript
function calculateDifficultyScore(params) {
```
- **目的**: 6軸難易度スコア計算
- **パラメータ**:
  - `avg_age`: 平均年齢
  - `female_ratio`: 女性比率
  - `avg_qualifications`: 平均資格数
  - `avg_desired_locations`: 平均希望勤務地数
  - `percentage`: セグメント割合
- **戻り値**: 0-100の難易度スコア

#### `getAgeScore(avgAge)`
```javascript
function getAgeScore(avgAge) {
```
- **目的**: 年齢による難易度スコア算出
- **ロジック**:
  - 若年層（20-30代）: 高スコア（採用困難）
  - 中高年層（40-50代）: 低スコア（採用容易）

#### `getDifficultyLevel(score)`
```javascript
function getDifficultyLevel(score) {
```
- **目的**: スコアから難易度レベル判定
- **レベル**:
  - 80-100: 超高難易度
  - 60-79: 高難易度
  - 40-59: 中難易度
  - 20-39: 低難易度
  - 0-19: 超低難易度

#### `getAgeGroup(avgAge)`
```javascript
function getAgeGroup(avgAge) {
```
- **目的**: 平均年齢から年齢グループ分類
- **グループ**: 20代, 30代, 40代, 50代, 60代以上

#### `getQualificationLevel(avgQualifications)`
```javascript
function getQualificationLevel(avgQualifications) {
```
- **目的**: 平均資格数から資格レベル分類
- **レベル**: 無資格, 低資格, 中資格, 高資格, 超高資格

#### `getMobilityLevel(avgDesiredLocations)`
```javascript
function getMobilityLevel(avgDesiredLocations) {
```
- **目的**: 平均希望勤務地数から移動性レベル分類
- **レベル**: 極低移動性, 低移動性, 中移動性, 高移動性, 超高移動性

#### `getGenderCategory(femaleRatio)`
```javascript
function getGenderCategory(femaleRatio) {
```
- **目的**: 女性比率から性別カテゴリ分類
- **カテゴリ**: 男性優位, 男性やや多い, バランス, 女性やや多い, 女性優位

#### `getMarketSizeCategory(percentage)`
```javascript
function getMarketSizeCategory(percentage) {
```
- **目的**: セグメント割合から市場規模分類
- **カテゴリ**: 極小市場, 小市場, 中市場, 大市場, 超大市場

#### `filterPersonasByConditions(filters)`
```javascript
function filterPersonasByConditions(filters) {
```
- **目的**: 6軸フィルタによるペルソナ絞り込み
- **フィルタ軸**:
  1. 年齢グループ
  2. 性別カテゴリ
  3. 資格レベル
  4. 移動性レベル
  5. 市場規模
  6. 総合難易度
- **戻り値**: フィルタ条件に合致するペルソナ配列

---

## 📁 HTMLファイル

### PersonaDifficultyCheckerUI.html

**ファイルパス**: `job_medley_project/gas_files/html/PersonaDifficultyCheckerUI.html`

**役割**: ペルソナ難易度確認UI

**主要機能**:
- 6軸フィルタUIコンポーネント
- ペルソナ一覧テーブル表示
- 難易度スコア可視化（プログレスバー）
- フィルタリング結果のリアルタイム更新

**使用箇所**: `showPersonaDifficultyChecker()`から表示

---

### Upload_Enhanced.html

**ファイルパス**: `job_medley_project/gas_files/html/Upload_Enhanced.html`

**役割**: 高速CSVアップロードUI

**主要機能**:
- ファイル選択UIコンポーネント
- アップロード進捗表示
- エラーハンドリング
- 大容量CSVファイル対応

**使用箇所**: `showEnhancedUploadDialog()`から表示

---

## 📊 データフロー

```
入力CSVファイル（data/input/）
  ↓
run_complete.py: main()
  ↓
AdvancedJobSeekerAnalyzer: __init__()
  ↓
process_data()
  ├─ _extract_basic_info() → Applicants.csv
  ├─ _process_desired_work() → DesiredWork.csv
  └─ _analyze_flow() → MunicipalityFlowEdges.csv
  ↓
export_phase1_data() → gas_output_phase1/
export_phase2_data() → gas_output_phase2/
export_phase3_data() → gas_output_phase3/
export_phase6_data() → gas_output_phase6/
  ↓
GAS: batchImportPythonResults()
  ↓
processCSVFile() × 11ファイル
  ↓
validateImportedDataEnhanced()
  ↓
Googleスプレッドシート完成
```

---

## 🔍 重要な注記

### Phase 4, 5の不在について

**調査結果**: `grep -r "phase4\|phase5" python_scripts/`の結果、0件

**結論**: Phase 4, 5は設計上存在しない（未実装ではなく、意図的に欠番）

**理由**: 不明（要プロジェクト設計書確認）

---

### データ生成失敗の可能性

以下のCSVファイルは空ファイル（BOM文字のみ）:

1. **MapMetrics.csv** - ヘッダーなし、データなし
2. **DesiredWork.csv** - ヘッダーなし、データなし
3. **ChiSquareTests.csv** - ヘッダーなし、データなし

**原因**: 不明（要調査）

**対処**: 該当Phase処理のデバッグが必要

---

### 入力CSVファイル

**格納場所**: `job_medley_project/data/input/`

**ファイル一覧**:
1. 統合_求職者情報沖縄_介護 (1).csv (1,485,916 bytes)
2. 統合_求職者情報京都_介護 (1).csv (4,123,981 bytes)
3. 栃木_生活相談員 (1).csv (572,769 bytes)
4. 統合_求職者情報宮城_介護.csv (3,162,226 bytes)

**カラム構造**: 250以上のカラム、HTML class名（`u-fw-bold`, `o-line__item`等）

**読み込み方法**: `run_complete.py`のGUIファイル選択でこれらを指定

---

### test_phase6_temp.pyの命名矛盾

**ファイル名**: `test_phase6_temp.py`

**実際の役割**: Phase 1, 2, 3, 6すべての処理を担当

**理由**: 不明（リファクタリング履歴により命名が陳腐化した可能性）

**影響**: なし（内部実装は正常）

---

## 📝 メンテナンス情報

- **作成日**: 2025-10-26
- **最終更新**: 2025-10-26
- **ドキュメント種別**: コードリファレンス（MECE準拠）
- **対象バージョン**: 1.0
