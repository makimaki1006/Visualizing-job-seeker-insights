# Reflex Hosting デプロイガイド

**バージョン**: 1.0
**最終更新**: 2025年11月18日
**デプロイURL**: https://mapcomplete-dashboard-aqua-orca.reflex.run
**ステータス**: 本番運用中 ✅

---

## 概要

このドキュメントは、ジョブメドレー求職者データ分析ダッシュボードをReflex Hostingにデプロイするプロセスをまとめたものです。

### なぜReflex Hostingを選んだのか？

当初Vercelでのデプロイを検討しましたが、以下の理由でReflex Hostingを選択しました：

| 要件 | Reflex Hosting (無料) | Vercel (無料) | 判定 |
|------|----------------------|--------------|------|
| CSVアップロード | ✅ タイムアウトなし | ❌ 10秒でタイムアウト | Reflex勝利 |
| WebSockets | ✅ 完全対応 | ❌ 非対応 | Reflex勝利 |
| 20名同時利用 | ✅ 可能 | ❌ 制限厳しい | Reflex勝利 |
| 月間稼働時間 | ✅ 750時間（常時稼働可能） | ✅ 無制限 | 両方OK |
| デプロイの簡単さ | ✅ 1コマンド | ⚠️ 複雑 | Reflex勝利 |
| 月額料金 | ✅ 無料 | ✅ 無料 | 両方OK |

**結論**: Reflexアプリケーションには、Reflex Hostingが最適です。

---

## デプロイ情報

### デプロイ済みアプリケーション

- **URL**: https://mapcomplete-dashboard-aqua-orca.reflex.run
- **プロジェクトID**: 3dfb8b60-e44d-457a-9b59-6f76e2823516
- **アプリID**: d85b4f79-855a-4db0-99af-4c03c49dabf5
- **プロジェクト名**: fuji1006.29292410
- **アプリ名**: mapcomplete_dashboard
- **リージョン**: Asia Pacific (Tokyo)

### 管理コンソール

Reflex Cloud: https://cloud.reflex.dev

---

## デプロイ手順（初回）

### 前提条件

1. **Reflex CLI インストール済み**
   ```bash
   pip install reflex --upgrade
   ```

2. **GitHubアカウント**（認証に必要）
   - まだない場合: https://github.com でアカウント作成（無料）

### 手順1: クリーンなデプロイディレクトリを作成

**重要**: OneDriveディレクトリから直接デプロイすると、タイムスタンプエラーが発生します。

```powershell
# クリーンなデプロイディレクトリを作成
mkdir C:\temp\reflex_app_deploy

# 元のディレクトリに移動
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app"

# 必要なファイルをコピー（dataディレクトリは除外）
Copy-Item -Path *.py, requirements.txt, rxconfig.py, assets -Destination C:\temp\reflex_app_deploy -Recurse -Exclude data

# モジュールディレクトリをコピー
Copy-Item -Path mapcomplete_dashboard -Destination C:\temp\reflex_app_deploy -Recurse -Force

# デプロイディレクトリに移動
cd C:\temp\reflex_app_deploy
```

### 手順2: 初回デプロイ

```bash
reflex deploy
```

### 手順3: 認証とプロジェクト設定

1. **ブラウザが自動的に開きます**
   - Reflex Cloudのダッシュボードが表示されます
   - GitHubアカウントでサインインします

2. **プロジェクト選択または作成**
   - 既存プロジェクトがある場合: 選択
   - 新規の場合: 「Create New Project」をクリック

3. **アプリ名を入力**
   ```
   ? What is your app name? mapcomplete_dashboard
   ```

4. **リージョンを選択**
   ```
   ? Select a region: Asia Pacific (Tokyo)
   ```

5. **デプロイ実行確認**
   ```
   Do you wish to proceed? [Y/n] Y
   ```

### 手順4: デプロイ完了

デプロイが成功すると、以下のようなメッセージが表示されます：

```
✅ Deployment successful!
🌐 Your app is live at: https://mapcomplete-dashboard-aqua-orca.reflex.run
```

---

## トラブルシューティング

### エラー1: ZIP Timestamp Error

**エラーメッセージ**:
```
Unable to export due to: ZIP does not support timestamps before 1980
```

**原因**: OneDrive同期により、一部のファイルが1980年以前のタイムスタンプを持つため

**解決方法**: 上記の「手順1: クリーンなデプロイディレクトリを作成」を実行してください

---

### エラー2: Module Not Found

**エラーメッセージ**:
```
Module mapcomplete_dashboard.mapcomplete_dashboard not found.
```

**原因**: `mapcomplete_dashboard/` ディレクトリがコピーされていない

**解決方法**:
```powershell
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app"
Copy-Item -Path mapcomplete_dashboard -Destination C:\temp\reflex_app_deploy -Recurse -Force
cd C:\temp\reflex_app_deploy
reflex deploy --project 3dfb8b60-e44d-457a-9b59-6f76e2823516
```

---

### エラー3: reflex: command not found

**解決方法**:
```bash
pip install reflex --upgrade
```

---

## 再デプロイ手順（アップデート時）

