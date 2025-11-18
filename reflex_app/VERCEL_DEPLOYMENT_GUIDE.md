# Reflex Hosting デプロイガイド（推奨）

## 重要: Vercelでは要件を満たせません ❌

CSVアップロード機能と20名同時利用を実現するには、**Reflex Hostingが唯一の選択肢**です。

### なぜVercelは使えないのか？

| 機能 | Reflex Hosting (無料) | Vercel (無料) | Vercel (Pro $20/月) |
|------|----------------------|--------------|-------------------|
| CSVアップロード | ✅ 制限なし | ❌ 10秒でタイムアウト | ⚠️ 60秒でタイムアウト |
| WebSockets | ✅ 完全対応 | ❌ 非対応 | ⚠️ 実験的（非推奨） |
| 20名同時利用 | ✅ 可能 | ❌ 制限厳しい | ✅ 可能 |
| 月間稼働時間 | ✅ 750時間（常時稼働可能） | ✅ 無制限 | ✅ 無制限 |
| デプロイの簡単さ | ✅ 1コマンド | ⚠️ 複雑 | ⚠️ 複雑 |
| 月額料金 | ✅ 無料 | ✅ 無料 | ❌ $20 |

**結論**: Vercelの無料プランは静的サイトのみ、有料プランでも制約あり。

---

## Reflex Hosting デプロイ手順（推奨） ✅

### 1. デプロイコマンド実行

```bash
cd C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app
reflex deploy
```

### 2. 初回のみ: アカウント作成

ブラウザが自動的に開き、認証ページが表示されます：

1. **GitHubアカウントでサインアップ**
2. **認証完了後、自動的にCLIに戻る**

### 3. デプロイ設定

```
? What is your app name? job-medley-dashboard
? Select a region: Asia Pacific (Tokyo)
```

### 4. 環境変数の設定（オプション）

PostgreSQLを使う場合のみ：

```bash
reflex deploy --env-var DATABASE_URL=postgresql://...
```

**注意**: SQLiteで十分な場合、環境変数設定は不要です。

### 5. デプロイ完了

```
✅ Deployment successful!
🌐 Your app is live at: https://job-medley-dashboard.reflex.run
```

---

## Reflex Hostingの特徴

### ✅ 完全無料で要件を満たす

- **CSVアップロード**: タイムアウトなし
- **20名同時利用**: 対応可能
- **リアルタイム更新**: WebSocket完全対応
- **自動デプロイ**: GitHubプッシュで自動更新
- **常時稼働**: 750時間/月 = 1日25時間相当

### 🔒 セキュリティ

- HTTPS自動対応
- 環境変数の安全な管理
- 自動バックアップ

### 📊 監視・ログ

- アクセスログ
- エラーログ
- パフォーマンス監視

---

## トラブルシューティング

### Q1: `reflex: command not found`

**解決方法**:
```bash
pip install reflex --upgrade
```

### Q2: GitHubアカウントがない

**解決方法**:
1. https://github.com でアカウント作成（無料）
2. `reflex deploy` を再実行

### Q3: デプロイ後にエラーが出る

**解決方法**:
1. ローカルで `reflex run` が正常に動作することを確認
2. `reflex deploy --verbose` で詳細ログ確認

---

## 次のステップ

### 推奨アクション

```bash
cd C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app
reflex deploy
```

数分でデプロイ完了し、すべての機能が使えるようになります。

---

## 参考: Vercelとの比較（詳細）

### Vercelの技術的制約

#### 1. Serverless Functionsのタイムアウト
- **無料**: 10秒（CSVアップロード不可）
- **Pro ($20/月)**: 60秒（大きなCSVは不可）
- **Enterprise**: カスタム（要問い合わせ）

#### 2. WebSocketsサポート
- **無料**: 非対応（リアルタイム更新不可）
- **Pro**: Edge Functionsで実験的（本番非推奨）

#### 3. 同時接続数
- **無料**: 厳しい制限（20名同時は困難）
- **Pro**: 制限緩和（可能）

### Reflex Hostingの優位性

- ✅ すべての制約なし
- ✅ Reflexに最適化された環境
- ✅ 無料プランで要件を完全に満たす
