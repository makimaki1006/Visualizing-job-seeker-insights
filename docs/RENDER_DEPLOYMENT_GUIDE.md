# Render.com デプロイガイド

**バージョン**: 1.0
**最終更新**: 2025年11月17日
**対象**: ジョブメドレー求職者データ分析ダッシュボード（Reflexアプリ）

---

## 📋 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [デプロイ手順（自動）](#デプロイ手順自動)
4. [デプロイ手順（手動）](#デプロイ手順手動)
5. [環境変数設定](#環境変数設定)
6. [データベース移行](#データベース移行)
7. [トラブルシューティング](#トラブルシューティング)
8. [運用・監視](#運用監視)

---

## 概要

このガイドでは、Reflexダッシュボードアプリケーションを **Render.com** にデプロイする方法を説明します。

### デプロイ構成

| コンポーネント | Render Service Type | プラン | 詳細 |
|---------------|-------------------|------|------|
| Webアプリ | Web Service | Free | Reflexダッシュボード |
| データベース | PostgreSQL | Free | 1GB ストレージ |

### 主な機能

- ✅ **ハイブリッドDB対応**: SQLite（ローカル） + PostgreSQL（本番）
- ✅ **Infrastructure as Code**: render.yaml による自動セットアップ
- ✅ **自動デプロイ**: GitHub連携で自動ビルド・デプロイ
- ✅ **無料プラン対応**: 月額$0で運用可能（制限あり）

---

## 前提条件

### 必須アカウント

1. **GitHub アカウント**
   - リポジトリ: `https://github.com/makimaki1006/Visualizing-job-seeker-insights.git`
   - アクセス権: リポジトリへのプッシュ権限

2. **Render.com アカウント**
   - 無料プラン登録済み
   - GitHubアカウント連携済み

### 必要なファイル（すでに作成済み）

✅ `reflex_app/requirements.txt` - Python依存関係
✅ `reflex_app/build.sh` - ビルドスクリプト
✅ `reflex_app/start.sh` - 起動スクリプト
✅ `render.yaml` - Infrastructure as Code
✅ `reflex_app/database_schema.py` - データベーススキーマ
✅ `reflex_app/db_helper.py` - データベース接続ヘルパー

---

## デプロイ手順（自動）

### ステップ1: GitHubにプッシュ

最新のコードをGitHubにプッシュします（すでに完了済み）：

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project"
git status
git add .
git commit -m "feat: Render deployment configuration"
git push origin main
```

### ステップ2: Render.comでBlueprint作成

1. Render.com ダッシュボードにログイン
   https://dashboard.render.com/

2. **「New」 → 「Blueprint」** をクリック

3. GitHubリポジトリを選択
   - Repository: `makimaki1006/Visualizing-job-seeker-insights`
   - Branch: `main`

4. **「Apply」** をクリック

   render.yamlが自動的に検出され、以下のサービスが作成されます：
   - ✅ PostgreSQLデータベース（job-medley-db）
   - ✅ Webサービス（job-medley-dashboard）

### ステップ3: ビルド完了を待つ

ビルドログを確認し、以下のメッセージが表示されれば成功：

```
=================================
Build Complete!
=================================
```

### ステップ4: アクセス確認

Render.comダッシュボードでWebサービスのURLを確認：

```
https://job-medley-dashboard.onrender.com
```

ブラウザでアクセスし、ダッシュボードが表示されることを確認。

---

## デプロイ手順（手動）

自動デプロイが利用できない場合の手動設定手順です。

### ステップ1: PostgreSQLデータベース作成

1. Render.com ダッシュボードで **「New」 → 「PostgreSQL」**
2. 設定値を入力：
   - **Name**: `job-medley-db`
   - **Database**: `job_medley`
   - **User**: `job_medley_user`
   - **Region**: `Oregon (US West)`
   - **Plan**: `Free`
3. **「Create Database」** をクリック

### ステップ2: Webサービス作成

1. Render.com ダッシュボードで **「New」 → 「Web Service」**
2. GitHubリポジトリを選択
   - Repository: `makimaki1006/Visualizing-job-seeker-insights`
   - Branch: `main`
3. 設定値を入力：
   - **Name**: `job-medley-dashboard`
   - **Region**: `Oregon (US West)`
   - **Branch**: `main`
   - **Root Directory**: (空欄)
   - **Runtime**: `Python 3`
   - **Build Command**: `cd reflex_app && chmod +x build.sh && ./build.sh`
   - **Start Command**: `cd reflex_app && chmod +x start.sh && ./start.sh`
   - **Plan**: `Free`
4. **「Create Web Service」** をクリック

### ステップ3: 環境変数設定

Webサービスの設定画面で **「Environment」** タブを開き、以下を追加：

| Key | Value | 説明 |
|-----|-------|------|
| `PYTHON_VERSION` | `3.11.0` | Pythonバージョン |
| `DATABASE_URL` | `postgres://...` | PostgreSQL接続文字列（Databaseから取得） |

DATABASE_URLの取得方法：
1. PostgreSQLサービスの **「Connect」** タブを開く
2. **「Internal Database URL」** をコピー
3. WebサービスのDATABASE_URLに貼り付け

---

## 環境変数設定

### 必須環境変数

| 変数名 | 設定値 | 説明 |
|--------|--------|------|
| `PYTHON_VERSION` | `3.11.0` | Pythonバージョン指定 |
| `DATABASE_URL` | `postgres://user:password@host:port/dbname` | PostgreSQL接続文字列 |

### オプション環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|------------|------|
| `PORT` | `8000` | アプリケーションポート |
| `REFLEX_ENV` | `prod` | Reflex実行環境 |

---

## データベース移行

### 初回デプロイ時の自動移行

build.shスクリプトが以下を自動実行します：

1. **スキーマ作成**: database_schema.pyからCREATE TABLE文を実行
2. **インデックス作成**: 都道府県・市区町村等のインデックスを作成

### 手動移行（必要時のみ）

SQLiteから PostgreSQLへのデータ移行：

```bash
# ローカルでmigrate_to_postgresql.pyを実行
set DATABASE_URL=postgres://user:password@host:port/dbname
python reflex_app/migrate_to_postgresql.py
```

---

## トラブルシューティング

### ビルドエラー: 「reflex: command not found」

**原因**: requirements.txtに reflex がない

**解決方法**:
```bash
# requirements.txtを確認
cat reflex_app/requirements.txt

# reflexが含まれていることを確認
reflex>=0.5.0
```

### 起動エラー: 「no such table: mapcomplete_raw」

**原因**: データベーススキーマが未作成

**解決方法**:
1. build.shのStep 5が実行されたか確認
2. 手動でスキーマ作成：
   ```bash
   python -c "from database_schema import get_all_create_table_sqls; ..."
   ```

### データベース接続エラー

**原因**: DATABASE_URL が正しくない

**解決方法**:
1. PostgreSQLサービスの **「Connect」** タブで接続文字列を確認
2. WebサービスのDATABASE_URL環境変数を更新
3. サービスを再デプロイ

### フリープランの制限に注意

Renderの無料プランには以下の制限があります：

- ✅ **ディスク容量**: 512MB
- ✅ **データベース**: 1GB
- ⚠️ **15分間アクセスなしでスリープ**
- ⚠️ **月750時間まで稼働** (31日フル稼働は不可)

### スリープ対策

15分間アクセスがないと自動的にスリープします。以下の方法で対策可能：

1. **外部監視サービス利用**: UptimeRobot等で5分ごとにアクセス
2. **有料プランへアップグレード**: $7/月でスリープなし

---

## 運用・監視

### ログ確認

Render.comダッシュボードの **「Logs」** タブでリアルタイムログを確認：

```
[INFO] DB起動時ロード成功: 1234行 (postgresql)
[INFO] 都道府県数: 47
[INFO] 市区町村数: 1896
```

### デプロイ履歴

**「Events」** タブで過去のデプロイ履歴を確認可能。

### メトリクス監視

**「Metrics」** タブで以下を確認：

- CPU使用率
- メモリ使用率
- リクエスト数
- レスポンスタイム

### 自動デプロイ設定

デフォルトで **mainブランチへのプッシュで自動デプロイ** が実行されます。

無効化する場合：
1. Webサービス設定の **「Settings」** タブ
2. **「Auto-Deploy」** をOFFに変更

---

## 次のステップ

### 1. カスタムドメイン設定（オプション）

独自ドメインを使用する場合：

1. Render.comダッシュボードで **「Settings」** → **「Custom Domain」**
2. ドメイン名を入力（例: `dashboard.example.com`）
3. DNSレコードを設定（CNAME）

### 2. HTTPS証明書

Renderは **自動的にLet's Encrypt証明書を発行** します（無料）。

### 3. パフォーマンス最適化

- データベースインデックスの最適化
- キャッシュ戦略の導入
- CDN利用（静的ファイル配信）

### 4. セキュリティ強化

- 環境変数にシークレット情報を保存
- アクセス制御の実装（認証機能追加）
- CORS設定の厳格化

---

## 参考リンク

- **Render.com公式ドキュメント**: https://render.com/docs
- **Reflex公式ドキュメント**: https://reflex.dev/docs/
- **プロジェクトリポジトリ**: https://github.com/makimaki1006/Visualizing-job-seeker-insights

---

## サポート

問題が発生した場合：

1. **ログ確認**: Render.comダッシュボードの「Logs」タブ
2. **ドキュメント確認**: `docs/REFLEX_DATABASE_INTEGRATION_REPORT.md`
3. **GitHub Issue**: リポジトリのIssuesで報告

---

**デプロイ成功をお祈りします！🚀**
