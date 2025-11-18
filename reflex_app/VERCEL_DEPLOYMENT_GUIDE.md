# Vercel デプロイガイド（Reflexアプリ）

## 前提条件

**重要**: Reflexアプリの完全な機能（CSVアップロード、リアルタイム更新等）をVercelで動作させるには、以下の制約があります：

1. **Vercelの無料プランでは、Serverless Functionsのタイムアウトが10秒**
2. **WebSocketsは完全にはサポートされていない**（Vercel Edge Functionsで部分的に可能）
3. **Reflexの完全な機能を使うには、Reflex Hosting（公式）推奨**

そのため、以下の2つの選択肢があります：

---

## オプション1: Reflex Hosting（公式・推奨）

### メリット
- ✅ CSVアップロード等すべての機能が動作
- ✅ WebSocket完全対応
- ✅ 自動デプロイ（GitHubプッシュで自動更新）
- ✅ 無料プランあり（月750時間まで）

### 手順

1. **Reflex CLIでデプロイ**:
   ```bash
   cd reflex_app
   reflex deploy
   ```

2. **初回のみ: Reflexアカウント作成**
   - ブラウザが開いて認証ページが表示される
   - GitHubアカウントでサインアップ

3. **デプロイ設定**:
   - プロジェクト名を入力
   - リージョンを選択（Asia Pacific推奨）

4. **環境変数の設定**:
   ```bash
   reflex deploy --env-var DATABASE_URL=postgresql://...
   ```

5. **完了**:
   - デプロイ完了後、URLが表示される（例: `https://your-app.reflex.run`）

---

## オプション2: Vercel（静的サイトのみ）

### メリット
- ✅ 完全無料
- ✅ 高速
- ✅ 簡単

### デメリット
- ❌ CSVアップロード等の動的機能が動作しない
- ❌ データ更新機能なし
- ❌ 読み取り専用

### 手順

1. **Vercel CLIのインストール**:
   ```bash
   npm install -g vercel
   ```

2. **ログイン**:
   ```bash
   vercel login
   ```

3. **プロジェクトルートで初期化**:
   ```bash
   cd reflex_app
   vercel
   ```

4. **設定の質問に回答**:
   - Set up and deploy: `Y`
   - Which scope: 自分のアカウント選択
   - Link to existing project: `N`
   - Project name: `job-medley-dashboard`
   - Directory: `.`（デフォルト）
   - Override settings: `Y`
   - Build Command: `reflex export --no-zip`
   - Output Directory: `.web/build`
   - Development Command: （空欄でEnter）

5. **デプロイ完了**:
   - URLが表示される（例: `https://job-medley-dashboard.vercel.app`）

---

## 推奨: オプション1（Reflex Hosting）

**理由**:
- すべての機能が動作する
- 無料プランでも十分（月750時間 = 常時稼働可能）
- セットアップが最も簡単

**次のステップ**:
```bash
cd reflex_app
reflex deploy
```

ブラウザで認証後、数分でデプロイ完了します。
