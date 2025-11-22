# GASデプロイ実行プラン

**作成日**: 2025年10月27日
**目的**: MenuIntegration.gsのエラーを完全に解消

---

## 🎯 現状の問題

### 確認された問題:

1. **MenuIntegration.gs**: 14個の存在しない関数を参照
   - `showMapBubble`, `showMapHeatmap`, `showChiSquareTests`, etc.

2. **UniversalPhaseUploader.gs**: Phase7のシート名不一致
   - ❌ `PersonaMapData` → ✅ `Phase7_PersonaMapData` にすべき
   - ❌ `PersonaMobilityCross` → ✅ `Phase7_PersonaMobilityCross` にすべき

---

## ✅ 解決策（ドキュメント準拠）

### 📋 更新ファイル（2ファイル）

| # | ファイル名 | 操作 | ソースファイル |
|---|-----------|------|--------------|
| 1 | MenuIntegration.gs | 🔄 全置換 | MinimalMenuIntegration.gs |
| 2 | UniversalPhaseUploader.gs | 🔄 2行修正 | - |

### 🚫 追加ファイル

**なし**（既存のファイルのみで対応）

### 🚫 削除ファイル

**なし**（削除不要）

---

## 📝 作業手順（詳細）

### ステップ1: MenuIntegration.gsを更新

#### 1-1. GASエディタでファイルを開く

1. Googleスプレッドシートで **拡張機能** > **Apps Script**
2. 左側のファイル一覧で **MenuIntegration.gs** をクリック
3. ファイルが開いたことを確認

#### 1-2. 現在の内容を全削除

4. **Ctrl+A** （全選択）
5. **Delete** （削除）
6. エディタが空白になったことを確認

#### 1-3. MinimalMenuIntegration.gsの内容をコピー

7. Windowsエクスプローラーを開く
8. 以下のパスに移動:
   ```
   C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\scripts
   ```
9. **MinimalMenuIntegration.gs** をダブルクリックして開く（メモ帳で開く）
10. **Ctrl+A** （全選択）
11. **Ctrl+C** （コピー）

#### 1-4. GASエディタにペースト

12. GASエディタのMenuIntegration.gsタブに戻る
13. **Ctrl+V** （ペースト）
14. 内容が貼り付けられたことを確認
15. **Ctrl+S** （保存）
16. 保存完了メッセージを確認

---

### ステップ2: UniversalPhaseUploader.gsを更新

#### 2-1. GASエディタでファイルを開く

1. 左側のファイル一覧で **UniversalPhaseUploader.gs** をクリック

#### 2-2. 該当箇所を検索

2. **Ctrl+F** （検索）
3. 検索ボックスに `PersonaMapData.csv` と入力
4. Enterキーを押す
5. 該当行（59行目付近）にジャンプ

#### 2-3. 2行を修正

6. 以下の2行を探す:
   ```javascript
   { name: 'PersonaMapData.csv', sheetName: 'PersonaMapData', label: 'ペルソナ地図' },
   { name: 'PersonaMobilityCross.csv', sheetName: 'PersonaMobilityCross', label: 'ペルソナ×移動' }
   ```

7. 以下に書き換える（`sheetName`の値のみ変更）:
   ```javascript
   { name: 'PersonaMapData.csv', sheetName: 'Phase7_PersonaMapData', label: 'ペルソナ地図' },
   { name: 'PersonaMobilityCross.csv', sheetName: 'Phase7_PersonaMobilityCross', label: 'ペルソナ×移動' }
   ```

8. **Ctrl+S** （保存）
9. 保存完了メッセージを確認

---

### ステップ3: スプレッドシートをリロード

1. Googleスプレッドシートのタブに切り替える
2. **Ctrl+Shift+R** （完全リロード）
3. 数秒待つ（5秒程度）
4. ページが完全に再読み込みされることを確認

---

### ステップ4: 動作確認

#### 4-1. メニュー確認

1. メニューバーに **📊 データ処理** が表示されることを確認
2. **📊 データ処理** をクリック
3. 以下のサブメニューが表示されることを確認:
   - 📥 データインポート
   - 📈 Phase 7高度分析
   - 🌊 自治体間フロー分析
   - 🗺️ ペルソナマップ可視化
   - 🎯 ペルソナ難易度確認

#### 4-2. Phase別アップロード確認

4. **📥 データインポート** にマウスオーバー
5. 以下が表示されることを確認:
   - 📍 Phase 1: 基礎集計（4ファイル）
   - 📊 Phase 2: 統計分析（2ファイル）
   - 👥 Phase 3: ペルソナ分析（2ファイル）
   - 🌊 Phase 6: フロー分析（3ファイル）
   - 📈 Phase 7: 高度分析（7ファイル）
   - ✅ 全Phaseアップロード状況

#### 4-3. エラーがないことを確認

6. 各メニュー項目をクリックしてエラーが出ないことを確認
7. エラーが出た場合は、Apps Scriptエディタの **表示** > **ログ** でエラー詳細を確認

---

## 📊 期待される結果

### ✅ 成功の基準

1. **メニューが正常に表示される**
   - 「スクリプト関数が見つかりません」エラーが出ない

2. **Phase別アップロードが動作する**
   - Phase 1〜7の各メニュー項目をクリックしてダイアログが開く

3. **Phase 7データが正しく表示される**
   - ペルソナマップ可視化でエラーが出ない
   - Phase7_PersonaMapDataシートを正しく参照できる

---

## 🚨 トラブルシューティング

### エラー1: 「スクリプト関数が見つかりません: uploadPhase1」

**原因**: MenuIntegration.gsの更新が反映されていない

**対処**:
1. Apps Scriptエディタで **Ctrl+S** で再保存
2. Googleスプレッドシートで **Ctrl+Shift+R** で完全リロード

---

### エラー2: 「PhaseUpload.htmlが見つかりません」

**原因**: PhaseUpload.htmlがGASプロジェクトに追加されていない

**対処**:
1. Apps Scriptエディタで **+** アイコン → **HTML**
2. ファイル名: `PhaseUpload`
3. 以下のパスの内容をコピー&ペースト:
   ```
   C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\gas_files\html\PhaseUpload.html
   ```

---

### エラー3: 「Phase7_PersonaMapDataシートが見つかりません」

**原因**: Phase 7のCSVファイルがアップロードされていない、またはシート名が異なる

**対処**:
1. **📊 データ処理** > **📥 データインポート** > **📈 Phase 7: 高度分析（7ファイル）**
2. 7つのCSVファイルをアップロード
3. シート名が `Phase7_PersonaMapData` で作成されることを確認

---

## ✅ 完了チェックリスト

実行前に以下を確認してください:

- [ ] MenuIntegration.gsの内容がMinimalMenuIntegration.gsと同じ
- [ ] UniversalPhaseUploader.gsの59-60行目が修正済み
- [ ] Googleスプレッドシートが完全にリロードされている
- [ ] メニュー「📊 データ処理」が表示される
- [ ] 「📥 データインポート」サブメニューが表示される
- [ ] Phase 1〜7の各メニュー項目が表示される
- [ ] いずれかのメニューをクリックしてもエラーが出ない

全てチェックが付いたら、**デプロイ完了**です！

---

**作業時間目安**: 5分