アプリケーションを更新した場合の再デプロイ手順：

```powershell
# 1. 元のディレクトリで変更を確認
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app"

# 2. デプロイディレクトリを削除して再作成
Remove-Item -Recurse -Force C:\temp\reflex_app_deploy
mkdir C:\temp\reflex_app_deploy

# 3. 最新ファイルをコピー
Copy-Item -Path *.py, requirements.txt, rxconfig.py, assets -Destination C:\temp\reflex_app_deploy -Recurse -Exclude data
Copy-Item -Path mapcomplete_dashboard -Destination C:\temp\reflex_app_deploy -Recurse -Force

# 4. デプロイディレクトリに移動
cd C:\temp\reflex_app_deploy

# 5. 既存プロジェクトに再デプロイ
reflex deploy --project 3dfb8b60-e44d-457a-9b59-6f76e2823516
```

---

## データ永続化について

### 現在の仕様（SQLite）

- **データベース**: SQLite (`data/job_medley.db`)
- **CSV アップロード**: データベースに保存されます
- **永続化期間**: 現在のデプロイセッション中のみ
- **再デプロイ時**: データベースがリセットされます

### 将来の拡張（PostgreSQL）

永続的なデータ保存が必要な場合は、PostgreSQLの導入を推奨します：

1. **無料PostgreSQL提供サービス**:
   - Supabase (https://supabase.com) - 500MB無料
   - Neon (https://neon.tech) - 3GBまで無料
   - ElephantSQL (https://www.elephantsql.com) - 20MB無料

2. **接続方法**:
   ```bash
   reflex deploy --env-var DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **rxconfig.py 設定**:
   ```python
   import os

   config = rx.Config(
       app_name="mapcomplete_dashboard",
       db_url=os.getenv("DATABASE_URL", "sqlite:///reflex.db"),
   )
   ```

**注意**: PostgreSQL統合は将来実装予定です。現在のSQLite版で問題なく動作します。

---

## Reflex Hostingの特徴

### ✅ 無料プランで利用可能な機能

- **CSVアップロード**: タイムアウトなし（大きなファイルも対応）
- **20名同時利用**: 問題なく対応可能
- **リアルタイム更新**: WebSocket完全対応
- **自動デプロイ**: GitHubプッシュで自動更新可能（オプション）
- **常時稼働**: 750時間/月 = 1日約25時間相当
- **HTTPS**: 自動対応
- **環境変数**: 安全な管理

### 📊 監視・ログ

Reflex Cloudダッシュボードから以下を確認できます：

- アクセスログ
- エラーログ
- パフォーマンス監視
- デプロイ履歴

---

## よくある質問

### Q1: 無料プランの制限は？

**A**: 750時間/月（約31日稼働）。実質的に常時稼働可能です。

### Q2: カスタムドメインは使える？

**A**: Reflex Hosting有料プラン（Pro）で対応可能です。無料プランでは `.reflex.run` ドメインのみです。

### Q3: デプロイに失敗したらどうする？

**A**: 「トラブルシューティング」セクションを参照してください。ほとんどの問題は解決できます。

### Q4: 本番環境で使用できますか？

**A**: はい。現在のデプロイは本番運用可能です。ただし、重要なデータの永続化にはPostgreSQLの導入を推奨します。

---

## 次のステップ

### 推奨アクション

1. **アプリケーションの動作確認**
   - https://mapcomplete-dashboard-aqua-orca.reflex.run にアクセス
   - CSVアップロード機能をテスト
   - 各種可視化機能を確認

2. **定期的な更新**
   - アプリケーションを更新した場合は、「再デプロイ手順」に従ってデプロイ

3. **将来的な拡張（オプション）**
   - PostgreSQL導入（データ永続化）
   - カスタムドメイン設定（有料プラン）
   - CI/CD統合（GitHub Actions等）

---

## 参考情報

### 公式ドキュメント

- **Reflex公式サイト**: https://reflex.dev
- **Reflex Hosting**: https://reflex.dev/docs/hosting/deploy-quick-start/
- **Reflex Cloud**: https://cloud.reflex.dev

### プロジェクトファイル

- **`.gitignore`**: デプロイ除外ファイル設定
- **`requirements.txt`**: Python依存関係
- **`rxconfig.py`**: Reflex設定ファイル

### 関連ドキュメント

- **[VERCEL_DEPLOYMENT_GUIDE.md](./VERCEL_DEPLOYMENT_GUIDE.md)**: Vercelとの比較
- **[README.md](../README.md)**: プロジェクト全体のドキュメント

---

## デプロイ履歴

| 日付 | バージョン | 変更内容 | デプロイ担当 |
|------|-----------|---------|------------|
| 2025-11-18 | 1.0 | 初回デプロイ成功 | Claude Code |

---

## サポート

問題が発生した場合は、以下を確認してください：

1. このドキュメントの「トラブルシューティング」セクション
2. Reflex公式ドキュメント: https://reflex.dev/docs/
3. Reflex Discord: https://discord.gg/T5WSbC2YtQ

---

**最終更新**: 2025年11月18日
**ドキュメントバージョン**: 1.0
