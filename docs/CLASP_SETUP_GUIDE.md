# clasp セットアップガイド（Apps Script 同期用）

## 前提条件
- Node.js / npm がインストール済み
- Google アカウントで Apps Script プロジェクト（スプレッドシートに紐づくプロジェクトでも OK）が存在
- 公式 CLI ツール clasp の使用が許可されている環境

ローカルの `gas_files_production/` を「真の開発ディレクトリ」として扱い、`clasp push` のみで Google Apps Script プロジェクトへ反映できる状態を構築します。

---

## 1. clasp をインストール

```bash
npm install -g @google/clasp
```

インストール後、バージョン確認（任意）:

```bash
clasp --version
```

---

## 2. Google アカウントでログイン

```bash
clasp login
```

ブラウザが開くので、ガイダンスに従って権限を承認します。複数アカウントを使い分ける場合は、後述の `clasp login --status` で切り替え可能です。

---

## 3. Apps Script プロジェクト ID を取得

1. 既存の Apps Script プロジェクトを開く（スプレッドシートに紐づく場合は「拡張機能 → Apps Script」）
2. URL を確認  
   `https://script.google.com/.../d/<PROJECT_ID>/edit`  
   この `<PROJECT_ID>` を控えます。

---

## 4. `.clasp.json` を作成

ルートディレクトリは `gas_files_production/` を想定します。

```bash
cd path/to/project/gas_files_production
```

`.clasp.json` を作成し、以下の内容を記述します。

```json
{
  "scriptId": "<PROJECT_ID>",
  "rootDir": "."
}
```

- ファイル名・拡張子は現在の構成 (`*.gs`, `*.html`) をそのまま利用できます。
- 複数環境を使い分ける場合は `.clasp.dev.json` など複数の設定ファイルを用意し、`clasp push --project .clasp.dev.json` のように指定できます。

(`.clasp.json` 自体をリポジトリに含めるかはプロジェクトのポリシーに従ってください)

---

## 5. 初回同期

### 5.1 プル（既存コードをローカルへ取得）

既に Apps Script 側でコードがある場合は、先にローカルへ引き込みます。

```bash
clasp pull
```

### 5.2 変更内容のアップロード

`gas_files_production/` に加えた変更をクラウドへ反映するには、

```bash
clasp push
```

実行後、Apps Script エディタを開いてコードが更新されたか確認します。

---

## 6. 途中の切り戻し／ステータス確認

- ログイン状態の確認: `clasp login --status`
- 他のアカウントへ切り替えたい場合: `clasp login --logout` → `clasp login`
- 差分を事前に確認したい場合はスプレッドシート側でバージョン管理を使うか、ローカルで Git 管理を併用してください。

---

## 7. 注意点

- `.clasp.json` の `rootDir` 以下がそのまま Apps Script へ push されます。不要なファイルは除外しておきましょう。
- `clasp push` は差分ベースではなく、対象フォルダ全体を送信します。  
  → 誤って削除したファイルも push すればクラウド側から削除されるため、Git 等でローカルのバックアップを保持しておくと安全です。
- Apps Script 側で手作業の編集を行い、`clasp pull` で同期し忘れるとローカルとクラウドがずれます。作業ルール（必ずローカルで編集 → push）を決めておくと良いでしょう。

---

これでローカルの `gas_files_production/` と Google Apps Script プロジェクトを直接同期できるようになります。複数環境（本番／検証）を分けたい場合の `.clasp.json` 設定例など必要があれば追記しますので、お知らせください。
