# GAS求人地図 Webアプリデプロイガイド

## 概要

このガイドでは、Google Apps Script（GAS）の求人地図機能をWebアプリとしてデプロイし、ReflexアプリにiframeとしてRIP埋め込む手順を説明します。

## 前提条件

- GASプロジェクトが存在すること
- プロジェクトURL: https://script.google.com/u/0/home/projects/1JYAF14K262xX1XtTkyUygFEUaQBfeMX2yKK0Pbc3k40hA07eipOa7IFo/edit

## Step 1: GAS Webアプリデプロイ（5分）

### 1-1. GASプロジェクトを開く

1. 上記のプロジェクトURLをブラウザで開く
2. Googleアカウントでログイン

### 1-2. デプロイを実行

1. 右上の「デプロイ」ボタンをクリック
2. 「新しいデプロイ」を選択
3. 設定:
   - **種類**: Webアプリ
   - **説明**: 求人地図可視化（任意）
   - **次のユーザーとして実行**: 自分（デプロイ実行者）
   - **アクセスできるユーザー**: **全員（匿名ユーザーを含む）** ← 重要！
4. 「デプロイ」をクリック

### 1-3. WebアプリURLをコピー

デプロイ完了後、以下の形式のURLが表示されます：

```
https://script.google.com/macros/s/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/exec
```

このURLをコピーしてください。

**重要**: このURLは以下で使用します。

## Step 2: Reflex統合（5分）

### 2-1. mapcomplete_dashboard.pyを編集

ファイル: `C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app\mapcomplete_dashboard\mapcomplete_dashboard.py`

Line 5657付近の`GAS_WEBAPP_URL`を更新：

```python
# 現在（仮URL）:
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzKYHRg3VFaPn8sRr0fiUqB6cIZNr1aUm2DPG_Nc8ydBbmKxNVFNOd6hSRGUvFqFWOI/exec"

# 変更後（Step 1-3でコピーした実際のURL）:
GAS_WEBAPP_URL = "https://script.google.com/macros/s/XXXXXXXXXXXXXXXXXXXXXXXXXXXX/exec"
```

### 2-2. Reflexアプリを再起動（自動）

ファイルを保存すると、Reflexアプリが自動的にリロードされます。
バックグラウンドで実行中のReflexアプリがファイル変更を検出し、自動更新します。

## Step 3: 動作確認（5分）

### 3-1. ブラウザでアクセス

1. http://localhost:3002/ を開く
2. 「🗺️ 求人地図」タブをクリック
3. GAS地図が表示されることを確認

### 3-2. 機能確認

以下の機能が動作することを確認：

- ✅ Leaflet地図が表示される
- ✅ 都道府県・市区町村で検索できる
- ✅ マーカーをクリックして詳細が表示される
- ✅ 詳細カードの「📌 ピン」ボタンで地図上にピン止めできる
- ✅ ピン止めカードをドラッグ&ドロップで移動できる
- ✅ マーカーとピン止めカードが点線で接続される
- ✅ 統計情報（平均・中央値・最頻値）が表示される

## トラブルシューティング

### iframeが表示されない

**原因**: GASのアクセス設定が間違っている

**解決方法**:
1. GASプロジェクトで「デプロイを管理」を開く
2. 既存のデプロイを編集
3. 「アクセスできるユーザー」を「全員（匿名ユーザーを含む）」に変更
4. 保存して再デプロイ

### 地図が表示されるが、データが表示されない

**原因**: GASスプレッドシートの`SourceData`シートにデータがない

**解決方法**:
1. スプレッドシートURL: https://docs.google.com/spreadsheets/d/1w7Mbo1eKiooLlt090Nj9nQQktE7m29qNPX1RcS5x7nw/edit?gid=0#gid=0
2. `SourceData`シートを確認
3. データが存在することを確認（30カラム形式）

### CORS エラー

**原因**: GASのWebアプリ設定が正しくない

**解決方法**:
GASの`appsscript.json`を確認：

```json
{
  "webapp": {
    "access": "ANYONE_ANONYMOUS",
    "executeAs": "USER_DEPLOYING"
  }
}
```

## 高度な機能（オプション）

### Reflex ↔ GAS データ連携

postMessage APIを使用して、ReflexからGASにデータを送信できます：

**Reflex側（mapcomplete_dashboard.py）**:
```python
rx.html(
    f"""
    <iframe id="gas-map" src="{GAS_WEBAPP_URL}" ...></iframe>
    <script>
        const iframe = document.getElementById('gas-map');
        iframe.contentWindow.postMessage({{
            type: 'filterUpdate',
            prefecture: '北海道',
            municipality: '札幌市'
        }}, '*');
    </script>
    """
)
```

**GAS側（Map.html）**:
```javascript
window.addEventListener('message', function(event) {
    if (event.data.type === 'filterUpdate') {
        document.getElementById('prefecture').value = event.data.prefecture;
        document.getElementById('municipality').value = event.data.municipality;
        filterAndDisplay();
    }
});
```

## まとめ

- **実装時間**: 合計15分（デプロイ5分 + 統合5分 + 確認5分）
- **機能カバー率**: 100%（GASの全機能をそのまま使用）
- **メンテナンス**: GAS側の変更がそのまま反映される

## 参考資料

- [GAS_WEBAPP_EMBEDDING_ANALYSIS.md](GAS_WEBAPP_EMBEDDING_ANALYSIS.md) - 技術的詳細
- [GAS_LOGIC_MECE_ANALYSIS.md](GAS_LOGIC_MECE_ANALYSIS.md) - 機能分析
- [PINNED_CARD_FEASIBILITY_ANALYSIS.md](PINNED_CARD_FEASIBILITY_ANALYSIS.md) - 代替実装の比較
