# Google Apps Script 新規作成手順書

## 📋 概要

ジョブメドレー求職者データ分析システムのGASプロジェクトを**完全に新規作成**するための手順書です。

---

## 🗑️ ステップ0: 既存コードの削除

### Google Apps Scriptエディタを開く
1. スプレッドシートを開く
2. **拡張機能 > Apps Script** をクリック

### 既存ファイルをすべて削除
1. 左側のファイル一覧で、各ファイルを選択
2. 右クリック → **削除** をクリック
3. **すべての.gsファイルと.htmlファイルを削除**
4. **Code.gs は削除できないので、後で上書きします**

---

## 📂 ステップ1: 必要なファイル一覧

### ✅ 必須GASスクリプトファイル (.gs)

1. **MinimalMenuIntegration.gs** - メインメニュー（onOpen関数含む）
2. **UniversalPhaseUploader.gs** - Phase別データアップローダー
3. **MapDataProvider.gs** - MAP機能データプロバイダー
4. **Phase2Phase3Visualizations.gs** - Phase 2/3可視化関数
5. **GoogleMapsAPIConfig.gs** - Google Maps API設定（オプショナル対応版）

### ✅ 必須HTMLファイル (.html)

1. **MapComplete.html** - MAP機能UI（Leaflet.js + OpenStreetMap）
2. **PhaseUpload.html** - Phase別アップロードUI

---

## 🔧 ステップ2: ファイルのアップロード

### 📝 GASスクリプトファイルのアップロード

#### 方法1: 手動コピー&ペースト（推奨）

1. **Code.gs を MinimalMenuIntegration.gs に改名**
   - Apps Scriptエディタで Code.gs をクリック
   - ファイル名部分をクリックして「MinimalMenuIntegration」に変更
   - Enter キーで確定

2. **MinimalMenuIntegration.gs の内容を置き換え**
   - ローカルファイルを開く:
     ```
     C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts\MinimalMenuIntegration.gs
     ```
   - 内容をすべてコピー
   - Apps Scriptエディタの MinimalMenuIntegration.gs に貼り付け
   - Ctrl+S で保存

3. **残りの.gsファイルを追加**
   - Apps Scriptエディタで **ファイル > 新規 > スクリプト** をクリック
   - ファイル名を入力（例: UniversalPhaseUploader）
   - ローカルファイルの内容をコピー&ペースト
   - Ctrl+S で保存

**追加する.gsファイル**:
- ✅ UniversalPhaseUploader.gs
- ✅ MapDataProvider.gs
- ✅ Phase2Phase3Visualizations.gs
- ✅ GoogleMapsAPIConfig.gs

---

### 🌐 HTMLファイルのアップロード

1. **Apps Scriptエディタで ファイル > 新規 > HTML** をクリック

2. **ファイル名を入力** (例: MapComplete)

3. **HTMLの内容を置き換え**
   - ローカルファイルを開く:
     ```
     C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\html\MapComplete.html
     ```
   - 内容をすべてコピー
   - Apps Scriptエディタの MapComplete.html に貼り付け
   - Ctrl+S で保存

**追加するHTMLファイル**:
- ✅ MapComplete.html
- ✅ PhaseUpload.html

---

## 🎯 ステップ3: 動作確認

### 3-1. スプレッドシートを再読み込み

1. Apps Scriptエディタを閉じる
2. スプレッドシートのページを **F5キー** で再読み込み
3. メニューバーに **「📊 データ処理」** が表示されることを確認

### 3-2. メニュー項目の確認

「📊 データ処理」メニューをクリックして、以下の項目が表示されることを確認:

```
📊 データ処理
├── 📥 データインポート
│   ├── 📍 Phase 1: 基礎集計（4ファイル）
│   ├── 📊 Phase 2: 統計分析（2ファイル）
│   ├── 👥 Phase 3: ペルソナ分析（2ファイル）
│   ├── 🌊 Phase 6: フロー分析（3ファイル）
│   ├── 📈 Phase 7: 高度分析（7ファイル）
│   ├── ───────────────
│   └── ✅ 全Phaseアップロード状況
├── ───────────────
├── 📈 Phase 7高度分析
├── ───────────────
├── 🗺️ 地図表示（完全版）
├── ───────────────
├── 📈 統計分析・ペルソナ
│   ├── 🔬 カイ二乗検定結果
│   ├── 📊 ANOVA検定結果
│   ├── ───────────────
│   ├── 👥 ペルソナサマリー
│   └── 📋 ペルソナ詳細
├── ───────────────
├── 🌊 自治体間フロー分析
├── 🗺️ ペルソナマップ可視化
└── 🎯 ペルソナ難易度確認
```

---

## 📊 ステップ4: データのアップロード

