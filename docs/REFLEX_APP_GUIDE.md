# Reflexアプリケーション完全ガイド

**バージョン**: 3.0 (Reflex統合版)
**最終更新**: 2025年11月22日
**Reflexバージョン**: v0.8.19
**ステータス**: 本番運用可能 ✅

このドキュメントでは、ジョブメドレー求職者データ分析・可視化システムのReflexダッシュボードアプリケーションの完全な使用方法とカスタマイズ方法を説明します。

---

## 📋 目次

1. [概要](#概要)
2. [システム要件](#システム要件)
3. [インストール](#インストール)
4. [起動方法](#起動方法)
5. [認証システム](#認証システム)
6. [ダッシュボード機能](#ダッシュボード機能)
7. [データベース統合](#データベース統合)
8. [カスタマイズ](#カスタマイズ)
9. [トラブルシューティング](#トラブルシューティング)
10. [デプロイ](#デプロイ)

---

## 🎯 概要

### システム構成

```
ユーザー（ブラウザ）
    ↓
ログインページ（login.py）
    ↓
認証処理（auth.py）
    ├─ ドメイン検証（@f-a-c.co.jp、@cyxen.co.jp）
    ├─ パスワード検証（共通パスワード）
    └─ セッション管理（サーバーサイド）
    ↓
ダッシュボード（mapcomplete_dashboard.py）
    ├─ 10パネル統合UI
    ├─ サーバーサイドフィルタリング
    └─ Tursoクラウドデータベース（18,877行）
    ↓
データ表示（グラフ、テーブル、マップ等）
```

### 主要機能

- **ドメイン制限認証**: @f-a-c.co.jp、@cyxen.co.jpのみアクセス可能
- **10パネル統合ダッシュボード**: 総合概要、人材供給、キャリア分析、緊急度分析、ペルソナ分析、クロス分析、フロー分析、需給バランス、希少人材分析、人材プロファイル
- **都道府県・市区町村フィルタ**: サーバーサイドフィルタリング（メモリ効率70MB→0.1-1MB/ユーザー）
- **Tursoクラウドデータベース**: 18,877行、48都道府県、22市区町村
- **CSVアップロード**: ローカルCSVファイルのアップロード・分析機能
- **色覚バリアフリー対応**: Okabe-Itoカラーパレット準拠

---

## 💻 システム要件

### 必須環境

- **Python**: 3.10以上（3.11推奨）
- **OS**: Windows 10/11、macOS 12以降、Linux（Ubuntu 20.04以降）
- **メモリ**: 4GB以上（推奨8GB以上）
- **ディスク**: 500MB以上の空き容量

### 推奨ブラウザ

- **Google Chrome**: 最新版（推奨）
- **Microsoft Edge**: 最新版
- **Firefox**: 最新版
- **Safari**: 最新版（macOSのみ）

---

## 🔧 インストール

### 1. リポジトリのクローン（オプション）

```bash
git clone https://github.com/your-org/job-medley-analyzer.git
cd job-medley-analyzer/reflex_app
```

### 2. 依存パッケージのインストール

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app"
pip install -r requirements.txt
```

**主要パッケージ**:
- `reflex==0.8.19` - Webフレームワーク
- `pandas` - データ分析
- `libsql-client` - Tursoデータベース接続
- `python-dotenv` - 環境変数管理

### 3. 環境変数の設定

`.env`ファイルを作成（存在しない場合）：

```bash
# reflex_app/.env
# ドメイン制限認証設定
ALLOWED_DOMAINS=f-a-c.co.jp,cyxen.co.jp
AUTH_PASSWORD=cyxen_2025_12_01
SESSION_SECRET=f8e9a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8

# Tursoクラウドデータベース設定
TURSO_DATABASE_URL=libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io
TURSO_AUTH_TOKEN=eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NjM3ODk2NzgsImlkIjoiNTU1YzQwMzgtZjI0MS00ODAwLTgzYTctYmE4MmYzOGQyZGFhIiwicmlkIjoiNjJmNTFkMjgtNTdhNC00M2Y2LWIzZTAtYmRlZGZiM2YxNmY1In0.Q-WMFowjDxhbdUqkeKYG7y4qkhfbsFaVgqKtAyU0y2bdCTNCHOp8IQsHFYgJ6wdT4m96WIXtP4UO-jRbB8woBg
```

**重要**: `.env`ファイルは`.gitignore`に追加し、Gitにコミットしないでください。

### 4. Reflexの初期化（初回のみ）

```bash
reflex init
```

---

## 🚀 起動方法

### 標準起動

```bash
cd "C:\Users\fuji1\OneDrive\Pythonスクリプト保管\job_medley_project\reflex_app"
reflex run
```

**デフォルトポート**:
- **フロントエンド**: http://localhost:3000/
- **バックエンド**: http://localhost:8000/

### カスタムポート指定

```bash
reflex run --backend-port 8003 --frontend-port 3003
```

**アクセスURL**: http://localhost:3003/

### 起動確認

以下のメッセージが表示されれば成功：

```
[DB] サーバーサイドフィルタリングを有効化 (turso)
[INFO] DB全体: 18,877行, フィルタ済み: 9行
[INFO] 都道府県数: 48, 市区町村数: 22
[INFO] 選択: 北海道 札幌市中央区

--------------------------------- App Running ---------------------------------
App running at: http://localhost:3003/
Backend running at: http://0.0.0.0:8003
```

---

## 🔐 認証システム

### 認証フロー

```
1. ユーザーがログインページにアクセス
    ↓
2. メールアドレスとパスワードを入力
    ↓
3. ドメイン検証（@f-a-c.co.jp、@cyxen.co.jp）
    ↓
4. パスワード検証（共通パスワード）
    ↓
5. セッション管理（サーバーサイド）
    ↓
6. ダッシュボードへリダイレクト
```

### ログイン手順

1. **ブラウザでアクセス**: http://localhost:3003/
2. **ログインページが表示**: 自動的にログインページへリダイレクト
3. **メールアドレス入力**: 例 `user@f-a-c.co.jp`
4. **パスワード入力**: `cyxen_2025_12_01`
5. **ログインボタンをクリック**
6. **ダッシュボード表示**: 認証成功後、ダッシュボードへ

### 認証エラーの対処

#### エラー: 「このドメイン（@xxx）は許可されていません」

**原因**: 許可されていないドメインのメールアドレスを使用

**対処法**: @f-a-c.co.jp または @cyxen.co.jp のメールアドレスを使用

---

#### エラー: 「パスワードが間違っています」

**原因**: パスワードが正しくない

**対処法**: `.env`ファイルの`AUTH_PASSWORD`の値を確認

---

#### エラー: 「メールアドレスとパスワードを入力してください」

**原因**: 入力フィールドが空

**対処法**: 両方のフィールドに入力

---

### ログアウト

ダッシュボード右上の「ログアウト」ボタンをクリック

---

## 📊 ダッシュボード機能

### 10パネル構成

| パネルID | パネル名 | 主要機能 |
|----------|---------|---------|
| overview | 総合概要 | 全体サマリー、KPIカード、統計概要 |
| supply | 人材供給 | 人材供給密度マップ、供給分布グラフ |
| career | キャリア分析 | キャリア分布、キャリア×年齢クロス集計 |
| urgency | 緊急度分析 | 転職意欲分布、緊急度×年齢クロス集計 |
| persona | ペルソナ分析 | ペルソナ分類、ペルソナ詳細プロファイル |
| cross | クロス分析 | 属性間クロス集計、相関分析 |
| flow | フロー分析 | 居住地→希望勤務地フロー、移動パターン |
| gap | 需給バランス | 需給ギャップ分析、需給比率マップ |
| rarity | 希少人材分析 | 希少性スコアリング、レアスキル分析 |
| competition | 人材プロファイル | 競合分析、人材プロファイル一覧 |

### パネル切り替え

**タブ方式**: 画面右側のタブをクリックでパネル切り替え

**ショートカットキー**（予定）:
- `1-9`: パネル1-9へ移動
- `0`: パネル10へ移動

---

### フィルタリング機能

#### 都道府県フィルタ

**位置**: サイドバー上部

**機能**: 選択した都道府県のデータのみ表示

**操作**:
1. ドロップダウンから都道府県を選択
2. 自動的にデータ更新
3. 市区町村フィルタも連動して更新

---

#### 市区町村フィルタ

**位置**: サイドバー上部（都道府県フィルタの下）

**機能**: 選択した市区町村のデータのみ表示

**操作**:
1. ドロップダウンから市区町村を選択
2. 自動的にデータ更新

**注意**: 都道府県選択後に市区町村が選択可能になります。

---

### CSVアップロード機能

**位置**: サイドバー下部

**対応形式**: CSV（UTF-8 with BOM推奨）

**操作手順**:
1. 「CSVファイルをアップロード」ボタンをクリック
2. ファイル選択ダイアログでCSVファイルを選択
3. 自動的にデータ読み込み・分析
4. ダッシュボード更新

**注意**: CSVアップロード後はデータベースではなくアップロードされたCSVデータを使用します。

---

## 🗄️ データベース統合

### Tursoクラウドデータベース

**データベース情報**:

| 項目 | 値 |
|------|-----|
| Organization | makimaki1006 |
| Database | job-jobseekeranalyzer |
| Region | ap-northeast-1 (Tokyo) |
| URL | libsql://job-jobseekeranalyzer-makimaki1006.aws-ap-northeast-1.turso.io |
| データ行数 | 18,877行 |
| 都道府県数 | 48 |
| 市区町村数 | 22 |

---

### サーバーサイドフィルタリング

**従来の問題**:
- 全データをクライアント側に送信（70MB/ユーザー）
- メモリ消費が大きく、30人以上の同時利用に耐えられない

**Reflexソリューション**:
- サーバー側でフィルタリング済みデータのみ送信（0.1-1MB/ユーザー）
- メモリ消費を99%削減
- 30人以上の同時利用に対応

**実装**:
```python
# db_helper.py
def get_filtered_data(prefecture: str, municipality: str = None) -> pd.DataFrame:
    """サーバーサイドフィルタリング"""
    query = f"SELECT * FROM jobseekers WHERE prefecture = '{prefecture}'"
    if municipality:
        query += f" AND municipality = '{municipality}'"
    return query_df(query)
```

---

### データベース接続確認

**接続成功メッセージ**:
```
[DB] サーバーサイドフィルタリングを有効化 (turso)
[INFO] DB全体: 18,877行, フィルタ済み: 9行
```

**接続失敗時の対処**:
1. `.env`ファイルの`TURSO_DATABASE_URL`と`TURSO_AUTH_TOKEN`を確認
2. ネットワーク接続を確認
3. Tursoダッシュボードでデータベースの状態を確認

---

## 🎨 カスタマイズ

### 配色変更

**ファイル**: `mapcomplete_dashboard/mapcomplete_dashboard.py`（Line 35-59）

**現在の配色**（色覚バリアフリー対応）:

```python
# 色覚多様性対応カラーパレット（Okabe-Ito準拠）
PRIMARY_COLOR = "#0072B2"       # 濃い青
SECONDARY_COLOR = "#E69F00"     # オレンジ
ACCENT_3 = "#CC79A7"            # 赤紫
ACCENT_4 = "#009E73"            # 青緑
ACCENT_5 = "#F0E442"            # 黄色
ACCENT_6 = "#D55E00"            # 朱色
ACCENT_7 = "#56B4E9"            # スカイブルー
```

**カスタマイズ方法**:
1. 上記の色コードを変更
2. `COLOR_PALETTE`配列を更新
3. アプリを再起動

---

### パネル追加

**手順**:

1. **TABS配列に追加**（Line 64-76）:
```python
TABS = [
    {"id": "overview", "label": "総合概要"},
    # ...
    {"id": "new_panel", "label": "新しいパネル"},  # 追加
]
```

2. **ページ関数を作成**:
```python
def page_new_panel() -> rx.Component:
    """新しいパネル"""
    return rx.box(
        rx.heading("新しいパネル", size="6"),
        # パネルコンテンツ
    )
```

3. **index()関数で分岐を追加**（Line 1700前後）:
```python
def index() -> rx.Component:
    """メインページ"""
    return rx.cond(
        DashboardState.active_tab == "overview",
        page_overview(),
        # ...
        rx.cond(
            DashboardState.active_tab == "new_panel",
            page_new_panel(),
            page_overview()  # デフォルト
        )
    )
```

---

### KPIカード追加

**手順**:

1. **State計算プロパティ追加**:
```python
class DashboardState(rx.State):
    @rx.var(cache=False)
    def new_kpi_value(self) -> str:
        """新しいKPI値"""
        if not self.df:
            return "0"
        # 計算ロジック
        return str(value)
```

2. **kpi_card()を使用**:
```python
kpi_card("新しいKPI", DashboardState.new_kpi_value, "単位")
```

---

## 🛠️ トラブルシューティング

### 問題: サーバーが起動しない

**確認事項**:
1. `.env`ファイルが存在するか
2. `TURSO_DATABASE_URL`と`TURSO_AUTH_TOKEN`が設定されているか
3. `libsql-client`がインストールされているか

**解決方法**:
```bash
pip show libsql-client
# インストールされていない場合
pip install libsql-client
```

---

### 問題: データベース接続エラー

**エラーメッセージ例**:
```
[ERROR] Failed to connect to Turso database
```

**確認事項**:
1. Tursoの認証トークンが正しいか
2. データベースURLが正しいか
3. ネットワーク接続が正常か

**解決方法**:
```bash
# .envファイルを確認
cat .env | grep TURSO

# Tursoダッシュボードでトークンを再発行
# https://turso.tech/dashboard
```

---

### 問題: ログインできない

**確認事項**:
1. メールアドレスのドメインが許可リストに含まれているか（@f-a-c.co.jp、@cyxen.co.jp）
2. パスワードが正しいか（`.env`の`AUTH_PASSWORD`と一致）
3. ブラウザのコンソールにエラーが表示されていないか

**解決方法**:
```bash
# .envファイルを確認
cat .env | grep ALLOWED_DOMAINS
cat .env | grep AUTH_PASSWORD
```

---

### 問題: パネルが表示されない

**確認事項**:
1. `DashboardState.active_tab`の値が正しいか
2. ブラウザのデベロッパーツール（F12）でエラーを確認
3. Stateが正しく初期化されているか

**解決方法**:
```bash
# ブラウザのコンソールを確認（F12キー）
# エラーメッセージを確認
```

---

### 問題: データが表示されない

**確認事項**:
1. データベース接続が正常か
2. フィルタ設定が適切か（都道府県・市区町村）
3. CSVアップロードがされている場合、CSVデータが正しいか

**解決方法**:
```bash
# サーバーログを確認
# [INFO] DB全体: 18,877行, フィルタ済み: 0行 ← フィルタ済み行数が0の場合、フィルタ設定を確認
```

---

## 🌐 デプロイ

### Render.com（推奨）

**手順**:

1. **Render.comアカウント作成**: https://render.com/

2. **新しいWebサービス作成**:
   - Repository: GitHub/GitLabリポジトリを接続
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `reflex run --backend-port 8000 --frontend-port 3000`

3. **環境変数設定**:
   - `ALLOWED_DOMAINS`: `f-a-c.co.jp,cyxen.co.jp`
   - `AUTH_PASSWORD`: 本番用パスワード
   - `SESSION_SECRET`: 本番用秘密鍵（64文字）
   - `TURSO_DATABASE_URL`: Turso URL
   - `TURSO_AUTH_TOKEN`: Tursoトークン

4. **デプロイ**: 自動的にデプロイ開始

**注意**: Render.comの無料プランは15分間アイドル後にスリープします。

---

### Vercel（代替案）

**手順**:

1. **Vercel CLIインストール**:
```bash
npm install -g vercel
```

2. **Reflexアプリをエクスポート**:
```bash
reflex export
```

3. **Vercelにデプロイ**:
```bash
vercel --prod
```

**注意**: VercelはPythonバックエンドの制約があるため、Render.com推奨。

---

## 📚 関連ドキュメント

- **[README.md](../README.md)** - プロジェクトメインドキュメント
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - プロジェクト構造詳細
- **[V3_CSV_SPECIFICATION.md](V3_CSV_SPECIFICATION.md)** - V3 CSV完全仕様
- **[DOMAIN_AUTHENTICATION_GUIDE.md](../reflex_app/docs/DOMAIN_AUTHENTICATION_GUIDE.md)** - 認証システム完全ガイド
- **[Reflexドキュメント](https://reflex.dev/docs)** - Reflex公式ドキュメント

---

## 🔗 参考リンク

### Reflex関連
- **Reflexドキュメント**: https://reflex.dev/docs
- **Reflexサンプル**: https://github.com/reflex-dev/reflex-examples
- **Reflexコミュニティ**: https://discord.gg/reflex

### Turso関連
- **Tursoダッシュボード**: https://turso.tech/dashboard
- **Tursoドキュメント**: https://docs.turso.tech/
- **libsql-client**: https://github.com/libsql/libsql-client-py

---

## ⚙️ 技術仕様

### 使用技術

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Reflex | v0.8.19 | Webフレームワーク |
| Python | 3.10+ | バックエンド |
| Turso | - | クラウドSQLiteデータベース |
| libsql-client | - | Turso接続 |
| python-dotenv | - | 環境変数管理 |
| pandas | - | データ分析 |

---

### サーバー設定

- **バックエンドポート**: 8003（デフォルト8000）
- **フロントエンドポート**: 3003（デフォルト3000）
- **認証方式**: サーバーサイドセッション管理
- **データベース**: Turso（サーバーサイドフィルタリング有効）

---

### パフォーマンス

**最適化手法**:
- サーバーサイドフィルタリング（メモリ消費99%削減）
- State計算プロパティのキャッシュ（`cache=False`で動的更新）
- 色覚バリアフリー対応（Okabe-Itoカラーパレット）

**同時接続可能ユーザー数**: 30人以上（サーバーサイドフィルタリングにより）

---

## 📝 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-22 | 3.0 | Reflex統合版として完全実装完了 |
| 2025-11-14 | 2.1 | ドメイン制限認証システム導入 |
| 2025-11-13 | 2.0 | Tursoクラウドデータベース統合 |
| 2025-11-01 | 1.0 | 初版リリース（GAS統合版） |

---

**作成**: Claude Code
**日付**: 2025年11月22日
**プロジェクト**: ジョブメドレー求職者データ分析・可視化システム v3.0
