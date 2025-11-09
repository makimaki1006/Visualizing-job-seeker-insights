# GASファイル完全デプロイガイド

**作成日**: 2025年10月27日
**Phase 2実装完了版**

このガイドは、Phase 2実装完了時点での全GASファイルをGoogle Apps Scriptプロジェクトにデプロイする手順を示します。

---

## 📋 デプロイするGASファイル一覧

### 🔴 必須ファイル（新規追加 or 更新）

Phase 2で追加・更新されたファイル：

| # | ファイル名 | 操作 | 行数 | 説明 |
|---|-----------|------|------|------|
| 1 | **MenuIntegration.gs** | ✏️ 更新 | 204 | メインメニュー統合（Phase 2メニュー追加） |
| 2 | **MunicipalityFlowNetworkViz.gs** | ➕ 新規 | 687 | 自治体間フローネットワーク図（D3.js） |
| 3 | **CompleteIntegratedDashboard.gs** | ➕ 新規 | 1,141 | 完全統合ダッシュボード（Phase 1+6+7+Network） |

### 🟢 既存ファイル（変更なし）

以下のファイルは既にデプロイ済みで、変更不要です：

| # | ファイル名 | 説明 |
|---|-----------|------|
| 4 | DataValidationEnhanced.gs | データ検証機能 |
| 5 | PersonaDifficultyChecker.gs | ペルソナ難易度分析 |
| 6 | PythonCSVImporter.gs | CSVインポート機能 |
| 7 | Phase7SupplyDensityViz.gs | 人材供給密度マップ |
| 8 | Phase7MobilityScoreViz.gs | 移動許容度スコアリング |
| 9 | Phase7QualificationDistViz.gs | 資格別人材分布 |
| 10 | Phase7AgeGenderCrossViz.gs | 年齢層×性別クロス分析 |
| 11 | Phase7PersonaProfileViz.gs | ペルソナ詳細プロファイル |
| 12 | Phase7CompleteDashboard.gs | Phase 7統合ダッシュボード |
| 13 | Phase7DataImporter.gs | Phase 7データインポート |
| 14 | Phase7AutoImporter.gs | Phase 7自動インポート |
| 15 | GoogleMapsAPIConfig.gs | Google Maps API設定 |
| 16 | PersonaMapDataVisualization.gs | PersonaMapData地図可視化 |
| 17 | Phase7PersonaMobilityCrossViz.gs | PersonaMobilityCross可視化 |

### 📄 HTMLファイル（分離型・変更なし）

**重要**: 以下のHTMLファイルは`.html`ファイルとして独立しています。既にデプロイ済みの場合は変更不要です。

| # | ファイル名 | 説明 | 備考 |
|---|-----------|------|------|
| 18 | Upload_Enhanced.html | 高速CSVアップロードUI | 分離型HTML |
| 19 | PersonaDifficultyCheckerUI.html | ペルソナ難易度分析UI | 分離型HTML |
| 20 | Phase7Upload.html | Phase 7アップロードUI | 分離型HTML |

**注意**: 上記以外のMAP描写系（Google Maps、D3.js等）のHTMLは、各.gsファイル内に**埋め込まれています**（例: `PersonaMapDataVisualization.gs`、`MunicipalityFlowNetworkViz.gs`、`CompleteIntegratedDashboard.gs`等）。そのため、.gsファイルをコピペすれば自動的にHTMLもデプロイされます。

---

## 🚀 デプロイ手順

### ステップ1: Google Apps Scriptプロジェクトを開く

1. Googleスプレッドシートを開く
2. **拡張機能** > **Apps Script** をクリック
3. Apps Scriptエディタが開く

---

### ステップ2: 新規ファイルを追加（3ファイル）

#### **2-1. MunicipalityFlowNetworkViz.gs を追加**

1. Apps Scriptエディタで **+** ボタン > **スクリプト** をクリック
2. ファイル名を `MunicipalityFlowNetworkViz` に変更
3. 以下のファイルの内容を全てコピーして貼り付け:
   ```
   C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\MunicipalityFlowNetworkViz.gs
   ```

#### **2-2. CompleteIntegratedDashboard.gs を追加**

1. Apps Scriptエディタで **+** ボタン > **スクリプト** をクリック
2. ファイル名を `CompleteIntegratedDashboard` に変更
3. 以下のファイルの内容を全てコピーして貼り付け:
   ```
   C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\CompleteIntegratedDashboard.gs
   ```

---

### ステップ3: 既存ファイルを更新（1ファイル）

#### **3-1. MenuIntegration.gs を更新**

1. Apps Scriptエディタで既存の `MenuIntegration.gs` を開く
2. 既存の `onOpen` 関数を以下の **`onOpen_Phase7Complete`** 関数に置き換え:
   ```
   C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\Phase7CompleteMenuIntegration.gs
   ```

**重要**: `onOpen_Phase7Complete` を `onOpen` にリネームしてください

```javascript
// 変更前
function onOpen_Phase7Complete() {
  // ...
}

// 変更後
function onOpen() {
  // ...
}
```

---

### ステップ4: 保存とデプロイ

1. **ファイル** > **すべてを保存** をクリック
2. Googleスプレッドシートをリロード（F5）
3. メニューバーに **📊 データ処理** > **📈 Phase 7高度分析** が表示されることを確認

---

## ✅ デプロイ確認チェックリスト

### 必須ファイル確認

- [ ] `MunicipalityFlowNetworkViz.gs` (687行) が追加されている
- [ ] `CompleteIntegratedDashboard.gs` (1,141行) が追加されている
- [ ] `MenuIntegration.gs` が更新され、`onOpen()` 関数が正しく動作する

### メニュー表示確認

Googleスプレッドシートのメニューバーに以下が表示されるか確認：

