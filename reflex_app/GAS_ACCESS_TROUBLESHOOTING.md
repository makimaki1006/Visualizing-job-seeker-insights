# GAS Webアプリ接続エラーのトラブルシューティング

## 現在の問題

Reflexアプリで「🗺️ 求人地図」タブを開くと、以下のエラーが表示されます：

```
script.google.com で接続が拒否されました。
```

## 原因

`clasp deploy`で作成したデプロイメントは、**初回アクセス時に認証が必要**です。
GAS WebアプリとしてRIP公開するには、Google Apps ScriptのWeb UIから手動でデプロイ設定を行う必要があります。

## 解決方法

### 方法1: Google Apps Script Web UIで手動デプロイ（推奨）

#### Step 1: GASプロジェクトを開く

1. 以下のURLをブラウザで開く:
   ```
   https://script.google.com/u/0/home/projects/1JYAF14K262xX1XtTkyUygFEUaQBfeMX2yKK0Pbc3k40hA07eipOa7IFo/edit
   ```

2. Googleアカウントでログイン

**注意**: 現在「Google ドキュメント内でエラーが発生しました」と表示される場合:
- ブラウザのキャッシュをクリア
- シークレットモードで開く
- 数分待ってから再度アクセス

#### Step 2: デプロイを管理

1. 右上の「デプロイ」ボタンをクリック
2. 「デプロイを管理」を選択

#### Step 3: 新しいWebアプリデプロイを作成

1. 「新しいデプロイ」をクリック
2. 設定:
   - **種類**: ⚙️マークをクリック → 「Webアプリ」を選択
   - **説明**: 求人地図Webアプリ（Reflex統合用）
   - **次のユーザーとして実行**: **自分（ユーザーのメールアドレス）** ← 重要！
   - **アクセスできるユーザー**: **全員（匿名ユーザーを含む）** ← 重要！
3. 「デプロイ」をクリック

#### Step 4: WebアプリURLをコピー

デプロイ完了後、以下の形式のURLが表示されます：

```
https://script.google.com/macros/s/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/exec
```

このURLをコピーしてください。

#### Step 5: Reflexアプリに設定

1. ファイルを開く:
   ```
   C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py
   ```

2. Line 5668付近の`GAS_WEBAPP_URL`を更新:
   ```python
   # 変更前（仮URL）:
   GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxBK5gRmDCuetK7bOp5IuLEFR1bnmsxPrIyYewgIYY/exec"

   # 変更後（Step 4でコピーした実際のURL）:
   GAS_WEBAPP_URL = "https://script.google.com/macros/s/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/exec"
   ```

3. ファイルを保存（Reflexアプリが自動リロードされます）

#### Step 6: 動作確認

1. http://localhost:3002/ を開く
2. 「🗺️ 求人地図」タブをクリック
3. GAS地図が表示されることを確認

### 方法2: 既存のデプロイメントを編集

既に`clasp deploy`で作成したデプロイメントがある場合:

1. GASプロジェクトを開く
2. 「デプロイ」→「デプロイを管理」
3. 既存のデプロイメント（@HEADまたは@1）を選択
4. 鉛筆アイコン（編集）をクリック
5. 「アクセスできるユーザー」を「全員（匿名ユーザーを含む）」に変更
6. 「新しいバージョンとしてデプロイ」をクリック
7. 生成されたWebアプリURLをコピー
8. 上記のStep 5-6を実行

## よくあるエラーと対処法

### エラー1: 「script.google.com で接続が拒否されました」

**原因**:
- デプロイメントが正しく設定されていない
- アクセス権限が「全員（匿名ユーザーを含む）」になっていない

**解決方法**:
- 上記の「方法1」を実行してください

### エラー2: 「Google ドキュメント内でエラーが発生しました」

**原因**:
- Google側の一時的なエラー
- ブラウザのキャッシュ問題

**解決方法**:
1. ブラウザのキャッシュをクリア
2. シークレットモード/プライベートブラウジングで開く
3. 数分待ってから再度アクセス
4. 別のブラウザで試す

