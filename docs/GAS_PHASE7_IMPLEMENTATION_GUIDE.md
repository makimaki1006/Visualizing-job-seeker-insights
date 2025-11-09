# GAS Phase 7 実装・導入ガイド

## 📋 目次

1. [実装概要](#実装概要)
2. [ファイル構成](#ファイル構成)
3. [GASプロジェクトへの追加手順](#gasプロジェクトへの追加手順)
4. [使用方法](#使用方法)
5. [トラブルシューティング](#トラブルシューティング)
6. [今後の拡張](#今後の拡張)

---

## 実装概要

### ✅ 完成した機能

| 機能 | ファイル | 状態 |
|------|---------|------|
| データインポート | Phase7DataImporter.gs | ✅ 完成 |
| 人材供給密度マップ | Phase7SupplyDensityViz.gs | ✅ 完成 |
| 移動許容度分析 | Phase7MobilityScoreViz.gs | ✅ 完成 |
| メニュー統合 | Phase7MenuIntegration.gs | ✅ 完成 |

### 🚧 今後実装予定の機能

| 機能 | 優先度 | 実装予定時期 |
|------|--------|------------|
| 資格別人材分布 | 中 | Phase 2 |
| 年齢層×性別クロス分析 | 中 | Phase 2 |
| ペルソナ詳細プロファイル | 高 | Phase 2 |
| 統合ダッシュボード | 低 | Phase 3 |

---

## ファイル構成

### Python側（既に完成）

```
job_medley_project/
├── python_scripts/
│   ├── run_complete.py                # メイン実行スクリプト
│   ├── phase7_advanced_analysis.py    # Phase 7分析エンジン
│   ├── test_phase7.py                 # ユニット・統合テスト
│   └── test_phase7_e2e.py             # E2Eテスト
└── docs/
    ├── PHASE7_TEST_REPORT.md          # テスト結果レポート
    └── GAS_PHASE7_VISUALIZATION_SPEC.md  # 可視化仕様書
```

### GAS側（新規作成）

```
gas_files/
└── scripts/
    ├── Phase7DataImporter.gs          # ✅ データインポート機能
    ├── Phase7SupplyDensityViz.gs      # ✅ 人材供給密度マップ
    ├── Phase7MobilityScoreViz.gs      # ✅ 移動許容度分析
    └── Phase7MenuIntegration.gs       # ✅ メニュー統合
```

---

## GASプロジェクトへの追加手順

### ステップ1: GASプロジェクトを開く

1. Google スプレッドシートを開く
2. メニュー: **拡張機能 > Apps Script**

### ステップ2: スクリプトファイルを追加

#### 2-1. Phase7DataImporter.gs

1. 左サイドバーの「+」をクリック → 「スクリプト」を選択
2. ファイル名: `Phase7DataImporter`
3. 内容: `gas_files/scripts/Phase7DataImporter.gs` の内容をコピー&ペースト
4. **保存**（Ctrl+S）

#### 2-2. Phase7SupplyDensityViz.gs

1. 同様に新規スクリプト作成
2. ファイル名: `Phase7SupplyDensityViz`
3. 内容: `gas_files/scripts/Phase7SupplyDensityViz.gs` の内容をコピー&ペースト
4. **保存**

#### 2-3. Phase7MobilityScoreViz.gs

1. 新規スクリプト作成
2. ファイル名: `Phase7MobilityScoreViz`
3. 内容: `gas_files/scripts/Phase7MobilityScoreViz.gs` の内容をコピー&ペースト
4. **保存**

#### 2-4. Phase7MenuIntegration.gs

1. 新規スクリプト作成
2. ファイル名: `Phase7MenuIntegration`
3. 内容: `gas_files/scripts/Phase7MenuIntegration.gs` の内容をコピー&ペースト
4. **保存**

### ステップ3: 既存MenuIntegration.gsにPhase 7メニューを追加

既存の `MenuIntegration.gs` の `onOpen()` 関数に以下を追加:

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  let menu = ui.createMenu('📊 データ処理');

  // ━━━ 既存のメニュー項目（変更なし） ━━━
  menu.addItem('⚡ 高速CSVインポート（推奨）', 'showEnhancedUploadDialog');
  // ... 他の既存メニュー項目 ...

  // ━━━ Phase 7メニュー追加（NEW） ━━━
  const phase7Menu = ui.createMenu('📈 Phase 7高度分析')
    .addItem('📥 Phase 7データ取り込み', 'importPhase7Data')
    .addSeparator()
    .addItem('🗺️ 人材供給密度マップ', 'showSupplyDensityMap')
    .addItem('🚗 移動許容度分析', 'showMobilityScoreAnalysis')
    .addSeparator()
    .addItem('✅ データ検証', 'validatePhase7Data')
    .addItem('📊 データサマリー', 'showPhase7DataSummary')
    .addSeparator()
    .addItem('📤 ランク別内訳エクスポート', 'exportRankBreakdownToSheet');

  menu.addSubMenu(phase7Menu);
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  menu.addToUi();
}
```

### ステップ4: スプレッドシートをリロード

1. スプレッドシートのタブに戻る
2. **ページをリロード**（F5）
3. メニューバーに「📊 データ処理」が表示されることを確認
4. サブメニューに「📈 Phase 7高度分析」が表示されることを確認

---

## 使用方法

### フェーズ1: Pythonでデータ生成

#### 1-1. Python実行

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\python_scripts"
python run_complete.py
```

#### 1-2. CSVファイル選択

- GUIダイアログが表示される
- 分析対象のCSVファイルを選択

#### 1-3. 出力確認

Phase 7出力フォルダ確認:
```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\gas_output_phase7\
├── SupplyDensityMap.csv           # 人材供給密度マップ
├── QualificationDistribution.csv  # 資格別人材分布
├── AgeGenderCrossAnalysis.csv     # 年齢層×性別クロス分析
├── MobilityScore.csv              # 移動許容度スコアリング
└── DetailedPersonaProfile.csv     # ペルソナ詳細プロファイル
```

---

### フェーズ2: GASにデータインポート

#### 重要な注意事項

**現在の実装では、`Phase7DataImporter.gs` の `importPhase7File()` 関数にファイルパスを設定する必要があります。**

#### オプション1: Google Driveを使用（推奨）

1. Phase 7のCSVファイルをGoogle Driveにアップロード
2. `Phase7DataImporter.gs` の `importPhase7File()` 関数を以下のように修正:

```javascript
function importPhase7File(fileName, sheetName) {
  // Google DriveからファイルID取得
  const fileId = getFileIdByName(fileName);

  if (!fileId) {
    throw new Error(`${fileName}がGoogle Driveに見つかりません`);
  }

  // CSVファイル読み込み
  const file = DriveApp.getFileById(fileId);
  const csvContent = file.getBlob().getDataAsString('UTF-8');

  // CSV解析
  const data = Utilities.parseCsv(csvContent);

  // シートにインポート
  return importCSVDataToSheet(data, sheetName);
}

function getFileIdByName(fileName) {
  const files = DriveApp.getFilesByName(fileName);
  if (files.hasNext()) {
    return files.next().getId();
  }
  return null;
}
```

#### オプション2: 手動コピー&ペースト

1. Phase 7のCSVファイルを開く
2. 全データをコピー（Ctrl+A → Ctrl+C）
3. Google スプレッドシートに新規シート作成
4. シート名を変更:
   - `Phase7_SupplyDensity`
   - `Phase7_QualificationDist`
   - `Phase7_AgeGenderCross`
   - `Phase7_MobilityScore`
   - `Phase7_PersonaProfile`
5. データをペースト（Ctrl+V）

---

### フェーズ3: 可視化機能を使用

#### 3-1. データ検証

メニュー: **📊 データ処理 > 📈 Phase 7高度分析 > ✅ データ検証**

- 5つのシートの存在確認
- 必須カラムの確認
- データ件数の確認

#### 3-2. 人材供給密度マップ

メニュー: **📊 データ処理 > 📈 Phase 7高度分析 > 🗺️ 人材供給密度マップ**

**表示内容:**
- ランク別統計カード（S/A/B/C/D）
- バブルチャート（求職者数×総合スコア）
- 地域別詳細データテーブル

**ビジネス活用:**
- 広告予算配分の意思決定
- 採用難易度の可視化
- 地域別戦略の立案

#### 3-3. 移動許容度分析

メニュー: **📊 データ処理 > 📈 Phase 7高度分析 > 🚗 移動許容度分析**

**表示内容:**
- レベル別統計カード（広域移動OK/中距離OK/近距離のみ/地元限定）
- スコア分布ヒストグラム
- レベル別円グラフ
- 希望地数×最大移動距離散布図
- 居住地別平均スコアTOP10

**ビジネス活用:**
- リモート勤務求人の提案
- 広域採用戦略の立案
- 通勤距離を考慮したマッチング

#### 3-4. データサマリー

メニュー: **📊 データ処理 > 📈 Phase 7高度分析 > 📊 データサマリー**

- 各シートのデータ行数確認
- カラム数確認

#### 3-5. ランク別内訳エクスポート

メニュー: **📊 データ処理 > 📈 Phase 7高度分析 > 📤 ランク別内訳エクスポート**

- 人材供給密度マップのランク別詳細を新規シート「Phase7_DensityRankBreakdown」に出力
- 営業提案資料の作成に活用

---

## トラブルシューティング

### エラー1: 「シートが見つかりません」

**原因**: Phase 7データがインポートされていない

**解決方法**:
1. メニュー: **📥 Phase 7データ取り込み** を実行
2. または手動でCSVデータをシートにコピー&ペースト

---

### エラー2: 「インポートするデータが空です」

**原因**: CSVファイルが空、またはファイルパスが間違っている

**解決方法**:
1. Pythonで `run_complete.py` を再実行
2. `gas_output_phase7/` フォルダにCSVファイルが生成されたことを確認
3. CSVファイルをテキストエディタで開き、データが存在することを確認

---

### エラー3: グラフが表示されない

**原因**: データ形式が不正、またはブラウザのJavaScriptエラー

**解決方法**:
1. メニュー: **✅ データ検証** を実行
2. ブラウザの開発者ツール（F12）でJavaScriptエラーを確認
3. ページをリロード（F5）

---

### エラー4: 「importPhase7File is not implemented」

**原因**: `Phase7DataImporter.gs` の `importPhase7File()` 関数が未実装

**解決方法**:
1. オプション1（推奨）: Google Driveを使用する実装を追加
2. オプション2: 手動でCSVをコピー&ペーストしてシート作成

---

## 今後の拡張

### Phase 2実装予定（優先度: 高）

#### 1. ペルソナ詳細プロファイル可視化

**ファイル**: `Phase7PersonaProfileViz.gs`

**機能**:
- レーダーチャート（ペルソナ別特性）
- 比較テーブル
- 構成比円グラフ
- 特徴カード表示

**実装工数**: 中（2-3時間）

#### 2. 年齢層×性別クロス分析可視化

**ファイル**: `Phase7AgeGenderCrossViz.gs`

**機能**:
- 積み上げ棒グラフ（地域別構成）
- ダイバーシティスコアヒートマップ
- 支配的セグメント円グラフ

**実装工数**: 中（2-3時間）

---

### Phase 3実装予定（優先度: 中）

#### 3. 資格別人材分布可視化

**ファイル**: `Phase7QualificationDistViz.gs`

**機能**:
- 横棒グラフ（資格カテゴリ別保有者数）
- 分布TOP3テーブル
- 希少地域アラート

**実装工数**: 小（1-2時間）

#### 4. 統合ダッシュボード

**ファイル**: `Phase7Dashboard.html`, `Phase7DashboardController.gs`

**機能**:
- タブ形式の統合ビュー
- KPI表示
- 全可視化を1画面で切り替え

**実装工数**: 大（4-6時間）

---

## パフォーマンス最適化

### データサンプリング

大量データ（>1000件）の場合、以下のサンプリング戦略を推奨:

```javascript
// 例: MobilityScore.csvが10,000件の場合
const maxRows = Math.min(lastRow - 1, 1000);  // 最大1000件
const range = sheet.getRange(2, 1, maxRows, 7);
```

### キャッシュ活用

頻繁にアクセスするデータはPropertiesServiceでキャッシュ:

```javascript
function getCachedSupplyDensityData() {
  const cache = PropertiesService.getScriptProperties();
  const cached = cache.getProperty('phase7_supply_density');

  if (cached) {
    return JSON.parse(cached);
  }

  const data = loadSupplyDensityData();
  cache.setProperty('phase7_supply_density', JSON.stringify(data));

  return data;
}
```

---

## セキュリティとプライバシー

### データ保護

- Phase 7データには個人情報（居住地、年齢等）が含まれる可能性があります
- Google スプレッドシートの共有設定を適切に管理してください
- 外部共有する場合は、個人を特定できる情報を削除してください

### アクセス制限

- GASプロジェクトの実行権限を限定してください
- 組織外への共有を制限してください

---

## まとめ

### ✅ 完成した機能

- Phase 7データインポート基盤
- 人材供給密度マップ可視化
- 移動許容度分析可視化
- メニュー統合

### 🚧 次のステップ

1. **Google Driveベースのインポート実装**（推奨）
2. **ペルソナ詳細プロファイル可視化**（Phase 2）
3. **年齢層×性別クロス分析可視化**（Phase 2）
4. **統合ダッシュボード**（Phase 3）

### 📞 サポート

実装に関する質問や問題が発生した場合は、以下のドキュメントを参照してください:

- `GAS_PHASE7_VISUALIZATION_SPEC.md` - 可視化仕様書
- `PHASE7_TEST_REPORT.md` - Phase 7テスト結果レポート
- `PHASE7_IMPLEMENTATION_COMPLETE.md` - Python側実装ドキュメント