- [ ] **📊 データ処理** メニューが表示される
- [ ] **📈 Phase 7高度分析** サブメニューが表示される
- [ ] **🎯 統合ダッシュボード** サブメニューに以下の2項目が表示される:
  - [ ] `📊 Phase 7統合ダッシュボード`
  - [ ] `🌐 完全統合ダッシュボード（Phase 1+6+7+Network）` ← **NEW**

---

## 📂 ファイルパス一覧

以下のパスからファイルをコピーしてください：

### 新規追加ファイル

```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\MunicipalityFlowNetworkViz.gs
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\CompleteIntegratedDashboard.gs
```

### 更新ファイル

```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\Phase7CompleteMenuIntegration.gs
```

**注意**: `Phase7CompleteMenuIntegration.gs` の内容を `MenuIntegration.gs` に上書きし、関数名を `onOpen()` に変更してください。

---

## 🚨 よくあるエラーと対処法

### エラー1: 「関数が見つかりません」

**症状**: メニューをクリックしても何も起こらない

**原因**: 関数名が間違っている、またはファイルが保存されていない

**対処**:
1. Apps Scriptエディタで **ファイル** > **すべてを保存**
2. 関数名のスペルミスを確認（大文字・小文字も区別される）
3. Googleスプレッドシートをリロード（F5）

### エラー2: 「メニューが表示されない」

**症状**: Googleスプレッドシートに「📊 データ処理」メニューが表示されない

**原因**: `onOpen()` 関数が正しく実行されていない

**対処**:
1. Apps Scriptエディタで `MenuIntegration.gs` を開く
2. 関数名が `onOpen()` になっているか確認（`onOpen_Phase7Complete()` ではない）
3. Googleスプレッドシートを**完全に閉じて**再度開く

### エラー3: 「完全統合ダッシュボードでデータが表示されない」

**症状**: ダッシュボードは開くが、グラフが空

**原因**: `CentralityRanking` シートが存在しない、または空

**対処**:
1. Googleスプレッドシートに `CentralityRanking` シートを作成
2. `gas_output_insights/CentralityRanking.csv` をインポート
3. 20行（ヘッダー + 20ハブ自治体）が表示されることを確認

---

## 📊 データインポート手順

Phase 2の新機能を使うには、以下のデータをインポートする必要があります：

### 必須データ

1. **CentralityRanking.csv**（ネットワーク中心性分析結果）
   - ソース: `C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_output_insights\CentralityRanking.csv`
   - インポート先: Googleスプレッドシートに `CentralityRanking` シートを作成してインポート

### インポート手順

1. Googleスプレッドシート下部の **+** をクリック
2. シート名を `CentralityRanking` に変更
3. **ファイル** > **インポート** をクリック
4. **アップロード** タブで `CentralityRanking.csv` を選択
5. **インポート場所**: `現在のシートを置換`
6. **区切り文字**: `自動検出`
7. **インポート** をクリック

### 確認

- シートに20行（ヘッダー + 20ハブ自治体）が表示される
- 列: `rank`, `municipality`, `composite_score`, `pagerank`, `betweenness_centrality`, etc.

---

## 🎯 動作確認手順

すべてのファイルをデプロイしたら、以下の手順で動作確認してください：

### 1. メニュー確認

Googleスプレッドシートを開き、以下のメニューが表示されるか確認：

```
📊 データ処理
  └── 📈 Phase 7高度分析
      ├── 📥 データインポート
      ├── 📊 個別分析
      ├── 🎯 統合ダッシュボード
      │   ├── 📊 Phase 7統合ダッシュボード
      │   └── 🌐 完全統合ダッシュボード（Phase 1+6+7+Network） ← NEW
      ├── 🔧 データ管理
      └── ❓ Phase 7クイックスタート
```

### 2. 完全統合ダッシュボード起動

1. メニュー: **📈 Phase 7高度分析** > **🎯 統合ダッシュボード** > **🌐 完全統合ダッシュボード（Phase 1+6+7+Network）**
2. ダッシュボードが開く（1700x1000pxモーダルダイアログ）

### 3. タブ確認

ダッシュボード内に以下の9つのタブが表示されることを確認：

- [ ] 📊 統合概要
- [ ] 📍 Phase 1: 基礎集計
- [ ] 🌊 Phase 6: フロー分析
- [ ] 🔗 **ネットワーク中心性** ← **NEW**
- [ ] 🗺️ Phase 7: 供給密度
- [ ] 🎓 Phase 7: 資格分布
- [ ] 👥 Phase 7: 年齢×性別
- [ ] 🚗 Phase 7: 移動許容度
- [ ] 📋 Phase 7: ペルソナ

### 4. ネットワーク中心性タブ確認

1. **🔗 ネットワーク中心性** タブをクリック
2. 以下が表示されることを確認：
   - 統計サマリー（ノード数、エッジ数、ハブ自治体数）
   - TOP 10ハブ自治体の棒グラフ
   - 中心性ランキングテーブル（TOP 20）
   - 1位: 京都府京都市伏見区（複合スコア: 0.2256）

---

## 📝 次のステップ

デプロイが完了したら、以下のアクションを実施してください：

1. **データ更新**: `python run_complete.py` を実行して最新データを生成
2. **CSVインポート**: `CentralityRanking.csv` をGoogleスプレッドシートにインポート
3. **動作確認**: 完全統合ダッシュボードでネットワーク中心性が表示されることを確認
4. **ステークホルダーレビュー**: ビジネス関係者にデモを実施

---

**デプロイ完了お疲れ様でした！🎉**

Phase 2実装により、Phase 1+6+7+Networkの全機能が統合され、包括的なデータ可視化プラットフォームが完成しました。
