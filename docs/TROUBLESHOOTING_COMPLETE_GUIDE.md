# トラブルシューティング完全ガイド（最適化版対応）

**バージョン**: 1.0
**最終更新**: 2025年10月26日
**対象**: Phase 1-7の最適化実装済みシステム

---

## 📋 目次

1. [診断フローチャート](#診断フローチャート)
2. [Python側の問題](#python側の問題)
3. [GAS側の問題](#gas側の問題)
4. [データ品質の問題](#データ品質の問題)
5. [パフォーマンスの問題](#パフォーマンスの問題)
6. [統合の問題](#統合の問題)
7. [クイックリファレンス](#クイックリファレンス)

---

## 診断フローチャート

### 問題の切り分け

```
問題が発生した
    ↓
Python実行中の問題？
    ├─ Yes → [Python側の問題](#python側の問題)
    └─ No
        ↓
    GAS実行中の問題？
        ├─ Yes → [GAS側の問題](#gas側の問題)
        └─ No
            ↓
        データが正しくない？
            ├─ Yes → [データ品質の問題](#データ品質の問題)
            └─ No
                ↓
            処理が遅い？
                ├─ Yes → [パフォーマンスの問題](#パフォーマンスの問題)
                └─ No
                    ↓
                Python↔GAS間の連携？
                    └─ Yes → [統合の問題](#統合の問題)
```

---

## Python側の問題

### P1: ファイルが見つかりません（FileNotFoundError）

**症状**:
```python
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\...\\統合_求職者情報宮城_介護.csv'
```

**診断**:

1. **ファイルパスを確認**
   ```bash
   # ファイルが実際に存在するか確認
   ls "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\input\統合_求職者情報宮城_介護.csv"
   ```

2. **エンコーディングを確認**
   - Windowsのパスに日本語が含まれる場合、エンコーディングエラーの可能性

**解決方法**:

**方法A: 絶対パスを使用**
```python
filepath = r"C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\data\input\統合_求職者情報宮城_介護.csv"
```

**方法B: 相対パスを使用**
```python
from pathlib import Path

# スクリプトの親ディレクトリを基準にする
base_dir = Path(__file__).parent.parent
filepath = base_dir / 'data' / 'input' / '統合_求職者情報宮城_介護.csv'
```

**方法C: ファイル選択GUIを使用**
```python
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()
filepath = filedialog.askopenfilename(
    title='CSVファイルを選択',
    filetypes=[('CSV files', '*.csv')]
)
```

---

### P2: モジュールが見つかりません（ModuleNotFoundError）

**症状**:
```python
ModuleNotFoundError: No module named 'pandas'
```

**診断**:

```bash
# インストール済みパッケージを確認
pip list | grep pandas
```

**解決方法**:

**方法A: pipでインストール**
```bash
pip install pandas numpy scikit-learn matplotlib seaborn
```

**方法B: requirements.txtを使用**
```bash
# requirements.txtを作成
cat > requirements.txt << EOF
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=0.24.0
matplotlib>=3.4.0
seaborn>=0.11.0
EOF

# 一括インストール
pip install -r requirements.txt
```

**方法C: 仮想環境を使用**
```bash
# 仮想環境作成
python -m venv venv

# 仮想環境アクティベート（Windows）
venv\Scripts\activate

# パッケージインストール
pip install -r requirements.txt
```

---

### P3: メモリ不足エラー（MemoryError）

**症状**:
```python
MemoryError: Unable to allocate ... for an array with shape (...)
```

**診断**:

```python
import psutil

# 使用可能メモリを確認
available_memory = psutil.virtual_memory().available / (1024**3)
print(f"使用可能メモリ: {available_memory:.2f} GB")
```

**解決方法**:

**方法A: チャンクで処理**
```python
# 大きなCSVをチャンクで読み込む
chunk_size = 10000
chunks = []

for chunk in pd.read_csv(filepath, chunksize=chunk_size):
    # 各チャンクを処理
    processed_chunk = process_chunk(chunk)
    chunks.append(processed_chunk)

# 最後に結合
df = pd.concat(chunks, ignore_index=True)
```

**方法B: データ型を最適化**
```python
# データ型を最適化してメモリ削減
df['age'] = df['age'].astype('int8')  # 0-255の範囲なら int8
df['category'] = df['category'].astype('category')  # カテゴリカルデータ
```

**方法C: 不要な列を削除**
```python
# 必要な列のみ読み込む
usecols = ['applicant_id', 'age', 'gender', 'prefecture']
df = pd.read_csv(filepath, usecols=usecols)
```

---

### P4: タイムアウト（処理が120秒を超える）

**症状**:
```
処理時間: 125秒
Phase 2: データなし
Phase 6: データなし
```

**診断**:

```bash
# 処理時間を測定
python test_run_timed.py
```

**期待される出力（最適化版）**:
```
合計処理時間: 87秒
タイムアウト余裕: 33秒 (2分制限)
```

**実際の出力（問題あり）**:
```
合計処理時間: 125秒
Phase 6: タイムアウト
```

**解決方法（最適化版を適用）**:

**ステップ1: ベクトル化実装を確認**
```bash
# _haversine_distance_vectorized() メソッドが存在するか確認
grep -n "_haversine_distance_vectorized" python_scripts/test_phase6_temp.py
# 期待: 1543:    def _haversine_distance_vectorized(self, lat1, lon1, lat2, lon2):
```

**ステップ2: 最適化版_prepare_phase6_data()を確認**
```bash
# ユニークマッピングが実装されているか確認
grep -n "drop_duplicates" python_scripts/test_phase6_temp.py
# 期待: 2825:    unique_residence = flow_data[['居住地_都道府県', '居住地_市区町村']].drop_duplicates()
```

**ステップ3: 実行順序を確認**
```bash
# Phase 7がPhase 6より先に実行されるか確認
grep -A 5 "Phase 7" python_scripts/run_complete.py
# 期待: Phase 7 → Phase 6 の順序
```

**ステップ4: 再実行**
```bash
python run_complete.py
```

**ステップ5: 処理時間を確認**
```
期待:
- Phase 2: 7秒
- Phase 6: 39秒
- 合計: 87秒
```

---

### P5: Unicode エンコーディングエラー

**症状**:
```python
UnicodeEncodeError: 'cp932' codec can't encode character '\u2705' in position 0
```

**診断**:

```python
import sys
print(sys.getdefaultencoding())  # 期待: 'utf-8'
print(sys.stdout.encoding)  # Windows: 'cp932' または 'shift_jis'
```

**解決方法**:

**方法A: print()で絵文字を避ける**
```python
# 絵文字を避ける
# Before
print('✅ テスト成功')

# After
print('[PASS] テスト成功')
```

**方法B: 環境変数を設定**
```bash
# Windowsの場合
set PYTHONIOENCODING=utf-8
python run_complete.py
```

**方法C: ファイル出力時にエンコーディングを指定**
```python
# ファイル出力時はUTF-8を明示
with open('output.csv', 'w', encoding='utf-8') as f:
    f.write(data)
```

---

### P6: Phase 2データが空（BOM 5バイトのみ）

**症状**:
```bash
ls -l data/output/phase2/ChiSquareTests.csv
# 出力: 5 bytes（BOMのみ）
```

**診断**:

```bash
# ファイルの内容を確認（16進数ダンプ）
xxd data/output/phase2/ChiSquareTests.csv
# 期待: EF BB BF（UTF-8 BOMのみ）
```

**原因**:
- タイムアウトによりPhase 2が未実行

**解決方法（最適化版で修正済み）**:

**ステップ1: 最適化版を確認**
```bash
# test_phase6_temp.py に最適化実装があるか確認
python -c "
import test_phase6_temp
analyzer = test_phase6_temp.AdvancedJobSeekerAnalyzer('dummy.csv')
print('_haversine_distance_vectorized' in dir(analyzer))
"
# 期待: True
```

**ステップ2: 実行順序を確認**
```bash
grep -n "Phase 7" python_scripts/run_complete.py
grep -n "Phase 6" python_scripts/run_complete.py
# 期待: Phase 7の行番号 < Phase 6の行番号
```

**ステップ3: 再実行**
```bash
python run_complete.py
```

**ステップ4: ファイルサイズを確認**
```bash
ls -lh data/output/phase2/ChiSquareTests.csv
# 期待: 691 bytes 以上
```

---

### P7: Phase 6データが生成されない

**症状**:
```bash
ls python_scripts/gas_output_phase6/
# 出力: （空）
```

**診断**:

```bash
# エラーログを確認
python run_complete.py 2>&1 | grep "Phase 6"
# エラーメッセージを探す
```

**原因**:
- Phase 6の処理時間が30秒超でタイムアウト

**解決方法（最適化版で修正済み）**:

**ステップ1: ベクトル化実装を確認**
```python
# test_phase6_temp.py を開く
# lines 1543-1603 に _haversine_distance_vectorized() があるか確認
```

**ステップ2: ユニークマッピング実装を確認**
```python
# test_phase6_temp.py を開く
# lines 2814-2935 に drop_duplicates() があるか確認
```

**ステップ3: 再実行**
```bash
python run_complete.py
```

**ステップ4: ファイル生成確認**
```bash
ls -lh python_scripts/gas_output_phase6/
# 期待:
# - MunicipalityFlowEdges.csv (152KB)
# - MunicipalityFlowNodes.csv (8KB)
# - ProximityAnalysis.csv (40KB)
```

---

### P8: ImportError（循環インポート）

**症状**:
```python
ImportError: cannot import name 'AdvancedJobSeekerAnalyzer' from partially initialized module 'test_phase6_temp'
```

**診断**:

```bash
# インポート階層を確認
python -c "
import sys
sys.path.insert(0, 'python_scripts')
import test_phase6_temp
print('OK')
"
```

**解決方法**:

**方法A: __init__.py を使用**
```bash
# python_scripts/ に __init__.py を作成
touch python_scripts/__init__.py
```

**方法B: sys.pathを設定**
```python
import sys
from pathlib import Path

# スクリプトのディレクトリをsys.pathに追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from test_phase6_temp import AdvancedJobSeekerAnalyzer
```

**方法C: パッケージとしてインストール**
```bash
# setup.py を作成
cat > setup.py << EOF
from setuptools import setup, find_packages

setup(
    name='job_medley_analysis',
    version='1.0',
    packages=find_packages(),
)
EOF

# インストール
pip install -e .
```

---

## GAS側の問題

### G1: メニューが表示されない

**症状**:
- Googleスプレッドシートを開いてもカスタムメニュー「📊 データ処理」が表示されない

**診断**:

1. **Apps Scriptエディタを開く**
   - `拡張機能` → `Apps Script`

2. **onOpen()関数が存在するか確認**
   ```javascript
   // MenuIntegration.gs または Phase7CompleteMenuIntegration.gs
   function onOpen() {
     // ...
   }
   ```

**解決方法**:

**方法A: Spreadsheetをリロード**
```
F5キーでリロード
```

**方法B: onOpen()を手動実行**
1. Apps Scriptエディタを開く
2. `Phase7CompleteMenuIntegration.gs` を選択
3. 関数ドロップダウンから `onOpen_Phase7Complete` を選択
4. 「実行」ボタンをクリック
5. 権限の承認を求められたら承認
6. Spreadsheetに戻る（F5でリロード）

**方法C: トリガーを設定**
1. Apps Scriptエディタで「トリガー」アイコン（時計マーク）をクリック
2. 「トリガーを追加」をクリック
3. 設定:
   - 実行する関数: `onOpen_Phase7Complete`
   - イベントのソース: `スプレッドシートから`
   - イベントの種類: `起動時`
4. 「保存」をクリック

---

### G2: HTMLファイルが見つかりません

**症状**:
```
エラー: Phase7Upload.htmlが見つかりません
```

**診断**:

1. **Apps Scriptエディタでファイル一覧を確認**
   - 左サイドバーに `Phase7Upload.html` が存在するか

**解決方法**:

**ステップ1: HTMLファイルを追加**
1. Apps Scriptエディタを開く
2. 左サイドバーの「+」ボタンをクリック
3. 「HTML」を選択
4. ファイル名: `Phase7Upload`（拡張子なし）
5. 内容をペースト（gas_files/html/Phase7Upload.html）

**ステップ2: 保存**
```
Ctrl+S で保存
```

**ステップ3: Spreadsheetをリロード**
```
F5でリロード
```

---

### G3: シートが見つかりません

**症状**:
```javascript
Exception: シートが見つかりません: SupplyDensityMap
```

**診断**:

```javascript
// GASエディタで実行
function checkSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();

  Logger.log('=== シート一覧 ===');
  sheets.forEach(sheet => {
    Logger.log(sheet.getName());
  });
}
```

**解決方法**:

**方法A: Phase 7を再インポート**
1. メニュー: `📈 Phase 7高度分析` → `📥 データインポート` → `📤 HTMLアップロード（最も簡単）`
2. 5つのCSVファイルをアップロード

**方法B: シート名を確認**
- シート名が正確に `SupplyDensityMap` か確認（大文字小文字区別）
- スペースや全角文字が含まれていないか確認

**方法C: 手動でシート作成**
1. Spreadsheet下部の「+」ボタンをクリック
2. シート名を `SupplyDensityMap` に変更
3. CSVデータを手動でペースト

---

### G4: データが表示されない（グラフが空）

**症状**:
- ダイアログは開くが、グラフが真っ白
- チャートエリアに何も表示されない

**診断**:

1. **ブラウザのデベロッパーツールを開く**
   ```
   F12キー → Consoleタブ
   ```

2. **エラーメッセージを確認**
   - Google Chartsのロードエラー
   - データ形式エラー
   - スクリプトエラー

**解決方法**:

**方法A: ブラウザをリロード**
```
F5でリロード
Ctrl+Shift+R（スーパーリロード）
```

**方法B: ポップアップブロックを無効化**
1. ブラウザのアドレスバー右側のアイコンをクリック
2. 「ポップアップとリダイレクトを常に許可する」を選択
3. ページをリロード

**方法C: Google Chartsライブラリの確認**
```javascript
// HTMLファイル内で確認
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

<script type="text/javascript">
  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawChart);
</script>
```

**方法D: データ形式の確認**
```javascript
// GASエディタで実行
function checkDataFormat() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('SupplyDensityMap');
  const data = sheet.getDataRange().getValues();

  Logger.log('=== データサンプル ===');
  Logger.log(data.slice(0, 5));  // 最初の5行
}
```

---

### G5: 実行時間の制限を超えました

**症状**:
```
Exception: Exceeded maximum execution time
```

**診断**:

```javascript
// 処理時間を測定
function measureExecutionTime() {
  const startTime = new Date().getTime();

  // 処理を実行
  importPhase7Data();

  const endTime = new Date().getTime();
  const elapsedTime = (endTime - startTime) / 1000;

  Logger.log(`処理時間: ${elapsedTime}秒`);
}
```

**GASの実行時間制限**:
- 無料アカウント: 6分
- Google Workspace: 30分

**解決方法**:

**方法A: データを分割してインポート**
```javascript
function importPhase7DataInBatches() {
  const files = [
    'SupplyDensityMap.csv',
    'AgeGenderCrossAnalysis.csv',
    'MobilityScore.csv',
    'DetailedPersonaProfile.csv'
  ];

  // 1ファイルずつインポート
  files.forEach(file => {
    importSingleFile(file);
    Utilities.sleep(1000);  // 1秒待機
  });
}
```

**方法B: バッチ処理を使用**
```javascript
function importLargeFile() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('MobilityScore');
  const data = getCsvData();  // CSVデータ取得

  // 1000行ずつバッチ処理
  const batchSize = 1000;
  for (let i = 0; i < data.length; i += batchSize) {
    const batch = data.slice(i, i + batchSize);
    sheet.getRange(i + 2, 1, batch.length, batch[0].length).setValues(batch);

    // 長時間処理の場合は一時停止
    if (i % 5000 === 0) {
      Utilities.sleep(2000);
    }
  }
}
```

**方法C: Apps Script APIのクォータを確認**
1. Apps Scriptエディタで「プロジェクトの設定」をクリック
2. 「割り当て」セクションを確認
3. 上限に達している場合は24時間待つ

---

### G6: 権限エラー（Authorization required）

**症状**:
```
Authorization required to perform that action
```

**診断**:

1. **現在の権限を確認**
   - Apps Scriptエディタで「実行」ボタンをクリック
   - 権限の承認を求められるか確認

**解決方法**:

**ステップ1: スクリプトを承認**
1. Apps Scriptエディタで関数を選択
2. 「実行」ボタンをクリック
3. 「権限を確認」ダイアログが表示される
4. 「権限を確認」をクリック
5. Googleアカウントを選択
6. 「詳細」→「（プロジェクト名）に移動」をクリック
7. 「許可」をクリック

**ステップ2: OAuth同意画面の設定**
1. GCPコンソールを開く
2. 「OAuth同意画面」を選択
3. 必要な情報を入力
4. スコープを追加

**ステップ3: Apps Scriptのマニフェストを確認**
```json
// appsscript.json
{
  "timeZone": "Asia/Tokyo",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
  ]
}
```

---

### G7: データ型エラー（型の不一致）

**症状**:
```javascript
TypeError: Cannot read property 'length' of undefined
```

**診断**:

```javascript
// データ型を確認
function checkDataTypes() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('SupplyDensityMap');
  const data = sheet.getDataRange().getValues();

  // 各列のデータ型を確認
  Logger.log('=== データ型チェック ===');
  data[1].forEach((cell, index) => {
    Logger.log(`列${index}: ${typeof cell} (値: ${cell})`);
  });
}
```

**解決方法**:

**方法A: データ型変換**
```javascript
// 数値に変換
const value = parseFloat(cell);
if (isNaN(value)) {
  Logger.log(`数値変換エラー: ${cell}`);
  return 0;  // デフォルト値
}

// 文字列に変換
const stringValue = String(cell).trim();
```

**方法B: null/undefined チェック**
```javascript
// データ存在チェック
if (data && data.length > 0) {
  // データ処理
} else {
  Logger.log('データが存在しません');
  return;
}

// セル値チェック
const cellValue = cell !== null && cell !== undefined ? cell : '';
```

**方法C: try-catchで例外処理**
```javascript
try {
  const result = processData(data);
} catch (error) {
  Logger.log(`エラー: ${error.message}`);
  Logger.log(`スタックトレース: ${error.stack}`);

  // フォールバック処理
  return defaultValue;
}
```

---

### G8: スクリプトエディタで保存できない

**症状**:
- Ctrl+S を押しても保存されない
- 「保存中...」のまま進まない

**診断**:

1. **ブラウザのコンソールを確認**
   ```
   F12 → Consoleタブ
   ```

2. **ネットワークエラーを確認**
   ```
   F12 → Networkタブ
   ```

**解決方法**:

**方法A: 別のブラウザを使用**
- Google Chrome推奨
- FirefoxまたはEdgeも可

**方法B: ブラウザキャッシュをクリア**
```
Ctrl+Shift+Delete → キャッシュをクリア
```

**方法C: シークレットモードで開く**
```
Ctrl+Shift+N（Chrome）
```

**方法D: 拡張機能を無効化**
- 広告ブロッカーやプライバシー拡張を一時的に無効化

---

## データ品質の問題

### D1: データ検証スコアが100点未満

**症状**:
```
データ検証スコア: 78/100点
```

**診断**:

```javascript
// GASで実行
function runDataValidation() {
  const result = validateAllData();
  Logger.log(JSON.stringify(result, null, 2));
}
```

**解決方法（検証項目別）**:

#### **1. 必須シート存在確認（配点: 20点）**

**失敗例**:
```
⚠️ 不足シート: SupplyDensityMap, AgeGenderCrossAnalysis
```

**対処方法**:
```
1. Python側で run_complete.py を実行
2. GASで Phase 7をHTMLアップロード
```

#### **2. 空シート検出（配点: 15点）**

**失敗例**:
```
⚠️ 空シート: ChiSquareTests（5バイトのみ）
```

**対処方法**:
```
1. 最適化版を確認（test_phase6_temp.py）
2. Python側で run_complete.py を再実行
3. Phase 2の処理時間が7秒程度であることを確認
```

#### **3. 必須列存在確認（配点: 15点）**

**失敗例**:
```
⚠️ MapMetrics: 列不足（lat, lngが存在しない）
```

**対処方法**:
```
1. geocache.jsonを確認（1,901件のキャッシュがあるか）
2. Python側でジオコーディングを再実行
3. MapMetrics.csvに lat, lng 列があることを確認
```

#### **4. 数値型検証（配点: 15点）**

**失敗例**:
```
⚠️ MapMetrics.総希望件数: 数値型でない（文字列型）
```

**対処方法**:
```javascript
// GASで型変換
function convertToNumber() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('MapMetrics');
  const range = sheet.getRange('C2:C');  // 総希望件数列
  const values = range.getValues();

  const converted = values.map(row => [parseFloat(row[0]) || 0]);
  range.setValues(converted);
}
```

#### **5. 座標データ検証（配点: 15点）**

**失敗例**:
```
⚠️ MapMetrics: 座標範囲外（lat=999, lng=999）
```

**対処方法**:
```
1. geocache.json の内容を確認
2. 無効な座標を削除
3. ジオコーディングを再実行
```

#### **6. 重複データ検出（配点: 10点）**

**失敗例**:
```
⚠️ Applicants: 重複率8.5%（許容範囲5%超）
```

**対処方法**:
```python
# Python側で重複削除
df = df.drop_duplicates(subset=['applicant_id'], keep='first')
```

#### **7. データ整合性チェック（配点: 10点）**

**失敗例**:
```
⚠️ PersonaDetails: 外部キー不整合（applicant_id=9999が存在しない）
```

**対処方法**:
```python
# Python側で外部キー整合性を確認
persona_details = persona_details[
    persona_details['applicant_id'].isin(df['applicant_id'])
]
```

---

### D2: 座標データが取得できない

**症状**:
```
lat: None, lng: None
または
lat: 999, lng: 999（ダミー座標）
```

**診断**:

```python
# geocache.jsonを確認
import json

with open('data/output/geocache.json', 'r', encoding='utf-8') as f:
    geocache = json.load(f)

print(f"キャッシュ件数: {len(geocache)}")
print(f"サンプル: {list(geocache.items())[:5]}")
```

**解決方法**:

**方法A: Google Maps APIキーを確認**
```python
# test_phase6_temp.py 内でAPIキーを確認
GOOGLE_MAPS_API_KEY = 'YOUR_API_KEY'

# APIキーが有効か確認
import requests
url = f'https://maps.googleapis.com/maps/api/geocode/json?address=東京都&key={GOOGLE_MAPS_API_KEY}'
response = requests.get(url)
print(response.json())
```

**方法B: geocache.jsonを再構築**
```bash
# 既存のキャッシュを削除
rm data/output/geocache.json

# 再実行（ジオコーディングが再実行される）
python run_complete.py
```

**方法C: 手動でジオコーディング**
```python
import googlemaps

gmaps = googlemaps.Client(key='YOUR_API_KEY')

def get_coords_manual(prefecture, municipality=None):
    address = prefecture
    if municipality:
        address = f"{prefecture}{municipality}"

    try:
        result = gmaps.geocode(address, language='ja')
        if result:
            location = result[0]['geometry']['location']
            return location['lat'], location['lng']
    except Exception as e:
        print(f"エラー: {e}")

    return None, None
```

---

### D3: Phase 7データの欠落（5ファイル中2ファイルのみ）

**症状**:
```bash
ls python_scripts/gas_output_phase7/
# 出力:
# - SupplyDensityMap.csv
# - MobilityScore.csv
# （3ファイル不足）
```

**診断**:

```bash
# Python実行時のエラーログを確認
python run_complete.py 2>&1 | grep "Phase 7"
```

**原因の可能性**:
1. 資格情報が元データに含まれていない → QualificationDistribution.csv未生成
2. 年齢情報が欠落 → AgeGenderCrossAnalysis.csv未生成
3. ペルソナクラスタリング失敗 → DetailedPersonaProfile.csv未生成

**解決方法**:

**ステップ1: 元データの内容を確認**
```python
import pandas as pd

df = pd.read_csv('data/input/統合_求職者情報宮城_介護.csv')

# 必須列の存在確認
required_cols = ['age', 'gender', 'qualification', 'desired_work_1_prefecture']
for col in required_cols:
    if col in df.columns:
        print(f'✅ {col}: 存在')
    else:
        print(f'❌ {col}: 不足')
```

**ステップ2: 欠損値の確認**
```python
print(df.isnull().sum())
```

**ステップ3: Phase 7コードをデバッグ**
```python
# phase7_advanced_analysis.py 内でデバッグ出力を追加
def qualification_distribution(self):
    print(f"[DEBUG] 資格情報: {self.df['qualification'].value_counts()}")

    if 'qualification' not in self.df.columns:
        print("[WARNING] 資格列が存在しないため、QualificationDistribution.csvをスキップ")
        return

    # 処理続行...
```

**ステップ4: 再実行**
```bash
python run_complete.py
```

---

### D4: 重複データが多い

**症状**:
```
重複データ検出: 8.5%（許容範囲5%超）
```

**診断**:

```python
# 重複データを確認
duplicates = df[df.duplicated(subset=['applicant_id'], keep=False)]
print(f"重複件数: {len(duplicates)}")
print(duplicates.head(10))
```

**解決方法**:

**方法A: 重複削除（最初のレコードを保持）**
```python
df = df.drop_duplicates(subset=['applicant_id'], keep='first')
```

**方法B: 重複削除（最新のレコードを保持）**
```python
# created_at列でソートしてから削除
df = df.sort_values('created_at', ascending=False)
df = df.drop_duplicates(subset=['applicant_id'], keep='first')
```

**方法C: 重複をマージ**
```python
# グループ化して統合
df_merged = df.groupby('applicant_id').agg({
    'age': 'first',
    'gender': 'first',
    'desired_work_1_prefecture': lambda x: ', '.join(x.unique())  # 複数を結合
}).reset_index()
```

---

## パフォーマンスの問題

### PF1: Python実行が遅い（120秒超）

**症状**:
```
処理時間: 125秒（タイムアウト）
```

**診断**:

```bash
# 詳細なタイミング測定
python test_run_timed.py
```

**ボトルネック特定**:
```python
import time

def measure_phase_time(func):
    start = time.time()
    func()
    elapsed = time.time() - start
    print(f"{func.__name__}: {elapsed:.2f}秒")

# 各フェーズの時間を測定
measure_phase_time(analyzer.export_phase1_data)
measure_phase_time(analyzer.export_phase2_data)
measure_phase_time(analyzer.export_phase3_data)
measure_phase_time(analyzer.export_phase6_data)
```

**解決方法（最適化版を適用）**:

既に[P4: タイムアウト](#p4-タイムアウト処理が120秒を超える)で説明した最適化版を適用してください。

**期待される改善**:
- Phase 6: 30秒超 → 39秒（ベクトル化+ユニークマッピング）
- Phase 2: タイムアウト → 7秒（実行順序変更）
- 合計: 120秒超 → 87秒（33秒余裕）

---

### PF2: GAS実行が遅い（HTMLアップロード）

**症状**:
```
HTMLアップロード: 5分以上かかる
```

**診断**:

```javascript
// 各ファイルのアップロード時間を測定
function measureUploadTime() {
  const files = ['SupplyDensityMap.csv', 'MobilityScore.csv'];

  files.forEach(file => {
    const startTime = new Date().getTime();

    // アップロード処理
    uploadFile(file);

    const elapsedTime = (new Date().getTime() - startTime) / 1000;
    Logger.log(`${file}: ${elapsedTime}秒`);
  });
}
```

**解決方法**:

**方法A: バッチ処理を使用**
```javascript
function uploadLargeFileInBatches(csvData, sheetName) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  const rows = Utilities.parseCsv(csvData);

  // 1000行ずつバッチ処理
  const batchSize = 1000;
  for (let i = 0; i < rows.length; i += batchSize) {
    const batch = rows.slice(i, i + batchSize);

    if (i === 0) {
      // ヘッダー行
      sheet.getRange(1, 1, 1, batch[0].length).setValues([batch[0]]);
    } else {
      // データ行
      sheet.getRange(i + 1, 1, batch.length, batch[0].length).setValues(batch);
    }

    // スクリプト実行時間を分散
    if (i % 5000 === 0 && i > 0) {
      Utilities.sleep(1000);
    }
  }
}
```

**方法B: appendRowの代わりにsetValues使用**
```javascript
// 遅い（行ごとに処理）
data.forEach(row => {
  sheet.appendRow(row);  // 6,411回のAPI呼び出し
});

// 速い（一括処理）
sheet.getRange(2, 1, data.length, data[0].length).setValues(data);  // 1回のAPI呼び出し
```

**方法C: Google Drive APIを使用**
```javascript
function uploadViaGoogleDrive(csvData, sheetName) {
  // CSVファイルとしてDriveに保存
  const file = DriveApp.createFile(sheetName + '.csv', csvData, MimeType.CSV);

  // Spreadsheetにインポート
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const importRange = spreadsheet.getRange('A1');
  importRange.setFormula(`=IMPORTDATA("${file.getUrl()}")`);

  // 値に変換
  SpreadsheetApp.flush();
  importRange.copyTo(importRange, {contentsOnly: true});

  // 一時ファイル削除
  file.setTrashed(true);
}
```

---

### PF3: メモリ使用量が多い

**症状**:
```python
MemoryError: Unable to allocate 512 MB for an array
```

**診断**:

```python
import psutil
import numpy as np

# 現在のメモリ使用量
process = psutil.Process()
memory_info = process.memory_info()
print(f"メモリ使用量: {memory_info.rss / 1024**2:.2f} MB")

# データフレームのメモリ使用量
print(df.memory_usage(deep=True).sum() / 1024**2)
```

**解決方法（最適化版で改善済み）**:

**改善内容**:
```
変数メモリ使用量:
- 最適化前: 1,094 KB
- 最適化後: 198 KB
- 削減率: 81.9%
```

**追加の最適化**:

**方法A: データ型の最適化**
```python
# int64 → int8/int16
df['age'] = df['age'].astype('int8')  # 0-255

# float64 → float32
df['lat'] = df['lat'].astype('float32')

# object → category
df['prefecture'] = df['prefecture'].astype('category')
```

**方法B: 不要なデータの削除**
```python
# 処理後に不要な列を削除
df = df.drop(['temp_column', 'intermediate_result'], axis=1)

# ガベージコレクション
import gc
gc.collect()
```

**方法C: チャンク処理**
```python
# 大きなファイルをチャンクで処理
chunk_size = 10000
for chunk in pd.read_csv(filepath, chunksize=chunk_size):
    process_chunk(chunk)
    # 処理後にメモリ解放
    del chunk
    gc.collect()
```

---

## 統合の問題

### I1: Python→GASデータ連携エラー

**症状**:
- Pythonで生成したCSVファイルをGASで読み込めない

**診断**:

**ステップ1: ファイルエンコーディングを確認**
```bash
file -i data/output/phase1/MapMetrics.csv
# 期待: text/csv; charset=utf-8
```

**ステップ2: BOM付きUTF-8か確認**
```bash
xxd data/output/phase1/MapMetrics.csv | head -1
# 期待: EF BB BF（UTF-8 BOM）
```

**ステップ3: 改行コードを確認**
```bash
file data/output/phase1/MapMetrics.csv
# 期待: CRLF（Windows）または LF（Unix）
```

**解決方法**:

**方法A: Python側でエンコーディングを統一**
```python
# UTF-8 BOM付きで保存
df.to_csv('output.csv', index=False, encoding='utf-8-sig')
```

**方法B: GAS側で自動検出**
```javascript
function readCsvWithEncoding(csvData) {
  // UTF-8 BOMをチェック
  if (csvData.charCodeAt(0) === 0xFEFF) {
    csvData = csvData.substring(1);  // BOMを削除
  }

  const rows = Utilities.parseCsv(csvData);
  return rows;
}
```

**方法C: 改行コードを統一**
```python
# Windowsスタイル（CRLF）で保存
df.to_csv('output.csv', index=False, line_terminator='\r\n')
```

---

### I2: ファイルパスの不一致

**症状**:
```python
FileNotFoundError: data/output/phase1/MapMetrics.csv
```

**診断**:

```python
from pathlib import Path

# 相対パスと絶対パスを確認
relative_path = Path('data/output/phase1/MapMetrics.csv')
absolute_path = relative_path.resolve()

print(f"相対パス: {relative_path}")
print(f"絶対パス: {absolute_path}")
print(f"存在: {absolute_path.exists()}")
```

**解決方法**:

**方法A: プロジェクトルートを基準にする**
```python
from pathlib import Path

# スクリプトの親ディレクトリをプロジェクトルートとする
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'output'

# ファイルパスを構築
filepath = DATA_DIR / 'phase1' / 'MapMetrics.csv'
```

**方法B: 環境変数を使用**
```bash
# 環境変数を設定
export PROJECT_ROOT="C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project"
```

```python
import os

PROJECT_ROOT = os.environ.get('PROJECT_ROOT', '.')
filepath = os.path.join(PROJECT_ROOT, 'data', 'output', 'phase1', 'MapMetrics.csv')
```

**方法C: 設定ファイルを使用**
```python
# config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data' / 'output'
```

```python
# run_complete.py
from config import DATA_DIR

filepath = DATA_DIR / 'phase1' / 'MapMetrics.csv'
```

---

### I3: テスト成功率が100%にならない

**症状**:
```
総合成功率: 78.26% (18/23テスト)
Phase 2成功率: 16.7% (1/6テスト)
Phase 6成功率: 0% (0/4テスト)
```

**診断**:

```bash
# テスト結果JSONを確認
cat TEST_RESULTS_COMPREHENSIVE.json | python -m json.tool
```

**失敗テストの内訳**:
```json
{
  "phase2_tests": [
    {"name": "ChiSquareTests.csv生成", "status": "FAIL", "reason": "ファイルサイズ5バイト（BOMのみ）"},
    {"name": "ANOVATests.csv生成", "status": "FAIL", "reason": "ファイルサイズ5バイト（BOMのみ）"}
  ],
  "phase6_tests": [
    {"name": "MunicipalityFlowEdges.csv生成", "status": "FAIL", "reason": "ファイルなし"},
    {"name": "MunicipalityFlowNodes.csv生成", "status": "FAIL", "reason": "ファイルなし"}
  ]
}
```

**解決方法（最適化版で修正済み）**:

既に[P4: タイムアウト](#p4-タイムアウト処理が120秒を超える)、[P6: Phase 2データが空](#p6-phase-2データが空bom-5バイトのみ)、[P7: Phase 6データが生成されない](#p7-phase-6データが生成されない)で説明した最適化版を適用してください。

**期待される結果**:
```
総合成功率: 100% (23/23テスト)
Phase 2成功率: 100% (6/6テスト)
Phase 6成功率: 100% (4/4テスト)
```

---

## クイックリファレンス

### よくあるエラーメッセージと対処法

| エラーメッセージ | 原因 | 対処法 | 参照 |
|----------------|------|--------|------|
| `FileNotFoundError` | ファイルパス間違い | 絶対パス使用、パス確認 | [P1](#p1-ファイルが見つかりませんfilenotfounderror) |
| `ModuleNotFoundError` | パッケージ未インストール | `pip install` 実行 | [P2](#p2-モジュールが見つかりませんmodulenotfounderror) |
| `MemoryError` | メモリ不足 | チャンク処理、データ型最適化 | [P3](#p3-メモリ不足エラーmemoryerror) |
| 処理時間120秒超 | タイムアウト | 最適化版適用 | [P4](#p4-タイムアウト処理が120秒を超える) |
| `UnicodeEncodeError` | エンコーディング不一致 | UTF-8指定、絵文字回避 | [P5](#p5-unicode-エンコーディングエラー) |
| BOM 5バイトのみ | Phase 2未実行 | 最適化版適用、実行順序確認 | [P6](#p6-phase-2データが空bom-5バイトのみ) |
| Phase 6ファイルなし | Phase 6未実行 | ベクトル化実装確認 | [P7](#p7-phase-6データが生成されない) |
| `ImportError` | 循環インポート | `__init__.py`追加、sys.path設定 | [P8](#p8-importerror循環インポート) |
| メニュー表示されない | onOpen未実行 | F5リロード、手動実行 | [G1](#g1-メニューが表示されない) |
| HTMLファイルなし | HTML未追加 | HTMLファイル追加 | [G2](#g2-htmlファイルが見つかりません) |
| シートなし | Phase 7未インポート | HTMLアップロード実行 | [G3](#g3-シートが見つかりません) |
| グラフ表示されない | Google Charts未ロード | F5リロード、ポップアップ許可 | [G4](#g4-データが表示されないグラフが空) |
| 実行時間制限 | 6分超過 | バッチ処理、データ分割 | [G5](#g5-実行時間の制限を超えました) |
| 権限エラー | OAuth未承認 | スクリプト承認、権限確認 | [G6](#g6-権限エラーauthorization-required) |
| データ型エラー | null/undefined | null チェック、型変換 | [G7](#g7-データ型エラー型の不一致) |
| 保存できない | ブラウザ問題 | 別ブラウザ、キャッシュクリア | [G8](#g8-スクリプトエディタで保存できない) |
| 検証スコア<100 | データ不完全 | 検証レポート確認、再実行 | [D1](#d1-データ検証スコアが100点未満) |
| 座標取得失敗 | APIキー無効 | APIキー確認、geocache再構築 | [D2](#d2-座標データが取得できない) |
| Phase 7ファイル不足 | 元データ欠落 | 必須列確認、デバッグ出力 | [D3](#d3-phase-7データの欠落5ファイル中2ファイルのみ) |
| 重複データ多い | 重複率>5% | 重複削除、マージ | [D4](#d4-重複データが多い) |

---

### チェックリスト

#### **Python実行前チェック**
- [ ] 元CSVファイルが存在する
- [ ] 必要なパッケージがインストール済み（pandas, numpy等）
- [ ] geocache.jsonが存在する（1,901件）
- [ ] 最適化版が適用されている（test_phase6_temp.py確認）
- [ ] 実行順序がPhase 7 → Phase 6になっている（run_complete.py確認）

#### **GASインポート前チェック**
- [ ] Pythonで全フェーズが完了している
- [ ] Phase 1-6のCSVファイルが生成されている（11ファイル）
- [ ] Phase 7のCSVファイルが生成されている（4-5ファイル）
- [ ] GASスクリプトが追加されている（.gsファイル）
- [ ] HTMLファイルが追加されている（.htmlファイル）
- [ ] onOpen()関数が実行されている（メニュー表示確認）

#### **データ検証チェック**
- [ ] 必須シート11枚が存在する
- [ ] すべてのシートにデータがある（空シートなし）
- [ ] 必須列がすべて存在する
- [ ] 数値列が数値型である
- [ ] 座標データが有効範囲内（lat: 20-50, lng: 120-150）
- [ ] 重複データが5%未満
- [ ] 外部キー整合性がある

#### **パフォーマンスチェック**
- [ ] Python処理時間が87秒程度（120秒未満）
- [ ] Phase 2が7秒程度で完了
- [ ] Phase 6が39秒程度で完了
- [ ] タイムアウト余裕が33秒以上
- [ ] テスト成功率が100%

---

### 緊急対応フロー

**Python実行エラー**:
```
1. エラーメッセージを確認
2. クイックリファレンスでエラーメッセージを検索
3. 対処法を実行
4. 再実行
5. 解決しない場合はログを保存して調査
```

**GASエラー**:
```
1. F12でブラウザコンソールを開く
2. エラーメッセージを確認
3. クイックリファレンスでエラーメッセージを検索
4. 対処法を実行
5. F5でリロード
6. 解決しない場合はスクリーンショットを保存
```

**データ品質問題**:
```
1. データ検証レポートを実行
2. 失敗項目を確認
3. D1の検証項目別対処法を実行
4. 再検証
5. スコアが100点になるまで繰り返し
```

**パフォーマンス問題**:
```
1. test_run_timed.py を実行
2. ボトルネックフェーズを特定
3. 最適化版が適用されているか確認
4. 未適用の場合は適用
5. 再実行して処理時間を確認
```

---

## まとめ

このトラブルシューティングガイドでは、Phase 1-7の最適化実装済みシステムで発生する可能性のある問題を、症状→診断→解決のMECE構造で網羅的に説明しました。

### 重要なポイント

1. **問題の切り分け**: 診断フローチャートで問題箇所を特定
2. **クイックリファレンス**: エラーメッセージから素早く対処法を検索
3. **チェックリスト**: 実行前に必要な条件を確認
4. **緊急対応フロー**: 問題発生時の標準的な対応手順

### 追加リソース

- [最適化実装ガイド](OPTIMIZATION_IMPLEMENTATION_GUIDE.md) - 最適化の詳細
- [GAS実装完全ガイド](GAS_IMPLEMENTATION_COMPLETE_GUIDE.md) - GAS実装手順
- [最適化レビューレポート](../gas_test/OPTIMIZATION_REVIEW_REPORT.md) - 品質保証
- [実測改善結果](../gas_test/ACTUAL_IMPROVEMENT_RESULTS.md) - パフォーマンス結果

**作成者**: Claude Code
**プロジェクト**: ジョブメドレー求職者データ分析
**バージョン**: 1.0（最適化版対応）
**ステータス**: 本番運用可能 ✅