### エラー3: 「承認が必要です」ダイアログが表示される

**原因**:
- 「次のユーザーとして実行」が「自分」に設定されていない

**解決方法**:
1. 「デプロイを管理」→ 既存デプロイを編集
2. 「次のユーザーとして実行」を「自分」に変更
3. 新しいバージョンとしてデプロイ

### エラー4: 地図は表示されるが、データが表示されない

**原因**:
- スプレッドシートの`SourceData`シートにデータがない
- スプレッドシートの共有設定が正しくない

**解決方法**:
1. スプレッドシートURL: https://docs.google.com/spreadsheets/d/1w7Mbo1eKiooLlt090Nj9nQQktE7m29qNPX1RcS5x7nw/edit
2. `SourceData`シートを確認
3. データが存在することを確認（30カラム形式）
4. スプレッドシートの共有設定:
   - 「リンクを知っている全員」が「閲覧者」以上

## デバッグ方法

### 1. GAS WebアプリURLを直接開く

ブラウザで以下のURLを直接開いてみてください：

```
https://script.google.com/macros/s/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/exec
```

**期待される結果**:
- Leaflet地図が表示される
- 検索コントロールパネルが表示される

**エラーが表示される場合**:
- デプロイ設定を確認してください

### 2. ブラウザの開発者ツールで確認

1. Reflexアプリ（http://localhost:3002/）を開く
2. F12キーを押して開発者ツールを開く
3. 「Console」タブを確認
4. 「🗺️ 求人地図」タブをクリック
5. エラーメッセージを確認

**よくあるエラーメッセージ**:
- `net::ERR_CONNECTION_REFUSED`: デプロイメントが無効
- `403 Forbidden`: アクセス権限の問題
- `401 Unauthorized`: 認証が必要

### 3. iframe要素の確認

開発者ツールの「Elements」タブで、iframe要素を確認：

```html
<iframe
    src="https://script.google.com/macros/s/.../exec"
    width="100%"
    height="800px"
    ...
></iframe>
```

`src`属性のURLが正しいか確認してください。

## 現在のデプロイメント状態

```bash
$ cd gas_deployment_reflex
$ clasp deployments

Found 2 deployments.
- AKfycbxBK5gRmDCuetK7bOp5IuLEFR1bnmsxPrIyYewgIYY @HEAD
- AKfycbwyUrJf_aJTN-UYj_CONbwXOB9fhp3Z7sb9X8Yt7UtwfOCuKf6avXoziE38OOkRryIQ @1 - 求人地図Webアプリ（Reflex統合用）
```

**現在設定されているURL**:
```
https://script.google.com/macros/s/AKfycbxBK5gRmDCuetK7bOp5IuLEFR1bnmsxPrIyYewgIYY/exec
```

このURLは`clasp deploy`で作成されたものなので、**初回アクセス時に認証が必要**な可能性が高いです。

## 推奨される次のステップ

1. **Google Apps Script Web UIが開けるようになるまで待つ**
   - 現在「Google ドキュメント内でエラーが発生しました」が表示されている
   - 数分後に再度アクセスを試す

2. **Web UIから手動でWebアプリデプロイを実行**
   - 「方法1」の手順に従ってください

3. **生成されたWebアプリURLをReflexアプリに設定**
   - `mapcomplete_dashboard.py` Line 5668を更新

4. **動作確認**
   - http://localhost:3002/ で「🗺️ 求人地図」タブをクリック

## 参考資料

- [GAS_DEPLOYMENT_GUIDE.md](GAS_DEPLOYMENT_GUIDE.md) - 詳細なデプロイ手順
- [GAS_INTEGRATION_COMPLETE.md](GAS_INTEGRATION_COMPLETE.md) - 実装完了レポート
- [Google Apps Script公式ドキュメント](https://developers.google.com/apps-script/guides/web) - Webアプリのデプロイ

---

**最終更新**: 2025年11月21日
**ステータス**: トラブルシューティング中（Google Docs エラー待機）