### 4-1. Pythonでデータ生成

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project"
python python_scripts/simple_analyzer.py
```

**ファイル選択ダイアログが表示される**
→ `C:\Users\fuji1\OneDrive\Pythonスクリプト保管\out\results_20251027_180423.csv` を選択

**生成されるファイル** (18ファイル):
- Phase 1: 4ファイル (gas_output_phase1/)
- Phase 2: 2ファイル (gas_output_phase2/)
- Phase 3: 2ファイル (gas_output_phase3/)
- Phase 6: 3ファイル (gas_output_phase6/)
- Phase 7: 7ファイル (gas_output_phase7/)

---

### 4-2. GASにアップロード

#### Phase 1のアップロード（必須）

1. スプレッドシートメニュー: **📊 データ処理 > 📥 データインポート > 📍 Phase 1: 基礎集計（4ファイル）**

2. アップロードUIが表示される

3. 以下の4ファイルを選択してアップロード:
   - ✅ MapMetrics.csv (536件)
   - ✅ Applicants.csv (355件)
   - ✅ DesiredWork.csv (2,968件)
   - ✅ AggDesired.csv (536件)

4. 「アップロード開始」をクリック

5. 完了メッセージを確認

#### Phase 2-7のアップロード（オプション）

同様の手順で、Phase 2, 3, 6, 7をアップロード可能

---

## ✅ ステップ5: 動作確認

### MAP機能のテスト

1. メニュー: **📊 データ処理 > 🗺️ 地図表示（完全版）**
2. ダイアログが表示される
3. データ読み込み完了後、地図にマーカーが表示される
4. 表示モード切り替え（個別/クラスター/ヒートマップ）を確認
5. フィルター（性別・年齢）を確認
6. サイドバーの統計情報を確認

### Phase 2/3可視化のテスト

1. メニュー: **📊 データ処理 > 📈 統計分析・ペルソナ**
2. 各項目をクリック:
   - ✅ 🔬 カイ二乗検定結果
   - ✅ 📊 ANOVA検定結果
   - ✅ 👥 ペルソナサマリー
   - ✅ 📋 ペルソナ詳細
3. HTMLダイアログが表示されることを確認

---

## 📋 最終チェックリスト

### GASファイル (.gs) - 5ファイル

- [ ] MinimalMenuIntegration.gs (メインメニュー)
- [ ] UniversalPhaseUploader.gs (アップローダー)
- [ ] MapDataProvider.gs (MAP機能)
- [ ] Phase2Phase3Visualizations.gs (可視化)
- [ ] GoogleMapsAPIConfig.gs (API設定)

### HTMLファイル (.html) - 2ファイル

- [ ] MapComplete.html (MAP UI)
- [ ] PhaseUpload.html (アップロードUI)

### メニュー動作確認

- [ ] 「📊 データ処理」メニューが表示される
- [ ] Phase 1-7のアップロード項目が表示される
- [ ] 地図表示メニューが表示される
- [ ] Phase 2/3可視化メニューが表示される

### データアップロード確認

- [ ] Phase 1の4ファイルがアップロードできる
- [ ] MapMetrics, Applicants, DesiredWork, AggDesired シートが作成される

### 機能動作確認

- [ ] MAP機能が動作する（マーカー表示）
- [ ] 表示モード切り替えが動作する
- [ ] フィルター機能が動作する
- [ ] Phase 2/3可視化が動作する

---

## 🚨 トラブルシューティング

### エラー: 「getAllVisualizationData is not defined」

**原因**: MapDataProvider.gs が追加されていない

**解決方法**:
1. MapDataProvider.gs を新規スクリプトとして追加
2. 内容をコピー&ペースト
3. 保存

---

### エラー: 「MapComplete.html が見つかりません」

**原因**: MapComplete.html が追加されていない

**解決方法**:
1. 新規 > HTML で MapComplete.html を追加
2. 内容をコピー&ペースト
3. 保存

---

### メニューが表示されない

**原因**: onOpen関数が実行されていない

**解決方法**:
1. Apps Scriptエディタで MinimalMenuIntegration.gs を開く
2. 関数選択ドロップダウンから「onOpen」を選択
3. 実行ボタン（▶）をクリック
4. 権限を許可
5. スプレッドシートをF5で再読み込み

---

## 📝 備考

### ファイルの場所

すべてのファイルは以下のディレクトリにあります:

```
C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\
├── gas_files/
│   ├── scripts/
│   │   ├── MinimalMenuIntegration.gs
│   │   ├── UniversalPhaseUploader.gs
│   │   ├── MapDataProvider.gs
│   │   ├── Phase2Phase3Visualizations.gs
│   │   └── GoogleMapsAPIConfig.gs
│   └── html/
│       ├── MapComplete.html
│       └── PhaseUpload.html
```

### 技術スタック

- **地図**: Leaflet.js + OpenStreetMap（Google Maps API不要）
- **グラフ**: Chart.js
- **データ**: Google Sheets

### サポート

問題が発生した場合は、Apps Scriptのログを確認してください:
1. Apps Scriptエディタ > 表示 > ログ
2. エラーメッセージを確認

---

**作成日**: 2025-10-27
**バージョン**: 1.0
**対象**: job_medley_project
